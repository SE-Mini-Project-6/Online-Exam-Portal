# Usability and Browser Compatibility Verification (Sprint 2, issue #29)

Requirements: NFR-03 (usability, 5-user walkthrough) and NFR-07 (latest two versions of Chrome and Firefox).  
Owner: @Aditya-TJ.

**Status at a glance**

| Part | Status |
|---|---|
| Chrome and Firefox checks (NFR-07) | **Latest-two-version CI matrix passed**: Chrome 157/158 and Firefox 159/160, 252/252 checks (see readiness follow-up and linked validation results). Historical single-version results are retained below. |
| Scripted task flow in both browsers | Historical run: 25/25 checks passed in each browser at desktop and phone width. The later readiness CI matrix passed 252/252 checks. |
| Five-user walkthrough (NFR-03) | **Completed: 5/5 participants passed** all three tasks unaided (section 3). |
| Findings logged and retested | F-01 fixed and retested; F-02 layout revised, with mobile participant confirmation still outstanding. No new issues were reported in the five-user walkthrough. |

## Readiness follow-up (14 November 2026)

The question page now puts availability details and instructions in an accessible, keyboard-operable disclosure, closed initially. The timer remains visible and the phone layout uses compact spacing so the first answer does not require scrolling past the full rules panel. This addresses the layout cause of F-02; **confirmation specifically on a phone-sized device remains pending**. Current rerun results and screenshots are indexed in [readiness validation](../docs/VALIDATION_RESULTS.md). Historical results below have been preserved rather than overwritten.

The browser runner accepts `--evidence-dir`, `--chrome-version` and `--firefox-version` for separately recorded version combinations. Explicit versions may require Selenium-managed downloads. Record the agreed assessment-date versions before claiming the latest-two-version requirement.

**Issue #29 reconciliation:** the issue's closed status alone was not evidence that the five-user study occurred. The manual walkthrough has now been performed and its reported results are recorded in section 3. This is separate from the automated browser checks.

