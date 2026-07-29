# Issue #83 — Phase 1 Proposal (coding)

files:
- `.claude-plugin/marketplace.json`
- `orchestrate/` -> moved to `on-the-record/` (`.claude-plugin/plugin.json`, `commands/run.md`, `hooks/hooks.json`, `hooks/deliverable-guard.sh`, `hooks/directive.sh`, `hooks/self-update.sh`)
- `README.md`, `README.ko.md`, `protocol.md`, `protocol.ko.md`
- `spawn.py`, `wakes.py`, `test_gates.py`, `test_spawn.py`, `bench/run.py`

## Request

Rebrand the muster stack as on-the-record: marketplace `name` `tokenmaxxxer-muster` -> `tokenmaxxxer`; plugin `orchestrate` -> `on-the-record` (directory move, `plugin.json` name, `/orchestrate:run` -> `/on-the-record:run`, hardcoded marketplace dir in `directive.sh`/`self-update.sh`); sweep remaining `muster` mentions in README/protocol docs and spawn.py/wakes.py/test/bench message strings. GitHub repo rename (`tokenmaxxxer/muster` -> `tokenmaxxxer/on-the-record`) is a user-side action, noted in the PR only.

## Constraints

- Historical records (`docs/issue-*/`, `docs/reports/*.md`, `docs/proposals/*.md`, `docs/superpowers/*`, `runs/observed/*`) are untouched — they describe the system as it was at the time, and rewriting them would falsify history.
- Internal test-fixture strings that are arbitrary placeholders, not product-name mentions (`Path(td) / "muster"` in test_gates.py, `/nonexistent/muster`, `muster-issue-38-test` in test_spawn.py, `.muster-cache` directory name in spawn.py) are left as-is — they are not "muster" the product name, and renaming them risks unrelated churn (stale `.gitignore`/exclude entries, fixture-path drift) without being what issue #83 asks for ("mentions" in messages).
- A citation-comment in test_spawn.py pointing at a real historical report filename (`docs/reports/2026-07-29-hunt-muster-role-model-build.md`) is left verbatim — it's a filename reference, not a mention to rename.
- No file under any `core/` path or other rulebook repo is touched.
- Install-string/command examples (`claude plugin marketplace add ...`, `/orchestrate:run` -> `/on-the-record:run`) are updated exactly, since these are literal commands users run.

## What will be done

1. `.claude-plugin/marketplace.json`: `name` -> `"tokenmaxxxer"`; the `orchestrate` plugin entry -> `name: "on-the-record"`, `source: "./on-the-record"`.
2. `git mv orchestrate on-the-record`; inside it, `.claude-plugin/plugin.json` `name` -> `"on-the-record"`; `hooks/directive.sh` and `hooks/self-update.sh`'s hardcoded `mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer-muster"` -> `tokenmaxxxer`; `commands/run.md` prose/example commands updated (`/orchestrate:run` -> `/on-the-record:run`, install strings).
3. `README.md`, `README.ko.md`, `protocol.md`, `protocol.ko.md`: sweep all `muster` (system name) -> `on-the-record`, `orchestrate` (plugin/slash-prefix) -> `on-the-record`, `tokenmaxxxer-muster` -> `tokenmaxxxer`, `tokenmaxxxer/muster` (repo slug) -> `tokenmaxxxer/on-the-record`.
4. `spawn.py`: rename product-name prose mentions of "muster" (Korean docstrings/comments/log lines, PR body text at line ~1594, log line ~1628) to "on-the-record"; leave `.muster-cache` directory name and the `"muster-probe"` payload field as internal identifiers out of scope.
5. `wakes.py:99`, `bench/run.py:7`: rename the one prose mention each.
6. `test_gates.py`, `test_spawn.py`: rename product-name prose mentions only; leave fixture placeholder paths/strings as noted in Constraints.
7. Add a note in the PR description that the GitHub repo rename (`tokenmaxxxer/muster` -> `tokenmaxxxer/on-the-record`) is a user-side follow-up, not performed here.

## Out of scope

- Historical docs/runs listed in Constraints.
- Other rulebook repos.
- The actual GitHub repo rename.

## How you'll know it worked

- `grep -rn "muster\|orchestrate" .` (excluding `runs/observed/`, `docs/issue-*/`, `docs/reports/`, `docs/proposals/`, `docs/superpowers/`, `.git/`, and the noted internal-fixture exceptions) returns nothing.
- `python3 -m py_compile spawn.py wakes.py` and existing test suites (`test_gates.py`, `test_spawn.py`) still pass after the rename (no path/string breakage from the `orchestrate/` -> `on-the-record/` move).
- `.claude-plugin/marketplace.json` is valid JSON with the updated `name`/plugin entry.
