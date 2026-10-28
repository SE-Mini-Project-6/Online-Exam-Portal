# Sprint 2 #30 â€” Architecture, HTTPS and deployment guidance

**Owner:** @Abhishekanand19. **Traceability:** SEC-REQ-04, NFR-05, EI-04.

## Architecture reflecting actual code

```text
Browser (student/admin)
  -> HTTPS reverse proxy / TLS terminator (deployment requirement, not deployed)
  -> Django URLs, authentication, role checks
     -> accounts/views.py  (login and dashboards)
     -> exams/views.py and exams/sprint1_views.py  (exam/MCQ/attempt/submit)
     -> exams/api.py  (PATCH answer autosave)
     -> exams/timing.py  (server deadline, locking, one-time grading)
     -> Django ORM -> SQLite (development; PostgreSQL recommended in production)
  -> Django templates + browser JavaScript countdown / autosave
```

This is a Django MVT server-rendered application, not a standalone microservice deployment. Server-side rules protect the exam availability window, answer ownership and finalization. `/api/v1/attempts/<attempt_id>/answers/<question_id>` handles PATCH and returns structured JSON errors. `/exams/<exam_id>/take/` renders questions and navigation; `/exams/<exam_id>/submit/` confirms or finalizes the attempt.

## Local development (PowerShell)

```powershell
cd Online_Exam_Portal
$env:DJANGO_DEBUG = "True"
python -m pip install "Django>=5.2,<5.3"
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

## Production deployment and HTTPS checklist

**The current repository is development-oriented, not production-deployed or production-hardened.** Its settings contain a development secret, empty `ALLOWED_HOSTS`, and SQLite. The steps below describe required future deployment work, not completed features.

1. Generate a unique `SECRET_KEY`; load it from a secret manager/environment into Django settings, never commit it or use the sample `django-insecure` value.
2. Set `DEBUG=False`; configure `ALLOWED_HOSTS` and HTTPS `CSRF_TRUSTED_ORIGINS` to actual production domains.
3. Put Django behind a trusted HTTPS reverse proxy/load balancer with a valid certificate. Redirect HTTP to HTTPS. Use `SECURE_PROXY_SSL_HEADER` only when the proxy strips untrusted forwarding headers.
4. Keep `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and appropriately reviewed HSTS configured; check browser/proxy behavior before HSTS preload.
5. Move to managed PostgreSQL with TLS, least-privilege DB credentials, migrations and tested backups. Current SQLite settings must be changed for that deployment.
6. Use a production WSGI/ASGI server behind the proxy and serve `collectstatic` assets through a separate static server or trusted service.
7. Configure a scheduler for `python manage.py finalize_expired_attempts` at an appropriate cadence (e.g., every minute), so abandoned attempts are finalized even without a browser request.
8. Run `python manage.py check --deploy`, full regression tests, integration and role tests, HTTPS smoke tests, and concurrency checks against the target database. Record warnings and errors; do not claim an HTTPS deployment merely because the Django security settings exist.

## API, error and design-deviation register

| Topic | Current implementation | Deviation / follow-up |
|---|---|---|
| Architecture | Django MVT with a JSON autosave endpoint | Not a general-purpose REST service |
| Data | Exam, Question, Attempt, Answer ORM models | SQLite dev default; production DB not configured |
| Answer save | PATCH API with owner checks, validation, 401/403/404/405/409 | Autosave only, not all endpoints REST |
| Submission | POST confirmation, transactional grade and lock | Server-side timer also finalizes on expiry |
| Timer | Stored start/deadline in Attempt | Scheduler required for abandoned sessions |
| Results visibility | Teammates' Sprint 2 #25/#26 | Not part of this issue's implementation |
| Review grid | Sprint 2 #21 branch | Avoid overwriting team's UI; reconcile migrations |
| HTTPS | Security toggles exist in Django settings | Proxy/certificate/prod hosts/secrets NOT deployed |

## Test evidence to attach after executing

`python manage.py check`; `python manage.py makemigrations --check --dry-run`; `python manage.py test`; and `python manage.py check --deploy` in an appropriately configured deployment environment. The GitHub Actions run and any deployed HTTPS screenshots are required evidence; none are presumed here.
