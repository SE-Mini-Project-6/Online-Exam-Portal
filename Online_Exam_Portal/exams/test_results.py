"""Student results page visibility (FR-14, FR-16)."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Attempt, Exam, Question


@override_settings(SECURE_SSL_REDIRECT=False)
class StudentResultVisibilityTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.alice = users.objects.create_user(username='res-alice', password='StudentPass123!')
        self.bob = users.objects.create_user(username='res-bob', password='StudentPass123!')
        self.admin = users.objects.create_user(username='res-admin', password='AdminPass123!', is_staff=True)
        now = timezone.now()
        self.exam = Exam.objects.create(
            title='Results Exam', duration_minutes=30,
            start_at=now - timedelta(hours=2), end_at=now + timedelta(hours=1),
        )
        for i in range(4):
            Question.objects.create(
                exam=self.exam, text=f'Q{i}', option_a='a', option_b='b',
                option_c='c', option_d='d', correct_option='A',
            )
        self.url = reverse('exams:result', args=[self.exam.id])

    def submit(self, student, score):
        return Attempt.objects.create(
            exam=self.exam, student=student, status=Attempt.SUBMITTED,
            score=score, submitted_at=timezone.now(),
        )

    def test_unreleased_result_hides_the_score(self):
        self.submit(self.alice, 3)
        self.client.force_login(self.alice)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'not been released')
        self.assertNotContains(response, 'Your score')
        self.assertNotContains(response, '3 of 4')

    def test_released_result_shows_the_score(self):
        self.submit(self.alice, 3)
        self.exam.results_released = True
        self.exam.save()
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(self.url), '3 of 4')

    def test_releasing_and_unreleasing_toggles_visibility(self):
        self.submit(self.alice, 3)
        self.client.force_login(self.alice)
        Exam.objects.filter(pk=self.exam.pk).update(results_released=True)
        self.assertContains(self.client.get(self.url), '3 of 4')
        Exam.objects.filter(pk=self.exam.pk).update(results_released=False)
        self.assertNotContains(self.client.get(self.url), '3 of 4')

    def test_student_only_ever_sees_their_own_score(self):
        self.submit(self.alice, 3)
        self.submit(self.bob, 1)
        self.exam.results_released = True
        self.exam.save()
        self.client.force_login(self.bob)
        # Nothing in the request can select another student's result.
        response = self.client.get(self.url, {'student': self.alice.id, 'attempt': Attempt.objects.get(student=self.alice).id})
        self.assertContains(response, '1 of 4')
        self.assertNotContains(response, '3 of 4')

    def test_no_score_before_submission(self):
        Attempt.objects.create(exam=self.exam, student=self.alice, status=Attempt.IN_PROGRESS)
        self.exam.results_released = True
        self.exam.save()
        self.client.force_login(self.alice)
        response = self.client.get(self.url)
        self.assertContains(response, 'no result yet')
        self.assertNotContains(response, 'Your score')

    def test_anonymous_and_staff_are_redirected(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertIn('/accounts/login/', self.client.get(self.url).url)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(self.url), reverse('accounts:admin_dashboard'))
