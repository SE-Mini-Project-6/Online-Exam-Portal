from datetime import timedelta
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, sys.argv[1])
os.environ.update(DJANGO_SETTINGS_MODULE='Online_Exam_Portal.settings', DJANGO_DB_ENGINE='sqlite')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from exams.models import Attempt, Exam, Question

with tempfile.TemporaryDirectory() as folder:
    connection.settings_dict['NAME'] = str(Path(folder) / 'profile.sqlite3')
    try:
        call_command('migrate', verbosity=0)
        student = get_user_model().objects.create_user(username='sql-profile')
        now = timezone.now()
        exam = Exam.objects.create(title='Profile', duration_minutes=10, start_at=now-timedelta(minutes=1), end_at=now+timedelta(minutes=25))
        question = Question.objects.create(exam=exam, text='Profile answer', option_a='a', option_b='b', option_c='c', option_d='d', correct_option='A')
        client = Client(); client.force_login(student)
        with override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False):
            take = reverse('exams:take', args=[exam.pk])
            assert client.get(take).status_code == 200
            attempt = Attempt.objects.get(exam=exam, student=student)
            patch = reverse('api:answer_detail', args=[attempt.pk, question.pk])
            for label, run in [('revisit', lambda: client.get(take)),
                               ('autosave', lambda: client.patch(patch, {'selectedOption':'B'}, content_type='application/json'))]:
                with CaptureQueriesContext(connection) as captured:
                    assert run().status_code == 200
                sql = [row['sql'].split(None, 2)[:2] for row in captured.captured_queries]
                print(json.dumps({'path':label, 'statements':len(sql), 'operations':[' '.join(item) for item in sql]}))
    finally:
        connection.close()