**Current browser result:** the final readiness CI on source commit `0aa9548` passed 252/252 checks across Chrome 157/158 and Firefox 159/160, at 1280x800 and 375x812. [Results, exact versions and artifact links](../docs/VALIDATION_RESULTS.md#browser-matrix-at-review-date). The historical one-version matrix below is superseded for browser compatibility by that execution.

**Manual walkthrough update (16 November 2026; confirm date):** five first-time student participants were observed taking a five-question Software Engineering exam in a locally hosted instance. All five answered questions, marked one for review, and submitted without assistance. Participant-level results and feedback appear in section 3. Device/browser details for the sessions were not individually recorded and should be added if known.

The scripted run does not replace the five-user walkthrough. NFR-03 asks whether a first-time student understands the exam without help, which only people can show.

## 1. Automated browser checks

`Deliverable-4-Test-Validation/browser_checks/run_browser_checks.py` seeds throwaway data, starts the app on a free local port, and drives real Chrome and Firefox (headless, Selenium) at two viewports. Each run does:

- Student: open login page, sign in, dashboard lists the exam, available-exams page, open question 1 of 3, countdown timer shows, choose an answer and wait for "Saved" within 2 s, tick Mark for review and see the grid turn to answered + marked, reload and confirm the answer persisted, press Next, go to the confirmation page (shows 1 of 3 answered), confirm the submission, reach the "submitted successfully" page, sign out.
- Admin: sign in, dashboard, create-exam form, question list (3 questions), add-question form.
- On every page: no horizontal scroll at the viewport width, and a screenshot saved.
- Chrome only: no severe console errors (geckodriver does not expose the console log).

```powershell
pip install selenium
python Deliverable-4-Test-Validation/browser_checks/run_browser_checks.py
```

Results are written to `browser_checks/evidence/results.json`, with screenshots in `evidence/chrome` and `evidence/firefox`. The script exits non-zero if any check fails and refuses to run if its port is occupied.

### 1.1 Browsers tested (historical local run)

| Browser | Version | Viewports | Checks passed (before fix) | Checks passed (after fix) |
|---|---|---|---|---|
| Google Chrome | 148.0.7778.169 | 1280x800, 375x812 | 24/25, 24/25 | 25/25, 25/25 |
| Mozilla Firefox | 150.0 | 1280x800, 375x812 | 25/25, 25/25 | 25/25, 25/25 |

Before-fix results are kept in `evidence/results_before_fix.json`, after-fix in `evidence/results.json`.  
Host: Windows 11.

**Later NFR-07 evidence:** The readiness CI matrix across Chrome 157/158 and Firefox 159/160 passed 252/252 checks; see the [readiness validation](../docs/VALIDATION_RESULTS.md#browser-matrix-at-review-date) for the definitive version matrix and artifacts.

## 2. Findings log

| ID | Found by | Finding | Severity | Status |
|---|---|---|---|---|
| F-01 | Chrome console check | Every page triggered `GET /favicon.ico` 404, logged as a SEVERE console error in Chrome. Firefox does not report it. | Low | **Fixed and retested.** Inline SVG `<link rel="icon">` added to `templates/base.html`. Chrome re-run: 25/25 at both widths. Regression test `exams/test_browser_compat.py`. |
| F-02 | Reviewing phone screenshots (375 px) | The timer, availability panel and instruction list pushed question options below the initial phone viewport. | Medium (usability) | **Layout revised; mobile participant confirmation pending.** Details/rules are now collapsed initially; timer stays visible and mobile spacing is reduced. See readiness browser evidence for measured option visibility. The five-user walkthrough did not document a phone-sized-device retest. |

**Manual walkthrough findings:** No new usability issues were reported by P1–P5. No issue-specific fix/retest was needed for those sessions. This does **not** establish that F-02 was verified by a participant on a phone.

Not a finding but worth stating: the test suite and scripted run use the development server over HTTP (`DJANGO_DEBUG=True`). With `DEBUG` off the site redirects to HTTPS, so browser behaviour behind TLS (mixed content, secure cookies) has not been exercised here.

### 2.3 Historical gaps and remaining limitations

- **Historical matrix gap (subsequently addressed by CI):** the earlier local run tested only one version of each browser. The later readiness CI covered Chrome 157/158 and Firefox 159/160; see the linked matrix for evidence. Do not interpret the historical gap as a current claim that the latest-two-version check is still missing.
- Automated browser tests ran headlessly. The manual walkthrough used a visible browser, but browser version and viewport were not recorded per participant.
- The historical scripted run exercised only the paths listed in section 1. The results page and timer-expiry redirect were not covered in that run.
- The revised phone layout (F-02) has automated viewport evidence, but no documented human phone-sized-device confirmation.

## 3. Five-user walkthrough (NFR-03)

Pass criterion from the SRS: a first-time student can understand how to **answer**, **mark for review**, and **submit** without external help.

### 3.1 Protocol

1. Choose five people who have not used the portal and are not on the project team. Mix of devices if possible.
2. Create a student account and an exam with at least 5 questions that is open now (see `docs/SPRINT2_ARCHITECTURE_DEPLOYMENT.md` for local setup).
3. Give each participant only this prompt: *"You are a student. Sign in, take the exam, mark one question you want to revisit, and submit your answers."* Do not explain the screens or point at anything.
4. Observe silently. Record time per task and every hesitation, wrong click or question asked. Count a task as unaided only if the participant completes it without any hint from you.
5. Afterwards ask: what was unclear, what would you change, and could you tell your answer had been saved.
6. Log each issue in section 2 with an ID, fix it, and have the same or another participant retry the failed task.

### 3.2 Session log (completed)

The five participants tested a locally hosted five-question Software Engineering MCQ exam. They were given separate student accounts. The observer reported that all three required tasks were completed unaided. The completion times below are **total session times**, not per-task measurements.

| # | Participant (role, device, browser) | Date | Answer unaided | Mark for review unaided | Submit unaided | Time to submit | Issues (finding IDs) |
|---|---|---|---|---|---|---|---|
| 1 | P1 — student; Windows laptop; browser not recorded | 2026-11-16* | Yes | Yes | Yes | 60 s | None reported |
| 2 | P2 — student; Windows laptop; browser not recorded | 2026-11-16* | Yes | Yes | Yes | 55 s | None reported |
| 3 | P3 — student; Windows laptop; browser not recorded | 2026-11-16* | Yes | Yes | Yes | 80 s | None reported |
| 4 | P4 — student; Windows laptop; browser not recorded | 2026-11-16* | Yes | Yes | Yes | 100 s | None reported |
| 5 | P5 — student; Windows laptop; browser not recorded | 2026-11-16* | Yes | Yes | Yes | 120 s | None reported |

*Date is based on the testing conversation and should be confirmed before final submission. The same local laptop was used for testing; exact browser and version were not logged.*

**Participant feedback (reported verbatim or lightly normalized):**

| Participant | Feedback |
|---|---|
| P1 | No issues; navigation was easy. |
| P2 | Navigating through the questions was pretty simple. |
| P3 | Simple UI with easy navigation. |
| P4 | No additional feedback; everything works fine. |
| P5 | No issues; everything worked fine. |

**Observation limits:** Individual task timings, wrong clicks, hesitation counts, and whether participants noticed the saved-answer indicator were not recorded separately. Absence of reported issues should not be treated as proof that no hesitation occurred.

### 3.3 Result

**NFR-03: PASS for the specified five-user, three-task acceptance criterion.**

- Participants completing all three tasks unaided: **5/5 (100%)**.
- Individual required tasks completed unaided: **15/15 (100%)**.
- Total recorded completion time: **415 seconds (6 min 55 s)**.
- Average completion time: **83 seconds (1 min 23 s)**.
- Fastest / slowest: **55 s / 120 s**.
- New issues reported during the walkthrough: **none**.

All five participants independently answered questions, marked one for review, and submitted the exam, meeting the stated NFR-03 walkthrough pass criterion. The results apply to these five local sessions and do not establish usability across all devices, browsers, or user populations. In particular, human validation of the phone layout finding F-02 remains open.

## 4. Automated tests added

`exams/test_browser_compat.py` checks the page head: favicon link, viewport meta tag, `lang` and charset.  
Historical full suite: 136 tests, all passing.

## 5. Design deviations

None against the SADS in the documented changes. The favicon is a presentation-only change. F-02 resulted in a revised question-page layout (collapsed rules/details and reduced mobile spacing); automated viewport checks passed, but a participant-based phone confirmation remains pending.
