# Technical completion evidence

16 November 2026. Source baseline `577638612ef398d31bde3aa6fdd095ec4bfa714c` includes PRs #56 and #57. The optimization is commit `96a4f917d2076a31ab6b32095ee7cc40d0eedbe8` on `remaining-technical-completion`. All new measurements used disposable data and loopback. The SRS thresholds remain unchanged.

| Requirement | Previous Status | Changes Made | Actual Test Result | Final Status | Evidence |
|---|---|---|---|---|---|
| NFR-01, every question page ≤3,000 ms | Failed under SQLite | Revisit active, already visited questions without a write transaction. PostgreSQL locks the attempt instead of also locking the exam row. | Matched after-run maximum 5,847 ms on SQLite and 1,146 ms on PostgreSQL 17. | PARTIAL | [SQLite](evidence/technical-load-after.json), [PostgreSQL](evidence/technical-postgres-after.json) |
| NFR-02, every autosave ≤2,000 ms | Failed in certain runs | Retain the answer-write transaction and deadline check. Eliminate shared exam-row lock in PostgreSQL so independent attempts wait less. | Matched after-run maximum 5,396 ms on SQLite and 794 ms on PostgreSQL 17. | PARTIAL | Same raw load reports |
| NFR-06, 50 students and ≤20% increase in means | Failed | Reduced transaction contention and profiled the read/write paths. | SQLite page/save mean growth +1047.2%/+852.7%; PostgreSQL +409.4%/+290.0%. | FAIL | Same raw load reports |
| NFR-05, at most two modules for another question type | Unverified | Ran a true/false prototype in an isolated checkout and discarded the feature. | Staff form, existing MCQ, two-option UI, both invalid-input paths, autosave and grading worked. Four application modules and one generated migration changed. | FAIL | [Experiment](tools/measure_question_type.py), [output](evidence/technical-maintainability.log) |
| SEC-REQ-04, HTTPS configuration | Automated configuration evidence only | Verified production settings and HTTPS over loopback with a freshly generated trusted test certificate. Documented scheduler and target checks. | Deployment check 0 warnings; HTTP redirect 301, unknown host 400, missing CSRF token 403; HTTPS HSTS and Secure cookies confirmed; session cookie HttpOnly. | PARTIAL | [Local smoke JSON](evidence/technical-local-deployment-ip.json), [runbook](https_deployment.md) |
| NFR-04 and unattended finalization | No deployed availability or scheduler evidence | Ran separate finalizer subprocesses against a disposable expired attempt without a browser request. | First tick finalized 1, second finalized 0. Regression tests covered timer, lock and results. Target scheduler and availability throughout a real exam window remain unverified. | PARTIAL | [Local smoke JSON](evidence/technical-local-deployment-ip.json), [Django log](evidence/technical-regression.log) |
| FR-01, student login within 2 seconds over standard broadband | No quantitative evidence | Measured student login POST through real local TLS, with normal password hashing and CSRF. | Explicit IPv4 loopback: 20 successful and 20 rejected logins, all under 2 seconds. An initial hostname-based run exceeded 2 seconds for all 40. Target broadband timing is unverified. | PARTIAL | [IPv4 results](evidence/technical-local-deployment-ip.json), [initial results](evidence/technical-local-deployment.json) |
| GitHub Project #2 | Board unverified | Checked the supplied board URL and attempted access. | Public fetch could not retrieve the board, connector rejects organization Projects URLs, and available credential lacked `read:project` and `read:org`. No changes made. | BLOCKED — ACCESS/ENVIRONMENT | [Project #2](https://github.com/orgs/SE-Mini-Project-6/projects/2), [issue snapshot](SPRINT_BACKLOG.md) |
| Original scope exclusions | Human activities pending | Prepared reproducible evidence and retained actual outcomes. | Usability participant sessions, human reviews, approvals, retrospective, freeze, evaluation demo and viva remain with their owners. | BLOCKED — ACCESS/ENVIRONMENT | [Team acceptance](TEAM_ACCEPTANCE.md) |

## Load comparison

Same command on both revisions for each database, from `Online_Exam_Portal`:

```text
python manage.py measure_load --users 50 --rounds 5 --think-ms 1000 --json
```

Windows, Python 3.13.13, Django 5.2.18, threaded WSGI server. PostgreSQL 17 used a disposable local password-protected cluster and the existing PostgreSQL settings. Each run had 25 one-user and 250 concurrent successful requests per endpoint. Pacing is randomized by the original harness, so this is a matched configuration, not an identical trace. Throughput includes pacing and counts both endpoints. The PostgreSQL runs shared the machine with verification processes, so they are engineering measurements rather than isolated capacity results.

| Database / run | Endpoint | Mean ms | Median ms | p95 ms | Max ms | Mean growth | Combined req/s | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| SQLite baseline | Page | 2151.64 | 148.82 | 12045.42 | 21879.92 | +6589.23% | 18.17 | 0 |
| SQLite baseline | Save | 533.30 | 111.98 | 1944.24 | 18519.34 | +1692.41% | 18.17 | 0 |
| SQLite after | Page | 383.21 | 72.13 | 2493.52 | 5847.16 | +1047.17% | 45.49 | 0 |
| SQLite after | Save | 251.52 | 47.70 | 1243.47 | 5396.47 | +852.74% | 45.49 | 0 |
| SQLite repeat | Page | 332.96 | 57.61 | 1794.34 | 5429.45 | +906.65% | 45.72 | 0 |
| SQLite repeat | Save | 124.45 | 38.00 | 570.19 | 1919.53 | +288.39% | 45.72 | 0 |
| PostgreSQL baseline | Page | 759.80 | 761.55 | 1188.90 | 1290.36 | +474.96% | 34.88 | 0 |
| PostgreSQL baseline | Save | 770.79 | 771.40 | 1187.35 | 1341.44 | +624.86% | 34.88 | 0 |
| PostgreSQL after | Page | 583.75 | 598.59 | 926.94 | 1146.01 | +409.43% | 42.16 | 0 |
| PostgreSQL after | Save | 435.87 | 453.76 | 708.35 | 794.13 | +289.99% | 42.16 | 0 |

