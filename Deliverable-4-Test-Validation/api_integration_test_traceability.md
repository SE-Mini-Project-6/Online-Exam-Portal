\# API Integration and Test Traceability



\## API setup



The current exam API is implemented in Django. Sign in first; these routes require an authenticated user. To request JSON, use `?format=json` or send the `Accept: application/json` header.



Run the app from the `Online\_Exam\_Portal` folder:



```text

python manage.py runserver

```



\## API contracts



| Request | Successful response | Other responses |

|---|---|---|

| `GET /exams/available/?format=json` | `200`; JSON object containing an `exams` list with each exam’s ID, title, duration, availability times, and status. | Unauthenticated users are redirected to login. |

| `GET /exams/<exam\_id>/take/?format=json` | `200`; JSON exam details when the exam is available. | `403` if the exam is upcoming or expired; `404` if the exam ID does not exist. Unauthenticated users are redirected to login. |



\## Test traceability



| Existing test | Requirement(s) | Evidence |

|---|---|---|

| `test\_available\_exams\_json\_api` | FR-05, SEC-REQ-02, SEC-OBJ-01 | Checks the JSON exam list and the available, upcoming, and expired statuses. |

| `test\_exam\_window\_enforcement\_json\_api` | FR-05, SEC-REQ-02, SEC-OBJ-01, NFR-04 | Checks JSON responses for active, upcoming, and expired exams. |

| Code inspection of exam URLs, views, and model | NFR-05 | Compare the route, view, and model responsibilities with the layered design in the architecture document; record any differences. |



\## Manual demo path



1\. Start the server with `python manage.py runserver`.

2\. Sign in as staff and create an exam whose availability window includes the current time.

3\. Sign in as a student and open `/exams/available/?format=json`.

4\. Use the exam ID from that response in `/exams/<exam\_id>/take/?format=json`; confirm the response says `available`.

5\. Confirm an upcoming or expired exam returns `403`.



This documents the API and tests currently present. Question management, submission, and grading endpoints are not implemented yet.

