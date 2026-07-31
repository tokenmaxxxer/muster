# Current-state survey — issue-162 (role rename execution ①)

## Scope recap
Issue #162 asks to execute step 1 of docs/issue-160/proposals/role-taxonomy.md's migration path (owner-approved via merged PR #161): rename the existing 9 `roles/*.json` files to the round-5 canon names, update every reference in this repo, and prep (but not execute) the 9 rulebook-repo GitHub renames.

## Inventory of touch points

**`roles/*.json` (9 files)** — `coding.json qa.json review.json verify.json ops.json reflect.json product.json feasibility.json ux-design.json`. Each has `marketplace`, `repo`, `path`, `decides`, `use_when`, `produces`, `write_scope`, `record_fields`. `repo`/`path` hardcode the old rulebook name (e.g. `tokenmaxxxer/coding-agent-rulebook`, `$TOKENMAXXXER_RULEBOOKS/coding-agent-rulebook`). `decides`/`use_when`/`produces` need narrowing per the round-5 table in the issue-160 proposal.

**`spawn.py`** — resolves role generically: `role_settings()` (spawn.py:317-336) loads `roles/<role>.json` by filename from `sys.argv`; on miss it already lists every known role name (`모르는 역할: {role} (있는 것: {have})`, spawn.py:332-333) — this generic fallback becomes the "old name → clear error naming the new one" behavior for free once the files are renamed, with no code change required in `role_settings()` itself. `rulebook_source()`/`rulebook_checkout()`/`ensure_rulebook()` read `spec["repo"]`/`spec["path"]` at runtime (spawn.py:141-291) and contain no hardcoded role/repo names — they clone whatever the (now-renamed) JSON says. **No `spawn.py` code change needed** beyond what naturally follows from the JSON renames — confirmed by reading, not assumed.

**`gates/gates.py`** — resolves the branch-prefix role the same generic way: splits `issue-<n>/<role>` (gates.py:506), loads `roles/<role>.json` (gates.py:314, 508), fails closed with a specific message if the role file doesn't exist or lacks `write_scope` (gates.py:510-515). **No hardcoded old-name string anywhere in gates.py** (grep confirmed) — again, renaming the JSON files is the entire fix here.

**`.claude-plugin/marketplace.json`** — 32 `"repo"` occurrences across per-role plugin blocks, each hardcoding `tokenmaxxxer/<old-name>-agent-rulebook` (e.g. 9 blocks reference `coding-agent-rulebook` including a `coding-agent-env` bundle name). These must be updated to the round-5 rulebook names to stay in lockstep with `roles/*.json` — a role file pointing at a renamed repo while marketplace.json still points at the pre-redirect name is an inconsistency the scout brief already flags as merely "safety-netted," not tolerated.

**`README.md`** — carries a prose role table (lines ~170-174) and inline mentions (`coding-cycle`, `qa-cycle`, "QA rulebook", "coding role", "coding's and qa's artifacts") that use the old names descriptively. Needs updating for accuracy, but is not load-bearing for any gate/script behavior.

**`run.md`** — no old-role-name hits found by grep; likely already uses generic `<role>` placeholders or wasn't matched by the exact-word grep used. Re-check narrowly at build time before assuming zero-touch.

**Test fixtures** — `test_spawn.py`, `test_gates.py`, `test_approve_scope.py`, `test_vocab_coherence_roles.py`, `tests/run-orchestrate-tests.sh`. `test_vocab_coherence_roles.py` globs `roles/*.json` generically (no hardcoded role-name literals found in the grepped region) — likely renames transparently, but each test file needs a pass to confirm no fixture hardcodes an old role string (e.g. a test that spawns `"coding"` literally to exercise `role_settings()`).

**Contract/protocol docs (`docs/specs/*`, this session's own SessionStart hook text)** — the role-handoff contract text itself is delivered by the `core`/`on-the-record` harness, not this repo's docs tree as far as this survey found; out of this issue's write set unless a repo-local copy exists (unconfirmed — flag as an open unknown, not a claim either way).

## Unknowns / open questions for the proposal
1. **Silent alias vs. hard error for old names** — resolved by scout brief: hard error, no alias (no in-flight execution history under old names to protect).
2. **In-flight branch compatibility** — the issue asks explicitly for a stance on `issue-<n>/<old-role>` branches already in progress. Since gates.py resolves role files generically and this repo has no currently-open issue branch under the pre-round-5 names (only `issue-162/coding` and recently-merged `issue-160`/`issue-161` work, all under still-valid current names), the practical exposure is low but the proposal must still state the rule for future safety.
3. **Historical record immutability** — `docs/issue-*/reports/<old-role>.md` files (e.g. any existing `docs/issue-*/reports/coding.md`) must never be renamed/rewritten to the new role name; this is a documentation/process rule, not a code change, and belongs in the proposal's explicit statement per the issue's own ask.
4. **GitHub rename ordering** — the 9 rulebook-repo renames are outside this session's execution authority (org/repo admin action); the proposal must supply the exact human-run command list and a sequencing rule (repo rename before/after `roles/*.json` merge) grounded in the scout brief's redirect-durability finding.
