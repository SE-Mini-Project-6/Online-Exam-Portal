"""
Sprint 2 security regression tests: password handling (SEC-REQ-01), logout/CSRF hardening
(SEC-REQ-01/02) and HTTPS-only deployment configuration (SEC-REQ-04).

Design spec OEP-SADS-1.0 section 3.6: "Passwords are stored using Django's configured salted
one-way password hasher, never as plaintext" and "Production/deployed access is HTTPS-only".
"""
import json
import os
import subprocess
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

STRONG_PASSWORD = 'Tr0ub4dor&3-Sprint2'


@override_settings(SECURE_SSL_REDIRECT=False)
class PasswordHandlingTests(TestCase):
    """SEC-REQ-01"""

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.student = users.objects.create_user('pw-student', password=STRONG_PASSWORD)
        cls.twin = users.objects.create_user('pw-twin', password=STRONG_PASSWORD)
        cls.admin = users.objects.create_user('pw-admin', password=STRONG_PASSWORD, is_staff=True)

    def test_password_is_stored_as_a_salted_pbkdf2_hash_never_plaintext(self):
        stored = self.student.password
        self.assertNotIn(STRONG_PASSWORD, stored)
        algorithm, iterations, salt, digest = stored.split('$')
        self.assertEqual(algorithm, 'pbkdf2_sha256')
        self.assertGreaterEqual(int(iterations), 600000)
        self.assertTrue(salt)
        self.assertTrue(digest)
        self.assertTrue(self.student.check_password(STRONG_PASSWORD))
        self.assertFalse(self.student.check_password(STRONG_PASSWORD + 'x'))

    def test_same_password_produces_different_hashes_per_user(self):
        self.assertNotEqual(self.student.password, self.twin.password)

    def test_password_hasher_configuration_is_not_weakened(self):
        self.assertEqual(settings.PASSWORD_HASHERS[0], 'django.contrib.auth.hashers.PBKDF2PasswordHasher')
        for weak in ('MD5', 'SHA1', 'UnsaltedMD5', 'UnsaltedSHA1', 'Crypt'):
            self.assertFalse(any(weak in name and 'PBKDF2' not in name for name in settings.PASSWORD_HASHERS), weak)

    def test_weak_passwords_are_rejected_by_the_configured_validators(self):
        weak = {
            'too short': 'Ab1!',
            'numeric only': '8274619305127',
            'common password': 'password',
            'similar to username': 'pw-student1',
        }
        for label, candidate in weak.items():
            with self.subTest(label):
                with self.assertRaises(ValidationError):
                    validate_password(candidate, user=self.student)
        validate_password(STRONG_PASSWORD, user=self.student)

    def test_changed_password_replaces_the_old_hash(self):
        old_hash = self.student.password
        self.student.set_password('N3w-Passw0rd#Sprint2')
        self.student.save()
        self.assertNotEqual(self.student.password, old_hash)
        self.assertFalse(self.student.check_password(STRONG_PASSWORD))
        self.assertTrue(self.student.check_password('N3w-Passw0rd#Sprint2'))

    def test_failed_login_message_is_identical_for_wrong_password_and_unknown_user(self):
        wrong_password = self.client.post(reverse('accounts:student_login'),
                                          {'username': 'pw-student', 'password': 'Wrong-Pass#1'})
        unknown_user = self.client.post(reverse('accounts:student_login'),
                                        {'username': 'nobody-here', 'password': 'Wrong-Pass#1'})
        for response in (wrong_password, unknown_user):
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Invalid username or password.')
            self.assertNotIn('_auth_user_id', self.client.session)
        self.assertNotContains(wrong_password, 'Wrong-Pass#1')
        self.assertNotContains(unknown_user, 'Wrong-Pass#1')

    def test_successful_login_never_echoes_the_password_or_its_hash(self):
        response = self.client.post(reverse('accounts:student_login'),
                                    {'username': 'pw-student', 'password': STRONG_PASSWORD}, follow=True)
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(STRONG_PASSWORD, body)
        self.assertNotIn(self.student.password, body)
        self.assertNotIn('pbkdf2_sha256', body)

    def test_inactive_account_cannot_log_in(self):
        get_user_model().objects.filter(pk=self.student.pk).update(is_active=False)
        response = self.client.post(reverse('accounts:student_login'),
                                    {'username': 'pw-student', 'password': STRONG_PASSWORD})
        self.assertContains(response, 'Invalid username or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_missing_credentials_are_rejected_without_a_server_error(self):
        for data in ({}, {'username': 'pw-student'}, {'password': STRONG_PASSWORD}):
            with self.subTest(data=data):
                response = self.client.post(reverse('accounts:login'), data)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('_auth_user_id', self.client.session)


@override_settings(SECURE_SSL_REDIRECT=False)
class LogoutAndCsrfTests(TestCase):
    """SEC-REQ-01/02: sessions can only be ended by an intentional, CSRF-protected POST."""

    @classmethod
    def setUpTestData(cls):
        cls.student = get_user_model().objects.create_user('csrf-student', password=STRONG_PASSWORD)

    def test_logout_rejects_get(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.student)
        response = client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 403)
        self.assertIn('_auth_user_id', client.session)

    def test_logout_post_with_csrf_token_ends_the_session(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.student)
        client.get(reverse('accounts:student_dashboard'))
        token = client.cookies['csrftoken'].value
        response = client.post(reverse('accounts:logout'), {'csrfmiddlewaretoken': token})
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', client.session)

    def test_login_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        for name in ('accounts:login', 'accounts:student_login'):
            with self.subTest(name):
                response = client.post(reverse(name), {'username': 'csrf-student', 'password': STRONG_PASSWORD})
                self.assertEqual(response.status_code, 403)
                self.assertNotIn('_auth_user_id', client.session)


