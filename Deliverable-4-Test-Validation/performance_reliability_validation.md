# Performance and Reliability Validation (Sprint 2, issue #28)

Requirements: NFR-01, NFR-02, NFR-04, NFR-06. Owner: @Aditya-TJ.

**Summary.** Absolute response-time targets (NFR-01, NFR-02) are met at 50 concurrent students when students
pace themselves like real test takers. They are not met in a worst-case run where every student sends requests
back to back. The relative-growth target (NFR-06, no more than 20% rise in mean response time) is **not met** in
any 50-student run on the current SQLite and development-server setup. NFR-04 is covered by existing automated
tests. Details and caveats follow.

## 1. Method

`python manage.py measure_load` (new, `exams/management/commands/measure_load.py`):

- Creates a throwaway exam with 10 questions and one student with an open attempt per simulated user, then deletes
  all of it afterwards.
- Starts Django's threaded WSGI server on a free local port and sends real HTTP requests, so middleware, sessions,
  CSRF, templates and the database are all exercised.
- Each student repeats a round: `GET /exams/<id>/take/?question=N` (the question page, NFR-01) followed by
  `PATCH /api/v1/attempts/<id>/answers/<qid>` (autosave, NFR-02), with a random think time of 0.5x to 1.5x of
  `--think-ms` between rounds.
- Runs once with 1 student (baseline), then with 50, and checks the targets below. Server-side exceptions are
  captured and printed.

```powershell
cd Online_Exam_Portal
python manage.py migrate
python manage.py measure_load --users 50 --rounds 15 --think-ms 3000   # realistic pacing
python manage.py measure_load --users 50 --rounds 20                    # worst-case stress
```

Environment: Windows 11, Python 3.13.13, Django 5.2.18, SQLite file database, client and server in one Python
process on the same laptop. No network latency is included, and client threads compete with the server for the
same interpreter, so the numbers overstate server load and understate network cost.

## 2. Results

Times in milliseconds. "1 user" is the baseline run, "50 users" the concurrent run.

### Realistic pacing: 3 s average think time, 15 rounds per student (750 page loads, 750 saves at 50 users)

| Measure | 1 user mean | 50 users mean | 50 users median | 50 users p95 | 50 users max | Growth of mean |
|---|---|---|---|---|---|---|
| Question page | 28.3 | 47.8 | 34.5 | 96.9 | 947.0 | +69% |
| Autosave | 15.7 | 39.7 | 29.0 | 107.6 | 697.3 | +152% |

No failed requests.

### Faster pacing: 1 s average think time, 15 rounds

| Measure | 1 user mean | 50 users mean | 50 users median | 50 users p95 | 50 users max | Growth of mean |
|---|---|---|---|---|---|---|
| Question page | 41.3 | 310.7 | 55.0 | 1561.1 | 8094.7 | +652% |
| Autosave | 21.8 | 241.3 | 38.1 | 1439.9 | 8302.3 | +1009% |

No failed requests.

### Worst-case stress: no think time, 20 rounds

| Measure | 1 user mean | 50 users mean | 50 users median | 50 users p95 | 50 users max | Growth of mean |
|---|---|---|---|---|---|---|
| Question page | 22.1 | 849.3 | 76.1 | 5051.4 | 18933.0 | +3746% |
| Autosave | 12.8 | 666.2 | 56.5 | 3731.1 | 19036.5 | +5098% |

No failed requests. This is 50 students sending about 100 requests each with no pause, far above a real exam.

## 3. Verdict per requirement

| Requirement | Target | Result | Verdict |
|---|---|---|---|
| NFR-01 | Question page within 3 s, up to 50 concurrent students | 3 s pacing: p95 96.9 ms, max 947 ms. 1 s pacing: p95 1561 ms but max 8095 ms. Stress: p95 5051 ms | **Met** at 3 s pacing. **Not met** at 1 s pacing (max) and in stress (p95 and max) |
| NFR-02 | Autosave within 2 s | 3 s pacing: max 697 ms. 1 s pacing: max 8302 ms. Stress: max 19037 ms | **Met** at 3 s pacing. **Not met** at 1 s pacing and in stress |
| NFR-06 | 50 concurrent attempts without more than 20% rise in average response time | +69% (page) and +152% (autosave) at 3 s pacing; far higher at faster pacing | **Not met** |
| NFR-04 | Exam available for 100% of its window | Window start/end enforced on the server, no time-of-check gaps found in tests (section 5) | **Met** by automated tests. Not measured under load or across a real deployment |

