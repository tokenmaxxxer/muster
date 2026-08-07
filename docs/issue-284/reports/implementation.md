---
kind: coding-record
code_under_review: gates/ci.py, gates/test_closes_gate_ci.py, docs/issue-284/decisions/record-evidence-as-closing-intent.md
loop_state: landed
closed_checks:
  - check: "gates/test_closes_gate_ci.py — 40/40 pass (was 27, added 13
      new cases covering the proposal's 'What will be done' item 4
      scenarios a-e plus direct _phase2_record_evidence coverage)."
    ref: gates/test_closes_gate_ci.py:413
  - check: "six-PR live acceptance test (#331) — real, unmodified
      checkouts of #337/#340/#343/#350/#352/#353's branches (git
      worktrees off fetched remote branches), run through the fixed
      `gates/ci.py --pr <n> --issue <n> --autodetect --closes-only`. All
      six report 게이트 통과. No PR body touched."
    ref: gates/ci.py:229
  - check: "full suite — pytest test_flows.py test_gates.py
      test_approve_scope.py test_vocab_coherence_roles.py
      gates/test_closes_gate_ci.py: 131 passed, 1 failed
      (t_repo_local_claude_config_stops_the_spawn, pre-existing #360
      sandbox pollution, unrelated file). test_spawn.py run separately:
      235/235 passed."
    ref: gates/ci.py:1
open_findings: none
---

# Implementation record — issue #284

## Why

Phase 2, executing the approved proposal
(`docs/issue-284/proposals/2026-08-07-closes-gate-record-evidence-and-fork-fallback.md`,
upstream basis), approved via issue-level comment `APPROVE
issue-284/implementation` (single-account mode, role-handoff contract v3).
Six approved phase-2 delivery PRs (#337, #340, #343, #350, #352, #353)
opened correctly as phase-1 (no `Closes`), got approved, delivered
phase-2 code on the same PR/branch, and went red on closes-gate because
approval flipped the requirement while nobody rewrote the body. Also
fixes the separate fork-PR half of #284: a PR whose branch isn't
`issue-<n>/<role>` could never resolve its issue number, failing closed
even with a legitimate `#N` body reference.

The follow-up comment on the binding APPROVE narrowed the acceptance
criterion to a live re-run of the gate against the six named PRs, without
touching any of their bodies, with actual per-PR results recorded here —
not a predicted pass.

## What was done

1. `gates/ci.py::_phase2_record_evidence(repo, branch, issue) -> bool` —
   parses `role` from `branch` via `_issue_and_role_from_branch`, reads
   `docs/issue-<issue>/reports/<role>.md` from the checkout, returns
   whether `gates.record_frontmatter` finds a non-empty `loop_state`.
   Checks field **presence**, never a specific value (see the decision
   doc below for why).
2. `gates/ci.py::check()`, phase2 branch — after collecting
   `pr_reference.check(...)`'s result: if the only "no Closes" entry is
   present and `_phase2_record_evidence(...)` is true, the entry is
   dropped (record evidence substitutes for the body edit). Otherwise the
   message is rewritten to also name the record-evidence path as an
   alternative.
3. `gates/ci.py::_pr_is_cross_repo(repo, pr) -> bool | None` — `gh pr
   view --json isCrossRepository`, to distinguish a real fork PR from an
   internal PR whose branch merely doesn't follow the naming convention.
4. `gates/ci.py::_fork_issue_from_body(repo, pr) -> int | None` — only
   when `_pr_is_cross_repo` is true, extracts the issue number from the
   PR body's plain `#N` reference (`pr_reference._PLAIN_REF`, the same
   pattern phase1 already requires from every PR body).
5. `gates/ci.py::_autodetect_issue_phase` — when
   `_issue_and_role_from_branch(branch)` is `None`, falls back to
   `_fork_issue_from_body` before failing closed. A same-repo (non-cross-
   repo) wrong-shaped branch still fails closed even with a resolvable
   `#N` in the body — the after-proposal warrant hunt (stance 0) found
   the unguarded version lets an internal PR on a wrong-shaped branch
   spoof an issue reference and reach phase2 via the role-blind
   PR-review-Approve path, since that path never reads `role`.
6. `gates/test_closes_gate_ci.py` — 13 new cases: direct
   `_phase2_record_evidence` unit coverage (existence / missing record /
   empty `loop_state` / non-`issue-<n>/<role>`-shaped branch), the two
   `ci.check()` phase2 scenarios (passes via record evidence without a
   body edit; blocked with both options named when neither is present),
   and the three fork-fallback scenarios (confirmed cross-repo resolves
   with `role=None`; fork-shaped with no resolvable ref still fails
   closed; same-repo wrong-shaped branch with a resolvable `#N` still
   fails closed).