class HttpsEnforcementTests(TestCase):
    """SEC-REQ-04: HTTP is redirected to HTTPS and cookies/HSTS protect HTTPS sessions."""

    @classmethod
    def setUpTestData(cls):
        cls.student = get_user_model().objects.create_user('https-student', password=STRONG_PASSWORD)

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_plain_http_request_is_redirected_to_https(self):
        for url in ('/', reverse('accounts:student_login'), reverse('exams:available'),
                    reverse('api:answer_detail', args=[1, 1])):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 301)
                self.assertTrue(response['Location'].startswith('https://'))

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_credentials_posted_over_http_are_never_processed(self):
        response = self.client.post(reverse('accounts:student_login'),
                                    {'username': 'https-student', 'password': STRONG_PASSWORD})
        self.assertEqual(response.status_code, 301)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(SECURE_SSL_REDIRECT=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True,
                       SECURE_HSTS_SECONDS=31536000, SECURE_HSTS_INCLUDE_SUBDOMAINS=True)
    def test_https_request_is_served_with_hsts_and_secure_cookies(self):
        response = self.client.post(reverse('accounts:student_login'),
                                    {'username': 'https-student', 'password': STRONG_PASSWORD}, secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn('max-age=31536000', response['Strict-Transport-Security'])
        self.assertIn('includeSubDomains', response['Strict-Transport-Security'])
        self.assertTrue(response.cookies[settings.SESSION_COOKIE_NAME]['secure'])
        self.assertTrue(response.cookies[settings.SESSION_COOKIE_NAME]['httponly'])


class HttpsSettingsModuleTests(TestCase):
    """SEC-REQ-04: the real settings module is HTTPS-only unless DJANGO_DEBUG=true."""

    @staticmethod
    def load_settings(**env_overrides):
        env = {k: v for k, v in os.environ.items() if not k.startswith('DJANGO_')}
        env.update(DJANGO_SETTINGS_MODULE='Online_Exam_Portal.settings', **env_overrides)
        script = (
            'import json, django; django.setup(); from django.conf import settings as s; '
            'print(json.dumps({k: getattr(s, k, None) for k in ('
            '"DEBUG", "SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", '
            '"SECURE_HSTS_SECONDS", "SECURE_HSTS_INCLUDE_SUBDOMAINS", "SECURE_PROXY_SSL_HEADER", '
            '"ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS", "SECRET_KEY")}))'
        )
        result = subprocess.run([sys.executable, '-c', script], cwd=settings.BASE_DIR, env=env,
                                capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_default_configuration_is_https_only(self):
        loaded = self.load_settings()
        self.assertFalse(loaded['DEBUG'])
        self.assertTrue(loaded['SECURE_SSL_REDIRECT'])
        self.assertTrue(loaded['SESSION_COOKIE_SECURE'])
        self.assertTrue(loaded['CSRF_COOKIE_SECURE'])
        self.assertGreaterEqual(loaded['SECURE_HSTS_SECONDS'], 31536000)
        self.assertTrue(loaded['SECURE_HSTS_INCLUDE_SUBDOMAINS'])
        self.assertIsNone(loaded['SECURE_PROXY_SSL_HEADER'])

    def test_debug_mode_relaxes_https_for_local_development_only(self):
        loaded = self.load_settings(DJANGO_DEBUG='true')
        self.assertTrue(loaded['DEBUG'])
        self.assertFalse(loaded['SECURE_SSL_REDIRECT'])
        self.assertFalse(loaded['SESSION_COOKIE_SECURE'])
        self.assertEqual(loaded['SECURE_HSTS_SECONDS'], 0)

    def test_deployment_environment_variables_are_honoured(self):
        loaded = self.load_settings(
            DJANGO_ALLOWED_HOSTS='exam.example.edu, www.exam.example.edu',
            DJANGO_CSRF_TRUSTED_ORIGINS='https://exam.example.edu',
            DJANGO_SECRET_KEY='x' * 60,
            DJANGO_BEHIND_PROXY='true',
        )
        self.assertEqual(loaded['ALLOWED_HOSTS'], ['exam.example.edu', 'www.exam.example.edu'])
        self.assertEqual(loaded['CSRF_TRUSTED_ORIGINS'], ['https://exam.example.edu'])
        self.assertEqual(loaded['SECRET_KEY'], 'x' * 60)
        self.assertEqual(loaded['SECURE_PROXY_SSL_HEADER'], ['HTTP_X_FORWARDED_PROTO', 'https'])

    def test_manage_check_deploy_is_clean_with_production_environment(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith('DJANGO_')}
        env.update(
            DJANGO_SETTINGS_MODULE='Online_Exam_Portal.settings',
            DJANGO_SECRET_KEY='k8#Zq!v2Lm9$Xw4@Rt7&Yb1^Nc5*Hd3%Gf6(Js0)Pa8-Ue2_Wo4+Ik',
            DJANGO_ALLOWED_HOSTS='exam.example.edu',
        )
        result = subprocess.run([sys.executable, 'manage.py', 'check', '--deploy', '--fail-level', 'WARNING'],
                                cwd=settings.BASE_DIR, env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
