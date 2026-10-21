# Student Available-Exam List and Window Enforcement Implementation Plan

## Overview
This document specifies the implementation, validation, and test evidence for the **Student Available-Exam List and Window Enforcement** feature (Issue #13, Requirements **FR-05**, **SEC-REQ-02**, and **SEC-OBJ-01**).

## Requirements & Traceability

- **FR-05 (Display Exam)**: The system shall display exam questions to a logged-in Student only during the exam's configured availability window.
- **SEC-REQ-02 (Role-Based Access Control)**: The system shall enforce role-based access control such that only authenticated users can access the portal and only authorized student accounts can attempt active exams.
- **SEC-OBJ-01 (Prevent Unauthorized Access)**: Prevent unauthorized users from accessing exam content outside configured time boundaries or without proper authentication.
- **NFR-04 (Availability)**: The system shall be available for Students to attempt an exam for 100% of its configured availability window.

## Acceptance Criteria Mapping

| Acceptance Criterion | Implementation Details | Status |
| :--- | :--- | :---: |
| **Student sees appropriate available exams** | Student dashboard queries configured exams and categorizes each as *Available Now*, *Upcoming*, or *Closed*. Active exams provide direct links to begin the attempt. | **SATISFIED** |
| **Scheduled times are displayed** | Each exam displays title, duration in minutes, and human-readable scheduled availability window (`start_at` to `end_at`). | **SATISFIED** |
| **Early access is blocked on server** | Requests to `/exams/<id>/` or `/exams/<id>/take/` before `start_at` are blocked server-side, returning `HTTP 403 Forbidden` with a descriptive message. | **SATISFIED** |
| **Expired access is blocked on server** | Requests to `/exams/<id>/` or `/exams/<id>/take/` after `end_at` are blocked server-side, returning `HTTP 403 Forbidden` with a descriptive message. | **SATISFIED** |
| **Active window grants access** | Requests to `/exams/<id>/take/` during `start_at <= now <= end_at` return `HTTP 200 OK` and render the exam attempt interface with instructions and rules. | **SATISFIED** |
| **Authentication required** | Unauthenticated visitors attempting to view or take exams are redirected to `/accounts/login/` (HTTP 302). | **SATISFIED** |

---

## Implementation Details

### 1. Database Model Helpers (`Online_Exam_Portal/exams/models.py`)
Enhanced the `Exam` model with standardized availability assessment methods and properties:
- `is_available(current_time=None)`: Evaluates `start_at <= current_time <= end_at`.
- `is_upcoming(current_time=None)`: Evaluates `current_time < start_at`.
- `is_expired(current_time=None)`: Evaluates `current_time > end_at`.
- `get_status(current_time=None)`: Returns `'available'`, `'upcoming'`, or `'expired'`.
- `get_status_label(current_time=None)`: Returns human-readable label (`'Available Now'`, `'Upcoming'`, `'Closed'`).
- Properties for clean template consumption: `is_currently_available`, `is_currently_upcoming`, `is_currently_expired`, `status`, `status_label`.

### 2. Views & Server-Side Enforcement (`Online_Exam_Portal/exams/views.py`)
- `available_exams(request)`:
  - Accessible to authenticated users at `/exams/` and `/exams/available/`.
  - Supports both HTML view (`available_exams.html`) and REST API JSON response (`Accept: application/json` or `?format=json`).
- `take_exam(request, exam_id)`:
  - Accessible at `/exams/<exam_id>/` and `/exams/<exam_id>/take/`.
  - `@login_required` decorator redirects unauthenticated users to `/accounts/login/`.
  - Compares current server time (`timezone.now()`) against `exam.start_at` and `exam.end_at`.
  - **Early access guard**: Returns `HttpResponseForbidden` (HTTP 403) stating: `"This exam has not started yet. Early access is blocked on server. Scheduled start: <start_at>."`
  - **Expired access guard**: Returns `HttpResponseForbidden` (HTTP 403) stating: `"This exam availability window has expired. Access is blocked on server. Scheduled end: <end_at>."`
  - **Active window**: Returns `HTTP 200 OK` rendering `exams/take_exam.html`.
  - Supports JSON response for REST API clients.

### 3. Student Dashboard Integration (`Online_Exam_Portal/accounts/views.py`)
- `student_dashboard(request)`:
  - Fetches all configured exams ordered by `start_at`.
  - Passes `exams` and `current_time` to `accounts/student_dashboard.html`.

### 4. User Interface Templates
- `templates/accounts/student_dashboard.html`:
  - Displays user profile badge, navigation, and overview cards.
  - Dedicated **Available Examinations** section rendering a responsive table with Title, Duration, Scheduled Window, Status Badges, and Action Buttons.
  - Active exams provide enabled **Start Exam** button.
  - Upcoming/expired exams show informative disabled states.
- `templates/exams/available_exams.html`:
  - Standalone view for browsing available exams with status indicators.
- `templates/exams/take_exam.html`:
  - Modern attempt launch page displaying exam metadata, duration countdown info, and test-taking instructions.

### 5. Architectural Alignment & Design Deviations
- Follows the Django MVT and REST architectural specifications in [Deliverable 3](../Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf).
- Aligns with endpoints `/exams`, `/exams/{examId}`, and `/exams/{examId}/attempts`.
- **Design Deviations**: None. Adheres strictly to the documented architecture and standard Django mechanisms without requiring external dependencies.

---

## Verification & Automated Test Evidence

Automated test suite in `Online_Exam_Portal/exams/tests.py` covers 24 unit and integration tests across exam configuration, student available-exam listing, and window enforcement:

1. `test_valid_exam_configuration_is_saved`: Valid exam creation and redirect.
2. `test_end_before_start_is_rejected`: Rejection of `end_at < start_at`.
3. `test_equal_start_and_end_is_rejected`: Rejection of zero-length interval.
4. `test_non_positive_duration_is_rejected`: Rejection of duration `<= 0`.
5. `test_empty_duration_is_handled_gracefully`: Graceful handling of missing duration.
6. `test_duration_exceeding_window_is_rejected`: Rejection of duration exceeding window.
7. `test_saved_exam_appears_on_admin_dashboard`: Admin dashboard display verification.
8. `test_students_cannot_create_exams`: HTTP 403 for student exam creation.
9. `test_anonymous_users_redirected_to_login`: HTTP 302 redirect for anonymous visitors.
10. `test_admin_can_access_exam_create_page`: GET request renders creation form.
11. `test_exam_str_returns_title`: Model `__str__` returns title.
12. `test_model_clean_validation`: Direct model `clean()` validation checks.
13. `test_student_dashboard_displays_exams_and_scheduled_times`: Verifies student dashboard lists exams, durations, and scheduled timestamps.
14. `test_student_dashboard_displays_appropriate_status_badges`: Verifies Available Now, Upcoming, and Closed badges and active action links.
15. `test_early_access_is_blocked_on_server_with_403`: Verifies early attempt access before `start_at` returns HTTP 403 Forbidden with descriptive explanation.
16. `test_expired_access_is_blocked_on_server_with_403`: Verifies expired attempt access after `end_at` returns HTTP 403 Forbidden with descriptive explanation.
17. `test_active_exam_access_is_granted_with_200`: Verifies attempt access during active window returns HTTP 200 OK.
18. `test_detail_url_route_enforces_windows`: Verifies `/exams/<id>/` enforces window boundaries.
19. `test_anonymous_user_redirected_to_login`: Verifies unauthenticated attempt access redirects to login.
20. `test_nonexistent_exam_returns_404`: Verifies invalid exam ID returns 404.
21. `test_available_exams_view_renders_correctly`: Verifies standalone available exams page loads correctly.
22. `test_available_exams_json_api`: Verifies REST API JSON endpoint for exam listing.
23. `test_exam_window_enforcement_json_api`: Verifies REST API JSON responses for window enforcement (403 for early/expired, 200 for active).
24. `test_exam_model_availability_methods`: Verifies model unit methods and properties across all temporal states.

### Execution Command
```text
cd Online_Exam_Portal
..\.venv\Scripts\python.exe manage.py test exams
```
All 24 exams tests pass cleanly with 0 failures and 0 errors.

To run the complete test suite across all portal modules (core, accounts, and exams — 41 tests total):
```text
cd Online_Exam_Portal
..\.venv\Scripts\python.exe manage.py test accounts.tests exams.tests core.tests
```
All 41 tests pass cleanly with 0 failures and 0 errors.

---

## Manual Verification Steps

1. **Sign in as Admin (`/accounts/login/`)**:
   - Create Exam A: Scheduled for now (e.g. starts 10 minutes ago, ends in 50 minutes).
   - Create Exam B: Scheduled for tomorrow (upcoming).
   - Create Exam C: Scheduled for yesterday (expired).
2. **Sign in as Student (`/accounts/student-login/` or `/accounts/login/`)**:
   - Access Student Dashboard (`/accounts/student-dashboard/`).
   - Observe **Available Examinations** table:
     - Exam A displays **Available Now** badge and an active **Start Exam** button.
     - Exam B displays **Upcoming** badge and a disabled action button.
     - Exam C displays **Closed** badge and a disabled action button.
     - All three exams display formatted scheduled times and duration.
3. **Verify Server-Side Window Enforcement**:
   - Click **Start Exam** on Exam A (or navigate to `/exams/<id>/take/`): HTTP 200 loads attempt page with rules and active window indicator.
   - Manually enter URL for Exam B (upcoming) (`/exams/<upcoming_id>/take/`): Server returns **HTTP 403 Forbidden** with message `"This exam has not started yet. Early access is blocked on server."`
   - Manually enter URL for Exam C (expired) (`/exams/<expired_id>/take/`): Server returns **HTTP 403 Forbidden** with message `"This exam availability window has expired. Access is blocked on server."`
4. **Verify Authentication Gate**:
   - Log out.
   - Attempt to access `/exams/<id>/take/` directly while unauthenticated: Server immediately redirects to `/accounts/login/?next=/exams/<id>/take/` (HTTP 302).
