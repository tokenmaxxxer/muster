Skip condition: pure bugfix (scout-directive skip condition 1). #432's
cause is already established in the issue text (measured pytest failure +
root cause diagnosis by the reporting session); this session's job is the
fix, the `ok=False` decision, and the call-site sweep — no product-shaped
or design-open surface to scout.

## Current state (write set)

- `spawn.py:963` — `_issue_comments(root, number) -> tuple[list[dict], bool]`,
  changed by #287.
- `spawn.py:1859-1861` (`_post_stall_comment`) and `spawn.py:1883-1885`
  (`_post_stranded_push_comment`) — both call `_issue_comments` with the
  pre-#287 shape (`for c in _issue_comments(...)`), both added/touched on
  #326's branch. `spawn.py:1884` is the one named in #432; `spawn.py:1860`
  is the same defect, undetected by #432's own pytest run apparently
  because the failing tests happened to route through the stranded-push
  path first — confirmed independently in this session.
- `spawn.py:1835` (`_post_crash_comment`) already uses the correct
  `comments, ok = ...; if ok and any(...)` pattern — this is the
  established convention to match.
- `spawn.py:1070-1073` and `gates/ci.py:154`, `gates/flows.py:308,314`,
  `gates/closure_sweep.py:163` — all already updated correctly by #287.
- `test_spawn.py` — `PostStallComment` and the stranded-push test class
  mock `spawn._issue_comments` with the old list-only shape; these mocks
  need updating alongside the fix or they stop testing the real
  contract.

## Full sweep for other exposed call sites

`grep -rn "_issue_comments(" --include=*.py .` (excluding the def and
test mocks) returns exactly 9 call sites, all listed above; all now
unpack `(comments, ok)`. No other call site exists.
