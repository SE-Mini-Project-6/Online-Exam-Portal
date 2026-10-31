# Admin Submissions Dashboard — Validation Note

## Requirement

Staff users need to review the attempt roster, submission state, and score for a selected exam. Non-staff users must be denied access. This implements the admin submissions-list capability described in SRS FR-17 and the Deliverable 3 result/submission component.

## Implementation

- Staff-only page: `/accounts/admin-submissions/`; choose an exam with the selector or follow a per-exam link from the admin dashboard.
- The roster includes active non-staff accounts. Students without an attempt show **Not started**; saved attempts show **In progress**; finalized attempts show **Submitted**.
- A score is shown only for submitted attempts, formatted as `score / question count`. Submission time is shown when present. Unreleased student results remain controlled separately by the existing result-release flag.
- Anonymous requests follow the normal login redirect. Authenticated non-staff requests receive HTTP 403.

## Automated coverage

`accounts/test_submissions.py` covers staff access, selected-exam roster isolation, submitted score and time data, in-progress and not-started states, student denial, anonymous redirect, and admin dashboard links.

Execution on 31 October 2026: the focused dashboard tests passed (4 tests), and the full `accounts` suite passed (38 tests). The full project suite ran 140 tests and had one environment-dependent failure in the pre-existing `exams.test_performance.test_measure_load_reports_every_target_and_cleans_up`: the sandbox denied the test server's local socket bind with Windows `WinError 10013`. The other tests completed without reported failures. A real browser walkthrough was not run; the steps below are the manual verification checklist.

Run from `Online_Exam_Portal/`:

```powershell
python manage.py test accounts.test_submissions
```

## Manual browser verification

1. Sign in as staff and open **View Submissions** from the admin dashboard, or use **View submissions** beside a configured exam.
2. Select an exam and confirm each active student appears with the correct state. A submitted attempt displays its score and submission time; an unfinished attempt has no score.
3. Select another exam and confirm the roster reflects that exam’s attempts.
4. Sign in as a student and open `/accounts/admin-submissions/`; confirm HTTP 403. Sign out and open it again; confirm redirect to `/accounts/login/`.

## Design alignment

The implementation uses an authenticated Django HTML view and ORM query, consistent with the repository’s current MVT approach. The design documents describe a broader REST-oriented result/submission component, but no admin submissions API was required by this story; this is a documented interface-scope deviation, with the admin UI requirement implemented server-side.
