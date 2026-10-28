# Sprint 2 #22 â€” Server-authoritative timer and auto-submit

**Owner:** @Abhishekanand19. **Requirements:** FR-12, SEC-REQ-03.

## Implemented behavior

- The first student access saves `Attempt.started_at` and `Attempt.deadline_at`, using only the server's clock. Deadline = earlier of start plus exam duration or the exam availability end.
- Navigating, refreshing, changing a browser clock, or sending a forged answer request never extends the stored deadline. The system may shorten it if an admin shortens the exam window.
- Shared `exams/timing.py` locks the attempt in a database transaction, grades saved answers once, and marks the attempt submitted. Manual submission, page access and autosave PATCH all enforce the same finalization state.
- The browser countdown shows remaining time and redirects to the submission endpoint on expiry. This is advisory: the server checks the deadline independently.
- For abandoned browser tabs, the scheduler must periodically run `python manage.py finalize_expired_attempts`. Without a configured scheduler, expiry is still enforced on the next page/API request, but records may remain open in storage until triggered.
- Retakes and student score-release controls belong to other stories.

## Tests and manual acceptance

Run `python manage.py migrate`, `python manage.py makemigrations --check --dry-run`, `python manage.py check`, `python manage.py test exams.test_sprint2_timer`, and `python manage.py test`.

The six regression cases cover first access and refresh, availability cap, automatic grading/locking, late PATCH rejection, duplicate submission, and abandoned-attempt cleanup. Record actual test/CI results rather than assuming a pass.

Manual walkthrough: create a 1-minute exam with at least one MCQ, enter it as a student, answer the question and watch countdown expire. Confirm the submission page, verify stored score and timestamp, and confirm POST/PATCH cannot alter it. Repeat with a manually submitted exam.

## Design deviations / limitations

- Legacy Sprint 1 attempts with no recorded start time start timing at their first access after migration (historical timing is unavailable).
- SQLite is suitable for the coursework demo but production-grade race testing should use PostgreSQL. Row locking in SQLite is not equivalent to PostgreSQL.
- The application has no continuously running timer worker; the provided management command requires external scheduling for unattended finalization.
- Merge any parallel teammate migration heads using `python manage.py makemigrations --merge` after reviewing both branches, before the release freeze.
