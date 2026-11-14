# Detailed test-case execution revision 1.1

14 November 2026. This addendum updates the execution contract of original Deliverable 4 TC-01..10 to match the implemented application. It does not change SRS targets or claim all tests passed. Read actual results in [VALIDATION_RESULTS.md](VALIDATION_RESULTS.md); unresolved design differences are in [DESIGN_DEVIATIONS.md](DESIGN_DEVIATIONS.md).

## Environment and common preconditions

Use Python/Django with the repository requirements installed, a migrated disposable database, one staff account and two student accounts. Create an exam with at least five four-option MCQs and known keys. For attempt tests use an open availability window. For timeout use a one-minute duration. Use separate exams/attempts where tests consume a submission; retakes are not supported. Never run load/seeding tests against a live student exam.

```powershell
cd Online_Exam_Portal
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput
```

For local HTTP, set `DJANGO_DEBUG=True` before `runserver`. For production/HTTPS verification use the deployment guide, genuine target secrets/hosts and actual TLS. Do not commit credentials.

## Current route contract

| Operation | Actual route and response |
|---|---|
| Staff login | GET/POST `/accounts/login/`; successful form login redirects to role dashboard |
| Student login | GET/POST `/accounts/student-login/`; session login and redirect |
| Logout | POST `/accounts/logout/`, CSRF protected |
| Create exam | GET/POST `/exams/create/`, staff only |
| List exam metadata | GET `/exams/available/?format=json` |
| Take exam | GET/POST `/exams/<exam_id>/take/`; form navigation and saved answers |
| Manage MCQs | `/exams/<exam_id>/questions/`, `add/`, `<question_id>/edit/`, `<question_id>/delete/`; delete requires POST |
| Autosave | PATCH `/api/v1/attempts/<attempt_id>/answers/<question_id>`; no trailing slash; JSON body and CSRF token |
| Confirm/finalize | GET/POST `/exams/<exam_id>/submit/`; POST `confirmed=yes`; success redirects, duplicate POST 409 |
| Student result | GET `/exams/<exam_id>/result/`; own result only; score omitted until release |
| Staff roster | GET `/accounts/admin-submissions/?exam=<exam_id>` |
| Release results | POST `/accounts/admin-submissions/<exam_id>/release/`; staff/CSRF protected; after window closes and all existing attempts submitted |

Autosave fields: `selectedOption` = A/B/C/D/null; `markedForReview` = boolean; at least one required. Errors use `error.code`, `error.message`, `error.requestId`. Anonymous=401, foreign attempt=403, wrong/unknown question=404, bad payload=400, finalized=409, unavailable window=403. A timeout triggered during a save finalizes first, then rejects the write. Exact window/finalization error precedence is endpoint-specific; the security invariant is no late mutation.

## Revised detailed cases

