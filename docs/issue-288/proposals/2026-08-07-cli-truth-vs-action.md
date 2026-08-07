---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

Subject: issue-288

## Request

`spawn.py`'s CLI reports success/no-op confidently in five places where it
either did not do what a flag asked, or did not check what it claims to
have checked: `clean --issue N` sweeps every workspace regardless of N;
`--dry-run` never validates `-C`; `--issue` accepts non-positive values;
a non-numeric `issue-*` docs dir silently drops off the board; and a
foreign repo pre-placed at the expected work path is treated as a reusable
workspace without an identity check. Live corroboration gathered the same
day (spawn.py watch against issues 301/141/304) surfaced a sixth, adjacent
case: `_await_bounded`'s stall clock reports "N seconds unchanged" even
when the log file it's supposedly watching doesn't exist — because it was
deleted by `clean`'s global sweep (the N1 bug). That is the same
truth-vs-action failure class the issue names, so it is folded into this
proposal per explicit instruction to check today's corroboration against
the issue.

## Constraints

- Acceptance criteria in #288 are executable checks (per #310): each fix
  needs a pinning test in `test_spawn.py`, not a prose claim.
- N6 (orphaned clone on failure), N7 (unvalidated `MUSTER_ROLE_MODEL`), and
  the "verified correct" `MUSTER_MCP_ALLOW` notice are named in the issue
  body but excluded from its own Acceptance list — out of scope here (see
  below).
- No new dependency, no new env var, no schema change — this is entirely
  input-validation and reporting-honesty inside `spawn.py`.
- A missing/deleted log must be reported as "cannot observe," never folded
  into the existing "stalled" message — silent stalls are this system's
  highest-severity failure class; a false stall on top of a real one trains
  the operator to disbelieve genuine stalls.

## Rationale

**`clean --issue N`: scope the sweep vs. reject the flag outright.**
Considered rejecting `--issue` on `clean` entirely (simplest: the flag
never worked, so make that explicit and force operators to use the
existing unscoped sweep). Rejected because `clean --issue N` is the
natural, already-guessable command an operator reaches for after finishing
one issue, and the issue's own Fix line offers scoping as the preferred
option ("scope the sweep, or reject the flag") — scoping preserves a useful
capability instead of just deleting a broken one. Scoping needs the same
`repo_name` derivation `workspace()` uses (origin → repo name) to match a
work dir's name against `-issue-{N}-`; that derivation already exists and
is reused, not reinvented.

**`--issue`: a `positive_int` argparse type vs. post-hoc validation in each caller.**
Considered validating `a.issue` inline at each of the three use sites
(`_spawn_one`, `checkout_issue_branch`, `_watch`, `clean`). Rejected:
argparse's `type=` hook rejects at parse time with a standard argparse
usage error, which is both less code (one function, one argument
declaration) and fails faster/more uniformly than three scattered checks
that could drift out of sync.

**`board()`: warn to stderr and still exclude, vs. include mis-named dirs on the board.**
Considered admitting `issue-NaN`-style dirs to the board under a
synthesized key so orchestrator routing could still see them. Rejected:
the board key is threaded through as an actual issue number all over this
file (`checkout_issue_branch`, GitHub API calls) — admitting a non-numeric
subject would just move the crash downstream to whichever caller tries to
use it as `int`. A stderr warning naming the dropped dir keeps `board()`'s
contract (numeric subjects only) intact while making the drop observable
instead of silent, which is exactly what N4's Fix line asks for.

**`_await_bounded`: distinguish missing-log from unchanged-log, vs. leaving it as "same bucket, different wording."**
Considered just rewording the existing stall message to soften the claim
("no change observed" instead of "N seconds unchanged") in all cases.
Rejected: that would still misreport a missing log as a *stall* (a health
signal about a running session), when it's actually a *loss of the
observation channel itself* — a distinct condition an operator should react
to differently (check `clean` history / re-run the role) rather than
assume the session hung.

## What will be done

