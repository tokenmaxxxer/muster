# Test fixture shape contracts

Why: a hand-typed fake that isn't checked against the real external
interface it stands in for is a second, private specification nobody
maintains. When it drifts, the tests built on it keep passing while
meaning less and less, and the false sense of coverage makes the area
get looked at *less* (issue #335). `shape_contracts.py` (repo root)
turns that drift into a loud `AssertionError` at fixture-construction
time instead of a silent pass.

## What it covers

Two external interfaces `spawn.py` parses that had no schema anywhere in
the repo before this:

- `gh api --paginate --slurp` (GitHub REST API comment envelope) —
  `shape_contracts.assert_gh_paginate_slurp_shape(payload)`. Verified
  against a real captured sample:
  `tests/fixtures/golden/gh_paginate_slurp_sample.json`.
- Claude Code CLI `stream-json` events — `shape_contracts.
  assert_claude_stream_event_shape(event)`. Derived from what
  `spawn.py`'s parse loop actually reads, **not** from a live capture of
  Anthropic's CLI — this leg checks internal consistency (fixture
  matches what the parser expects), not external truth (that the
  parser's expectation still matches the CLI's real current output).
  Closing that external-truth gap is a follow-up, not done here.

Not covered (deliberately, per the issue-335 proposal): the rulebook/
marketplace manifest fixtures under `tests/fixtures/rulebooks/**` — an
internal, repo-owned format, not a third-party interface.

## Using it in a new test

```python
import shape_contracts

# gh api leg
shape_contracts.assert_gh_paginate_slurp_shape(payload)

# stream-json leg — test_spawn.py's _event() helper builds + validates
# in one call:
event = _event("assistant", message={"content": [...]})
```

Route every new hand-typed fixture for these two interfaces through the
matching `assert_*_shape` call at construction time. There is no
fixture-linter enforcing this mechanically — a new fixture that skips
the check reintroduces the exact drift risk this page exists to guard
against.

## Re-capturing the gh golden sample

The committed sample is a real, one-time capture, not a synthetic
literal. To refresh it deliberately (e.g. after GitHub changes the
comment schema):

```
gh api --paginate --slurp -X GET /repos/<owner>/<repo>/issues/<n>/comments \
  > tests/fixtures/golden/gh_paginate_slurp_sample.json
```

Pick an issue/PR with at least one real comment so the sample exercises
the populated shape, not just the empty-page case (`[[]]`).

## Why not Pact / VCR.py / Pydantic

Considered and rejected during the issue-335 proposal — full reasoning
in `docs/issue-335/proposals/2026-08-07-fixture-shape-contracts.md`'s
Rationale section. Short version: Pact needs a provider-side CI hook
this project has no access to; VCR.py is HTTP-shaped and both interfaces
here are subprocess stdout; a schema library would be this project's
first external dependency for something a ~150-line stdlib module does
just as correctly.
