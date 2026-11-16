# Team acceptance and remaining evaluation gates

Prepared 14 November 2026. **Release not frozen.** Repository issue closure is not an acceptance signature.

| Gate | Owner | Current evidence / next action |
|---|---|---|
| Five-user usability study | Aditya-TJ (#29) | Not conducted. Recruit five first-time users; use the existing protocol and fill actual observations. No simulated participants. |
| Two-version browser matrix | Aditya-TJ (#29) | Passed 252 checks across Chrome 157/158 and Firefox 159/160. See the [validation report](VALIDATION_RESULTS.md). |
| Performance acceptance | Aditya-TJ (#28), backend owner | Retain failures and target-environment limits. Fix and remeasure or record explicit evaluator acceptance. |
| Test-case revision and evidence index | Aditya Jaiswal (original cases), Aditya-TJ (plan) | Current execution addendum and index prepared; team review required. |
| Separate sprint recordings | Demo team (#31) | [Sprint 1, 60 seconds](../Project_Demo/Sprint_1_Demo.mp4) and [Sprint 2, 120 seconds](../Project_Demo/Sprint_2_Demo.mp4) are available as retrospective demonstrations. |
| Linked GitHub Project and sprint views | Repository maintainers | Board linkage remains unverified. The [sprint backlog snapshot](SPRINT_BACKLOG.md) lists all 24 existing stories, owners and estimates for linking to the board. |
| Human review | Reviewing repository owner | No human review submissions found on 25 merged baseline PRs. Review the readiness PR and record a real final integration review; do not backdate reviews. |
| Retrospective and freeze | Abhishek Anand (#32), all team members | Hold meeting and fill actual attendees, findings/actions, reviewed SHA, approver and date. |
| Final demo and viva | All members | Rehearse each person's PRs, implementation choices, tests, story points and blockers. |

## GitHub Project setup

An authorized maintainer should open the organization Projects page, create a project, and link `SE-Mini-Project-6/Online-Exam-Portal`. Add existing issues #9-#32. Use Status, Assignees, Story Points, Sprint and Requirement fields. Sprint 1 stories are #9-#20 (19-23 October 2026); Sprint 2 stories #21-#32 (26-30 October 2026). The historical dates come from issues; do not claim the board existed then if it is created now.

Make views for each sprint and a remaining-validation view. Closed issue #29 needs a visible follow-up or reopening decision because its evidence still says the participant study is pending. Give evaluators read access to the board and record its URL here once created. Current board URL: **pending**.

## Recording delivery

Both videos capture live application states from seeded demo accounts. The [recording notes](../Project_Demo/README.md) give the source revisions, durations and setup. The generic recording remains available as historical evidence.

## Real final-review record

- Meeting date/time and attendees: pending.
- Reviewed branch/commit: pending final review. The [post-merge test run](https://github.com/SE-Mini-Project-6/Online-Exam-Portal/actions/runs/43594192327) passed for `41bc4aa`.
- Core demo observed by: pending.
- Accepted deviations / evaluator permission: pending; see register.
- Remaining risks, owners and due dates: pending meeting decisions.
- Reviewer approval link: pending.
- Freeze approver and time: pending.

The maintainer may fill these fields only after the events occur. Do not infer approval from a green test run.
