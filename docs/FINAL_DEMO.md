# Final demonstration and viva

Use a local database with a staff account and a student account. Prepare an open exam with three questions and a second exam with a one-minute timer. For the result release demonstration, prepare a closed exam with a submitted attempt. Preparation keeps the live walkthrough short and avoids changing any participant's answers or grades.

| Time | Show | Explain |
|---|---|---|
| 0:00–0:30 | Home page and staff dashboard | Staff configure a duration, availability window and four-option questions. Students see exams according to the availability window. |
| 0:30–1:20 | Student exam view | Select an answer, mark for review, navigate, and refresh. Point to the saved answer and question grid. |
| 1:20–2:00 | Submission and results | Confirm one submission. Show an unreleased result, then release grades for the prepared closed exam as staff and show the student's own score. |
| 2:00–2:30 | Timer and late writes | Show the Sprint 2 timeout sequence. The server stores the deadline, grades the attempt, and rejects late writes. An unattended attempt requires the scheduled finalizer. |
| 2:30–3:00 | Test evidence and limitations | Show the automated regression run, the browser matrix and the load report. State that the five-person study is pending and the measured load thresholds remain unmet. |

## Evidence to have open

- [Merged evaluation changes](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pull/56) and [passing post-merge Django CI](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43594192327).
- [Validation results](VALIDATION_RESULTS.md), [test cases](TEST_CASE_EXECUTION.md), and the [design deviation register](DESIGN_DEVIATIONS.md).
- [Usability protocol and session log](../Deliverable-4-Test-Validation/usability_browser_verification.md) and [performance measurements](../Deliverable-4-Test-Validation/performance_reliability_validation.md).

## Aditya-TJ viva notes

- Start with the Test Plan, then use TC-09 as an example of mapping a security requirement to an executable check. Explain how a second authenticated student is blocked from changing the first student's attempt and how the test checks that data is unchanged.
- For usability and browser verification, show a 375-by-812 capture. Explain why exact viewport dimensions matter, what the scripted checks covered, and what five first-time participants still need to demonstrate.
- For load testing, explain the one-student baseline, the 50-student run and the difference between mean and worst-case latency. The shorter database write transaction improved the measured question-page mean, but some requests still exceeded their targets. Quote the measured results and environment.
- Open your [security regression PR](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pull/46), [usability PR](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pull/49) and [performance PR](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pull/51). Be ready to explain the story estimate, a blocker, and how you checked the outcome.

## Decisions for the team review

- Record the attendees, final reviewed commit, CI link, accepted deviations, remaining owners and release decision in the [freeze record](SPRINT2_REVIEW_AND_FREEZE_DRAFT.md).
- Link the GitHub Project and both sprint views in the [team acceptance record](TEAM_ACCEPTANCE.md). Preserve the original sprint dates if the board is assembled retrospectively.
- Keep reported failures and missing evidence visible until the requirement is verified or the evaluator accepts a deviation.
