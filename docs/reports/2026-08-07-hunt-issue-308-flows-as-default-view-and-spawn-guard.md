---
proposal: docs/issue-308/proposals/2026-08-07-flows-as-default-view-and-spawn-guard.md
---

# Hunt record — flows-as-default-view-and-spawn-guard

## after-proposal — stance 0: assume the gate/claim just written is bypassable or wrong — find the bypass or the false claim

Verdict: NO FINDING
Seed: docs/issue-308/proposals/2026-08-07-flows-as-default-view-and-spawn-guard.md (docs-only diff, no code changed)
cap_seconds: 180
tier: size:docs-only
diff_stat_lines: 2 files changed (docs only, >200 lines per dispatcher)
started_at: 2026-08-07T16:17:41+09:00
ended_at: 2026-08-07T16:24:00+09:00

Both cited claims were verified directly against the code, not the proposal's account of it:

1. `test_gates.py:779-781` (`t_closure_sweep_merged_delivery_issue_open_violates`) exists verbatim as
   cited, calls `closure_sweep.classify("OPEN", "MERGED", "Closes #135", 135)`, asserts the result
   equals `closure_sweep.MERGED_DELIVERY_ISSUE_OPEN` (defined at `gates/closure_sweep.py:24`, returned
   at `gates/closure_sweep.py:49`), and `python3 -m pytest test_gates.py -k
   t_closure_sweep_merged_delivery_issue_open_violates -q` passes (1 passed). No falsity here.

2. Traced `spawn.py` `main()` for the `--issue` path: `positive_int` parses `--issue`, and the only
   consumers are `roster_kill`, `_watch`, `approve_scope`, and ultimately `_spawn_one(...)` at line 2690
   which reaches `spawn_cmd()` at line 3117. Grepped the whole file for `flows` / `roster_ps` — the only
   `flows` reference is the `role == "flows"` dispatch branch (line 2529-2532), a separate CLI subcommand
   never called from the `--issue` spawn path. `roster_ps()` is likewise only invoked when `role == "ps"`
   (line 2526), never from `_spawn_one`/`spawn_cmd`. No guard, no consultation of flow/roster state before
   minting a role session via `--issue` exists anywhere in `spawn.py`. Claim is accurate as stated — this
   is docs-only phase 1, the gap is real and not yet closed.

No bypass or falsity found in either cited claim; both hold as stated in the proposal.
