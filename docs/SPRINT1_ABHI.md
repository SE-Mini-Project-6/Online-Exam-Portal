# Sprint 1 — Abhi's deliverables (Online Exam Portal)

**GitHub issues:** #9 (NFR-05/EI-02), #12 (FR-04), #16 (FR-11/SEC-REQ-03), #17 (FR-13). 12 story points total.

## Implemented scope

- **#9:** Reuse the team's existing Django MVT app and existing Exam/Question models; add relational `Attempt` and `Answer` models and migration `exams.0003_attempt_answer`.
- **#12:** Staff-only MCQ create, edit, delete, and list views. Every question has fields A/B/C/D, each nonblank, and exactly one correct-option key from A-D. Model validation is enforced on save. Links are available beside configured exams on the admin dashboard.
- **#16:** A student saves answers while navigating, chooses **Save and review submission**, sees a server-rendered confirmation page, then submits. A submitted attempt is locked; repeated submission and post-submission writes are rejected on the server.
- **#17:** During the transactional submission, the server compares stored answers against the correct option. One point per correct response; incorrect/unanswered receive zero. Review flags have no effect. Score and submission timestamp persist on the attempt.

## Routes

- `GET /exams/<exam_id>/questions/` — staff-only question list
- `GET|POST /exams/<exam_id>/questions/add/` — staff-only MCQ creation
- `GET|POST /exams/<exam_id>/questions/<question_id>/edit/` — staff-only MCQ edit
- `GET|POST /exams/<exam_id>/questions/<question_id>/delete/` — staff-only delete (POST required)
- `GET|POST /exams/<exam_id>/take/` — student attempt, navigation and saved answers
- `GET|POST /exams/<exam_id>/submit/` — confirmation and one-time final submission

## Setup and automated tests

From repository root:

```powershell
cd Online_Exam_Portal
python -m pip install "Django>=5.2,<5.3"
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py runserver
```

Dedicated tests: `python manage.py test exams.test_sprint1_abhi`.

## Manual verification

1. Sign in as **staff**. Create a valid exam (duration 20 minutes; window covering the present time). Click **Manage questions** beside the exam.
2. Create a four-choice question with correct choice A. Edit and delete a practice question; ensure invalid (blank) choices are rejected.
3. Log in as a **student**. Open the active exam, answer Q1 and mark it for review. Navigate to other questions; verify answers persist.
4. Click **Save and review submission**. Verify the correct answered count, then confirm.
5. Verify the confirmation page, saved score, and locked attempt; repeat submission and answer mutation should not succeed.
6. Run automated tests, attach successful CI output to the PR, and request another admin's review before merging.

## Scope and design notes

- Navigation already existed in teammate PR #38. This Sprint 1 work replaces **session-only** answers with relational DB persistence; the legacy session key is still written for compatibility with previously merged tests. The database is authoritative.
- Only one Attempt per student and exam is permitted. A later requirement could support explicit retakes; these are not part of this sprint.
- The grading score is calculated and stored at submission, but **result release to students** is outside this story. Students see confirmation, not an unreleased grade.
- **Automatic timer/timeout submission belongs to Sprint 2 issue #22** and is intentionally not implemented here.
- Changes to existing SRS/SAD/Test Plan documents must be noted for the team's final demo if they conflict with this persistent-attempt design.

### Test evidence

- `python manage.py test`: 43 tests passed.
- `python manage.py test exams.test_sprint1_criteria`: 2 exam admin edit/delete tests passed.
- GitHub Actions runs the Django test suite on pushes and pull requests.
