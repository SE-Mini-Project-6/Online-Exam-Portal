# Evaluation evidence index

This is the entry point for the final evaluation package. A closed issue is workflow metadata, not a substitute for an executed test or a reviewer approval.

## Requirements, design and test cases

| Artifact | Purpose |
|---|---|
| [SRS](../SRS_Online_Exam_Portal.docx) | Original FR-01..17, NFR-01..07 and security baseline |
| [Test Plan](../Deliverable-2-Test-Plan/Deliverable_2_Test_Plan.pdf) | IEEE-style scope, approach, sections 3/4/5/5.1 and traceability |
| [Architecture/design baseline](../Deliverable-3-Architecture-Design/03_Member3_Deliverable3_Software_Architecture_and_Design_Specification.pdf.pdf) | Original component/sequence diagrams and design contracts |
| [Original detailed cases](../Deliverable-4-Test-Validation/04_Member4_Deliverable4_Test_Case_Update_Online_Exam_Portal%20(1).pdf) | Original TC-01..10 |
| [Test-case execution revision](TEST_CASE_EXECUTION.md) | Current routes, expected behavior, coverage and outstanding checks; supersedes conflicting execution details in the original cases |
| [Printable execution revision 1.1](../Deliverable-4-Test-Validation/Test_Case_Execution_Revision_1_1.pdf) | Rendered and visually checked copy of the execution revision |
| [Design deviation register](DESIGN_DEVIATIONS.md) | Actual implementation versus original design, consequences and approval state |

## Execution reports

| Report | Evidence and limits |
|---|---|
| [Current validation](VALIDATION_RESULTS.md) | Commands, actual results and remaining checks for this readiness branch |
| [Security](../Deliverable-4-Test-Validation/security_regression_traceability.md) | Authentication, RBAC, ownership and finalization regression mapping |
| [Performance](../Deliverable-4-Test-Validation/performance_reliability_validation.md) | Recorded SQLite/PostgreSQL measurements, including unmet targets |
| [Browser/usability](../Deliverable-4-Test-Validation/usability_browser_verification.md) | Scripted browser evidence, real-participant protocol and unresolved matrix requirements |
| [Admin submissions/release](../Deliverable-4-Test-Validation/admin_submissions_dashboard.md) | Roster, result-release workflow and manual checks |
| [API integration](../Deliverable-4-Test-Validation/api_integration_test_traceability.md) | API contract and initial test traceability; read with current revision above |
| [Raw readiness evidence](evidence/) | Machine-readable load measurements and current command results |

## Release, demos and individual contributions

- [Remaining team actions](TEAM_ACCEPTANCE.md): honest checklist, owners, board and recording instructions, review/freeze gates.
- [Demo scripts](DEMO_SCRIPTS.md): separate one-minute and two-minute recordings using the real application.
- [Existing freeze draft](SPRINT2_REVIEW_AND_FREEZE_DRAFT.md): remains pending until real team review and approval.
- [Deployment guide](https_deployment.md) and [architecture/deployment notes](SPRINT2_ARCHITECTURE_DEPLOYMENT.md): HTTPS, environment variables, database and scheduling requirements.
- [Sprint 1 Abhishek](SPRINT1_ABHI.md), [Sprint 1 Aditya Jaiswal](SPRINT1_Aditya_Jaiswal.md), [Sprint 1 Adithya Sundar](SPRINT1_ADITHYA_SUNDAR), [Sprint 2 Adithya Sundar](SPRINT2_ADITHYA_SUNDAR.md), [Sprint 2 timer](SPRINT2_ABHI_TIMER.md).
- Aditya-TJ: issues #2, #18, #19, #27, #28, #29; PRs #8, #36, #37, #43, #44, #46, #49, #50, #51. The five-person usability study is still pending despite closed #29.

## Verified baseline before readiness changes

Main commit `7abce9eb8c6d4016a5125738c3b93a4404597f93`: [CI run](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/41690572788), **145 tests passed**. This is baseline evidence, not a claim that subsequent edits are already validated. Use the current validation report for branch-specific results.
