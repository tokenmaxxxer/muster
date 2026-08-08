# defect-verification — issue #497 (side-effect round, phase 2)

kind: defect-verification-record
loop_state: phase-2-complete
Subject: issue-497
upstream: docs/proposals/2026-08-08-side-effect-round-verification.md

## What was done

All six attempts named in the approved proposal
(`docs/proposals/2026-08-08-side-effect-round-verification.md`) were
executed against `code_under_review:` `5df67a4` (tip of `origin/main` at
proposal time; this branch is built on top of it). One reproduced, five
did not.

## Why

Issue #497 asks for adversarial verification that today's ~25 merges do
not interact badly as a set — an interaction check no single PR's own
review could have run, since each PR was reviewed in isolation.

## Attempt outcomes

| # | Area | Source (verbatim, from issue #497) | Outcome |
|---|------|--------------------------------------|---------|
| 1 | hook-interaction | "multiple PreToolUse hooks (preflights, claim guards, contract-guard) firing on the same tool call — ordering, double-deny, one hook's output confusing another" — applied to the Bash matcher chain (`contract-guard.sh` → `pr-preflight.sh` → `spec-index-preflight.sh`) | not-reproduced |
| 2 | hook-interaction | same source, applied to the Write/Edit matcher pair (`deliverable-guard.sh` → `record-claim-guard.sh`) | not-reproduced |
| 3 | hook-interaction | same source, applied to the Stop chain (`stop-gate.sh` → `role-test-claim-guard.sh` → `decision-queue-stopgate.sh` → `report-framing-check.sh`) | not-reproduced |
| 4 | consumer-install | "fresh clone as a consumer project, run a minimal session lifecycle (spawn → record write → commit → pr-create shapes) and confirm each new hook fires or stays silent correctly" | not-reproduced |
| 5 | retired-actions | "nothing still references workflow checks" | **reproduced** |
| 6 | supervision | "auto-arm + reconcile + watchdog on the same tick — no duplicate respawns, no event storms" | not-reproduced |

### Attempt 1 — PreToolUse Bash chain, same call (not-reproduced)

Claude Code runs all hooks registered for a matcher in parallel for a
single tool call; results merge by most-restrictive-wins (deny > defer >
ask > allow) rather than a sequential pipe where one hook's stdout feeds
the next. `contract-guard.sh:52`, `pr-preflight.sh:48`,
`spec-index-preflight.sh:48` each independently re-parse the same
`CG_PAYLOAD` env var and gate on disjoint command substrings (`gh pr
merge`, `gh pr create|edit`, `git commit` respectively) — none reads or
depends on another's output. A compound command touching two of them
triggers two independent, correct denials for two different facts, not a
double-deny of the same fact.

### Attempt 2 — PreToolUse Write/Edit chain, same call (not-reproduced)

`hooks.json` wires `deliverable-guard.sh` and `record-claim-guard.sh` as
two separate matcher entries on the same `Write|Edit|MultiEdit` pattern,
not a literal pipeline. `deliverable-guard.sh:23` only fires when
`CLAUDE_ROLE` is unset (orchestrator session); `record-claim-guard.sh` is
unconditional but scoped to `docs/issue-*/reports/`. Where both can fire
(orchestrator writing a report), each denies independently for its own
distinct, correct reason — role-gating vs. claim-shape — not a
misfire caused by the pair being chained.

Incidental observation made while exercising this attempt, noted here for
completeness but **not** filed as a #497 finding (out of scope per the
proposal — not one of the four named hunt areas, and not new from today's
interaction): `record-claim-guard.sh`'s `unverifiable:` regex
(`\s*:\s*(.*)$`) greedily captures an empty reason across the following
line, so `unverifiable: ` with no reason on its own line can swallow the
next line and suppress the #310 violation report. This is a same-script,
pre-existing defect unrelated to hook-chain interaction; if pursued, it
belongs to a future issue against `record-claim-guard.sh` itself, not
#497.

### Attempt 3 — Stop hook chain, same event (not-reproduced)

`stop-gate.sh:25` fires only when `CLAUDE_ROLE` is unset;
`role-test-claim-guard.sh:32` fires only when it **is** set — mutually
exclusive, never both live for one event. `decision-queue-stopgate.sh:21`
and `report-framing-check.sh:20` are both orchestrator-only but keyed off
independent triggers (aged `decision_queue` items vs. report-shaped
message text) with no shared state between them. Simultaneous blocks
merge to "block" under the same most-restrictive-wins model as attempt
1 — expected behavior, not a misreport.

### Attempt 4 — Consumer-install fresh-clone minimal lifecycle (not-reproduced)

`record-claim-guard.sh`, `pr-preflight.sh`, and `spec-index-preflight.sh`
resolve paths relative to `cwd`/discovered `.git` root, contain no
hardcoded absolute paths, and fail open (exit 0) when
`docs/specs/approvers.md` or `docs/specs/reconciled-index.md` are absent
— verified live by running `record-claim-guard.sh` against a synthetic
payload from a fresh `git init` tmpdir outside this repo; it produced the
expected findings with no path errors.

