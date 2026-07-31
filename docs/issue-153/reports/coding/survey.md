# Survey — issue-153: spawned-session permission profile

## Scope skip record

Not applicable — this is a survey/proposal issue, not a pure bugfix, and a
design decision (which read-only patterns to allow-list, at which layer) is
open. Scout ran conceptually as "read the deciding code + classify the
evidence"; there is no external product category to benchmark against for an
internal permission-profile fix, so no web sweep was run — the field here is
`spawn.py` itself and the preserved session logs.

## 1. Where the spawned session's permission profile is decided

Single place: `spawn.py::role_settings(role)` (spawn.py:317-440), invoked
once per spawn to build the `--settings` payload merged over
`~/.claude/settings.json` (merge, not replace — confirmed by the existing
"전역 플러그인은 전부 끈다" block at spawn.py:409-417, which exists *because*
`--settings` merges).

Two independent layers, both built here, both must allow a call before it
runs:

- **Sandbox layer** — `sandbox.filesystem.{allowRead,allowWrite,denyRead,
  denyWrite}`, taken from the role's `roles/<role>.json` `sandbox` key and
  expanded (spawn.py:359-407). This is the boundary — what paths exist to
  the process at all.
- **CLI permission-prompt layer** — `permissions.allow`, a separate list
  spawn.py already appends to today, but only for two tools:
  `WebSearch`/`WebFetch` (spawn.py:419-428), fixed in #58/#65. The comment
  at spawn.py:421-422 states the mechanism precisely: headless sessions run
  `--permission-mode acceptEdits` with no one to answer a prompt, so **any
  tool call with no matching `permissions.allow` rule is silently denied**,
  regardless of what the sandbox layer would have allowed.

`roles/<role>.json` values flow straight into settings via
`s = {k: v for k, v in spec.items() if k not in ("marketplace","path","repo")}`
(spawn.py:336) — a role file could already declare a top-level
`"permissions"` key and it would merge exactly like `"sandbox"` does. No role
file does today (`roles/coding.json` inspected; no `permissions` key).
Target repo `.claude/` and CLI defaults were not found to matter here: the
denial happens before any repo-level hook or gate runs — it is the outer
CLI-permission layer, not `gates/*.py` or repo hooks.

## 2. Preserved-log denial census

Searched all 91 preserved `*.session.log` files under
`/home/jwjung/.tokenmaxxxer/work/` (JSONL transcripts) for `tool_result`
entries with `is_error: true` whose content is the CLI's
`"Claude requested permissions to ... but you haven't granted it yet."`
message, correlated back to the originating `tool_use` by `tool_use_id`.

**13 denial events found, across 11 session logs.** Full breakdown:

| tool | count | target | classification |
|---|---|---|---|
| Read | 11 | `record-fields-gate.sh` (×6, across 5 different sibling worktrees/plugin-marketplace paths), `board-gate.sh` (×1), `trailer-gate.sh` (×1), `finding-record-template.md` (×1), a sibling role's `reports/coding.md` (×1), a sibling role's `record-fields-gate.sh` under a different worktree (×1) | **(b) read-only, blocked** |
| Write | 2 | `/tmp/claude/extract_denials.py`, `/tmp/claude-1000/repro/orchestrator.py` | **(c) write, blocked by a non-gate permission (path outside the scratchpad allow-list)** |

Classification detail:

- **(a) gate's intended denial (board-gate etc.)**: **zero found.** No
  `PreToolUse` hook `deny`/`block` decision appears in any of the 91 logs
  (searched for `"decision":"block"`, `permissionDecision*deny`, the literal
  string `"deny"` — no hits). Every denial in this dataset is the CLI
  permission-prompt layer, not a repo gate script exiting non-zero.
- **(b) read-only, blocked**: all 11 `Read` denials. Each is a `Read` tool
  call at a fully-qualified path — mostly a hook script the session wanted
  to inspect (`record-fields-gate.sh`, `board-gate.sh`, `trailer-gate.sh`)
  living in a *different* checkout than the session's own working directory:
  a sibling role's worktree under `~/.tokenmaxxxer/work/`, or the plugin
  marketplace cache under `~/.claude/plugins/marketplaces/`. These are
  read-only by construction (the `Read` tool cannot write) and the paths sit
  outside whatever `sandbox.filesystem.allowRead` the spawning role declared
  for its *own* working tree — so the CLI prompt layer, not the sandbox
  boundary, is what actually stopped them.
- **(c) write, non-gate**: both `Write` denials target paths under `/tmp/`
  that are not the session's assigned scratchpad directory
  (`/tmp/claude-1000/<session>/scratchpad/...`) — i.e. legitimately
  out-of-scope writes, correctly stopped, just not by a role/board gate.

**Limitation, stated plainly**: the issue text cites `python3 -c` schema
reads and `ugrep` invocations as recurring denied patterns. Zero `Bash`
denials of any kind appear in this log set — every denial found is `Read` or
`Write`. The `python3 -c`/`ugrep` cases the issue references most likely
live in the sibling `외부 프로젝트` repo's own preserved
logs, which are not present on this host/session and could not be surveyed
here. The allow-list below is scoped to what this survey actually evidenced
(`Read`-tool denials); it does not extend to `Bash`-invoked read-only
patterns, for the reason given in section 3.

## 3. Side-effect check (mandatory per issue #3)

Widening `permissions.allow` for **dedicated read-only tools** (`Read`,
`Grep`, `Glob`) is safe as a gate-bypass vector: none of the three can write,
execute, or mutate state — the sandbox's `allowRead`/`denyRead` boundary
still fully governs *which* paths they can reach, and `write_scope` (#149)
still governs writes independently. Allow-listing them at the CLI-permission
layer does not touch either of those; it only removes a redundant second
prompt for calls the sandbox would already let through.

Widening it for **`Bash` command patterns** (e.g. `python3 -c:*`, `rg:*`) is
NOT safe to do generically: `python3 -c` is Turing-complete — a pattern that
allows it "for read-only schema queries" allows it for everything, including
writes and network calls, i.e. exactly the "disguised write" the issue warns
about in item 3. This survey found no evidence in-repo of *which* narrow
Bash sub-patterns are actually needed, so the proposal does not allow-list
any `Bash` pattern; that is deferred pending real denial evidence (see
proposal's Out of scope).

## Sources

- `spawn.py:317-440` (`role_settings`), read directly.
- `roles/coding.json`, read directly.
- 91 files under `/home/jwjung/.tokenmaxxxer/work/*.session.log`, grepped/parsed with a one-off script (not committed — analysis only).
- `docs/issue-58/...`, `docs/issue-65/...`, `docs/issue-149/reports/coding/survey.md` — prior art for `permissions.allow` and `write_scope`, referenced via spawn.py's own comments.
