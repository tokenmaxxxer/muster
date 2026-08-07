files:
  - gates/test_closes_gate_ci.py
  - shape_contracts.py
  - docs/handbooks/operations.md
  - docs/issue-435/reports/implementation.md

## Request

Fix the 13 `gates/test_closes_gate_ci.py` failures caused by test stubs
that still fake `spawn._issue_comments`'s pre-#287 return shape
(`list[dict]`) against production code that now expects
`(list[dict], bool)`. Determine whether `shape_contracts.py` already
covers this drift class and, if not, why not, before adding anything new.
Make running the full suite without `--ignore=gates` the default.

Scout-directive skip condition: pure bugfix, no design decision open —
see `docs/issue-435/reports/implementation/survey.md`.

## Constraints

- 13 failing tests must pass; no other test's behavior may change.
- `shape_contracts.py`'s existing two interfaces (gh API envelope, Claude
  stream-json events) must not be altered.
- `python3 -m pytest -q` with no `--ignore` must be the acceptance check,
  run and reported, not predicted (#416).

## Rationale

Considered fixing only the 13 stubs and leaving scope items 2-3 for a
follow-up issue. Rejected: the issue's own acceptance criteria require
both the signature-drift check and the no-ignore default in the same
pass, and both are small (a handful of lines) — splitting them into a
second issue would just re-open the exact same file twice for no
isolation benefit, and scope item 3's grep already showed there is no
config to touch, so it costs one doc edit rather than a separate unit of
work.

Considered building a new stub-linting mechanism (e.g., a pytest plugin
that inspects every `monkeypatch`/reassignment automatically). Rejected:
`shape_contracts.py` already exists for exactly this family of problem
(#376: don't rebuild what exists) and one generic function
(`assert_stub_return_shape`, called explicitly where a stub replaces an
internal function) fits its existing style — an automatic, all-stubs
scanner would be new infrastructure for a drift class that, per the
issue, has exactly one known instance.

## What will be done

1. Rewrite all 13 `spawn._issue_comments` stubs in
   `gates/test_closes_gate_ci.py` to return `(comments, True)` instead of
   a bare list; fix the one stub whose Acceptance-section gap the unpack
   crash had been masking.
2. Add `shape_contracts.assert_stub_return_shape(stub, real, *args)` —
   checks a stub's return value against `real`'s `-> ...` annotation —
   plus one demonstration test that red-lines on an old-shape stub and
   passes on the new-shape one.
3. Update both self-check sections of `docs/handbooks/operations.md` to
   run `python3 -m pytest -q` with no `--ignore=gates`, with the reason.
4. Write the phase-2 record.

## Out of scope

- Auditing every other test file in the repo for the same stub-drift
  pattern against other internal functions — issue #435's scope is this
  file's 13 failures; a broader sweep belongs to #419's tracked list,
  which this work adds the new category to (in the record, not as new
  code).
- Any change to `gates/ci.py` or `spawn.py` production code — neither is
  wrong; the stubs are.

## How you'll know it worked

`python3 -m pytest -q` (no `--ignore`) passes, run and reported with the
actual number. `t_issue_comments_stub_shape_contract_catches_old_pre_287_shape`
demonstrates the new check going red on a diverging stub and green on a
matching one.
