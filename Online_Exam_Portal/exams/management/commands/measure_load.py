import http.client
import json
import random
import statistics
import sys
import threading
import time
from collections import Counter
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.signals import got_request_exception
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler, get_internal_wsgi_application
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from exams.models import Attempt, Exam, Question

PAGE_TARGET_MS = 3000       # NFR-01: question page within 3 s under up to 50 concurrent students
AUTOSAVE_TARGET_MS = 2000   # NFR-02: autosave within 2 s
MAX_DEGRADATION = 0.20      # NFR-06: no more than a 20% rise in average response time at 50 attempts
QUESTIONS = 10


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


def _summary(samples):
    ordered = sorted(samples)
    return {
        'n': len(ordered),
        'mean': statistics.mean(ordered),
        'median': statistics.median(ordered),
        'p95': ordered[max(0, int(len(ordered) * 0.95) - 1)],
        'max': ordered[-1],
    }


class Command(BaseCommand):
    help = (
        'Measure question-page and autosave response times over real HTTP with 1 and N concurrent '
        'students (NFR-01, NFR-02, NFR-06). Creates throwaway data and deletes it afterwards.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50, help='Concurrent students (default 50).')
        parser.add_argument('--rounds', type=int, default=20, help='Page+autosave rounds per student (default 20).')
        parser.add_argument('--think-ms', type=int, default=0, help='Pause between rounds per student; 0 is a worst-case stress run.')
        parser.add_argument('--json', action='store_true', help='Print machine-readable results only.')

    def handle(self, *args, **options):
        users_n, rounds, think = options['users'], options['rounds'], options['think_ms']
        tag = uuid.uuid4().hex[:8]
        User = get_user_model()
        now = timezone.now()
        exam = Exam.objects.create(
            title=f'Load check {tag}', duration_minutes=30,
            start_at=now - timedelta(minutes=5), end_at=now + timedelta(hours=1),
        )
        users = []
        server_errors = []

        def record_exception(sender, **kwargs):
            exc = sys.exc_info()[1]
            server_errors.append(f'{type(exc).__name__}: {exc}')

        got_request_exception.connect(record_exception)
        try:
            questions = [
                Question.objects.create(
                    exam=exam, text=f'Question {i} ' + 'lorem ipsum ' * 10, option_a='a', option_b='b',
                    option_c='c', option_d='d', correct_option='A',
                )
                for i in range(QUESTIONS)
            ]
            sessions = []
            for i in range(users_n):
                user = User.objects.create_user(username=f'load-{tag}-{i}', password=uuid.uuid4().hex)
                users.append(user)
                attempt = Attempt.objects.create(exam=exam, student=user)
                client = Client()
                client.force_login(user)
                sessions.append((client.cookies['sessionid'].value, attempt.id))

            with override_settings(ALLOWED_HOSTS=['*'], SECURE_SSL_REDIRECT=False, DEBUG=False):
                server = ThreadedWSGIServer(('127.0.0.1', 0), _QuietHandler)
                server.set_app(get_internal_wsgi_application())
                server.daemon_threads = True
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                port = server.server_address[1]
                try:
                    page_urls = [reverse('exams:take', args=[exam.id]) + f'?question={q}' for q in range(1, QUESTIONS + 1)]
                    # Warm-up so template compilation and connection setup are not counted.
                    self._worker(port, sessions[0][0], page_urls, self._save_url(sessions[0][1], questions), 2, 0, [], [], [])
                    baseline = self._run(port, sessions[:1], page_urls, questions, rounds * 5, think)
                    loaded = self._run(port, sessions, page_urls, questions, rounds, think)
                finally:
                    server.shutdown()
                    server.server_close()
        finally:
            got_request_exception.disconnect(record_exception)
            exam.delete()
            for user in users:
                user.delete()

        results = self._evaluate(baseline, loaded, users_n)
        results['server_errors'] = dict(Counter(server_errors))
        if options['json']:
            self.stdout.write(json.dumps(results, indent=2))
        else:
            self._report(results, users_n, rounds, think)

    @staticmethod
    def _save_url(attempt_id, questions):
        return lambda i: reverse('api:answer_detail', args=[attempt_id, questions[i % len(questions)].id])

    def _run(self, port, sessions, page_urls, questions, rounds, think):
        pages, saves, errors = [], [], []
        threads = [
            threading.Thread(
                target=self._worker,
                args=(port, cookie, page_urls, self._save_url(attempt_id, questions), rounds, think, pages, saves, errors),
            )
            for cookie, attempt_id in sessions
        ]
        started = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return {'pages': pages, 'saves': saves, 'errors': errors, 'wall_s': time.perf_counter() - started}

    @staticmethod
    def _worker(port, cookie, page_urls, save_url, rounds, think, pages, saves, errors):
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=30)
        csrf = 'x' * 32  # a browser sends the cookie and X-CSRFToken header together
        headers = {'Cookie': f'sessionid={cookie}; csrftoken={csrf}', 'X-CSRFToken': csrf}
        try:
            for i in range(rounds):
                if think:
                    time.sleep(think / 1000 * random.uniform(0.5, 1.5))
                started = time.perf_counter()
                conn.request('GET', page_urls[i % len(page_urls)], headers=headers)
                response = conn.getresponse()
                response.read()
                elapsed = (time.perf_counter() - started) * 1000
                if response.status == 200:
                    pages.append(elapsed)
                else:
                    errors.append(f'page {response.status}')

                body = json.dumps({'selectedOption': 'ABCD'[i % 4]})
                started = time.perf_counter()
                conn.request(
                    'PATCH', save_url(i), body=body,
                    headers={**headers, 'Content-Type': 'application/json'},
                )
                response = conn.getresponse()
                payload = response.read()
                elapsed = (time.perf_counter() - started) * 1000
                if response.status == 200:
                    saves.append(elapsed)
                else:
                    errors.append(f'autosave {response.status} {payload[:80]!r}')
        except Exception as exc:  # report, do not hide, connection-level failures
            errors.append(f'{type(exc).__name__}: {exc}')
        finally:
            conn.close()

    @staticmethod
    def _evaluate(baseline, loaded, users_n):
        out = {'users': users_n}
        for name in ('pages', 'saves'):
            out[name] = {
                'single': _summary(baseline[name]) if baseline[name] else None,
                'concurrent': _summary(loaded[name]) if loaded[name] else None,
            }
        out['errors'] = {'single': baseline['errors'], 'concurrent': loaded['errors']}
        out['wall_s'] = loaded['wall_s']
        checks = {}
        if out['pages']['concurrent']:
            checks['NFR-01 page <= 3000 ms (max under load)'] = out['pages']['concurrent']['max'] <= PAGE_TARGET_MS
            checks['NFR-01 page <= 3000 ms (p95 under load)'] = out['pages']['concurrent']['p95'] <= PAGE_TARGET_MS
        if out['saves']['concurrent']:
            checks['NFR-02 autosave <= 2000 ms (max under load)'] = out['saves']['concurrent']['max'] <= AUTOSAVE_TARGET_MS
        for name, label in (('pages', 'page'), ('saves', 'autosave')):
            single, conc = out[name]['single'], out[name]['concurrent']
            if single and conc:
                growth = conc['mean'] / single['mean'] - 1
                out[name]['mean_growth'] = growth
                checks[f'NFR-06 {label} mean growth <= 20%'] = growth <= MAX_DEGRADATION
        checks['No failed requests'] = not (baseline['errors'] or loaded['errors'])
        out['checks'] = checks
        return out

    def _report(self, r, users_n, rounds, think):
        w = self.stdout.write
        w(f'Load run: 1 student vs {users_n} concurrent students, {rounds} page+autosave rounds each, real HTTP, think time {think} ms.')
        for name, label in (('pages', 'Question page GET'), ('saves', 'Autosave PATCH')):
            w(f'{label} (ms):')
            for key, title in (('single', '1 user'), ('concurrent', f'{users_n} users')):
                s = r[name][key]
                if s:
                    w(f'  {title:>9}: n={s["n"]} mean={s["mean"]:.1f} median={s["median"]:.1f} '
                      f'p95={s["p95"]:.1f} max={s["max"]:.1f}')
            if 'mean_growth' in r[name]:
                w(f'  mean growth: {r[name]["mean_growth"] * 100:+.1f}%')
        for key in ('single', 'concurrent'):
            if r['errors'][key]:
                w(f'Errors ({key}): {len(r["errors"][key])}, first: {r["errors"][key][0]}')
        for message, count in r['server_errors'].items():
            w(f'Server exception x{count}: {message}')
        w('Checks:')
        for label, ok in r['checks'].items():
            w(f'  [{"PASS" if ok else "FAIL"}] {label}')
