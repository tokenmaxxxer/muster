---
proposal: docs/issue-492/proposals/2026-08-08-shipped-session-supervision.md
---

# Hunt record — shipped-session-supervision

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — reconcile()'s planned integration point (drive()/roster_watchdog tick) is not where the orchestrator's continuation decision actually happens, so it is trivially bypassable by the orchestrator continuing to read board() directly, exactly as it does today.
Kind: design-error
Seed: docs/issue-492/proposals/2026-08-08-shipped-session-supervision.md (Decision item 4: "its output is what drive() consults for 'what next' instead of raw loop_state")
cap_seconds: 60
tier: default (docs-only diff)
diff_stat_lines: 251 insertions across 3 files (proposal + survey.md + scout-brief.md)
started_at: 2026-08-08T20:11:16+09:00
ended_at: 2026-08-08T20:16:00+09:00

### Reproduce
```
grep -n "def drive\|roster_watchdog\|a.role == \"drive\"" spawn.py
sed -n '2502,2513p' spawn.py
```

### Observed
`drive()`'s own docstring (spawn.py:2502-2508) states the opposite of what
the proposal assumes: "누구를 다음에 띄울지는 기계가 평가하는 라우팅 표가
아니라 오케스트레이터가 보드(기록, loop_state)를 직접 읽고 내리는 판단이다
(이슈 #120)" — i.e. the *orchestrator itself* reads the board directly and
decides; `drive()` is a stub that never consults `loop_state` and always
returns immediately (spawn.py:2511-2513: "띄울 게 없다고 보고 멈춘다").
`drive()` (CLI verb, spawn.py:2865-2870) and `roster_watchdog()` (CLI verb,
spawn.py:2741) are two independent, separately-invocable subcommands with no
call relationship — `drive()` never calls `roster_watchdog()` or anything
that would call `reconcile()`. The proposal's stated wiring — "called from
inside roster_watchdog's existing tick... and its output is what drive()
consults" — has no code path connecting those two functions today, and the
proposal doesn't add one; it only says reconcile "rides" the watchdog tick.
Since the real continuation decision-maker (the orchestrator, reading the
board directly per #120) sits entirely outside both `drive()` and
`roster_watchdog()`, nothing in the proposed design stops the orchestrator
from reading `board()`/`loop_state` directly and ignoring `reconcile()`'s
divergence list — which is the exact "trusting the happy-path report"
failure mode the proposal claims to close.

### Expected
The proposal should either (a) name the actual mechanism that forces the
orchestrator to consult `reconcile()`'s output before acting (e.g. `drive()`
refusing to no-op silently and instead surfacing divergences, or the board
itself being rewritten by reconcile so a direct board read already reflects
reconciled state), or (b) acknowledge as a known gap that orchestrator
behavior is out-of-repo/human judgment and cannot be forced to consult
`reconcile()`'s output, rather than asserting "drive() consults [reconcile]
... instead of raw loop_state" as though that closes the loop when `drive()`
does not read `loop_state` at all today and is not called by
`roster_watchdog`.
