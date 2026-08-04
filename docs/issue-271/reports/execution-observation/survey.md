# Current-state survey — issue #271, step 2 (execution-observation)

Phase 1 artifact (role-handoff contract v3 §19). Descriptive only: this
file records what exists and what was read, not how it is judged. No
judgment of the observed work appears here; that belongs to phase 2.

## 1. Scope under observation — named, not "recent work"

| Field | Value |
|---|---|
| Issue | **#271** — "자동 종결 트리거 표면 전수 커버 + phase 술어 분리" (state: OPEN, author jjongkwann, 1 comment) |
| Observed role | **implementation** (issue #271 execution plan, step 1) |
| Observed session | the single 2026-08-04 session that produced branch `issue-271/implementation`, commits authored 05:10:05Z → 05:58:01Z, force-pushed 05:58:07Z |
| Observed PR | **#273** — `[issue-271/implementation]`, `issue-271/implementation` → `main`, author jjongkwann, **MERGED** 2026-08-04T06:00:21Z, merge commit `c6c4363`, `reviews: []`, `comments: []` (`gh pr view 273 --json ...`, this session) |
| Observer | this session, role **execution-observation**, branch `issue-271/execution-observation`, forked from `c6c4363` |
| Not in scope | issues #245 / #262 / #266 themselves — they appear only as the cited provenance of #271's requirements, and their own observation records already landed (PRs #268/#269/#270, visible in `git log`). |

## 2. What was read this session (primary evidence only)

Everything below was read directly in this session — no secondhand
summary, nothing inferred from the issue title.

- `gh issue view 271` (body + execution plan) and `gh issue view 271
  --comments` → exactly one comment, body `APPROVE issue-271/implementation`,
  author `jjongkwann`, association `member`.
- `docs/specs/approvers.md` → `JiwonJung94`, `jjongkwann`.
- `gh pr view 273 --json number,title,author,state,mergedAt,mergeCommit,headRefName,baseRefName,url,reviews,comments`.
- `gh api repos/tokenmaxxxer/on-the-record/pulls/273/commits` → the four
  branch commits, all SHAs below confirmed present on `main` via `git log`:
  - `ddc9b0f` 05:10:05Z — phase 1: survey + scout brief + proposal (600 insertions, docs only)
  - `6cd0ef2` 05:31:27Z — phase 2 open: record skeleton (`loop_state: in-progress`)
  - `1cab34b` 05:45:58Z — phase 2 delivery (6 files, +667/−98)
  - `e2bac95` 05:58:01Z — post-landing rebase record (`docs/issue-271/reports/implementation.md` only, +22)
- `gh api repos/.../issues/273/timeline` → four `committed` events, **one**
  `head_ref_force_pushed` at 05:58:07Z pointing at `e2bac95`, `merged`
  06:00:21Z, `head_ref_deleted` 06:00:23Z. No `reviewed` event of any kind.
- `git diff 1d7df88 c6c4363 --stat` → the landed delta:
  `docs/handbooks/operations.md` (28), `docs/issue-271/decisions/...` (86),
  `docs/issue-271/proposals/...` (259), `docs/issue-271/reports/implementation.md` (233),
  `.../implementation/scout-brief.md` (81), `.../implementation/survey.md` (260),
  `gates/ci.py` (154), `gates/test_closes_gate_ci.py` (284), `test_spawn.py` (24)
  — 9 files, +1323/−86. **`spawn.py` is absent from the delta.**
- The observed role's own record, in full: `docs/issue-271/reports/implementation.md`
  (233 lines, `loop_state: landed`, 7 `closed_checks`, sections Why /
  What was done / What did not work / Rationale for deviations /
  Doc-placement ladder / Hunt / Next steps / Open-finding resolution path).
- The full `gates/ci.py` hunk set of `1cab34b`, the added/removed test
  function names of `gates/test_closes_gate_ci.py` in the same commit, the
  complete `test_spawn.py` and `docs/handbooks/operations.md` deltas, and
  the observed role's proposal trigger-surface inventory table (rows A–H)
  at `c6c4363`.
- `git show --format=... 9d1394f` — issue #247's phase-2 commit, the change
  this branch was rebased over.

## 3. Observation surfaces and their unknowns

The "write surfaces" for this role are the artifacts a verdict would have
to rest on. Each is listed with what is already established from the
reads above and what is still unknown at survey time.

| # | Surface | Established | Unknown at survey time |
|---|---|---|---|
| S1 | `gates/ci.py` @ `1cab34b` — `_issue_and_role_from_branch`, `_pr_title`, `_pr_commit_messages`, `_pr_reviews`, `_phase_from_approval`, `_phase1_surface_mismatch`, rewired `_autodetect_issue_phase` / `check()` | Hunks read in full; `_phase_from_body` / `_issue_from_branch` removed; three surfaces threaded into the `phase == "phase1"` branch; each of the three fetches fails closed | Whether `_phase_from_approval`'s use of `spawn._issue_comments(repo, pr)` alongside `(repo, issue)` matches contract v3 §19's single-account path (which names an **issue-level** comment); whether anchoring the branch regex to `^issue-(\d+)/([^/]+)$` changes the accepted-branch set versus the prior unanchored `^issue-(\d+)/` |
| S2 | `gates/test_closes_gate_ci.py` @ `1cab34b` | Test-function names read: 5 `_phase_from_approval` cases, 4 `_phase1_surface_mismatch` cases, `t_pr_commit_messages_paginates_and_flattens`, and the two `t_autodetect_*` cases named as the reachability and requirement-4 pair | Whether those two `t_autodetect_*` tests actually drive the wired call form (`--pr <n> --autodetect --closes-only`) that issue #271 requirement 2 demands, rather than a narrower `--phase`-supplied call — the exact insufficiency #271 says the prior record had |
| S3 | `test_spawn.py` @ `c6c4363` (24-line delta) | The arrangement changed from `roster_remove(...)` to a live roster entry with a dead `wrapper_pid`, with a comment citing `spawn.py:1884-1894` | Whether that arrangement is discriminating for the drain-priority block — judgeable only from the diff plus the record's own red-proof claim, since re-running the observed role's tests is prohibited for this role |
| S4 | `docs/handbooks/operations.md` (28-line delta) | The stale "phase from whether the body has a closing keyword" line is replaced; two new paragraphs describe the approval-derived phase signal and the three-surface check; the `**Blocking for real as of 2026-08-04**` paragraph from issue #245's F3 wrap-up is present in the merged text | Whether any other text on this page still asserts the pre-#271 behaviour |
| S5 | Rebase integrity vs issue #247 (`9d1394f`, merged as `1d7df88`) | #247 touched `spawn.py`, `test_spawn.py`, `docs/handbooks/operations.md`, `docs/issue-247/reports/implementation.md`; the #271 landed delta touches **no** `spawn.py` line and 24 `test_spawn.py` lines | The pre-rebase commit SHAs are **not recoverable**: the timeline exposes only the post-force-push head (`e2bac95`), the branch was deleted at 06:00:23Z, and this clone has no reflog for it. Integrity therefore has to be judged from the merged tree at `c6c4363` against `1d7df88`, not from a pre/post-rebase diff |
| S6 | `docs/issue-271/reports/implementation.md` — the record's own internal consistency | `closed_checks` entries cite `test_spawn.py:3497`; the record's own "What did not work" states the post-rebase location is `:3749`, matching the delta read at S3 | Whether the record flags that shift anywhere the `closed_checks` refs themselves can be resolved, and whether every other `ref:` in `closed_checks` resolves at `c6c4363` |
| S7 | Issue-requirement coverage | Proposal rows A–H exist and rows D/E/F are argued as transitively covered, G/H as not coverable pre-merge | Whether requirement 1's second half — "**같은 클래스**(검사 표면 불완전)의 다른 구성원" swept across the gate system — was actually delivered, and whether requirement 4's regression is "실물 또는 동형 환경" as asked |
| S8 | Trajectory: phase-1→phase-2 gating | `ddc9b0f` (phase 1) precedes the sole approval comment; `6cd0ef2`/`1cab34b` (phase 2) follow it; PR `reviews: []`, so the two-account path was never used; author and approver are both `jjongkwann` (single-account mode) | Whether the approval comment's body is byte-exact `APPROVE issue-271/implementation` with nothing else, and whether the phase-2 commits are timestamped after it |

## 4. Constraints on this role, as they bear on the surfaces above

- Re-running the observed role's code is prohibited; its produced
  artifacts are the only admissible evidence. S2 and S3 therefore have to
  be settled from diffs and the record, never from a test run.
- Reading the observed role's `src/` as evidence of what happened is
  prohibited. Where a pre-existing, unmodified dependency has to be
  consulted (e.g. `gates/flows.py`'s `_pr_approved`, which the record says
  it reuses rather than rewrites), it is read at a pinned tree
  (`git show c6c4363:<path>`) and cited as such — never as the observed
  role's own output.
- This role edits nothing under `src/`, `test/`, or another role's
  `docs/issue-271/reports/` path; everything it produces lands under
  `docs/issue-271/reports/execution-observation/`,
  `docs/issue-271/reports/execution-observation.md`, and
  `docs/issue-271/proposals/`.

## 5. Scout aim derived from this survey

The unknowns that are about **method rather than fact** — S5 (how to
establish rebase integrity when the pre-rebase state is gone), S2/S3 (how
to establish that a red-green pair is discriminating without re-running
it), and S7 (what a same-class sweep is expected to cover) — are what the
scout sweep is aimed at. The purely factual unknowns (S1, S4, S6, S8) are
settled by reading, not by scouting.
