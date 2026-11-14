# Implementation and design deviation register

Revision 1.1, 14 November 2026. This records facts for review; **team/evaluator acceptance is pending**. Original Part 1 documents remain the historical baseline. Current execution instructions are in [TEST_CASE_EXECUTION.md](TEST_CASE_EXECUTION.md).

| ID | Baseline | Implemented behavior | Consequence / verification |
|---|---|---|---|
| D-01 | REST/JSON catalogue for login, CRUD, submit and results | Django MVT/session authentication and server-rendered form routes. Versioned JSON PATCH API for autosave; optional JSON exam metadata/list. | Use current route table; do not execute obsolete design URLs or expect JSON from HTML forms. Security remains server-side. |
| D-02 | Explicit ADMIN/STUDENT role field | Django `is_staff` distinguishes roles. | Staff restricted from student attempt writes. Security regression suite covers both role directions and ownership. |
| D-03 | IN_PROGRESS, SUBMITTED and AUTO_SUBMITTED states | Manual and timeout finalization both persist SUBMITTED. | UI/locking work for both. Database does not distinguish submission reason. TC-05 must expect SUBMITTED unless a future reviewed schema change introduces a separate state. |
| D-04 | Deadline = start + duration | Stored server deadline = min(start + duration, exam.end_at); window shortening may shorten it, never extend it. | Consistent with availability guard; timer suite tests the cap, refresh and late writes. |
| D-05 | Automatic finalization without further student action | Request paths enforce expiry; `finalize_expired_attempts` finalizes abandoned sessions when scheduled. | Configure a real scheduler before claiming unattended finalization. A manual command test proves logic, not an installed scheduler. |
| D-06 | JSON 403 RESULTS_NOT_RELEASED | Own-student HTML result page displays a withheld-result message with 200 and no score. | Confidentiality preserved; response contract differs. Student results tests check that grades are not leaked. |
| D-07 | Login/authorization errors uniformly JSON 401/403 | Form login redirects anonymous users; autosave returns JSON 401/403. Missing/foreign resource responses depend on actual endpoint. | Test actual routes and content, not an assumed global REST error envelope. |
| D-08 | Thin controllers, separate services/repositories | Django views contain orchestration, forms/models validate, ORM handles storage, shared timing helper finalizes. | NFR-05's <=2-module change claim is not demonstrated. Do not claim formal layered-design compliance from folder names alone. |
| D-09 | PostgreSQL/Linux/HTTPS target | Default SQLite local demo; PostgreSQL selected by environment; deployment configuration documented. | Local HTTP tests do not establish TLS or deployed uptime. Production secret, hosts, certificate, server and scheduler still need target-environment evidence. |
| D-10 | NFR-06 <=20% mean growth at 50 students | Historical measurements exceed the threshold in multiple runs. | Measurement story complete; target not accepted as passed. Keep raw remeasurements and seek a fix or explicit evaluator decision. |
| D-11 | Latest two versions of Chrome and Firefox; five new users | Existing browser evidence covers one installed version of each at two widths; participant study not conducted. | Automated scripts cannot substitute for real participant observations or a second-version matrix. |
| D-12 | Final result denominator fixed to submitted exam | Result total uses current question count. | Avoid editing exam questions after attempts begin for the demo. Persisting an immutable exam/score snapshot is a possible future improvement. |

Approval record: pending. At the team review, record reviewer, date, accepted/rejected IDs, rationale and any evaluator permission. Approval must be real; this file is not an approval declaration.
