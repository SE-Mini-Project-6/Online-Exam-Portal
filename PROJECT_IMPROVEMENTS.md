## Project Improvements — Before vs After

During Sprint 1 and Sprint 2, we improved the Online Exam Portal in terms of performance, security, reliability, exam management and testing.

### 1. Performance Improvements

Tested locally using PostgreSQL with 50 simulated students.

| What we improved                       | Before  | After  | Improvement         |
| -------------------------------------- | ------- | ------ | ------------------- |
| Question loading time                  | 2856 ms | 780 ms | 72.7% faster        |
| Answer autosave time                   | 1040 ms | 719 ms | 30.8% faster        |
| Requests handled per second            | 19.19   | 36.36  | 89.5% increase      |
| Database queries for visited questions | 11      | 6      | 45.5% fewer queries |
| Database queries for autosave          | 16      | 14     | 12.5% fewer queries |

We reduced unnecessary database operations and locking, making question loading and answer saving faster.

**Evidence:** [Performance Test Results](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/docs/FINAL_TECHNICAL_COMPLETION.md#final-sign-off-round)

### 2. Database Reliability

| Before                                                                                           | After                                                                                          |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| 476 out of 500 requests failed in an initial SQLite concurrency test because of database locking | After fixing the locking configuration, the repeated tests completed with 0 failed requests    |
| Database writes could fail under heavy concurrent access                                         | Database transactions were configured to queue competing writes instead of failing immediately |

**Evidence:** [Database Reliability Testing](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/Deliverable-4-Test-Validation/performance_reliability_validation.md)

### 3. Security Improvements

| Before                                                                  | After                                                                                   |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Logout could be performed using GET and was exempt from CSRF protection | Logout now requires POST with CSRF protection                                           |
| Access restrictions needed stronger verification                        | Admin/student access and ownership restrictions are enforced and tested                 |
| Submission protection needed stronger verification                      | Submitted answers cannot be modified or submitted again                                 |
| HTTPS settings were not fully verified through live local requests      | HTTPS redirects, secure cookies, HSTS and CSRF protections were verified in local tests |

**Evidence:** [Security Testing Report](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/Deliverable-4-Test-Validation/security_regression_traceability.md)

### 4. Exam System Improvements

| Sprint 1                              | Sprint 2 / Final Implementation                     |
| ------------------------------------- | --------------------------------------------------- |
| Manual exam submission                | Automatic submission when the timer expires         |
| Basic question navigation             | Question navigation with mark-for-review status     |
| Student answers saved during the exam | Persistent answers with server-side deadline checks |
| Automatic grading after submission    | Grading with admin-controlled result release        |
| Basic exam and question management    | Admin submissions dashboard with student scores     |
| Basic student exam workflow           | Complete student result viewing after release       |

**Evidence:** [Sprint 1 Demo](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/Project_Demo/Sprint_1_Demo.mp4) | [Sprint 2 Demo](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/Project_Demo/Sprint_2_Demo.mp4)

### 5. Testing Improvements

| Testing                                | Earlier                                          | Final Result                                         |
| -------------------------------------- | ------------------------------------------------ | ---------------------------------------------------- |
| Django automated tests                 | 145 passing tests                                | 147 passing tests                                    |
| Browser testing                        | 122 passing checks in an earlier two-browser run | 252 passing checks across four browser versions      |
| Usability testing                      | No completed five-user walkthrough recorded      | 5 out of 5 students completed the tasks without help |
| Average usability task completion time | Not measured earlier                             | 83 seconds                                           |

The browser testing covered desktop and mobile screen sizes using Chrome and Firefox.

**Evidence:** [Django Tests](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43889325603) | [Browser Tests](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43889325512) | [Usability Results](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/docs/VALIDATION_RESULTS.md)

### 6. Code Maintainability

| Before                                                                                                             | After                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Adding a new question type required changes across 4 application modules and 1 migration in the initial experiment | After refactoring, an isolated True/False prototype required only 1 module change and no new migration |

This reduced the effort needed to support another question type in the future. The True/False type was tested separately and was not added to the released portal.

**Evidence:** [Maintainability Results](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/docs/FINAL_TECHNICAL_SIGNOFF_CHECKLIST.md)

### Summary

Over the two sprints, we:

- Reduced question loading time by **72.7%** and autosave latency by **30.8%** in the measured PostgreSQL comparison.
- Improved measured throughput by **89.5%**.
- Fixed database locking errors observed during SQLite load testing.
- Improved login security, authorization and submission protection.
- Added automatic exam submission, review flags and admin-controlled results.
- Passed **147 automated Django tests** and **252 browser checks**.
- Completed usability testing with **5 students**, all completing the required tasks without assistance.
- Reduced the number of modules needed to prototype a new question type.

*Performance figures are from local benchmark tests. These improvements do not imply that every non-functional acceptance target was met.*

**Full technical evidence:** [Final Technical Report](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/blob/main/docs/FINAL_TECHNICAL_COMPLETION.md)
