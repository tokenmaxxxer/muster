# Survey — issue #323

## Scope of the write set the eventual build will touch

- `docs/specs/parallel-conflict-methodology.md` — new spec: the methodology itself.
- `scripts/check-write-set-conflicts.sh` (or equivalent) — the executable acceptance artifact.
- `test/check-write-set-conflicts.test.sh` (or under whatever test harness this repo's scripts use) — a test fixturing an unresolved overlap and asserting the checker fails on it.
- `docs/handbooks/operations.md` — one cross-reference line, if the checker needs to run as part of an existing operational step (e.g. before merge).

## Current state

- The role-handoff contract (v3, injected this session) already gives each role session an isolated worktree/branch (`issue-<n>/<role>`) and a frozen write set per phase-1 proposal (`files:` frontmatter). This is the raw material a conflict-detection mechanism needs — write sets already exist on disk, per proposal, before phase 2 starts.
- `docs/specs/` holds no document about cross-session conflict handling. `git log`/`ls docs/specs` (flows-schema.md, approvers.md, two proposal-adjacent docs) confirms nothing here addresses it.
- No `.agents/` coordination directory or equivalent exists in this repo.
- Two general-purpose skills are already installed and available to any session: `agent-coordination` (claims.json / conflicts / resolutions protocol, heartbeat-based liveness, self-merge) and `merge-gates` (four-property gate shape test, combined-state requirement, fail-open audit). Both are generic — written for arbitrary git-writing agents, not specifically for this repo's role-session model (proposal-gated write sets, PR-mediated landing via human Approve, not self-merge).
- Sibling issue #324 ("independent work is serialized... partly because conflict handling is unsolved") depends on this issue's methodology but is filed separately — per operator item 7, do not fold it in here. This issue's boundary: define and mechanically check the conflict methodology; #324's boundary: use it to justify running things in parallel. Nothing in this proposal touches orchestrator scheduling behavior.
- #298 documents that the orchestrator itself is under-enforced (1 gate vs. 8+ for role sessions) — relevant only as a caution: any conflict-methodology gate proposed here must be a role/session-side mechanical check (like the existing `board-gate`, `trailer-gate`), not another orchestrator-side promise.
- #310's constraint governs acceptance: a prose methodology alone does not discharge the issue. There must be a script/test that fails when two overlapping write-set claims exist unresolved.

## Gaps the proposal must close

1. **Adaptation gap**: `agent-coordination`'s self-merge and heartbeat-file protocol assumes agents merge themselves; this repo's roles land only through human-approved PRs (contract v3 s19). The methodology has to be rewritten in this repo's terms — proposal `files:` frontmatter as the claim, open PRs as the liveness signal (an open PR branch is "in flight") — not copied verbatim.
2. **Enforcement gap**: nothing today mechanically flags two open PRs (any role, any issue) whose frozen write sets overlap. This is the acceptance artifact #310 demands.
3. **Recording gap**: when an overlap is found, there is currently no place to record how it was resolved (analogous to `agent-coordination`'s `.agents/resolutions/`). The methodology needs a document location for this, scoped under `docs/`, not a new top-level directory (per this repo's `docs/`-only-document rule from contract v3).
