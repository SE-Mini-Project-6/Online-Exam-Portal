from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from exams.models import Attempt, Exam, Question


@override_settings(SECURE_SSL_REDIRECT=False)
class AdminSubmissionsDashboardTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username='submissions-admin', password='AdminPass123!', is_staff=True,
        )
        self.submitted_student = user_model.objects.create_user(username='alice', password='StudentPass123!')
        self.progress_student = user_model.objects.create_user(username='bob', password='StudentPass123!')
        self.unstarted_student = user_model.objects.create_user(username='carol', password='StudentPass123!')
        now = timezone.now()
        self.exam = Exam.objects.create(
            title='Biology Final', duration_minutes=60,
            start_at=now - timedelta(minutes=10), end_at=now + timedelta(hours=1),
        )
        self.other_exam = Exam.objects.create(
            title='Chemistry Final', duration_minutes=60,
            start_at=now - timedelta(minutes=10), end_at=now + timedelta(hours=1),
        )
        for number in range(2):
            Question.objects.create(
                exam=self.exam, text=f'Question {number + 1}',
                option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A',
            )
        self.submitted_attempt = Attempt.objects.create(
            exam=self.exam, student=self.submitted_student, status=Attempt.SUBMITTED,
            score=1, submitted_at=now,
        )
        self.progress_attempt = Attempt.objects.create(
            exam=self.exam, student=self.progress_student, status=Attempt.IN_PROGRESS,
        )
        self.url = reverse('accounts:admin_submissions')

    def test_staff_sees_selected_exam_roster_states_and_submitted_score(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url, {'exam': self.exam.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Biology Final')
        self.assertContains(response, 'alice')
        self.assertContains(response, 'Submitted')
        self.assertContains(response, '1 / 2')
        self.assertContains(response, 'bob')
        self.assertContains(response, 'In progress')
        self.assertContains(response, 'carol')
        self.assertContains(response, 'Not started')
        self.assertEqual(
            {row['student'].username for row in response.context['roster']},
            {'alice', 'bob', 'carol'},
        )

    def test_exam_selection_excludes_students_with_only_another_exam_attempt(self):
        Attempt.objects.create(
            exam=self.other_exam, student=self.submitted_student, status=Attempt.IN_PROGRESS,
        )
        self.client.force_login(self.admin)

        response = self.client.get(self.url, {'exam': self.other_exam.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_exam'], self.other_exam)
        self.assertEqual(len(response.context['roster']), 3)
        self.assertTrue(all(row['attempt'] is None or row['attempt'].exam_id == self.other_exam.pk
                            for row in response.context['roster']))

    def test_student_is_forbidden_and_anonymous_user_is_redirected(self):
        student = get_user_model().objects.create_user(username='student', password='StudentPass123!')

        self.client.force_login(student)
        forbidden = self.client.get(self.url, {'exam': self.exam.pk})
        self.assertEqual(forbidden.status_code, 403)

        self.client.logout()
        anonymous = self.client.get(self.url, {'exam': self.exam.pk})
        self.assertEqual(anonymous.status_code, 302)
        self.assertIn('/accounts/login/', anonymous.url)

    def test_admin_dashboard_links_to_submission_roster(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('accounts:admin_dashboard'))

        self.assertContains(response, reverse('accounts:admin_submissions'))
        self.assertContains(response, f'?exam={self.exam.pk}')

    def test_results_release_requires_staff_post_and_completed_exam(self):
        url = reverse('accounts:release_exam_results', args=[self.exam.pk])
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.exam.refresh_from_db()
        self.assertFalse(self.exam.results_released)

        self.progress_attempt.delete()
        self.exam.end_at = timezone.now() - timedelta(minutes=1)
        self.exam.save()
        self.assertRedirects(self.client.post(url), f'{self.url}?exam={self.exam.pk}')
        self.exam.refresh_from_db()
        self.assertTrue(self.exam.results_released)

    def test_results_cannot_be_released_with_open_attempt_or_by_student(self):
        self.exam.end_at = timezone.now() - timedelta(minutes=1)
        self.exam.save()
        self.client.force_login(self.admin)
        self.client.post(reverse('accounts:release_exam_results', args=[self.exam.pk]))
        self.exam.refresh_from_db()
        self.assertFalse(self.exam.results_released)
        self.client.force_login(self.submitted_student)
        self.assertEqual(self.client.post(reverse('accounts:release_exam_results', args=[self.exam.pk])).status_code, 403)