- `spawn.py` `clean` branch: when `a.issue is not None`, only consider work
  dirs whose name matches `-issue-{a.issue}-` (mirroring how `workspace()`
  names dirs: `f"{repo_name}-issue-{issue}-{role}"`); dirs not matching are
  left untouched and not counted in the removed/kept/failed tally at all
  (they're outside the requested scope, not "kept" within it).
- `spawn.py` `--issue` argparse: replace `type=int` with a small
  `positive_int(s)` validator function (`int(s)`, then reject `< 1`,
  raising `argparse.ArgumentTypeError` on failure) used for the `--issue`
  argument.
- `spawn.py` dry-run branch: before printing settings, resolve `a.cwd` and
  verify it exists and is a directory; on failure, exit non-zero with a
  message naming the bad path — mirroring the existing halt style used
  elsewhere in this file (`sys.exit(f"...: {detail}")`).
- `spawn.py` `board()`: for each `issue-*`-prefixed dir under `docs/` that
  fails the numeric-suffix regex, print one stderr line naming the dir and
  that it's excluded from the board; the numeric-only filtering and return
  value are otherwise unchanged.
- `spawn.py` `workspace()` reuse branch (`(work / ".git").exists()` case):
  before calling `_fetch_or_halt`, read `work`'s own `origin` remote and
  compare it (post https-normalization, same rule already applied to the
  source repo's origin above it) against the expected `origin`; on
  mismatch, `sys.exit` with a message naming the path and that it's a
  foreign repo, not a network problem — never call `_fetch_or_halt` on a
  mismatched dir.
- `spawn.py` `_await_bounded`: track whether `log_path` exists at all
  (`log_path.exists()`) separately from its size; if it doesn't exist,
  report `[watch] cannot observe: 세션 로그 파일이 없다 — <path>` (or
  equivalent explicit "cannot observe" wording) instead of the stall
  message, and keep the same non-zero-eventual-return behavior (still
  returns after `limit_s` so the caller doesn't block forever) but never
  phrases it as a stall.
- `test_spawn.py`: one test per fix above pinning the corrected
  observable behavior (exit code / stdout / stderr content), following the
  file's existing test conventions.

## Out of scope

- N6 (orphaned clone left on disk when `_fetch_or_halt` fails in the
  new-clone branch) and N7 (`MUSTER_ROLE_MODEL` validated at dry-run) —
  named in the issue but not in its Acceptance list.
- The `MUSTER_MCP_ALLOW` stderr notice mentioned under "Verified correct" —
  explicitly not a requested change in the issue.
- `--stall-timeout 0`/negative (N8) as a standalone reject-at-parse fix —
  not in the Acceptance list on its own; the related missing-log
  misreport in `_await_bounded` (the corroboration item) is in scope, but
  adding a `positive_float` validator for `--stall-timeout` itself is not.
- Any change to `_watch`'s overall control flow beyond the log-existence
  check inside `_await_bounded`.

## How you'll know it worked

Each is a pinned, executable `test_spawn.py` test:
- `clean --issue N` against a work base containing workspaces for issues
  N, M (M != N): only N's eligible workspace is removed; M's is untouched
  and not reported.
- `--dry-run -C <nonexistent path>` exits non-zero and prints no settings
  JSON.
- `--issue 0` and `--issue -5` are rejected by argparse (non-zero exit,
  usage error) before any spawn/board logic runs.
- `board()` against a `docs/` tree containing `issue-NaN/` alongside a
  valid `issue-12/`: returns only `issue-12` in the dict, and a warning
  naming `issue-NaN` is emitted (captured via capsys/stderr in the test).
- `workspace()` reuse path against a `work` dir that is a git repo with an
  origin different from the expected one: exits non-zero with a message
  identifying it as a foreign/mismatched repo, and `_fetch_or_halt` is
  never invoked on it (assert via mock/monkeypatch or absence of its
  side effects).
- `_await_bounded` against an `events_path`/`log_path` where `log_path`
  does not exist: after the stall window elapses, output contains
  "cannot observe" (or the chosen equivalent) and does NOT contain the
  existing stall wording ("stall:" / "무변화" describing elapsed time on a
  file that was never there).
