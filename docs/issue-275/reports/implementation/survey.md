# Survey — issue #275 (phase 1)

HEAD at survey time: `e2bef37` (merge of PR #274, issue #271 step 2). All
four files this issue's findings point at — `gates/ci.py`, `spawn.py`,
`gates/test_closes_gate_ci.py`, `docs/handbooks/operations.md`,
`test_spawn.py`, `docs/issue-271/reports/implementation.md` — are byte-
identical to their state at `c6c4363` (`git log c6c4363..HEAD -- <those
paths>` is empty; `e2bef37` only added
`docs/issue-271/reports/execution-observation.md` and its `reports/
execution-observation/` dir). So every line number the source record
(`docs/issue-271/reports/execution-observation.md`) cites "@ `c6c4363`"
still resolves at HEAD, and this survey cites bare `file:line` throughout
without repeating the `@ sha` suffix.

## F3 — `_phase_from_approval`'s PR-comment union

`gates/ci.py:144-162` defines `_phase_from_approval(repo, pr, issue,
role)`. Body (`:155-162`):

```
subject = f"issue-{issue}"
approvers = spawn._approvers(repo)
comments = spawn._issue_comments(repo, issue)      # :157
comments += spawn._issue_comments(repo, pr)         # :158 — the widening
reviews = _pr_reviews(repo, pr)
pr_dict = {"reviews": reviews or []}
approved = flows._pr_approved(pr_dict, comments, approvers, subject, role)
return "phase2" if approved else "phase1"
```

`spawn._issue_comments(root, number)` is at `spawn.py:831-857`. Its own
docstring (`:832-834`) states the mechanism precisely: GitHub serves both
issue and PR conversation comments from the same `/issues/<n>/comments`
endpoint, so passing a PR number returns that PR's conversation-tab
comments, not review comments. There is no response-side way to tell
"this comment happened to be posted under an issue's own thread" from
"this comment was posted on a PR's conversation tab" once you've chosen
which number to query — the two are different fetches, not a filterable
union of one fetch. `flows._pr_approved` (`gates/flows.py:130-143`) does
no fetching itself; it takes whatever `comments` list its caller hands it
and applies the exact-string/approvers test, so the widening is entirely
`_phase_from_approval`'s doing, not a defect in the reused function.

Contract text is unambiguous and lives in two places, English and
Korean, word for word: `protocol.md:239-246` — "The canonical location
for the `APPROVE issue-<n>/<role>` signal (contract v3 s19) is the
**issue comment**, not a PR comment or PR review... A PR review Approve
is only the two-account hardened alternative" — and
`protocol.ko.md:189-195`, the same claim in Korean. Both name issue-126
as the incident that already happened once from signal-location drift.

**This codebase already contains both the correct pattern and two other
instances of the same widening**, none of them F3's target but all
relevant to scoping the fix:

- Correct, issue-only: `gates/closure_sweep.py:132` —
  `spawn._issue_comments(root, issue)`, no PR union. (Different purpose:
  dedup-marker check for a posted sweep comment, not an approval
  predicate — but the call shape is exactly what F3 wants.)
- Same widening, different consumer: `gates/flows.py:295-304`,
  `comments_for()` — unions issue + PR comments for the status
  dashboard's `_pr_approved` calls (`:318`, `:342`). This feeds
  `decision_queue`/`unapproved_open_prs`, both informational displays,
  not a merge-blocking gate.
- Same widening, different subject: `spawn.py:896-935`
  (`approve_scope`), the `scope-approved` transition gate (issue #115).
  `:930-935` unions `_issue_comments(root, issue)` with
  `_issue_comments(root, pr)` whenever a PR exists — despite a code
  comment two lines above (`:930-932`) asserting "이슈 댓글이 승인
  정본이다... PR 댓글은... fallback 이지 대등한 소스가 아니다," the code
  doesn't actually implement fallback semantics (try issue first, only
  consult PR if no match) — it unions unconditionally, same shape as
  F3.

Issue #275 names only `gates/ci.py`'s `_phase_from_approval` /
`spawn._issue_comments(repo, pr)` call. The other two sites are read-only
context for this survey, not in this issue's write set.

`gates/test_closes_gate_ci.py:129-197` carries five `_phase_from_approval`
cases (`t_phase_from_approval_no_signal_is_phase1:129`,
`_qualifying_issue_comment_is_phase2:142`,
`_non_approver_comment_is_phase1:157`, `_wrong_role_comment_is_phase1:171`,
`_pr_review_approve_from_differing_account_is_phase2:186`). Every one
mocks `spawn._issue_comments` as `lambda repo, n: [...] if n == 245 else
[]` — the qualifying comment is only ever returned for `n == 245` (the
issue number used throughout the fixture's `pr=1`), so the mock silently
answers `[]` for the second (`pr`) call in every case. None of the five
posts an approval-shaped string under the PR's own number to check it is
rejected. That is the missing red-green pair requirement 1 asks for.

## F2 — Korean/English mirror divergence in `docs/handbooks/operations.md`

`## 머지 게이트 (CI)` (Korean) runs `:743-760`. The phase-derivation
sentence at `:749-750` reads "phase는 본문의 closing 키워드 유무에서
끌어낸다" — this is `_phase_from_body`, deleted at `1cab34b`
(issue #271's landing commit). `## Merge gate (CI)` (English) runs
`:762-804` — noticeably longer than the Korean block. `:769-770` only
covers issue-number/role extraction from the branch name (does not
itself claim anything about phase); the actual phase-derivation content
lives in two paragraphs that have **no Korean counterpart at all**:
`:784-795` (phase comes from a human approval event — single-account
issue/PR comment or two-account PR review Approve — not from closing-
keyword presence; cites `flows.py`'s `_pr_approved`, the predicate-
coupling fix, issue #245's F1) and `:797-804` (the three-surface
`_phase1_surface_mismatch` expansion: body/title/commit messages).

One more consequence for sequencing: `:785-786`'s current English text
itself documents the still-open F3 bug — "a qualifying `APPROVE
issue-<n>/<role>` issue/PR comment" (emphasis on "issue/PR"). If F2 is
done by mirroring today's English into Korean, it would faithfully
translate a bug description. F2's phase-2 work has to target the
post-F3-fix behavior (issue comment only), which means F2 depends on F3
landing first, or at minimum on F3's target wording being decided before
either doc edit is written.

## F1 — stale line citations in the restored drain-guard test

The restored test is `test_follow_prioritizes_pending_session_end_over_pid_check`
at `test_spawn.py:3749-3788`. Its own comment (`:3749-3765`) makes two
citations, both stale post-rebase:

- `:3754` — "spawn.py:1884-1894 의 드레인-우선 블록이 지키는 순서." The
  guard it means is the `if events_path.exists(): ... continue` block
  that re-checks for a pending `session-end` before trusting a dead
  `wrapper_pid` — currently at `spawn.py:1943-1953` (comment `:1943-1948`
  + code `:1949-1953`, inside `_watch`'s `--follow` loop,
  `spawn.py:1906-1970`). `spawn.py:1884-1894` at HEAD instead falls
  inside the non-`--follow` `_await_bounded` function's stall/size-
  polling code — a different function entirely.
- `:3762` — "test_spawn.py:3480-3485," meant to point at the sibling test
  that builds the same dead-`wrapper_pid` fixture,
  `test_follow_detects_dead_session_and_returns_crash_rc`. That test is
  currently at `test_spawn.py:3719-3747`. `:3480-3485` at HEAD lands
  inside an unrelated fixture (a `flows` plan-parser test region, per the
  execution-observation record's own check).

`docs/issue-271/reports/implementation.md` (the landed, `loop_state:
landed` role record for issue #271, not owned by issue #275 but named by
its own F1 finding) carries two `closed_checks` entries citing the same
stale spot:

- `:19-23` (red proof) — `ref: test_spawn.py:3497`
- `:24-27` (green proof) — `ref: test_spawn.py:3497`

Both should resolve to `test_spawn.py:3749`, the test's current `def`
line.

Background on citation style: `docs/issue-227/reports/execution-
observation.md:265-268` — a different role's execution-observation, not
this issue — already names this exact failure class: "The refs read as
wrong against today's `main` only because [later commits] shifted
`run.md` afterwards — a property of unpinned line citations in this
repo's record convention, not an error by this role." That record treats
drift as a known, forgivable property of the dominant convention (bare
`file:line`, no commit qualifier) rather than grounds to switch styles.
Meanwhile, this repo's execution-observation reports (including
`docs/issue-271/reports/execution-observation.md` itself, throughout)
consistently use a different, sha-qualified style for citations of
frozen history: `` `file:line` @ `sha` ``. Two different artifact classes,
two different existing conventions already in this repo — the proposal
must pick which applies to test-file self-comments vs. a landed record's
`closed_checks` refs, not invent a third style. See scout-brief for the
resolved decision.

## F4 — requirement 4's red proof is a missing-symbol crash, not a behavioral demonstration

`docs/issue-271/reports/implementation.md:7-12` (frontmatter
`closed_checks`) records the red proof as: "new tests referencing
not-yet-existing API crash with `AttributeError: module 'ci' has no
attribute '_pr_title'`." That is evidence the new API (`_pr_title`,
added in the same commit that fixed the gap) did not exist yet in the
pre-fix tree — not evidence that the pre-fix gate, given a clean body and
a commit-message-only closing keyword, actually let it through.

The green half is solid and stays as-is:
`gates/test_closes_gate_ci.py:322-348`
(`t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body`)
arranges clean body/title, no approval, commit messages
`["proposal work", "Closes #245"]`, drives the real
`_autodetect_issue_phase` → `check(..., closes_only=True)` composition,
and asserts the block cites `커밋 메시지에`.

A genuinely behavioral pre-fix counterfactual is available without
reverting any code: `gates/ci.py:165-169` still defines
`_phase1_mismatch(body, issue)`, the single-surface (body-only) checker
kept byte-for-byte as the pre-#271 predicate shape (its own docstring:
"기존 단위테스트가 이 시그니처를 직접 부르므로 그대로 유지한다"). Calling
`ci._phase1_mismatch(clean_body, 245)` where `clean_body` has no closing
keyword returns `[]` regardless of what the commit messages contain,
because the pre-#271 predicate never looked at commit messages at all —
that is the actual, live, still-runnable old code path, and asserting
`== []` against it while the paired new-path test blocks the identical
scenario is the behavioral red the finding asks for.

## Write set phase 2 will need

- `gates/ci.py` — F3: remove the `spawn._issue_comments(repo, pr)` line
  and its accumulation in `_phase_from_approval`.
- `gates/test_closes_gate_ci.py` — F3: new red-green case(s) proving a
  PR-comment union no longer flips phase2; F4: new case pairing the old
  single-surface `_phase1_mismatch` (no block) against the existing
  multi-surface green (blocks) for the same commit-message-only
  scenario.
- `docs/handbooks/operations.md` — F2: Korean `## 머지 게이트 (CI)`
  section brought to parity with the (F3-corrected) English section.
- `test_spawn.py` — F1: fix the two stale citations in
  `test_follow_prioritizes_pending_session_end_over_pid_check`'s comment
  (`:3754`, `:3762`).
- `docs/issue-271/reports/implementation.md` — F1: fix the two
  `ref: test_spawn.py:3497` `closed_checks` entries (`:23`, `:27`) to the
  correct current location.

## Unknowns / gaps for scouting

- Whether GitHub's REST API offers any per-comment marker (e.g. an
  `html_url` substring, an `issue_url` field) that would let a single
  fetch distinguish "posted while this number was viewed as an issue"
  from "posted while viewed as a PR" — relevant to whether F3's fix
  should filter a response or simply not issue the second fetch.
  (Resolved in scout-brief: no such filter is needed or exists; the
  fetch itself, not its contents, is the problem.)
- Whether to sha-pin the corrected citations (issue #227's execution-
  observation background) or match the plain `file:line` convention
  already dominant in this repo's `*.py` comments. (Resolved in
  scout-brief.)
- Exact Korean phrasing parity bar for F2: whether "문면 일치" requires
  translating the two English-only paragraphs (`:784-795`, `:797-804`)
  in full, or only removing the direct contradiction at `:749-750`.
  (Resolved in scout-brief and stated in the proposal's Rationale.)