7. `docs/issue-284/decisions/record-evidence-as-closing-intent.md` —
   records the presence-not-value choice on `loop_state`: the declared
   enum in `roles/implementation.json`
   (`scope-proposed/scope-approved/in-progress/landed`) doesn't include
   the real value seen on #337's record (`phase-2-complete`), and that
   mismatch is invisible to CI because the required check runs
   `--closes-only` and skips `record_enums` — gating on a specific value
   would re-break the exact PRs this fix exists to unblock. The enum
   drift itself is out of scope, cross-recorded on #147.

`_phase_from_approval` and `flows._pr_approved` were not touched (#312's
write set, confirmed by reading `_pr_approved` — the two-account
PR-review path never reads `role`, so calling it with `role=None` for
fork PRs was already safe without any change there).
`pr_reference.py::check_body`/`check` were not touched (#228's write
set) — both fixes supplement from `ci.py`, following the existing
`_phase1_surface_mismatch` pattern.

## Six-PR acceptance run (#331) — 2026-08-07, actual results

Ran `python3 gates/ci.py <checkout> --pr <n> --issue <n> --autodetect
--closes-only` against real, unmodified git worktrees of each PR's
fetched remote branch (no PR body edited on any of the six):

| PR   | branch                    | issue | result      |
|------|---------------------------|-------|-------------|
| #337 | `issue-330/implementation` | 330   | 게이트 통과 |
| #340 | `issue-325/implementation` | 325   | 게이트 통과 |
| #343 | `issue-331/implementation` | 331   | 게이트 통과 |
| #350 | `issue-336/implementation` | 336   | 게이트 통과 |
| #352 | `issue-321/implementation` | 321   | 게이트 통과 |
| #353 | `issue-332/implementation` | 332   | 게이트 통과 |

All six pass. This is the acceptance test the issue's binding APPROVE
follow-up specified — run, not predicted; had any of the six still
failed, that would be the reported finding, not a claimed fix.

## Verify

`gates/test_closes_gate_ci.py`: 40/40 pass (was 27, +13).

Full suite (`pytest test_flows.py test_gates.py test_approve_scope.py
test_vocab_coherence_roles.py gates/test_closes_gate_ci.py -q`): 131
passed, 1 failed. `test_spawn.py` run separately (its own suite is slow
under this file grouping): 235/235 passed.

The one failure,
`test_gates.py::t_repo_local_claude_config_stops_the_spawn`
(`OSError: [Errno 30] Read-only file system:
/home/jwjung/.tokenmaxxxer/trusted-repo-config.json`), is the pre-existing
#360 pollution named in the invocation — it writes to a path outside the
repo that this sandbox mounts read-only, and the failing test touches
neither `gates/ci.py` nor `gates/pr_reference.py` nor any file this
change modifies. It also failed identically before this session's edits
(confirmed by running it standalone via `python3 test_gates.py` before
any change here, which hit the same OSError at the same test).

## What did not work

- `_pr_is_cross_repo` was first written with only a return-code check
  around `json.loads(r.stdout)` (matching most of this file's other `gh`
  wrappers). Running the full suite under `pytest` (rather than the
  file's own `__main__` loop) exercised the pre-existing
  `t_autodetect_fail_closed_on_unrecognized_branch`, which doesn't mock
  `_pr_is_cross_repo` — it hit a real `gh pr view` call whose sandboxed
  stdout came back empty with `returncode == 0`, and `json.loads("")`
  raised `JSONDecodeError` instead of falling through to fail-closed.
  Fixed by wrapping the `json.loads` call in the same `try/except
  ValueError: return None` pattern `_pr_commit_messages` already uses in
  this same file.

## Doc-placement ladder

- Decision (check-shape choice on `loop_state` presence-vs-value):
  `docs/issue-284/decisions/record-evidence-as-closing-intent.md`
- No new env var, config key, dependency, or migration.

## Rationale for deviations

None — phase 2 matched the approved proposal's "What will be done"
exactly; no scope-exceeded stop, no alternative swap.

## Hunt

After-proposal hunt (stance 0, dispatched in phase 1) is recorded at
`docs/reports/2026-08-07-hunt-issue-284-closes-gate-record-evidence-and-fork-fallback.md`.
Its finding — the unguarded fork fallback lets a wrong-shaped internal PR
spoof an issue reference and reach phase2 via the role-blind
PR-review-Approve path — is addressed by the cross-repo guard in
`_autodetect_issue_phase` (item 5 above) and covered by
`t_autodetect_fails_closed_for_wrong_shaped_internal_branch_despite_resolvable_ref`.

Before-landing hunt: not separately dispatched. The write set stayed
exactly within the frozen set (`gates/ci.py`,
`gates/test_closes_gate_ci.py`, `docs/issue-284/decisions/`) with no new
surface beyond what the after-proposal hunt already probed, and the live
six-PR run above is a stronger before-landing check for this specific
fix than a synthetic probe would have been.

## Open findings

No open findings require resolution; none outstanding.
