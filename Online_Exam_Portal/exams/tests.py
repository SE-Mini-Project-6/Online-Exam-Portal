from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import ExamForm
from .models import Exam


@override_settings(SECURE_SSL_REDIRECT=False)
class ExamConfigurationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username='exam-admin',
            password='AdminPass123!',
            is_staff=True,
        )
        self.student = user_model.objects.create_user(
            username='exam-student',
            password='StudentPass123!',
        )
        self.start_at = timezone.now() + timedelta(days=1)
        self.end_at = self.start_at + timedelta(hours=2)

    def exam_data(self, **overrides):
        data = {
            'title': 'Mathematics Midterm',
            'duration_minutes': 90,
            'start_at': self.start_at.strftime('%Y-%m-%dT%H:%M'),
            'end_at': self.end_at.strftime('%Y-%m-%dT%H:%M'),
        }
        data.update(overrides)
        return data

    def test_valid_exam_configuration_is_saved(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('exams:create'),
            self.exam_data(),
        )

        self.assertRedirects(response, reverse('accounts:admin_dashboard'))
        exam = Exam.objects.get()
        self.assertEqual(exam.title, 'Mathematics Midterm')
        self.assertEqual(exam.duration_minutes, 90)

    def test_end_before_start_is_rejected(self):
        form = ExamForm(self.exam_data(
            end_at=(self.start_at - timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M'),
        ))

        self.assertFalse(form.is_valid())
        self.assertIn('End time must be after the start time.', form.errors['end_at'])
        self.assertEqual(Exam.objects.count(), 0)

    def test_equal_start_and_end_is_rejected(self):
        form = ExamForm(self.exam_data(
            end_at=self.start_at.strftime('%Y-%m-%dT%H:%M'),
        ))

        self.assertFalse(form.is_valid())
        self.assertIn('End time must be after the start time.', form.errors['end_at'])

    def test_non_positive_duration_is_rejected(self):
        form = ExamForm(self.exam_data(duration_minutes=0))

        self.assertFalse(form.is_valid())
        self.assertIn('duration_minutes', form.errors)

    def test_empty_duration_is_handled_gracefully(self):
        form = ExamForm(self.exam_data(duration_minutes=''))

        self.assertFalse(form.is_valid())
        self.assertIn('duration_minutes', form.errors)

    def test_duration_exceeding_window_is_rejected(self):
        form = ExamForm(self.exam_data(
            duration_minutes=150,  # window is 120 minutes (2 hours)
        ))

        self.assertFalse(form.is_valid())
        self.assertIn('Exam duration cannot exceed the availability window.', form.errors['duration_minutes'])

    def test_saved_exam_appears_on_admin_dashboard(self):
        Exam.objects.create(
            title='Existing Exam',
            duration_minutes=30,
            start_at=self.start_at,
            end_at=self.end_at,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('accounts:admin_dashboard'))

        self.assertContains(response, 'Existing Exam')
        self.assertContains(response, '30 minutes')

    def test_students_cannot_create_exams(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse('exams:create'))

        self.assertEqual(response.status_code, 403)

    def test_anonymous_users_redirected_to_login(self):
        response = self.client.get(reverse('exams:create'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_admin_can_access_exam_create_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('exams:create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create exam')
        self.assertIsInstance(response.context['form'], ExamForm)

    def test_exam_str_returns_title(self):
        exam = Exam(title='Physics Final')
        self.assertEqual(str(exam), 'Physics Final')

    def test_model_clean_validation(self):
        # End before start
        exam = Exam(
            title='Test Exam',
            duration_minutes=60,
            start_at=self.start_at,
            end_at=self.start_at - timedelta(hours=1),
        )
        with self.assertRaises(ValidationError) as ctx:
            exam.clean()
        self.assertIn('end_at', ctx.exception.message_dict)

        # Duration exceeding window
        exam_long = Exam(
            title='Test Exam 2',
            duration_minutes=180,
            start_at=self.start_at,
            end_at=self.start_at + timedelta(hours=1),
        )
        with self.assertRaises(ValidationError) as ctx:
            exam_long.clean()
        self.assertIn('duration_minutes', ctx.exception.message_dict)