Raw data: [SQLite baseline](evidence/technical-load-baseline.json), [SQLite after](evidence/technical-load-after.json), [SQLite repeat](evidence/technical-load-repeat.json), [PostgreSQL baseline](evidence/technical-postgres-baseline.json), [PostgreSQL after](evidence/technical-postgres-after.json). The repeat passed the SQLite autosave maximum once, while SQLite page maximum and both growth measures still failed. SQL profile: [before](evidence/technical-sql-baseline.jsonl) and [after](evidence/technical-sql-after.jsonl). A visited-question GET changed from 11 statements including `BEGIN IMMEDIATE` and an attempt synchronization query to 6 reads. An existing-answer PATCH retained 16 statements including a write transaction, model validation queries and an update. A new visit, deadline shortening, expiration or submission still takes the write path. The timer samples the current clock after taking the attempt lock if the caller did not supply a timestamp.

SQLite serializes writes and the workload includes first visits and saves. PostgreSQL no longer serializes independent attempts on the shared exam row, but still pays per-request database/session work and load contention. The SQL evidence isolates the lock change. It does not apportion latency among connection churn, CPU scheduling and database execution. Reproduce on an isolated deployment with PostgreSQL, an appropriate WSGI server and connection persistence/pooling, then measure those components. Keep the 20% requirement open and avoid trading off grading, deadline or data integrity for lower measurements.

## Maintainability and operational reproduction

NFR-05 requires a layered design where a new question type needs at most two changed modules. Run `python docs/tools/measure_question_type.py` from the repository root. It migrates a temporary copy and drives the staff form, student view, both answer endpoints and grading. `exams.models` held schema and core validation; `exams.forms` exposed the new type; `exams.api` and `exams.sprint1_views` each needed an endpoint guard against options the question does not offer. The generated migration is additional. A small next change is to route answer validation in both endpoints through the same question option contract and leave the feature-specific rules in the model and admin form. Re-run the isolated experiment after that refactor. A migration still matters if the evaluator counts generated modules.

For SEC-REQ-04 and FR-01, run `python docs/tools/verify_local_deployment.py --openssl openssl --attempts 20`. On this host the executable was `C:\Program Files\Git\usr\bin\openssl.exe`. Each timing starts before connection/TLS and ends after the POST response body. Successful attempts return the dashboard redirect and a secure session, invalid attempts show the form without a session. Dashboard rendering and actual broadband latency need separate target evidence. The hostname-based initial run measured about 3 seconds per POST; the explicit IPv4 repeat changed endpoint addressing and machine load also differed. No isolated attribution to DNS, network fallback or CPU can be made from those runs.

| Address / authentication | Count | Mean ms | Median ms | p95 ms | Max ms | >2,000 ms |
|---|---:|---:|---:|---:|---:|---:|
| Hostname / correct | 20 | 2976.52 | 2983.24 | 3041.94 | 3060.17 | 20 |
| Hostname / incorrect | 20 | 2975.97 | 2974.60 | 3043.36 | 3043.72 | 20 |
| IPv4 / correct | 20 | 747.75 | 735.15 | 799.98 | 875.91 | 0 |
| IPv4 / incorrect | 20 | 746.77 | 747.68 | 824.25 | 831.15 | 0 |

The deployment owner can use the [HTTPS and scheduler runbook](https_deployment.md) against the intended deployment. Ask the organization maintainer to grant an existing authorized account project read access or provide a board export showing the repository linkage, views, item IDs, assignees and story points. A token must have Projects read permission and organization read access where required. Grant write access only to a maintainer making corrections. When access is available, compare #9–#32 to the [sprint issue snapshot](SPRINT_BACKLOG.md), including the evidence still outstanding on closed issues.

## Regression commands and evidence

| Command | Result | Evidence |
|---|---|---|
| `python manage.py check` | No issues | Windows, Python 3.13.13, Django 5.2.18 |
| `python manage.py makemigrations --check --dry-run` | No changes detected | Same environment |
| `python manage.py test --noinput` | 147 passed, 0 failed in 220.256 seconds. Includes security, timer, student/admin flows, load harness, and attempt-transaction regressions. | [Full output](evidence/technical-regression.log) |
| `python Deliverable-4-Test-Validation/browser_checks/run_browser_checks.py --evidence-dir ../tmp/technical-browser` | Chrome 148.0.7778.169 30 desktop + 31 phone, Firefox 160.0 30 desktop + 31 phone, 122 passed and 0 failed. | [Browser log](evidence/technical-browser.log) |

The pull request shows the GitHub Actions results for this branch. See [prior browser matrix](VALIDATION_RESULTS.md#browser-matrix-at-review-date) for the historical four-version run.
