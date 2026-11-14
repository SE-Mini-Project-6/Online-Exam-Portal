import json
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.template.response import TemplateResponse
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from exams.models import Attempt, Exam, Question
from exams.timing import sync_attempt


class LoadMeasurementTests(TransactionTestCase):
    """NFR-01/02/06 tooling: the harness must run end to end and leave no data behind."""

    def test_measure_load_reports_every_target_and_cleans_up(self):
        out = StringIO()
        # One student: the in-memory test database uses shared-cache table locks, which cannot honour
        # the busy timeout, so true 50-user concurrency is measured against the file database instead
        # (docs/SPRINT2_PERFORMANCE_RELIABILITY.md).
        call_command('measure_load', users=1, rounds=3, json=True, stdout=out)
        result = json.loads(out.getvalue())
        self.assertEqual(result['server_errors'], {})
        self.assertEqual(result['errors'], {'single': [], 'concurrent': []})
        self.assertEqual(result['pages']['concurrent']['n'], 3)
        self.assertEqual(result['saves']['concurrent']['n'], 3)
        self.assertIn('NFR-01 page <= 3000 ms (p95 under load)', result['checks'])
        self.assertIn('NFR-02 autosave <= 2000 ms (max under load)', result['checks'])
        self.assertIn('NFR-06 page mean growth <= 20%', result['checks'])
        self.assertEqual(Exam.objects.count(), 0)

    def test_sqlite_writers_queue_instead_of_failing(self):
        # Regression for "database is locked" at 50 concurrent attempts (NFR-06).
        options = connection.settings_dict['OPTIONS']
        self.assertEqual(options.get('transaction_mode'), 'IMMEDIATE')
        self.assertGreaterEqual(options.get('timeout', 0), 20)


@override_settings(SECURE_SSL_REDIRECT=False)
class ExamTransactionTests(TransactionTestCase):
    """HTML rendering must not hold the database's attempt-write transaction."""

    def setUp(self):
        student = get_user_model().objects.create_user(username='render-student')
        self.client.force_login(student)
        now = timezone.now()
        self.exam = Exam.objects.create(
            title='Rendering lock check', duration_minutes=10,
            start_at=now - timedelta(minutes=5), end_at=now + timedelta(hours=1),
        )
        Question.objects.create(
            exam=self.exam, text='Question?', option_a='A', option_b='B',
            option_c='C', option_d='D', correct_option='A',
        )
        self.url = reverse('exams:take', args=[self.exam.pk])

    def test_html_renders_after_attempt_transaction_commits(self):
        render = TemplateResponse.render
        transaction_states = []

        def observe(response):
            transaction_states.append(connection.in_atomic_block)
            return render(response)

        with patch.object(TemplateResponse, 'render', observe):
            response = self.client.get(self.url)
        self.assertContains(response, 'Question?')
        self.assertEqual(transaction_states, [False])
        self.assertTrue(Attempt.objects.get().deadline_at)

    def test_refresh_checks_deadline_once_without_extending_it(self):
        self.client.get(self.url)
        deadline = Attempt.objects.get().deadline_at
        with patch('exams.sprint1_views.sync_attempt', wraps=sync_attempt) as synchronize:
            self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(synchronize.call_count, 1)
        self.assertEqual(Attempt.objects.get().deadline_at, deadline)
