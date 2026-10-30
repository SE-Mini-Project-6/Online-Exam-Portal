import json
from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase

from exams.models import Exam


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
