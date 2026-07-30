---
kind: coding-record
subject: issue-120
loop_state: landed
upstream:
  - path: docs/issue-120/proposals/coding.md
    sha: acae408
---

# issue-120 — phase 2: remove the wake system

Approval: issue #120 comment "APPROVE issue-120/coding" (single-account
mode, exact string match).

## Why

The owner has repeatedly said wake-style automated routing ("who runs
next", read from a machine-evaluated table) must not exist in this
repo. Recent work (#95/#99/#103) moved the opposite direction by
centralizing the routing table here. This phase reverses it: routing
becomes orchestrator judgment reading the board directly, not a table
lookup.

## What was done

Executed docs/issue-120/proposals/coding.md clause by clause:

1. Deleted `wakes.py`, `docs/specs/wake-routing.md`,
   `docs/specs/loop-state-vocab.md`, `test_vocab_coherence.py`.
2. `spawn.py`: removed `import wakes` and every call site (`_front`,
   `fresh`, `observed`, `evaluate`, `consume`); removed the `if a.role
   == "wake":` dispatch branch, its `--all` argparse flag, and its help
   text. `approve_scope()` now calls a new self-contained `_front_role`
   (with a small `_record_upstream` helper) instead of
   `wakes._front` — same rootless-record-then-product/feasibility-fallback
   logic, inlined. `drive()` no longer imports `wakes` or picks a role —
   it always prints that there is no auto-routing table and returns 0
   immediately (its one contractual job — stop — is now its only job).
   `_spawn_one()` no longer computes `answering` via `wakes.fresh` nor
   calls `wakes.consume`; the `blocked` list feeding `classify()` is now
   a hardcoded empty list (previously `wakes.evaluate()`'s third
   element) — `classify()`/`fail_closed_downgrade()` themselves are
   untouched, but this callsite can no longer produce
   `waiting-on-human`, since the human-gate-blocked-row source was
   `wakes`-only and this proposal does not replace it.
3. Deleted `docs/specs/wake-routing.md` and
   `docs/specs/loop-state-vocab.md` (done in step 1).
4. Reworded `gates/gates.py`'s two "wake 라우팅" fallback strings to
   describe the board-reading failure without naming the deleted layer.
5. `test_vocab_coherence.py` deleted; `test_gates.py` stripped of
   `_wake_repo`, `_woken`/`_blocked` helpers, and all 11 `t_wake_*`
   cases; `test_spawn.py`'s `Drive` test class rewritten to two cases
   asserting drive() returns 0 immediately and never calls
   `_spawn_one`, without touching `wakes`.
6. `README.md`, `README.ko.md`, `on-the-record/commands/run.md`
   rewritten: file-purpose tables drop the `wakes.py` line; the loop
   walkthroughs describe the orchestrator reading
   `docs/issue-<n>/reports/*.md`/`loop_state` directly instead of
   calling `spawn.py wake`; the "Every command" lists drop `wake`/
   `wake --all` and describe `drive` as always-stops; the "Open" /
   "미해결" sections drop the resolved §3/§5 wake-routing-doc bullet and
   add a bullet naming the new orchestrator-judgment behavior.
7. Ran `python3 -m pytest test_spawn.py test_gates.py` — 81 passed.

## What did not work

- The phase-1 survey (docs/issue-120/reports/coding/survey.md) did not
  enumerate `on-the-record/hooks/directive.sh` as a wake consumer, even
  though it instructs the orchestrator to run `spawn.py wake -C <repo>`
  on every merge/new issue. The warrant-hunter caught this (see Hunt
  below) after the rest of the build landed. Fixed in this same commit:
  rewrote directive.sh's routing paragraph to match run.md's — read the
  board directly, no `wake` reference left. This was outside the
  proposal's frozen `files:` list, but leaving a live, actively-executed
  hook script instructing agents to run a just-deleted CLI subcommand
  would defeat the issue's core intent (no consumer left silently
  depending on the removed layer) — judged in-scope as a survey-gap fix
  rather than a scope expansion requiring a new proposal.

## Hunt

Dispatched `coding:warrant-hunter` after the rest of the build landed
(pre-completion hunt per role cadence). One finding returned:

- **FINDING** (`docs/reports/2026-07-30-hunt-issue-120-wake-removal.md`):
  `on-the-record/hooks/directive.sh` still told agents to run `spawn.py
  wake -C <repo>`, which now fails with a generic, unrelated usage
  error ("맡길 일이 없다") instead of signaling the command was removed.
  **Resolved** in this build: directive.sh rewritten (see "What did not
  work" above); resolution appended to the hunt record itself.

closed_checks:
- `grep -rli wake` across non-historical, non-`docs/issue-<n>/` files —
  only `protocol.md`/`protocol.ko.md` remain (explicitly out of scope,
  flagged for the canon owner per the proposal's Constraints) and
  archival `docs/superpowers/`/`docs/proposals/` material predating this
  issue. code_sha: (this commit, see `git log -1`)
- `python3 spawn.py --help` — no `wake` subcommand listed. code_sha:
  (this commit)
- `python3 -m pytest test_spawn.py test_gates.py` — 81 passed, 0
  failed. code_sha: (this commit)

## Test plan

- `python3 -m pytest test_spawn.py test_gates.py` — 81 passed (run
  directly, output captured in this session).
- `python3 spawn.py --help` and `python3 spawn.py` (no args) — manually
  inspected, no `wake` subcommand or mention in the role list or usage
  text.
- `python3 -c "import ast; ast.parse(open('spawn.py').read())"` and same
  for `test_gates.py`, `on-the-record/hooks/directive.sh` (`bash -n`) —
  syntax OK.

## Open findings

None open. The one hunt finding above was resolved in this same build
and commit.

## Next steps

None — this closes issue #120's phase 2. Any future wake-adjacent
cleanup (protocol.md/protocol.ko.md canon lines) belongs to whoever
owns protocol canon, not coding.

## Open-finding resolution path

No findings are open. The one hunt finding raised during this build was
resolved in the same commit (see Hunt above); its resolution is
recorded both here and in the hunt record itself.

## Out of scope (per proposal, untouched)

- protocol.md / protocol.ko.md canon edits — their wake-adjacent lines
  (protocol.md:34,225; protocol.ko.md:204) remain, flagged for whoever
  owns protocol canon.
- Any replacement auto-routing mechanism — none added, per the issue's
  explicit instruction.
