# Online Exam Portal

## Software Engineering Mini Project

This repository contains the work for **Mini Project 6 – Online Exam Portal**.

The Online Exam Portal is a web-based examination system with two main users:

- **Admin** – creates and manages exams, questions, submissions, and results.
- **Student** – attempts exams, answers questions, marks questions for review, submits the exam, and views released results.

---

## Project Deliverables

The project is divided into four deliverables, with each team member responsible for one deliverable.

| Deliverable | Description |
|---|---|
| **Deliverable 1** | Software Requirements Specification (SRS) |
| **Deliverable 2** | Test Plan |
| **Deliverable 3** | Software Architecture & Design Specification |
| **Deliverable 4** | Test Cases Update for Test Plan |

---

## Deliverable 1 – Software Requirements Specification

The SRS contains:

- Introduction and project description
- Functional Requirements
- Non-Functional Requirements
- UML Use Case Diagram
- Security Objectives
- Security Requirements

---

## Deliverable 2 – Test Plan

The Test Plan contains:

- Introduction
- Test items
- Features to be tested
- Features not to be tested
- Test approach
- Test environment
- Entry and exit criteria
- Security validation
- Traceability with SRS requirements

---

## Deliverable 3 – Software Architecture & Design Specification

### Architecture

- Component Diagram and component descriptions
- Architectural Pattern
- Requirement Traceability
- Security Architecture
- Deployment and supporting architecture details

### Design

- UML Sequence Diagrams
- API Design
- Error Handling
- Data and state design
- Supporting design details

---

## Deliverable 4 – Test Case Update

The Test Case document contains:

- Functional Test Cases
- Non-Functional Test Cases
- Security Test Cases
- Preconditions
- Test Steps
- Expected Results
- Pass Criteria
- Security Validation
- Requirement Traceability

A minimum of **7–10 test cases** are included.

---

## Main Features

### Admin

- Login with Admin privileges
- Create exams with a title, duration, and availability window
- Configure exam duration and reject invalid availability intervals
- Add, edit, and delete MCQ questions
- View student submissions
- Release examination results

### Student

- Login to the portal
- Attempt available examinations
- Answer questions in any order
- Change answers before submission
- Mark questions for review
- Navigate through the question-status grid
- Submit examination manually
- Automatic submission after timeout
- View results after release

## Exam configuration

Staff users can configure an exam at `/exams/create/` from the **Manage Exams**
card on the admin dashboard. The form stores the title, duration in minutes,
and timezone-aware start and end timestamps. Validation ensures:
- The end timestamp must be strictly later than the start timestamp.
- The duration must be a positive integer (at least one minute).
- The duration cannot exceed the total availability window.
- Missing or malformed fields are handled gracefully with field-level errors.

Successfully saved exams are listed in the **Configured Exams** section of the
admin dashboard.

The implementation satisfies requirement **FR-03** (Create Exam) and extends the
admin exam-management capability described in the
[Deliverable 3 architecture/design document](Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf).
No design deviation was required.

### Test evidence

Automated coverage is in
[exams/tests.py](Online_Exam_Portal/exams/tests.py) (12 tests) and verifies:
- Successful exam creation and redirection to dashboard.
- Configured exam and duration appear in the admin dashboard table.
- Invalid interval rejection: end timestamp earlier than start timestamp.
- Invalid interval rejection: end timestamp equal to start timestamp.
- Non-positive duration rejection (0 or negative).
- Missing/empty duration handled gracefully without runtime errors.
- Duration exceeding availability window rejection.
- Direct model-level `clean()` validation checks.
- Non-staff / student access prohibition (HTTP 403 Forbidden).
- Anonymous user redirect to login page (HTTP 302).
- Admin GET form render verification.
- Model string representation (`__str__`).

Run the automated test suite with:

```text
cd Online_Exam_Portal
..\.venv\Scripts\python.exe manage.py test exams
```

Manual verification steps:

1. Sign in through `/accounts/login/` as an admin (staff) user.
2. Select **Create an exam** from the **Manage Exams** card.
3. Enter a title, valid duration (e.g., `90`), and valid window (e.g., start tomorrow 10:00, end tomorrow 12:00), then click **Save exam**.
4. Confirm redirection to the admin dashboard and that the exam appears under **Configured Exams** with title, duration, and formatted window timestamps.
5. Attempt invalid intervals:
   - End time before or equal to start time: confirm error `"End time must be after the start time."`
   - Duration exceeding the window (e.g., 180 minutes for a 2-hour window): confirm error `"Exam duration cannot exceed the availability window."`
   - Duration of 0 or blank: confirm validation error without server error.
6. Attempt to visit `/exams/create/` while logged in as a student user; confirm HTTP 403 Forbidden.

---

