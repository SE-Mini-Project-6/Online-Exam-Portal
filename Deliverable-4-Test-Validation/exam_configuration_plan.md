# Exam Configuration and Availability Windows Implementation Plan

## Overview
This document specifies the implementation, validation, and test evidence for the **Exam Configuration and Availability Windows** feature (Issue #11, Requirement **FR-03**).

## Requirements & Traceability

- **FR-03 (Create Exam)**: The Admin shall be able to create a new exam by specifying a title, duration (in minutes), and a start/end availability window.
- **SEC-REQ-02 (Role-Based Access Control)**: Only Admin / staff accounts can access exam creation and configuration features; unauthorized student access is blocked.
- **Interval Validation**: The system must reject invalid intervals where `end_at <= start_at` or where `duration_minutes` exceeds the availability window.
- **Dashboard Visibility**: All successfully configured exams must appear on the Admin Dashboard with their title, duration, and formatted availability timestamps.

## Implementation Details

### 1. Database Model (`Online_Exam_Portal/exams/models.py`)
- `title`: `models.CharField(max_length=200)`
- `duration_minutes`: `models.PositiveIntegerField()`
- `start_at`: `models.DateTimeField()`
- `end_at`: `models.DateTimeField()`
- `created_at`: `models.DateTimeField(auto_now_add=True)`
- Model-level `clean()` method enforcing:
  - `duration_minutes >= 1` (guarded against `None`)
  - `end_at > start_at`
  - `duration_minutes <= (end_at - start_at)` in minutes

### 2. Form & Parsing (`Online_Exam_Portal/exams/forms.py`)
- `ExamForm(forms.ModelForm)` with explicit `DateTimeField` bindings for `start_at` and `end_at`.
- HTML5 datetime widget support (`type="datetime-local"`).
- Explicit `input_formats` supporting ISO-8601 (`%Y-%m-%dT%H:%M`, `%Y-%m-%dT%H:%M:%S`) and standard space-separated datetime formats.
- Clean field-level error mapping (`end_at`, `duration_minutes`).

### 3. Views & Access Control (`Online_Exam_Portal/exams/views.py`)
- `@login_required` to redirect unauthenticated users to `/accounts/login/`.
- `request.user.is_staff` check returning `HttpResponseForbidden` (HTTP 403) for non-admin students.
- Saves valid configurations and redirects to `accounts:admin_dashboard`.

### 4. Admin Dashboard Integration (`Online_Exam_Portal/templates/accounts/admin_dashboard.html`)
- **Manage Exams** card links directly to `exams:create`.
- **Configured Exams** section dynamically lists all configured exams in a table displaying Title, Duration in minutes, and human-readable availability interval (`M j, Y, g:i A`).
- Displays friendly fallback text when no exams have been created yet.

### 5. Architectural Alignment & Design Deviations
- Follows the Django MVT and REST architectural specification in [Deliverable 3](../Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf).
- **Design Deviations**: None. Reuses Django's standard form and model validation mechanisms without requiring third-party libraries.

## Verification Checklist

### Acceptance Criteria Compliance
- [x] Admin can specify Title, Duration (minutes), and Start/End timestamps.
- [x] Invalid availability interval (`end_at <= start_at`) is rejected with descriptive error message.
- [x] Non-positive durations (0 or negative) are rejected.
- [x] Duration exceeding the total availability window is rejected.
- [x] Missing or blank fields are handled gracefully without runtime exceptions.
- [x] Saved exams immediately appear in the **Configured Exams** table on the Admin Dashboard.
- [x] Students attempting to access the configuration form receive HTTP 403 Forbidden.
- [x] Unauthenticated users are redirected to login.

### Automated Test Evidence
Suite in `Online_Exam_Portal/exams/tests.py` covers 12 automated unit and integration tests:
1. `test_valid_exam_configuration_is_saved`: Verifies valid creation, database insertion, and dashboard redirect.
2. `test_end_before_start_is_rejected`: Verifies rejection of intervals where `end_at < start_at`.
3. `test_equal_start_and_end_is_rejected`: Verifies rejection of zero-length interval (`end_at == start_at`).
4. `test_non_positive_duration_is_rejected`: Verifies duration of 0 is rejected.
5. `test_empty_duration_is_handled_gracefully`: Verifies missing duration field returns form error instead of 500.
6. `test_duration_exceeding_window_is_rejected`: Verifies duration greater than window length is rejected.
7. `test_saved_exam_appears_on_admin_dashboard`: Verifies dashboard table displays title, duration, and window.
8. `test_students_cannot_create_exams`: Verifies HTTP 403 Forbidden for authenticated student accounts.
9. `test_anonymous_users_redirected_to_login`: Verifies HTTP 302 redirect to login for unauthenticated visitors.
10. `test_admin_can_access_exam_create_page`: Verifies GET request loads form with 200 OK.
11. `test_exam_str_returns_title`: Verifies model `__str__` representation.
12. `test_model_clean_validation`: Verifies model-level validation independently of forms.

### Execution Command
```text
cd Online_Exam_Portal
..\.venv\Scripts\python.exe manage.py test exams
```
All 12 tests pass cleanly with 0 failures and 0 errors.
