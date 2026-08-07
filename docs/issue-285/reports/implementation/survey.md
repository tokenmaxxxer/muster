files:
- spawn.py
- test_spawn.py

# Survey — issue #285 (spawn latency: sleep, redundant git, unbounded network)

## Write set

- `spawn.py` — all five fixes land here (P1-P5).
- `test_spawn.py` — phase 2 will add/extend: a warm-spawn timing test, a
  `rulebook_checkout` call-count test, a workspace-fetch call-count test,
  and a network-timeout-behavior test. `test_spawn.py` already has the
  scaffolding for this style of test (see below).
- `docs/issue-285/reports/implementation.md` — phase 2 writes this; not
  touched in phase 1.

No other files were found to reference the functions in scope
(`rulebook_checkout`, `_await_bounded`, `issue_workspace`,
`checkout_issue_branch`, `_fetch_or_halt`, `_git_env`, `ensure_rulebook`) —
`grep -rn` for each name outside `spawn.py`/`test_spawn.py`/`docs/` turned up
nothing.

## Confirmed current state (line numbers re-verified against HEAD, not taken
on faith from the issue body — they had drifted by a few lines in places)

### P1 — flat 2s sleep

- `_await_bounded()` — `spawn.py:1875-1918`. `time.sleep(2)` is the last
  line of the polling loop, confirmed at `spawn.py:1918`. The loop polls
  `events_path` (a jsonl file) for a new line and separately tracks
  `log_path`'s size for stall detection. Docstring cites issue #114 for the
  "don't block forever" contract — that contract (bounded return on either
  event-append or stall) is not touched by this fix, only the poll cadence.

### P2 — `rulebook_checkout` called 3x per spawn

- `rulebook_checkout(role, spec)` — `spawn.py:177-210`. The git pull is at
  `spawn.py:201` (`git -C <d> pull -q --ff-only`, `capture_output=True`, no
  `text=True`, no `timeout=`).
- Three call sites confirmed:
  - `checkout_version()` — `spawn.py:213-226`, calls `rulebook_checkout` at
    `spawn.py:216`.
  - `plugin_dirs()` — `spawn.py:229-252`, calls `rulebook_checkout` at
    `spawn.py:236`.
  - `ledger_write()` — `spawn.py:2012+` — need to trace its call path to
    confirm it goes through `checkout_version`/`plugin_dirs` rather than
    calling `rulebook_checkout` directly; either way the net effect (3
    pulls of the same marketplace per spawn) matches the issue's measured
    0.90s.
- Existing memoization precedent: `_GH_TOKEN_CACHE` — a module-level
  `str | None` global at `spawn.py:2508`, read/written inside
  `_resolve_gh_token()` (`spawn.py:2511-2534`) with the documented rationale
  "so `issue_workspace`/`checkout_issue_branch` calling `_fetch_or_halt` up
  to twice per spawn doesn't shell out to `gh auth token` twice." This is
  exactly the P2 shape — a per-process, not per-call, cache — and is the
  pattern to copy: a module-level dict (keyed on `spec["marketplace"]`
  since there can be more than one role/marketplace per orchestrator
  process) rather than a single scalar cache.

### P3 — workspace fetched twice

- `issue_workspace(cwd, issue, role)` — `spawn.py:2580-2654`. Three
  `_fetch_or_halt` call sites inside it, only one of which runs per
  invocation depending on branch: reused src (`spawn.py:2622`), reused work
  dir (`spawn.py:2625`), or new clone (`spawn.py:2651`, via `after=`).
- `checkout_issue_branch(cwd, issue, role)` — `spawn.py:2657-2683`. Calls
  `_fetch_or_halt(cwd, "브랜치 체크아웃")` unconditionally at
  `spawn.py:2667`, with no knowledge of whether `issue_workspace` was just
  called against the same `cwd` moments earlier.
- These two functions are independent (no shared state passed between
  them today) — confirmed by reading both signatures; the caller (not
  shown in this excerpt, presumed in `_spawn_one`) calls
  `issue_workspace()` then `checkout_issue_branch()` on its return value.
  A freshness flag/stamp must be threaded through that call site or stored
  keyed on the resolved workspace path.

### P4 — TTL on rulebook/core pulls

- Rulebook pull: `spawn.py:201` (inside `rulebook_checkout`).
- Core pull: `spawn.py:2054`, inside `ensure_rulebook`'s core-resolution
  path (`spawn.py:2042-2069`, the `_core_candidates()` loop and its
  on-the-record-owned-clone fallback). Both pulls are plain
  `git pull -q --ff-only`, `capture_output=True`, no timeout.
