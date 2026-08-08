---
status: proposed
files:
  - docs/issue-512/reports/execution-observation.md
---

## Request

Independently reproduce, in a fresh scratch TARGET-repo fixture built
outside this repository, the runtime claims in the implementation
session's own record: `call-shape-guard.sh` and
`accumulation-claim-guard.sh` each deny (exit 2) a synthetic violation
and pass (exit 0) a clean write, and `gates/closure_sweep.py`'s
`accumulation_trend()` produces a valid "no prior data" artifact on an
empty fixture — then render the three-level verdict (outcome /
trajectory / step) in `docs/issue-512/reports/execution-observation.md`.

## Constraints

- Verdict claims require citation adjacent to the claim (commit SHA,
  file:line, or PR comment URL) — no bare assertion.
- Independence: never edit the observed role's `src/`, `test/`, or
  `docs/issue-512/` paths outside this role's own report path.
- Never re-run the observed *task* (do not rebuild or modify the hooks);
  invoking the already-shipped hook scripts and `closure_sweep.py`
  function against a fixture I build myself, to observe their runtime
  behavior, is the acceptance criterion the issue itself names
  (`provenance: executed-unit`) — distinct from re-executing the
  implementation work.
- Record must state the independence statement before any verdict
  language.

## What will be done

1. Build a scratch git repo under `$TMPDIR`, outside this repo's tree.
2. Write a synthetic `.py` file matching the accumulation shape-1
   pattern (three-plus inline `subprocess.run`/`gh` calls) and a
   synthetic divergent-call-shape `.py` write, and invoke
   `call-shape-guard.sh` / `accumulation-claim-guard.sh` against each,
   per their documented payload contract (`CSG_PAYLOAD`/`ACG_PAYLOAD`
   env var, JSON PreToolUse-shaped), with `cwd` set to the fixture root.
3. Confirm each hook: exit 2 on the synthetic violation, exit 0 on an
   accompanying clean write.
4. Call `accumulation_trend(root)` directly against the same
   empty-until-populated fixture (no prior `runs/accumulation_trend.json`)
   and confirm `has_prior: False` plus a non-raising, valid
   `format_accumulation_trend()` string.
5. Write `docs/issue-512/reports/execution-observation.md` — outcome /
   trajectory / step verdict, each claim cited to what was actually
   observed this session (the fixture run's own output, or the read PR
   artifacts).

## Out of scope

Fixing anything found; filing issues; editing the observed role's hook
scripts, tests, or docs; re-litigating the phase-1 hunt finding already
recorded in `docs/issue-512/reports/implementation.md` beyond citing it.

## How you'll know it worked

`docs/issue-512/reports/execution-observation.md` exists, committed,
with `loop_state` at a terminal value for this record kind, every
verdict-bearing sentence carrying an adjacent citation, and the
independence statement preceding all verdict language.

## Hunt record

docs-only, no before-landing dispatch — the only file this transition
touches (`docs/issue-512/reports/execution-observation.md`) is under
`docs/`.
