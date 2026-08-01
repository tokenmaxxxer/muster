---
code_under_review: spawn.py (spawn_cmd()), test_spawn.py
loop_state: landed
---

# Phase 2 — CLAUDE_PLUGIN_ROOT_CORE injection (issue #182)

## What was done
- `spawn_cmd()` (spawn.py) now picks the `core_plugins` entry whose
  `Path(p).name == "core"` and sets `env["CLAUDE_PLUGIN_ROOT_CORE"]` to
  that path string — the same value already handed to `--plugin-dir`, so
  the "injected path == actually loaded core plugin path" invariant holds
  by construction, per the approved proposal's Rationale (alternative 2).
- If no `core` entry is present in `core_plugins` (missing/deficient core
  checkout), the variable is not injected and a warning is printed to
  stderr instead of silently falling through to the unresolvable relative
  fallback.
- `spawn_cmd()`'s signature and its no-second-`core_root()`-call
  constraint are both unchanged — no new network clone path added.

## Why (upstream basis)
Approved phase-1 proposal (`docs/issue-182/proposals/proposal.md`),
approved via `APPROVE issue-182/implementation` issue comment
(single-account mode, role-handoff contract v3 s19). Root cause per the
issue and phase-1 survey: `grep -rn CLAUDE_PLUGIN_ROOT spawn.py` returned
zero hits pre-fix — gates fell to a relative fallback that resolves inside
the rulebook clone rather than the real deploy path, fail-opening when
combined with unguarded `source`.

## Doctor probe extension — design draft (per proposal, review-only scope)
Issue requirement #2 asked for review, not implementation; the proposal's
Out of scope section excludes actually building this probe from this
delivery. Design draft, satisfying the review requirement:

- **Target gate script**: `board-gate.sh` (core) — smallest gate with a
  well-known deny condition (no board declared for the target repo),
  already exercised by the doctor probe plugin's hook-firing check.
- **Deny-inducing condition**: point the probe's throwaway workdir at a
  repo with no `docs/specs/approvers.md`, so `board-gate.sh` takes its
  documented deny branch instead of the pass-through branch — this
  distinguishes "gate script loaded and ran" from "gate script sourced
  gate-lib.sh but hit an unrelated early return."
- **Failure mode to add**: exit 2 fires but the *reason* logged is
  "gate-lib.sh not found" rather than the intended deny — that would mean
  `CLAUDE_PLUGIN_ROOT_CORE` still isn't resolving even though the process
  exits nonzero, and doctor-ok must not be written in that case.
- **doctor-ok recording condition**: this probe's outcome becomes a second
  required condition alongside the existing UserPromptSubmit/PreToolUse
  firing check — `runs/doctor-ok` is written only if both probes pass.

## What did not work
None.

## Open findings
None. All three issue requirements are met at the scope the proposal
committed to: (1) injection implemented and tested, (2) doctor probe
extension reviewed and its design recorded above, (3) regression tests
added.

## Verification
`python3 -m pytest test_spawn.py -x -q` — 127 passed (includes the 2 new
regression tests: `test_claude_plugin_root_core_matches_attached_core_dir`,
`test_claude_plugin_root_core_unset_without_core_plugin`).

## Doc placement (completed)
- [x] Phase 1 survey: `docs/issue-182/reports/implementation/survey.md`
  (pre-existing, from prior session)
- [x] Phase 1 scout brief: `docs/issue-182/reports/implementation/scout-brief.md`
  (pre-existing, from prior session)
- [x] Phase 1 proposal: `docs/issue-182/proposals/proposal.md`
  (pre-existing, from prior session)
- [x] Phase 2 record: `docs/issue-182/reports/implementation.md` (this file)
- [x] Code: `spawn.py` (spawn_cmd())
- [x] Tests: `test_spawn.py`