| TC / traceability | Preconditions and steps | Expected result and pass criterion | Automated evidence |
|---|---|---|---|
| TC-01 / FR-01, FR-02, SEC-REQ-01 | Provision staff/student. Submit valid credentials on their form routes; repeat with wrong password; inspect stored hash through Django password verification. Measure login round trip separately on target network. | Correct role dashboard/session; invalid credentials denied; salted one-way hash, no plaintext. FR-01 <=2 s requires a measured result, not merely a functional login test. | `accounts.tests`, `accounts.test_security` |
| TC-02 / FR-06, FR-07 | Student opens active exam; choose C on Q3 via PATCH or form, choose D later, navigate Q5/Q3, refresh and log in again. | Latest saved selection D persists and can change until finalization; question navigation unrestricted within valid attempt. | `exams.test_autosave`, `exams.test_sprint1_abhi`, `exams.tests` |
| TC-03 / FR-08, FR-09, FR-10 | Leave Q5 unvisited; visit Q1 without answer; answer Q2; mark unanswered Q3; answer+mark Q4. Refresh; toggle mark without changing answer. | Grid shows all five distinct correct states; current ring independent; mark never changes selected answer. Saved states persist. | `exams.test_review_grid` plus browser script |
| TC-04 / FR-11, FR-13, SEC-REQ-03 | Answer questions, open submit confirmation, cancel by returning to exam, then POST `confirmed=yes`. Repeat POST; PATCH saved answer. | Confirmation counts accurate; final submit redirects to success; score correct; repeated POST/PATCH 409 and no score/answer changes. | `exams.test_sprint1_abhi`, `exams.test_security_regression` |
| TC-05 / FR-12, FR-13 | Open one-minute exam, save answer; wait for real deadline without manual submission. Repeat with tab abandoned and scheduled finalizer; attempt late PATCH. | Countdown redirects; server grades once and persists SUBMITTED; late answer rejected; saved score unchanged. Abandoned attempt is finalized by scheduler within its configured cadence. Scheduler installation must be separately verified. | `exams.test_sprint2_timer`; real browser expiry and scheduler acceptance |
| TC-06 / FR-14, FR-15, FR-16 | Submit student attempt; open own result before release. Close exam window, finalize remaining attempts, POST staff release. Reopen own result; try another student's identifiers. | Before release no score in HTML; after release own score displayed. Students cannot release or retrieve foreign score. HTML withheld page may return 200; original REST 403 assumption superseded. | `exams.test_results`, `accounts.test_submissions`, security regression |
| TC-07 / NFR-01, NFR-06 | Run controlled 1-user and 50-user real HTTP measurement, record machine/database/server/pacing, raw JSON and all errors. | Every question response <=3000 ms, no request errors, 50-user page mean <=1.20 x baseline. p95 alone is insufficient. Keep failure as failure; do not alter thresholds to obtain green output. | `measure_load` raw report; `exams.test_performance` only validates harness behavior |
| TC-08 / NFR-02 | Select option, measure click-to-save completion, refresh and reopen. Repeat under declared concurrent load. | Answer survives refresh; every measured save <=2000 ms in the claimed scenario. Server-only timings are not broadband/browser evidence. | `exams.test_autosave`, browser script, `measure_load` |
| TC-09 / SEC-OBJ-01, SEC-REQ-01/02 | Anonymous protected requests; B PATCHes A's attempt; student requests each staff write route; staff tries student flow; cross-exam question ID. | Redirect/401 as route specifies; foreign/role access denied; no protected data leak or unauthorized database mutation. | `exams.test_security_regression`, `accounts.test_security` |
| TC-10 / SEC-OBJ-02, SEC-REQ-03 | Record finalized score/answers. Try manual and late timeout submissions and answer/review writes; compare stored values. | Duplicate submission and finalized write rejected; grade and answer/review state unchanged. | `exams.test_security_regression`, `exams.test_sprint2_timer` |

## Additional planned coverage and outstanding evidence

| Requirements | Execution / evidence | Completion gate |
|---|---|---|
| FR-03..05 | Exam creation/invalid intervals, four-option question create/edit/delete and early/closed access: `exams.tests`, `exams.test_sprint1_abhi`, `exams.test_sprint1_criteria` | Regression result and final browser walkthrough |
| FR-17 | Roster with not started/in progress/submitted; grades hidden before submission: `accounts.test_submissions` | Regression result |
| NFR-03 | Five actual first-time participants follow protocol in usability report | Real session log and fixed/retested findings; pending |
| NFR-04 | Window guards plus observed target deployment availability throughout declared exam window | Local unit tests alone insufficient; operational observation pending |
| NFR-05 | Review code boundaries; demonstrate representative additional question type and record touched modules | <=2-module target not demonstrated; pending or approved deviation |
| NFR-07 | Desktop/phone scripted flows in two agreed current versions each of Chrome/Firefox; record exact versions and screenshots | All four browser-version combinations; only measured combinations may pass |
| SEC-REQ-04 | Check HTTPS redirect, secure cookies and trusted proxy behavior on actual assessment deployment | Local configuration check is not a deployed TLS test |

## Execution record policy

Each final execution record must contain commit SHA, date, environment, command/manual steps, actual result, pass/fail/pending, evidence link and retest decision. The generated branch regression output and raw load JSON are linked from the current validation report. Original PDF security result summaries describe intended behavior; they are not historical execution proof without matching logs.
