"""
Sprint 2 security and integrity regression tests (issue: security regression story).

Traceability (design spec OEP-SADS-1.0, section 3.6 and 5):
    SEC-REQ-01  password handling ............ accounts/test_security.py
    SEC-REQ-02  RBAC + object ownership ...... RoleAuthorizationTests, OwnershipTests
    SEC-REQ-03  attempt state guard (409) .... PostSubmitMutationTests
    SEC-REQ-04  HTTPS-only deployment ........ accounts/test_security.py
"""
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Answer, Attempt, Exam, Question


@override_settings(SECURE_SSL_REDIRECT=False)
class SecurityTestCase(TestCase):
    """Shared fixtures: one admin, two students, one open exam with two questions."""

    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.admin = users.objects.create_user('sec-admin', password='SecAdmin#2026', is_staff=True)
        cls.student = users.objects.create_user('sec-student', password='SecStudent#2026')
        cls.other = users.objects.create_user('sec-other', password='SecOther#2026')
        now = timezone.now()
        cls.exam = Exam.objects.create(
            title='Security exam', duration_minutes=20,
            start_at=now - timedelta(minutes=5), end_at=now + timedelta(hours=1),
        )
        cls.q1 = Question.objects.create(
            exam=cls.exam, text='2+2?', option_a='4', option_b='3', option_c='2', option_d='5', correct_option='A',
        )
        cls.q2 = Question.objects.create(
            exam=cls.exam, text='Capital of India?', option_a='Mumbai', option_b='Delhi',
            option_c='Kolkata', option_d='Chennai', correct_option='B',
        )
        cls.take_url = reverse('exams:take', args=[cls.exam.pk])
        cls.submit_url = reverse('exams:submit', args=[cls.exam.pk])

    def api_url(self, attempt, question):
        return reverse('api:answer_detail', args=[attempt.pk, question.pk])

    def patch(self, attempt, question, payload):
        return self.client.patch(
            self.api_url(attempt, question), data=json.dumps(payload), content_type='application/json',
        )

    def staff_only_requests(self):
        """Every (method, url, data) an admin-only view exposes."""
        exam_id, q_id = self.exam.pk, self.q1.pk
        question_data = {
            'text': 'Injected', 'option_a': 'a', 'option_b': 'b', 'option_c': 'c', 'option_d': 'd',
            'correct_option': 'A',
        }
        return [
            ('get', reverse('exams:create'), None),
            ('post', reverse('exams:create'), {'title': 'Injected exam', 'duration_minutes': 10,
                                              'start_at': '2030-01-01T10:00', 'end_at': '2030-01-01T12:00'}),
            ('get', reverse('exams:questions', args=[exam_id]), None),
            ('get', reverse('exams:question_create', args=[exam_id]), None),
            ('post', reverse('exams:question_create', args=[exam_id]), question_data),
            ('get', reverse('exams:question_edit', args=[exam_id, q_id]), None),
            ('post', reverse('exams:question_edit', args=[exam_id, q_id]), dict(question_data, text='Tampered')),
            ('get', reverse('exams:question_delete', args=[exam_id, q_id]), None),
            ('post', reverse('exams:question_delete', args=[exam_id, q_id]), {}),
            ('get', reverse('accounts:admin_dashboard'), None),
        ]


