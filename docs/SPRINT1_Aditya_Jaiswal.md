# Answer persistence and autosave (FR-07, NFR-02)

Implements the "Answer / Review / Auto-save" interaction of the Software Architecture &
Design Specification (section 4.4, API 4.7.2, errors 4.8) on top of the existing
`Attempt` and `Answer` models.

## Behaviour
- Choosing an option, or toggling *Mark for review*, is sent immediately to the server. The
  page shows "Saving...", then "Saved (N ms)". Network failures are retried up to 3 times.
- Answers live in the database, so a refresh, a new login or another device shows the saved
  selections. A student can change an answer any number of times until the attempt is submitted.
- The existing form buttons (Previous/Next, grid, Save and review submission) still save the
  current answer as before, so the page also works without JavaScript.

## API
`PATCH /api/v1/attempts/{attemptId}/answers/{questionId}`

    { "selectedOption": "C", "markedForReview": true }      (either key may be sent alone;
                                                              selectedOption null clears the answer)
    200 { "questionId": 7, "selectedOption": "C", "markedForReview": true,
          "displayState": "ANSWERED_MARKED_FOR_REVIEW", "savedAt": "..." }

Errors use `{ "error": { "code", "message", "requestId" } }`:

| HTTP | Code | When |
|---|---|---|
| 400 | VALIDATION_ERROR | bad JSON, option outside A-D, wrong type, empty body |
| 401 | AUTHENTICATION_REQUIRED | not signed in |
| 403 | FORBIDDEN | attempt belongs to another student |
| 403 | EXAM_NOT_AVAILABLE | outside the exam window |
| 404 | ATTEMPT_NOT_FOUND / QUESTION_NOT_FOUND | unknown attempt, or question not in this exam |
| 409 | ATTEMPT_ALREADY_FINALIZED | attempt already submitted |

Every response carries a `Server-Timing: save;dur=<ms>` header.

## Differences from the design specification
- **Deadline:** the spec computes `start_time + duration_minutes`. `Attempt` has no start time
  yet, so the server enforces the exam availability window only. Per-attempt deadlines belong
  with the timer / auto-submit work.
- **Navigator state:** `displayState` follows spec 4.6 but `Answer` has no `visited` field, so a
  saved row counts as visited (`NOT_ANSWERED`). A row exists only once the student interacted.
- **Schema:** `Answer.saved_at` (named in the spec's data design) was added (migration 0004).

## Measuring autosave latency
Target (design spec, NFR-02): each change is persisted well inside 2 seconds.

    python manage.py measure_autosave --count 200

It creates a throwaway user, exam and attempt, sends the PATCH requests, prints
min/median/p95/max against the 2000 ms target, and deletes its data.

Results in the development environment (SQLite, no network, not production):

| Measure | Result |
|---|---|
| Server-side, 200 saves: median / p95 / max | 8.2 / 10.0 / 14.4 ms |
| Browser round trip on localhost (3 saves) | 34, 19 and 32 ms |

Re-run on the deployed setup before quoting these for a real 50-student load.

## Manual test
1. As a student, open an active exam with 5 questions and pick an answer on question 3.
2. Confirm "Saved (N ms)" appears. Change the answer and confirm it saves again.
3. Tick *Mark for review*; confirm it saves, and the answer is still selected.
4. Refresh: the latest answer and the review tick are still there.
5. Jump to question 5 and back to 3 using the grid: still there.
6. Log out and in again, reopen the exam: still there.
7. Submit the exam, then try to change an answer in the page: it is refused (409).
