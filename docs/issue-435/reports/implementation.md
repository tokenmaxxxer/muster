---
code_under_review: HEAD
loop_state: done
---

# Implementation record — issue #435

## Why

Upstream basis: #435 (this issue). #287 is the basis for the target
shape (`spawn._issue_comments` -> `(list[dict], bool)`); #398 is the
basis for why the 13 failures were invisible all day (`gates/` could not
be collected at all until #398 landed); #376 is the reason the
investigation checked `shape_contracts.py` before adding a new mechanism.
`gates/`'s 13 failures had been broken since #287 merged and stayed
invisible until #398 made `gates/` collectible again.

## What was done

1. `gates/test_closes_gate_ci.py`: all 13 `spawn._issue_comments` stubs
   changed from `lambda repo, n: [...]` to `lambda repo, n: ([...], True)`
   (or the `([], True)` / ternary equivalents), matching #287's
   `(list[dict], bool)` return shape. One of the 13
   (`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`)
   had a second, independent staleness that the unpack crash had been
   masking: its `pr_reference._issue_view_body` stub predated the
   acceptance_gate check (#310) and had no `## Acceptance` section — fixed
   by giving it one (`check: \`gates/test_closes_gate_ci.py\``).
2. `shape_contracts.py`: added `assert_stub_return_shape(stub, real,
   *args, **kwargs)` — calls the stub and checks the result against
   `real`'s return annotation via `inspect.signature(eval_str=True)` +
   `typing.get_origin`. Documented in the module docstring as a third,
   narrower kind of drift (internal-function stub vs. the existing two
   external-interface legs) — `shape_contracts.py` did not cover this
   before because its scope (per its own docstring and the issue-335
   proposal) was external payload shapes only, not stubs standing in for
   the repo's own functions. Added
   `t_issue_comments_stub_shape_contract_catches_old_pre_287_shape` in
   `gates/test_closes_gate_ci.py`, which builds a deliberately old-shape
   stub and asserts the check raises, then builds a correct-shape stub
   and asserts it passes.
3. `docs/handbooks/operations.md`: both self-check sections (한국어/
   English) now instruct `python3 -m pytest -q` with no `--ignore=gates`,
   with the reason (#398 fixed; the flag now only re-hides `gates/` if it
   breaks again). No CI job or config file set `--ignore=gates` anywhere
   in the repo (checked `.github/workflows/`, `pytest.ini`,
   `pyproject.toml`) — it was a pure CLI habit with no mechanical switch
   to flip, so the doc line is the whole fix.
4. New category for #419's list (recorded here since #419 itself is out
   of this issue's write scope): **a test stub is a stand-in, not a call
   site** — signature-change audits that grep for call sites of a changed
   function will not find a `lambda` built to impersonate it during a
   test. #435's 13 failures are the first instance of this category.

## Doc-placement ladder

- Investigation result (scope item 2, "does shape_contracts.py cover
  this, and if not why not") — this record, `## What was done` item 2.
- New generic assertion function (`assert_stub_return_shape`) — landed in
  `shape_contracts.py` itself alongside the two existing legs, not a new
  module (#376: don't rebuild what exists).
- Handbook update (self-check command default) —
  `docs/handbooks/operations.md`, both language sections.

## Acceptance

```
$ python3 -m pytest -q
495 passed in 26.11s
```
Run directly, not predicted (#416). No `--ignore` flag used.

`t_issue_comments_stub_shape_contract_catches_old_pre_287_shape` is the
signature-drift check demonstration: it constructs an old-shape
(pre-#287) stub, asserts `shape_contracts.assert_stub_return_shape`
raises `AssertionError` naming the `list`/`tuple` mismatch, then
constructs a correct-shape stub and asserts the same call passes.

## What did not work

- First attempt at fixing the 13 stubs only touched the `_issue_comments`
  shape; re-running the file after that still showed one failure
  (`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`)
  because a second, unrelated stub gap (missing `## Acceptance` section)
  had been masked by the same unpack crash. Fixed by adding a valid
  Acceptance section to that test's `pr_reference._issue_view_body`
  stub.
- First version of `assert_stub_return_shape` called
  `inspect.signature(real)` without `eval_str=True`; `spawn.py` uses
  `from __future__ import annotations`, so the return annotation came
  back as the string `"tuple[list[dict], bool]"` and
  `typing.get_origin(...)` returned `None`, then `isinstance(result,
  origin)` raised `TypeError: isinstance() arg 2 must be a type...`
  instead of the intended `AssertionError`. Fixed by passing
  `eval_str=True` to resolve the annotation to a real `tuple` object.

## Open findings

resolved_findings:
- warrant-hunter, before-landing, stance 2 (assume this guard goes
  silent when its own input is malformed):
  `docs/reports/2026-08-07-hunt-fix-gates-stubs-and-default-full-suite.md`
  — `assert_stub_return_shape` discarded a parameterized annotation's
  type arguments (`typing.get_origin(tuple[list[dict], bool])` returns
  bare `tuple`), so a stub returning e.g. `(5, "not-a-bool")` against
  `-> tuple[list[dict], bool]` passed silently. Fixed by recursing one
  level into `tuple`/`list`/`set` element types
  (`shape_contracts._check_shape`); repro from the finding now raises
  `AssertionError`. No further open findings.

