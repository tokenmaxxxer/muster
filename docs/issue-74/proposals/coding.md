---
subject: issue-74
role: coding
kind: proposal
loop_state: proposal-submitted
code_under_review: 1fb59e5d9322162b5f5cf09872a3c69eebaa8be6
files:
  - test_gates.py
  - tests/run-orchestrate-tests.sh
  - docs/issue-74/reports/coding.md
  - spawn.py  # CONDITIONAL — only if the test_spawn.py failure is confirmed to be the git-template rulebook-clone copy
---

# issue-74 — proposal: revive the self-check suite

## Request

Issue #74 says the self-check suite is dead: `python3 test_gates.py` crashes on its first test,
before it can tell anyone anything about the other 32. Its "Done when" is all three commands —
`python3 test_gates.py`, `python3 test_spawn.py`, `bash tests/run-orchestrate-tests.sh` — passing,
and it mandates TDD discipline: each fix is watched failing first, then made to pass. This proposal
covers the four conceptual root causes issue #74 names (its 5 bullets collapse to 4 — bullets 3 and
4 are two instances of one cause, v3's abolition of the per-repo contract copy) plus a fifth defect
found during the survey that the suite cannot be observed passing without fixing.

## Constraints

- **TDD, and how red is observed given the runner aborts on first failure.** `test_gates.py`'s
  runner (`test_gates.py:616-621`) is a bare loop with no per-test try/except — one uncaught
  exception stops the whole file, hiding every test after it. So "watch it fail first" cannot mean
  "run `python3 test_gates.py` and read the traceback" past the first broken test. Each fix in this
  proposal is watched red by isolating the one test under repair — e.g.
  `python3 -c "import test_gates; test_gates.t_board_tolerates_trailing_comment()"` — or by
  temporarily narrowing the `tests = [...]` list at `test_gates.py:617` to just that test, run,
  fail, edit, rerun, pass. Only after every test is individually green does the full-file run at
  `test_gates.py:616-621` get used as the final confirmation.
- **No source file outside the frozen write set.** Edits land only in `test_gates.py`,
  `tests/run-orchestrate-tests.sh`, `docs/issue-74/reports/coding.md`, and `spawn.py` — and the
  `spawn.py` edit is conditional (see Out of scope).
- **`tests/run-orchestrate-tests.sh` cannot be run as-is in this sandbox** until its `guard()`
  helper is fixed: `mktemp -d` fails in this sandbox, so `guard()`'s unchecked
  `td="$(cd "$(mktemp -d)" && pwd -P)"` at line 24 resolves `td` to the current working directory,
  and the following `git init -q "$td"` / `rm -rf "$td"` then operate on the repo root — this has
  already destroyed this checkout twice. Its `wc -l` fix (line 21) and its `mktemp` fix (line 24)
  must land together in one edit before the script is executed even once here; a half-fixed script
  is still unsafe to run.
- **Human approval gates phase 2.** Approval recorded in `docs/specs/approvers.md` is required
  before the edits described below (and the `docs/issue-74/reports/coding.md` write) land.

## What will be done

1. **`_board()` and `_wake_repo()` rebuilt to the v3 shape, plus 5 direct record-path sites.**
   `_board()` (`test_gates.py:20-27`) currently builds `docs/<subject>/<role>.md` (v2); the reader,
   `spawn.board()` (`spawn.py:773-789`), requires `docs/issue-<n>/reports/<role>.md` — a directory
   matching `^issue-[0-9]+$` (`BOARD = "docs"` at `spawn.py:618`) with records inside its
   `reports/`. Edit: change `_board()`'s path construction at `test_gates.py:23` to
   `docs/issue-<n>/reports/<role>.md`, and update its two callers,
   `t_board_reads_loop_state` (`test_gates.py:38-52`, call at `:40`) and
   `t_board_tolerates_trailing_comment` (`test_gates.py:54-61`, call at `:57`), to pass an
   `issue-<n>`-shaped subject. Same shape for `_wake_repo()` (`test_gates.py:64-75`, board-dir
   construction at `:68`) and its 9 callers (`:90, 97, 114, 131, 142, 167, 192, 215, 247`), plus the
   5 direct record-path sites that build paths under the old shape (`:101, 115, 132, 134, 143`).
   *Red*: isolate `t_board_reads_loop_state` — reproduces the captured `AssertionError: {}` at
   `test_gates.py:44`. *Green*: rerun `t_board_reads_loop_state` and
   `t_board_tolerates_trailing_comment` in isolation, no traceback; then every `t_wake_*` test
   individually, since `wakes._rows()` (`wakes.py:235`) calls `spawn.board()` and was failing
   transitively through the same fixture.

