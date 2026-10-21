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


@override_settings(SECURE_SSL_REDIRECT=False)
class ExamAvailabilityAndWindowEnforcementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.student = user_model.objects.create_user(
            username='student-alice',
            password='StudentPass123!',
        )
        self.admin = user_model.objects.create_user(
            username='admin-bob',
            password='AdminPass123!',
            is_staff=True,
        )
        self.now = timezone.now()

        # Active exam: started 30 mins ago, ends in 30 mins
        self.active_exam = Exam.objects.create(
            title='Active Chemistry Exam',
            duration_minutes=45,
            start_at=self.now - timedelta(minutes=30),
            end_at=self.now + timedelta(minutes=30),
        )
        # Upcoming exam: starts tomorrow
        self.upcoming_exam = Exam.objects.create(
            title='Upcoming Physics Exam',
            duration_minutes=60,
            start_at=self.now + timedelta(days=1),
            end_at=self.now + timedelta(days=1, hours=2),
        )
        # Expired exam: ended yesterday
        self.expired_exam = Exam.objects.create(
            title='Expired Biology Exam',
            duration_minutes=30,
            start_at=self.now - timedelta(days=2),
            end_at=self.now - timedelta(days=2) + timedelta(hours=1),
        )

    def test_student_dashboard_displays_exams_and_scheduled_times(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('accounts:student_dashboard'))

        self.assertEqual(response.status_code, 200)
        # Scheduled exams appear
        self.assertContains(response, 'Active Chemistry Exam')
        self.assertContains(response, 'Upcoming Physics Exam')
        self.assertContains(response, 'Expired Biology Exam')
        # Durations appear
        self.assertContains(response, '45 minutes')
        self.assertContains(response, '60 minutes')
        self.assertContains(response, '30 minutes')
        # Scheduled times are displayed
        self.assertContains(response, self.active_exam.start_at.strftime('%Y'))
        self.assertContains(response, self.upcoming_exam.start_at.strftime('%Y'))
        self.assertContains(response, self.expired_exam.start_at.strftime('%Y'))

    def test_student_dashboard_displays_appropriate_status_badges(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('accounts:student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available Now')
        self.assertContains(response, 'Upcoming')
        self.assertContains(response, 'Closed')

        # Active exam has enabled link to start
        take_url = reverse('exams:take', args=[self.active_exam.id])
        self.assertContains(response, f'href="{take_url}"')

    def test_early_access_is_blocked_on_server_with_403(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('exams:take', args=[self.upcoming_exam.id]))

        self.assertEqual(response.status_code, 403)
        self.assertIn('not started yet', response.content.decode())
        self.assertIn('Early access is blocked', response.content.decode())

    def test_expired_access_is_blocked_on_server_with_403(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('exams:take', args=[self.expired_exam.id]))

        self.assertEqual(response.status_code, 403)
        self.assertIn('expired', response.content.decode().lower())
        self.assertIn('Access is blocked', response.content.decode())

    def test_active_exam_access_is_granted_with_200(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('exams:take', args=[self.active_exam.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Chemistry Exam')
        self.assertContains(response, '45 minutes')
        self.assertContains(response, 'Active Availability Window')

    def test_detail_url_route_enforces_windows(self):
        self.client.force_login(self.student)

        # Early access via detail route -> 403
        resp_early = self.client.get(reverse('exams:detail', args=[self.upcoming_exam.id]))
        self.assertEqual(resp_early.status_code, 403)

        # Expired access via detail route -> 403
        resp_expired = self.client.get(reverse('exams:detail', args=[self.expired_exam.id]))
        self.assertEqual(resp_expired.status_code, 403)

        # Active access via detail route -> 200
        resp_active = self.client.get(reverse('exams:detail', args=[self.active_exam.id]))
        self.assertEqual(resp_active.status_code, 200)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse('exams:take', args=[self.active_exam.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_nonexistent_exam_returns_404(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('exams:take', args=[99999]))

        self.assertEqual(response.status_code, 404)

    def test_available_exams_view_renders_correctly(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('exams:available'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Chemistry Exam')
        self.assertContains(response, 'Upcoming Physics Exam')
        self.assertContains(response, 'Expired Biology Exam')
        self.assertContains(response, 'Available Now')

    def test_available_exams_json_api(self):
        self.client.force_login(self.student)
        response = self.client.get(
            reverse('exams:available'),
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('exams', data)
        self.assertEqual(len(data['exams']), 3)

        statuses = {item['title']: item['status'] for item in data['exams']}
        self.assertEqual(statuses['Active Chemistry Exam'], 'available')
        self.assertEqual(statuses['Upcoming Physics Exam'], 'upcoming')
        self.assertEqual(statuses['Expired Biology Exam'], 'expired')

    def test_exam_window_enforcement_json_api(self):
        self.client.force_login(self.student)

        # Early access JSON -> 403
        early_resp = self.client.get(
            reverse('exams:take', args=[self.upcoming_exam.id]),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(early_resp.status_code, 403)
        self.assertEqual(early_resp.json()['status'], 'upcoming')

        # Expired access JSON -> 403
        expired_resp = self.client.get(
            reverse('exams:take', args=[self.expired_exam.id]),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(expired_resp.status_code, 403)
        self.assertEqual(expired_resp.json()['status'], 'expired')

        # Active access JSON -> 200
        active_resp = self.client.get(
            reverse('exams:take', args=[self.active_exam.id]),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(active_resp.status_code, 200)
        self.assertEqual(active_resp.json()['status'], 'available')

    def test_exam_model_availability_methods(self):
        # Active exam tests
        self.assertTrue(self.active_exam.is_available(self.now))
        self.assertFalse(self.active_exam.is_upcoming(self.now))
        self.assertFalse(self.active_exam.is_expired(self.now))
        self.assertEqual(self.active_exam.get_status(self.now), 'available')
        self.assertEqual(self.active_exam.get_status_label(self.now), 'Available Now')

        # Upcoming exam tests
        self.assertFalse(self.upcoming_exam.is_available(self.now))
        self.assertTrue(self.upcoming_exam.is_upcoming(self.now))
        self.assertFalse(self.upcoming_exam.is_expired(self.now))
        self.assertEqual(self.upcoming_exam.get_status(self.now), 'upcoming')
        self.assertEqual(self.upcoming_exam.get_status_label(self.now), 'Upcoming')

        # Expired exam tests
        self.assertFalse(self.expired_exam.is_available(self.now))
        self.assertFalse(self.expired_exam.is_upcoming(self.now))
        self.assertTrue(self.expired_exam.is_expired(self.now))
        self.assertEqual(self.expired_exam.get_status(self.now), 'expired')
        self.assertEqual(self.expired_exam.get_status_label(self.now), 'Closed')

        # Properties default to current time
        self.assertTrue(self.upcoming_exam.is_currently_upcoming)
        self.assertTrue(self.expired_exam.is_currently_expired)

