# Survey — issue #392

## Current state, read directly from this checkout

- Merge relay is one documented step: `on-the-record/commands/run.md:229`
  — `gh pr merge <n> --merge --delete-branch`. Nothing after it touches
  the orchestrator's own local checkout. The orchestrator reads files
  directly (per issue text) and has no scripted refresh step; this
  session's own habit of `git pull` after merges is exactly the
  "habit, not mechanism" #392 names.
- `gates/closure_sweep.py` (`find_violations`, `:71-100`) is the sweep
  #383 refers to: detect-only, reports `MERGED_DELIVERY_ISSUE_OPEN` by
  reading issue + PR state via `gh`. It is invoked explicitly via
  `spawn.py closure-sweep` (`spawn.py:2485-2499`) and is also folded
  into `spawn.py flows --json`'s `hygiene.closure_sweep` field
  (`gates/flows.py`, per `docs/specs/flows-schema.md:191-200`) — the
  scheduled/standing surface #392 is asked to check first. It has no
  branch-vs-PR check today; its unit of comparison is issue state vs
  PR body, never `git ls-remote`.
- `spawn.py clean` (`spawn.py:2509-2559`) is LOCAL workspace cleanup
  under `MUSTER_WORK_DIR` / `~/.tokenmaxxxer/work` — it deletes local
  clones, gated on no uncommitted changes and no commits absent from
  `origin`. It never touches the remote's own branch list. #288's N1-N8
  are about this command's own bugs (`--issue` scoping, `--dry-run`
  validation, etc.) — orthogonal to #392's remote-branch question.
  Per #392's own instruction to check whether `clean` is the right home
  for item 2: it is not — `clean` operates on local work directories by
  path, has no concept of "remote branch with no open PR", and mixing
  a remote `ls-remote`-vs-PR reconciliation into a command whose gate
  is "uncommitted changes present?" would conflate two different
  safety questions (local dirty state vs. remote submission state).
- `flows --json`'s `decision_queue` (issue #374) already demonstrates
  the pattern #392 item 4 asks for: computed data surfaced to the
  operator through a standing command output, not a new notifier.
  `hygiene.closure_sweep` is the same shape and already reaches the
  same surface.

## What #392 asks to check first (per its own Boundary section)

- **#288**: local workspace cleanup (`clean`), not remote branch state.
  Confirmed above — different resource, different safety gate. Item 2
  does not belong in `clean`.
- **#374**: same family (unbounded accumulation with no floor), but a
  different resource (decision queue items, not branches). Its fix
  pattern — surface existing computed data through the existing
  standing surface — is directly reusable for #392 item 4.
- **#383**: `closure_sweep`'s sweep already runs on a schedule path
  (`spawn.py flows --json` is polled/read repeatedly by the
  orchestrator per the run.md protocol) and already makes `gh` calls
  for issue + PR state per subject. Adding a branch-reconciliation
  check here means one more read (`git ls-remote` — no `gh` call
  needed, `#392` itself is only a two-line computation) inside a
  mechanism that already exists and is already read, rather than a
  second standing checker nobody wires up (the exact failure #383
  itself documents for the *existing* sweep going unwired to CI).

## Write surfaces this proposal will touch (frozen in the proposal)

- `on-the-record/commands/run.md` — merge-relay step, symptom 1.
- `gates/closure_sweep.py` — new branch-reconciliation check, symptom 2.
- `gates/flows.py` / `docs/specs/flows-schema.md` — surface the new
  check's output under `hygiene`, item 4.
- `test_gates.py` — unit coverage for the new classification.

## Skip-condition note (scout directive)

This issue is internal orchestration-tooling design, not a
product-facing surface — there is no external "category" of comparable
products to benchmark against (git-branch-hygiene bots exist, but the
constraint set here — never delete unsubmitted work, detect-only
contract, no CI wiring assumed — is specific to this repo's own prior
decisions). The field for this build is the codebase and the prior
decisions already recorded, per the scout directive's own definition of
"field" for non-product-shaped work. That field is what this survey
covers (issues #135, #189, #374, #383, #288, and the code they
describe). Scout stage 1's external sweep is skipped on that basis; the
stage 2 "deepen" motion is replaced by reading the prior-art issues in
full, done above.
