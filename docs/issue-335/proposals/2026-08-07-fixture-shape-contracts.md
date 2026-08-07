files:
- shape_contracts.py
- tests/fixtures/golden/gh_paginate_slurp_sample.json
- test_spawn.py
- docs/handbooks/test-fixture-shape-contracts.md
- docs/issue-335/reports/implementation.md

## Request

가짜 응답이 실제 서버 응답과 모양이 달라서 틀린 코드가 테스트를 통과하고
있었다 — a fake's shape silently drifted from the real external interface
it stands in for, and passing tests built on the drifted fake created
false confidence instead of catching the bug. Fix: make a fake's shape
verifiable against the real dependency it mimics, and make drift fail
loudly instead of passing silently.

## Constraints

- No new external dependency: the project is stdlib-only today (no
  `requirements.txt`/`pyproject.toml`, `spawn.py` imports stdlib only —
  confirmed in the survey). `pydantic`/`jsonschema` happen to be
  importable in this sandbox but are not declared project dependencies;
  adding one for this alone is disproportionate and out of step with
  this repo's own stated "no new external dependencies" preference
  (`docs/issue-285/proposals/spawn-latency-fixes.md`).
- No behavior change to `spawn.py`'s parsing logic (`classify()`,
  `_classify_refusal_text()`, `_tool_result_text()`,
  `_prior_event_details()`, the stream loop at `spawn.py:3161-3230`) —
  this issue is about test-fixture trustworthiness, not about changing
  how the orchestrator parses real events.
- Per #310: the acceptance criterion below must name an executable
  artifact that fails on regression; a doc/handbook entry alone does not
  discharge the requirement.
- Per #330 (stated below in "What this reaches beyond its own acceptance
  criteria"): must state what already-on-disk state this invalidates.

## Rationale

**Chosen: stdlib hand-rolled shape-assertion module + one committed
golden sample per interface, validated once and reused by every
hand-typed fixture.** Considered three alternatives (full findings in
`docs/issue-335/reports/implementation/scout-brief.md`):

1. **Consumer-driven contract testing (Pact)** — rejected: its core
   mechanism requires replaying the same contract against the real
   provider in a separate verification pipeline (a broker, provider-side
   CI hook). This project has no reachable CI hook into Anthropic's CLI
   release process or GitHub's API test suite, so the mechanism that
   makes Pact's drift-detection real (provider-side replay) cannot exist
   here — it would only give the appearance of contract testing.
