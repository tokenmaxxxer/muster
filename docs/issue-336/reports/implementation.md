---
code_under_review:
  - docs/specs/reconciled-index.md
  - gates/spec_index.py
  - test_spec_index.py
  - gates/ci.py
  - docs/handbooks/on-the-record.md
loop_state: phase-2-complete
---

# Implementation record — issue #336

Approved via single-account `APPROVE issue-336/implementation` comment on
the issue (author = PR author; approvers.md lists JiwonJung94). No
second/conditional comment followed the token.

## What was done

1. `docs/specs/reconciled-index.md` — table of every spec-shaped document
   named in the proposal, with recorded SHA256, plus a "Resolved
   ambiguities" section fixing the confirmed ledger-location
   contradiction (`runs/ledger.jsonl` is canonical storage;
   `ledger/collect.py` is an aggregator over it, not itself storage).
2. `docs/handbooks/on-the-record.md` — reworded both diagram lines
   (Korean line 27, English line 51) so `ledger/` is labeled as the
   aggregator over `runs/ledger.jsonl`, not the storage location,
   matching the index. Checked `operations.md`, `flows-schema.md`, and
   `on-the-record/commands/run.md` — all already say `runs/ledger.jsonl`
   correctly; no other file needed the same fix.
3. `gates/spec_index.py` — recomputes each listed file's SHA256 against
   `docs/specs/reconciled-index.md` and exits nonzero listing every
   mismatch; check mode (default) and `--update` mode (rewrites recorded
   hashes), matching the two-mode convention other `gates/*.py` scripts
   use.
4. `gates/ci.py` — imported `spec_index` and added
   `bad += spec_index.check(repo)` to the non-`closes_only` branch of
   `check()`, alongside the other deterministic checks (`record_enums`,
   `record_wellformed_in`, etc.).
5. `test_spec_index.py` (repo root, matching `test_gates.py`'s existing
   convention) — 4 tests: baseline passes, a mutated tracked file fails,
   a missing index fails, and `--update` resyncs a drifted hash. Uses a
   temp copy of only the tracked-doc paths (not a full-tree copy — the
   sandbox denies copying dotfiles/`.claude`/etc., so the test copies
   exactly the files the index references).

## Why (upstream basis)

Approved phase-1 proposal:
`docs/issue-336/proposals/2026-08-07-spec-reconciliation-index.md`.
Approach B (content-hash manifest + CI-available gate) was chosen there
over approach A (semantic contradiction detection) because only B
satisfies #310's "fails on regression" requirement without introducing
an unverifiable LLM-judgment gate. This session implemented exactly
that approved "What will be done" list (5 steps) with no scope
additions.

## Verification run (actually executed, not narrated)

```
$ python3 -m pytest test_spec_index.py -v
```
Result: 4 passed, 0 failed, 0 skipped.

```
$ python3 gates/spec_index.py
```
Result: exit 0 — "통과: 모든 spec 문서가 기록된 해시와 일치한다".

```
$ python3 -c "import sys; sys.path.insert(0,'gates'); import ci"
```
Result: imports cleanly — `spec_index.check` wiring does not break
`gates/ci.py`'s existing import graph.

`python3 test_gates.py` (pre-existing full suite) was also run: it
fails on one pre-existing, unrelated test
(`t_repo_local_claude_config_stops_the_spawn`) with `OSError: [Errno 30]
Read-only file system: '/home/jwjung/.tokenmaxxxer/trusted-repo-config.json'`
— a sandbox filesystem-permission issue in a test that writes outside
the repo, present before this change and untouched by this change's
write set. Not treated as a regression from this work; not silently
passed over either — recorded here as observed, per #334 (a skipped or
masked failure is not a passing test).

## What did not work

None — no attempt was made and undone during this build.

## Doc-placement ladder (completed items)

- [x] New gate script (`gates/spec_index.py`) + wiring
      (`gates/ci.py`): no new env var, config key, or dependency
      introduced — nothing further to place in a handbook.
- [x] Library/format decision (content-hash manifest chosen over
      semantic detection): already recorded in the approved phase-1
      proposal's `## Rationale`
      (`docs/issue-336/proposals/2026-08-07-spec-reconciliation-index.md`)
      — that is the decision record for this choice; no separate
      `docs/issue-336/decisions/` entry, since phase 2 made no
      alternative choice not already decided in phase 1.
- [x] No benchmark/investigation numbers produced — no
      `docs/issue-336/reports/` entry beyond this record.

## CI-enforcement scope (per #358 — what was searched and where)

`gates/ci.py`'s `check()` now calls `spec_index.check(repo)` in the
non-`closes_only` path, so the check is *available* — callable locally
via `python3 gates/ci.py` or through the router's `check()`. Whether it
actually blocks a PR on GitHub depends on which CI entrypoint invokes
`ci.py` and with which flags:

- Searched `.github/workflows/*.yml` in this clone: the only file
  present is `plan-aware-closes-gate.yml`. It checks out `main` (never
  the PR's own diff) and runs `gates/ci.py --pr <n> --autodetect
  --closes-only`, and `--closes-only` skips every gate but the
  plan-aware Closes gate by design (see `gates/ci.py`'s own module
  docstring and the `check()` docstring, and issue #245's
  trust-boundary rationale: running a gate against a PR's own diff lets
  the PR rewrite the gate to pass).
- Did not treat `runs/` as evidence either way: `runs/` is
  gitignored and absent from this clone, so it was not searched at all
  — it holds session/ledger logs, not CI configuration, so its absence
  says nothing about whether `spec_index` is CI-enforced.
- Did not treat a `hooks.json` declaring events as evidence either way:
  a hooks file (if present) declares Claude-Code-harness hook wiring
  for local sessions — a fact about local hook configuration, not about
  what GitHub Actions runs against a pull request. Neither this nor the
  `runs/` absence was used to support the enforcement conclusion below.
- Conclusion: `spec_index` is reachable the same way
  `record_enums`/`record_wellformed_in`/etc. already are, but is **not**
  enforced as a required PR check today. Designing a workflow that
  invokes the full (non-`closes_only`) `ci.py` safely against a PR's own
  diff is exactly the kind of trust-boundary design #245 already did
  for the Closes gate — extending that to `spec_index` is out of scope
  for this proposal (see the proposal's "Out of scope," item 4/5).

## What this change reaches beyond its own acceptance criteria (per #330)

The proposal's stated acceptance is `pytest test_spec_index.py` failing
on regression (discharged above — 4/4 passed, and the gate demonstrably
fails when a tracked file is mutated, per `t_mutated_tracked_file_fails`
and `t_missing_index_fails`). Beyond that specific check, this change
also corrects the live, currently-read `docs/handbooks/on-the-record.md`
diagram — any reader of that document today sees the accurate
ledger-location claim regardless of whether a CI workflow ever invokes
`spec_index`. That reach is independent of the CI-enforcement gap
recorded above: the doc correction is not gated on enforcement landing
later.

## Open findings

None open. The one prior warrant-hunter finding on this subject (the
`--closes-only` CI-enforcement gap) was already folded into the
approved proposal's step 4/"Out of scope" before this phase-2 session
started, and is restated accurately above rather than left as a new
open item.

## Rationale for deviations

None — build matched the approved proposal's "What will be done"
exactly; no scope-exceeded stop and no alternative swap occurred.
