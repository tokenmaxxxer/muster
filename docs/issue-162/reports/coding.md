---
loop_state: landed
---

# Coding record — issue #162

upstream: docs/issue-162/proposals/role-rename-execution-1.md
(approved via issue comment `APPROVE issue-162/coding`)

## Why

Execute step 1 of the merged issue-160 role taxonomy (docs/issue-160/proposals/role-taxonomy.md, round-5 table): rename the 9 existing `roles/*.json` to canon names with narrowed `decides`/`use_when`/`produces`/`write_scope`, update every in-repo reference, and carry the proposal's in-flight-branch/historical-record-immutability rules and human-run GitHub-rename command list.

## What was done

- Renamed all 9 `roles/*.json` (`git mv`) to the round-5 canon names and rewrote each file's `marketplace`/`repo`/`path` to the new rulebook name and `decides`/`use_when`/`produces`/`write_scope` to the round-5 table values from `docs/issue-160/proposals/role-taxonomy.md`: `coding→implementation`, `qa→execution-observation`, `review→conformance-review`, `verify→defect-verification`, `ops→release-engineering`, `reflect→issue-retrospective`, `product→product-discovery`, `feasibility→technical-feasibility`, `ux-design→interaction-design`.
- `.claude-plugin/marketplace.json`: updated all 30 `"repo"` occurrences from `tokenmaxxxer/<old>-agent-rulebook`/`tokenmaxxxer/ux-design-rulebook` to `tokenmaxxxer/<new>-rulebook`; renamed the role-scoped plugin/bundle `"name"` fields in lockstep (`coding-agent-env→implementation-env`, `qa-agent-env→execution-observation-env`, `qa-cycle→execution-observation-cycle`, and the equivalent `-cycle`/`-agent-env` pairs for the other 7 roles); left role-specific command names that don't embed the old role name (`intake`, `testrun`, `bugreport`, `stats`, `regress`, `signoff`) unchanged; updated the handful of prose `description` mentions of old role names to match.
- `README.md`: updated the role table (9 rows) and every inline mention of an old role name used as an identifier (install examples, `spawn.py` invocations, `/on-the-record:run` example, the two named-halt bullets, the `--settings`-merge example) to the round-5 name.
- `run.md`: confirmed at execution time it does not exist in this repo (re-grepped, zero hits) — no-op, matches the survey's flagged-unconfirmed note.
- `spawn.py`/`gates/gates.py`: confirmed by reading — no code change needed. Both resolve `roles/<role>.json` generically by branch/argv role name; the existing fail-closed `모르는 역할: {role} (있는 것: {have})` message (spawn.py `role_settings()`) already lists the new names the moment an old file no longer exists. No silent alias added, per the phase-1 scout brief: no execution history survives under the old names.
- `test_spawn.py`: fixed 4 hardcoded literal paths that broke once `roles/coding.json`/`roles/qa.json` were renamed (`Path(spawn.ROOT) / "roles" / "coding.json"` ×2, and two `_spawn_one`/`ownership_report` calls passing `"qa"`/`"coding"` as the live role argument with matching `docs/issue-3/reports/qa.md` fixture paths) — these exercise real role-file resolution, not arbitrary test literals, so they needed the rename; left `BoardSnapshot.test_delta_shows_changed_and_new`'s `qa.md`/`coding.md` filenames alone since those are arbitrary board-snapshot filenames unrelated to role resolution. `test_gates.py`/`test_approve_scope.py`/`test_vocab_coherence_roles.py` needed no change — confirmed by running: none of their `"coding"`/`"qa"`/`"feasibility"`/etc. literals touch a real `roles/*.json` file (mock repos / generic fixture strings only), consistent with the proposal's "pending-confirm pass only" prediction.
- Local dev-machine rulebook checkouts (this session's own `$TOKENMAXXXER_RULEBOOKS` clones and this repo's `runs/rulebooks/tokenmaxxxer-qa` cache) were renamed to match on disk so the test suite exercises the real local-checkout path instead of falling through to a network clone (which the sandbox blocks) — a local, this-machine-only operation, not a GitHub action and not part of the repo's tracked write set.
- In-flight-branch check (proposal §5): `git branch -r` and `gh pr list --state open` show no live `issue-<n>/<old-role>` branch other than this session's own `issue-162/coding` — which lands via this same PR, satisfying proposal §5's option (a) ("that branch's role session finishes and lands first"). No temporary alias stub was needed.
- Historical-record immutability (proposal §6) and the GitHub rulebook-repo rename human command list (proposal §7) are carried unchanged from the proposal — no code enforces either; both are process text, already stated there.
- `pytest test_spawn.py test_gates.py test_approve_scope.py test_vocab_coherence_roles.py` — 117 passed.
- `grep -rn "agent-rulebook"` — remaining hits are all under historical `docs/issue-<n>/` records (proposals/surveys/reports predating this rename, never rewritten per §6) plus three files outside this proposal's frozen write set (`protocol.md`, `protocol.ko.md`, `bench/run.py`, and one `test_gates.py` line) that use `qa-agent-rulebook` only as a generic illustrative example unconnected to real role resolution — left untouched per the SCOPE-EXCEEDED rule since the proposal's file list did not include them; flagged here for a possible fast-follow, not silently expanded into this PR.

## Open findings

None. (Scope-exceeded items — `protocol.md`/`protocol.ko.md`/`bench/run.py`'s illustrative `qa-agent-rulebook` mentions — are noted above as a fast-follow candidate, not a blocking finding against this PR's frozen write set.)

## Next steps

None for this issue — phase 2 is complete and landed. A human with org admin rights runs the 9 `gh repo rename` commands from the proposal's §7 whenever convenient (independent, no code dependency, redirect covers the gap). A possible fast-follow issue could sync the illustrative old-role-name mentions in `protocol.md`/`protocol.ko.md`/`bench/run.py`.

## Open-finding resolution path

No open findings block. If a hunt or review later surfaces one, it will be logged here with a resolved_findings entry before further build commits, per the coding role directive.
