# Security and Integrity Regression Tests — Traceability and Evidence

Sprint 2 story: *run security and integrity regression tests so the Online Exam Portal satisfies
its documented requirements.* Owner: @Aditya-TJ. Design reference: OEP-SADS-1.0 sections 3.6, 4.2, 4.8 and 5.

## 1. Requirement-to-test traceability

| Requirement | Design element (SADS §5) | Automated tests |
|---|---|---|
| **SEC-REQ-01** Password handling | Authentication Service + password hasher (§3.6) | `accounts/test_security.py::PasswordHandlingTests` — PBKDF2 hash format, per-user salt, hasher not weakened, weak passwords rejected by validators, password change, identical error for wrong password vs unknown user, no password/hash echoed, inactive user blocked, missing credentials handled. `LogoutAndCsrfTests` — login/logout CSRF protection, POST-only logout. |
| **SEC-REQ-02** Unauthorized roles and wrong-owner access | RBAC + object ownership (§3.6) | `exams/test_security_regression.py::RoleAuthorizationTests` — student 403 on every admin endpoint (GET and POST, data unchanged), anonymous redirect/401 everywhere, admin cannot start/submit/save an attempt, `/admin/` closed to students, Start Exam hidden from admins. `OwnershipTests` — another student gets 403 on a foreign attempt, no data leaked, own attempt untouched by someone else's submit, saved answers never shown to another student, 404 for unknown attempt. |
| **SEC-REQ-03** Post-submit mutation | Attempt state guard — 409 after finalization (§3.6, §4.2, §4.8) | `exams/test_security_regression.py::PostSubmitMutationTests` — API answer/review update after submit returns 409 `ATTEMPT_ALREADY_FINALIZED`, web form POST returns 409, second submit returns 409 and keeps score and timestamp, unsupported API methods return 405, model layer refuses answer changes, editing the answer key does not change a stored score, confirmation required to finalize. |
| **SEC-REQ-04** HTTPS-only deployment | Deployment configuration, Fig. 3 | `accounts/test_security.py::HttpsEnforcementTests` — HTTP gets 301 to `https://`, credentials posted over HTTP are never processed, HTTPS response carries HSTS and `Secure`/`HttpOnly` session cookie. `HttpsSettingsModuleTests` — real settings module is HTTPS-only by default, relaxed only by `DJANGO_DEBUG=true`, env variables honoured, `manage.py check --deploy` clean. Documentation: `docs/https_deployment.md`. |

Existing tests that already cover related behaviour and still pass: `accounts/tests.py`
(`test_password_hashing_security`, `test_csrf_protection`), `exams/test_autosave.py`
(`test_requires_login_and_ownership`, `test_saves_blocked_after_finalization_and_outside_window`),
`exams/test_sprint1_abhi.py` (submission lock, user-scoped answers).

## 2. Code changes made for this story

| File | Change | Requirement |
|---|---|---|
| `Online_Exam_Portal/settings.py` | `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_BEHIND_PROXY` read from the environment; explicit `PASSWORD_HASHERS`; `STATIC_ROOT`; cookie flags | SEC-REQ-01, 04 |
| `accounts/views.py` | `logout_view` is `@require_POST` and no longer `csrf_exempt` | SEC-REQ-01/02 |
| `exams/sprint1_views.py` | Admins get 403 on `take_exam` (HTML) and `submit_exam` (Student operations verify role = STUDENT); JSON exam metadata stays readable by admins | SEC-REQ-02 |
| `exams/api.py` | Authentication is checked before the HTTP method (anonymous always 401); admins get 403 `FORBIDDEN` | SEC-REQ-02 |
| `templates/exams/available_exams.html` | Admins no longer see a Start Exam link | SEC-REQ-02 |
| `accounts/__init__.py`, `core/__init__.py` | New, empty. Without them `manage.py test` silently skipped `accounts/tests.py` and `core/tests.py` | test coverage |
| `accounts/tests.py`, `core/tests.py` | Added `@override_settings(SECURE_SSL_REDIRECT=False)` like the `exams` test classes; they only passed with `DJANGO_DEBUG=true` before | test coverage |

## 3. Test evidence

Run in a clean environment (Python 3.x, Django 6.1.2). Re-run locally and attach your own output or screenshots to the pull request.

```bash
python manage.py test                       # default (HTTPS-only) configuration
DJANGO_DEBUG=true python manage.py test     # development configuration
DJANGO_SECRET_KEY=<50+ chars> DJANGO_ALLOWED_HOSTS=exam.example.edu python manage.py check --deploy
```

| Run | Result |
|---|---|
| `python manage.py test` | 115 tests, OK |
| `DJANGO_DEBUG=true python manage.py test` | 115 tests, OK |
| `manage.py check --deploy` (production variables set) | System check identified no issues |
| `manage.py check --deploy` (no variables) | 2 warnings: `security.W009` (insecure secret key), `security.W020` (empty ALLOWED_HOSTS) — expected, resolved by the two required variables |
| New security tests against the pre-change code | 15 failures, i.e. the tests detect the gaps they were written for |

Manual evidence for SEC-REQ-04 on the real deployment (cannot be automated in CI): the `curl`
and browser checks in `docs/https_deployment.md` section 4 — attach the output and a cookie
screenshot.

## 4. Design deviations and decisions

| Topic | Design says | Implementation | Decision |
|---|---|---|---|
| Wrong-owner response | §4.8: `403 FORBIDDEN` for ownership failure | 403 for another student's attempt, 404 for a non-existent attempt | Kept as designed. Side effect: attempt IDs can be told apart from non-existent IDs. If the team prefers hiding existence, return 404 for both (§4.8 allows 404 "intentionally hidden by access rules") and update `test_other_student_cannot_patch_a_foreign_attempt`. |
| Roles | `role` field with STUDENT/ADMIN | Django `is_staff` flag | Unchanged; tests use `is_staff` as the admin role. |
| Attempt states | `IN_PROGRESS`, `SUBMITTED`, `AUTO_SUBMITTED` | `IN_PROGRESS`, `SUBMITTED` only | Not part of this story. Post-submit protection is tested for `SUBMITTED`; add `AUTO_SUBMITTED` to the same guard when the timeout story lands. |
| Late writes | §4.2: deadline = `start_time + duration` | Attempts have no `start_time`; writes are blocked when the exam window (`end_at`) has closed | Not part of this story; already covered by `test_saves_blocked_after_finalization_and_outside_window`. |
| Login endpoint | JSON `POST /api/v1/auth/login` | Form-based session login at `/accounts/login/` and `/accounts/student-login/` | Unchanged; password and CSRF behaviour is tested on the real endpoints. |
| Logout | Not specified | POST-only with CSRF (was GET-able and CSRF-exempt) | Hardening; the navbar already submits a POST form. |
| Login throttling | Not specified | None | Out of scope; `test_multiple_failed_login_attempts` only proves repeated failures never authenticate. |
| Result release, `AUTO` submit mode, submissions list | FR-14..FR-17 | Not implemented | Belong to other stories; no security tests are possible until they exist. |
