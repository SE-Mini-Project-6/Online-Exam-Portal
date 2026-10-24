import json
import statistics
import time
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from exams.models import Attempt, Exam, Question

TARGET_MS = 2000  # auto-save requirement from the design specification (NFR-02)


class Command(BaseCommand):
    help = (
        'Measure autosave latency by sending PATCH requests to the autosave endpoint. '
        'Creates throwaway data and deletes it afterwards.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=200, help='Number of saves to time (default 200).')

    def handle(self, *args, **options):
        count = options['count']
        tag = uuid.uuid4().hex[:8]
        user = get_user_model().objects.create_user(username=f'latency-{tag}', password=uuid.uuid4().hex)
        now = timezone.now()
        exam = Exam.objects.create(
            title=f'Latency check {tag}', duration_minutes=30,
            start_at=now - timedelta(minutes=5), end_at=now + timedelta(hours=1),
        )
        try:
            questions = [
                Question.objects.create(
                    exam=exam, text=f'Q{i}', option_a='a', option_b='b',
                    option_c='c', option_d='d', correct_option='A',
                )
                for i in range(5)
            ]
            attempt = Attempt.objects.create(exam=exam, student=user)
            timings = []
            with override_settings(ALLOWED_HOSTS=['*'], SECURE_SSL_REDIRECT=False):
                client = Client()
                client.force_login(user)
                for i in range(count):
                    url = reverse('api:answer_detail', args=[attempt.id, questions[i % 5].id])
                    started = time.perf_counter()
                    response = client.patch(
                        url, data=json.dumps({'selectedOption': 'ABCD'[i % 4]}),
                        content_type='application/json',
                    )
                    timings.append((time.perf_counter() - started) * 1000)
                    if response.status_code != 200:
                        self.stderr.write(f'Unexpected status {response.status_code}: {response.content!r}')
                        return
        finally:
            exam.delete()
            user.delete()

        timings.sort()
        p95 = timings[max(0, int(len(timings) * 0.95) - 1)]
        verdict = 'within' if timings[-1] <= TARGET_MS else 'EXCEEDS'
        self.stdout.write(f'Autosave latency over {count} saves (server-side, no network):')
        self.stdout.write(f'  min    {timings[0]:.1f} ms')
        self.stdout.write(f'  median {statistics.median(timings):.1f} ms')
        self.stdout.write(f'  p95    {p95:.1f} ms')
        self.stdout.write(f'  max    {timings[-1]:.1f} ms')
        self.stdout.write(f'Slowest save {verdict} the {TARGET_MS} ms auto-save target.')
