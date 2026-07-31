# Proposal — role rename execution ① (issue-162)

files (phase 2 write set): `roles/coding.json → roles/implementation.json`, `roles/qa.json → roles/execution-observation.json`, `roles/review.json → roles/conformance-review.json`, `roles/verify.json → roles/defect-verification.json`, `roles/ops.json → roles/release-engineering.json`, `roles/reflect.json → roles/issue-retrospective.json`, `roles/product.json → roles/product-discovery.json`, `roles/feasibility.json → roles/technical-feasibility.json`, `roles/ux-design.json → roles/interaction-design.json`, `.claude-plugin/marketplace.json`, `README.md`, `run.md` (pending confirm), `test_spawn.py`/`test_gates.py`/`test_approve_scope.py`/`test_vocab_coherence_roles.py` (pending-confirm pass only, no fixture hardcodes an old name per current grep). No `spawn.py`/`gates/gates.py` code changes — both resolve roles generically from `roles/*.json`, confirmed by reading (docs/issue-162/reports/coding/survey.md).

## Request (paraphrased, secrets stripped)
Execute step 1 of the already-merged issue-160 role taxonomy: rename the 9 existing `roles/*.json` files to their round-5 canon names with narrowed `decides`/`use_when`/`produces`/`write_scope`, update every in-repo reference, prep the 9 GitHub rulebook-repo renames as a human-run command list, and state the in-flight-branch and historical-record-immutability rules explicitly.

## Constraints
- Proposal only in this PR — no `roles/*.json`, `marketplace.json`, README, or test edits land here; phase 2 opens only after human Approve per contract v3 s19.
- GitHub repo renames are outside this session's authority — deliverable is a command list for a human, not an executed action.
- Historical `docs/issue-*/reports/<old-role>.md` files are never renamed or rewritten.

## What will be done

