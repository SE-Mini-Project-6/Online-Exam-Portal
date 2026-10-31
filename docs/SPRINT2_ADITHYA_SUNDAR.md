# GitHub Issue: Add admin submissions dashboard
User story
As a user or team member, I need add admin submissions dashboard so the Online Exam Portal satisfies its documented requirements.

Acceptance criteria
Admin sees attempt roster, submission state and score for chosen exam; non-admin access denied.
Include automated/manual test evidence appropriate for the change.
Update docs and link any design deviation, if applicable.

Definition of done
Assignee opens a branch and pull request; repo owner reviews and merges after checks pass. Do not close this issue before the stated criteria are met.

# Resolved PR:
## Summary

Adds a staff-only submissions dashboard for selecting an exam and reviewing the active student roster, attempt state, submission time, and score for submitted attempts. Students without an attempt are listed as **Not started**; unfinished attempts show **In progress**.

The dashboard is linked from the admin home page and each configured exam. Non-staff users receive HTTP 403; anonymous visitors are redirected to login.

## Verification

- Dashboard tests: 4 passed
- Accounts suite: 38 passed
- Full suite: 139 passed; one existing load-measurement test failed because the environment blocked a local socket bind (`WinError 10013`)
- `manage.py check`: clean
- Migration check: no changes detected

# GitHub Issue: Enforce role, ownership and exam-access authorization
User story
As a user or team member, I need enforce role, ownership and exam-access authorization so the Online Exam Portal satisfies its documented requirements.

Acceptance criteria
Students cannot access other attempts; students cannot change exams or release results; access checks are server-side.
Include automated/manual test evidence appropriate for the change.
Update docs and link any design deviation, if applicable.

Definition of done
Assignee opens a branch and pull request; repo owner reviews and merges after checks pass. Do not close this issue before the stated criteria are met.

# Resolved PR
## Description

Hardens server-side authorization for exam access and clarifies how staff can access exam metadata. Staff may request exam metadata as JSON only with `GET`; attempts to access the student exam flow through other methods are denied. Submitted attempts return a JSON conflict when requested in JSON mode.

Adds regression tests covering the staff restriction, student-scoped result access, and rejection of answer autosaves that pair an attempt with a question from another exam. Updates the security traceability documentation with current behavior, test evidence, and the existing implementation notes.

## Verification

- 43 authorization-related tests passed across security regression, autosave, results, and submissions.
- Django system check reported no issues.
- Full suite: 144 passed; one existing performance test failed because the Windows sandbox denied local socket binding (`WinError 10013`).