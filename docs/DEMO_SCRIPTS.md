# Recording and viva scripts

These are recording plans, not submitted video evidence. Use a disposable demo database, prepared accounts and exams; do not display passwords or connection secrets. Capture the real application and explain limitations. Do not stretch or pad the existing 86-second recording to pretend it represents two sprint deliverables.

## Sprint 1: 60-second working-product demonstration

| Time | Action / narration |
|---|---|
| 0-8 s | State project, team and that this is a retrospective Sprint 1 demo. Show staff login/dashboard. |
| 8-22 s | Create an exam with duration/window; open prepared question list; show four options and one correct key. |
| 22-42 s | Student login; open available exam; answer Q1, jump Q3, change answer, refresh to show persistence. |
| 42-54 s | Open submission confirmation and finalize. Explain one-time grading and locked answers. |
| 54-60 s | Show passing Sprint 1 tests/CI and name the relevant contribution PRs. |

## Sprint 2: 120-second working-product demonstration

| Time | Action / narration |
|---|---|
| 0-10 s | Identify retrospective Sprint 2 demo and additional capabilities. |
| 10-35 s | Student answers/marks questions; show all five grid states and compact mobile layout; refresh persistence. |
| 35-60 s | Use a prepared one-minute exam already close to expiry. Show countdown, server finalization and rejected late write. Explain that abandoned tabs need the scheduled finalizer. |
| 60-85 s | Show staff roster, withheld student score, then an ended demo exam with all attempts submitted; release and show student's own result. |
| 85-105 s | Show current CI result and measured performance/browser reports. Explicitly identify pending participant study or unmet NFR targets if still unresolved. |
| 105-120 s | Show accepted deviation register, linked board and actual freeze record if available. Otherwise identify those as pending rather than completed. |

Use prepared separate exams to avoid waiting for full windows on camera. Do not change stored answers or scores outside application actions to stage a pass.

## Individual viva preparation

- Aditya-TJ: explain Test Plan sections 3/4/5/5.1, FR/NFR mapping, negative security tests, 50-user baseline comparison, why an unmet target is not a pass, and why Selenium does not replace five participants.
- Aditya Jaiswal: explain navigation/autosave, review-state precedence, student result confidentiality and recording evidence.
- Adithya Sundar: explain login/role boundaries, exam validation, window authorization, roster and result-release preconditions.
- Abhishek Anand: explain model relationships, MCQ validation, transactional grading, server deadlines, scheduler dependency and freeze procedure.

Each person should open their authored PR, explain a meaningful changed function and test, describe a blocker and show how the story estimate/sprint plan relates to delivered work. Use real histories and decisions.
