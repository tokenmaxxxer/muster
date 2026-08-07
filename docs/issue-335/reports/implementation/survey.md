files:
- spawn.py
- test_spawn.py

# Survey — issue #335 (fakes drift from the real interface)

## Scope of the defect (per the issue text)

"가짜 응답이 실제 서버 응답과 모양이 달라서 틀린 코드가 테스트를 통과" — a
hand-authored fake's *shape* silently diverges from the real external
interface it stands in for, so tests built on the fake keep passing while
the parsing code they're meant to protect mis-handles real output. This is
about **fixture-shape drift against an external dependency**, not about
`test_gates.py`'s broken monkeypatch/tautology/no-CI problems (already
filed separately as issue #290) and not about unchecked prose claims in
general (issue #310) or blast-radius review (issue #330) — those are
adjacent but distinct defects; this survey stays inside #335's own scope.

## Where hand-authored external-interface fakes live today

Delegated research (general-purpose agent, repo-wide grep + read) found
two external interfaces whose response *shape* is hand-typed into test
fixtures with no tie back to the real thing:

### 1. Claude Code CLI's `stream-json` event stream (highest risk)

`test_spawn.py` hand-builds dozens of JSONL lines shaped like
`{"type": "assistant", "message": {"content": [{"type": "tool_use", ...}]}}`,
`{"type": "user", "message": {"content": [{"type": "tool_result", ...}]}}`,
and `{"type": "result", "permission_denials": [...]}` — confirmed at
`test_spawn.py:1745-1746, 1761, 1763, 1788-1791, 1816-1819, 1836-1839,
1855-1856, 1874-1877, 1891-1893, 1918-1919` and more.

The consumer is `spawn.py`'s streaming parse loop (`spawn.py:3161-3230`),
plus `classify()` (`spawn.py:1268`), `_classify_refusal_text()`
(`spawn.py:1623`), `_tool_result_text()` (`spawn.py:1608`), and
`_prior_event_details()` (`spawn.py:1717`). Reading that loop line-by-line,
the fields it actually reads from a real Claude Code CLI stream-json event
are:

- top-level `type` in `{"result", "user", "assistant"}`
- `message.content[]`, each block a dict with `type` in
  `{"tool_result", "tool_use"}`
- `tool_result` blocks: `is_error` (bool), `content` (str or list of
  `{"type": "text", "text": str}` blocks or plain strings — see
  `_tool_result_text()`), `tool_use_id` (str)
- `tool_use` blocks: `id` (str), `name` (str)
- `result` lines: `permission_denials` (expected list of
  `{"tool_name": str}`, but the code explicitly handles it being absent,
  `None`, or a non-list — `spawn.py:3170-3182`, hardened by issue #246)

There is **no schema/model anywhere in the repo** asserting this shape.
The fixture literals in `test_spawn.py` and the parsing code in `spawn.py`
each encode the same tribal knowledge independently. If Anthropic changes
the CLI's stream-json shape (renames a field, changes how multi-block
`tool_result.content` nests, adds a wrapping envelope), the hand-typed
fixtures do not change, `spawn.py`'s parser silently degrades (e.g. a
renamed `tool_use_id` makes every refusal `unattributable` — a branch that
already exists and is designed not to crash, per
`_flush_correlated_refusals`'s docstring at `spawn.py:1656-1677` —
precisely the "fails silently, not loudly" shape #335 describes), and
every test that hand-typed the old shape keeps passing.

### 2. `gh api --paginate --slurp` JSON envelope

`test_spawn.py:3408-3423` fakes the paginate/slurp envelope as
`json.dumps([page1, page2])`, and `test_spawn.py:3433-3440` fakes the
empty-result case as `[[]]` — a comment at `test_spawn.py:3433` records
"실측: ... 는 [[]]" (measured once, by hand, not re-verified
mechanically). I re-ran the equivalent command against this repo just now
to confirm the shape is still current:

```
$ gh api --paginate --slurp -X GET /repos/tokenmaxxxer/on-the-record/issues/335/comments
[[]]
```

— matches the comment. This interface is lower-drift-risk than (1)
(GitHub's REST API is versioned and slower-moving than an actively
developed CLI's streaming format), but the binding is still "a comment
saying it was checked once," not an enforced check.

### 3. Rulebook/marketplace manifest JSON (`tests/fixtures/rulebooks/**`)

Mimics `.claude-plugin/marketplace.json`/`plugin.json`, an
internal/repo-owned schema (on-the-record's own convention, not a
third-party API). Lowest risk of the three — the "external dependency" is
this same repo's own file format, which the codebase already controls and
changes deliberately. Out of scope for this issue's fix (see proposal).

## What already exists to build on

- No schema/model layer of any kind (`pydantic`, `jsonschema`, hand-rolled)
  is used anywhere in `spawn.py` or the test suite today.
- The project has **no dependency manifest at all** — no
  `requirements.txt`/`pyproject.toml` — `spawn.py` imports stdlib only
  (`argparse, contextlib, re, fcntl, hashlib, json, os, stat, string,
  subprocess, sys, tempfile, time`, `collections.Counter`, `pathlib.Path`).
  `pydantic` and `jsonschema` happen to be importable in this sandbox
  environment but are not declared project dependencies — introducing
  either would be the project's first-ever external dependency.
- `docs/decisions/` (2 ADRs) and `docs/handbooks/` have no existing
  page on test fakes, contract testing, golden fixtures, or schema
  validation — this is a new area, not a revision of a documented
  practice.
- The nearest existing precedent for "capture something real, assert
  parsing against it, don't hand-wave" is
  `docs/decisions/2026-07-29-headless-cli-measured-facts.md` (measured,
  not assumed, CLI facts) — a naming/spirit precedent, not a mechanism.

## Prior-art scan (scout, single web-search agent, one round — budget-scoped)

Angles covered in one pass: consumer-driven contract testing (Pact),
record/replay cassette testing (VCR.py) and snapshot testing (syrupy),
and lightweight schema-derived validation (Pydantic/JSON Schema). Full
findings in `docs/issue-335/reports/implementation/scout-brief.md`.
Headline: Pact needs a broker and provider-side CI hook this project has
no access to (`https://docs.pact.io/consumer`); VCR.py is HTTP-shaped and
doesn't map cleanly onto subprocess/stdout capture
(`https://vcrpy.readthedocs.io/en/latest/advanced.html`); the pattern
that fits a small, dependency-free CLI-orchestration project with no live
test access to the real Claude/gh services is: capture one real golden
sample per external interface once, define a shape-check against it,
validate the golden sample once to lock the contract in, and require
every hand-typed test fixture to pass the same check before use — drift
becomes a loud validation failure at test-setup time instead of a silent
pass.

## Write set this proposal will use

- `spawn.py` — no behavior change; only source of truth for which fields
  the shape-check must require (read-only reference during phase 2, not
  edited unless the shape-check surfaces an actual bug in the parser).
- `test_spawn.py` — hand-typed event/gh-response fixtures gain shape
  validation.
- A new small module for the shape-check itself (exact path decided in
  the proposal; see `## What will be done`).
- A new fixtures directory for the one committed real golden sample per
  interface (`gh api --paginate --slurp` is capturable live right now;
  the Claude Code CLI `stream-json` sample cannot be safely captured
  inside this headless session — see the proposal's Out of scope).
- `docs/issue-335/reports/implementation.md` — phase 2 writes this.

No other files reference `classify`, `_classify_refusal_text`,
`_tool_result_text`, or `_prior_event_details` outside `spawn.py`/
`test_spawn.py`/`docs/` (`grep -rn` for each name confirmed).
