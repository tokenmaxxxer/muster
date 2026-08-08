---
proposal: docs/issue-523/proposals/2026-08-09-technical-writing-devrel-write-scope-split.md
---

# Hunt record — technical-writing-devrel-write-scope-split

## after-proposal — stance 1: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — proposal's acceptance check #2 (`bash scripts/check-write-set-conflicts.sh`) never reads `roles/*.json` or `write_scope` at all, so it cannot detect the write_scope collision the proposal is trying to fix; the real (and only) collision check is proposal step 1's ad-hoc python one-liner, and no CI/gate mechanism re-runs an equivalent check after this phase-1 PR merges.
Kind: design-error
Seed: docs/issue-523/proposals/2026-08-09-technical-writing-devrel-write-scope-split.md (git diff --stat main...issue-523/implementation: two new docs files, no code changed)
cap_seconds: 60
tier: default (docs-only, diff under docs/ only)
diff_stat_lines: 2 files changed (docs-only)
started_at: 2026-08-09T01:24:10+09:00
ended_at: 2026-08-09T01:24:35+09:00

### Reproduce
```
grep -n "roles/" scripts/check-write-set-conflicts.sh
# -> no output at all
grep -n "write_scope" scripts/check-write-set-conflicts.sh
# -> no output at all
```
`scripts/check-write-set-conflicts.sh`'s `main`/`check_conflicts`/`parse_files_frontmatter` only compare the `files:` YAML frontmatter block of proposal markdown files across issues with currently-open PRs (via `find_open_issue_proposals`, itself driven by `gh pr list`). It has zero code path that opens `roles/technical-writing.json` or `roles/devrel.json`, so running it can never surface an identical/overlapping `write_scope` between those two role files — including the exact collision (`["docs/**"] == ["docs/**"]`) that this proposal exists to fix.

The only place that actually enforces `write_scope` against real file writes is `gates/gates.py:846` (`write_scope 이탈` check), and that function checks a *single* role's diff against its *own* declared `write_scope` — it never compares two roles' `write_scope` lists for overlap, so it would not have caught the identical-scope problem either. The proposal's step 1 python one-liner is therefore the only actual collision detector, and it is a manual command run once at proposal time, not a gate wired into CI (grep of `gates/ci.py` shows no reference to this comparison).

### Expected
Either (a) the proposal's acceptance check #2 should name a script that actually inspects `roles/*.json` `write_scope` fields for pairwise overlap (the named `check-write-set-conflicts.sh` does not, and grep confirms it has no `roles/` or `write_scope` string anywhere in its 127 lines), or (b) the proposal should acknowledge that disjointness is enforced only by a one-off manual command with no CI wiring, so a future edit reintroducing `["docs/**"]` in either role file would go undetected by any automated gate.

## before-landing — stance 1 (index 0 mod 5): assume the gate just touched is bypassable — find the bypass

Verdict: FINDING -- the write_scope check in gates/gates.py uses `fnmatch.fnmatch`, whose `*` matches path separators too (fnmatch has no path-separator semantics), so `role_scope()`'s always-on `_always_writable()` allowances (the always-writable "proposals" and "reports/<role>" globs, rooted at the issue-tree prefix) let any role -- including the newly-restricted technical-writing and devrel roles -- write into a path where an extra directory segment (matching the OTHER role's declared directory name) has been inserted before "proposals/", defeating the disjointness this diff claims to establish.
Kind: composition
Seed: roles/technical-writing.json, roles/devrel.json (write_scope now split into disjoint "guides" vs "devrel" globs); enforcement in gates/gates.py `role_scope()` (line ~845) and `_always_writable()` (line ~825)
cap_seconds: 60
tier: default (diff is 4 lines across roles/technical-writing.json and roles/devrel.json)
diff_stat_lines: 4
started_at: 2026-08-09T02:05:00+09:00
ended_at: 2026-08-09T02:10:30+09:00

### Reproduce
Pure fnmatch semantics check, no file writes involved:
```
python3 - <<'PYEOF'
import fnmatch
ISSUE_PREFIX = "ISSUE_DIR"  # stands for the real issue-tree root segment used by _always_writable()
always_writable_proposals_glob = ISSUE_PREFIX + "/*/proposals/**"
candidate_path = ISSUE_PREFIX + "/OTHER_ROLE_DIR/proposals/evil.md"
print(candidate_path, "->", fnmatch.fnmatch(candidate_path, always_writable_proposals_glob))
PYEOF
```

### Observed
```
ISSUE_DIR/OTHER_ROLE_DIR/proposals/evil.md -> True
```
`_always_writable(role)` in `gates/gates.py` returns an issue-tree-rooted "proposals" glob unconditionally for every role, and `role_scope()` unions it into `allowed` after the role's declared write_scope is applied (`allowed = allowed + _always_writable(role)`). Because `fnmatch.fnmatch`'s `*` also matches literal `/` characters, the wildcard segment absorbs any number of extra path components, including a literal directory name reserved for the OTHER role. A technical-writing-branch PR can therefore add a file at a path whose first component after the issue directory is the exact directory name this diff carved out as devrel-exclusive, followed by "proposals/<file>", and `role_scope()` reports zero write_scope violations for it -- even though that directory segment is precisely what the diff was written to keep out of technical-writing's reach. The same escape applies symmetrically the other direction, and for any role via the analogous "reports/<role>/**" always-writable pattern combined with an extra path segment.

### Expected
`role_scope()`'s always-writable union should be enforced against the true issue-tree structure (e.g. no intervening path segments allowed between the issue directory and "proposals/", or match path components explicitly instead of running fnmatch on the raw string) so a file cannot claim the "proposals is always writable" exemption by nesting an arbitrary extra directory -- including the other role's declared-scope directory name -- in front of "proposals/". As written, the new disjoint write_scope in roles/technical-writing.json and roles/devrel.json is bypassable through this always-writable carve-out, and the same bug affects every role's write_scope, not just these two.
