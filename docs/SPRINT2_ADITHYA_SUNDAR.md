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