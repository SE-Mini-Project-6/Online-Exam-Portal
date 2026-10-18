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
