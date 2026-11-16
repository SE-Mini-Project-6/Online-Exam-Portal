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

    def change(name, old, new):
        file = app / 'exams' / name
        text = file.read_text(encoding='utf-8')
        assert old in text, (name, old)
        file.write_text(text.replace(old, new, 1), encoding='utf-8')

    change('models.py', '    option_c = models.CharField(max_length=300)\n    option_d = models.CharField(max_length=300)',
        '    question_type = models.CharField(max_length=4, choices=[("mcq", "Multiple choice"), ("tf", "True/False")], default="mcq")\n'
        '    option_c = models.CharField(max_length=300, blank=True)\n    option_d = models.CharField(max_length=300, blank=True)')
    change('models.py', '        return [(\'A\', self.option_a)', '        if self.question_type == "tf":\n            return [("A", "True"), ("B", "False")]\n        return [(\'A\', self.option_a)')
    change('models.py', "        for field in ('option_a', 'option_b', 'option_c', 'option_d'):",
        '        required_fields = () if self.question_type == "tf" else ("option_a", "option_b", "option_c", "option_d")\n'
        '        for field in required_fields:')
    change('models.py', "        if self.correct_option not in ('A', 'B', 'C', 'D'):",
        '        if self.correct_option not in dict(self.options()):')
    change('models.py', "        if self.selected_option is not None and self.selected_option not in ('A', 'B', 'C', 'D'):",
        '        if self.selected_option is not None and self.selected_option not in dict(self.question.options()):')
    change('forms.py', "fields = ('text', 'option_a'", "fields = ('question_type', 'text', 'option_a'")
    change('api.py', "    fields['visited'] = True", '    selection = fields.get("selected_option")\n'
        '    if selection is not None and selection not in dict(question.options()):\n'
        '        return _error(400, "VALIDATION_ERROR", "Option is unavailable for this question.")\n'
        "    fields['visited'] = True")
    change('sprint1_views.py', "        if selected in ('A', 'B', 'C', 'D'):", '        if selected in dict(question.options()):')

    # Make the existing A/B labels optional for the new canonical type while keeping MCQ model validation.
    for field in ('option_a', 'option_b'):
        change('models.py', f'    {field} = models.CharField(max_length=300)',
               f'    {field} = models.CharField(max_length=300, blank=True)')
    env = dict(os.environ, DJANGO_DB_ENGINE='sqlite', DJANGO_DEBUG='True')

    def manage(*args):
        subprocess.run([sys.executable, 'manage.py', *args], cwd=app, env=env, check=True)

    manage('makemigrations', 'exams')
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
form = QuestionForm(data={'question_type':'tf','text':'True or false?','correct_option':'A'})
assert form.is_valid(), form.errors
question = form.save(commit=False); question.exam = exam; question.save()
mcq = Question.objects.create(exam=exam, text='Existing MCQ', option_a='a', option_b='b', option_c='c', option_d='d', correct_option='D')
assert len(mcq.options()) == 4 and question.options() == [('A', 'True'), ('B', 'False')]
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
    print('Production modules changed: exams.models, exams.forms, exams.api, exams.sprint1_views. Generated schema migration counted separately.')
