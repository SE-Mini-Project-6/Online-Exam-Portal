# Online Exam Portal
# SE Mini Project — Evaluation Checklist & GitHub Evidence

The Online Exam Portal is a Django-based web application developed over two sprints. It provides separate Admin and Student dashboards for conducting online examinations, managing questions, submitting answers, grading exams and publishing results.

The project documentation, development work and testing results are organized below according to the evaluation checklist.

## Project Documentation & Results

| Document | Link |
|---|---|
| ⭐ **Project Improvements — Before vs After** | **[View Improvements Report](PROJECT_IMPROVEMENTS.md)** |
| Software Requirements Specification (SRS) | [SRS Document](SRS_Online_Exam_Portal.docx) |
| Test Plan | [Test Plan Document](Deliverable-2-Test-Plan/Deliverable_2_Test_Plan.pdf) |
| Software Architecture & Design (SAD) | [Architecture & Design Document](Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf) |
| Test Cases & Validation | [Test Case Document](Deliverable-4-Test-Validation/Test_Case_Execution_Revision_1_1.pdf) |
| GitHub Project Board | [Project #2](https://github.com/orgs/SE-Mini-Project-6/projects/2) |
| Sprint Backlog | [Sprint 1 & Sprint 2](docs/SPRINT_BACKLOG.md) |
| GitHub Issues | [Issues](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/issues) |
| Pull Requests | [PR History](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pulls?q=is%3Apr) |
| GitHub Actions | [Automated Test Runs](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions) |
| Sprint 1 Demonstration | [1-Minute Video](Project_Demo/Sprint_1_Demo.mp4) |
| Sprint 2 Demonstration | [2-Minute Video](Project_Demo/Sprint_2_Demo.mp4) |

---

## Part 1 — Requirements & Design Documents

### 1. Software Requirements Specification (SRS)

The SRS contains the project scope, functional requirements, non-functional requirements, use case diagrams and security requirements.

| No. | Requirement | Document |
|---|---|---|
| 1 | IEEE-standard SRS format | [SRS](SRS_Online_Exam_Portal.docx) |
| 2 | Introduction and project description | [SRS](SRS_Online_Exam_Portal.docx) |
| 3 | Functional Requirements (FRs) and Non-Functional Requirements (NFRs) | [SRS](SRS_Online_Exam_Portal.docx) |
| 4 | UML Use Case Diagram | [SRS](SRS_Online_Exam_Portal.docx) |
| 5 | Security objectives and security requirements | [SRS](SRS_Online_Exam_Portal.docx) |

### 2. Test Plan Document

The Test Plan defines the testing approach, test environment, security validation and mapping of test cases to requirements.

| No. | Requirement | Document |
|---|---|---|
| 6 | IEEE-standard Test Plan format | [Test Plan](Deliverable-2-Test-Plan/Deliverable_2_Test_Plan.pdf) |
| 7 | Sections 3, 4 and 5 | [Test Plan](Deliverable-2-Test-Plan/Deliverable_2_Test_Plan.pdf) |
| 8 | Section 5.1 — Security Validation | [Test Plan](Deliverable-2-Test-Plan/Deliverable_2_Test_Plan.pdf) |
| 9 | Traceability to SRS | [Test Plan](Deliverable-2-Test-Plan/Deliverable_2_Test_Plan.pdf) · [Test Traceability](docs/TEST_CASE_EXECUTION.md) |
| 10 | 7–10 FR and NFR test cases | [Original 10 Test Cases](Deliverable-4-Test-Validation/04_Member4_Deliverable4_Test_Case_Update_Online_Exam_Portal%20%281%29.pdf) |

### 3. Software Architecture & Design (SAD)

The SAD describes the system architecture, components, UML diagrams, API design, security architecture and error handling.

| No. | Requirement | Document |
|---|---|---|
| 11 | IEEE-standard SAD format | [SAD](Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf) |
| 12 | Component diagrams, architectural pattern, traceability and security architecture | [SAD](Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf) |
| 13 | Two UML sequence diagrams, API design and error handling | [SAD](Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf) |

---

## Part 2 — Agile Planning & Repository Setup

### 1. GitHub Project Management

We divided development into two sprints and maintained a backlog with user stories, assignees, requirement references and story points.

| No. | Requirement | Evidence |
|---|---|---|
| 14 | GitHub Project linked to the repository | [GitHub Project #2](https://github.com/orgs/SE-Mini-Project-6/projects/2) |
| 15 | Backlog based on SRS requirements | [Sprint Backlog](docs/SPRINT_BACKLOG.md) · [Issues](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/issues) |
| 16 | Story points assigned to backlog items | [Story Points](docs/SPRINT_BACKLOG.md) |
| 17 | User stories assigned to team members | [Member Assignments](docs/SPRINT_BACKLOG.md) |
| 18 | Sprint 1 and Sprint 2 planning | [Sprint Breakdown](docs/SPRINT_BACKLOG.md) · [Project Board](https://github.com/orgs/SE-Mini-Project-6/projects/2) |

### 2. Sprint 1 — Core Exam System

**Sprint 1: 19–23 October 2026**

The first sprint focused on developing the basic examination workflow.

Work completed during Sprint 1 included:

- Student and Admin authentication
- Exam creation and scheduling
- MCQ creation, editing and deletion
- Student exam dashboard
- Question navigation
- Answer saving
- Manual exam submission
- Automatic answer-key grading
- Initial automated tests and GitHub Actions

| No. | Requirement | Evidence |
|---|---|---|
| 19 | GitHub Actions automation | [GitHub Actions](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions) · [Workflow Files](.github/workflows) |
| 20 | Implementation based on SRS/SAD | [Source Code](Online_Exam_Portal) · [Design Deviations](docs/DESIGN_DEVIATIONS.md) |
| 21 | Pull Requests raised by assigned members | [Pull Requests](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pulls?q=is%3Apr) · [Backlog](docs/SPRINT_BACKLOG.md) |
| 22 | PR review and merging | [Merged PR History](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pulls?q=is%3Apr+is%3Amerged) · [Review Records](docs/TEAM_ACCEPTANCE.md) |
| 23 | One-minute working-product video | [Sprint 1 Demo](Project_Demo/Sprint_1_Demo.mp4) |

### 3. Sprint 2 — Additional Features & Testing

**Sprint 2: 26–30 October 2026**

The second sprint focused on completing the examination workflow and improving security, reliability and testing.

Work developed during Sprint 2 included:

- Server-controlled exam timer
- Automatic submission on timeout
- Mark-for-review functionality
- Question status indicators
- Admin submissions dashboard
- Admin-controlled result release
- Student result viewing
- Security and authorization tests
- Performance and reliability testing
- Browser compatibility and usability testing

| No. | Requirement | Evidence |
|---|---|---|
| 24 | Sprint 2 completion and release-freeze documentation | [Sprint 2 Review & Freeze Draft](docs/SPRINT2_REVIEW_AND_FREEZE_DRAFT.md) |
| 25 | Documentation of SRS/SAD deviations | [Design Deviations](docs/DESIGN_DEVIATIONS.md) |
| 26 | Project documentation | [Documentation Index](docs/README.md) · [Team Acceptance](docs/TEAM_ACCEPTANCE.md) |
| 27 | Two-minute working-product video | [Sprint 2 Demo](Project_Demo/Sprint_2_Demo.mp4) |

### 4. Project Improvements

The performance, security, reliability and feature improvements made during development are documented separately.

**⭐ [PROJECT_IMPROVEMENTS.md — Complete Before & After Comparison](PROJECT_IMPROVEMENTS.md)**

The report includes measured improvements in question loading time, autosave latency, database queries, throughput, security controls, test coverage and maintainability.

---

## Part 3 — Testing & Quality Assurance

### 1. Test Case Updates & Execution

Original test cases were updated to reflect changes made during Sprint 1 and Sprint 2.

| No. | Requirement | Evidence |
|---|---|---|
| 28 | Original test cases updated according to sprint changes | [Updated Test Cases](docs/TEST_CASE_EXECUTION.md) · [Revision 1.1 PDF](Deliverable-4-Test-Validation/Test_Case_Execution_Revision_1_1.pdf) |
| 29 | Test execution and results based on the Test Plan | [Validation Results](docs/VALIDATION_RESULTS.md) · [Final Technical Checklist](docs/FINAL_TECHNICAL_SIGNOFF_CHECKLIST.md) |

### 2. Automated Testing Results

| Testing | Recorded Result | Evidence |
|---|---|---|
| Django automated tests | 147 tests passed | [Django CI](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43889325603) |
| Browser compatibility | 252 checks passed | [Browser CI](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43889325512) |
| Usability testing | 5/5 users completed the required tasks | [Usability Report](Deliverable-4-Test-Validation/usability_browser_verification.md) |
| Security regression testing | Authentication, authorization and submission integrity tested | [Security Tests](Deliverable-4-Test-Validation/security_regression_traceability.md) |

Browser compatibility testing covered Chrome and Firefox across desktop and mobile screen sizes.

### 3. Generated Reports

| Report | Link |
|---|---|
| Test Case Execution | [Execution Report](docs/TEST_CASE_EXECUTION.md) |
| Validation Results | [Validation Report](docs/VALIDATION_RESULTS.md) |
| Security Validation | [Security Report](Deliverable-4-Test-Validation/security_regression_traceability.md) |
| API Integration | [API Test Report](Deliverable-4-Test-Validation/api_integration_test_traceability.md) |
| Performance & Reliability | [Performance Report](Deliverable-4-Test-Validation/performance_reliability_validation.md) |
| Browser & Usability Testing | [Browser Report](Deliverable-4-Test-Validation/usability_browser_verification.md) |
| Technical Completion | [Technical Report](docs/FINAL_TECHNICAL_COMPLETION.md) |
| Final Requirement Status | [Technical Sign-off Checklist](docs/FINAL_TECHNICAL_SIGNOFF_CHECKLIST.md) |
| Raw Test Evidence | [Evidence Files](docs/evidence) |

---

## Part 4 — Final Evaluation

### 1. Application Demonstration

The application supports the following workflow:

**Admin creates exam → Adds MCQs → Student attempts exam → Answers are saved → Student submits or timer expires → Admin reviews submissions → Results are released → Student views score**

| No. | Requirement | Evidence |
|---|---|---|
| 30 | Working application and core use cases | [Sprint 2 Demo](Project_Demo/Sprint_2_Demo.mp4) · [Application Code](Online_Exam_Portal) |
| 31 | Documented deviations from the original design | [Design Deviations](docs/DESIGN_DEVIATIONS.md) |
| 32 | Readable, accessible and version-controlled code | [Source Code](Online_Exam_Portal) · [Commit History](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/commits/main/) |

### 2. Team Contributions & Development Process

| No. | Requirement | Evidence |
|---|---|---|
| 33 | Individual code contributions and Pull Requests | [Team Sprint Work](docs) · [Pull Requests](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pulls?q=is%3Apr) |
| 34 | Agile/SDLC process, sprint planning, story points and blockers | [Sprint Backlog](docs/SPRINT_BACKLOG.md) · [GitHub Project](https://github.com/orgs/SE-Mini-Project-6/projects/2) |
| 35 | Architecture, API design and automated testing | [SAD](Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf) · [API Testing](Deliverable-4-Test-Validation/api_integration_test_traceability.md) · [CI](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions) |

### 3. Individual Contributions

| Team Member | Main Work | Evidence |
|---|---|---|
| Abhishek Anand | Database models, MCQ CRUD, submission, grading and exam timer | [Sprint 1](docs/SPRINT1_ABHI.md) · [Sprint 2](docs/SPRINT2_ABHI_TIMER.md) |
| Adithya Sundar | Authentication, exam management, access control and result release | [Sprint 1](docs/SPRINT1_ADITHYA_SUNDAR) · [Sprint 2](docs/SPRINT2_ADITHYA_SUNDAR.md) |
| Aditya Jaiswal | Question navigation, autosave, review flags, UI and demos | [Sprint 1](docs/SPRINT1_Aditya_Jaiswal.md) · [Sprint Backlog](docs/SPRINT_BACKLOG.md) |
| Aditya-TJ | Automated testing, security validation, performance testing and usability | [Testing Reports](Deliverable-4-Test-Validation) |

**All contributions:** [GitHub Pull Requests](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pulls?q=is%3Apr)

---

## Project Results

| Area | Result |
|---|---|
| Question-page average latency | Reduced by 72.7% in the measured PostgreSQL comparison |
| Answer autosave average latency | Reduced by 30.8% in the measured PostgreSQL comparison |
| Measured throughput | Increased by 89.5% |
| Database reliability | SQLite locking failures from the initial concurrency test were resolved in the repeated test |
| Automated Django tests | 147 passed |
| Browser compatibility | 252 checks passed |
| Usability evaluation | 5/5 participants completed the required tasks without assistance |
| Extensibility | Isolated question-type experiment required one module change after refactoring |

**⭐ [Detailed Project Improvements — Before vs After](PROJECT_IMPROVEMENTS.md)**

The performance measurements were carried out locally. The requirement-level results and remaining acceptance items are recorded in the [Final Technical Sign-off Checklist](docs/FINAL_TECHNICAL_SIGNOFF_CHECKLIST.md).
