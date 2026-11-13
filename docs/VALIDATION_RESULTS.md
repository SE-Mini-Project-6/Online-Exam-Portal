# Readiness branch validation

Revision prepared 14 November 2026. Actual branch results are recorded here after execution. Baseline CI on main `7abce9e` passed 145 tests; this does not automatically validate new changes.

| Check | Current readiness result |
|---|---|
| System check | Passed: no issues |
| Migration consistency | Passed: no changes detected |
| Full regression suite | Passed: 147 tests in 236.170 s; [verbose log](evidence/regression.txt) |
| Browser flows / mobile layout | Passed: installed Chrome 148.0.7778.169 and Firefox 160.0, exact 1280x800 and 375x812 page viewports, 122/122 checks; [results](evidence/browser-completed/results.json), [summary](evidence/browser-completed.txt) |
| Before/after 50-user load measurement | Measured: question mean 439.1 -> 301.4 ms; strict maximum/growth targets still fail; [before](evidence/load-before.json), [after](evidence/load-after.json) |
| Five-user usability | Pending real participants |
| Required second browser versions | Passed: Chrome 157.0.8103.50 / 158.0.8127.18 and Firefox 159.0.1 / 160.0, desktop + exact phone viewports, 252/252 CI checks; [run and artifacts](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43497888502) |
| Target HTTPS/uptime/scheduler | Pending target-environment evidence |
| Human review / freeze | Pending team approval |

Raw outputs are retained under `docs/evidence/`. Record errors and failed targets without changing the SRS thresholds.

## Scope and provenance

Local readiness branch `evaluation-readiness`, based on main `7abce9eb8c6d4016a5125738c3b93a4404597f93`; 14 November 2026, Windows, Python 3.13.13, Django 5.2.18, SQLite. Full regression ran outside the restricted socket sandbox against Django's isolated temporary test database. Browser checks used temporary local fixture accounts/exam and removed them after the run. Browser screenshots and JSON retain the actual installed versions, not a claim that Chrome 148 is current stable.

Mobile evidence: [Chrome phone question](evidence/browser-completed/chrome/phone-question_page.png) and [Firefox phone question](evidence/browser-completed/firefox/phone-question_page.png). Both runs check that the first answer lies inside the initial viewport and that collapsed instructions can be opened. Each run also verifies the actual page width and height. Historical `browser-current` screenshots used native-window sizing, which could be clamped to 500 px; they are superseded for exact-phone-width acceptance by `browser-completed`. This fixes the layout obstruction; it does not replace participant confirmation of usability.

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

Five-person usability, final board linkage, two actual sprint recordings, deployed TLS/uptime/scheduler checks, quantitative maintainability evidence and human review/freeze remain separate outstanding gates. Performance failures remain visible. Do not use the green automated suite to close these gates.
