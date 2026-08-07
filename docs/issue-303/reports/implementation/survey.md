# Survey — issue #303

## Scope note

Skip condition does not apply — this issue explicitly asks for a design (declaration channel shape), so the scout/survey path runs.

## The three lists, current state

1. `core_plugin_dirs()` (spawn.py:2179-2205) — **already converted**, before this issue. It reads `marketplace.json` under `core_root()` and fails loudly (`sys.exit`) if a declared plugin's directory is missing. Nothing to do here; issue #282 already landed this pattern. Confirmed by reading the function body and its docstring, which references #282 directly.

2. `RECORD_FIELDS_TERMINAL_STATES` (issue #147) — lives in `hooks/record-fields-gate.sh` **inside each rulebook plugin**, not in this repo. `grep -rn RECORD_FIELDS_TERMINAL_STATES` and `find . -iname record-fields-gate.sh` in this repo only find copies under `docs/issue-{167,170}/_assets/rulebook-skeleton/*/hooks/` — asset templates for a different issue's deliverable, not live gate code this repo owns or spawns from. There is no `spawn.py` list to convert for this one; the fix belongs to the rulebook-gate code in each consumer/rulebook repo, out of this repo's write set. **Follow-up, not converted here.**

3. `PACKAGE_REGISTRY_HOSTS` / `PACKAGE_CACHE_DIRS` (spawn.py:104-125) and the `allowRead` gap (spawn.py:433, 472-479) — live in `spawn.py`, owned by this repo, and are the write set for this issue.

## `role_settings()` merge order (spawn.py:390-520)

- `roles/<role>.json` is read; `sandbox.filesystem.{allowWrite,denyWrite,denyRead}` template-substituted from resolved env (spawn.py:433-439). `allowRead` is conspicuously **absent** from that key tuple — a role file cannot declare it today.
- If `sandbox.enabled`: `PACKAGE_REGISTRY_HOSTS` merged into `network.allowedDomains` (spawn.py:441-450).
- If `sandbox.enabled`: for each `(env_var, default_path)` in `PACKAGE_CACHE_DIRS`, if the resolved path exists on the host, it's appended to `sandbox.filesystem.allowRead` (spawn.py:472-479) — **the only writer of `allowRead` in the whole file**.
- None of the 43 `roles/*.json` files declare a `filesystem` block (confirmed by issue's own comment-3 measurement, and by `grep -L filesystem roles/*.json` returning all 43).

## Measurement 1 — is `allowRead` a whitelist or additive to default-allow?

Extracted from the installed Claude Code CLI binary (`/home/jwjung/.local/share/claude/versions/2.1.220`, v2.1.220) via `strings`/`grep -a`:

```
allowRead: array(v.string()).optional().describe(
  "Paths to re-allow reading within denyRead regions. Takes precedence over denyRead for matching paths.")
allowManagedReadPathsOnly: "When true (set in managed settings), only allowRead paths from policySettings are used."
```

and the resolved-config shape builder:
```
getFsReadConfig: ... return {denyOnly: e.filesystem.denyRead.map(...), allowWithinDeny: (e.filesystem.allowRead ?? []).map(...)}
```

**Observed answer: additive to default-allow.** The resolved filesystem-read policy is `{denyOnly, allowWithinDeny}` — everything is readable except `denyRead` entries, and `allowRead` re-permits specific paths *inside* a `denyRead` region. It only becomes an exhaustive whitelist when `allowManagedReadPathsOnly=true` is set in **managed** settings (an org-level lockdown flag) — `spawn.py` never sets this flag, and this session's own tool-permission block (visible in the Bash tool description this turn) is exactly this shape: `"read":{"denyOnly":["/home/jwjung/.claude/ide"]}`. This matches spawn.py's current usage: it only ever appends to `allowRead`, never sets `denyRead` for cache dirs, and the resolved `PACKAGE_CACHE_DIRS`/candidate read-path declaration is naturally an allow-list-of-exceptions model, not a full enumeration.

## Measurement 2 — does a workspace-internal symlink to an outside path resolve, or get refused?

Observed directly in this session's own sandboxed Bash tool (same `{denyOnly, allowWithinDeny}` mechanism, `denyOnly: ["/home/jwjung/.claude/ide"]`):

```
$ ln -sf /home/jwjung/.claude/ide symlink-to-denied
$ ls -la symlink-to-denied/
합계 4
drwxr-xr-x  2 jwjung jwjung   40  8월  7 13:18 .
drwxrwxr-x 16 jwjung jwjung 4096  8월  7 10:49 ..
```

**Observed answer: resolves.** A symlink from an allowed workspace path to a `denyRead`-listed path was followed and its contents were listed — the sandbox does not re-check `denyRead` against the symlink target. This means:
- for the 3.4 GB `onnx_models/` case, a symlink from inside the workspace to the real directory is an *immediate stopgap* available today, with no spawn.py change — worth stating to affected projects while the declaration channel is built.
- it also means the declaration channel, once built, must not be treated as the only enforcement boundary for `denyRead` — a determined workspace can already read past `denyRead` via a symlink. Widening `allowRead` via declaration is strictly no more permissive than what a symlink already allows; this is not a new risk introduced by this fix.

## `docs/specs/approvers.md` — the pattern this issue asks to mirror

A plain one-fact-per-line file the consumer repo owns and this orchestrator reads at spawn/approval time (`docs/specs/approvers.md`, two lines, `- <github-username>`). No schema versioning, no nested structure — precedent for keeping the new declaration file similarly flat.

## Write set (confirmed against the above)

- `spawn.py` — new declaration-file reader, merged as floor-not-ceiling into `PACKAGE_REGISTRY_HOSTS`/`PACKAGE_CACHE_DIRS`/new `allowRead` support in `role_settings()`; loud `sys.exit` on an unsatisfiable declaration.
- A new consumer-owned file convention, e.g. `docs/specs/sandbox-needs.json` (mirrors `docs/specs/approvers.md`'s ownership model, JSON because the declared shape — host lists, path lists — is structured, unlike approvers' flat name list).
- `docs/handbooks/` entry (or extend an existing spawn handbook if one exists) documenting the new declaration file for consumer repos — doctrine-ladder placement for a new config-key surface.
- Test file covering the new merge/fail-loud logic, if `tests/` already covers `role_settings()` (checked next, in the proposal).
