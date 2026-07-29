# Issue #40 — Survey: board-gate false-positive on Bash mkdir/rm of a role's own record subpath

## Scope

Phase-1 research only. No code changes in this commit.

## File(s) implementing the gate

- `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer-muster/runs/rulebooks/tokenmaxxxer-core/core/hooks/board-gate.sh`
- Mirrored at `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/board-gate.sh`

The gate is a `PreToolUse` hook. Its rule set is described in the header of
`core/hooks/tests/run-board-gate-tests.sh` as the "five deny-only rules of the
issue/PR interaction model (contract v3)":

- R1 — docs/ layout: README.md, the six buckets, or `issue-<n>/<bucket>`
- R2 — a board write requires the repo contract to hash-match the canonical
- R3 — a write under `docs/issue-<n>/` requires `CLAUDE_ROLE`
- R4 — a board write happens only on branch `issue-<n>/<role>`
- R5 — within `issue-<n>/reports/`, a role writes only its own record area

This survey concerns **R5**, implemented in the embedded Python
(`CORE_BOARD_GATE` heredoc) inside `board-gate.sh`.

## The R5 ownership loop

Near the end of the heredoc, after candidate paths under `docs/issue-<n>/` are
extracted into `issue_hits`, R5 is enforced with:

```python
for parts in issue_hits:
    if len(parts) < 3 or parts[1] != "reports":
        continue
    tail = parts[2:]
    owner_file = role + ".md"
    extra = EXTRA_SUBTREE.get(role)
    if tail[0] == owner_file and len(tail) == 1:
        continue
    if tail[0] == role and len(tail) > 1:
        continue
    if extra and tail[0] == extra:
        continue
    deny("docs/%s/reports/%s belongs to another role. ..." % ...)
```

Three `continue` (allow) conditions guard the fall-through `deny()`:

1. `tail[0] == owner_file and len(tail) == 1` — a bare per-role markdown file,
   e.g. `reports/coding.md`.
2. `tail[0] == role and len(tail) > 1` — something *inside* the role's own
   subtree directory, e.g. `reports/coding/notes.md` (tail = `["coding",
   "notes.md"]`, len 2).
3. `extra and tail[0] == extra` — an explicitly configured extra subtree for
   the role.

Anything not matched by one of these three falls through to `deny()`.

## Root cause

Condition 2 requires `len(tail) > 1`. It was written to match "a file inside
the role's own directory," but it never considers the case where the target
**is the bare subtree directory itself**, with nothing after it:
`docs/issue-<n>/reports/coding` → `tail == ["coding"]`, `len(tail) == 1`.

For that shape:
- Condition 1 fails: `tail[0]` is `"coding"`, not `"coding.md"`.
- Condition 2 fails: `len(tail) > 1` is false (`len(tail) == 1`).
- Condition 3 fails unless `coding` happens to be some other role's configured
  `extra` subtree (it isn't its own).

So it falls through to `deny("... belongs to another role ...")`, even though
`tail[0] == role` — i.e. it plainly *is* the role's own directory.

This is **not** two diverging code paths for Bash vs. Write. It is a single
incomplete condition in the R5 loop. The reason it manifests as a "Bash fails,
Write passes" asymmetry is purely about what *shapes* of `tail` each tool can
ever produce:

- A `Write` tool call always carries `tool_input.file_path` pointing at an
  actual file, e.g. `.../reports/coding/notes.md`. Extracted, this always
  yields `tail` with `len(tail) >= 2` (the role directory plus at least one
  filename segment). Write can **never** produce `tail == [role]` — there is
  no way for a file write to target a bare directory path. So Write always
  hits condition 2 and is allowed. It cannot exhibit the bug, not because its
  ownership logic is more correct, but because its input shape structurally
  avoids the len(tail)==1 case.
- A Bash `mkdir docs/issue-40/reports/coding` or `rm -rf
  docs/issue-40/reports/coding` targets the bare directory itself. Extracted,
  this yields `tail == ["coding"]`, `len(tail) == 1` — the exact case none of
  the three conditions cover. Bash is denied.

Adding one more path segment to the same Bash command (e.g. `mkdir -p
docs/issue-40/reports/coding/somefile`) already produces `tail = ["coding",
"somefile"]`, len 2, which condition 2 already allows — confirming the fix
target is precisely the `len(tail) == 1` boundary, not a Bash-vs-Write
divergence in path extraction.

## Secondary finding: WRITEISH regex catches shell fd-redirection

Separately, and only indirectly related, `board-gate.sh` uses a `WRITEISH`
regex (approximately `[>|`]|\$\(`) to fast-path plain read-only Bash commands
(e.g. `ls`, `cat`) around the full extraction/ownership pipeline. This regex
matches any `>` character, including shell **file-descriptor redirection**
that has nothing to do with writing a file — `2>&1`, `2>/dev/null`, etc.

Concretely: `ls docs/issue-40/reports/coding 2>&1` is a read-only command, but
because it contains `2>&1`, the WRITEISH regex flags it as write-ish, the
read-only fast path is skipped, and the command falls through into the full
candidate-extraction / R5 ownership check — which, given the root cause
above, then wrongly denies it with "belongs to another role." This was
confirmed live: `ls docs/issue-40/reports/coding 2>&1` from within this
session was denied by board-gate for exactly this reason.

This regex quirk is a secondary, contributing issue: it's why a plain `ls`
with a redirected stderr can be denied at all (it should never have reached
the ownership check in the first place), but the primary defect — the actual
false "belongs to another role" outcome for a role's own bare subtree — is
the `len(tail) > 1` condition described above, and would still misfire on
`mkdir`/`rm` even without any stderr redirection present.

## Minimal repro

Run as `CLAUDE_ROLE=coding` on branch `issue-40/coding`, from the project root
containing a `docs/issue-40/reports/` bucket:

```bash
mkdir -p docs/issue-40/reports/coding
# → denied by board-gate: "belongs to another role"

rm -rf docs/issue-40/reports/coding
# → also denied by board-gate: "belongs to another role"
```

Meanwhile, on the identical branch/role, a `Write` tool call to
`docs/issue-40/reports/coding/x.md` succeeds — because, as explained above,
its `tail` always has `len(tail) >= 2` and therefore always hits condition 2.
