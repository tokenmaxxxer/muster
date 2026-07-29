# Issue #83 — Current-State Survey (phase 1)

Scope: rename repo `muster` -> `on-the-record`, marketplace name -> `tokenmaxxxer`, plugin `orchestrate` -> `on-the-record`, per issue #83.

## 1. Marketplace manifest

`.claude-plugin/marketplace.json`:
- top-level `name`: `"tokenmaxxxer-muster"` -> `"tokenmaxxxer"`.
- plugin entry `name: "orchestrate"`, `source: "./orchestrate"` -> `name: "on-the-record"`, `source: "./on-the-record"`. Description text is generic (no `muster`/`orchestrate` mention) — untouched.

## 2. `orchestrate/` directory contents (to move -> `on-the-record/`)

```
orchestrate/.claude-plugin/plugin.json   — "name": "orchestrate" -> "on-the-record"
orchestrate/commands/run.md              — prose + example commands reference /orchestrate:run, muster
orchestrate/hooks/hooks.json             — no orchestrate/muster text, only ${CLAUDE_PLUGIN_ROOT} refs (path-relative, unaffected by rename)
orchestrate/hooks/deliverable-guard.sh   — grep shows no muster/orchestrate hits
orchestrate/hooks/directive.sh           — hardcoded marketplace dir `$HOME/.claude/plugins/marketplaces/tokenmaxxxer-muster`
orchestrate/hooks/self-update.sh         — same hardcoded marketplace dir
```

`directive.sh:28` and `self-update.sh:22` both hardcode `mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer-muster"` — must become `tokenmaxxxer` (the marketplace dir name follows the marketplace `name` field, not the repo name).

## 3. `spawn.py` (repo root, not moved)

No `orchestrate` references. Heavy `muster` usage in Korean docstrings/comments/messages (prose referring to "muster" as the system) and in path-ish identifiers: `.muster-cache` (cache dir name), `"muster-probe"` (a hardcoded name field in a probe payload), `"muster 소유 클론"` prose. `.muster-cache` is a directory name written into `.git/info/exclude` and used as a cwd — it is not user-facing installer content, but issue #83 says "sweep remaining muster mentions in README/docs/spawn.py messages," which covers spawn.py's user-facing message strings (docstrings, log/PR body text), not necessarily internal cache directory naming. Decision: rename the prose/message occurrences of "muster" (the system's name in Korean sentences, PR body text at line 1594, log line 1628) to "on-the-record"; leave `.muster-cache` as an internal directory-name identifier out of scope (renaming a cache dir isn't a "mention" the issue is describing, and touching it risks stale `.gitignore`/`.git/info/exclude` entries on existing checkouts). Flagging this line for the approver in the proposal.

## 4. README.md / README.ko.md / protocol.md / protocol.ko.md

All four files use `muster` as the system's name throughout prose (headers, install commands `claude plugin marketplace add tokenmaxxxer/muster`, `claude plugin install orchestrate@tokenmaxxxer-muster`, directory-listing line `orchestrate/  ...`, references to `/orchestrate:run`). These need a full sweep: `muster` -> `on-the-record`, `orchestrate` (as plugin name/slash-command prefix) -> `on-the-record`, `tokenmaxxxer-muster` -> `tokenmaxxxer`, `tokenmaxxxer/muster` (repo slug) -> `tokenmaxxxer/on-the-record`.

## 5. `wakes.py`, `test_gates.py`, `test_spawn.py`, `bench/run.py`

- `wakes.py:99` — one Korean prose mention ("관찰 기록은 muster 안에 산다") -> "on-the-record".
- `test_gates.py` — prose mentions ("muster 자체 점검", "muster 의 진짜 runs/", test tmp path `Path(td) / "muster"`, warning text). The tmp path is an internal test fixture name, not a repo/plugin identifier — cosmetic only if changed; low priority, can leave or rename for consistency (proposal will rename the prose, leave the fixture path since it's arbitrary and not "muster" the product).
- `test_spawn.py` — prose mentions and placeholder paths (`/nonexistent/muster`, `muster-issue-38-test`) — same as above, internal fixture strings not depicting the product name; leave those, sweep the docstring prose reference in the citation-comment (line 234) which itself is just a pointer to a historical report filename (`docs/reports/2026-07-29-hunt-muster-role-model-build.md`) and must NOT be renamed since it points to a real historical filename.
- `bench/run.py:7` — one Korean prose mention ("러너를 muster 에") -> "on-the-record".

## 6. Explicitly out of scope (per issue #83)

- `runs/observed/` historical filenames containing `muster-issue-*` — untouched.
- `docs/issue-*/`, `docs/reports/*.md`, `docs/proposals/*.md`, `docs/superpowers/*` — these are historical, point-in-time records of past issues/decisions (their own body text describing what existed at the time); rewriting "muster" inside them would falsify history the same way editing `runs/observed/` would. Not swept.
- Other rulebook repos (`*-agent-rulebook`, `tokenmaxxxer-core`) — separate repositories, out of this issue.
- The GitHub repo rename itself (`tokenmaxxxer/muster` -> `tokenmaxxxer/on-the-record`) is a user-side action; this PR only notes it, does not perform it.
