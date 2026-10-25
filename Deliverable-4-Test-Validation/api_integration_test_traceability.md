# API Integration and Test Traceability



## API setup



The current exam API is implemented in Django. Sign in first; these routes require an authenticated user. To request JSON, use `?format=json` or send the `Accept: application/json` header.



Run the app from the `Online_Exam_Portal` folder:



```text

python manage.py runserver

```



## API contracts



| Request | Successful response | Other responses |

|---|---|---|

| `GET /exams/available/?format=json` | `200`; JSON object containing an `exams` list with each exam’s ID, title, duration, availability times, and status. | Unauthenticated users are redirected to login. |

| `GET /exams/<exam_id>/take/?format=json` | `200`; JSON exam details when the exam is available. | `403` if the exam is upcoming or expired; `404` if the exam ID does not exist. Unauthenticated users are redirected to login. |

| `PATCH /api/v1/attempts/{attempt_id}/answers/{question_id}` | Send JSON with `selectedOption` (`A`–`D` or `null`) and/or `markedForReview` (`true` or `false`). Returns the saved answer and display state. | `400` invalid JSON or fields; `401` not signed in; `403` wrong student or exam unavailable; `404` attempt/question not found; `405` method isn’t PATCH; `409` attempt already submitted. |

## Test traceability



| Existing test | Requirement(s) | Evidence |

|---|---|---|

| `test_available_exams_json_api` | FR-05, SEC-REQ-02, SEC-OBJ-01 | Checks the JSON exam list and the available, upcoming, and expired statuses. |

| `test_exam_window_enforcement_json_api` | FR-05, SEC-REQ-02, SEC-OBJ-01, NFR-04 | Checks JSON responses for active, upcoming, and expired exams. |

| `test_admin_login_valid`, `test_student_login_valid` | FR-01 | Checks that staff and students can sign in with valid credentials. |

| `test_valid_exam_configuration_is_saved` | FR-02 | Checks that a valid exam configuration is saved. |

| `test_staff_can_create_edit_delete_questions` | FR-03 | Checks staff question create, edit, and delete. |

| `test_confirm_page_and_submission_lock` | FR-04 | Checks submission confirmation and that a submitted attempt is locked. |

| `test_grading_unanswered_zero_and_review_flag_ignored`, `test_all_correct_answers_score_three` | FR-11, FR-13 | Checks grading for incorrect, unanswered, and all-correct answers. |

| Routes are declared in exams/urls.py and exams/api_urls.py. Exam pages, question management, submission, and grading use Django views; answer autosave uses the versioned JSON API in exams/api.py. |

## Automated validation evidence

- Command: `python manage.py test`
- Result: 41 tests passed on 25 October 2026.
- The suite covers login, exam availability, question management and navigation, answer persistence, submission, and grading.
- The Sprint 1 demo flow is supported by these automated tests; a manual browser walkthrough was not run.



## Manual demo path



1. From the `Online_Exam_Portal` folder, run `python manage.py runserver`.
2. Sign in as staff at `/accounts/login/`, create an exam that is available now, and add at least two questions.
3. Sign out, sign in as a student at `/accounts/student-login/`, and open `/exams/available/`.
4. Start the active exam. Choose an answer and confirm the page shows it as saved; navigate away and back to verify it remains.
5. Choose “Save and review submission,” review the answers, then confirm submission.
6. Confirm the submitted page appears and the attempt is locked. Automated tests verify the grading score.
7. Check `/exams/available/?format=json` and `/exams/<exam_id>/take/?format=json`; confirm an active exam is available and an upcoming or expired exam is blocked.



Question management, submission, and grading are available through the authenticated exam pages. They do not have JSON endpoints. Answer autosave uses the PATCH API documented above.

