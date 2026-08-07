---
status: proposed
files:
  - docs/handbooks/operations.md
  - spawn.py
  - test_spawn.py
---

## Request

#308 (paraphrased): an orchestrator answering "is issue N already done?" today has to
hand-reconcile three partial views (board-only status, GitHub issue open/closed,
live-session roster) and got it wrong — it spawned a duplicate PR for work already
merged. `gates/flows.py` already computes the composed answer (`stage` per subject,
live sessions, decision queue) but the contract's documented "read the board" step
points at the weaker board-only view instead, that weaker view's default output
buries its own signal in a 42-role enumeration, and nothing at spawn time consults
the composed view before minting a session — so a duplicate spawn is avoidable but
not mechanically prevented.

## Constraints

- Per #310: acceptance is discharged by an executable artifact that runs, not a doc
  sentence or a promise. The refusal/override behavior below ships as code with a
  test that fails on regression, not as an instruction added to a handbook.
- Per #363 (generator vs instance): the generator here is "the contract names a
  weak-but-existing view instead of the strong one, and nothing gates spawn against
  the strong one." Repointing the doc removes the *first* generator (wrong default
  answer); adding the spawn-time consult removes the *second* (nothing asks even
  when the strong view is read). Fixing only the doc leaves an operator who skips
  reading it (or misreads a stale terminal) able to reproduce the original incident;
  the spawn-time check is what makes the class, not just this instance, structurally
  harder to hit again.
- Per #358: `runs/` is gitignored and absent from this clone (confirmed:
  `git check-ignore runs` and `ls runs` both fail to find a tracked entry); this
  proposal's write set does not depend on reading `runs/ledger.jsonl` at spawn time,
  only on `flows.flows()`, which is git-network (`gh`) backed, not `runs/`-backed.
  `hooks.json` declaring three events is a fact about *this repo's* configuration,
  not a claim about what Claude Code supports in general — not relevant to this
  issue's write set, noted only because the invoking prompt required addressing it
  if encountered; it was not encountered as a dependency here.
- Boundary confirmed against #374 (decision-queue aging), #325 (closed;
  never-spawned coverage), #390 (post-landing re-verification), #398 (test
  collection collision, unrelated infra) — none own this write set; see
  `docs/issue-308/reports/implementation/survey.md` for the per-issue check.
