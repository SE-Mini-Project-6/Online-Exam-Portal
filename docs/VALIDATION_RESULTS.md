# Readiness branch validation

See the [technical completion report](FINAL_TECHNICAL_COMPLETION.md) for the follow-up SQL profile, SQLite/PostgreSQL load runs, loopback TLS/login measurements, and change-impact experiment. Earlier results below are retained as historical evidence.

## Final demonstration check, 16 November 2026

The post-merge [Django Actions run](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43594192327) passed on `41bc4aa`. A fresh local run on that application revision passed `manage.py check`, `makemigrations --check --dry-run`, and all 38 tests in `exams.test_sprint2_timer`, `accounts.test_security`, `accounts.test_submissions`, and `exams.test_results`. The timer tests include the expired-attempt management command. They exercise finalization behavior without establishing that a periodic job is installed on a deployment.

The [Sprint 2 recording](../Project_Demo/Sprint_2_Demo.mp4) captures browser timer expiry, the withheld result, staff release, and the student's released score. [Recording notes](../Project_Demo/README.md) describe the disposable data and the cut in elapsed waiting time. Target-environment security and availability evidence and the load-test failures remain in the acceptance record.

Revision prepared 14 November 2026. Actual branch results are recorded here after execution. Baseline CI on main `7abce9e` passed 145 tests; this does not automatically validate new changes.

