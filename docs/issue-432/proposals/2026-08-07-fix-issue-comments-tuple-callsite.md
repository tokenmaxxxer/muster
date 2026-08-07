---
status: approved
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-432/reports/implementation.md
---

Skip condition: pure bugfix. #287 changed `spawn._issue_comments` from
`list[dict]` to `(list[dict], ok: bool)` and updated its four then-existing
call sites correctly; #326, developed concurrently on a different branch,
added a new call site at `spawn.py:1884` using the old shape. The defect
exists only in the merged tree — neither branch could see the other. No
design decision is open except the `ok=False` behavior named in #432
scope item 1, which is decided and recorded in the rationale below, not
left for review.

## Request

Fix `main`'s test suite regression (#432): a call site added by #326 uses
`_issue_comments`'s pre-#287 return shape and crashes with
`AttributeError: 'list' object has no attribute 'get'`.

## Constraints

- Do not re-litigate #287's tuple-shape decision — only fix callers.
- Do not solve "no pre-merge suite run" here (#398 scope 3 / #290); cross-
  record only.
- `ok=False` behavior must be a stated decision, pinned by a test.

## Rationale

Two behaviors were considered for the `ok=False` (comments unreadable)
path in the idempotent marker checks (`_post_stall_comment`,
`_post_stranded_push_comment`): (a) treat unreadable as "marker absent,
post anyway," risking a duplicate alert comment, or (b) treat unreadable
as "assume already posted, skip." Option (b) was rejected: #287
established that "could not check is not a pass," and these functions
exist to guarantee a human gets paged when respawn/push is stuck — a
silently dropped alert (false negative) is worse than an occasional
duplicate comment (false positive). This also matches the existing
pattern already used in `_post_crash_comment` (`if ok and any(...)`),
so the fix makes all three functions consistent instead of introducing a
second convention.

## What will be done

- Fix `spawn.py:1860` (`_post_stall_comment`) and `spawn.py:1884`
  (`_post_stranded_push_comment`) to unpack `(comments, ok)` and only
  skip posting when `ok and marker found`, matching
  `_post_crash_comment`'s existing pattern.
- Sweep all call sites of `_issue_comments` for the same exposure;
  report the list.
- Add regression tests pinning the `ok=False` -> post-anyway decision for
  both fixed functions.
- Fix stale test mocks in `test_spawn.py` still using the pre-#287 list
  return shape.
- Cross-record this incident as evidence on #398 and #290.

## Out of scope

- Adding a pre-merge full-suite CI gate (#398 scope 3, #290).
- Any change to `_issue_comments`'s own signature or #287's tuple
  decision.

## How you'll know it worked

`python3 -m pytest -q --ignore=gates` passes on this branch; the `ok=False`
tests fail if the chosen behavior regresses; the call-site sweep result is
recorded.
