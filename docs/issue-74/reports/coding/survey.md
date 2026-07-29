---
subject: issue-74
role: coding
kind: survey
loop_state: surveyed
code_under_review: 1fb59e5d9322162b5f5cf09872a3c69eebaa8be6
---

# Survey — issue-74

## Scope
Issue #74, "the self-check suite is dead: test_gates.py crashes on its
first test" (https://github.com/tokenmaxxxer/muster/issues/74), reports
five bullets under "What is broken" — four conceptual root causes in
total, since bullets 3 and 4 are two instances of one cause (v3 abolished
the per-repo contract copy). "Done when" is defined as all three of
`python3 test_gates.py`, `python3 test_spawn.py`, and
`bash tests/run-orchestrate-tests.sh` passing, and the issue mandates TDD
discipline: watch each fail first, then fix. The README's self-check
pointer (README.md:439-443) is a `## Self-check` section whose bash block
is `python3 test_gates.py`. Environment: Python 3.11.8, Darwin, macOS
26.5.2.

## Red state as found
Captured once, before the tree was wiped by the sixth defect below. Not
re-captured since: re-running `bash tests/run-orchestrate-tests.sh` in
this sandbox is destructive (see below), so its red-state evidence here
is the one surviving capture.

### (A) `python3 test_gates.py` → exit 1
```
  ok  t_board_absent_names_the_v1_location
Traceback (most recent call last):
  File "test_gates.py", line 619, in <module>
    t()
  File "test_gates.py", line 44, in t_board_reads_loop_state
    assert list(b) == ["2026-07-26-wash"], b
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {}
```
The runner at test_gates.py:616-621 is a bare loop with no per-test
try/except, so the first uncaught exception aborts the whole script —
exactly one test ever reports `ok`.

### (B) `python3 test_spawn.py` → exit 1
unittest, "Ran 54 tests ... FAILED (errors=1)". The single error:
```
ERROR: test_preparation_and_preamble_happen_once (__main__.IssueScopedPrompt.test_preparation_and_preamble_happen_once)
  File "test_spawn.py", line 674, in test_preparation_and_preamble_happen_once
    spawn._spawn_one(str(work), "qa", "원래 맡긴 일.\n", ...)
  File "spawn.py", line 1605, in _spawn_one
    plugins = plugin_dirs(role, spec)
  File "spawn.py", line 216, in plugin_dirs
    d = rulebook_checkout(role, spec)
  File "spawn.py", line 189, in rulebook_checkout
    sys.exit(f"[{role}] 룰북을 받지 못했다: {repo}\n  {r.stderr.strip()[:200]}")
SystemExit: [qa] 룰북을 받지 못했다: tokenmaxxxer/qa-agent-rulebook
  fatal: cannot copy '/Applications/Xcode.app/.../hooks/commit-msg.sample' to '.../runs/rulebooks/tokenmaxxxer...'
```

### (C) `bash tests/run-orchestrate-tests.sh` → exit 1
```
ok     hooks.json wires SessionStart+UserPromptSubmit+PreToolUse
ok     directive-injects                  x
FAIL   directive-silent-for-roles         want=0 got=       0
ok     guard-docs-in-board                deny
FAIL   guard-src-in-board                 want=deny got=exit-127
FAIL   guard-approvers-ok                 want=allow got=exit-127
FAIL   guard-nonboard-repo                want=allow got=exit-127
FAIL   guard-outside-trees                want=allow got=exit-127

== 3 passed, 5 failed ==
```

## Root causes, located

### Cause 1: board fixture builds a v2 shape, spawn.board() reads v3
Fixture `_board()` at test_gates.py:20-27 builds
`docs/<subject>/<role>.md` (its docstring still says "계약 v2 §10").
Reader `spawn.board()` at spawn.py:773-789 requires
`docs/issue-<n>/reports/<role>.md`: it iterates `docs/` children matching
the regex `^issue-[0-9]+$` and then looks in that dir's `reports/`
subdirectory. `BOARD = "docs"` and `MARKER = "docs/specs/approvers.md"`
are at spawn.py:618-622. There is no schema-version constant anywhere in
spawn.py — "v3" is encoded only by that inline regex plus the hardcoded
`reports/` segment. `LEGACY` (spawn.py:620-622) models v1's flat
filenames (`review-record.md` etc.) and is exercised by
`t_board_absent_names_the_v1_location` (test_gates.py:415-425) — the one
test that passes. "v2" was never implemented in code at all; it survives
only as a stale docstring label on this fixture.