2. **Hypothesis fixture moved under `docs/issue-<n>/proposals/`.** `wakes._hypotheses()`
   (`wakes.py:175-184`) globs only `docs/issue-*/proposals/*.md` filtered by frontmatter
   `kind == "hypothesis"`; `_wake_repo()` (`test_gates.py:64-75`) writes `docs/proposals/h.md`.
   Edit: change the path at `test_gates.py:66-69` to `docs/issue-<n>/proposals/h.md` (and its
   two references inside `t_wake_acknowledged_hypothesis_goes_quiet`, `test_gates.py:99, 103`).
   *Red*: isolate `t_wake_hypothesis_wakes_feasibility` (`test_gates.py:88-91`) — currently fails
   (transitively, via cause 1's board-shape mismatch, and independently once cause 1 is fixed,
   via the hypothesis-path mismatch). *Special care*: `t_wake_acknowledged_hypothesis_goes_quiet`
   (`test_gates.py:94-105`) asserts a **negative** — `"feasibility" not in _woken(root)` — so it
   passes today for the wrong reason: with the board unreadable (cause 1), no role is ever woken
   regardless of hypothesis content, so the assertion holds vacuously. Before trusting this test as
   green post-fix, it must first be made to fail for the right reason: after landing the path fix,
   temporarily invalidate the acknowledgement it depends on (e.g. corrupt the recorded `sha` in the
   `upstream:` block it writes at `test_gates.py:101-103`) and confirm `"feasibility"` *does* appear
   in `_woken(root)` — proving the test is exercising the suppress-on-matching-evidence path and not
   passing by default — then revert the corruption and confirm the test returns to green. *Green*:
   `t_wake_hypothesis_wakes_feasibility` passes in isolation, and
   `t_wake_acknowledged_hypothesis_goes_quiet` passes only after the above red/green round-trip
   confirms it fails for the right reason when broken.

