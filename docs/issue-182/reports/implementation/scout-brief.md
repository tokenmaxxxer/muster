# Scout brief — issue #182

Mode: single-stage, this is internal-infra plumbing with no external
product category to compare against (no UI, no user-facing feature) — the
relevant "field" is the rulebook itself (tokenmaxxxer-core), which is a
local checkout, not a web search target. One targeted read of the actual
gate scripts substitutes for the sweep/deepen stages; no further rounds
would change the build decision (gate scripts are the ground truth for
what the env var must resolve to).

## Finding
Every core gate script sources gate-lib.sh via the exact pattern:
```
. "${CLAUDE_PLUGIN_ROOT_CORE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}/hooks/lib/gate-lib.sh"
```
(board-gate.sh:42, gate-lib.sh:13, and the same line appears in
gh-guard.sh, approval-gate.sh, handbook-trigger-gate.sh,
record-fields-gate.sh, trailer-gate.sh, directive.sh, role-directive.sh —
8 files, all identical shape).

This fixes the contract precisely: `CLAUDE_PLUGIN_ROOT_CORE` must be the
**core plugin's own root directory** (the dir containing `hooks/`), not
the parent checkout root and not `hooks/lib/`. That is exactly
`core_root() / "core"` in spawn.py terms — matches survey.md's reading of
`core_plugin_dirs()`.

## Must-be (single, non-negotiable)
The injected path must literally equal one of the `--plugin-dir` core
entries spawn.py already passes (spawn.py:1944-1945) — any drift between
"what plugin-dir loads the core plugin from" and "what
CLAUDE_PLUGIN_ROOT_CORE points at" reopens exactly the fail-open the
issue reports, just relocated.

## Gap line
Current state meets: nothing — the var is entirely absent (confirmed
survey.md). Missing: the var itself, and (separately) any doctor-time
check that a gate can actually resolve gate-lib and deny (ask #2).

Sources:
- /home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/board-gate.sh (local checkout, read directly)
- /home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/lib/gate-lib.sh (local checkout, read directly)
