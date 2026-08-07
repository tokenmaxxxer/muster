---
code_under_review: spawn.py, test_spawn.py
loop_state: done
---

# Issue #432 — fix `_issue_comments` tuple-shape call sites

## What was done

Fixed the two remaining call sites of `spawn._issue_comments` that still
used the pre-#287 `list[dict]` return shape (`spawn.py:1860` and
`spawn.py:1884`), pinned the `ok=False` behavior decision with regression
tests, swept the repository for any other exposed call site (none found),
and confirmed the full suite is green.

## Why

#287 and #326 each correctly implemented their own branch but could not
see the other's concurrent change — #287's shape change never touched
#326's new call site, and #326's call site was written correctly against
the shape that existed on its own branch at the time. The defect is a
property of the merged tree, not of either PR in isolation (per #390,
cross-referenced in #432). Fixing it requires updating the surviving call
sites to the shape #287 established, and closing the `ok=False` gap that
#287's own principle ("could not check is not a pass") already answers.

## Root cause (established in the issue, not re-investigated)

#287 changed `spawn._issue_comments` from `list[dict]` to
`(list[dict], ok: bool)` and updated its then-existing four call sites.
#326, developed concurrently on a different branch, added a new call site
(`spawn.py:1884`, inside `_post_stranded_push_comment`) using the old
shape. The defect exists only in the merged tree.

## Scope 1 — fix the call site(s) and decide `ok=False`

The sweep (below) found the defect at **two** sites, not one:
`spawn.py:1860` (`_post_stall_comment`) in addition to the one named in
the issue, `spawn.py:1884` (`_post_stranded_push_comment`). Both are
idempotent marker checks of the same shape as `_post_crash_comment`
(`spawn.py:1835`, already correct).

Decision on `ok=False`: **post anyway** (accept a possible duplicate
comment), not "assume already posted and skip." Per #287's own principle
— "could not check is not a pass" — treating an unreadable comment list
as equivalent to "marker already there" would let a real alert (respawn
capped, session stranded) go silently unposted whenever the GitHub API
read fails. A duplicate alert comment is a minor annoyance; a dropped
one defeats the whole point of these functions. This also matches the
pre-existing convention in `_post_crash_comment` (`if ok and any(...)`),
so all three idempotent-comment functions now agree.

Fix applied to both `spawn.py:1859-1861` and `spawn.py:1883-1885`:
unpack `comments, ok = _issue_comments(root, issue)` and gate the skip on
`ok and any(marker in c.get("body", "") for c in comments)`.

Pinned with tests in `test_spawn.py`:
- `PostStallComment.test_posts_when_comments_unreadable`
- `EnsurePushed...test_ensure_pushed_stranded_comment_posts_when_comments_unreadable`
(both assert a comment call still fires when `ok=False` even though the
marker is present in the stale/unreliable list returned).

## Scope 2 — exhaustive call-site sweep

`grep -rn "_issue_comments(" --include=*.py .` (excluding the `def` and
test mocks) — 9 call sites total:

- `spawn.py:1070` (`comments, issue_ok = ...`) — already correct.
- `spawn.py:1073` (`pr_comments, pr_ok = ...`) — already correct.
- `spawn.py:1835` (`_post_crash_comment`) — already correct.
- `spawn.py:1860` (`_post_stall_comment`) — **fixed this session**.
- `spawn.py:1885` (`_post_stranded_push_comment`) — **fixed this session**
  (the one named in the issue, at the pre-fix line number 1884).
- `gates/ci.py:154` — already correct.
- `gates/flows.py:308`, `gates/flows.py:314` — already correct.
- `gates/closure_sweep.py:163` — already correct.

No other call site exists; the sweep is exhaustive over the repository's
`.py` files.

## Scope 3 — cross-record on #398 / #290

Not resolved here by design (#432's own scope says not to duplicate).
This record documents the incident; the reporting session's issue body
already cites #398 and #290 as bearing this evidence. Cross-posting to
those issues is left to the user/next session per the standard
issue-authorship boundary (this session does not file/comment on issues
outside its own).

## What did not work

None — the fix, sweep, and tests landed on the first pass; no attempt was
undone or replaced.

## Open findings

None outstanding. The scope-2 sweep is exhaustive (see above) and found
no further exposed call site. Scope 3 (pre-merge suite gate) is
explicitly not resolved here — it is cross-referenced to #398/#290, which
remain open and own that follow-up.

## Acceptance

`python3 -m pytest -q --ignore=gates` on this branch: **418 passed**
(0 failed), up from 3 failed / 413 passed at the top of the issue. New
regression tests for the `ok=False` decision are included in that count.

## Doc placement

- Decision (return-shape call-site fix + `ok=False` choice): this record
  and the phase-1 proposal
  (`docs/issue-432/proposals/2026-08-07-fix-issue-comments-tuple-callsite.md`).
- No new env var, dependency, or migration — no handbook update needed.
