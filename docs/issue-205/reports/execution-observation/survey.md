# Survey — issue #205: execution-observation of PR #210 (`implementation` role, phase 2)

## Scope

Observed: role `implementation`, subject `issue-205`. Sessions landed as PR #206
(`implementation` phase 1 — survey + proposal, merge `de0f873`, merged
2026-08-02T12:19:36Z, plus a phase-1 revision commit `ee0c740` inside the same PR)
and PR #210 (`implementation` phase 2 — code + record, merge `86bf624`, merged
2026-08-02T12:57:03Z). Code-and-record commit under observation: `ded7993b2f46321efc0ce5a8d111cb56efd71b68`
(PR #210's sole commit — unlike issue-197/issue-201's precedent of a separate
code commit and record commit, this PR combines both in one commit, confirmed via
`gh pr view 210 --json commits` returning exactly one commit oid, `ded7993`).

The invoking prompt names four judgment items (fail_closed_downgrade's direct
branch, `.warrant-hunt.*` gitignore effect, the clean directory guard + its
reproduction test, gates/flows.py ledger-consumer non-breakage) plus one
additional required item: a commit-level bisection of two issue-201-registered
test failures (`Ledger::test_entry_carries_the_live_log_path`,
`IssueScopedPrompt::test_preparation_and_preamble_happen_once`) against an
orchestrator hypothesis that commit `1c230db`'s `.warrant-hunt.count` deletion
removed a dirty condition inside those tests. This survey scopes all five as the
phase-2 subject.

## Scope skip record (scout-directive)

Scouting is skipped. Skip condition: the spec — this role's own directive (the
three-level outcome/trajectory/step verdict format, the citation-adjacency rule,
the blameless four-part finding shape, the record file path) plus the invoking
prompt's five named judgment items — leaves no design decision open for this
proposal to make; the acceptance criteria are fixed by the approved
`docs/issue-205/proposals/session-end-defects.md` and by the invoking prompt
itself. This is a mechanical evidence-gathering task against a fixed spec, not a
product/design choice to scout industry practice for — the same skip condition
issue-197's and issue-201's execution-observation/implementation surveys
recorded for the same reason.

## What was read this session

- `gh issue view 205` / `gh issue view 205 --comments` / `gh issue view 205 --json comments`
  — full issue body (결함 1-3, 요구사항 1-4, 실행 계획 checklist showing step 1
  checked, step 2 unchecked), and its one comment: `APPROVE issue-205/implementation`,
  author `jjongkwann`, association MEMBER, 2026-08-02T12:19:34Z,
  https://github.com/tokenmaxxxer/on-the-record/issues/205#issuecomment-5157807265.
  `gh api repos/tokenmaxxxer/on-the-record/issues/205/events` returns `[]` — issue
  #205 has never been closed or reopened, unlike issue #197's precedent.
- `docs/issue-205/proposals/session-end-defects.md` (on `main`, revision `ee0c740`)
  — the approved phase-1 proposal in full: Constraints (existing-tests-unchanged
  relaxed for defect-asserting tests, per a mid-phase-1 user decision), Rationale's
  adopted choices and named rejected alternatives for all three defects, "What will
  be done" (5 numbered items), "Out of scope," and "How you'll know it worked."
- `docs/issue-205/reports/implementation.md` (on `main`) — the observed role's own
  phase-2 record in full. Frontmatter: `code_under_review: ee0c74067102a57702d740b7657b385b29269875`,
  `loop_state: landed`, three `closed_checks` entries, all three citing the same
  `code_sha: ee0c74067102a57702d740b7657b385b29269875`. Flagged below — this SHA
  is `ee0c740`, the phase-1 proposal-revision commit (docs-only, touches
  `docs/issue-205/proposals/session-end-defects.md` and
  `docs/issue-205/reports/implementation/survey.md` per `git show ee0c740 --stat`,
  no `spawn.py`/`test_spawn.py`/`.gitignore` touch at all per the same stat), not
  the actual code commit `ded7993` that the closed_checks' test-run results could
  only have been produced against.
