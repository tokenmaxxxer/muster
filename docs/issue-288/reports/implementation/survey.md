Subject: issue-288

# Current-state survey — spawn.py CLI truth/action gaps

Scope: the write surface is a single file, `spawn.py` (3382 lines), plus its
existing test file `test_spawn.py` at repo root (established convention —
this repo does not use `test/` for spawn.py's own tests; `test_spawn.py`,
`test_gates.py`, `test_flows.py` etc. all sit at root).

## Scout skip record

Skip condition: **spec leaves no design decision open**. Issue #288 names,
per finding, both the observed bug and a concrete `Fix:` line, and the
Acceptance section pins the externally-observable behavior for each. This is
a bugfix set against an existing CLI's stated intent (fail loudly, do only
what was scoped) — there is no product-shaped surface, no external
comparable to scout, and no open framing question. Scouting is skipped;
proceeding straight to survey-derived proposal.

## Findings, by code site

### N1 — `clean --issue N` ignores `--issue` (spawn.py:2467-2535)
The `clean` branch never reads `a.issue` at all. It globs every dir under
the work base (`wb.glob("*")`) and applies the same commit/push safety
check to each, regardless of what `--issue` was passed. `--issue 424242`
"succeeds" with 0/0 because the loop never filtered by issue in the first
place — there's nothing to not-find.

### N2 — `--dry-run` never validates `-C` (spawn.py:2568-2592)
`--dry-run` returns at line 2586-2592, before `require_doctor()` (2593) and
before `workspace()`/`checkout_issue_branch()` (which live inside
`_spawn_one`, only reached on the non-dry-run path at 2594). `require_board`
(2570) and `require_no_repo_config` (2573) *do* run under dry-run already,
but neither one stats `a.cwd` for plain existence/dir-ness before reading
files under it — `role_settings(a.role)` doesn't touch `a.cwd` either. A
`-C` that doesn't exist or isn't a directory currently produces no error
before `role_settings()` prints its JSON and returns 0.

### N3 — `--issue` is unvalidated (spawn.py:2409-2410)
`ap.add_argument("--issue", type=int, ...)` — plain `int`, so 0, negative,
and huge values all parse. Consumers (`_spawn_one`, `checkout_issue_branch`
at 2773: `br = f"issue-{issue}/{role}"`, `_watch`) do no range check of
their own.

### N4 — non-numeric `issue-*` dirs vanish from the board (spawn.py:1084-1099)
`board()` iterates `docs.iterdir()` filtered by
`re.match(r"^issue-[0-9]+$", p.name)` — anything that starts with `issue-`
but fails the numeric suffix (e.g. `issue-NaN`) is silently excluded from
the returned dict, with no diagnostic anywhere in the call chain
(`status()` at 1102 just prints what `board()` returned).

### N5 — foreign repo at the expected work path enters "reuse" unchecked (spawn.py:2699-2735)
`workspace()` computes the expected `origin` from `cwd`'s own remote
(2700-2716), then computes `work` from the repo name (2727-2728). If
`(work / ".git").exists()` (2733), it goes straight to
`_fetch_or_halt(str(work), ...)` (2734) with **no check that `work`'s own
origin matches the `origin` computed above**. A foreign repo with a working
origin is silently fetched and returned as the workspace; one with a broken
or unrelated origin fails inside `_fetch_or_halt` (2656-2685) with a generic
"fetch 실패" message that reads as a network problem, not an identity
mismatch. The `src == work.resolve()` reuse path (2730-2732) is a different,
legitimate case (cwd already IS the workspace) and is out of scope for this
check.

### N6 — orphaned clone on `_fetch_or_halt` failure in the new-clone branch (spawn.py:2737-2763)
Named in the issue but **not in the Acceptance list** — out of scope for
this proposal (see Out of scope in the proposal doc).

### N7 — `MUSTER_ROLE_MODEL` unvalidated — not in Acceptance list, out of scope.

### N8 — `--stall-timeout 0`/negative accepted (spawn.py:2416-2417)
`type=float, default=5.0`, no range check. Not in the Acceptance list as a
standalone item, but related to the corroboration below — see there.

## Live corroboration to check against the issue

Today's `spawn.py watch` runs against issues 301, 141, 304 each printed
`stall: N초째 무변화` while the ledger and open PRs showed real progress.
Root cause, read at `_await_bounded` (spawn.py:1946-1991): the stall clock
is driven by `log_path.stat().st_size` (line 1979). When `log_path` does not
exist — e.g. because `clean`'s global sweep (N1) deleted the session's log
sibling files (spawn.py:2518-2524, the `w.parent.glob(w.name + ".*")` loop)
— `log_path.stat()` raises `OSError`, which is caught and silently
substitutes `size = last_size` (1980-1981). Size therefore never changes,
`last_change` never advances, and after `stall_timeout_min` the function
reports `stall: 세션 로그 N초째 무변화` (1987) — a confident, specific claim
("N seconds of no change") about a file it never actually observed changing
because the file is gone. This is the same failure family as the issue's
framing ("a CLI that reports a confident state it did not actually
observe"): a missing log is being reported as a normal stall, not as an
inability to observe. `clean` deleting a running session's logs while
another process (`watch`) still expects them is the concrete trigger
matching N1's blast radius. Fixing N1 (scoping `clean --issue`) narrows
*when* this happens but does not fix the false report itself — `_await_bounded`
still can't tell "the log file was there and stopped growing" from "the log
file was never there / got removed out from under us." This is added to
the write set as a `_await_bounded` fix, distinct from but adjacent to N1.

## Write set implied

- `spawn.py`:
  - `clean` branch (~2467-2535): scope sweep candidates to `--issue` when given.
  - dry-run branch (~2574-2592): stat/validate `a.cwd` before printing settings.
  - `--issue` argparse (~2409): swap `type=int` for a `positive_int` validator.
  - `board()` (~1084-1099): warn to stderr for `issue-*` dirs that fail the numeric pattern, still excluding them from the returned dict.
  - `workspace()` reuse branch (~2733-2735): verify `work`'s origin against the expected origin before `_fetch_or_halt`; refuse by name on mismatch.
  - `_await_bounded()` (~1946-1991): distinguish "log path missing/vanished" from "log path present but unchanged" and report the former as non-observation, not stall.
- `test_spawn.py`: one pinning test per behavior above (existing file, existing pytest conventions in this repo).

No new dependency, no new env var, no schema/migration.
