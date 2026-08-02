---
code_under_review: ded7993b2f46321efc0ce5a8d111cb56efd71b68
record_under_review: ded7993b2f46321efc0ce5a8d111cb56efd71b68
loop_state: landed
---

# Execution observation — `implementation` role on issue #205, phase 2 (PR #210)

Gate: this record opens only after `APPROVE issue-205/execution-observation`
(issue comment, single-account mode, author `jjongkwann` — a
`docs/specs/approvers.md` account — at 2026-08-02T13:35:35Z,
https://github.com/tokenmaxxxer/on-the-record/issues/205#issuecomment-5158242173).
The accompanying phase-1 survey
(`docs/issue-205/reports/execution-observation/survey.md`) and proposal
(`docs/issue-205/proposals/execution-observation-plan.md`), PR #213
(squash-merged `b78b3ef`, merged 2026-08-02T13:36:18Z), are this role's own
prior output; this file is the sole phase-2 artifact. `code_under_review` and
`record_under_review` are the same SHA because PR #210 is a single commit
(`ded7993`) that carries both the code diff and the `implementation` role's
own record — unlike issue-197's/issue-201's precedent of separate code and
record commits.

## Independence statement

This role did not author or edit the observed artifact. Nothing under
`spawn.py`, `.gitignore`, `test_spawn.py`, `gates/flows.py`, or
`docs/issue-205/reports/implementation.md` / `docs/issue-205/reports/implementation/`
/ `docs/issue-205/proposals/session-end-defects.md` was touched this session
or on this branch — only `docs/issue-205/reports/execution-observation.md`
(this file) and, in phase 1, `docs/issue-205/reports/execution-observation/`
and `docs/issue-205/proposals/execution-observation-plan.md` were written. No
code under observation (`spawn.py`, `gates/flows.py`, `test_spawn.py`) was
executed this session — every claim below is a static read of the `ded7993`
diff (`gh pr diff 210`, `git show ded7993 --stat`, both run this session), a
static read of current `HEAD` (confirmed this session via
`git log --oneline --follow -- <path>` for `spawn.py`, `test_spawn.py`,
`.gitignore`, and `gates/flows.py` — `ded7993` or an older commit is each
file's most recent touch, so no later commit on `main` altered the code under
review), a citation of the observed role's own record
(`docs/issue-205/reports/implementation.md`, read in full this session), or a
citation of issue-201's/issue-204's own records (read this session) — never a
re-run of `spawn.py`/`gates/flows.py`/`test_spawn.py` performed by this role.

## What was done this session (beyond phase 1)

`gh issue view 205 --json comments` (confirms the gating `APPROVE` comment
above); `gh pr view 210 --json commits,body,mergedAt,mergeCommit` and
`gh pr diff 210` (full diff of all four changed files, read in full);
`git show ded7993 --stat`; `.gitignore` current-`HEAD` read; `grep -n outcome
gates/flows.py`; `git show ee0c740 --stat`, `git show 1c230db --stat`,
`git show 6a54d5a` (full diff); `git log --oneline --follow` for each of the
four files under review; `gh pr view 206 --json reviews,comments,commits`
(confirms PR #206's own feedback comment text and that `reviews: []` — the
phase-1→phase-2 gate for `implementation` was the issue-comment path, not a PR
review); `gh api repos/tokenmaxxxer/on-the-record/issues/205/events`;
`git ls-files | grep -i warrant`; direct `Read` of `test_spawn.py:790-849` and
`:951-1010` (the two issue-201-registered tests' current bodies); full `Read`
of `docs/issue-205/proposals/session-end-defects.md`,
`docs/issue-205/reports/implementation/survey.md`,
`docs/issue-205/reports/implementation.md`,
`docs/issue-201/reports/implementation/survey.md`,
`docs/issue-201/reports/implementation.md`, and
`docs/issue-204/reports/implementation/survey.md`.

## Outcome — did PR #210 land what issue #205 asked

Judged against `docs/issue-205/proposals/session-end-defects.md` (the
approved, user-revised proposal — Constraints/Rationale/"What will be done"
read in full this session) rather than the issue body alone, since the
proposal is the user-approved interpretation of the issue.

**요구사항 1** ("커밋이 있는 세션은 outcome이 실패로 찍히지 않는다. 커밋은
있으나 트리가 dirty인 경우는 별도 표기로 구분한다") — **met, as scoped by the
approved proposal.** `ded7993`'s `spawn.py` hunk (`gh pr diff 210`) inserts
`if new_commit and uncommitted: return "progressed-dirty-tree"` directly above
the pre-existing `if uncommitted: return "failed-no-commit"` — no
reclassification wrapper, matching `session-end-defects.md`'s "What will be
done" item 1 verbatim. The two literal 원장 실측 cases the issue cites
(`1ed27b9`/PR #191, `7d11c9e`/PR #194, both `new_commit=True`+dirty per
`docs/issue-205/reports/implementation/survey.md`) are now correctly
separated from a real no-commit failure. The proposal's Constraints/"Out of
scope" (read this session) explicitly excludes the `already_delivered`-only
(no new commit this session) + dirty case from this fix, on the grounds that
neither measured case was `already_delivered`-only and the existing test
`test_already_delivered_with_dirty_tree_still_downgrades` already treats that
case as an independent risk signal — a deliberate, approved narrowing bounded
to the issue's own measured evidence, not a silent gap. `ded7993`'s test diff
confirms the narrowing was honored: only
`test_new_commit_dirty_tree_is_still_downgraded` (renamed
`test_new_commit_dirty_tree_is_promoted_not_downgraded`, new expected value
`"progressed-dirty-tree"`) was touched; `test_already_delivered_with_dirty_tree_still_downgrades`
and `test_no_new_commit_dirty_tree_is_downgraded` are absent from the diff's
test hunk entirely (`gh pr diff 210`), i.e. byte-unchanged.

**요구사항 2** (".warrant-hunt.count가 워크스페이스 트리를 더럽히지 않게 한다
— 방향 후보는 git 추적 해제 + gitignore") — **met.** Current `.gitignore`
(read this session) is:
```
runs/
__pycache__/
.router.lock
.warrant-hunt.*
```
— the 4th line matches `ded7993`'s diff (`+.warrant-hunt.*`) exactly, and the
wildcard (not the literal `.warrant-hunt.count`) also covers `.warrant-hunt.lock`,
matching the proposal's Rationale (rejects the literal-filename alternative on
the same "접미사를 하나씩 나열하면 빠뜨린다" principle `clean()`'s own comment
already states). `git ls-files | grep -i warrant` (this session) returns only
unrelated `warrant-hunter.md` persona files — neither `.warrant-hunt.count`
nor `.warrant-hunt.lock` is tracked, confirming `git show 1c230db --stat`
(this session)'s deletion still holds. Both halves of "추적 해제 + gitignore"
are independently confirmed at current `HEAD` by this role directly. The
record's own §검증 3 (`touch .warrant-hunt.count .warrant-hunt.lock` →
`git status --porcelain` empty) is cited, not independently re-run — live
mutation of the real repo's working tree is outside this role's read-only
research scope; the static `.gitignore`/`git ls-files` facts above are
consistent with that citation.

**요구사항 3** ("`spawn.py clean`의 형제 삭제가 디렉터리를 만나도 멈추지
않는다") — **met.** `ded7993`'s `spawn.py` hunk adds
`if sibling.is_file(): sibling.unlink()` immediately replacing the prior
unguarded `sibling.unlink()` (`gh pr diff 210`, confirmed against current
`HEAD` at `spawn.py:2125-2127`). The new test
`test_directory_sibling_does_not_abort_the_clean_loop` (full body read via
`gh pr diff 210`) is a genuine end-to-end reproduction, not a unit check on
the guard line alone: it plants two dead workspaces plus one directory
sibling and one file sibling, runs `spawn.main()` with
`sys.argv = ["spawn.py", "clean"]`, and asserts both dead workspaces are gone
(proving the loop reached the second, alphabetically-later workspace without
aborting), the file sibling is gone, and the directory sibling survives (the
guard skips rather than crashes or deletes it) — exactly requirement 3's
"안전한 디렉터리 형제 처리."

**요구사항 4** ("기존 원장 스키마 소비자(`gates/flows.py`의 ledger 구역
등)가 깨지지 않는다") — **met.** `gates/flows.py` (grepped this session,
5 total matches on `outcome`): line 316
(`verdict = matches[-1].get("outcome") if matches else None`, opaque
passthrough) and lines 328/338
(`outcome = entry.get("outcome") or "unknown"` then
`agg["outcomes"][outcome] = agg["outcomes"].get(outcome, 0) + 1`, opaque
dict-key bucketing). No site branches on a specific `outcome` string value —
a new value (`"progressed-dirty-tree"`) cannot break either site by
construction, and no other `outcome` reference exists in the file.

**Verdict: outcome met — all four of issue #205's numbered requirements, and
the proposal's five "What will be done" items 1:1 against `ded7993`'s actual
diff, cited above.**

## Trajectory — was the `implementation` role's phase-1→phase-2 path sound

**Survey before proposing — sound.**
`docs/issue-205/reports/implementation/survey.md` (read in full this session)
locates all three defects with exact line numbers, ties the two cited
ledger-misclassification cases to real commits (`1ed27b9`, `7d11c9e`) present
in this repo's history, and documents the existing-test baseline (12 passed,
isolated run) before proposing — a located-defect-then-Rationale pattern with
an explicit, correctly-applied scout skip record (스킵 조건 1, internal
session-end logic, no product-facing surface to scout).

**Human approval before phase 2 — sound.** Issue comment
`APPROVE issue-205/implementation`, author `jjongkwann`
(`docs/specs/approvers.md` account), 2026-08-02T12:19:34Z,
https://github.com/tokenmaxxxer/on-the-record/issues/205#issuecomment-5157807265
— satisfied 2 seconds before PR #206 merged (`de0f873`, 12:19:36Z) and well
before `ded7993` (12:29:04Z, `gh pr view 210 --json commits`). `gh pr view 206
--json reviews` (this session) returns `reviews: []` — the gate was the
issue-comment path (single-account mode, contract v3 s19), consistent with
PR #206's author and the approving account being the same (`jjongkwann`).

**The mid-phase-1 constraint relaxation stayed inside its own declared
scope — sound.** PR #206's own comment (`gh pr view 206 --json comments`,
this session), posted 12:11:52Z by `jjongkwann`, is literally titled
"[오케스트레이터 중계 — 사용자 결정: 수정 요구]" and instructs: relax
"existing tests unchanged" only for tests asserting the defect itself, and
re-adopt the direct-order-fix (no reclassify wrapper). `ee0c740` (the
proposal-revision commit, authored 12:17:14Z — 5 minutes after that comment,
12 minutes before PR #206 merged) implements exactly that instruction in its
commit message and diff (`git show ee0c740 --stat`, this session: touches
only `docs/issue-205/proposals/session-end-defects.md` and
`docs/issue-205/reports/implementation/survey.md`). This is a phase-1-internal
revision responding to review feedback on the still-open phase-1 PR, not a
phase-2 deviation — `ee0c740` predates PR #206's merge by 2 minutes. The
actual `test_spawn.py` diff in `ded7993` honors the relaxation's declared
boundary exactly: only the one defect-asserting test was touched (confirmed
under 요구사항 1 above).

**Write-set discipline — sound, no stray file (unlike issue-197's
precedent).** `git show ded7993 --stat` (this session): exactly 4 files —
`.gitignore`, `docs/issue-205/reports/implementation.md`, `spawn.py`,
`test_spawn.py` — matching the approved proposal's declared
`files: spawn.py, .gitignore, test_spawn.py` plus the role's own record file.
No file outside that set was touched, in contrast to issue-197's
`execution-observation` record's Finding 1 (`.warrant-hunt.count` deleted
outside a declared write set).