class RoleAuthorizationTests(SecurityTestCase):
    """SEC-REQ-02: unauthorized roles are rejected on the server, not just hidden in the UI."""

    def test_student_gets_403_on_every_staff_endpoint_and_nothing_changes(self):
        self.client.force_login(self.student)
        for method, url, data in self.staff_only_requests():
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data or {})
                self.assertEqual(response.status_code, 403)
        self.assertEqual(Exam.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 2)
        self.q1.refresh_from_db()
        self.assertEqual(self.q1.text, '2+2?')

    def test_anonymous_user_is_redirected_to_login_on_every_protected_page(self):
        protected = [(m, u, d) for m, u, d in self.staff_only_requests()]
        protected += [
            ('get', self.take_url, None),
            ('post', self.take_url, {'current': '1', 'answer': 'A'}),
            ('get', self.submit_url, None),
            ('post', self.submit_url, {'confirmed': 'yes'}),
            ('get', reverse('exams:available'), None),
            ('get', reverse('accounts:student_dashboard'), None),
        ]
        for method, url, data in protected:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data or {})
                self.assertEqual(response.status_code, 302)
                self.assertIn('/accounts/login/', response.url)
        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Attempt.objects.count(), 0)

    def test_anonymous_api_call_gets_401_with_stable_error_code(self):
        attempt = Attempt.objects.create(exam=self.exam, student=self.student)
        url = self.api_url(attempt, self.q1)
        for method in ('get', 'patch', 'post', 'put', 'delete'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()['error']['code'], 'AUTHENTICATION_REQUIRED')

    def test_admin_cannot_start_or_submit_an_attempt(self):
        self.client.force_login(self.admin)
        for method, url, data in [
            ('get', self.take_url, None),
            ('post', self.take_url, {'current': '1', 'answer': 'A'}),
            ('get', self.submit_url, None),
            ('post', self.submit_url, {'confirmed': 'yes'}),
        ]:
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(self.client, method)(url, data or {}).status_code, 403)
        self.assertEqual(Attempt.objects.count(), 0)

    def test_admin_can_still_read_exam_metadata_as_json(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.take_url, {'format': 'json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Security exam')
        self.assertEqual(Attempt.objects.count(), 0)

    def test_admin_cannot_save_answers_through_the_api(self):
        attempt = Attempt.objects.create(exam=self.exam, student=self.student)
        self.client.force_login(self.admin)
        response = self.patch(attempt, self.q1, {'selectedOption': 'A'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error']['code'], 'FORBIDDEN')
        self.assertEqual(Answer.objects.count(), 0)

    def test_student_cannot_use_the_django_admin_site(self):
        self.client.force_login(self.student)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_exam_list_offers_start_button_to_students_but_not_to_admins(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(reverse('exams:available')), 'Start Exam')
        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get(reverse('exams:available')), 'Start Exam')


class OwnershipTests(SecurityTestCase):
    """SEC-REQ-02: a student can only touch their own attempt (design 3.6 'Object ownership')."""

    def setUp(self):
        self.attempt = Attempt.objects.create(exam=self.exam, student=self.student)
        Answer.objects.create(attempt=self.attempt, question=self.q1, selected_option='A')

    def test_other_student_cannot_patch_a_foreign_attempt(self):
        self.client.force_login(self.other)
        for question in (self.q1, self.q2):
            with self.subTest(question=question.pk):
                response = self.patch(self.attempt, question, {'selectedOption': 'D', 'markedForReview': True})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['error']['code'], 'FORBIDDEN')
        self.assertEqual(Answer.objects.count(), 1)
        answer = Answer.objects.get()
        self.assertEqual((answer.selected_option, answer.marked_for_review), ('A', False))

    def test_forbidden_response_leaks_no_attempt_data(self):
        self.client.force_login(self.other)
        response = self.patch(self.attempt, self.q1, {'selectedOption': 'D'})
        body = response.content.decode()
        self.assertEqual(set(response.json()), {'error'})
        self.assertIn('requestId', response.json()['error'])
        for leaked in ('selectedOption', 'markedForReview', 'sec-student', '"A"'):
            self.assertNotIn(leaked, body)

    def test_unknown_attempt_returns_404_not_a_server_error(self):
        self.client.force_login(self.other)
        response = self.client.patch(
            reverse('api:answer_detail', args=[999999, self.q1.pk]),
            data=json.dumps({'selectedOption': 'A'}), content_type='application/json',
        )
        self.assertEqual((response.status_code, response.json()['error']['code']), (404, 'ATTEMPT_NOT_FOUND'))

    def test_other_students_submission_never_touches_a_foreign_attempt(self):
        self.client.force_login(self.other)
        self.client.post(self.submit_url, {'confirmed': 'yes'})
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, Attempt.IN_PROGRESS)
        self.assertIsNone(self.attempt.score)
        self.assertEqual(Attempt.objects.get(student=self.other).status, Attempt.SUBMITTED)

    def test_exam_page_never_shows_another_students_saved_answer(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(self.take_url), 'value="A" checked')
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.take_url), 'value="A" checked')
        self.assertEqual(self.attempt.answers.count(), 1)

    def test_owner_can_still_save_their_own_answer(self):
        self.client.force_login(self.student)
        response = self.patch(self.attempt, self.q2, {'selectedOption': 'B'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.attempt.answers.count(), 2)


class PostSubmitMutationTests(SecurityTestCase):
    """SEC-REQ-03: a finalized attempt is immutable (design 3.6 'Submission integrity', 4.2)."""

    def setUp(self):
        self.attempt = Attempt.objects.create(exam=self.exam, student=self.student)
        Answer.objects.create(attempt=self.attempt, question=self.q1, selected_option='A')
        self.client.force_login(self.student)
        self.client.post(self.submit_url, {'confirmed': 'yes'})
        self.attempt.refresh_from_db()
        self.assertEqual((self.attempt.status, self.attempt.score), (Attempt.SUBMITTED, 1))
        self.assertIsNotNone(self.attempt.submitted_at)

    def assertAttemptUntouched(self):
        self.attempt.refresh_from_db()
        self.assertEqual((self.attempt.status, self.attempt.score), (Attempt.SUBMITTED, 1))
        self.assertEqual(self.attempt.answers.count(), 1)
        answer = self.attempt.answers.get()
        self.assertEqual((answer.selected_option, answer.marked_for_review), ('A', False))

    def test_api_answer_update_after_submit_returns_409(self):
        response = self.patch(self.attempt, self.q1, {'selectedOption': 'B'})
        self.assertEqual((response.status_code, response.json()['error']['code']), (409, 'ATTEMPT_ALREADY_FINALIZED'))
        self.assertAttemptUntouched()

    def test_api_review_flag_and_new_answer_after_submit_return_409(self):
        self.assertEqual(self.patch(self.attempt, self.q1, {'markedForReview': True}).status_code, 409)
        self.assertEqual(self.patch(self.attempt, self.q2, {'selectedOption': 'B'}).status_code, 409)
        self.assertAttemptUntouched()

    def test_web_form_post_after_submit_returns_409(self):
        response = self.client.post(self.take_url, {'current': '1', 'answer': 'B', 'mark_for_review': 'on'})
        self.assertEqual(response.status_code, 409)
        self.assertAttemptUntouched()

    def test_second_submit_returns_409_and_keeps_score_and_timestamp(self):
        submitted_at = self.attempt.submitted_at
        response = self.client.post(self.submit_url, {'confirmed': 'yes'})
        self.assertEqual(response.status_code, 409)
        self.assertAttemptUntouched()
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.submitted_at, submitted_at)

    def test_unsupported_api_methods_are_rejected_for_the_owner(self):
        url = self.api_url(self.attempt, self.q1)
        for method in ('get', 'post', 'put', 'delete'):
            with self.subTest(method=method):
                self.assertEqual(getattr(self.client, method)(url).status_code, 405)
        self.assertAttemptUntouched()

    def test_model_layer_refuses_answer_changes_after_submit(self):
        answer = self.attempt.answers.get()
        answer.selected_option = 'B'
        with self.assertRaises(ValidationError):
            answer.save()
        with self.assertRaises(ValidationError):
            Answer.objects.create(attempt=self.attempt, question=self.q2, selected_option='B')
        self.assertAttemptUntouched()

    def test_editing_the_answer_key_after_submit_does_not_change_the_stored_score(self):
        self.q1.correct_option = 'C'
        self.q1.save()
        self.assertAttemptUntouched()

    def test_confirmation_is_required_to_finalize(self):
        fresh = Attempt.objects.create(exam=self.exam, student=self.other)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.submit_url, {}).status_code, 400)
        self.assertEqual(self.client.post(self.submit_url, {'confirmed': 'no'}).status_code, 400)
        fresh.refresh_from_db()
        self.assertEqual(fresh.status, Attempt.IN_PROGRESS)
