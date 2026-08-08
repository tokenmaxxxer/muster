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
