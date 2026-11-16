"""Disposable true/false change-impact experiment. Never edits the live checkout."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
source = root / 'Online_Exam_Portal'
with tempfile.TemporaryDirectory(prefix='portal-question-type-') as folder:
    app = Path(folder) / 'app'
    shutil.copytree(source, app, ignore=shutil.ignore_patterns('*.sqlite3*', '__pycache__'))
    original = {path.relative_to(app): path.read_bytes() for path in app.rglob('*.py')}

    def change(name, old, new):
        file = app / 'exams' / name
        text = file.read_text(encoding='utf-8')
        assert old in text, (name, old)
        file.write_text(text.replace(old, new, 1), encoding='utf-8')

    change('models.py', "    TYPES = {DEFAULT_TYPE: ('Multiple choice', None)}",
           "    TYPES = {DEFAULT_TYPE: ('Multiple choice', None), "
           "'tf': ('True/False', (('A', 'True'), ('B', 'False')))}")

    env = dict(os.environ, DJANGO_DB_ENGINE='sqlite', DJANGO_DEBUG='True')

    def manage(*args):
        subprocess.run([sys.executable, 'manage.py', *args], cwd=app, env=env, check=True)

    manage('makemigrations', '--check', '--dry-run')
    manage('migrate', '--noinput', '--verbosity', '0')
    manage('shell','-c', '''
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from exams.forms import QuestionForm
from exams.models import Exam, Question, Attempt, Answer
from exams.timing import sync_attempt
now = timezone.now()
exam = Exam.objects.create(title='Mixed practice', duration_minutes=5, start_at=now-timedelta(minutes=1), end_at=now+timedelta(minutes=10))
data = {'question_type':'tf','text':'True or false?','correct_option':'A'}
form = QuestionForm(data=data)
assert form.is_valid(), form.errors
assert not QuestionForm(data={**data, 'correct_option':'C'}).is_valid()
staff = get_user_model().objects.create_user(username='prototype-admin', is_staff=True)
admin = Client(); admin.force_login(staff)
with override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False):
    assert admin.post(reverse('exams:question_create', args=[exam.pk]), data).status_code == 302
question = Question.objects.get(exam=exam, question_type='tf')
mcq = Question.objects.create(exam=exam, text='Existing MCQ', option_a='a', option_b='b', option_c='c', option_d='d', correct_option='D')
assert len(mcq.options()) == 4 and list(question.options()) == [('A', 'True'), ('B', 'False')]
student = get_user_model().objects.create_user(username='prototype')
client = Client(); client.force_login(student)
with override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False):
    take = reverse('exams:take', args=[exam.pk]); page = client.get(take)
    assert page.status_code == 200 and b'B. False' in page.content and b'name="answer" value="C"' not in page.content
    attempt = Attempt.objects.get(student=student, exam=exam)
    url = reverse('api:answer_detail', args=[attempt.pk,question.pk])
    assert client.patch(url, {'selectedOption':'C'}, content_type='application/json').status_code == 400
    assert client.post(take, data={'current':1,'goto':1,'answer':'C'}).status_code == 302
    assert Answer.objects.get(attempt=attempt, question=question).selected_option is None
    assert client.patch(url, {'selectedOption':'A'}, content_type='application/json').status_code == 200
    assert sync_attempt(attempt.pk, manual=True)[0].score == 1
print('PASS: staff form, existing MCQ, true/false rendering, API rejection, form rejection, autosave and grading.')
''')
    current = {path.relative_to(app): path.read_bytes() for path in app.rglob('*.py')}
    changed = sorted(path.as_posix() for path in original.keys() | current.keys()
                     if original.get(path) != current.get(path))
    assert changed == ['exams/models.py'], changed
    print(f'Application modules changed: {len(changed)} ({", ".join(changed)}). Generated schema migrations: 0.')
