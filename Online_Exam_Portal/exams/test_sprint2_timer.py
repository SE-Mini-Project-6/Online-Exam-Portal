"""Sprint 2 #22 tests: fixed server deadline and once-only finalization."""
import json
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Answer, Attempt, Exam, Question


@override_settings(SECURE_SSL_REDIRECT=False)
class ServerTimerTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(username='timer-student', password='SafePass123!')
        now = timezone.now()
        self.exam = Exam.objects.create(title='Timer Exam', duration_minutes=10,
            start_at=now - timedelta(minutes=5), end_at=now + timedelta(hours=1))
        self.question = Question.objects.create(exam=self.exam, text='Correct?',
            option_a='yes', option_b='no', option_c='maybe', option_d='unknown', correct_option='A')
        self.take = reverse('exams:take', args=[self.exam.pk])
        self.submit = reverse('exams:submit', args=[self.exam.pk])
        self.client.force_login(self.student)

    def attempt(self):
        return Attempt.objects.get(student=self.student, exam=self.exam)

    def expire(self, attempt):
        attempt.started_at = timezone.now() - timedelta(minutes=12)
        attempt.deadline_at = timezone.now() - timedelta(minutes=2)
        attempt.save(update_fields=['started_at', 'deadline_at'])

    def test_first_access_stores_deadline_which_refresh_cannot_extend(self):
        self.assertContains(self.client.get(self.take), 'id="exam-countdown"')
        initial = self.attempt()
        self.assertEqual(initial.deadline_at, initial.started_at + timedelta(minutes=10))
        deadline = initial.deadline_at
        self.client.get(self.take)
        self.attempt().refresh_from_db()
        self.assertEqual(self.attempt().deadline_at, deadline)

    def test_exam_window_caps_stored_deadline(self):
        self.exam.end_at = timezone.now() + timedelta(minutes=2)
        self.exam.save()
        self.client.get(self.take)
        self.assertEqual(self.attempt().deadline_at, self.exam.end_at)

    def test_expiry_finalizes_score_and_locks_answer_once(self):
        self.client.get(self.take)
        attempt = self.attempt()
        Answer.objects.update_or_create(attempt=attempt, question=self.question, defaults={'selected_option': 'A'})
        self.expire(attempt)
        self.assertContains(self.client.get(self.take), 'Exam submitted successfully')
        attempt.refresh_from_db()
        self.assertEqual((attempt.status, attempt.score), (Attempt.SUBMITTED, 1))
        submitted_at = attempt.submitted_at
        self.assertEqual(self.client.post(self.take, {'current': 1, 'answer': 'B'}).status_code, 409)
        self.assertEqual(self.client.post(self.submit, {'confirmed': 'yes'}).status_code, 409)
        attempt.refresh_from_db()
        self.assertEqual(attempt.submitted_at, submitted_at)
        self.assertEqual(Answer.objects.get(attempt=attempt).selected_option, 'A')

    def test_late_patch_is_denied_and_cannot_change_deadline(self):
        self.client.get(self.take)
        attempt = self.attempt()
        self.expire(attempt)
        url = reverse('api:answer_detail', args=[attempt.pk, self.question.pk])
        response = self.client.patch(url, data=json.dumps({'selectedOption': 'A'}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'ATTEMPT_ALREADY_FINALIZED')
        self.assertFalse(Answer.objects.filter(attempt=attempt, selected_option__isnull=False).exists())
        attempt.refresh_from_db()
        self.assertLess(attempt.deadline_at, timezone.now())

    def test_repeat_manual_submission_does_not_regrade(self):
        self.client.post(self.take, {'current': 1, 'answer': 'A', 'goto': 1})
        self.assertEqual(self.client.post(self.submit, {'confirmed': 'yes'}).status_code, 302)
        original = self.attempt()
        self.assertEqual(original.score, 1)
        self.assertEqual(self.client.post(self.submit, {'confirmed': 'yes'}).status_code, 409)
        self.assertEqual(self.attempt().submitted_at, original.submitted_at)

    def test_scheduled_sweep_closes_abandoned_attempt_once(self):
        self.client.get(self.take)
        self.expire(self.attempt())
        out = StringIO()
        call_command('finalize_expired_attempts', stdout=out)
        self.assertIn('Finalized 1', out.getvalue())
        self.assertEqual(self.attempt().status, Attempt.SUBMITTED)
        out = StringIO()
        call_command('finalize_expired_attempts', stdout=out)
        self.assertIn('Finalized 0', out.getvalue())

