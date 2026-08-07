---
status: proposed
files:
  - gates/ci.py
  - gates/test_closes_gate_ci.py
  - docs/issue-284/decisions/record-evidence-as-closing-intent.md
---

files:
- gates/ci.py
- gates/test_closes_gate_ci.py
- docs/issue-284/decisions/record-evidence-as-closing-intent.md

## Request

closes-gate's phase-2 Closes requirement is judged purely off the mutable
PR body. Six approved deliveries (#337, #340, #343, #350, #352, #353) opened
correctly as phase-1 (no Closes), got approved, delivered phase-2 code on
the same PR, and are now red because nobody rewrote the body after
approval flipped the requirement. Also fix the separate fork-PR half of
#284: a PR whose branch isn't `issue-<n>/<role>` can never resolve its
issue number today, so it fails closed even with a legitimate `#N`
reference in the body.

## Constraints

- Do not touch `gates/pr_reference.py::check_body`/`check` — owned by
  #228; the established pattern (`ci.py::_phase1_surface_mismatch`) is to
  supplement it from `ci.py`, never edit it.
- Do not touch `gates/ci.py::_phase_from_approval` or
  `gates/flows.py::_pr_approved` — `_phase_from_approval` is #312's write
  set (PR #314, open, phase2). Confirmed by reading `_pr_approved`
  (flows.py:130): the two-account PR-review path never reads `role`, so
  calling it with `role=None` for fork PRs is already safe without
  changing its signature or behavior — no coordination needed on that call
  site's internals, only on which PR owns which function (this proposal
  touches none of #312's functions).
- Acceptance (#284 issue body) requires a phase-2 delivery to still need an
  explicit, checked closing intent — this proposal must not make the
  Closes requirement a no-op.
- Per #310/#330: name an executable artifact and state what the change
  reaches. Executable artifact: `gates/ci.py --pr <n> --issue <n> --phase
  phase2` (and its `--autodetect --closes-only` form, the required CI
  entrypoint). Reach: this changes `ci.py::check()`'s phase2 branch and
  `_autodetect_issue_phase`'s branch-parse fallback — both used only by
  `.github/workflows/plan-aware-closes-gate.yml`'s `--closes-only` call, so
  the reach is exactly that one required status check, not `gates/gates.py`
  or the router.

## Rationale

**F1 — considered "keep requiring a literal Closes in the body, just
improve the refusal message" (the issue's stated fallback option) and
rejected it.** It's the smaller diff, but it does not unblock the six live
PRs without a role session editing each one — the actual cost the issue is
complaining about ("고치려면 각각 역할 세션을 다시 띄워야 한다"). Chosen
instead: accept the phase-2 record file's mere existence (with a non-empty
`loop_state` field) as alternate evidence of closing intent, checked
alongside the literal Closes keyword. This is derived from "an artifact the
session necessarily produces" (the issue's own fix direction) rather than a
body edit, and `record-shape-directive` already mandates every phase-2
record carry `loop_state:` frontmatter — so this is not a new obligation on
sessions, it recognizes one that already exists. Rejected using the
record's specific `loop_state` *value* (e.g. requiring exactly
`"landed"`): surveyed and found `roles/implementation.json`'s declared enum
(`scope-proposed/scope-approved/in-progress/landed`) does not match the
real value seen on #337's record (`phase-2-complete`), and that mismatch
is invisible to CI today because the required check runs
`--closes-only` and skips `record_enums`. Gating on a specific string would
either miss #337-shaped records or require also fixing the enum drift,
which is out of this issue's scope. Presence-of-field is the check that is
actually true today.

**F2 — considered leaving fork PRs to the existing admin-bypass workaround**
(what #278/#279 actually did) and rejected it: the issue's acceptance
criterion is explicit that no merge of an external contribution should
require lifting `enforce_admins`. Chosen: when the branch doesn't match
`issue-<n>/<role>`, fall back to extracting the issue number from the PR
body's plain `#N` reference (reusing `pr_reference._PLAIN_REF`, the same
pattern phase1 already requires from every PR body) instead of failing
closed outright. Role stays unresolved (`None`) in that path — surveyed
`flows._pr_approved` and confirmed the two-account review-Approve path
never reads `role`, so fork PRs still classify correctly via that path;
they simply can't use the single-account `APPROVE issue-<n>/<role>`
comment path (which was never reachable for external contributors anyway,
since approvers.md logins commenting `APPROVE issue-N/role` presumes an
internal role session exists). The after-proposal warrant hunt (stance 0,
`docs/reports/2026-08-07-hunt-issue-284-closes-gate-record-evidence-and-fork-fallback.md`)
found the unguarded version of this fallback lets any internal PR on a
wrong-shaped branch spoof an issue reference and reach phase2 via the
role-blind PR-review-Approve path — addressed by scoping the fallback to
confirmed cross-repo (fork) PRs only, see step 3 below.

## What will be done

1. `gates/ci.py`: add `_phase2_record_evidence(repo, branch, issue) -> bool`
   — parses `role` from `branch` via the existing
   `_issue_and_role_from_branch`, reads
   `repo / f"docs/issue-{issue}/reports/{role}.md"` from the local
   checkout (already present in a CI checkout, same access pattern
   `gates.record_enums` uses), and returns whether
   `gates.record_frontmatter(text)` has a non-empty `loop_state`.
2. `gates/ci.py::check()`: in the phase2 branch, after collecting
   `pr_reference.check(...)`'s result, if the only new bad entries are the
   "no Closes" message and `_phase2_record_evidence(...)` is true, drop
   that entry (record evidence substitutes for the body edit). Otherwise
   leave it — and rewrite the message to also name the record-evidence
   path as an alternative so the refusal is actionable per the issue's
   fallback direction.
3. `gates/ci.py::_autodetect_issue_phase`: when
   `_issue_and_role_from_branch(branch)` returns `None`, fall back to the
   body-`#N` extraction (below) **only if the PR is actually cross-repo**
   (`gh pr view --json isCrossRepository` true) — i.e. a real fork PR, not
   an internal PR whose branch merely doesn't follow the naming
   convention. On that condition, use `pr_reference._PLAIN_REF` against the
   PR body before failing closed; on a match, proceed with `role=None`.
   Still fail closed if neither the branch resolves, nor (for a confirmed
   fork) the body resolves an issue number (see Rationale above for why
   the cross-repo guard is required).
4. `gates/test_closes_gate_ci.py`: add coverage for (a) a phase2 PR with no
   Closes in body but a record file carrying `loop_state`, passing; (b) a
   phase2 PR with neither, still blocked, message names both options; (c)
   a confirmed-cross-repo branch with a resolvable `#N` body reference,
   issue resolved and role `None`; (d) a fork-shaped branch with no
   resolvable reference anywhere, still fail-closed; (e) a wrong-shaped
   but same-repo (non-cross-repo) branch with a resolvable `#N` in the
   body — still fail-closed, per the after-proposal hunt finding.
5. `docs/issue-284/decisions/record-evidence-as-closing-intent.md`: record
   the "existence, not value" choice on `loop_state` and why (the enum
   mismatch found in the survey), since it's a check-shape decision a
   future session could otherwise silently "fix" by tightening to a
   specific enum value and re-break #337-shaped records.

## Out of scope

- The `roles/implementation.json` `loop_state` enum drift itself (does not
  include `phase-2-complete`) — noted as a decision constraint, not fixed
  here.
- `_phase_from_approval`'s role-matching change — #312's write set.
- `pr_reference.py::check_body`/`check` — #228's write set; this proposal
  only supplements from `ci.py`, per the existing `_phase1_surface_mismatch`
  pattern.
- Retroactively fixing #337/#340/#343/#350/#352/#353 — those go green as a
  side effect of the merged gate once each PR's branch already has its
  own phase-2 record (all six should, per `record-shape-directive`); no
  PR body is edited by this session.
- F3 (plan-step ordering) — issue #284 itself lists this as "working as
  intended."

## How you'll know it worked

- `python3 gates/ci.py . --pr 337 --issue 330 --autodetect --closes-only`
  against the real, unmodified #337 (no body edit) reports `게이트 통과`
  once run from a checkout of `issue-330/implementation` that has its
  existing record file — same live-check method #312's PR #314 used.
- `gates/test_closes_gate_ci.py` new cases (4 above) pass; full file still
  passes (report exact N/N in the phase-2 record, plus full-suite numbers
  distinguishing pre-existing #360 pollution from anything this change
  touches).
- A synthetic fork-shaped branch (e.g. `patch-1`) with body `Fixes bug,
  see #330` and no record resolves to issue 330, role `None`, and is
  judged by the same phase logic as any other PR from there on — no
  `enforce_admins` bypass needed to test it.
