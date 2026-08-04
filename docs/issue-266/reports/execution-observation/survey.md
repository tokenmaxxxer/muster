---
kind: survey
date: 2026-08-04
subject: issue-266
role: execution-observation
phase: 1
---

# Current-state survey — what is under observation, and what I read to scope it

## Scope statement (the specific target)

- **Observed role**: `implementation`, issue #266.
- **Observed session**: the single `issue-266/implementation` session that ran
  phase 1 and phase 2 on 2026-08-04 between 02:53:18Z (first commit) and
  03:21:30Z (last commit).
- **Observed issue**: #266 — "명부 삭제가 session-end 기록보다 앞서 실행 —
  watch 가 정상 종료를 크래시로 오보" (execution plan: step 1
  `implementation`, step 2 `execution-observation`).
- **Observed PR**: **#267** (`issue-266/implementation` → `main`), state
  MERGED at 2026-08-04T04:08:44Z, merge commit `247051e`.
- **This session**: `execution-observation`, issue #266, branch
  `issue-266/execution-observation`, delivering plan step 2. This session is
  phase 1 (research + survey + scout + proposal) at the time of writing.

Not "recent work", not "the last PR": the observation target is PR #267 and
its three commits only.

## What I read to arrive at that scope (firsthand, this session)

| Artifact | How read | Key identifiers |
|---|---|---|
| Issue #266 body + both comments | `gh issue view 266`, `gh api .../issues/266/comments` | approve comment `APPROVE issue-266/implementation` by `jjongkwann` at 2026-08-04T03:00:27Z; reopen comment at 04:09:13Z |
| PR #267 metadata (body, commits, reviews, merge) | `gh pr view 267 --json ...` | `reviews: []`; merged 04:08:44Z; head `issue-266/implementation` |
| Commit `1fdd1ac` | `gh pr view` commit list | "issue-266: phase 1 — survey + scout brief + proposal", 02:53:18Z |
| Commit `d61e93c` | same | "issue-266: phase 2 start — implementation record opened", 03:04:51Z |
| Commit `be53d1e` | `git show be53d1e --stat`, `git show be53d1e -- spawn.py`, `git show be53d1e -- test_spawn.py` | "issue-266: phase 2 — drop roster-entry-absence…", 03:21:30Z; 4 files, +306/−36 |
| `docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md` | Read (full) | the approved proposal; `files:` header lines 1-4 |
| `docs/issue-266/reports/implementation.md` | Read (full, 225 lines) | the observed role's own record; `loop_state: landed` |
| `docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md` | `git show be53d1e:…` | the phase-2 decision doc |
| `docs/issue-224/decisions/watch-crash-exit-code.md:18-32` | `sed -n '18,32p'` | the amendment's *target* wording, at current HEAD |
| `docs/specs/approvers.md` | `cat` | `JiwonJung94`, `jjongkwann` |
| `docs/handbooks/operations.md:650-694` | `sed -n` | merge-gate section: the Closes gate reads the **PR body** |
| `docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:1-60` | `sed -n` | the plan-aware Closes rule's actual judgment |

Deliberately **not** read as evidence: the current contents of `spawn.py` and
`test_spawn.py`. Present-tense source shows what exists now, not what this
role did — the diff of `be53d1e` is the admissible form and is what I read.
Nothing was re-executed: no test run, no `_watch()` invocation.

## Current state of the observed change (facts, no judgment)

1. **The code change** (`be53d1e`, `spawn.py` hunk at :1900-1911): the
   `--follow` death predicate went from
   `if roster_entry is None or not pid or not _alive(pid):` to
   `if pid is not None and not _alive(pid):`, plus a 5-line Korean comment
   citing `spawn.py:2995` / `spawn.py:3097`. Seven lines changed total.
2. **The tests** (`be53d1e`, `test_spawn.py` hunk): one test added
   (`test_follow_tolerates_roster_entry_fully_absent_before_session_end`,
   +26 lines) and one pre-existing test rewritten
   (`test_follow_detects_dead_session_and_returns_crash_rc`: its arrange
   changed from `spawn.roster_remove("issue-180/implementation")` to
   `subprocess.Popen(["true"]) … roster_register(… wrapper_pid=dead.pid …)`).
3. **The docs**: `docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md`
   (new, 56 lines) + `docs/issue-266/reports/implementation.md` (+231/−…).
4. **Approval path**: single-account mode. PR #267 has `reviews: []`; the
   approval is the issue comment whose entire body is
   `APPROVE issue-266/implementation`, posted by `jjongkwann`, who is listed
   in `docs/specs/approvers.md`.
5. **Two recorded deviations** from the approved proposal's "What will be
   done" (`docs/issue-266/reports/implementation.md:98-141`): item 3
   (re-run the pre-existing test unchanged → rewrote it) and item 4 (edit
   `docs/issue-224/decisions/watch-crash-exit-code.md` → wrote a new
   decision doc under `docs/issue-266/` instead, citing `board-gate.sh` R4).
6. **The proposal's item-4 target is still stale at HEAD**:
   `docs/issue-224/decisions/watch-crash-exit-code.md:25-26` still reads
   "`2` (new) — `--follow` detected the session's pid is dead (or its roster
   entry is gone)…" — verified by reading that file at the merge commit's
   tree state.
7. **The issue auto-closed on merge**: commit `be53d1e`'s message body
   contains the line `Closes #266`. PR #267's *body* carries no closing
   keyword (it notes "closing keyword removed by relay per plan-aware
   rule"). The issue was reopened by the human 29 seconds after merge.

## Write surfaces of THIS session, and their unknowns

| Surface | State | Unknown the scout sweep must aim at |
|---|---|---|
| `docs/issue-266/reports/execution-observation/survey.md` | this file | — |
| `docs/issue-266/reports/execution-observation/scout-brief.md` | to write | what strong audits of a *failure-detector predicate change* actually check |
| `docs/issue-266/proposals/execution-observation-plan.md` | to write | how audits treat **execution-time deviations from an approved plan** — is a deviation a finding, or is the *handling* of it what gets judged? |
| `docs/issue-266/reports/execution-observation.md` | phase 2 only | how an evidence-only audit (may not re-execute) establishes that a red→green claim is *sufficient* evidence |
| — | — | how audits classify a **control that inspects only one surface** (Closes gate reads the PR body; the closing keyword arrived via the commit message) — role deficiency vs. control gap |

## Thin / contested spots in the current state (the gaps)

- **G1 — predicate completeness.** The narrowed predicate drops two former
  death branches, not one: `roster_entry is None` *and* falsy `pid`. The
  issue text (요구 1(b)) names only the first. The proposal's item 1
  (`…proposals/roster-lifetime-vs-absence-signal.md:34`) does name both. So
  whether the delivered predicate is in scope turns on which document is the
  binding one — an unknown to state a checking rule for, not to answer here.
- **G2 — the rewritten test.** #224 owns that test (요구 3 says #224's landed
  items stay). It was rewritten, not merely re-run. Whether the coverage
  #224 owned survives the rewrite is checkable from the diff pre-image alone.
- **G3 — red→green sufficiency.** The record claims red (`AssertionError:
  2 != 0`) then green. I may not re-run it. What makes such a claim
  *auditable* from artifacts only is a gap.
- **G4 — deviation handling.** Two deviations, both self-recorded. Unknown:
  what a strong audit demands of a deviation record beyond "it is written
  down".
- **G5 — the closing-keyword escape.** The gate reads the PR body
  (`docs/handbooks/operations.md:662-666`); the keyword rode in on the
  commit message. Unknown: whether comparable review practice books this
  against the author or against the control.