**Out-of-scope items honored — sound.** The proposal's "Out of scope" (read
this session) names: no `already_delivered`-only reclassification (confirmed
above), no recursive directory-sibling deletion in `clean` (confirmed —
`ded7993`'s guard only skips, never deletes, directory siblings), and no
`rulebook_checkout`/`core_root` network-fix (confirmed — `ded7993`'s diff
touches none of that code). All three checked directly against the diff, not
assumed from the proposal's text alone.

**Verdict: trajectory sound overall — surveyed before proposing, obtained
real human approval before phase 2, kept a mid-phase-1 scope relaxation
inside its own stated boundary, held its declared write set exactly, and
honored every declared out-of-scope item — with one confirmed step-level
deficiency (Finding 1, below).**

## Step — which specific artifact, if any, is deficient

### Finding 1 (confirmed) — `implementation.md`'s frontmatter `code_under_review` cites the wrong commit

- **Summary**: `docs/issue-205/reports/implementation.md`'s frontmatter (and
  all three `closed_checks` entries) cite
  `code_under_review: ee0c74067102a57702d740b7657b385b29269875`. `git show
  ee0c740 --stat` (this session) confirms `ee0c740` is the phase-1
  proposal-revision commit — a docs-only commit touching only
  `docs/issue-205/proposals/session-end-defects.md` and
  `docs/issue-205/reports/implementation/survey.md`, no `spawn.py`/
  `test_spawn.py`/`.gitignore` line at all. `gh pr view 210 --json commits`
  (this session) confirms PR #210's sole commit is `ded7993`, which contains
  both the actual code diff (`spawn.py`, `.gitignore`, `test_spawn.py`) and
  this very record file. None of the three `closed_checks` entries' reported
  pytest/manual results (13 passed isolated run; 135 passed/18 failed full
  suite with the new test counted; the `.warrant-hunt.*` manual touch check)
  could have been produced against `ee0c740`'s tree state, since that state
  contains none of the code or new tests those checks exercise — they can
  only reflect `ded7993`.