## Student available-exam list and window enforcement

Students can view all scheduled examinations directly on the **Student Dashboard**
at `/accounts/student-dashboard/` or through `/exams/available/`. Each exam card
and table row displays:
- The exam **Title** and **Duration** in minutes.
- The scheduled availability window with formatted start and end timestamps.
- An availability status indicator:
  - **Available Now**: For exams whose current time is within `start_at` and `end_at`. Provides an active **Start Exam** button.
  - **Upcoming**: For exams scheduled in the future (`now < start_at`). Action button is disabled with start time indication.
  - **Closed**: For exams whose window has elapsed (`now > end_at`). Action button is disabled.

### Server-side window enforcement

Strict server-side validation is enforced in `take_exam` (`/exams/<id>/take/` and `/exams/<id>/`):
- **Early access guard**: Requests made before the start timestamp (`now < start_at`) are rejected with `HTTP 403 Forbidden` (`"This exam has not started yet. Early access is blocked on server."`).
- **Expired access guard**: Requests made after the window closes (`now > end_at`) are rejected with `HTTP 403 Forbidden` (`"This exam availability window has expired. Access is blocked on server."`).
- **Active window**: Requests within the window (`start_at <= now <= end_at`) are granted `HTTP 200 OK` and render the exam attempt interface with duration and test rules.
- **Authentication**: Unauthenticated users attempting to access exam URLs are redirected to `/accounts/login/` (`HTTP 302`).
- **REST API support**: The endpoints return JSON representations when requested with `Accept: application/json` or `?format=json`.

The implementation satisfies requirements **FR-05** (Display Exam), **SEC-REQ-02**
(Role-Based Access Control), and **SEC-OBJ-01** (Prevent Unauthorized Access) as
specified in the [SRS document](SRS_Online_Exam_Portal.docx) and follows the MVT/REST
specifications in [Deliverable 3](Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf).
No design deviations were required.

### Test evidence

Automated coverage in [exams/tests.py](Online_Exam_Portal/exams/tests.py) (24 tests total, including 12 dedicated window-enforcement tests) verifies:
- Student dashboard displays configured exams, durations, and scheduled timestamps.
- Appropriate status badges (`Available Now`, `Upcoming`, `Closed`) and active action links.
- Early exam access attempts return `HTTP 403 Forbidden` with descriptive messages.
- Expired exam access attempts return `HTTP 403 Forbidden` with descriptive messages.
- Active window exam access returns `HTTP 200 OK` with attempt instructions.
- Detail and take URL routes consistently enforce window boundaries.
- Anonymous users are redirected to login (`HTTP 302`).
- Invalid exam ID returns `HTTP 404 Not Found`.
- Standalone available-exams view and REST API JSON endpoints.
- Model availability methods and properties across active, upcoming, and expired states.

Run the automated test suite with:

```text
cd Online_Exam_Portal
..\.venv\Scripts\python.exe manage.py test exams
```

Manual verification steps:

1. Sign in as Admin (`/accounts/login/`) and create three test exams:
   - **Exam 1 (Active)**: Window starts 10 minutes ago, ends in 50 minutes.
   - **Exam 2 (Upcoming)**: Window starts tomorrow at 10:00 AM.
   - **Exam 3 (Expired)**: Window was scheduled for yesterday.
2. Sign in as a Student (`/accounts/student-login/` or `/accounts/login/`) and visit the Student Dashboard (`/accounts/student-dashboard/`).
3. Confirm that all three exams appear under **Available Examinations** with their respective titles, durations, and scheduled window timestamps.
4. Confirm statuses:
   - Exam 1 shows **Available Now** and an enabled **Start Exam** button.
   - Exam 2 shows **Upcoming** and a disabled button.
   - Exam 3 shows **Closed** and a disabled button.
5. Click **Start Exam** on Exam 1; confirm HTTP 200 and attempt page renders with active window indicator.
6. Directly navigate to `/exams/<upcoming_id>/take/`; confirm server blocks access with **HTTP 403 Forbidden** stating exam has not started yet.
7. Directly navigate to `/exams/<expired_id>/take/`; confirm server blocks access with **HTTP 403 Forbidden** stating window has expired.
8. Log out and attempt direct access to `/exams/<active_id>/take/`; confirm HTTP 302 redirect to `/accounts/login/`.

---

## Technology Stack

- **Backend:** Python / Django
- **API:** REST API
- **Database:** Relational Database
- **Version Control:** Git
- **Repository Hosting:** GitHub

---

## Repository Structure

```text
Online-Exam-Portal/
│
├── README.md
│
├── Deliverable-1-SRS/
│
├── Deliverable-2-Test-Plan/
│
├── Deliverable-3-Architecture-Design/
│
└── Deliverable-4-Test-Cases/