3. **`t_contract_drift_is_detected_by_content` deleted.** This test (`test_gates.py:383-401`)
   calls `spawn.contract_drift` and `spawn.init_contract`, both removed by commit
   `613a5fbced1b08b48c4c8215a241d0b8a823dbcc` ("init writes approvers.md, not a contract copy;
   require_board replaces require_contract"). `grep -rn "contract_drift\|init_contract\|
   require_contract\|CONTRACT" --include="*.py" .` hits only this file, confirming nothing else
   depends on these names. Edit: delete `test_gates.py:383-401` and its `def` line, replacing it
   with an in-file comment recording that v3 abolished the per-repo contract copy (commit
   `613a5fb`) so the test is not reintroduced by a future contributor who sees a gap and tries to
   "restore" it. *Red*: already captured — calling `spawn.contract_drift` raises `AttributeError`
   (the symbol does not exist in `spawn.py`); no further reproduction needed before deleting.
   *Green*: `grep -n "contract_drift\|init_contract" test_gates.py` returns nothing, and the full
   isolated-then-combined test run has one fewer test with no error at that name.

4. **`t_missing_contract_stops_the_spawn` replaced by a `require_board()` test with the same
   intent.** The old test (`test_gates.py:254-272`) calls the same deleted symbols
   (`spawn.require_contract`, `spawn.CONTRACT`). Its v3 equivalent is `require_board(cwd: str,
   override: bool) -> None` (`spawn.py:661-676`): returns early if `(root / MARKER).is_file()`
   or if `override` is true, else `sys.exit(...)` naming `MARKER` (`"docs/specs/approvers.md"`,
   `spawn.py:619`). It is called before every session spawn — `spawn.py:1393`
   (`require_board(a.cwd, a.no_contract)`, the `drive` role) and `spawn.py:1413`
   (`require_board(a.cwd, a.no_contract or a.dry_run)`, direct role spawn) — and
   `grep -n "require_board" test_gates.py test_spawn.py` currently returns nothing: zero test
   coverage, exactly as the issue claims. Edit: replace `test_gates.py:254-272` with a new test
   covering all three branches of `spawn.py:661-676`: (a) marker present → `require_board` returns
   without raising; (b) marker absent, `override=True` → returns without raising; (c) marker
   absent, `override=False` → raises `SystemExit` whose message contains `spawn.MARKER`. This keeps
   the old test's intent — an unmet precondition stops the spawn before a session is burned — on
   the current mechanism. *Red*: isolate the new test against the current (pre-edit) file — it
   fails with `AttributeError: module 'spawn' has no attribute 'require_contract'`, confirming the
   gap the issue names. *Green*: after rewriting to call `require_board`, each of the three
   branches passes in isolation, and `grep -n "require_board" test_gates.py` now returns the three
   call sites.

5. **`wc -l` comparison at `tests/run-orchestrate-tests.sh:21` made padding-proof.** BSD `wc -l`
   left-pads its count (observed: `FAIL directive-silent-for-roles want=0 got=       0` — `$lines`
   is literally `"       0"` on macOS), and `[ "$lines" = 0 ]` is a string comparison that a padded
   value never satisfies. Edit: change the comparison operator at line 21 from `[ "$lines" = 0 ]`
   (string equality) to `[ "$lines" -eq 0 ]` (numeric equality, which tolerates the leading
   whitespace `wc -l`'s output carries on this platform). *Red*: reproduce the padding in isolation,
   without invoking `tests/run-orchestrate-tests.sh` or any part of it (per the hard safety rule
   below) — confirm on this platform that `wc -l`'s single-line output is left-padded (e.g. its
   length exceeds the digit count) and that a bare string-equality check against `0` fails on that
   padded value, matching the captured `want=0 got=       0`. *Green*: the same isolated
   reproduction, now compared with `-eq` instead of `=`, succeeds; the change is confirmed against
   the real hook output only as part of item 6's first full run, once `guard()` is safe to execute.

6. **`guard()`'s `mktemp` footgun at `tests/run-orchestrate-tests.sh:24` fixed.** Today,
   `td="$(cd "$(mktemp -d)" && pwd -P)"` does not check whether `mktemp -d` succeeded; when it
   fails (as it does in this sandbox), `cd ""` combined with `pwd -P` resolves `td` to the current
   working directory, and the following `git init -q "$td"` / `rm -rf "$td"` (line 29) then act on
   the repo root — this is the mechanism that destroyed this checkout twice. Edit: check `mktemp
   -d`'s exit status and abort the script immediately if it fails, before `td` is ever used, e.g.
   `td="$(mktemp -d)" || exit 1` followed by a non-empty guard on `$td` before any `git init` or
   `rm -rf` touches it. *Why this is in scope even though issue #74 does not name it*: the issue's
   "Done when" requires `bash tests/run-orchestrate-tests.sh` to be observed passing; in this
   sandbox (and any environment where `mktemp -d` is unavailable or restricted) the script cannot
   be run at all — let alone observed passing — while this defect stands, because running it
   destroys the checkout being tested. A "Done when" clause that names a command is not satisfied
   by a command that cannot safely execute. *Red*: this cannot be reproduced by invoking the script
   (that is the hazard itself) — the red state is the historical fact already on record: two prior
   destructions of this checkout, both traced to this line. *Green*: with the check added, a
   simulated `mktemp -d` failure (stubbed, not the real script, e.g. a throwaway shell function
   that shadows `mktemp` to fail) causes an immediate non-zero exit with no `git init` / `rm -rf`
   executed; only then is the real, unmodified script run once, end to end, for the first time.

## Decisions

- **(a) Fix the fixtures to emit v3 shape, rather than loosening `spawn.board()` to accept both
  shapes.** Alternative considered: widen `spawn.board()`'s regex/path logic to also read the v2
  layout `_board()` currently produces. Rejected — the fixture is the thing that drifted from the
  contract (v3 deleted the v2 shape deliberately); widening the reader to tolerate a shape v3
  abolished would re-legitimise exactly what the migration removed, and would leave a dead code
  path in production (`spawn.py`) whose only caller is a test fixture that should never have drifted
  in the first place.
- **(b) Fix `guard()` in place, rather than declaring it environment-specific and skipping it.**
  Alternative considered: treat the `mktemp -d` failure as a known sandbox limitation, document it,
  and skip the `guard`-backed tests (`guard-docs-in-board`, `guard-src-in-board`,
  `guard-approvers-ok`, `guard-nonboard-repo`, `guard-outside-trees`) when the environment can't
  support them. Rejected — this is not merely an environment quirk to work around, it is an
  unchecked-command-substitution bug that would resolve to the cwd and run `git init` / `rm -rf` on
  it in *any* environment where `mktemp -d` fails for *any* reason (quota, sandboxing, missing
  binary), not just this one; skipping it would leave the same destructive footgun live for the
  next person or CI environment that hits it, and would leave the issue's own "Done when" for this
  command permanently unobservable here.

## Out of scope

- **The `test_spawn.py` rulebook-clone failure is not one of issue #74's causes.** The captured
  error is `test_spawn.py:674` (inside `test_preparation_and_preamble_happen_once`, defined at
  `test_spawn.py:633`) → `spawn.py:1605` (inside `_spawn_one`, defined at `spawn.py:1584`) →
  `spawn.py:216` (inside `plugin_dirs`, defined at `spawn.py:209`) →
  `spawn.py:189` (`rulebook_checkout`, defined at `spawn.py:157`) raising `SystemExit: [qa] 룰북을
  받지 못했다: tokenmaxxxer/qa-agent-rulebook / fatal: cannot copy
  '/Applications/Xcode.app/.../hooks/commit-msg.sample' to '.../runs/rulebooks/tokenmaxxxer...'` —
  a `git clone` failure copying the *system* git template hooks, not a defect in the code under
  test. Item 4 of the frozen write set (`spawn.py`) is **conditional**: it only activates if a
  re-run in a clean environment confirms this is reproducibly the git-template copy, in which case
  the narrow fix is to stop the rulebook clone from copying the system template hooks at all (e.g.
  cloning with an empty template directory). If instead the failure turns out to be
  network/credential-related (this environment could not reach `github.com` for this clone) rather
  than the template-copy mechanism, that is an environment blocker to report, not a code change —
  `spawn.py` stays untouched and this proposal's write set drops to the first three files.
- **The bare test runner at `test_gates.py:616-621`** aborts on the first uncaught exception, which
  is the reason one broken test hid every other result. Worth noting as the shape of the problem,
  but issue #74 does not ask for a resilient runner (e.g. per-test try/except with a summary), so
  none is added here.
- **`wakes.py`, `gates/`, `orchestrate/`, `README.md`, `protocol.md`** are not touched. The fixes
  above are entirely test-fixture and test-runner-script corrections; no production behavior in
  `wakes.py` or `spawn.py`'s board/wake logic is believed to be wrong (the fixtures drifted, not the
  readers — see Decision (a)), and none of the causes touches `gates/`, `orchestrate/`,
  `README.md`, or `protocol.md`.