| Check | Current readiness result |
|---|---|
| System check | Passed: no issues |
| Migration consistency | Passed: no changes detected |
| Full regression suite | Passed: 147 tests in 236.170 s; [verbose log](evidence/regression.txt) |
| Browser flows / mobile layout | Passed: installed Chrome 148.0.7778.169 and Firefox 160.0, exact 1280x800 and 375x812 page viewports, 122/122 checks; [results](evidence/browser-completed/results.json), [summary](evidence/browser-completed.txt) |
| Before/after 50-user load measurement | Measured: question mean 439.1 -> 301.4 ms; strict maximum/growth targets still fail; [before](evidence/load-before.json), [after](evidence/load-after.json) |
| Five-user usability (NFR-03) | **Passed: 5/5 first-time participants completed answering, marking for review, and submitting unaided; average total completion time 83 seconds; no issues reported.** [Walkthrough session log](../Deliverable-4-Test-Validation/usability_browser_verification.md#32-session-log) |
| Required second browser versions | Passed: Chrome 157.0.8103.50 / 158.0.8127.18 and Firefox 159.0.1 / 160.0, desktop + exact phone viewports, 252/252 CI checks; [run and artifacts](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43497888502) |
| Target HTTPS/uptime/scheduler | Pending target-environment evidence |
| Human review / freeze | Pending team approval |

Raw outputs are retained under `docs/evidence/`. Record errors and failed targets without changing the SRS thresholds.

## Five-user usability walkthrough evidence (NFR-03)

Five non-team participants completed the locally hosted Online Exam Portal walkthrough on a Windows laptop. Each participant independently answered questions, marked a question for review, and submitted the exam. The recorded time is total time to submit, not a separate per-task timing.

| Participant | Answer unaided | Mark for review unaided | Submit unaided | Total time | Feedback / issues |
|---|---|---|---|---|---|
| P1 | Yes | Yes | Yes | 60 s | No issues; navigation was easy |
| P2 | Yes | Yes | Yes | 55 s | Navigating through questions was pretty simple |
| P3 | Yes | Yes | Yes | 80 s | Simple UI with easy navigation |
| P4 | Yes | Yes | Yes | 100 s | No additional feedback; everything worked fine |
| P5 | Yes | Yes | Yes | 120 s | No issues; everything worked fine |

**Outcome:** 5/5 participants and 15/15 required task completions succeeded unaided (100% observed success rate). Total elapsed time across sessions was 415 seconds; mean completion time was **83 seconds (1 min 23 sec)**. No usability problems were reported during these sessions. This verifies the observed NFR-03 three-task acceptance criterion for this five-person sample, not broader device/browser usability or the separate NFR-07 requirement. Exact session dates and individual browser versions should be confirmed in the [walkthrough log](../Deliverable-4-Test-Validation/usability_browser_verification.md#32-session-log) if not already recorded.

## Additional local SQLite load test — 16 November 2026

A supplementary load test was run on a local Windows laptop using SQLite and the Django `measure_load` command with **50 concurrent users** and **20 rounds per user**. The JSON output was saved as `local_load_results.json` and validated as valid JSON. This is additional evidence; it does not replace the project's earlier SQLite or PostgreSQL runs.

| Measurement | Single-user baseline | 50-user load | Acceptance | Result |
|---|---:|---:|---|---|
| NFR-01 question-page mean | 14.64 ms | 615.48 ms | — | Measured |
| NFR-01 question-page p95 | 26.97 ms | 3,289.88 ms | ≤3,000 ms | **FAIL** |
| NFR-01 question-page maximum | 62.90 ms | 19,907.98 ms | ≤3,000 ms | **FAIL** |
| NFR-02 autosave mean | 8.81 ms | 455.47 ms | — | Measured |
| NFR-02 autosave p95 | 22.18 ms | 2,563.92 ms | — | Measured |
| NFR-02 autosave maximum | 28.26 ms | 11,303.09 ms | ≤2,000 ms | **FAIL** |
| NFR-06 question-page mean growth | — | +4,105.28% | ≤20% | **FAIL** |
| NFR-06 autosave mean growth | — | +5,067.56% | ≤20% | **FAIL** |
| Failed HTTP requests | 0 | 0 | 0 | **PASS** |

The run measured **1,000 concurrent page requests** and **1,000 concurrent autosave requests**, with no reported server errors; elapsed wall time was **28.15 seconds**. Successful HTTP requests do not imply acceptable latency or scalability.

**Conclusion:** NFR-01, NFR-02 and NFR-06 failed in this local SQLite run. Existing PostgreSQL measurements met the absolute NFR-01 and NFR-02 latency thresholds, but NFR-06 remained failed. Target-deployment verification is still pending. 
The raw test evidence has been uploaded and committed to [docs/evidence/local_load_results.json](evidence/local_load_results.json), completing the local SQLite load-test evidence archive.


## Scope and provenance

Local readiness branch `evaluation-readiness`, based on main `7abce9eb8c6d4016a5125738c3b93a4404597f93`; 14 November 2026, Windows, Python 3.13.13, Django 5.2.18, SQLite. Full regression ran outside the restricted socket sandbox against Django's isolated temporary test database. Browser checks used temporary local fixture accounts/exam and removed them after the run. Browser screenshots and JSON retain the actual installed versions, not a claim that Chrome 148 is current stable.

Mobile evidence: [Chrome phone question](evidence/browser-completed/chrome/phone-question_page.png) and [Firefox phone question](evidence/browser-completed/firefox/phone-question_page.png). Both runs check that the first answer lies inside the initial viewport and that collapsed instructions can be opened. Each run also verifies the actual page width and height. Historical `browser-current` screenshots used native-window sizing, which could be clamped to 500 px; they are superseded for exact-phone-width acceptance by `browser-completed`. This fixes the layout obstruction; it does not replace participant confirmation of usability **on mobile devices**, which was not established by the five-user laptop walkthrough.

Firefox now sets the page viewport through WebDriver BiDi; Chrome uses device metrics. The navigation helper resolves the button again if a completed page transition invalidated its previous element reference. No failed application assertion is ignored or converted into a pass.

## Browser matrix at review date

The optional/PR browser workflow requests Chrome 157/158 and Firefox 159/160 at desktop and phone widths, checks actual requested major versions, and uploads results/screenshots even when a job fails. Both final jobs passed on source commit `0aa9548b23a3c29e6becbbdb08dce551b9c426b3`. Chrome 158 is an early-stable Windows release at review time; 157 is the broadly stable major. The explicitly tested version matrix must be refreshed when releases change.

| CI runner | Browser | Desktop checks | Phone checks |
|---|---|---|---|
| Ubuntu | Chrome 157.0.8103.50 | 31/31 | 32/32 |
| Ubuntu | Firefox 159.0.1 | 31/31 | 32/32 |
| Windows | Chrome 158.0.8127.18 | 31/31 | 32/32 |
| Windows | Firefox 160.0 | 31/31 | 32/32 |

[Ubuntu artifacts](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43497888502/artifacts/14071893839) and [Windows artifacts](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43497888502/artifacts/14073505432) contain exact versions, per-check results and screenshots. Final [Django PR CI](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43497888460) and [push CI](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43497878922) also passed. Artifacts may expire according to repository retention; the run logs and this summary identify the verified source commit.

Version references: [Google November release log](https://chromereleases.googleblog.com/2026/11/) (157 stable, 158 early stable); [Mozilla Firefox 160](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/160), [159](https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/159).

## Submission state

The PDF execution addendum was generated from `docs/TEST_CASE_EXECUTION.md` and all six pages visually reviewed. It is a revision of expected steps/coverage, not an invented execution pass sheet. The design register, evidence index, demo scripts and remaining team acceptance checklist are prepared for real review.

**The five-person usability walkthrough is now complete (NFR-03 passed; see results above).** Final board linkage, two actual sprint recordings, deployed TLS/uptime/scheduler checks, quantitative maintainability evidence and human review/freeze remain separate outstanding gates. Performance failures remain visible. Do not use the green automated suite or the usability walkthrough to close those gates.

## Final sign-off round

See the [final sign-off checklist](FINAL_TECHNICAL_SIGNOFF_CHECKLIST.md) for the updated status. PostgreSQL passed both absolute latency limits, SQLite failed both, and each failed the 20% growth criterion. Local HTTPS, exam-window access and the finalizer passed their smoke checks. **The five-person usability study is complete;** intended-deployment evidence still needs review. The historical browser matrix above applies to its original revision. See [current PR checks](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/pull/59/checks).
