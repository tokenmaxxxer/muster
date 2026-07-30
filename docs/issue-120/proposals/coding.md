# Build proposal — issue #120

files:
- wakes.py (delete)
- docs/specs/wake-routing.md (delete)
- docs/specs/loop-state-vocab.md (delete — its sole stated purpose was documenting `wakes.py`'s consumed vocabulary)
- spawn.py (remove `wakes` import and all call sites; remove the `wake` subcommand; re-point drive mode and the first-build gate to not depend on wake routing)
- gates/gates.py (reword the two fallback-message strings that mention "wake 라우팅"; no behavior change)
- test_gates.py (remove all wake-routing tests and the `_wake_repo` fixture)
- test_spawn.py (rewrite the drive-mode tests at L788-840 so they exercise "drive mode stops when nothing to spawn" without monkeypatching `wakes`)
- test_vocab_coherence.py (delete — its target, `wakes.py`, is gone)
- README.md, README.ko.md (rewrite the `spawn.py wake` / WAKES-ON sections to describe reading the board directly; drop the command)
- on-the-record/commands/run.md (rewrite the "누구를 깨울지" step to describe orchestrator judgment over the board, not `spawn.py wake`)

## Request (paraphrased intent)

The owner has repeatedly said wake-style automated routing (a machine table that decides "who runs next") must not exist in this repo — recent work (#95/#99/#103) moved the opposite direction by centralizing routing tables here. Issue #120 reverses that: delete `wakes.py`, delete the `wake` subcommand, drop `docs/specs/wake-routing.md` from canon. What survives is reading the board (records, `loop_state`) — the judgment about who runs next belongs to the orchestrating conversation, not to code evaluating a table.

## Constraints

- Human-only gates (approval, scope, round-end) are unaffected — they were never wake-automated.
- Board-reading itself (loop_state, verdict fields, records under docs/issue-<n>/) stays; only the "what auto-wakes whom" layer goes.
- protocol.md / protocol.ko.md are core's canon, not coding's docs/ area — this proposal does not edit them. Their wake-adjacent lines (protocol.md:34,225; protocol.ko.md:204) are flagged for whoever owns protocol canon to address separately; coding's write set stays inside spawn.py, gates.py, docs/specs/*, README*.md, on-the-record/commands/run.md, and the tests.
- docs/handbooks/on-the-record.md had no direct wake references at survey time; re-checked during build, edited only if a reference surfaces.

## What will be done

1. Delete `wakes.py`.
2. In `spawn.py`: remove `import wakes` and every call site (`_front`, `fresh`, `observed`, `evaluate`, `consume`, `report`); remove the `if a.role == "wake":` dispatch branch and its argparse registration/help text. Drive mode (currently importing `wakes` to decide what to spawn next, ~L2030-2210) is rewired to its contract-mandated job only — stop when there's nothing left to do — without consulting an auto-routing table; it no longer picks a role automatically. The first-build check (`gates/spawn.py` around L829-843, currently `wakes._front`) is either inlined as a direct "has any role output ever existed for this subject" check or dropped if the underlying gate concept was wake-specific — resolved during build per what the code actually needs, not re-litigated here.
3. Delete `docs/specs/wake-routing.md` and `docs/specs/loop-state-vocab.md` (no withdrawal convention exists elsewhere in docs/specs — outright delete matches how this repo has removed dead specs before).
4. Reword the two comment strings in `gates/gates.py` that mention "wake 라우팅" in fallback messages, to describe the board-reading fallback without naming the deleted layer.
5. Remove wake-routing tests: delete `test_vocab_coherence.py` outright; strip `test_gates.py` of the `_wake_repo` fixture and all `t_wake_*` cases; rewrite `test_spawn.py`'s drive-mode section to assert "stops when nothing to spawn" and "spawns when there's something to do" without touching `wakes`.
6. Rewrite `README.md`/`README.ko.md`'s `spawn.py wake` / WAKES-ON sections and `on-the-record/commands/run.md`'s "who to wake" step to describe the orchestrator reading the board directly (records, loop_state) and deciding by judgment — no CLI subcommand replaces it.
7. Run the full test suite (`test_spawn.py`, `test_gates.py`, whatever else references spawn/gates) after the removal and fix what breaks before calling it done.

## Out of scope

- protocol.md / protocol.ko.md canon edits (owner other than coding).
- Any new automated routing mechanism to replace wake — the issue is explicit that none should exist.
- Re-litigating human-only gates (approval/scope/round-end) — unaffected by this change.

## How it'll be known to work

- `wakes.py` and `docs/specs/wake-routing.md` no longer exist in the tree; `grep -ri wake` across non-historical files (excluding docs/issue-<n>/ proposal and report history, which record what happened and are left as-is) returns nothing live.
- `python3 spawn.py --help` (or equivalent) shows no `wake` subcommand.
- `test_spawn.py` and `test_gates.py` pass after edits; `test_vocab_coherence.py` is gone.
- Drive mode still stops correctly when there is nothing to spawn (its one contractual job), verified by the rewritten test.