- **Impact**: low functional impact — `ded7993`'s own commit message and PR
  #210's body correctly attribute the change to the approved proposal by
  content, and this role was able to reconstruct the correct commit
  independently this session via `gh pr view 210 --json commits`. The impact
  is on the record's own audit trail: `code_under_review` exists precisely so
  a reader (or a future automated consumer, including this
  execution-observation role's own phase-1 proposal, which had to
  cross-check it manually) can verify `closed_checks` against the actual code
  state without re-deriving it from the PR — that anchor is currently wrong.
- **Timeline**: `ee0c740` committed 2026-08-02T12:17:14Z (the last commit of
  PR #206, tip of the approved proposal, merged `de0f873` at 12:19:36Z);
  `ded7993` committed 2026-08-02T12:29:04Z, roughly 10 minutes after PR #206
  merged and the proposal was finalized.
- **Root cause**: the frontmatter's `code_under_review` value appears to have
  been filled with the last-known SHA at drafting/approval time (the just-
  merged proposal revision) and never re-pointed to the commit the record
  itself ultimately shipped inside, once phase-2 code landed in `ded7993`. An
  editorial slip in the record's self-citation, not a code defect — `ded7993`'s
  diff and PR body independently and correctly reference the approved
  proposal by name.
- **Action item**: not performed by this role — this role's standing
  prohibition bars editing the observed role's artifacts. Recorded for the
  human to route: correcting `docs/issue-205/reports/implementation.md`'s
  `code_under_review` to `ded7993b2f46321efc0ce5a8d111cb56efd71b68` (matching
  the pattern issue-201's own `implementation.md` correctly follows for its
  single-commit PR — `code_under_review` equals that PR's sole commit), or
  more generally confirming that `code_under_review` is set from the commit
  actually being pushed, not carried over from an earlier drafting state.

### Issue-201-registered test causation bisection (mandatory item)

Orchestrator hypothesis: commit `1c230db`'s deletion of `.warrant-hunt.count`
caused `Ledger::test_entry_carries_the_live_log_path` and
`IssueScopedPrompt::test_preparation_and_preamble_happen_once` to flip from
failing to passing.

**Verdict: refuted — not "fixed by `1c230db`," and not even "a dirty-tree
condition disappeared as `1c230db`'s side effect."** The two are causally
disconnected by construction, on evidence read this session:

1. `git show 1c230db --stat`: touches exactly three files —
   `.warrant-hunt.count` (deleted) and two new `docs/issue-197/...` files. No
   line of `test_spawn.py` or `spawn.py` is touched.
2. `git show 6a54d5a` (full diff, this session): touches exactly
   `test_spawn.py`, exactly the two named tests, replacing each test's
   post-session `roster.read_text()` lookup with a call-through spy that
   captures `roster_register`'s argument before delegating to the original.
   The commit message states the root cause verbatim: both tests always
   failed with `KeyError` because `_spawn_one` removes its own roster entry
   (`roster_remove`, `spawn.py:2548`) before returning — the tests were
   reading a dict key the session's own contract guarantees is already gone
   by the time they look.
3. Direct read of both tests' current bodies this session
   (`test_spawn.py:790-849`, `:951-1010`): each test builds its own
   self-contained temporary git repository (`tempfile.TemporaryDirectory()`,
   `git init` inside it) and a temporary roster file
   (`spawn.ROSTER = roster`, also a temp `Path`) — `spawn.ROOT` (the real
   repo, the only place `.warrant-hunt.count` could exist) is never
   reassigned in either test. Neither test calls `fail_closed_downgrade` or
   asserts on any `outcome`/dirty-tree value; both assert only on the
   captured roster entry's `log` field and the delivered log content. The
   dirty-tree-detection code path that `.warrant-hunt.count` could influence
   and the roster-capture code path these two tests exercise are structurally
   disjoint regions of `_spawn_one` — one cannot affect the other's outcome
   regardless of which commit touched which file.
4. `docs/issue-201/reports/implementation/survey.md` (read in full this
   session) independently reproduced the pre-fix failure as
   `KeyError: 'issue-9/execution-observation'` (`test_spawn.py:843`) and
   `KeyError: 'issue-7/execution-observation'` (`test_spawn.py:987`) — a
   dict-key lookup failure, not a git-status/dirty-tree-shaped assertion
   failure — and states plainly: "코드가 아니라 테스트의 관측 시점이 계약과
   어긋난다."

`1c230db` (2026-08-02T08:13:28Z) is chronologically upstream of `6a54d5a`
(2026-08-02T10:34:28Z), but upstream-in-time is not causally connected here:
`1c230db`'s diff never touches the code path either test exercises, and
neither test's failure or success ever depended on `.warrant-hunt.count`'s
tracked state. The correct characterization is **fixed, and fixed
specifically by `6a54d5a`** (issue-201's approved, deliberate
call-through-spy change) — the orchestrator hypothesis linking the flip to
`1c230db` does not hold, on both diff-content and test-body evidence read
this session.

## Open findings

Carried forward from the Step section above, for the human to route (this
role files no issues itself):

1. `docs/issue-205/reports/implementation.md`'s frontmatter
   `code_under_review` cites `ee0c740` (a docs-only commit) instead of
   `ded7993` (the actual code+record commit). Evidence: Finding 1 above.

## Summary

**Outcome**: all four of issue #205's requirements are met by PR #210
(`ded7993`), cited above, including an explicit note that requirement 1's fix
is correctly scoped to the two measured `new_commit=True`+dirty cases per the
approved proposal's own narrowing, not a broader "any commit ever" guarantee.

**Trajectory**: the `implementation` role surveyed before proposing, obtained
real human approval before phase 2 via the issue-comment path, kept a
mid-phase-1 scope relaxation inside its own stated boundary, held its
declared write set exactly (no stray file, unlike issue-197's precedent), and
honored every declared out-of-scope item — sound overall, with one confirmed
step-level deficiency (Finding 1).

**Step**: one confirmed deficiency (Finding 1, the `implementation.md`
frontmatter's `code_under_review` citation); the mandatory issue-201 causation
bisection is resolved — the orchestrator's `1c230db` hypothesis is refuted,
the two tests' fail→pass flip is `6a54d5a` (issue-201's approved fix), on
diff-content and direct test-body evidence read this session.