Why NFR-06 fails even though absolute times are small: the baseline is a single user on an idle server at 16 to
28 ms, so a 20% allowance is 3 to 6 ms. Any queueing among 50 writers on one SQLite file exceeds that. The mean
at 3 s pacing is still under 50 ms. Whether the SRS intends a relative or an absolute reading is a question for
the team; this report states the literal result and does not claim a pass.

The stress run is not representative of an exam. A real student answers a question every 20 to 60 seconds, so the 3 s
pacing run is itself conservative. That is an argument for the target being reachable in practice, not a
measurement of it. A real 50-student test on the target deployment (PostgreSQL, production WSGI server, separate
client machines) has not been run.

## 4. Defect found and fixed: `database is locked`

The first load run on the unchanged code failed badly: with 50 concurrent students, 476 of 500 requests (5 rounds
each) returned HTTP 500 with `OperationalError: database is locked`. Cause: SQLite default deferred transactions.
`take_exam` and the autosave endpoint read first and then write inside one transaction. When another writer holds
the lock, SQLite refuses the read-to-write upgrade immediately and ignores the busy timeout.

Fix (`Online_Exam_Portal/settings.py`): `transaction_mode: IMMEDIATE`, `journal_mode=WAL` and `timeout: 30`.
Writers now queue rather than fail. After the change all three runs above completed with zero failed requests.
The price is the queueing delay visible in the 1 s and 0 s pacing tables.

## 5. Reliability evidence (NFR-04)

Existing automated tests that pin the availability window and the lock-in behaviour, all passing:

| Behaviour | Test |
|---|---|
| Early access is blocked with 403 | `exams/tests.py::test_early_access_is_blocked_on_server_with_403` |
| Access after the window is blocked with 403 | `exams/tests.py::test_expired_access_is_blocked_on_server_with_403` |
| Both the `/take/` and detail URL enforce the window | `exams/tests.py::test_detail_url_route_enforces_windows` |
| Answers rejected after the window closes | `exams/tests.py::test_answers_are_not_accepted_after_window_closes` |
| Autosave blocked after finalisation and outside the window | `exams/test_autosave.py::test_saves_blocked_after_finalization_and_outside_window` |
| Submission rejected outside the window | `exams/test_sprint1_abhi.py::test_submission_rejected_outside_exam_window` |
| Stored deadline never beyond the window | `exams/test_sprint2_timer.py::test_exam_window_caps_stored_deadline` |

Not covered: uptime of a deployed instance, restart or failover behaviour, and scheduled maintenance handling.
The dev server is not a deployment, so a 100% availability claim for production cannot be made from this
evidence.

Single-request autosave latency without network or concurrency (`python manage.py measure_autosave`, from Sprint 1)
remains available and is well under 2 s.

## 6. Automated tests added

`exams/test_performance.py`:

- `test_measure_load_reports_every_target_and_cleans_up` runs the harness end to end with one student and checks
  that the report contains each NFR check, no errors occurred and no data is left behind.
- `test_sqlite_writers_queue_instead_of_failing` pins the SQLite options that fixed the lock failures.

The 50-user run itself is not part of the unit suite. Django's in-memory test database uses shared-cache table
locks that ignore the busy timeout, so concurrent writers fail there regardless of the fix, and a 50-user run
takes minutes. It is a manual/CI-optional measurement against the file database.

Full suite after this story: 136 tests, all passing.

## 7. Design deviations and follow-ups

| Item | Deviation | Follow-up |
|---|---|---|
| Database | SRS/SADS assume a relational database for production. Development uses SQLite, which serialises writers. NFR-06 is not met on it | Run the same harness against PostgreSQL and a production WSGI server (gunicorn/uvicorn) and record the result before claiming NFR-06 |
| Server | Measured on Django's development-style threaded server in a single process | Repeat with multiple workers on separate load-generating machines |
| NFR-06 wording | A 20% relative rise is nearly impossible from a very fast single-user baseline | Team to confirm whether the intended test is relative or an absolute ceiling |
| Question page writes | Opening a question writes the "visited" flag, so every page view is a database write | Candidate optimisation if PostgreSQL results are still short of target |

See also `docs/SPRINT2_ARCHITECTURE_DEPLOYMENT.md` (deployment checklist, item 8 asks for concurrency checks against
the target database).