### 1. Role JSON rename + content narrowing (Track A, single pass)
Rename all 9 files per the issue-160 mapping, each keeping `marketplace`/`sandbox`/`record_fields` structurally as-is and updating:
- `repo` → the new rulebook repo name (`tokenmaxxxer/<new-name>-rulebook`, dropping `-agent` per the round-6 convention already ratified in issue-160's proposal).
- `path` → `$TOKENMAXXXER_RULEBOOKS/<new-name>-rulebook`.
- `decides`/`use_when`/`produces`/`write_scope` → the round-5 table values from `docs/issue-160/proposals/role-taxonomy.md` (e.g. `implementation`'s produces gains `closed_checks entries`; `write_scope` stays `["src/**","test/**"]` for `implementation`, empty `[]` for the other 8 — matches the merged proposal, no re-litigation here).

No file is renamed in place under the old name at any intermediate step — Track A stands up all 9 in one commit, matching the issue-160 proposal's "no in-flight rename" rationale.

### 2. Unknown-old-name behavior: hard error, no silent alias
`spawn.py`'s `role_settings()` (spawn.py:330-333) already errors with `모르는 역할: {role} (있는 것: {have})`, listing all current role names, the moment `roles/coding.json` etc. no longer exists — this is sufficient and requires no code change. Per the scout brief (docs/issue-162/reports/coding/scout-brief.md), no silent alias is added: this repo has zero execution history under the old names surviving past this rename (no role has run mid-issue under a to-be-renamed name at merge time), so there is no user to protect with a grace period. If a future rename ever needs staged deprecation, that is a new decision made at that time, not inherited from this one.

### 3. `.claude-plugin/marketplace.json`
Update all 32 `"repo"` occurrences (9 role blocks) from `tokenmaxxxer/<old>-agent-rulebook` to `tokenmaxxxer/<new>-rulebook`, plugin/bundle names (e.g. `coding-agent-env` → `implementation-env`) renamed in lockstep with their role.

### 4. README.md / run.md / test fixtures
- README's role table (~lines 170-174) and inline old-name prose mentions updated to round-5 names.
- `run.md`: re-grep at execution time to confirm zero hits before treating as no-op (survey flagged this unconfirmed rather than assuming).
- Test fixtures: pass over `test_spawn.py`, `test_gates.py`, `test_approve_scope.py`, `test_vocab_coherence_roles.py` to confirm (or fix) any literal old-role-name string; `test_vocab_coherence_roles.py` already globs `roles/*.json` generically so is expected to need no change, confirmed at execution time rather than assumed here.

### 5. In-flight branch compatibility
Any branch already open as `issue-<n>/<old-role>` at merge time continues to resolve via `gates/gates.py`'s generic `roles/<role>.json` lookup **only if the old-name file still exists** — since this rename deletes those 9 files outright (no alias, per §2), an in-flight branch under an old role name would break at the next gate check after this merges. Mitigation: this PR's phase 2 checks `git branch -r` and open PRs for any live `issue-*/<old-role>` branch immediately before merging; if one exists, either (a) that branch's role session finishes and lands first, or (b) an explicit temporary passthrough `roles/<old-role>.json` (a one-line `{"alias_of": "<new-role>"}` stub, if `role_settings()` needs a one-line addition to follow it) is added and removed in a fast-follow once the branch lands — decided at execution time from the actual state, not speculated here. At authoring time (2026-07-31) no such branch is known to exist.

### 6. Historical record immutability
`docs/issue-*/reports/<old-role>.md` (and any other already-landed record under an old role name) is never renamed, moved, or rewritten by this or any future rename. History is not renamed — only the live `roles/*.json` and forward-looking references change. This rule is stated here as the proposal's explicit answer to the issue's ask; no code enforces it (nothing currently touches historical report files), so it is a process rule for future sessions to read, not a gate.

### 7. GitHub rulebook-repo rename — human command list (outside role-session authority)
Per the scout brief: `git clone`/`fetch`/`push` against a renamed GitHub repo keep working via redirect indefinitely (until the old name is reused), but the redirect is a safety net, not a substitute for updating `roles/*.json`/`marketplace.json` (already done in this repo per §1/§3 regardless of GH-rename timing). Recommended order: rename the JSON references first (this PR, once approved) — since clone continues to work through the old name via GitHub's own redirect during the gap — then perform the 9 GitHub renames at any convenient time after. Commands for a human with org admin rights to run (via `gh` CLI, one per repo):

```
gh repo rename implementation-rulebook       --repo tokenmaxxxer/coding-agent-rulebook
gh repo rename execution-observation-rulebook --repo tokenmaxxxer/qa-agent-rulebook
gh repo rename conformance-review-rulebook   --repo tokenmaxxxer/review-agent-rulebook
gh repo rename defect-verification-rulebook  --repo tokenmaxxxer/verify-agent-rulebook
gh repo rename release-engineering-rulebook  --repo tokenmaxxxer/ops-agent-rulebook
gh repo rename issue-retrospective-rulebook  --repo tokenmaxxxer/reflect-agent-rulebook
gh repo rename product-discovery-rulebook    --repo tokenmaxxxer/product-agent-rulebook
gh repo rename technical-feasibility-rulebook --repo tokenmaxxxer/feasibility-agent-rulebook
gh repo rename interaction-design-rulebook   --repo tokenmaxxxer/ux-design-rulebook
```
Each is independent (no cross-repo ordering constraint) — safe to run in any order, any time after this PR merges, without breaking `spawn.py`'s clone step at any point in between (redirect covers it).

## Out of scope
- Renaming the 34 not-yet-existing roles (round-3/4 promoted set) — separate issue per #162's own text.
- Executing the `roles/*.json`/`marketplace.json`/README/test edits, or the GitHub repo renames themselves — both wait for phase-2 Approve and human execution respectively.
- Re-deriving `decides`/`use_when`/`produces`/`write_scope` content — already settled and merged in issue-160's proposal; this proposal only sequences applying it.

## How you'll know it worked
- `python3 spawn.py <new-role-name> ...` resolves correctly for all 9 renamed roles; `python3 spawn.py <old-role-name> ...` fails with the existing generic "모르는 역할" error listing the new names.
- `gates/gates.py` accepts branches named `issue-<n>/<new-role-name>` and fails closed (already-existing behavior) on unknown role suffixes.
- `pytest test_spawn.py test_gates.py test_approve_scope.py test_vocab_coherence_roles.py` passes unchanged (or with only mechanical fixture-string updates, no logic changes).
- `grep -rn "agent-rulebook"` across the repo returns zero hits outside historical `docs/issue-*/` records.
