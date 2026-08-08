# Survey — issue-501 (session-latency breakdown)

SCOUT SKIP: external scouting skipped. This is an internal measurement task
over this repo's own orchestrator telemetry — there is no product-shaped
exemplar to compare against; the only "field" is the ledger/session-log
format this repo already defines. Surveyed that field directly below
instead of an external sweep.

## What exists

- `spawn.py:2602` `ledger_write()` appends one JSON line per finished role
  session to `runs/ledger.jsonl`, resolved under the *installed plugin*
  root, not this git clone: `/home/jwjung/.claude/plugins/marketplaces/
  tokenmaxxxer/runs/ledger.jsonl` (gitignored, `spawn.py:2603-2604`
  docstring: "측정 데이터는 소스가 아니다"). One process across every spawned
  role/issue writes to this single file — it is the "runs ledger" the
  issue refers to.
  - Fields per row (`spawn.py:4018-4032`): `ts` (unix time the row was
    written, i.e. session end), `role`, `cwd`, `repo`, `session_id`,
    `cost_usd`, `turns`, `rc`, `outcome`, `board_delta`, `denials`
    (permission-denial count), `duration_s` (wall-clock,
    `time.monotonic()` delta from spawn start), `rulebook`, `core`,
    `gates` (gate-check text), `log` (absolute path to that session's raw
    transcript), `push_reason`.
  - As of this survey: 123 rows, all `ts` within 2026-08-08 (today), spans
    ~4.3h wall-clock (15453s between first and last row). The issue's "~80
    sessions" estimate underexplains — 123 were actually available; used
    all 123 rather than sampling, since the full set was cheap to read.
- `_session_log_path()` (`spawn.py:3498`) names each session's raw
  transcript `<workspace>.session.<ts>.<pid>.log` next to the workspace
  clone. All 123 `log` paths referenced by today's ledger rows still
  exist on disk (verified: `os.path.exists` for all 123).
- Each `.log` file is the Claude Code `--output-format stream-json`
  transcript: one JSON object per line. Confirmed by direct read of
  `tokenmaxxxer-core-issue-185-implementation.session.20260808T212109.
  1547936.log`. Relevant line shapes:
  - `{"type":"system","subtype":"init", ...}` — session start, tool/model
    config, no wall-clock timestamp field.
  - `{"type":"system","subtype":"hook_started"/"hook_response", ...}` —
    per-hook records (e.g. `SessionStart:startup`), but **no timestamp
    field either** — hook cost cannot be isolated from this log format
    alone.
  - `{"type":"result", ..., "duration_api_ms": <int>, "num_turns": <int>,
    "total_cost_usd": <float>, "permission_denials": [...], ...}` — one
    per session, at the end. `duration_api_ms` is the Anthropic API's own
    reported cumulative response time for the session (model "thinking +
    generation" time as billed), independent of the ledger's
    `duration_s` (process wall-clock).
  - No line in this format carries a wall-clock timestamp per event, so
    "hook time" and "gate-check time" cannot be isolated further than
    `duration_s - duration_api_ms/1000` (whatever is not spent waiting on
    the model API).

## What does NOT exist yet (relevant to acceptance)

- `test/test_latency_report.py` (named in the issue's acceptance check)
  does not exist in this repo yet — it is prospective, step-2 build
  output, not present now.
- No existing report or doc under `docs/` already computes this
  breakdown; #140's "9.5% staircase" measurement (referenced by the
  issue) is a different metric (review acceptance rate via `ledger/`
  at repo root, a *different* "ledger" than `runs/ledger.jsonl` used
  here — same word, two unrelated systems. `ledger/collect.py` counts
  review verdict rates, not session timing.)
- "approval round-trip idle" (time a human takes to Approve between
  phase-1 and phase-2) is not directly recorded anywhere as a field —
  it can only be reconstructed as the gap between one session's end
  (`ts`) and the next session's start (`ts - duration_s`) for the same
  issue/role pair, which conflates orchestrator respawn latency,
  approval wait, and (for cross-role issues) time waiting on a
  different role entirely. Treated as a single "inter-session idle"
  measure below; the survey could not separate approval-wait from
  orchestrator-respawn-wait further with what's recorded.

## Measured (see proposal for the table + interpretation)

Computed directly from the 123 ledger rows + their 123 still-present log
files. Full breakdown, largest term, and candidate-cut analysis are in the
proposal (`docs/issue-501/proposals/implementation.md`) since the issue
requires "no proposal until the numbers name the biggest term" — the
survey establishes what's measurable and from where; the proposal carries
the actual numbers as its evidence.
