# Scout brief — issue #335

Mode: single web-search agent, one sweep round + no deepening needed
(judge point 1: the three angles converged on one clear-fit pattern, so
stage 2 deepening was skipped — saturation reached in one round). This is
non-product internal test-infra work; "best-in-class" here means
established prior art for the specific failure class (fixture-shape
drift against an external dependency), not a consumer product category.

## Angles and findings

- **Consumer-driven contract testing (Pact).** Core mechanism: the same
  contract is replayed against the real provider in a separate
  verification step, so drift fails on the provider side, not silently.
  Must-be: a provider-side verification hook. Cost: broker service + DSL
  + dedicated pipeline. Fit: poor — this project has no CI hook into
  Anthropic's or GitHub's provider-side tests.
  Sources: https://docs.pact.io/consumer ,
  https://pactflow.io/what-is-consumer-driven-contract-testing/

- **Record/replay cassette + snapshot testing (VCR.py, syrupy).**
  Must-be: the fixture *is* a literal captured real response; replay
  matches exact recorded interactions. `re_record_interval` forces
  re-capture after N seconds, so cassette staleness is at least bounded
  (not indefinite). Cost: light-medium, but VCR.py's request/response
  matcher is HTTP-shaped and doesn't map cleanly onto subprocess/stdout
  capture (Claude CLI, `gh` subprocess) without adaptation. Syrupy
  snapshots *your own parsed output*, not the raw external payload, so
  by itself it doesn't validate the fake's shape against reality.
  Sources: https://vcrpy.readthedocs.io/en/latest/advanced.html ,
  https://syrupy-project.github.io/syrupy/

- **Schema-derived validation (Pydantic/JSON Schema) + one golden
  sample.** Must-be: a real captured golden sample locks the contract in;
  every fixture is validated against the same model before use. Cost:
  lightest — no broker, no CI job, no HTTP interception; a model/schema
  module + one committed golden file per interface, re-captured only via
  a deliberate, explicit script run.
  Sources: https://docs.pydantic.dev/latest/usage/schema/ ,
  https://superjson.ai/blog/2025-08-12-how-to-generate-pydantic-models-from-json/

## Adopt / skip

- **Adopt**: capture-once-golden-sample + shape-check-every-fixture,
  the property all three approaches share stripped to its essentials
  (real ground truth + fail-loud validation + an explicit contract) —
  without Pact's broker or VCR's HTTP-shaped matcher, neither of which
  this project can use.
- **Skip**: adding `pydantic` as a dependency. GAP LINE: the codebase's
  current state is stdlib-only, zero declared dependencies — that "must
  be a schema-validated model" performance axis the field competes on is
  not yet met here, but the gap is closed with a stdlib hand-rolled
  shape-assertion function instead of a new dependency, consistent with
  this repo's own prior stated preference for zero new external
  dependencies (`docs/issue-285/proposals/spawn-latency-fixes.md`'s
  "Out of scope" section, rejecting `watchdog` for the same reason).
- **Skip**: Pact-style provider-side verification — no reachable
  provider CI to hook into for either Anthropic's CLI or GitHub's API.

## Segment fit

One-line: this is closer to "a small CLI-orchestration tool with no test
double for its two external processes" than to any of the three
projects' typical use case (web services with live/staged provider
access) — hence adopting the shared *principle*, not any single tool.

## Stage count / mode

1 sweep stage (3 web-search angles inside one agent call — session tool
budget made a true parallel 3-agent fan-out disproportionate for a
research pass this narrow; documented here as the mode actually used,
not silently presented as parallel fan-out), 0 deepening stages
(saturation at judge point 1). Wall-clock: ~35s per the agent's own
reported duration.