Expected: v3 path shape. Actual: v2 path shape. Result: `board()` returns
`{}` for everything these fixtures build — the subject names used
(`"2026-07-26-wash"`, `"s"`) do not match `^issue-[0-9]+$`, and there is
no `reports/` segment either. Crash site: test_gates.py:44 in
`t_board_reads_loop_state` (function spans test_gates.py:38-52).

Full inventory of v2-shaped construction sites in test_gates.py — 18
total:
- fixture definitions embedding the shape: test_gates.py:20 (`_board`,
  builds path at line 23), test_gates.py:64 (`_wake_repo`, builds path at
  line 68)
- calls to `_board(`: test_gates.py:40, 57
- calls to `_wake_repo(`: test_gates.py:90, 97, 114, 131, 142, 167, 192,
  215, 247
- tests building a record path directly on top of a `_wake_repo()` root:
  test_gates.py:101, 115, 132, 134, 143

That is 2 + 2 + 9 + 5 = 18 sites. The issue's own count for this cause
was 12 call sites; the actual count found by walking every construction
site is 18. Stating this discrepancy rather than papering over it: the
issue's number appears to undercount either the fixture-definition sites
or the direct record-path-building sites (test_gates.py:101, 115, 132,
134, 143), which don't go through `_wake_repo(` as a call but still bake
in the v2 shape on top of its root.

Tests tripped: `t_board_reads_loop_state` (38-52),
`t_board_tolerates_trailing_comment` (54-61), and every `t_wake_*` test,
because `wakes._rows()` calls `spawn.board(root)` at wakes.py:235.

By contrast test_spawn.py already uses the correct v3 shape at its own
lines 424, 432-433, 507 — the defect is confined to test_gates.py.

### Cause 2: hypothesis fixture written to a path v3 never walks
`wakes._hypotheses()` at wakes.py:175-184 globs only
`docs/issue-*/proposals/*.md` (filtering frontmatter
`kind == "hypothesis"`). `_wake_repo()` at test_gates.py:64-75 creates
`docs/proposals/` and writes `docs/proposals/h.md` — no `issue-*`
segment, so the glob never matches.

Tests tripped: `t_wake_hypothesis_wakes_feasibility` (test_gates.py:88-91)
and `t_wake_acknowledged_hypothesis_goes_quiet` (test_gates.py:94-104).
Worth stating plainly: the second one asserts a negative, so it can pass
for the wrong reason — the hypothesis is invisible to `wakes._rows()`
rather than genuinely acknowledged.

### Cause 3+4: two tests call an API v3 deleted
Deleting commit: 613a5fbced1b08b48c4c8215a241d0b8a823dbcc — "init writes
approvers.md, not a contract copy; require_board replaces
require_contract". `grep -rn "contract_drift\|init_contract\|require_contract\|CONTRACT" --include="*.py" .`
hits only test_gates.py, at lines 262, 264, 269, 271, 272, 383, 390, 392,
393, 395, 396, 400, 401. Zero hits in spawn.py, wakes.py, gates/.

- `t_contract_drift_is_detected_by_content`, test_gates.py:383-401 —
  calls `spawn.contract_drift` (first at line 390), `spawn.init_contract`,
  `spawn.CONTRACT`. Fails with AttributeError. The issue's direction:
  DELETE it, and leave a comment saying why so it is not reintroduced.
- `t_missing_contract_stops_the_spawn`, test_gates.py:254-272 — calls
  `spawn.require_contract` (first at line 262) and `spawn.CONTRACT`.
  Fails with AttributeError. The issue's direction: REPLACE it with the
  same intent against the v3 equivalent.

