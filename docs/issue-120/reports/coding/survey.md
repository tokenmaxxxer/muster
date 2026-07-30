# Current-state survey — issue #120

Scope: remove the wake system (wakes.py, spawn.py's `wake` subcommand, docs/specs/wake-routing.md) and every place that quietly depends on it. Routing "who runs next" moves entirely to orchestrator judgment reading the board (docs/issue-<n>/, loop_state) directly.

Scout skip record: this is a removal mandated by an explicit, non-negotiable owner directive in the issue body — no design decision is open (what to remove and why is fully specified). Skip condition: "spec literally leaves no design decision open."

## Write set (files touching wake)

**Core removal:**
- `wakes.py` — delete entirely (the automated routing-table evaluator).
- `docs/specs/wake-routing.md` — remove from canon (delete or mark superseded/withdrawn per doc convention; check `docs/specs/` for a withdrawal pattern before deleting outright).

**spawn.py** — heaviest consumer. `wake` role/subcommand:
- L829, L842-843: imports `wakes`, calls `wakes._front()` for the first-build check.
- L1526, L1531, L1533: `wakes.fresh`, `wakes.observed` used in judgment-row reporting.
- L1550: `wakes.observed(cwd).get(row.key)`.
- L1740: `--all` flag help text references `wake`.
- L1812-1818: `if a.role == "wake":` dispatch — the `wake` subcommand itself, prints `wakes.report(...)`.
- L1842: help text "보드가 누구를 깨우는지: spawn.py wake".
- L2030, L2081, L2083: drive-mode loop imports `wakes`, consumes `wakes.fresh()` to decide what to spawn next.
- L2173: `wakes.evaluate(cwd)` for blocked-role check.
- L2208-2210: `wakes.consume(cwd, answering)` — must record wake-consumption for §6 semantics.

This is the core of the removal: spawn.py's **drive mode** currently decides what to spawn next by calling into `wakes`. Per the issue, that automated decision layer goes away; board-reading (loop_state, verdict) stays, but nothing auto-picks a role from it — that judgment moves to the orchestrating conversation. Drive mode's stop-only responsibility (test_spawn.py:788 "드라이버의 유일한 일은 멈추는 것") needs preserving without a `wakes` dependency.

**gates/gates.py** — L328, L333: only comment strings mentioning "wake 라우팅" in a fallback message when loop_state/verdict can't be read; not an import, likely safe to reword without behavior change.

**Tests:**
- `test_gates.py` — imports `wakes` directly (L18), builds a `_wake_repo` fixture, and asserts wake-evaluation behavior (hypothesis wakes feasibility, acknowledged rows go quiet, first-build gate, finding-wakes-role, answered rows don't refire, wake-routing.md matches wakes.py's rows, etc.). All of this tests the layer being deleted — must be removed, not adapted.
- `test_spawn.py` — monkeypatches `wakes.fresh`/`wakes.observed` to test drive mode's spawn-or-stop decision (L788-840). Needs rewriting so drive mode's tested behavior no longer routes through `wakes` at all.
- `test_vocab_coherence.py` — entire file's purpose is cross-checking `wakes.py`'s literal comparisons against `docs/specs/loop-state-vocab.md`. Its reason to exist disappears with `wakes.py`; delete.

**Docs referencing wake as consumer-facing behavior (not proposal/report history):**
- `docs/specs/loop-state-vocab.md` — L1, L4, L14, L17, and each vocab entry's "consumed at `wakes.py`..." line: the doc's stated purpose is entirely about what `wakes.py` consumes. Needs a rewrite or a decision on whether the vocab itself still has a canonical consumer worth documenting (board-reading orchestrator judgment, not exact-match code) — flag for the proposal's "what will be done" rather than deciding here.
- `README.md` L63, L280-324, L508-511 and `README.ko.md` L59, L255-299, L476 — the `spawn.py wake` command docs, WAKES-ON table description, and the §3/§5 resolution note. These describe the CLI surface being removed and must be rewritten to describe orchestrator-judgment routing instead.
- `protocol.md` L34, L225 and `protocol.ko.md` L204 — contract text: "Pick a role. Decide which role an event should wake" and the "WAKES-ON watcher" future-automation clause. These are canon protocol text (out of coding's write area normally — protocol.md/.ko.md are core's canon, not coding's docs/ bucket) — the proposal should flag this as needing a decision on ownership/scope rather than editing it directly, since it sits outside `docs/issue-<n>/` and outside coding's own output layout.
- `on-the-record/commands/run.md` L33-37 — orchestrate-directive-adjacent guidance telling a human/agent to run `spawn.py wake` to decide who's up next. In coding's write set (it's under `on-the-record/`, a command doc, not under docs/specs).
- `docs/handbooks/on-the-record.md` — has no direct wake references found by grep at survey time, but is the standing handbook bucket for this component; check again before finishing.

## Consumers enumerated (per issue's directive #4)

1. **spawn.py drive mode** (issue #95/#99 area) — automated next-role selection. Highest-risk consumer; must be re-pointed to "stop only" / no auto-routing.
2. **spawn.py `wake` subcommand / judgment-row reporting** — human-facing report of unanswered rows; the *reporting* (reading loop_state/verdict and rendering rows) may be worth keeping as a manual "board summary" command, but without the auto-consume/§6-suppression machinery tied to `wakes.py`'s internal state. Needs a decision: keep a slimmed manual summary, or remove the `wake` subcommand entirely and tell users to read the board files directly. The issue's directive #1 says routing is judgment, not a machine table — leans toward full removal of the subcommand, but the proposal should state this explicitly rather than assume it.
3. **gates.py first-build check** (`wakes._front`) — needs a non-`wakes` equivalent or removal of that specific gate behavior; check whether `_front`'s logic (has any role ever run for this subject) needs to be inlined into spawn.py directly.
4. **coherence test** (issue #103, `test_vocab_coherence.py`) — deleted wholesale.
5. **Rulebook references**: README.md/.ko.md, protocol.md/.ko.md, on-the-record/commands/run.md, docs/specs/loop-state-vocab.md, docs/specs/wake-routing.md itself — all named above.

## Open questions for the proposal (not decided here)

- Does `spawn.py wake` survive as a manual, non-auto-consuming "board summary" command, or is it deleted outright?
- Does `docs/specs/loop-state-vocab.md` get rewritten to describe a different consumer, or does it get withdrawn alongside wake-routing.md (the vocab's only stated purpose was serving `wakes.py`)?
- protocol.md/protocol.ko.md are core's canon, not coding's — the proposal should scope coding's edit to what's in coding's write area (spawn.py, gates.py, docs/specs/wake-routing.md, docs/specs/loop-state-vocab.md, README*.md, on-the-record/commands/run.md, tests) and flag protocol.md/.ko.md as needing a separate decision/PR from whoever owns protocol canon.