- `gh pr view 210 --json ...,commits`, `gh pr diff 210`, `gh pr view 210 --json body`
  — PR #210's single commit (`ded7993`, authored/committed 2026-08-02T12:29:04Z),
  full diff (`.gitignore` +1, `spawn.py` +28/-12 across two hunks, `test_spawn.py`
  +56/-2, plus the new `docs/issue-205/reports/implementation.md`), and its body
  (a `## Summary`/`## Test plan` matching the record's own §검증).
- `git show ded7993 --stat` — confirms the write set exactly matches the approved
  proposal's declared `files:` (`spawn.py`, `.gitignore`, `test_spawn.py`) plus the
  role's own record, 4 files total, 228 insertions / 12 deletions — no stray file.
- `spawn.py:1230-1263` (current `HEAD`, confirmed identical to `ded7993`'s state —
  no commit after `ded7993` on `main` touches `spawn.py` per `git log --oneline --follow -- spawn.py`
  not yet run this session but `git log --oneline` shows only `0ab22b4`/`dd65451`
  (issue-204) after `ded7993`, and issue-204's own survey — read below — declares
  its write set as `conftest.py` + new fixture files only, no `spawn.py` touch) —
  `fail_closed_downgrade()`'s full body, including the new line
  `if new_commit and uncommitted: return "progressed-dirty-tree"` inserted directly
  above the pre-existing `if uncommitted: return "failed-no-commit"`, with the
  `blocked`-check and `already_delivered` branches left in their original positions
  below it.
- `spawn.py:2090-2135` — `clean()`'s full sibling-glob loop, confirming the new
  `if sibling.is_file(): sibling.unlink()` guard (current `HEAD`, matching `ded7993`'s
  diff) replaces the prior unguarded `sibling.unlink()`.
- `test_spawn.py:585-657` — the full `FailClosedDowngrade` class (9 tests): read
  each of the 9 test bodies directly against `ded7993`'s diff — only
  `test_new_commit_dirty_tree_is_promoted_not_downgraded` (renamed from
  `test_new_commit_dirty_tree_is_still_downgraded`) differs from its pre-`ded7993`
  form (expected value changed `"failed-no-commit"` → `"progressed-dirty-tree"`);
  the other 8, including `test_already_delivered_with_dirty_tree_still_downgrades`
  (`:649-656`, still asserts `"failed-no-commit"` for `already_delivered=True` +
  dirty tree) and `test_no_new_commit_dirty_tree_is_downgraded` (`:594-598`, still
  asserts `"failed-no-commit"` for `new_commit=False` + dirty tree), are
  byte-identical to their pre-`ded7993` bodies per `gh pr diff 210`'s hunk (which
  shows only the one test's lines touched).
- `test_spawn.py:1253-1401` — the full `Clean` class (3 tests, including
  `_make_clean_repo` helper): confirms the two pre-existing tests
  (`test_keeps_live_session_workspace_but_deletes_dead_sibling`,
  `test_removes_all_generation_logs_and_sibling_files`) are unchanged, and the new
  `test_directory_sibling_does_not_abort_the_clean_loop` (`:1377-1401`) creates two
  dead workspaces (`issue-51-review`, `issue-52-review`), plants a directory
  sibling (`.somedir/`, containing a file) and a file sibling
  (`.events.jsonl`) on the first, runs `spawn.main()` with `sys.argv = ["spawn.py", "clean"]`,
  and asserts: both dead workspaces are gone (`assertFalse(dead_ws_a.exists())`,
  `assertFalse(dead_ws_b.exists())` — proving the loop did not abort and reached
  the second, alphabetically-later workspace), the file sibling is gone, and the
  directory sibling still exists (`assertTrue(dir_sibling.is_dir())` — the guard
  skips it rather than deleting it).
- `gates/flows.py:306-338` — the two ledger-outcome consumer sites: line 316
  (`verdict = matches[-1].get("outcome") if matches else None`, a session-view
  field, opaque passthrough) and lines 328/338 (`outcome = entry.get("outcome") or "unknown"`
  then `agg["outcomes"][outcome] = agg["outcomes"].get(outcome, 0) + 1`, a dict
  keyed by whatever string `outcome` is). Neither site branches on any specific
  outcome string value — both treat `outcome` as an opaque bucket key. No other
  reference to `outcome` exists in `gates/flows.py` per `grep -n "outcome" gates/flows.py`
  (5 total matches, all read).
- `.gitignore` (current `HEAD`) — confirms the added line `.warrant-hunt.*` (4th
  line, after `runs/`, `__pycache__/`, `.router.lock`), matching `ded7993`'s diff
  exactly.
- `git ls-files | grep -i warrant` — returns only unrelated
  `docs/issue-{167,170}/_assets/rulebook-skeleton/*/agents/warrant-hunter.md` paths
  (a different, unrelated agent-persona filename); no `.warrant-hunt.count` or
  `.warrant-hunt.lock` is tracked, confirming the untracking (attributed in the
  record to `1c230db`'s side effect) still holds as of current `HEAD`.
- `git show 1c230db --stat` and `git show 1c230db -- .warrant-hunt.count` — full
  diff of the commit the orchestrator hypothesis names: deletes `.warrant-hunt.count`
  (content `3`, `-1` line) and adds two new files
  (`docs/issue-197/proposals/plan-parser-fix.md`,
  `docs/issue-197/reports/implementation/scout-brief.md`). **`1c230db`'s diff does
  not touch `test_spawn.py` or `spawn.py` at all** — 3 files changed total, none of
  them the test file containing the two named tests.
- `git show 6a54d5a` (full commit, message + diff) — the commit whose own message
  states, verbatim: "the two tests that read the roster file after `_spawn_one`
  returns … always failed with `KeyError` because `_spawn_one` removes its own
  roster entry before returning (`roster_remove` at `spawn.py:2548`)," and whose
  diff (read in full) modifies exactly `test_spawn.py`, replacing each test's
  `json.loads(roster.read_text())[key]` lookup (the pre-fix form) with a
  call-through spy (`spy_roster_register`) that captures `roster_register`'s
  argument before delegating to the original — for both
  `Ledger::test_entry_carries_the_live_log_path` (hunk at old `:820-849`) and
  `IssueScopedPrompt::test_preparation_and_preamble_happen_once` (hunk at old
  `:976-1003`).
- `docs/issue-201/reports/implementation/survey.md` (read in full, prior session)
  — documents the pre-fix failure mode directly: naive `pytest -k <name>` runs
  (dated 2026-08-02, same day) reproduce `KeyError: 'issue-9/execution-observation'`
  and `KeyError: 'issue-7/execution-observation'` respectively — a `KeyError` on a
  roster-dict lookup, not any git-dirty-tree-shaped error — and states plainly:
  "코드가 아니라 테스트의 관측 시점이 계약과 어긋난다" (not the code, the test's
  observation timing is out of step with the contract). The same survey's "이미
  결정된 것(D1-D3)" section states D3 (`.warrant-hunt.count`, `clean`'s
  `sibling.unlink()`, `fail_closed_downgrade` false-positives) was "이번 조사에서
  다시 마주치지 않았다 — 손대지 않는다" (not encountered again in this
  investigation — left untouched), i.e. issue-201's own investigation found no
  connection between its two target tests and `.warrant-hunt.count`.