v3 equivalent: `require_board(cwd: str, override: bool) -> None` at
spawn.py:661-676. It returns early if `(root / MARKER).is_file()` or if
`override`, else `sys.exit(...)` with a message naming `MARKER` and
suggesting `python3 spawn.py init -C <root>`. Its docstring states the
intent explicitly: core's gate would refuse the write anyway, so this
says the same thing before a session is burned — "버려질 세션에 과금하지
않는다". Call sites in the spawn path: spawn.py:1393
`require_board(a.cwd, a.no_contract)` and spawn.py:1413
`require_board(a.cwd, a.no_contract or a.dry_run)`, both in CLI dispatch
before a session spawns.

`grep -n "require_board" test_gates.py test_spawn.py` returns nothing —
confirmed zero coverage anywhere, exactly as the issue claims. v3's
actual init mechanism is `init_board()` at spawn.py:632-648, which writes
`docs/specs/approvers.md` directly.

### Cause 5: BSD `wc -l` left-pads
tests/run-orchestrate-tests.sh:20
`lines=$(CLAUDE_ROLE=qa /bin/bash "$H/directive.sh" | wc -l)`
tests/run-orchestrate-tests.sh:21
`[ "$lines" = 0 ] && report x x directive-silent-for-roles || report 0 "$lines" directive-silent-for-roles`

Command substitution strips the trailing newline but not leading spaces,
so on macOS `$lines` is literally `"       0"` and the string compare is
always false. Observed: `FAIL directive-silent-for-roles want=0
got=       0`. The hook under test (directive.sh) is correct — it did
emit 0 lines; the test's comparison is what's broken.

## Sixth defect: the suite destroys its own checkout
Not named by the issue; found during this survey. This is the most
important finding in this document — **do not run
`bash tests/run-orchestrate-tests.sh` in this sandbox.**

tests/run-orchestrate-tests.sh:23-30, the `guard()` helper:
```
23  guard() { # want name file_path board(yes/no)
24    td="$(cd "$(mktemp -d)" && pwd -P)"; git init -q "$td"
25    [ "$4" = yes ] && { mkdir -p "$td/docs/specs"; echo "- u" > "$td/docs/specs/approvers.md"; }
26    printf '{"tool_name":"Write","tool_input":{"file_path":"%s","content":"x"},"cwd":"%s"}' "$td/$3" "$td" \
27      | env -u CLAUDE_ROLE /bin/bash "$H/deliverable-guard.sh" >/dev/null 2>&1
28    rc=$?; case "$rc" in 0) got=allow ;; 2) got=deny ;; *) got="exit-$rc" ;; esac
29    rm -rf "$td"; report "$1" "$got" "$2"
30  }
```

Mechanism: `mktemp -d` fails in this sandbox
(`mktemp: mkdtemp failed on /var/folders/.../T/tmp.XXXX: Operation not
permitted`). The assignment has no failure check, so `td` becomes the
empty string; `git init -q ""` and `rm -rf ""` then both resolve to the
current working directory, i.e. the repo root.

Observed live: `error: could not lock config file
/Users/jk/.../muster-issue-74-coding/.git/config` from the `git init`,
then a wall of `rm:
/Users/jk/.../muster-issue-74-coding/...: Operation not permitted` from
the `rm -rf`, which succeeded on every file NOT covered by the sandbox
write-deny list. That is what wiped this checkout: the whole working
tree vanished while only `.git/config` and `.claude/*` survived. Once
`orchestrate/` was gone, each later `guard()` call's
`deliverable-guard.sh` was missing, producing the four `exit-127` results
in (C) above.

Recovery performed: `git init` + manual `.git/HEAD` write + `git fetch
origin` + `git checkout -B issue-74/coding origin/main` (there is no
`origin/issue-74/coding` on the remote; remote branches are origin/main,
origin/issue-69/coding, origin/issue-72/coding). HEAD is now
1fb59e5d9322162b5f5cf09872a3c69eebaa8be6.