- Scout-directive skip: no external scouting run. This is an internal, single-
  operator orchestration CLI with no product-category analog to benchmark against;
  the issue's own "Fix direction" §2 already prescribes the mechanism shape
  ("refuse — or at minimum warn loudly and require an explicit override that is
  recorded"), leaving the only real design decision the refuse-vs-warn choice
  handled below in Rationale, not a market-facing UX question scouting would inform.

## Rationale

**Repoint vs. rebuild `flows`.** Considered rebuilding the composed view as new
code under this issue. Rejected: `gates/flows.py` already computes exactly the
four-way split the issue asks for (`docs/specs/flows-schema.md`, built across
#172-#222) and is under active schema-versioning discipline of its own; duplicating
that logic in `status()` would create two implementations of "what stage is this
subject in" that can drift. Chose: make `status()` (the no-args default) call into
`flows.flows()` for its per-subject line instead of `board()` directly, and keep
`flows --json` as the machine-readable form already documented at
`docs/specs/flows-schema.md`.

**Hard refuse vs. warn+override at spawn time.** Considered a hard refusal with no
override (spawn.py exits nonzero, full stop, if `flows` says the subject+role is
`closed` or has a live session). Rejected as the sole behavior: `flows`'s own stage
derivation can be wrong in ways this repo already documents (`flows-schema.md`'s
"not forced into the five named stages" note) — a hard block with no escape hatch
turns a `flows` false positive into a hard stop with no path forward, which is worse
than the status quo for the legitimate case (e.g. deliberately reopening finished
work). Chose: refuse by default, `--force-spawn` flag required to override, and the
override is recorded (a stderr line plus a marker file under `docs/issue-<n>/` is
out of the frozen write set for this proposal — recording lands as a printed,
greppable stderr line naming the override at spawn time, since no new board-write
path is in this write set). This matches the issue's own "or at minimum... requires
an explicit override that is recorded" alternative literally, and keeps the write
set to `spawn.py` + its test rather than also touching the board-write path.

**Collapse the 42-role enumeration vs. leave it.** Considered leaving `status()`'s
missing-role line as-is once it stops being the primary default (since `flows`
becomes the headline). Rejected: the doc's own repointing (handbook change) does not
change what `python3 spawn.py` with no args actually prints, and the issue's
acceptance #3 is explicit ("board's default output is readable without filtering") —
about the command's actual stdout, not just the docs describing which command to
run. Chose: same code change that switches `status()`'s per-subject line to
`flows`-sourced also removes the full-42-role listing (flows already reports stage
+ present roles only, no exhaustive absence list).

## What will be done

1. `docs/handbooks/operations.md`: change the "read the board" step (currently
   line 391, `python3 spawn.py # read the board (read-only)`, and the loose
   "read the board" prose at line 345) to name `python3 spawn.py flows` (human
   table) / `--json` (machine) as the documented way to answer untouched / in-flight
   / awaiting-decision / done, with one line on why (`status()` is board-only,
   `flows` composes board + PRs + live sessions).
2. `spawn.py`: change `status(cwd)` (spawn.py:1147-1183) to source its per-subject
   line from `flows.flows(cwd, json=False)`'s parsed stage/session/decision-queue
   data instead of `board(root)` directly, and drop the `(기록 없음: ...)` full-role
   enumeration in favor of listing only roles actually present, mirroring what
   `flows`'s human-table branch already reports.
3. `spawn.py`: before `spawn_cmd()` is invoked with `a.issue` set, consult
   `flows.flows(cwd, json=True)` for that issue's subject: if `stage == "closed"`
   or a live session already exists for that issue+role (cross-check
   `roster_ps()`'s live list), refuse with a nonzero exit and a message naming the
   conflicting PR/session, unless `--force-spawn` is passed, in which case proceed
   and print a stderr line recording the override (issue, role, reason:
   force-spawn-on-{closed-flow|live-session}).
4. `spawn.py`: add `--force-spawn` to the argparse definition (`main()`,
   spawn.py:2489 on).
5. `test_spawn.py`: unit tests for (a) the new pre-mint refusal on a closed-stage
   subject, (b) refusal on a live-session collision, (c) `--force-spawn` overriding
   both with the stderr record present, (d) `status()`'s output no longer listing
   absent roles for a subject with partial records.
6. Confirm (no code change — documented as already-satisfied, per survey): acceptance
   #4, `hygiene.closure_sweep` detecting merged-but-open, already holds via
   `closure_sweep.classify()` + `test_gates.py:779-781`; the phase-2 record notes
   this rather than re-touching `gates/closure_sweep.py`.

## Out of scope

- `#374`'s decision-queue floor/clock — a different field of `flows` output, not
  touched here.
- Rebuilding or re-deriving `flows[].stage`'s classification logic itself — this
  proposal consumes it, does not change how it is computed.
- Any change to `gates/closure_sweep.py` — acceptance #4 is already met (see
  Rationale/survey); nothing there needs to change.
- Persisting spawn-refusal overrides as a board record or GitHub comment — the
  stderr line is the recording mechanism for this proposal; a durable audit trail
  (if wanted) is a follow-up, not silently added here.
- `runs/ledger.jsonl` — gitignored, absent from this clone, not read by this write
  set (see Constraints).

## How you'll know it worked

- `python3 spawn.py -C <repo>` (no args) prints per-subject `stage` (untouched /
  in-flight / awaiting-decision / done — closed) sourced from `flows`, with no
  41-of-42-role noise line.
- `python3 spawn.py <role> <task> --issue N` against a subject whose `flows` stage
  is `closed`, or whose issue+role already has a live session, exits nonzero and
  names the conflict, without `--force-spawn`; with `--force-spawn` it proceeds and
  a stderr line records the override.
- `python3 -m pytest -q --ignore=gates test_spawn.py` (root suite; `gates/` excluded
  per the tracked #398 collection collision) passes, including the new refusal/
  override/status-output tests, with no regression in the existing 347-test
  baseline (`python3 -m pytest -q --ignore=gates`, verified on this branch at
  commit `0378202`, identical to `main` since the working tree was clean at session
  start).
