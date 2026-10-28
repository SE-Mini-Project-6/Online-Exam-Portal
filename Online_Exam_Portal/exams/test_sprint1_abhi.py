"""Regression tests for Abhi's four Sprint-1 stories: #9, #12, #16 and #17."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Answer, Attempt, Exam, Question


@override_settings(SECURE_SSL_REDIRECT=False)
class Sprint1AbhiTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.admin = users.objects.create_user(username='sprint-admin', password='SecureAdmin123!', is_staff=True)
        self.student = users.objects.create_user(username='sprint-student', password='SecureStudent123!')
        self.other = users.objects.create_user(username='sprint-other', password='SecureOther123!')
        now = timezone.now()
        self.exam = Exam.objects.create(title='Sprint Test', duration_minutes=20,
                                        start_at=now-timedelta(minutes=5), end_at=now+timedelta(hours=1))
        self.q1 = Question.objects.create(exam=self.exam, text='2+2?',
                                          option_a='4', option_b='3', option_c='2', option_d='5', correct_option='A')
        self.q2 = Question.objects.create(exam=self.exam, text='Capital of India?',
                                          option_a='Mumbai', option_b='Delhi', option_c='Kolkata', option_d='Chennai', correct_option='B')
        self.q3 = Question.objects.create(exam=self.exam, text='Unanswered question',
                                          option_a='Yes', option_b='No', option_c='Maybe', option_d='Unknown', correct_option='D')
        self.take_url = reverse('exams:take', args=[self.exam.pk])
        self.submit_url = reverse('exams:submit', args=[self.exam.pk])

    def test_all_four_relational_models_exist(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(self.take_url).status_code, 200)
        attempt = Attempt.objects.get(student=self.student, exam=self.exam)
        self.assertEqual(attempt.status, Attempt.IN_PROGRESS)
        self.assertEqual(attempt.answers.exclude(selected_option__isnull=True).count(), 0)

    def test_question_exactly_four_choices_and_one_correct(self):
        self.assertEqual(len(self.q1.options()), 4)
        self.assertEqual(self.q1.correct_option, 'A')
        for wrong in ('', 'X'):
            self.q1.correct_option = wrong
            with self.assertRaises(ValidationError):
                self.q1.full_clean()
        self.q1.correct_option = 'A'
        self.q1.option_c = '   '
        with self.assertRaises(ValidationError):
            self.q1.save()

    def test_staff_can_create_edit_delete_questions(self):
        self.client.force_login(self.admin)
        create = reverse('exams:question_create', args=[self.exam.pk])
        payload = {'text': 'New question?', 'option_a': 'One', 'option_b': 'Two',
                   'option_c': 'Three', 'option_d': 'Four', 'correct_option': 'C'}
        response = self.client.post(create, payload)
        self.assertEqual(response.status_code, 302)
        q = Question.objects.get(text='New question?')
        self.assertEqual(q.correct_option, 'C')
        payload['text'] = 'Edited question?'
        response = self.client.post(reverse('exams:question_edit', args=[self.exam.pk, q.pk]), payload)
        self.assertEqual(response.status_code, 302)
        q.refresh_from_db()
        self.assertEqual(q.text, 'Edited question?')
        self.assertEqual(self.client.post(reverse('exams:question_delete', args=[self.exam.pk, q.pk])).status_code, 302)
        self.assertFalse(Question.objects.filter(pk=q.pk).exists())

    def test_invalid_mcq_rejected_and_not_persisted(self):
        self.client.force_login(self.admin)
        payload = {'text': 'Invalid', 'option_a': 'A', 'option_b': 'B',
                   'option_c': '', 'option_d': 'D', 'correct_option': 'Z'}
        response = self.client.post(reverse('exams:question_create', args=[self.exam.pk]), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Question.objects.filter(text='Invalid').exists())

    def test_non_staff_cannot_manage_questions(self):
        self.client.force_login(self.student)
        url = reverse('exams:question_create', args=[self.exam.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'text': 'Unauthorized'}).status_code, 403)
        self.assertEqual(self.client.get(reverse('exams:questions', args=[self.exam.pk])).status_code, 403)

    def test_answer_persists_across_session_and_is_user_scoped(self):
        self.client.force_login(self.student)
        self.client.post(self.take_url, {'current': '1', 'goto': '2', 'answer': 'A'})
        attempt = Attempt.objects.get(student=self.student, exam=self.exam)
        self.assertEqual(attempt.answers.get(question=self.q1).selected_option, 'A')
        # Switching users should not reveal the first user's answer.
        self.client.force_login(self.other)
        response = self.client.get(self.take_url)
        self.assertContains(response, '2+2?')
        self.assertEqual(Attempt.objects.get(student=self.other, exam=self.exam).answers.exclude(selected_option__isnull=True).count(), 0)
        self.assertEqual(Attempt.objects.get(student=self.student, exam=self.exam).answers.count(), 1)

    def test_confirm_page_and_submission_lock(self):
        self.client.force_login(self.student)
        self.client.post(self.take_url, {'current': 1, 'goto': 2, 'answer': 'A'})
        response = self.client.get(self.submit_url)
        self.assertContains(response, 'Confirm exam submission')
        self.assertContains(response, '1 of 3')
        self.assertEqual(self.client.post(self.submit_url, {}).status_code, 400)
        self.assertEqual(self.client.post(self.submit_url, {'confirmed': 'yes'}).status_code, 302)
        attempt = Attempt.objects.get(student=self.student, exam=self.exam)
        self.assertEqual(attempt.status, Attempt.SUBMITTED)
        self.assertIsNotNone(attempt.submitted_at)
        self.assertEqual(attempt.score, 1)
        self.assertContains(self.client.get(self.take_url), 'Exam submitted successfully')
        self.assertEqual(self.client.post(self.take_url, {'current': '1', 'answer': 'B'}).status_code, 409)
        self.assertEqual(self.client.post(self.submit_url, {'confirmed': 'yes'}).status_code, 409)
        self.assertEqual(Answer.objects.get(attempt=attempt, question=self.q1).selected_option, 'A')

    def test_grading_unanswered_zero_and_review_flag_ignored(self):
        self.client.force_login(self.student)
        self.client.post(self.take_url, {'current': 1, 'goto': 2, 'answer': 'A', 'mark_for_review': 'on'})
        self.client.post(self.take_url, {'current': 2, 'goto': 3, 'answer': 'C'})  # wrong
        self.assertEqual(self.client.post(self.submit_url, {'confirmed': 'yes'}).status_code, 302)
        attempt = Attempt.objects.get(student=self.student, exam=self.exam)
        self.assertEqual(attempt.score, 1)
        answer = attempt.answers.get(question=self.q1)
        self.assertTrue(answer.marked_for_review)
        self.assertFalse(attempt.answers.filter(question=self.q3).exists())
        with self.assertRaises(ValidationError):
            answer.selected_option = 'B'
            answer.save()
        answer.refresh_from_db()
        self.assertEqual(answer.selected_option, 'A')
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 1)

    def test_all_correct_answers_score_three(self):
        self.client.force_login(self.student)
        for question_no, selected in enumerate(('A', 'B', 'D'), start=1):
            self.client.post(self.take_url, {'current': question_no, 'goto': question_no, 'answer': selected})
        self.client.post(self.submit_url, {'confirmed': 'yes'})
        self.assertEqual(Attempt.objects.get(student=self.student, exam=self.exam).score, 3)

    def test_cross_exam_answer_reference_rejected(self):
        other_exam = Exam.objects.create(title='Different exam', duration_minutes=20,
                                         start_at=self.exam.start_at, end_at=self.exam.end_at)
        self.client.force_login(self.student)
        self.client.get(self.take_url)
        attempt = Attempt.objects.get(student=self.student, exam=self.exam)
        foreign_question = Question.objects.create(exam=other_exam, text='Foreign?',
            option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A')
        with self.assertRaises(ValidationError):
            Answer.objects.create(attempt=attempt, question=foreign_question, selected_option='A')

    def test_submission_rejected_outside_exam_window(self):
        self.client.force_login(self.student)
        self.exam.end_at = timezone.now() - timedelta(minutes=1)
        self.exam.save()
        self.assertEqual(self.client.post(self.submit_url, {'confirmed': 'yes'}).status_code, 403)
        self.assertFalse(Attempt.objects.filter(student=self.student, exam=self.exam, status=Attempt.SUBMITTED).exists())

    def test_invalid_option_does_not_create_answer(self):
        self.client.force_login(self.student)
        self.client.post(self.take_url, {'current': 1, 'goto': 2, 'answer': 'Z'})
        attempt = Attempt.objects.get(student=self.student, exam=self.exam)
        self.assertEqual(attempt.answers.count(), 0)
        self.assertNotIn('exam_answers', self.client.session)
