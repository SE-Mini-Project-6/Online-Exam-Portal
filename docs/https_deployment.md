# HTTPS Deployment Configuration (SEC-REQ-04)

Design reference: OEP-SADS-1.0 section 3.6 / Figure 3 — *"Production/deployed access is HTTPS-only.
HTTP is redirected or refused by deployment configuration."*

The portal is HTTPS-only by default. Plain HTTP is only allowed when you explicitly opt in to
local development with `DJANGO_DEBUG=true`.

## 1. What the application enforces (`Online_Exam_Portal/settings.py`)

| Setting | Production (`DJANGO_DEBUG` unset/false) | Local dev (`DJANGO_DEBUG=true`) |
|---|---|---|
| `SECURE_SSL_REDIRECT` | `True` — HTTP requests get a 301 to `https://` | `False` |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | `True` — cookies are never sent over HTTP | `False` |
| `SECURE_HSTS_SECONDS` | `31536000` (1 year) | `0` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` / `SECURE_HSTS_PRELOAD` | `True` | `False` |
| `SESSION_COOKIE_HTTPONLY` | `True` | `True` |
| `SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE` | `Lax` | `Lax` |
| `PASSWORD_HASHERS[0]` | PBKDF2 (salted, one-way) | same |

`SECURE_HSTS_PRELOAD` only matters if you submit the domain to the browser preload list. Do not
submit it until HTTPS works on the domain and every subdomain.

## 2. Environment variables

| Variable | Required in production | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | **Yes** | Long random value (50+ chars). Without it the insecure development key is used and `check --deploy` reports `security.W009`. |
| `DJANGO_ALLOWED_HOSTS` | **Yes** | Comma-separated host names, e.g. `exam.example.edu`. With debug off, an empty list makes Django reject every request with HTTP 400 (`security.W020`). |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | If the site is served on a different origin than Django sees | Comma-separated origins including scheme, e.g. `https://exam.example.edu`. |
| `DJANGO_BEHIND_PROXY` | Only behind a TLS-terminating proxy | `true` makes Django trust `X-Forwarded-Proto` (`SECURE_PROXY_SSL_HEADER`). **Only** enable it when the proxy sets/overwrites that header and the app port is not reachable directly, otherwise clients can spoof HTTPS. |
| `DJANGO_DEBUG` | No (leave unset) | `true` only on a developer machine or in CI. Never in production. |

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## 3. Deployment steps (Linux server, Gunicorn + nginx + Let's Encrypt)

```bash
# 1. Install and prepare the application
python3 -m venv venv && . venv/bin/activate
pip install django gunicorn
export DJANGO_SECRET_KEY='<generated value>'
export DJANGO_ALLOWED_HOSTS='exam.example.edu'
export DJANGO_CSRF_TRUSTED_ORIGINS='https://exam.example.edu'
export DJANGO_BEHIND_PROXY=true            # nginx terminates TLS (step 3)
python manage.py migrate
python manage.py collectstatic --noinput   # writes to STATIC_ROOT (./staticfiles)

# 2. Run the app on a local-only port
gunicorn Online_Exam_Portal.wsgi:application --bind 127.0.0.1:8000

# 3. Obtain a certificate (Let's Encrypt)
sudo certbot --nginx -d exam.example.edu
```

nginx server blocks (certbot fills in the certificate paths):

```nginx
server {                                   # HTTP: only redirects
    listen 80;
    server_name exam.example.edu;
    return 301 https://$host$request_uri;
}

server {                                   # HTTPS: terminates TLS, proxies to Gunicorn
    listen 443 ssl;
    server_name exam.example.edu;
    ssl_certificate     /etc/letsencrypt/live/exam.example.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/exam.example.edu/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location /static/ { alias /srv/online_exam_portal/staticfiles/; }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;   # overwrites any client-supplied value
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

If Django itself is exposed over TLS without a proxy (not recommended), leave
`DJANGO_BEHIND_PROXY` unset and terminate TLS in the application server.

## 4. Verification checklist (record the output as test evidence)

```bash
# Deployment check — must print "no issues"
DJANGO_SECRET_KEY=... DJANGO_ALLOWED_HOSTS=exam.example.edu python manage.py check --deploy

# HTTP is redirected to HTTPS (expect 301 and a https:// Location header)
curl -sI http://exam.example.edu/accounts/login/

# HTTPS answers with HSTS and Secure cookies
curl -sI https://exam.example.edu/accounts/login/ | grep -i strict-transport-security
curl -si https://exam.example.edu/accounts/login/ | grep -i set-cookie     # csrftoken ... Secure
```

Browser check: open `http://exam.example.edu`, confirm it lands on `https://` with a valid
certificate, log in, and confirm in DevTools → Application → Cookies that `sessionid` has
**Secure** and **HttpOnly** ticked.

## 5. Local development and CI

```bash
DJANGO_DEBUG=true python manage.py runserver      # plain HTTP on localhost, no redirects
python manage.py test                             # works with or without DJANGO_DEBUG
```

Test classes that use the plain-HTTP test client declare
`@override_settings(SECURE_SSL_REDIRECT=False)`; the HTTPS tests in
`accounts/test_security.py` turn the redirect on explicitly and also load the real settings
module in a subprocess to prove the defaults.

## 6. Scheduled expiry and a disposable verification run

Run the finalizer once as the same service account that runs Django, with the same production environment, working directory, and database. Then configure a recurring job. On Linux, the following example uses the deployment account's crontab and a wrapper that loads the environment file managed by the deployment. Replace the paths with the installed paths.

```sh
#!/bin/sh
set -eu
set -a
. /etc/exam-portal/environment
set +a
cd /srv/exam-portal/Online_Exam_Portal
exec /srv/exam-portal/.venv/bin/python manage.py finalize_expired_attempts
```

Install the wrapper as `/srv/exam-portal/bin/finalize-expired`, make it executable, and add `* * * * * /srv/exam-portal/bin/finalize-expired` to the deployment account's crontab. Keep the environment file readable only by the appropriate service account and administrators. Use the same account for a manual smoke invocation before relying on the recurring job. In a multi-instance deployment, configure one scheduled job against the shared database.

On the target, start a disposable student attempt and close the tab. After the deadline and one scheduler interval, verify that the stored attempt is submitted, the score is stable, a second invocation reports no additional finalization, and an authenticated late save is rejected. Keep scheduler logs and a separate availability observation through a declared exam window.

Run `python docs/tools/verify_local_deployment.py --openssl openssl --attempts 20` from the repository root for the disposable loopback test. It generates and trusts a temporary certificate, exercises the production settings, submits valid and invalid credentials over TLS, and invokes the finalizer in separate processes. The script uses a separate SQLite database and prints a JSON report. The deployment host, certificate, reverse proxy and managed scheduler require their own checks.

## 7. Out of scope

Certificate issuance/renewal automation, database hardening (PostgreSQL TLS), and WAF or
rate-limiting rules are not part of this story.

## Evidence from the final local smoke

Run `python docs/tools/verify_local_deployment.py --openssl openssl --attempts 20` from the repository root. [The loopback run](evidence/final-loopback.json) checked production Django settings, HTTPS, availability before/during/after an exam window and finalization in two separate command invocations. The login timings cover the HTTPS POST through response, with redirect and cookie checks. On the authorized evaluation deployment, also capture browser dashboard arrival, target-network latency and scheduler logs across two consecutive real ticks with one disposable expired attempt.
