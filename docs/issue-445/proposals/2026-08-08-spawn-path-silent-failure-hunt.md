---
status: landed
files:
  - docs/issue-445/reports/defect-verification.md
  - test/test_silent_failure_repros.py
---

## Intent

Issue #445 asks for an adversarial hunt for silent failures and spawn-path
defects across `spawn.py`, `gates/`, `on-the-record/hooks/`, `scripts/` —
error paths that swallow failures, spawn-time defects (doctor cost/
repetition, stale workspace reuse, branch-name inheritance, watch
early-return, log overwrite), and anything that renders as success while
the work didn't happen.

## Constraints

- Role-handoff contract v3 s19 two-phase gate: this proposal, plus the
  current-state survey, is the entire phase-1 output. No reproduction
  attempts run and no finding is written until a listed approver Approves
  the PR.
- Findings must be reproduced (concrete repro), not inferred from reading
  code — an outcome of `reproduced` with no evidence pointer is refused.
- Severity assigned by the deterministic band lookup (Critical/High →
  blocking, Medium/Low/Unknown → advisory), never freehand.

## Attempt list (phase 2)

Each item names its source verbatim; all are self-devised paths against
`code_under_review: 0fa8a2c621e536bcfbd27876ae53b8e122f756ba` (no prior
qa/review record exists for this issue to cite).

1. **Self-devised — credential-exclude write failure is swallowed.**
   `issue_workspace()` spawn.py:2964-2983: writing `.git/info/exclude`
   entries (the guard against #289 H1's credential-leak-via-`git add -A`)
   is wrapped in `except OSError: pass`. Attempt: force that write to fail
   (read-only `.git/info/`, or a `.git` that is a file not a dir at that
   path) and confirm `issue_workspace()` still returns a workspace with no
   surfaced warning that the exclude guard didn't take.

2. **Self-devised — unbounded `--follow` wait on absent roster entry.**
   spawn.py:2199-2235: when `roster_entry` is `None`, the follow loop has
   no timeout, no retry cap, and no diagnostic — it silently re-polls
   forever. Attempt: register a workspace-index entry with no matching
   roster entry (simulating a crash before registration) and confirm
   `spawn.py watch --follow` blocks indefinitely with no error, no stall
   message, no exit.

3. **Self-devised — doctor re-probe under version drift is a live paid
   session with no confirmation.** spawn.py:2405-2431: `require_doctor()`
   re-runs `doctor()` (a real `claude -p` session) the moment
   `runs/doctor-ok`'s stored version stops matching `claude --version`,
   inside what looks to the caller like a routine spawn. Attempt: flip
   the recorded doctor-ok version and drive a normal (non-`doctor`) spawn
   call to confirm it silently launches a billed session with no
   pre-charge notice distinguishable from the routine spawn it was
   invoked as.

4. **Self-devised — `issue-bundling-gate` may be advisory-only.**
   `gates/issue_bundling.py` + its workflow posted a fail-closed comment
   on #445 itself, yet the issue stayed open/assignable and this role was
   invoked against it. Attempt: trace whether the gate's workflow actually
   fails a check run / blocks a PR merge, or only ever posts a comment —
   i.e. whether "게이트 차단" renders as enforcement or is silently
   decorative.

## Out of scope

- `gates/ci.py`, `gates/closure_sweep.py`, and the other gate modules not
  named above — issue #445 scopes to spawn.py's own paths plus
  hooks/scripts; a full gates/ audit is a separate width.
- Any fix. This role reproduces and files; coding fixes.
- Filing follow-up issues for anything not reproduced.

## How you'll know it worked

Each of the four attempts above has a recorded outcome
(`reproduced`/`not-reproduced`/`blocked: needs-repro-access`) in
`docs/issue-445/reports/defect-verification.md`, and every `reproduced`
outcome carries an evidence pointer and a severity band. Reproduced items
are filed as follow-up issues per the splitting rules.

## What did not work

- First draft of `test_attempt_1_exclude_write_swallowed_no_warning`'s
  fixture called `_git("clone", ..., str(src))` without the `cwd=` kwarg
  the local `_git()` helper requires — `TypeError` at fixture setup, fixed
  by passing `cwd=tmp_path`.
- First draft of attempt 3's repro called `require_doctor(version="2.0.0")`
  (an explicit version) expecting it to trigger the live auto-probe; it
  instead hit the explicit-version branch, which halts and tells the
  caller to run `spawn.py doctor` manually without ever calling `doctor()`
  — the auto-probe only fires on `require_doctor(version=None)`. Fixed by
  driving the `None` path and mocking `_claude_version()` instead.
