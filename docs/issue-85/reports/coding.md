# Issue #85 — Coding Record

loop_state: phase2-complete

code_under_review: e7a6a33

## Upstream basis

- Issue #85 (rewrite README around the problems on-the-record solves, benefit-first).
- PR #86 phase-1 proposal: `docs/issue-85/proposals/readme-rewrite.md`.
- Approval: approved via PR #86, per task brief ("approved via PR #86").
- Phase-1 survey: `docs/issue-85/reports/current-state-survey.md`.

## Why

Execute the approved rewrite: lead README.md / README.ko.md with the five
named problems and the "off the record vs on the record" brand answer,
above the fold, then reposition all existing accurate mechanism/install
content as supporting detail below it — without inventing new technical
claims and while bringing README.ko.md to structural parity with README.md.

## What was done

- Rewrote `README.md`: new opening section listing the five problems (vibe
  coding drift, quality coin-flip, re-taught rules, no handover, parallel-agent
  collisions), followed by the "Other AI works off the record. Yours works
  on the record." brand section (issues=requirements/PRs=work/recorded
  approvals=decisions/versioned rulebooks=rules, plus the four benefits:
  clean-context role experts, process asset in git, sole-approver CEO
  position, self-contained single plugin). All prior content (musters-a-role
  intro, directory map, Getting started, Why this exists, Roles, Using it,
  Isolation, Three traps + package-registry/web-access/default-open-posture
  subsections, Gates, Self-check, Open) preserved verbatim below the new hook,
  reused rather than rewritten.
- Rewrote `README.ko.md` as an independent Korean rewrite carrying the same
  new structure: the five-problems hook and the on-the-record brand section
  translated idiomatically (not literal), followed by the previously-existing
  Korean content. Fixed the parity gaps the proposal and survey named:
  added a full "시작하기 (Getting started)" section (previously missing),
  and added the "패키지 레지스트리 접근 (issue #38)", "웹 접근 (issue #58,
  #65)", and "기본 개방 태세 (issue #72)" subsections under the traps
  section (previously missing). Also updated stale content encountered
  while achieving parity: the outdated `harness`-name footnote and the
  `role-handoff-contract.md`/`contract/` wording were replaced with the
  current `docs/specs/approvers.md` / core-only-canonical-contract wording
  already used in README.md, since carrying the stale terms forward would
  have made the Korean file inaccurate rather than just non-parallel.

## What did not work

(none)

## Open findings

None raised against this work.

## Next steps

None — proposal scope executed. Any future README content changes are
out of scope for this record.

## Open-finding resolution path

No open findings currently block progress. Should a reviewer raise a
blocking finding, it will be addressed and logged here as
resolved_findings before further commits, per the coding-progress gate.

## resolved_findings

(none)

## closed_checks

closed_checks:
  - check: readme-rewrite-hunt (links/facts/parity/skeleton)
    code_sha: e7a6a33
    result: no finding

## hunt-results

A warrant-hunter probe ran against `code_under_review: e7a6a33` covering
broken links/anchors, factual contradictions vs. repo docs, Korean/English
parity gaps, and skeleton deviations from the approved proposal. The probe
concluded with no finding.

## board-gate note

The hunter's report was written to `docs/reports/2026-07-29-hunt-readme-rewrite.md`,
outside the issue tree. Per contract v3 s11 (board-gate R5), the `coding`
role may write only `coding.md` and `coding/**` under
`docs/issue-85/reports/`; relocating a foreign role's record into
`docs/issue-85/reports/` is refused by the gate for this session (it is
warrant-hunter's own record to place, at `docs/issue-85/reports/warrant-hunter.md`
or `docs/issue-85/reports/warrant-hunter/**`). The report file itself was
kept and staged at its current standing-bucket location
(`docs/reports/2026-07-29-hunt-readme-rewrite.md`) rather than lost; a
warrant-hunter-role session or the human maintainer should complete the
move into the issue tree.
