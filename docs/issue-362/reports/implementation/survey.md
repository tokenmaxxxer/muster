# Survey — issue-362

## What the rule actually requires

"A check must not put an artifact into a failing state for a reason its author
could not have addressed at authoring time." The instance (#284/#312) is
`closes-gate`: its verdict depends on GitHub approval-comment state, which the
system itself (the orchestrator posting `APPROVE`) can flip after the PR body
is frozen. #362 splits this into two asks: (1) give the rule a durable home so
future gate authors hit it before shipping a gate, not after a live incident;
(2) audit `gates/gates.py` / `gates/ci.py` for other checks with the same
shape — verdict depends on state outside the artifact being judged.

## Where the rule could live

- `gates/gates.py`'s module docstring already carries adjacent reasoning
  ("게이트가 죽는 흔한 경로" — how a gate dies by blocking what shouldn't be
  blocked). It is read by anyone editing a gate, so it is live documentation,
  not an archive.
- `docs/decisions/` holds cross-cutting rationale that outlives any one issue
  (e.g. `2026-07-29-permanently-closed-alternatives.md`). A gate-authoring
  principle fits this bucket better than an issue-scoped report — it is meant
  to be found by someone adding gate #12, not someone reading #362's history.
- Putting it only in the issue thread (as it is now) means it gets
  rediscovered per gate, which is exactly the failure #362 opens with.

Chosen shape (see proposal): a decision record in `docs/decisions/` states the
rule and its test, and `gates/gates.py`'s docstring gets one paragraph that
names the rule and points at the decision record — so the person editing the
file that actually breaks this rule sees it in place, without duplicating the
full reasoning inline.

## Audit of `gates/gates.py` / `gates/ci.py`

Method: for every gate function, ask whether its verdict for a *fixed* diff
can change between two CI runs with no change to the PR/commit itself.

| Gate | Reads | Verdict depends on | Shape |
|---|---|---|---|
| `_phase_from_approval` / closes-gate (`gates/ci.py`) | GitHub PR review/issue comments via `gh` | Approval state, mutable by the system's own orchestrator action | Confirmed instance — already the subject of #284/#312 (PR #364, open, not yet merged). Not duplicated here. |
| `record_enums` (`gates/gates.py:296`) | `roles/<role>.json`'s `record_fields` enum, read from `ON_THE_RECORD_ROOT` — the on-the-record **tool's own** checkout, not the PR's repo or commit | Whatever the tool's `roles/<role>.json` says *at CI-run time* | **New instance.** A board-repo record file that was compliant with the enum in force when authored can start failing after an unrelated tool update changes `roles/<role>.json`'s allowed values — with the record's own PR unchanged. Same three properties as closes-gate: unpreventable at authoring time, the state change is the system's own (a tool maintainer's edit, not the author's), and it re-fires as a required-check notification with no available fix on the flagged PR. |
| `deps` / `registry_status` (`gates/gates.py:264`) | Live PyPI/npm registry HTTP status for each newly added dependency | Whether the package name resolves right now | **Different shape, not an instance.** The check's *purpose* is "does this name exist" — a package that gets unpublished between authoring and CI genuinely changes what's true about the claim being checked, not an external fact orthogonal to the artifact. This is ordinary real-world state a naming check is supposed to track, not a system-caused reclassification. Documented here so the audit is visibly complete, not silently skipping a live-network gate. |
| `is_protected`, `writeset`, `role_scope`, `record_wellformed`, `record_no_tool_residue`, `record_fulfils_diff` | The PR's own diff/commit content, or static path tables in `gates/gates.py` | Nothing outside the artifact and the gate's own source (which changing IS a normal code change, reviewable like any other) | Not instances — verdict is a pure function of the artifact plus the gate's own versioned logic. |

## Acceptance shape

Per #310 this needs an executable artifact, and per #362's own acceptance
note, "could the author have satisfied this at authoring time" is a property
of a check's *design*, not of any single run — so a per-run assertion inside
`record_enums` itself (e.g. "refuse to tighten an enum") is the wrong shape:
it would require the gate to know the history of every `roles/*.json` edit,
which it does not have and should not be made to reconstruct.

The honest ceiling, matching what #362 itself proposes as the fallback: a
**verdict-stability test per audited gate**, pinning that a fixed artifact's
verdict does not flip when only the *external* input changes. This is
mechanical (no history reconstruction needed) and it is exactly the shape
that would have caught the closes-gate incident before it went live six
times: hold the PR fixed, vary the approval/config state, assert the verdict
line is the same.

Scope for this pass: one such test for `record_enums` (the newly confirmed
instance). closes-gate's own stability test belongs to #284/#312, already in
flight on PR #364 — writing a second one here would duplicate that work
rather than close a gap.

## Skip conditions

Scout-directive: not skipped — this issue is a design decision (where the
rule lives, which gates are instances) with no single obvious answer, so the
sweep applies. Given the audit is entirely internal (reading this repo's own
`gates/gates.py`/`gates/ci.py` against a rule stated in the issue itself,
with no external category of comparable products to benchmark against — a
gate-authoring principle is not a product with market exemplars), the
relevant "field" is the codebase and its own prior decisions
(`docs/decisions/`, #284/#312/#147's shape), not an external web sweep.
Consulted: `docs/decisions/` directory listing, `gates/ci.py` and
`gates/gates.py` in full, issue #284's 2026-08-07 comment thread, issue #312.
