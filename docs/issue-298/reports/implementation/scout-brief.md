# Scout brief — issue-298

Non-product, infra-pattern deliverable: the "category" is this house's own
enforcement-gate convention, not an external market. Per the scout
directive's non-product routing, the comparable systems scouted are the
project's own best-in-class exemplars of the pattern, not web results — no
web search applies here (no exemplar claim below is unsourced; every
"source" is a repo-local file, cited by path instead of URL). Batched
sequential reads (no parallel fan-out): one dependency chain (eo-state ->
its consuming gate -> core's approval-gate/gh-guard as the more elaborate
version of the same shape), each read informed by the previous one, not
independent angles.

## Must-bes (what every gate in this house already assumes)

- Fail-closed trap on the whole script, not just the deny path
  (`core/hooks/lib/gate-lib.sh:gate_trap_fail_closed`; mirrored ad hoc in
  `deliverable-guard.sh`'s own `trap` line — present but its embedded
  python still escapes it via a deliberate `sys.exit(0)`, the S4 defect).
- A kill switch whose *unrecognized* value stays active, not disables
  (`gate-lib.sh:gate_kill_switch_active` — the narrowed on-spelling
  default; `deliverable-guard.sh`'s hand-rolled case statement already
  gets this right by luck, same idiom).
- The marker producer and the refusing gate are separate hooks
  (`eo-state/hooks/state.sh` vs. the sibling `eo-methodology-gate`) — one
  writes a *signal*, the other *interprets* it. Not one script doing both.
- `SessionStart` always resets the marker before anything else runs, so a
  stale marker from a dead session can never vouch for this session's
  reads (`eo-state/hooks/state.sh` reset case, explicit in its own
  comment).
- Best-effort substring matching on the raw hook payload is an accepted
  signal shape for "was X read this session" — not a strict AST-level
  prover (`eo-state/hooks/state.sh` comment: "False positives are
  accepted ... false negatives are the known limitation").

## Performance axes the strong exemplars compete on

1. **Deny message quality** — `approval-gate.sh`/`gh-guard.sh` always name
   the *why* and the *contract clause* in the stderr message
   (`"(contract v3 s19)"`, `"(two-account model, contract v3 s8)"`).
   `deliverable-guard.sh` does this too for its one path. New gates in
   this issue keep that bar.
2. **Bash-command coverage, not just Write/Edit** — `gh-guard.sh` matches
   the raw API/graphql spellings of the same act (`gh api ... pulls/N/
   merge`, `curl -X POST .../merge`), not just the `gh` CLI form. The
   merge-refusal gate in this issue should at minimum cover `gh pr
   merge`; the API/graphql spellings are a plausible future hardening but
   out of this issue's stated acceptance criteria (which names `gh pr
   merge <n>` and `gh issue comment ... APPROVE` specifically).

## Adopt / skip

- **Adopt**: separate marker-producer hook + separate refusing gate (not
  fused into one script) — matches eo-state's split and keeps the marker
  format legible independent of any one gate's refusal logic.
- **Adopt**: fail-closed trap + narrowed kill switch, self-contained
  (no `core` dependency — `on-the-record` has none today, and adding one
  for this issue would exceed the frozen write set).
- **Skip**: importing `core/hooks/lib/gate-lib.sh` wholesale. `on-the-record`
  is not a `core`-dependent plugin (survey confirmed no such dependency
  exists); vendoring or depending on it here is a larger structural change
  than this issue asks for. The *shape* is adopted, not the file.

## Gap line

The current state (`deliverable-guard.sh` alone) already has the
fail-closed-trap and kill-switch must-bes at the shell level, but violates
them at the python-parse level (S4) and has an incomplete path match (S5)
— those two gaps are what #287 named and this issue's acceptance
criteria explicitly folds in. The larger gap is structural, not a defect
in the existing gate: no marker-producer hook exists at all, and no gate
consumes one — both must be built new.

## Sources

- `/home/jwjung/tokenmaxxxer/rulebooks/execution-observation-rulebook/execution-observation/plugins/eo-state/hooks/state.sh`
- `/home/jwjung/tokenmaxxxer/rulebooks/execution-observation-rulebook/execution-observation/plugins/eo-state/hooks/hooks.json`
- `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/approval-gate.sh`
- `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/gh-guard.sh`
- `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/lib/gate-lib.sh`
- `on-the-record/hooks/deliverable-guard.sh` (this repo, current state)
- `tests/run-orchestrate-tests.sh` (this repo, current state)

Stage count: 1 sweep-equivalent stage (batched-sequential reads, stated
explicitly per the directive's fallback-disclosure rule) + judge point,
no further deepening needed — the pattern was unambiguous on first read
and a second round would not change which shape to mirror.