- `docs/issue-201/reports/implementation.md` (read in full, prior session) —
  confirms the fix landed exactly as `6a54d5a`'s diff shows (call-through spy,
  `spawn.py` unchanged per "D1"), and its own §검증 reports, post-fix,
  `1 passed` for each test individually and `152 passed` for the full suite —
  the same day, same repo state class the issue-205 implementation record later
  cites.
- `docs/issue-204/reports/implementation/survey.md` (read in full, prior session)
  — documents the *other*, unrelated failure mode that can also make these same
  two tests fail: with `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` unset, all 18
  of a fixed set of tests (including these same two, explicitly listed in its
  table as "범위 밖 — 이슈 #201," i.e. already fixed and out of that issue's own
  scope) fail via `rulebook_checkout`'s `sys.exit` or `core_root()`'s
  `UnboundLocalError` — a sandbox network/git-clone artifact, reached because
  neither test mocks `spawn.roster_register`'s siblings `plugin_dirs`/`core_root`
  and both run with real `spawn.ROOT`. That survey explicitly states the fix
  (issue #201, `6a54d5a`) already works correctly once past this bottleneck: "이미
  존재하는 #201 수정이 이 병목 뒤에서 정상 동작함을 재확인하는 것일 뿐."
- `docs/reports/2026-08-02-hunt-issue-204-rulebook-checkout-test-fixture.md` (read
  in full, prior session) — a hunt record for a different, adjacent finding
  (conftest.py fixture silently not applying under non-pytest invocations); read
  for context, not directly relevant to the two named tests.
- `docs/specs/approvers.md` — approver accounts `JiwonJung94`, `jjongkwann`.
- `gh pr list --state all --search "head:issue-205/execution-observation"` —
  returns empty; no PR yet exists for this role's branch this session.
- `docs/issue-197/reports/execution-observation/survey.md` and
  `docs/issue-197/proposals/execution-observation-plan.md` (read for format/
  structure precedent only — this repo's established phase-1 pattern for this
  exact role, and the source of the citation-adjacency and skip-record
  conventions followed here).

## Current-state facts, mapped to the four named judgment items (read statically, not executed)

**Item 1 — `fail_closed_downgrade`'s direct branch matches spec.**
`spawn.py:1256-1257` (current `HEAD`) inserts
`if new_commit and uncommitted: return "progressed-dirty-tree"` immediately above
the pre-existing `if uncommitted: return "failed-no-commit"`, with no separate
reclassification function — matching the revised proposal's (`ee0c740`) "What will
be done" item 1 verbatim, including the explicit carve-out that
`already_delivered`+dirty (`new_commit=False` in that path) still falls through to
the unchanged `if uncommitted: return "failed-no-commit"` line below. All 9
`FailClosedDowngrade` tests read line-by-line against `ded7993`'s diff: 8 unchanged
(including the two dirty-tree tests the proposal named as must-stay-unchanged
guardrails), 1 renamed+re-asserted as the proposal's "What will be done" item 5
specifies. Whether this fully satisfies 요구사항 1's stated framing ("커밋은 있으나
트리가 dirty인 경우는 별도 표기로 구분한다") is a phase-2 judgment, not rendered
here.

**Item 2 — `.warrant-hunt.*` gitignore effect.** `.gitignore` (current `HEAD`)
contains the line, confirmed by direct read. `git ls-files` confirms neither
`.warrant-hunt.count` nor `.warrant-hunt.lock` is tracked. The record's own §검증 3
reports a manual `touch` + `git status --porcelain` empty-output check; this
session did not repeat that manual reproduction (would require creating files at
the real repo root, a live-tree mutation outside this role's read-only research
scope) — noted as unverified-by-this-role-directly, resting on the record's own
citation plus the static `.gitignore`/`git ls-files` facts above.

**Item 3 — clean directory guard + its reproduction test.** `spawn.py:2125-2127`
(current `HEAD`) confirmed to carry the `if sibling.is_file(): sibling.unlink()`
guard. `test_directory_sibling_does_not_abort_the_clean_loop`
(`test_spawn.py:1377-1401`) read in full: exercises exactly the guarded code path
end-to-end via `spawn.main()` with two dead workspaces, asserting the loop reaches
and removes the second workspace (proving no abort) and that the directory sibling
survives (proving the guard skips rather than crashes or deletes). Whether this
test is an adequate reproduction of the proposal's requirement 3 (worded "안전한
디렉터리 형제 처리") is a phase-2 judgment.

**Item 4 — `gates/flows.py` ledger-schema consumer non-breakage.**
`gates/flows.py:306-338` read in full: both sites that read a ledger entry's
`outcome` field treat it as an opaque string (a session-view field at line 316, a
dict-key bucket at lines 328/338) — no branch anywhere in the file matches against
a specific outcome value. A new value (`"progressed-dirty-tree"`) added to the set
of possible `outcome` strings cannot break either site by construction; no other
occurrence of `outcome` exists in `gates/flows.py` (5 total `grep` matches, all
accounted for above).

## Bisection candidate — the two issue-201-registered tests' fail→pass transition

The invoking prompt names an orchestrator hypothesis: that `1c230db`'s deletion of
`.warrant-hunt.count` removed a dirty condition inside
`Ledger::test_entry_carries_the_live_log_path` and
`IssueScopedPrompt::test_preparation_and_preamble_happen_once`, causing their
flip from failing to passing.

Facts gathered this session bear directly on this, without yet rendering the
verdict this role's phase-1 facet prohibits:

1. `1c230db`'s full diff (`git show 1c230db --stat`, read above) touches exactly
   three files: `.warrant-hunt.count` (deleted), and two new
   `docs/issue-197/...` files. It does not touch `test_spawn.py` or `spawn.py` at
   any line.
2. `6a54d5a`'s full diff (`git show 6a54d5a`, read above) touches exactly
   `test_spawn.py`, at exactly the two test bodies named in the invoking prompt,
   replacing each test's post-session `roster.read_text()` lookup with a
   call-through-spy-captured value. The commit message states the root cause
   (`KeyError` from reading the roster after the session's own `roster_remove`)
   and the fix in its own words.
3. `1c230db` is chronologically and causally *upstream* of `6a54d5a` (author dates
   2026-08-02T08:13:28Z and 2026-08-02T10:34:28Z respectively, per `git log`;
   `1c230db` reachable as an ancestor of `main` before `6a54d5a` was authored) —
   but upstream-in-time is not the same as causally connected, and no line in
   `1c230db`'s diff is capable of altering either test's outcome, since neither
   file it touches is imported or read by either test.
4. Issue #201's own survey (`docs/issue-201/reports/implementation/survey.md`,
   read above) independently reproduced the pre-fix failure as `KeyError` on a
   roster-dict key lookup — not a git-dirty-tree-shaped assertion failure or
   error — and explicitly logged `.warrant-hunt.count`/`clean`/`fail_closed_downgrade`
   (D3) as "not re-encountered" in that investigation.
5. A second, independent, later-discovered failure mode exists for these same two
   tests (issue-204's survey, read above): under `TOKENMAXXXER_RULEBOOKS`/
   `TOKENMAXXXER_CORE` unset, both tests fail via `rulebook_checkout`/`core_root`'s
   sandbox network-clone artifact — a completely different mechanism, also
   unconnected to `.warrant-hunt.count`, and the issue-205 implementation record's
   own §검증 2 attributes its session's observed 18-failure baseline (which
   includes these same two tests as individually re-checked) to this same class.

Whether the orchestrator hypothesis holds, and whether "fixed" (issue-201's
deliberate approved change) or "condition disappeared" (an incidental side effect)
is the correct characterization, is the phase-2 judgment this survey defers —
the evidence above is presented as read-and-cited facts, not a rendered verdict.

## Other candidates surfaced while reading the diff (not evaluated)

- **`docs/issue-205/reports/implementation.md`'s frontmatter `code_under_review`
  field cites `ee0c74067102a57702d740b7657b385b29269875`**, which `git show ee0c740 --stat`
  (read above) confirms is the phase-1 proposal-revision commit — a docs-only
  commit touching `docs/issue-205/proposals/session-end-defects.md` and
  `docs/issue-205/reports/implementation/survey.md`, with no `spawn.py`/
  `test_spawn.py`/`.gitignore` change at all. The three test-run results the same
  frontmatter's `closed_checks` report (13 passed isolated run, 135 passed/18
  failed full suite, manual gitignore check) could only have been produced
  against the actual code change, `ded7993` (PR #210's sole commit, which also
  contains this very record file) — `ee0c740` predates `ded7993` by about 12
  minutes and contains none of the code those checks exercise. Not evaluated as a
  deficiency here — reserved for phase 2's step-level check, alongside whether it
  is a mechanical citation slip (e.g., a stale value carried over from drafting
  against the proposal revision) or points to something more substantive.