2. **Record/replay cassette testing (VCR.py)** — rejected: VCR.py's
   request/response matcher is built for HTTP interception; both
   external interfaces here are subprocess stdout (`claude`'s
   stream-json on stdout, `gh`'s JSON on stdout), which VCR.py doesn't
   natively capture. Adapting its matcher to subprocess I/O is more
   machinery than the problem needs, for a project with two call sites,
   not dozens.
3. **Schema library (Pydantic/`jsonschema`)** — rejected as the
   *mechanism*, not the *idea*: the shape-check idea from this pattern
   (define the shape once, validate every fixture against it) is exactly
   what's adopted, but the schema layer itself would be this project's
   first external dependency for something a ~40-line stdlib function
   (walk a dict, assert required keys/types present, raise
   `AssertionError` with a field path on mismatch) does just as
   correctly, with no new supply-chain surface. The failure mode being
   fixed here is "hand-typed dict drifts from reality," not "we lack
   expressive validation" — dependency weight buys nothing extra for
   this repo's two shapes.

## What will be done

- **`shape_contracts.py`** (new, repo-root, flat — matching the
  existing flat layout of `spawn.py`/`test_spawn.py`/`test_gates.py`; a
  `tests/support/` package was considered and rejected after the
  after-proposal warrant hunt reproduced a real `ModuleNotFoundError`:
  no `tests/__init__.py` exists, and an unrelated `tests` package
  elsewhere on `sys.path` shadows a bare `tests.support` import in this
  environment): two functions,
  `assert_gh_paginate_slurp_shape(payload)` and
  `assert_claude_stream_event_shape(event: dict)`. Each walks the
  structure and raises `AssertionError` naming the missing/wrong-typed
  field on mismatch. The Claude-event shape is derived directly from what
  `spawn.py`'s parsing loop actually reads (per the survey: top-level
  `type` in `{result, user, assistant}`; `message.content[]` blocks with
  `type` in `{tool_result, tool_use}`; `tool_result.is_error`,
  `.content`, `.tool_use_id`; `tool_use.id`, `.name`; `result.
  permission_denials` as list-or-absent-or-malformed, all three
  explicitly legal per `spawn.py:3170-3182`'s existing handling).
- **`tests/fixtures/golden/gh_paginate_slurp_sample.json`** (new):
  a real `gh api --paginate --slurp` capture against this repo (the
  empty-page shape `[[]]`, confirmed live during the survey, plus a
  populated-comment capture if a suitable existing issue/PR with
  comments is found during phase 2 — falls back to the empty shape alone
  if none is found, documented either way). This is validated against
  `assert_gh_paginate_slurp_shape` in a new test — the one interface in
  this issue where "verified against the real dependency" is fully true,
  not a weaker proxy.
- **`test_spawn.py`**: every hand-typed `gh api --paginate --slurp` fake
  (`test_spawn.py:3408-3423, 3433-3440`) and every hand-typed
  stream-json event fixture gains a call to the matching
  `assert_*_shape()` function at fixture-construction time (a small
  helper, e.g. `_event(type_, **kw)`, replacing ad-hoc dict literals
  where practical without restructuring unrelated test logic). A
  dedicated new test validates the golden gh sample against
  `assert_gh_paginate_slurp_shape` directly, proving the shape-check
  itself isn't just checking itself.
- **`docs/handbooks/test-fixture-shape-contracts.md`** (new): documents
  the pattern (why, how to add a new golden sample, how to re-capture
  deliberately) per the doctrine ladder for a house convention that
  future test-writers need to follow.
- **`docs/issue-335/reports/implementation.md`**: phase-2 record.

## Out of scope

- **Capturing a real golden sample of the Claude Code CLI's
  `stream-json` output.** This is the higher-risk of the two interfaces
  (survey ranks it highest-risk), but a live capture requires invoking
  `claude --output-format stream-json` as a nested session from inside
  this headless role session — cost, recursion, and policy concerns this
  proposal does not resolve. The shape-check for this interface is
  therefore derived from `spawn.py`'s own parsing code, which verifies
  **internal consistency** (fixtures match what the parser expects) but
  not **external truth** (that the parser's expectation still matches
  Anthropic's actual current CLI output). This is weaker than the gh-api
  leg and is stated as such, not silently presented as equivalent
  coverage — closing the external-truth gap for this interface is a
  follow-up, not claimed as done here.
- No change to `spawn.py`'s actual parsing behavior.
- No `pydantic`/`jsonschema` dependency (see Rationale).
- No change to the rulebook/marketplace manifest fixtures
  (`tests/fixtures/rulebooks/**`) — internal/repo-owned schema, not a
  third-party interface, lowest risk per the survey.
- No re-litigation of issue #290's broken-monkeypatch/tautology/no-CI
  findings — different defect class, filed separately.

## How you'll know it worked

- **Executable artifact (gh-api leg, fully verified against the real
  dependency):** `pytest test_spawn.py -k gh_paginate_slurp` passes only
  when every gh-fixture and the golden sample satisfy
  `assert_gh_paginate_slurp_shape`; deleting a required key from the
  golden sample or a fixture makes the corresponding test fail with a
  named `AssertionError`, demonstrably (phase 2 will show one such
  induced failure and its message in the record, then revert it).
- **Executable artifact (Claude-event leg, internal-consistency only —
  explicitly the weaker leg per Out of scope):** `pytest test_spawn.py -k
  stream_event_shape` fails if a hand-typed event fixture is missing a
  field `spawn.py`'s parser reads, or if `spawn.py`'s parser starts
  reading a field no fixture declares.
- Both tests run under the existing `pytest -q` invocation with no new
  CI wiring required (test-suite-is-decorative/no-CI is issue #290's
  scope, not fixed here).

### What this reaches beyond its own acceptance criteria (per #330)

- Invalidates the informal comment at `test_spawn.py:3433` ("실측: ... 는
  [[]]") as the record of truth for the gh-api shape — the golden file
  plus its validating test replace that comment as the authority.
  Nothing else currently depends on that comment's wording.
- Any future test author who hand-types a new Claude-stream-json or
  gh-api fixture without routing it through
  `shape_contracts.py` reintroduces exactly the drift risk
  this issue describes — the handbook page is the documented expectation
  going forward, but nothing mechanically forces a *new* fixture through
  the check (no fixture-linter). This is a known residual gap, stated
  here rather than left implicit.
- Does not touch, invalidate, or depend on any in-flight proposal
  (`docs/proposals/2026-07-27-shared-core-and-consent.md`, currently
  awaiting approval and unrelated to test fixtures).
