files:
- core/hooks/board-gate.sh
- core/hooks/tests/run-board-gate-tests.sh (extend with new cases; this repo
  already uses a plain-shell-script test harness under `core/hooks/tests/`
  keyed one file per hook — `run-board-gate-tests.sh`, `run-approval-gate-tests.sh`,
  `run-gh-guard-tests.sh` — there is no bats framework present, so the new
  regression cases belong as additional `run`/`runb` invocations appended to
  the existing `run-board-gate-tests.sh`, matching its established pattern
  rather than introducing a new test file or framework)

## Request

Issue #40: `board-gate.sh`'s R5 ownership check falsely denies a Bash
`mkdir`/`rm` targeting a role's own record subpath
(`docs/issue-<n>/reports/<role>/`) as "belongs to another role," while a
`Write` tool call to a file inside that same subpath is allowed. The ask is
to make the ownership judgment consistent — a role's own subtree, including
the bare directory itself, must be treated as allowed regardless of which
tool is used to reach it — and to add a regression test that reproduces the
original false positive so it cannot silently return.

## Constraints

- Fail-closed behavior must not weaken: genuinely foreign records (e.g.
  `docs/issue-40/reports/otherrole`, or `docs/issue-40/reports/otherrole/x.md`)
  must still be denied.
- The fix must be minimal and confined to the R5 ownership loop in
  `board-gate.sh`. No behavioral change to R1–R4.
- No new test framework/dependency; extend the existing plain-shell harness in
  `core/hooks/tests/run-board-gate-tests.sh`.

## What will be done

In the R5 ownership loop's second `continue` condition, drop the `len(tail) >
1` requirement so it matches on the role directory alone:

```python
# before
if tail[0] == role and len(tail) > 1:
    continue

# after
if tail[0] == role:
    continue
```

This one-line change allows the bare own-subtree directory (`tail == [role]`,
e.g. from `mkdir docs/issue-40/reports/coding` or `rm -rf
docs/issue-40/reports/coding`) alongside anything deeper under it
(`tail == [role, ...]`, already allowed today), while leaving conditions 1 and
3, and the final `deny()` for any other role's directory, untouched. No other
line in R5 or in R1–R4 needs to change.

Optionally worth a follow-up note (not part of this fix): the WRITEISH regex
(`[>|`]|\$\(`) used for the read-only Bash fast-path also matches shell
fd-redirection like `2>&1`/`2>/dev/null`, causing plain reads with redirected
stderr to skip the fast path and fall through into the full
extraction/ownership pipeline unnecessarily. This does not itself produce a
false "belongs to another role" for a role's own path — it only causes a
redundant full pass that still resolves correctly for genuinely foreign
paths — so it's out of scope for this fix, but flagged for awareness.

## Out of scope

- The WRITEISH/fd-redirection regex quirk described above (it doesn't cause a
  false-positive on a role's own subtree by itself — see above — so fixing it
  is not required to close issue #40).
- Any broader refactor of `board-gate.sh`'s path-extraction or candidate logic.
- Any change to R1, R2, R3, or R4.

## How you'll know it worked

Add regression cases to `core/hooks/tests/run-board-gate-tests.sh`, using the
same invocation shape the file already establishes (`run`/`runb` helpers:
synthesize a `PreToolUse` JSON payload piped via stdin, with `CLAUDE_ROLE` and
the checked-out branch set via env, then assert the hook's exit code —
0 = allow, 2 = deny):

1. **Positive — bare own-subtree directory via Bash, `mkdir`.**
   `CLAUDE_ROLE=coding`, branch `issue-40/coding`, Bash tool_input command
   `mkdir -p docs/issue-40/reports/coding`. Expect exit 0 (allow).

2. **Positive — bare own-subtree directory via Bash, `rm`.**
   Same role/branch, Bash tool_input command
   `rm -rf docs/issue-40/reports/coding`. Expect exit 0 (allow).

3. **Negative — bare subtree directory belonging to another role.**
   Same role/branch, Bash tool_input command
   `mkdir -p docs/issue-40/reports/otherrole`. Expect exit 2 (deny), with
   stderr containing "belongs to another role."

4. **No-regression — existing file-inside-own-subtree write.**
   Same role/branch, `Write` tool_input `file_path` =
   `docs/issue-40/reports/coding/notes.md`. Expect exit 0 (allow), unchanged
   from current behavior — confirms the one-line change does not alter the
   already-passing case it's adjacent to.

Each case follows the existing `run`/`runb` helper convention already in
`run-board-gate-tests.sh`: build a synthetic project dir with a git repo,
canonical contract, and the target branch checked out; pipe a JSON payload of
the form `{"tool_name": "...", "tool_input": {...}, "cwd": "..."}` into
`board-gate.sh` via stdin with `CLAUDE_ROLE` (and `CLAUDE_PROJECT_DIR`,
`CLAUDE_PLUGIN_ROOT`) set in the environment; capture `$?` and map 0/2 to
allow/deny via the script's existing `report()` accounting. The test file
itself is not created in this phase — this is a phase-1 proposal only.
