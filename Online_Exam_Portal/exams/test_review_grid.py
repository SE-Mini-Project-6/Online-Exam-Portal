"""Tests for mark-for-review and the five-state question grid (FR-08, FR-09)."""
import json
import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Answer, Attempt, Exam, Question


@override_settings(SECURE_SSL_REDIRECT=False)
class ReviewAndGridTests(TestCase):
    def setUp(self):
        self.student = get_user_model().objects.create_user(username='grid-student', password='StudentPass123!')
        now = timezone.now()
        self.exam = Exam.objects.create(
            title='Grid Exam', duration_minutes=30,
            start_at=now - timedelta(minutes=10), end_at=now + timedelta(hours=1),
        )
        self.questions = [
            Question.objects.create(
                exam=self.exam, text=f'Grid question {i}',
                option_a='a', option_b='b', option_c='c', option_d='d', correct_option='A',
            )
            for i in range(1, 6)
        ]
        self.take_url = reverse('exams:take', args=[self.exam.id])
        self.client.force_login(self.student)

    def patch(self, number, payload):
        question = self.questions[number - 1]
        attempt = Attempt.objects.get_or_create(exam=self.exam, student=self.student)[0]
        url = reverse('api:answer_detail', args=[attempt.id, question.id])
        return self.client.patch(url, data=json.dumps(payload), content_type='application/json')

    def grid_states(self, response):
        html = response.content.decode()
        found = re.findall(r'<button[^>]*data-number="(\d+)"[^>]*data-state="([A-Z_]+)"', html)
        return {int(n): state for n, state in found}

    def test_display_state_precedence(self):
        attempt = Attempt.objects.create(exam=self.exam, student=self.student)
        question = self.questions[0]
        cases = [
            (dict(), 'NOT_VISITED'),
            (dict(visited=True), 'NOT_ANSWERED'),
            (dict(visited=True, selected_option='B'), 'ANSWERED'),
            (dict(visited=True, marked_for_review=True), 'MARKED_FOR_REVIEW'),
            (dict(visited=True, selected_option='B', marked_for_review=True), 'ANSWERED_MARKED_FOR_REVIEW'),
            (dict(marked_for_review=True), 'MARKED_FOR_REVIEW'),
        ]
        for fields, expected in cases:
            self.assertEqual(Answer(attempt=attempt, question=question, **fields).display_state, expected, fields)

    def test_review_toggles_independently_of_answer(self):
        self.patch(1, {'selectedOption': 'C'})
        body = self.patch(1, {'markedForReview': True}).json()
        self.assertEqual((body['selectedOption'], body['displayState']), ('C', 'ANSWERED_MARKED_FOR_REVIEW'))
        body = self.patch(1, {'selectedOption': 'D'}).json()  # changing the answer keeps the mark
        self.assertEqual((body['selectedOption'], body['markedForReview']), ('D', True))
        body = self.patch(1, {'selectedOption': None}).json()  # clearing the answer keeps the mark
        self.assertEqual(body['displayState'], 'MARKED_FOR_REVIEW')
        body = self.patch(1, {'markedForReview': False}).json()
        self.assertEqual(body['displayState'], 'NOT_ANSWERED')

    def test_grid_shows_all_five_states_and_persists_across_refresh(self):
        self.patch(2, {'selectedOption': 'B'})                                   # answered
        self.patch(3, {'markedForReview': True})                                 # marked, unanswered
        self.patch(4, {'selectedOption': 'A', 'markedForReview': True})          # answered and marked
        # question 1 is opened (not answered); question 5 is never opened
        self.client.get(self.take_url + '?question=1')
        expected = {1: 'NOT_ANSWERED', 2: 'ANSWERED', 3: 'MARKED_FOR_REVIEW',
                    4: 'ANSWERED_MARKED_FOR_REVIEW', 5: 'NOT_VISITED'}
        for _ in range(2):  # a second load is a refresh
            response = self.client.get(self.take_url + '?question=1')
            self.assertEqual(self.grid_states(response), expected)
        self.assertContains(response, 'id="grid-legend"')

    def test_opening_a_question_marks_it_visited(self):
        self.assertEqual(self.grid_states(self.client.get(self.take_url + '?question=3'))[3], 'NOT_ANSWERED')
        self.assertEqual(self.grid_states(self.client.get(self.take_url + '?question=2'))[3], 'NOT_ANSWERED')
        self.assertEqual(self.grid_states(self.client.get(self.take_url + '?question=2'))[5], 'NOT_VISITED')

    def test_form_fallback_can_mark_unanswered_question_for_review(self):
        self.client.post(self.take_url, {'current': 2, 'goto': 3, 'mark_for_review': 'on'})
        answer = Answer.objects.get(question=self.questions[1])
        self.assertEqual((answer.selected_option, answer.marked_for_review), (None, True))
        self.assertEqual(self.grid_states(self.client.get(self.take_url + '?question=1'))[2], 'MARKED_FOR_REVIEW')

    def test_review_cannot_change_after_submission(self):
        self.patch(1, {'markedForReview': True})
        Attempt.objects.update(status=Attempt.SUBMITTED)
        response = self.patch(1, {'markedForReview': False})
        self.assertEqual((response.status_code, response.json()['error']['code']), (409, 'ATTEMPT_ALREADY_FINALIZED'))
        self.assertTrue(Answer.objects.get().marked_for_review)