## Not caused by #74
- The test_spawn.py rulebook-clone failure (evidence B above): a `git
  clone` failure while copying the system git template hooks
  (`/Applications/Xcode.app/.../hooks/commit-msg.sample`) into the
  rulebook checkout at `rulebook_checkout` (spawn.py:189). This is an
  environment/template-copy problem in `spawn.py`'s clone invocation, not
  one of the four conceptual causes the issue names (board-shape
  mismatch, hypothesis-path mismatch, or the deleted contract API). It is
  the reason item 4 in the projected write set is conditional rather than
  committed.
- The four `exit-127` guard results in (C)
  (`guard-src-in-board`, `guard-approvers-ok`, `guard-nonboard-repo`,
  `guard-outside-trees`): these are collateral damage from the sixth
  defect above, not from anything issue #74 names. Once the checkout was
  wiped mid-run, `orchestrate/deliverable-guard.sh` no longer existed on
  disk for subsequent `guard()` calls to invoke, so each one exited 127
  ("command not found") rather than reflecting any real allow/deny
  decision about deliverable guarding.

## Projected write set
1. `test_gates.py` — fix `_board()` and `_wake_repo()` to build the v3
   shape and the v3 hypothesis path; update the 5 direct record-path
   sites; delete `t_contract_drift_is_detected_by_content` leaving a
   comment explaining why; replace `t_missing_contract_stops_the_spawn`
   with a `require_board()` test carrying the same intent.
2. `tests/run-orchestrate-tests.sh` — fix the `wc -l` comparison at line
   21; fix the unguarded `mktemp -d` at line 24 so a failed mktemp aborts
   instead of resolving to the cwd.
3. `docs/issue-74/reports/coding.md` — the role record (phase-2 output,
   written first thing in phase 2).
4. `spawn.py` — CONDITIONAL, only if the `test_spawn.py` failure is
   confirmed to be the git-template copy: narrow the clone in
   `rulebook_checkout` (spawn.py:~189) so it does not copy the system git
   hook templates.

Not in the write set: wakes.py, gates/, orchestrate/, README.md,
protocol.md.

## What did not work
The tree was wiped mid-survey by running (an early, unguarded probe of)
`bash tests/run-orchestrate-tests.sh`. Expected: a clean checkout to
observe the suite's red state in. Actual: the suite itself deleted the
checkout (see "Sixth defect" above) — the working tree vanished except
for `.git/config` and `.claude/*`.

Recovering it did not work cleanly either: `git init` and
`git checkout -B issue-74/coding origin/main` could not write
`.git/config` directly under this sandbox's rename-based-overwrite
write restriction (the sandboxed filesystem policy denies the
rename-into-place pattern git normally uses to update that file in a
freshly-initialized repo). HEAD had to be written by hand into
`.git/HEAD` instead of letting `git checkout -B` set it, before
`git fetch origin` and checkout could proceed.

## Hunt (phase 1)

Stance: end-of-phase-1 probe for a defect other than the five already
located above.

Finding: `wakes.py:335` — `subject = Path(f).parent.name` recovers the
wrong path component. Under v3 a role record lives at
`docs/issue-<n>/reports/<role>.md`, so `Path(f).parent.name` evaluates to
`"reports"` instead of `issue-<n>`. In the finding-to-coding branch
(`wakes.py:331-340`) this means the subject never resolves, and the
section-19 first-build approval gate is silently bypassed for every
finding addressed to `coding`.

Reproduction (as run by the hunter): build a v3-shaped fixture with a
feasibility record at `loop_state: probing` and a review record carrying
`addressed_to: coding`, then call `wakes.evaluate()`; `coding` appears in
`woken` with `blocked` empty, when it should be blocked.

Why the suite never caught it: `test_gates.py:139-148` is the only
`addressed_to:` coverage in the suite and it never targets `coding`, so
this branch is never exercised.

Corroborating: `spawn.board()` (`spawn.py:773-789`) keys the board by the
issue-directory name, not by `"reports"` — confirming which component
`wakes.py:335` should have read.

Disposition: OUT of the frozen write set for this issue. Raised in the
proposal as an approver decision; not fixed unilaterally.

Full report: `docs/issue-74/reports/coding/hunt-phase1.md`.
