# Platform capabilities not derivable from this repo

This repo's gates (`gates/gates.py`, `gates/ci.py`) can only check what is
present in this repository's own tree. Some capabilities are properties of
the underlying platform (Claude Code) itself, not of this repo, and no
repo-local check can confirm or deny them — a survey that concludes "no
mechanism exists to do X" must check this file's pointer first, not just
this repo's own configured surface.

## Claude Code hook events

`on-the-record/hooks/hooks.json` currently configures three event types:
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `Stop`. Claude Code's
hook system supports more event types than these four — the authoritative,
current list lives in Claude Code's own documentation (not mirrored here,
since it would go stale the moment the platform adds an event this repo
hasn't configured). A survey concluding "no hook can observe X" is a claim
about this repo's *configured* `hooks.json`, not about the platform's
actual capability — those are different claims, and only the first is
mechanically checkable from this repo's tree.

This fact is stated once, here, as unchecked/unmechanizable — a platform
property, not a repo-derived claim. No gate in `gates/gates.py` claims to
verify it.
