---
loop_state: landed
---

# Execution observation — issue #441

Observed role: `architecture`. Observed artifacts: PR #442 (merged via
`0fa8a2c`, 2026-08-07T10:55:06+09:00), its phase-1 commits `05f4866`,
`0af7d94`, its phase-2 commit `d289d33`, `docs/specs/enforcement-boundary.md`,
`docs/issue-441/reports/architecture.md`,
`docs/issue-441/proposals/2026-08-07-contract-enforcement-boundary.md`.

**Independence statement**: this role did not author or edit any of the
observed artifacts this session. Nothing under `architecture`'s `src/`,
`test/`, or `docs/issue-441/reports/architecture*` paths was touched by
this session; all findings below return only through this role's own
record.

## What was done

Read PR #442's merged commits (`05f4866`, `0af7d94`, `d289d33`), the
issue's full body and all 6 comments with timestamps, `docs/specs/
enforcement-boundary.md`, `docs/issue-441/reports/architecture.md`, the
`spawn.py` diff, and `on-the-record/hooks/contract-guard.sh` in full.
Checked outcome against the issue's own 5-item Acceptance list, checked
trajectory against the phase-1→phase-2 commit/approval sequence, and
checked whether any single artifact is deficient — the upstream basis for
each check is cited inline by commit SHA, file, or comment timestamp
throughout the sections below.

## Outcome

The issue's Acceptance list has five checks. Against the merged state:

1. "소비 프로젝트 한 곳에서 `closes-gate` 가 실제로 돌아 phase-1/phase-2
   규율을 강제한다 — 실행으로 보일 것" — **met**. `architecture.md`'s
   "Live, zero-install consumer demonstration" section runs
   `contract-guard.sh` and `spawn.py`'s `require_acceptance_gate` for real
   against a fresh `project-rich` clone with no on-the-record install,
   showing an actual refusal (exit 2 / session-abort text), not a
   description of one. Independently confirmed by reading
   `on-the-record/hooks/contract-guard.sh` (114 lines, `PreToolUse`+`Bash`,
   intercepts `gh pr merge`, denies via `sys.exit(2)`) and the
   `spawn.py` diff in commit `d289d33` (`require_acceptance_gate`, wired
   into `main()` before `_spawn_one`).
2. "종결 일관성 스윕이 소비 프로젝트에서 돈다" (`closure_sweep.py`
   board-wide) — **explicitly out of scope**, not met and not claimed met.
   `docs/specs/enforcement-boundary.md` records `closure_sweep.py`
   board-wide mode as "out of scope — operator decision, 2026-08-07,"
   citing the operator's issue-441 comment at 2026-08-07T10:32:56Z
   ("이미 어긋난 상태를 사후에 발견하는 것은 이 이슈의 범위가 아니다").
   This is a legitimate scope narrowing by the operator, not a gap
   architecture introduced or hid — the boundary doc names it plainly.
3. "배포되는 것과 안 되는 것의 경계가 손으로 유지되는 목록이 아니라
   도출된다" — **met**. `gates/test_boundary.py` (104 lines, added in
   `d289d33`) walks the filesystem and fails the build on any
   `gates/*.py`/hook/workflow with no row in
   `docs/specs/enforcement-boundary.md`; `architecture.md`'s Verification
   section shows it run live, and shows it actually catching an
   unrecorded throwaway module and passing once removed.
4. "강제되지 않는 계약 조항이 있다면 그 목록이 소비 프로젝트에서 읽을 수
   있다" — **not met, undisclosed as such**. `docs/specs/
   enforcement-boundary.md` is the list, but it lives only in the
   on-the-record repository's own `docs/specs/`. `grep -rln
   enforcement-boundary on-the-record/` (the plugin-shipped directory
   named in the issue body itself: "플러그인이 담는 것:
   on-the-record/commands, on-the-record/hooks") finds only a
   comment-string reference inside `contract-guard.sh`, not the file
   itself or any mechanism that surfaces its content inside a consumer
   session. A consumer that installed only the plugin — the exact
   scenario `architecture.md`'s own "Live... demonstration" section
   demonstrates for criteria 1 and 3 — has no zero-install path to read
   this list; they would need to separately visit the on-the-record
   repository. `architecture.md`'s "What shipped" item 4 records the
   per-session visibility check as **dropped**, and its "Alternatives
   considered" section reasons that nothing is left for such a check to
   report once board-wide drift detection went out of scope — but that
   reasoning answers a narrower question (is CI-supplement installation
   observable) than criterion 4 actually asks (is the unenforced-clause
   list reachable from inside a consumer project at all, zero-install).
   Those are not the same question, and the record does not name the gap
   between them.
5. "각 게이트가 계약의 일부인지 내부 사정인지에 대한 기계별 판단"
   — **met**. `docs/specs/enforcement-boundary.md`'s three tables cover
   all `gates/*.py` modules, all plugin-shipped hooks, all workflows, and
   `spawn.py` itself, each with a verdict and reason; `gates/
   test_boundary.py` is the mechanical floor stated in the issue's own
   "unverifiable" acceptance note (no gate with a missing verdict).

Finding (blameless shape): criterion 4 is stated as satisfied
implicitly (via item 4 being "dropped" with a stated reason) but the
reason given does not address zero-install reachability, only
CI-supplement-installation observability.
- **Impact**: a consumer who reads only what installs with the plugin
  cannot learn which contract clauses are unenforced for them (e.g.
  `landing_readiness.py`, recorded `contract, CI-supplement` in
  `docs/specs/enforcement-boundary.md`) — the exact failure mode #310
  and this issue's own framing warn against ("검사되지 않는 규칙이 강제되는
  규칙 행세").
- **Timeline**: introduced in `d289d33` (2026-08-07T10:47:44+09:00),
  when item 4's visibility check was dropped per the operator's
  2026-08-07T10:32:56Z follow-up comment giving architecture discretion
  to drop it "필요없다고 판단되면... 이유를 적어라."
- **Root cause**: the operator's follow-up comment scoped item 4 around
  one narrower question (CI-supplement install visibility); architecture
  answered that narrower question and treated it as discharging the
  issue's broader criterion 4 text, without flagging the gap between the
  two.
- **Action item**: not filed as an issue by this role (contract v3:
  issues are user-authored only) — recorded here for the human to judge
  and file if they agree it's a real gap, e.g. a plugin-shipped command
  or hook-emitted line surfacing `docs/specs/enforcement-boundary.md`'s
  unenforced rows inside a consumer session.

## Trajectory

Phase-1→phase-2 path, read from the PR's own commit history and the
issue's own comments (contract v3 s19 shape: research → survey → propose
→ approve → build):

- Phase-1 commits `05f4866` (2026-08-07T10:08:42Z, initial survey +
  proposal) and `0af7d94` (2026-08-07T10:26:29Z, a **rework** after "PR
  #442 was rejected" per that commit's own message — its message states
  the rejection reason: hand-added CI caller file left installation state
  unknowable) show one real reject-and-rework cycle inside phase 1, not a
  single unreviewed pass.
- First approval: `APPROVE issue-441/architecture` at
  2026-08-07T10:32:55Z, immediately followed (10:32:56Z) by an
  operator feedback comment attached to that approval, scoping
  `closure_sweep.py`/`spawn_coverage.py` out and asking architecture to
  re-decide item 4. Phase-2 commit `d289d33` (10:47:44Z) directly
  implements both instructions — the commit message names the operator's
  follow-up explicitly and `docs/specs/enforcement-boundary.md`'s verdict
  values quote the exact scope decision. This is a sound, cited
  approval→build link.
- Second approval: `APPROVE issue-441/architecture` at
  2026-08-08T08:07:17Z, followed at 08:08:21Z by a further operator
  feedback comment (hooks-primary-over-CI framing) and at 08:08:40Z by a
  `stranded-relay` system message: PR create failed, "No commits between
  main and issue-441/architecture" — the branch had already been merged
  and reset to `main`, so a session opened against this second approval
  produced nothing and never reached a PR. The relay message itself says
  a human must intervene.
  - Substance check: does the already-merged `d289d33` already satisfy
    the 08:08:21Z feedback ("hooks primary, CI-supplement only optional,
    phase 2 must reflect this priority")? Yes, on the artifacts already
    read above — `contract-guard.sh` and `spawn.py`'s preflight are the
    primary zero-install path; every `.github/workflows/*.yml` row in
    `docs/specs/enforcement-boundary.md` is `repo-local`, none shipped to
    consumers. So the *content* of the 08:08:21Z feedback is already
    reflected in what merged, even though that merge predates the
    comment by ~21 hours and the second approval round produced no new
    commit addressing it directly.
  - This is a genuine trajectory gap, but not a soundness defect in the
    merged work itself: the second round is stranded/incomplete, not
    wrong. It is an open loop, flagged by its own relay message, not a
    silent failure this role is newly surfacing.

## Step

No single artifact is deficient in a way that blocks closing #441.
`gates/test_boundary.py` and `docs/specs/enforcement-boundary.md` are
internally consistent with each other and with the issue's own acceptance
language, verified by direct reading (not re-execution) in this session.
The one deficiency found (criterion 4's zero-install reachability, above)
is a scope-interpretation gap in `architecture.md`'s reasoning, not a
broken test or a false claim — `architecture.md` does not claim item 4 is
still met; it records it as dropped, which is honest but leaves the
issue's own criterion 4 unaddressed by name.

## Verdict — can #441 close?

**Yes, with one open item to route to the operator.** Outcome: 4 of 5
Acceptance criteria are met and demonstrated live (not merely argued);
the 1 unmet-and-not-flagged criterion (#4, zero-install reachability of
the unenforced-clause list) is a real but narrow gap — the list exists
and is correct, it is just not reachable from a plugin-only install.
Trajectory: phase-1→phase-2 for the merged PR was sound (one honest
reject-and-rework cycle, cited operator approval before each build step).
The second approval round (2026-08-08T08:07:17Z) is stranded and did not
produce a PR, but its substance is already reflected in what merged — it
does not block closing #441 on its own, though the stranded session
itself is an open loop a human should clear (start a fresh session or
close it out) separately from the #441 closability question.

Recommendation: the operator can close #441 on the merged state, treating
criterion-4 zero-install reachability as either (a) accepted as
out-of-scope alongside item 2's board-wide-drift narrowing (operator's
call to make, not this role's), or (b) filed as a small follow-up issue if
the operator wants a plugin-shipped surface for the unenforced-clause
list. Either resolves the one open item found in this observation.

## Open findings

One: criterion 4 (unenforced-clause list readable from a consumer
project, zero-install) is not actually discharged by the merged delivery
— see "Outcome" item 4 above for the full blameless-shape writeup. Not
filed as an issue by this role; routed to the operator for a scope call.