`decision-queue-stopgate.sh:24-43`'s `_checkout_resolve` falls through to
`git clone -q https://github.com/tokenmaxxxer/on-the-record.git
$HOME/.claude/tokenmaxxxer/on-the-record` (line 41) when no local
checkout is discoverable. This looked at first like a consumer-install
portability landmine (a silent network write to `$HOME` from inside a
Stop hook), but it is not new or specific to today's merges: the
identical fallback pattern already exists, deliberately, in
`self-update.sh:31` and `directive.sh:37/46`
(`docs/reports/2026-08-08-hunt-decision-queue-stophook-and-respawn-branch-fix.md:28-32`
documents `decision-queue-stopgate.sh` being brought into line with
`directive.sh`'s existing behavior). It is consistent, pre-existing,
repo-wide plugin-resolution design, not an interaction defect produced by
today's merge set — so this attempt is not-reproduced under #497's scope.

### Attempt 5 — Retired-Actions edge (**reproduced**)

`gates/gates.py:1125`'s `.github/workflows/` reference is inert (a
docstring describing the historical retirement, no live logic).

`gates/acceptance_gate.py`'s `_ARTIFACT_REF` regex
(`gates/acceptance_gate.py:20-24`) still matches a backtick-quoted
`` `.github/workflows/...` `` path as a valid executable-artifact
reference satisfying issue-310's Acceptance-gate requirement — even
though `.github/workflows/` is confirmed absent from the repo per
`gates/test_boundary_workflow_migration.py`. An issue author can cite a
path in a directory that no longer exists, and will never execute
anything, and the gate accepts it as if it were live.

Live repro: `test/test_side_effect_round.py::test_acceptance_gate_accepts_phantom_github_workflows_reference`
— asserts `gates.acceptance_gate.check_issue_body()` returns zero
violations for an Acceptance section that cites only a phantom
`` `.github/workflows/ci.yml` `` path. Confirmed passing (i.e. the bug is
present) via `python3 -m pytest -q test/test_side_effect_round.py`.

**Finding**, addressed_to: coding —
`gates/acceptance_gate.py`'s `_ARTIFACT_REF` regex (line 20-24) should
stop accepting `.github/workflows/` paths as valid artifact references
now that the directory is retired (issue #460), or should verify the
referenced path actually exists in the repo tree before accepting it.
Evidence pointer: `test/test_side_effect_round.py::test_acceptance_gate_accepts_phantom_github_workflows_reference`
(reproduces live); `gates/acceptance_gate.py:20-24` (the stale regex);
`gates/test_boundary_workflow_migration.py` (confirms `.github/workflows/`
is retired/absent).
Severity: **Medium → advisory** (Medium/Low/Unknown band maps to
advisory per the deterministic lookup; this degrades gate precision —
an issue can claim a dead artifact and still pass #310's check — but
does not itself block landing of anything, corrupt state, or cause a
crash).

### Attempt 6 — Supervision interplay, same tick (not-reproduced)

`spawn.py`'s `roster_watchdog()` (line 1886-1907) runs `reconcile()`
(observe/print-only in this path — line 1890-1894, it does not call
`_respawn_or_cap` itself) and the watchdog crashed-check
(`_auto_respawn_check` → `_respawn_or_cap`, line 1897-1899/2262-2297) in
the same loop iteration for the same roster entry, per issue #492's ADR
(comment at `spawn.py:1887-1888`: "same tick, riding the existing scan").
`_respawn_or_cap` (line 2199-2259) has real cross-trigger idempotency: an
atomic `O_CREAT|O_EXCL` claim file keyed by `session_start_ts`
(2240-2245), an events-log `already_claimed` check (2228-2234), and a
shared attempt-cap counter keyed by roster `key` that both the
watchdog-observed-crashed path and `_self_trigger_respawn` (2303+) draw
from — deliberately so both triggers "spend the same budget" (docstring
2207-2209). Auto-arm (issue #488) launches the watcher once at spawn
time, not repeatedly per tick; dead-watcher detection folds into
watchdog signal 5 (1806-1808) rather than racing a separate mechanism.
No duplicate-respawn or event-storm path found — the dedup is real and
was purpose-built for this exact same-tick scenario.

## Open findings

One: attempt 5, `gates/acceptance_gate.py:20-24`, advisory, addressed_to
coding (see above). No blocking findings — nothing here gates landing of
#497 itself.

## Basis

Upstream: docs/proposals/2026-08-08-side-effect-round-verification.md
(approved via `APPROVE issue-497/defect-verification` comment on issue
#497, single-account mode, JiwonJung94 is both author and approver).

## Resolution path

Advisory finding above is handed to coding for `gates/acceptance_gate.py`;
no action required from this role. This record's own loop_state
(phase-2-complete) is terminal for the defect-verification kind — closing
#497 itself is not blocked on the advisory finding's resolution, per the
deterministic band lookup (Medium → advisory, never blocking regardless
of a clean upstream record).

## Full suite

`python3 -m pytest -q` — run at commit time for this record; see below.
