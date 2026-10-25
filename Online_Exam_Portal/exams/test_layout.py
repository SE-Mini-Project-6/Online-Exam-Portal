"""Tests for the shared layout and role-based routing (EI-03, NFR-03)."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from exams.models import Exam, Question


@override_settings(SECURE_SSL_REDIRECT=False)
class SharedLayoutAndRoutingTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.admin = users.objects.create_user(username='layout-admin', password='AdminPass123!', is_staff=True)
        self.student = users.objects.create_user(username='layout-student', password='StudentPass123!')
        now = timezone.now()
        self.exam = Exam.objects.create(
            title='Layout Exam', duration_minutes=30,
            start_at=now - timedelta(minutes=10), end_at=now + timedelta(hours=1),
        )
        Question.objects.create(
            exam=self.exam, text='Layout question', option_a='a', option_b='b',
            option_c='c', option_d='d', correct_option='A',
        )

    def student_pages(self):
        return [
            reverse('accounts:student_dashboard'),
            reverse('exams:list'),
            reverse('exams:take', args=[self.exam.id]),
        ]

    def test_student_pages_have_no_admin_links(self):
        self.client.force_login(self.student)
        admin_urls = [
            reverse('exams:create'), reverse('accounts:admin_dashboard'),
            reverse('exams:questions', args=[self.exam.id]),
        ]
        for url in self.student_pages():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            for admin_url in admin_urls:
                self.assertNotContains(response, f'href="{admin_url}"', msg_prefix=url)
            self.assertContains(response, 'Available Exams')

    def test_admin_pages_show_admin_navigation(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertContains(response, f'href="{reverse("exams:create")}"')
        self.assertContains(response, 'id="role-tag">Admin<')
        self.assertNotContains(response, f'href="{reverse("exams:list")}"')

    def test_pages_share_one_base_layout_with_single_logout(self):
        self.client.force_login(self.student)
        for url in self.student_pages():
            response = self.client.get(url)
            self.assertTemplateUsed(response, 'base.html')
            self.assertContains(response, 'id="logout-button"', count=1)
        self.client.force_login(self.admin)
        for url in [reverse('accounts:admin_dashboard'), reverse('exams:create'),
                    reverse('exams:questions', args=[self.exam.id])]:
            response = self.client.get(url)
            self.assertTemplateUsed(response, 'base.html')
            self.assertContains(response, 'id="logout-button"', count=1)

    def test_anonymous_visitor_sees_only_login_links(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Student Login')
        self.assertNotContains(response, 'id="logout-button"')
        self.assertNotContains(response, f'href="{reverse("exams:create")}"')

    def test_each_role_is_routed_to_its_own_dashboard(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse('accounts:student_dashboard')), reverse('accounts:admin_dashboard'))
        self.assertRedirects(self.client.get(reverse('core:home')), reverse('accounts:admin_dashboard'))
        self.client.force_login(self.student)
        self.assertRedirects(self.client.get(reverse('core:home')), reverse('accounts:student_dashboard'))
        self.assertRedirects(self.client.get(reverse('accounts:login')), reverse('accounts:student_dashboard'))

    def test_server_still_blocks_students_from_admin_pages(self):
        self.client.force_login(self.student)
        for url in [reverse('accounts:admin_dashboard'), reverse('exams:create'),
                    reverse('exams:questions', args=[self.exam.id])]:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_login_pages_are_role_specific(self):
        self.assertContains(self.client.get(reverse('accounts:login')), 'Admin Sign In')
        self.assertContains(self.client.get(reverse('accounts:student_login')), 'Student Sign In')
