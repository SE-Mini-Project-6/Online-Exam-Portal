"""Tests for answer autosave (FR-07, NFR-02): PATCH /api/v1/attempts/{id}/answers/{questionId}."""
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
class AnswerAutosaveTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.student = users.objects.create_user(username='auto-student', password='StudentPass123!')
        self.other = users.objects.create_user(username='auto-other', password='StudentPass123!')
        now = timezone.now()
        self.exam = Exam.objects.create(
            title='Autosave Exam', duration_minutes=30,
            start_at=now - timedelta(minutes=10), end_at=now + timedelta(hours=1),
        )
        self.questions = [
            Question.objects.create(
                exam=self.exam, text=f'Autosave question {i}',
                option_a='a', option_b='b', option_c='c', option_d='d', correct_option='A',
            )
            for i in range(1, 4)
        ]
        self.attempt = Attempt.objects.create(exam=self.exam, student=self.student)
        self.take_url = reverse('exams:take', args=[self.exam.id])
        self.client.force_login(self.student)

    def patch(self, payload, question=None, attempt=None):
        url = reverse('api:answer_detail', args=[(attempt or self.attempt).id, (question or self.questions[0]).id])
        return self.client.patch(url, data=json.dumps(payload), content_type='application/json')

    def test_autosave_persists_answer_and_review_flag_independently(self):
        response = self.patch({'selectedOption': 'C'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['selectedOption'], 'C')
        self.assertEqual(body['displayState'], 'ANSWERED')
        self.assertIn('Server-Timing', response)

        body = self.patch({'markedForReview': True}).json()
        self.assertEqual(body['selectedOption'], 'C')  # review change must not erase the answer
        self.assertEqual(body['displayState'], 'ANSWERED_MARKED_FOR_REVIEW')
        answer = Answer.objects.get()
        self.assertEqual((answer.selected_option, answer.marked_for_review), ('C', True))
        self.assertIsNotNone(answer.saved_at)

    def test_answer_can_be_changed_and_refresh_preserves_it(self):
        self.patch({'selectedOption': 'B'})
        self.patch({'selectedOption': 'D'})
        self.assertEqual(Answer.objects.count(), 1)
        self.assertContains(self.client.get(self.take_url), 'value="D" checked')

    def test_requires_login_and_ownership(self):
        self.client.logout()
        self.assertEqual(self.patch({'selectedOption': 'A'}).status_code, 401)
        self.client.force_login(self.other)
        response = self.patch({'selectedOption': 'A'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error']['code'], 'FORBIDDEN')
        self.assertEqual(Answer.objects.count(), 0)

    def test_invalid_input_is_rejected_with_error_codes(self):
        self.assertEqual(self.patch({'selectedOption': 'Z'}).json()['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(self.patch({}).status_code, 400)
        other_exam = Exam.objects.create(
            title='Other', duration_minutes=10, start_at=self.exam.start_at, end_at=self.exam.end_at,
        )
        foreign = Question.objects.create(
            exam=other_exam, text='x', option_a='a', option_b='b', option_c='c', option_d='d', correct_option='A',
        )
        response = self.patch({'selectedOption': 'A'}, question=foreign)
        self.assertEqual((response.status_code, response.json()['error']['code']), (404, 'QUESTION_NOT_FOUND'))
        self.assertEqual(Answer.objects.count(), 0)

    def test_saves_blocked_after_finalization_and_outside_window(self):
        self.patch({'selectedOption': 'A'})
        self.attempt.status = Attempt.SUBMITTED
        self.attempt.save()
        response = self.patch({'selectedOption': 'B'})
        self.assertEqual((response.status_code, response.json()['error']['code']), (409, 'ATTEMPT_ALREADY_FINALIZED'))
        self.assertEqual(Answer.objects.get().selected_option, 'A')

        self.attempt.status = Attempt.IN_PROGRESS
        self.attempt.save()
        self.exam.end_at = timezone.now() - timedelta(minutes=1)
        self.exam.save()
        response = self.patch({'selectedOption': 'B'})
        self.assertEqual((response.status_code, response.json()['error']['code']), (403, 'EXAM_NOT_AVAILABLE'))

    def test_exam_page_is_wired_for_autosave_and_latency_command_runs(self):
        self.assertContains(self.client.get(self.take_url), 'data-autosave-url')
        out = StringIO()
        call_command('measure_autosave', count=10, stdout=out)
        self.assertIn('p95', out.getvalue())
        self.assertFalse(Exam.objects.filter(title__startswith='Latency check').exists())