- No existing TTL/staleness-marker pattern found anywhere in `spawn.py` —
  this will be new machinery, not a copy of an existing convention. It
  needs to be disk-persisted (a marker file with a pull timestamp next to
  each clone, e.g. `<clone-dir>/.muster-last-pull`) since P4's freshness
  window must survive across separate orchestrator processes (successive
  spawns), unlike P2's in-process memo dict.

### P5 — timeouts + git env

- Confirmed only 3 `timeout=` in the file today:
  `spawn.py:2135` (`timeout=30`, unrelated git-diff-ish subprocess — need
  to double check identity but not in scope to change), `spawn.py:2199`
  (`timeout=180`), `spawn.py:2529` (`timeout=15`, inside
  `_resolve_gh_token`'s `gh auth token` call).
- Network subprocess calls confirmed with NO timeout today:
  - `spawn.py:201` — rulebook pull (P2/P4 territory too).
  - `spawn.py:206` — rulebook clone (inside `rulebook_checkout`, no
    `after` fetch shown yet but clearly a clone).
  - `spawn.py:2054` — core pull.
  - `spawn.py:2060-2062` — core clone.
  - `spawn.py:2572` — `_fetch_or_halt`'s `git fetch -q origin`
    (`spawn.py:2559-2577`), env via `_git_env()`.
  - `spawn.py:2628` — `issue_workspace`'s new-clone `git clone -q`.
  - `spawn.py:2710` — `ensure_pushed`'s `git push -q -u origin`
    (`spawn.py:2686-2714`), also via `_git_env()`.
- `_git_env()` — `spawn.py:2537-2556`. Currently returns
  `{**os.environ, "GH_TOKEN": token}` or `None` if no token resolved. It
  does NOT set `GIT_TERMINAL_PROMPT` or `GIT_ASKPASS` — confirmed by
  reading the full function body. The only place `GIT_TERMINAL_PROMPT=0`
  is set today is `spawn.py:2287`, inside the spawned session's own env
  construction (near `agent_token`/`CLAUDE_PLUGIN_ROOT_CORE` injection,
  `spawn.py:2280-2299`), which has nothing to do with the orchestrator's
  own git calls through `_git_env()`.

## Existing conventions to follow (from `docs/decisions/` and code)

- `docs/decisions/2026-07-29-headless-cli-measured-facts.md` and
  `docs/decisions/2026-07-29-permanently-closed-alternatives.md` — both are
  ADR-style docs with `kind: decision` front matter, citing every claim to
  `path:line`. Not directly reusable content for #285 (they're about
  headless-CLI permission semantics), but they set the house convention of
  measured-fact citation, which the survey above follows (every line number
  re-verified against HEAD, not copied from the issue body verbatim).
- `_GH_TOKEN_CACHE` (`spawn.py:2508`) is the house pattern for P2's
  per-process memoization: bare module-level global (or dict, when keyed),
  guarded by an `if cached is not None: return cached` short-circuit,
  documented with a docstring explaining which call sites would otherwise
  duplicate work.
- fail-closed style: `_fetch_or_halt` (`spawn.py:2559`) treats a fetch
  failure as `sys.exit`, not a silent continue — P5's timeouts must produce
  the same fail-closed shape (named error message, `sys.exit`, not a
  swallowed `TimeoutExpired`).
- Korean-language docstrings/comments are the house style throughout
  `spawn.py` (every function above has a Korean docstring). Phase-2 code
  changes should match this; this survey and the proposal are written in
  English per the `work-in-english` policy for repository-bound work
  docs, consistent with how `docs/issue-280/proposals/...` was written in
  English while `gates/*.py` itself may carry Korean comments.

## Test coverage found

- `test_spawn.py` (3500+ lines) already exercises `_fetch_or_halt`
  directly (`test_spawn.py:1067,1098,1298`), including a call-count-style
  test at `test_spawn.py:1343-1364`
  (`test_..._call_count`-shaped: counts lines appended to a
  `call_count_file` by a stub `gh` script to assert `_fetch_or_halt` isn't
  called more than once for a given scenario). This is the existing
  pattern phase 2's P2/P3 call-count tests should copy — a stub
  git/gh executable on `PATH` that records invocation count to a file,
  asserted via `assertEqual(len(...), N)`.
- No existing timing test (`time.monotonic()`-based assertion) found in
  `test_spawn.py` for spawn latency — phase 2's warm-spawn timing test
  (P1's <=1.5s acceptance criterion) will be new.
- No existing timeout-behavior test (asserting a `subprocess.TimeoutExpired`
  is caught and surfaced as a named error within a bound) found — also new
  for phase 2.
