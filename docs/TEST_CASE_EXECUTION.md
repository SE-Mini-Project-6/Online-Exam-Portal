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

The [technical completion report](FINAL_TECHNICAL_COMPLETION.md) records follow-up execution for TC-01, TC-05, TC-07 and TC-08 and related NFRs. Local timing and expiry tests have evidence. Target-network latency, deployment uptime and the production scheduler still need validation on the declared target.

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

| Requirements | Execution / evidence | Completion gate / status |
|---|---|---|
| FR-03..05 | Exam creation, invalid intervals, four-option question create/edit/delete and early/closed access: `exams.tests`, `exams.test_sprint1_abhi`, `exams.test_sprint1_criteria` | Automated regression evidence available; final browser walkthrough evidence should be reviewed |
| FR-17 | Roster with not started/in progress/submitted; grades hidden before submission: `accounts.test_submissions` | Automated regression evidence available |
| NFR-03 | Five first-time participants independently answered questions, marked a question for review, and submitted the exam. All 5/5 completed the tasks unaided; average completion time was 83 seconds, with no reported usability issues. | **PASS** — [Usability walkthrough](../Deliverable-4-Test-Validation/usability_browser_verification.md) |
| NFR-04 | Local HTTPS exam-window access checks passed. Actual target-environment availability has not been verified. | **BLOCKED — TARGET ENVIRONMENT** |
| NFR-05 | An isolated True/False question-type experiment changed one application module and generated zero migrations. | **PASS** — [Experiment evidence](evidence/final-maintainability.log) |
| NFR-07 | Desktop and phone browser flows were verified across Chrome 157/158 and Firefox 159/160. All 252 CI checks passed. | **PASS** — [Browser CI evidence](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43889325512) |
| NFR-01 | Existing PostgreSQL results met the absolute question-page latency target. The additional local SQLite test recorded a maximum of 19,907.98 ms against a 3,000 ms limit. | **PARTIAL** — target configuration verification pending |
| NFR-02 | Existing PostgreSQL results met the absolute autosave latency target. The additional local SQLite test recorded a maximum of 11,303.09 ms against a 2,000 ms limit. | **PARTIAL** — target configuration verification pending |
| NFR-06 | Existing PostgreSQL and SQLite runs failed the 20% mean response-time growth requirement. The additional local SQLite test measured +4,105.28% page growth and +5,067.56% autosave growth. | **FAIL** — performance improvement or approved deviation required |
| FR-01 | Local HTTPS login timing passed 40/40 samples, with valid and invalid login responses below 2 seconds. | **BLOCKED** — target broadband verification pending |
| SEC-REQ-04 | Local HTTPS security checks passed, including redirect, TLS/HSTS, CSRF, secure cookies and host rejection. Actual deployment configuration remains unverified. | **BLOCKED — TARGET ENVIRONMENT** |

### Additional local SQLite load-test evidence

A supplementary load test was conducted on a local Windows laptop using the SQLite database and the project's `measure_load` Django management command.

**Test configuration:**
- Database: SQLite
- Concurrent users: 50
- Rounds per user: 20
- Concurrent question-page requests measured: 1,000
- Concurrent autosave requests measured: 1,000
- Failed HTTP requests: 0
- Server errors: None reported
- Total test duration: 28.15 seconds

**Measured results:**

| Metric | Measured value | Acceptance target | Result |
|---|---:|---:|---|
| NFR-01 question-page maximum | 19,907.98 ms | <=3,000 ms | FAIL |
| NFR-01 question-page p95 | 3,289.88 ms | <=3,000 ms | FAIL |
| NFR-02 autosave maximum | 11,303.09 ms | <=2,000 ms | FAIL |
| NFR-06 question-page mean growth | +4,105.28% | <=20% | FAIL |
| NFR-06 autosave mean growth | +5,067.56% | <=20% | FAIL |
| Failed HTTP requests | 0 | 0 | PASS |

**Evidence:** [Local SQLite 50-user load-test JSON](evidence/local_load_results.json)

**Conclusion:** The local SQLite configuration failed the NFR-01, NFR-02 and NFR-06 performance requirements under 50 concurrent users. All requests completed without reported HTTP errors. These findings are retained as supplementary evidence and do not replace the earlier PostgreSQL or SQLite measurements.

The five-user usability requirement (NFR-03) and browser compatibility requirement (NFR-07) are complete and passed. Target-network performance, deployed security, availability and unattended finalization require coordination with the deployment owner.

## Execution record policy

Each final execution record must contain commit SHA, date, environment, command/manual steps, actual result, pass/fail/pending, evidence link and retest decision. The generated branch regression output and raw load JSON are linked from the current validation report. Original PDF security result summaries describe intended behavior; they are not historical execution proof without matching logs.

## Final sign-off execution evidence

NFR-01, NFR-02 and NFR-06 use 25 single-user and 250 concurrent page and save samples each per run. Evidence includes [PostgreSQL baseline](evidence/final-postgres-baseline.json), [updated PostgreSQL](evidence/final-postgres-after.json) and [updated SQLite](evidence/final-sqlite-after.json). NFR-05 uses the [isolated True/False experiment](evidence/final-maintainability.log). SEC-REQ-04, FR-01 timing and NFR-04 have [local HTTPS evidence](evidence/final-loopback.json). See [final acceptance status](FINAL_TECHNICAL_SIGNOFF_CHECKLIST.md) for environment limits and owners.