## How I will know it worked

1. `python3 test_gates.py` — expected shape: one `  ok  <test_name>` line per test, in the order
   `sorted(globals().items())` yields them (`test_gates.py:617`), zero exceptions, ending in
   `<N> passed` with a clean process exit. The current file has 33 `t_`-prefixed tests; after
   deleting one (item 3) and replacing one 1-for-1 (item 4), the expected final line is
   `32 passed`.
2. `python3 test_spawn.py` — expected shape: unittest's summary line, `Ran 54 tests in <time>s`
   followed by `OK` (not `FAILED (errors=1)`) — conditional on item 4 of the write set landing and
   the rulebook-clone failure being confirmed and fixed per the Out of scope conditional; if that
   failure is instead an environment blocker, this command's expected outcome is reported as
   blocked, not silently declared passing.
3. `bash tests/run-orchestrate-tests.sh` — expected shape: one `ok     <name> <value>` or
   `FAIL   <name> want=<x> got=<y>` line per check, ending in a `<pass> passed, <fail> failed`
   summary with `<fail> = 0`. **This command will only be run after the `guard()` fix (item 6)
   lands together with the `wc -l` fix (item 5).** Until both land, `bash
   tests/run-orchestrate-tests.sh` — or any extracted part of it — must not be executed in this
   checkout: with `guard()` unfixed, `mktemp -d`'s failure in this sandbox causes `git init -q ""` /
   `rm -rf ""` to resolve to the repo root, which has already destroyed this checkout twice.

## Scope decision requested: wakes.py:335

The phase-1 hunt (end-of-phase-1 warrant probe) found a defect that is real, is not one of
issue #74's five bullets, and is not in this proposal's frozen write set — `wakes.py` is explicitly
excluded above (see Out of scope).

The defect: `wakes.py:335` recovers `subject = Path(f).parent.name`, which resolves to the literal
string `"reports"` instead of the issue directory name one level further up. As a consequence, the
section-19 first-build approval gate is silently bypassed for every finding addressed to `coding` —
such a finding wakes `coding` unconditionally instead of being held in `blocked` until the subject's
front record is scope-approved. See `docs/issue-74/reports/coding/hunt-phase1.md` for the full
reproduction.

Two options, and the approver should pick one:

- **(a)** Extend this issue's write set to include the one-line fix at `wakes.py:335` plus a
  regression test in `test_gates.py` that targets `coding` with `addressed_to:` — cheap, and the
  suite is already being opened up in this very change.
- **(b)** Leave `wakes.py` untouched here and let the human file it as its own issue, keeping this
  PR strictly to #74's stated causes.

Default if the approver says nothing: **(b)** — no unilateral widening. `wakes.py` is not added to
this proposal's `files:` frontmatter list; the write set stays frozen until a human changes it.
