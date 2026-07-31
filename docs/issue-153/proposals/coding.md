# Build proposal — issue-153

files: `spawn.py` (`role_settings`, near the existing WebSearch/WebFetch
allow-list at spawn.py:419-428)

## Request (paraphrased intent, secrets stripped)

Spawned role sessions run headless (`--permission-mode acceptEdits`) with no
one to answer a permission prompt. Legitimate read-only tool calls that fall
outside the sandbox path the CLI-permission layer already knows about get
silently denied, and the session burns turns retrying in a different form.
Declare a default allow-list for read-only tool access in the spawn profile,
without touching the write/gate boundary.

## Constraints

- Must not widen the sandbox boundary (`sandbox.filesystem.allowRead/
  allowWrite/denyRead/denyWrite`) — that boundary is untouched by this
  change; only the CLI-permission layer (`permissions.allow`) changes.
- Must not create a gate-bypass path: no `Bash` command pattern is
  allow-listed, since `Bash(python3 -c:*)`-style patterns cannot be
  constrained to "read-only" (survey section 3).
- Must not touch `write_scope` (#149) — that stays the artifact-layer gate;
  this issue is the tool layer, per the issue's own framing.
- Applies to every role uniformly, same precedent as the #58/#65
  WebSearch/WebFetch fix at the same call site.

## What will be done

In `role_settings()`, at the same block that appends `WebSearch`/`WebFetch`
to `permissions.allow` (spawn.py:425-428), extend the loop to also include
`Read`, `Grep`, and `Glob`:

```python
allow = s.setdefault("permissions", {}).setdefault("allow", [])
for tool in ("WebSearch", "WebFetch", "Read", "Grep", "Glob"):
    if tool not in allow:
        allow.append(tool)
```

Update the existing comment above that block to state the extended
rationale (read-only tools, sandbox boundary still governs reachable paths)
rather than only WebSearch/WebFetch.

## Out of scope

- `Bash`-invoked read-only patterns (`python3 -c`, `ugrep`, `rg`, etc.) —
  survey found zero evidence of these in this repo's preserved logs; the
  issue's cited cases live in a sibling repo not surveyable here. Allow-
  listing arbitrary `Bash` sub-patterns as "read-only" is unsafe by
  construction (section 3) and needs its own evidence-backed, narrowly-
  scoped follow-up issue if the sibling repo's logs confirm a real pattern.
- Any change to `sandbox.filesystem.*` boundaries, or to `write_scope`
  (#149) — both stay exactly as they are.
- The 2 `Write` denials found (category c) — correctly gated, not this
  issue's target.

## How it'll know it worked

`test_spawn.py` gains one assertion: `role_settings("coding")["permissions"]
["allow"]` contains `Read`, `Grep`, `Glob` alongside the existing
`WebSearch`/`WebFetch`. Run once, must pass, before the PR.
