"""Exercise production settings over loopback TLS with a disposable SQLite database."""
import argparse
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import ssl
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlencode


def summarize(samples):
    ordered = sorted(samples)
    return dict(count=len(samples), mean_ms=statistics.mean(samples),
                median_ms=statistics.median(samples),
                p95_ms=ordered[(95 * len(samples) + 99) // 100 - 1], max_ms=max(samples),
                over_2000_ms=sum(t > 2000 for t in samples))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openssl', default='openssl')
    parser.add_argument('--attempts', type=int, default=20)
    args = parser.parse_args()
    if args.attempts < 1:
        parser.error('--attempts must be positive')

    project = Path(__file__).resolve().parents[2] / 'Online_Exam_Portal'
    with tempfile.TemporaryDirectory(prefix='portal-tls-') as directory:
        folder = Path(directory)
        cert, key = folder / 'cert.pem', folder / 'key.pem'
        subprocess.run([args.openssl, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-days', '1', '-subj', '/CN=127.0.0.1', '-addext',
                        'subjectAltName=IP:127.0.0.1', '-keyout', str(key), '-out', str(cert)],
                       check=True, capture_output=True)
        (folder / 'smoke_settings.py').write_text(
            'from Online_Exam_Portal.settings import *\n'
            f'DATABASES["default"]["NAME"] = {str(folder / "smoke.sqlite3")!r}\n', encoding='utf-8')
        sys.path[:0] = [str(project), directory]
        os.environ.update(DJANGO_SETTINGS_MODULE='smoke_settings', DJANGO_DEBUG='False',
                          DJANGO_DB_ENGINE='sqlite', DJANGO_ALLOWED_HOSTS='127.0.0.1',
                          DJANGO_SECRET_KEY=secrets.token_urlsafe(64), DJANGO_BEHIND_PROXY='False')
        os.environ.pop('DJANGO_CSRF_TRUSTED_ORIGINS', None)
        import django
        django.setup()
        from datetime import timedelta
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
        from django.core.wsgi import get_wsgi_application
        from django.db import connections
        from django.test import Client
        from django.utils import timezone
        from exams.models import Attempt, Exam

        call_command('migrate', verbosity=0, interactive=False)
        call_command('check', deploy=True, fail_level='WARNING', verbosity=0, stdout=sys.stderr)
        password = secrets.token_urlsafe(24)
        student = get_user_model().objects.create_user(username='smoke-student', password=password)
        redirect = Client(HTTP_HOST='127.0.0.1').get('/')
        assert redirect.status_code == 301 and redirect['Location'] == 'https://127.0.0.1/'
        assert Client(HTTP_HOST='bad.invalid').get('/', secure=True).status_code == 400

        class HTTPSHandler(WSGIRequestHandler):
            def get_environ(self):
                environ = super().get_environ()
                environ['HTTPS'] = 'on'
                return environ

            def log_message(self, *args):
                pass

        with ThreadedWSGIServer(('127.0.0.1', 0), HTTPSHandler) as server:
            server.set_app(get_wsgi_application())
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.load_cert_chain(cert, key)
            server.socket = tls.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_address[1]
            context = ssl.create_default_context(cafile=str(cert))
            path = '/accounts/student-login/'

            def request(method, url, body=None, headers=None):
                with_connection = http.client.HTTPSConnection('127.0.0.1', port, context=context, timeout=15)
                try:
                    start = time.perf_counter()
                    with_connection.request(method, url, body=body, headers=headers or {})
                    response = with_connection.getresponse()
                    payload = response.read()
                    return response.status, response.headers, payload, (time.perf_counter()-start)*1000
                finally:
                    with_connection.close()

            try:
                status, headers, payload, _ = request('GET', path)
                assert status == 200 and headers['Strict-Transport-Security']
                cookie = next(value for value in headers.get_all('Set-Cookie') if value.startswith('csrftoken='))
                assert 'Secure' in cookie
                token = re.search(rb'name="csrfmiddlewaretoken" value="([A-Za-z0-9]+)"', payload)[1].decode()
                origin = f'https://127.0.0.1:{port}'
                assert request('POST', path, '', {'Origin': origin})[0] == 403
                post_headers = {'Cookie': cookie.split(';')[0], 'Origin': origin,
                                'Content-Type': 'application/x-www-form-urlencoded'}
                results = {'successful': [], 'unsuccessful': []}
                for _ in range(args.attempts):
                    for label, secret in [('successful', password), ('unsuccessful', 'incorrect')]:
                        body = urlencode(dict(username=student.username, password=secret, csrfmiddlewaretoken=token))
                        status, headers, _, latency = request('POST', path, body, post_headers)
                        if label == 'successful':
                            assert status == 302 and '/student-dashboard/' in headers['Location']
                            session = next(v for v in headers.get_all('Set-Cookie') if v.startswith('sessionid='))
                            assert 'Secure' in session and 'HttpOnly' in session
                        else:
                            assert status == 200 and not any(v.startswith('sessionid=') for v in headers.get_all('Set-Cookie', []))
                        results[label].append(latency)

                now = timezone.now()
                exam = Exam.objects.create(title='Scheduler smoke exam', duration_minutes=1,
                                           start_at=now-timedelta(minutes=2), end_at=now+timedelta(minutes=1))
                attempt = Attempt.objects.create(exam=exam, student=student, started_at=now-timedelta(minutes=1), deadline_at=now)
                env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path[:2]))
                command = [sys.executable, str(project / 'manage.py'), 'finalize_expired_attempts']
                ticks = []
                for _ in range(2):
                    ticks.append(subprocess.check_output(command, env=env, cwd=project, text=True).strip())
                    time.sleep(1)
                attempt.refresh_from_db()
                assert attempt.status == Attempt.SUBMITTED and attempt.submitted_at
                assert 'Finalized 1' in ticks[0] and 'Finalized 0' in ticks[1]
                print(json.dumps(dict(scope='localhost HTTPS, disposable SQLite',
                    checks=['production settings', 'HTTP redirect', 'allowed hosts', 'TLS/HSTS',
                            'CSRF rejection', 'secure cookies', 'unattended finalization and repeat invocation'],
                    login={label: summarize(samples) for label, samples in results.items()},
                    login_samples_ms=results, scheduler_ticks=ticks), indent=2))
            finally:
                server.shutdown()
                thread.join()
                connections.close_all()


if __name__ == '__main__':
    main()