- **Issue #205 itself has no close/reopen event** (`gh api .../issues/205/events`
  → `[]`), unlike issue #197's precedent (closed twice). The issue's own `## 실행
  계획` checklist (read via `gh issue view 205`) shows step 1 `[x]`, step 2 `[ ]` —
  consistent with this role's own gate not yet being satisfied. Not a deficiency,
  a process-state fact.
- **Approval-to-merge latency**: `APPROVE issue-205/implementation` posted
  2026-08-02T12:19:34Z; PR #206 merged 2026-08-02T12:19:36Z, 2 seconds later —
  consistent with the same near-instant automated-merge-on-approval pattern
  issue-197's execution-observation record already documented (3-second gaps on
  two independent PRs there). Noted as a recurring pattern, not evaluated as a
  deficiency.
- **The mid-phase-1 constraint relaxation** (`ee0c740`'s commit message: "PR #206
  feedback (orchestrator relay, user decision): the 'existing tests unchanged'
  constraint is relaxed for tests that assert the defect itself") happened
  *before* PR #206 merged (`ee0c740` authored 12:17:14Z, PR #206 merged
  12:19:36Z, both inside the same PR/branch) — i.e., this was a phase-1-internal
  revision responding to review feedback on the still-open phase-1 PR, not a
  phase-2 deviation. Not evaluated as a trajectory concern here — a candidate for
  phase 2 to confirm this characterization against the full PR #206 review
  history (not yet read this session — PR #206's own comments/reviews were not
  fetched).

## Not this role's job to resolve

Per this role's standing prohibition, no code under observation (`spawn.py`,
`gates/flows.py`, `test_spawn.py`) was executed this session — only `gh`/`git`
read commands against `main`, PR #206, PR #210, and issues #205/#201/#204, plus
direct file reads via the `Read` tool. No file under `spawn.py`, `.gitignore`,
`test_spawn.py`, `gates/flows.py`, or the `implementation` role's own
`docs/issue-205/` artifacts was written or edited this session or on this branch.
