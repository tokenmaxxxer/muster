---
proposal: docs/issue-419/proposals/2026-08-07-pattern-recurrence-checks.md
---

# Hunt record — issue-419 pattern-recurrence-checks

## after-proposal — stance 0: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — `subprocess_call_shape_divergence` groups call sites "within a touched file" only, so the real #388 pattern (same command, divergent flags, across separate files) can never trigger it — a PR editing just one file with the dangerous shape sails through untouched.
Kind: design-error
Seed: docs/issue-419/proposals/2026-08-07-pattern-recurrence-checks.md, step 1 under "What will be done"
cap_seconds: 60
tier: default
diff_stat_lines: ~260 (docs-only, two files added under docs/)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:03:00Z

### Reproduce
```
grep -n '"gh", "api"' -A2 gates/closure_sweep.py gates/ci.py spawn.py
```
Shows the actual four `gh api` call sites this check is modeled on:
- `gates/closure_sweep.py:147` — `["gh","api", ..., "-f", ...]` (no `-X`, POSTs)
- `spawn.py:1833` and `spawn.py:1855` — same `-f`-only shape
- `gates/ci.py:205` — `["gh","api","-X","GET", ..., "-f", ...]` (the safe shape)

These are the exact call sites the proposal cites as the #388 instance, and they live in three
different files. Per step 1 of "What will be done": "Group calls **within a touched file** by
their first two argv elements ... Within a group of 2+ ... flag when the flag sets diverge."
Grouping is scoped to a single touched file, and the check only parses touched files
(`changed_files()`), never a comparison file that isn't part of the diff.

### Observed
Following the design literally: a PR that touches only `spawn.py` and adds/keeps the `-f`-only
`gh api` call (identical to the real regression) produces a group of size 1 in that file for the
`("gh","api")` command (or a same-file group where all members share the same, wrong, flag
shape) — never 2+ divergent members, since the correct `-X GET` variant lives only in
`gates/ci.py`, an untouched file the check never parses. Result: `subprocess_call_shape_divergence`
returns `[]`, the gate passes silently, even though this is precisely the #388 shape the
"How you'll know it worked" section claims will be caught ("this mechanism would have caught
instance 1 (#388's argument-shape divergence)").

### Expected
For the check to make good on its stated acceptance claim (catching instance 1), grouping must
compare call sites across all files touched by, or reachable from, the repo — not scoped to a
single touched file — since the real divergence the issue names is inherently cross-file. As
written, the design's own worked example (fixture: "two `gh api` calls" presumably in one test
file) will pass the unit test while the actual repo pattern it's meant to generalize to remains
undetected, because the scoping rule silently excludes the multi-file case that is the norm, not
the exception, for this codebase's call sites.
