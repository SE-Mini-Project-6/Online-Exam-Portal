# Usability and Browser Compatibility Verification (Sprint 2, issue #29)

Requirements: NFR-03 (usability, 5-user walkthrough) and NFR-07 (latest two versions of Chrome and Firefox).
Owner: @Aditya-TJ.

**Status at a glance**

| Part | Status |
|---|---|
| Chrome and Firefox checks (NFR-07) | Done for the latest installed version of each. Previous-version check still open (section 2.3) |
| Scripted task flow in both browsers | Done, 25 of 25 checks pass in each browser at desktop and phone width |
| Five-user walkthrough (NFR-03) | **Not yet conducted.** Needs five people. Protocol and log are ready below (section 3) |
| Findings logged and retested | 1 fixed and retested, 1 open |

## Readiness follow-up (14 November 2026)

The question page now puts availability details and instructions in an accessible, keyboard-operable disclosure, closed initially. The timer remains visible and the phone layout uses compact spacing so the first answer does not require scrolling past the full rules panel. This addresses the layout cause of F-02; participant confirmation is still pending. Current rerun results and screenshots are indexed in [readiness validation](../docs/VALIDATION_RESULTS.md). Historical results below have been preserved rather than overwritten.

The browser runner accepts `--evidence-dir`, `--chrome-version` and `--firefox-version` for separately recorded version combinations. Explicit versions may require Selenium-managed downloads. Record the agreed assessment-date versions before claiming the latest-two-version requirement.

**Issue #29 reconciliation:** its closed status and checked boxes do not establish that the five-user study occurred. The current session log remains empty. Complete the actual study before marking NFR-03 verified.

The scripted run does not replace the five-user walkthrough. NFR-03 asks whether a first-time student
understands the exam without help, which only people can show. Nothing in section 3 has been filled in with
invented results.

## 1. Automated browser checks

`Deliverable-4-Test-Validation/browser_checks/run_browser_checks.py` seeds throwaway data, starts the app on a free
local port, and drives real Chrome and Firefox (headless, Selenium) at two viewports. Each run does:

- Student: open login page, sign in, dashboard lists the exam, available-exams page, open question 1 of 3,
  countdown timer shows, choose an answer and wait for "Saved" within 2 s, tick Mark for review and see the grid
  turn to answered + marked, reload and confirm the answer persisted, press Next, go to the confirmation page
  (shows 1 of 3 answered), confirm the submission, reach the "submitted successfully" page, sign out.
- Admin: sign in, dashboard, create-exam form, question list (3 questions), add-question form.
- On every page: no horizontal scroll at the viewport width, and a screenshot saved.
- Chrome only: no severe console errors (geckodriver does not expose the console log).

```powershell
pip install selenium
python Deliverable-4-Test-Validation/browser_checks/run_browser_checks.py
```

Results are written to `browser_checks/evidence/results.json`, with screenshots in `evidence/chrome` and
`evidence/firefox`. The script exits non-zero if any check fails and refuses to run if its port is occupied.

### 1.1 Browsers tested

| Browser | Version | Viewports | Checks passed (before fix) | Checks passed (after fix) |
|---|---|---|---|---|
| Google Chrome | 148.0.7778.169 | 1280x800, 375x812 | 24/25, 24/25 | 25/25, 25/25 |
| Mozilla Firefox | 150.0 | 1280x800, 375x812 | 25/25, 25/25 | 25/25, 25/25 |

Before-fix results are kept in `evidence/results_before_fix.json`, after-fix in `evidence/results.json`.
Host: Windows 11.

## 2. Findings log

| ID | Found by | Finding | Severity | Status |
|---|---|---|---|---|
| F-01 | Chrome console check | Every page triggered `GET /favicon.ico` 404, logged as a SEVERE console error in Chrome. Firefox does not report it | Low | **Fixed and retested.** Inline SVG `<link rel="icon">` added to `templates/base.html`. Chrome re-run: 25/25 at both widths. Regression test `exams/test_browser_compat.py` |
| F-02 | Reviewing phone screenshots (375 px) | The timer, availability panel and instruction list pushed question options below the initial phone viewport. | Medium (usability) | **Layout revised; participant confirmation pending.** Details/rules are now collapsed initially; timer stays visible and mobile spacing is reduced. See readiness browser evidence for measured option visibility; the five-user walkthrough still needs to confirm usability. |

Not a finding but worth stating: the test suite and scripted run use the development server over HTTP
(`DJANGO_DEBUG=True`). With `DEBUG` off the site redirects to HTTPS, so browser behaviour behind TLS (mixed content,
secure cookies) has not been exercised here.

### 2.3 Gaps in the browser matrix

- NFR-07 says the **latest two** versions. Only the latest installed stable build of each browser was available, so
  Chrome 147 and Firefox 149 were not tested. This needs an environment with the previous versions, for example
  BrowserStack, or portable installs, before the requirement can be called fully verified.
- Headless mode was used. A person opening the pages in a visible window is covered by the walkthrough below.
- Only the paths listed in section 1 were exercised. The results page and timer expiry redirect were not.

## 3. Five-user walkthrough (NFR-03)

Pass criterion from the SRS: a first-time student can understand how to **answer**, **mark for review** and
**submit** without external help.

### 3.1 Protocol

1. Choose five people who have not used the portal and are not on the project team. Mix of devices if possible.
2. Create a student account and an exam with at least 5 questions that is open now
   (see `docs/SPRINT2_ARCHITECTURE_DEPLOYMENT.md` for local setup).
3. Give each participant only this prompt: *"You are a student. Sign in, take the exam, mark one question you want to
   revisit, and submit your answers."* Do not explain the screens or point at anything.
4. Observe silently. Record time per task and every hesitation, wrong click or question asked. Count a task as
   unaided only if the participant completes it without any hint from you.
5. Afterwards ask: what was unclear, what would you change, and could you tell your answer had been saved.
6. Log each issue in section 2 with an ID, fix it, and have the same or another participant retry the failed task.

### 3.2 Session log

| # | Participant (role, device, browser) | Date | Answer unaided | Mark for review unaided | Submit unaided | Time to submit | Issues (finding IDs) |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |

### 3.3 Result

Pending. NFR-03 counts as verified when all five complete the three tasks unaided, or when each failure has a
logged finding that was fixed and retested by the participant who hit it.

## 4. Automated tests added

`exams/test_browser_compat.py` checks the page head: favicon link, viewport meta tag, `lang` and charset.
Full suite: 136 tests, all passing.

## 5. Design deviations

None against the SADS. The favicon is a presentation-only change. F-02 may become a layout change to the question
page if the walkthrough confirms it.
