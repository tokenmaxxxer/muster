---
status: proposed
files:
  - docs/issue-505/reports/implementation/survey.md
  - docs/issue-505/proposals/2026-08-08-slow-session-attribution.md
  - docs/issue-505/reports/implementation.md
  - test/test_latency_report.py
---

## Request

Mine today's slowest N>=8 sessions (`runs/ledger.jsonl` wall-clock,
spanning both `on-the-record` and `tokenmaxxxer-core`), read each
session's log, and attribute its wall-clock time to one of: (a)
gate-refusal/workaround loops, (b) harness permission walls and retries,
(c) network/tooling stalls, or (d) genuine task size — distinguishing
"the work was big" from "the system fought the worker." Every (a)/(b)
cause becomes a candidate bug: either cross-referenced to an existing
issue (#187 is named as a proven example) or written up as a file-ready
new description.

## Constraints

- Every attributed row must cite its log file and the line range the
  attribution was read from (issue's own acceptance check).
- `test/test_latency_report.py` must be extended so a parser asserts one
  row per analyzed session with a log citation — the check is mechanical
  on citation presence, not on the correctness of the judgment call
  itself (the issue itself marks attribution judgment "unverifiable;
  citations are the floor").
- No new instrumentation: the stream-json log format carries no
  per-event timestamp (confirmed again in survey.md, same constraint
  #501 hit) — attribution is by event content and order, not summed
  sub-durations.

## Rationale

**Chosen approach**: a markdown table in `docs/issue-505/reports/implementation.md`
with one row per analyzed session — `issue | repo | duration_s | cause
class | log citation (file:line-range) | one-line finding` — plus a
separate "bug candidates" section listing each (a)/(b) cause as either an
`#NNN` cross-reference or a complete file-ready description block. A
companion parser function in `test/test_latency_report.py` (mirroring
`compute_idle_gaps`'s style from #501) reads that table and asserts
row-count and citation-presence.

**Alternative considered and rejected**: emit the bug table as a JSON
sidecar file (e.g. `docs/issue-505/reports/implementation/attribution.json`)
instead of a markdown table, and have the test parse JSON directly.
Rejected because the record's own prose is supposed to carry the finding
for a human reader (contract §20 record-shape expectations) and because
GitHub issue file-ready descriptions read naturally as markdown, not as
JSON blobs a human has to re-render — a JSON sidecar would duplicate the
same content in two files with no reader benefit, only sync risk between
them. The markdown table is parsed with a regex, the same technique
`test_latency_report.py` already uses for the #501 proposal file, so
this isn't a new parsing pattern for the codebase.

## What will be done

1. Extend `test/test_latency_report.py` with a `parse_slow_session_table(text)`
   function that reads the markdown table described above and returns one
   dict per row (`issue`, `repo`, `duration_s`, `cause_class`, `log_citation`,
   `finding`), plus a regression test asserting: >=8 rows, every row's
   `log_citation` matches a `path:L\d+(-\d+)?` shape, and every row's
   `cause_class` is one of `a`/`b`/`c`/`d`.
2. Write `docs/issue-505/reports/implementation.md` (phase-2 record,
   gated behind approval per contract v3 s19) containing:
   - The attribution table for the N=10 sessions already identified in
     survey.md (issues 474, 147, 473, 444, 466, 180, 476, 457, 171, 497),
     each row citing the specific log line(s) the finding was read from.
   - A "bug candidates" section: the #187 cross-reference for the
     scratchpad/permission-wall-retry-loop pattern (confirmed present in
     issues 171, 444, 466 today) and any new file-ready description for a
     pattern #187 does not already cover (e.g. gate-refusal loops against
     self-generated wrong-branch/nonexistent-issue paths in board-gate.sh,
     seen in issues 474 and 147, which is a distinct failure shape from
     #187's scratchpad-write wall).
   - Required frontmatter (`code_under_review:`, `loop_state:`) and a
     `## What did not work` heading per record-shape-gate.sh.

## Out of scope

- Fixing any of the identified bugs (gate false-positives, permission-wall
  retry loops) — this issue is measurement/attribution only, per its own
  acceptance criteria; fixes are separate issues (#187 already exists for
  one class).
- Building new log instrumentation (per-event timestamps) to get
  sub-second attribution precision — ruled out for the same reason #501's
  proposal ruled it out (operational-surface change, separate gate).
- Sessions outside the N=10 identified in survey.md; the ledger has 130
  rows today and mining all of them is not what "slowest N>=8" asks for.

## How you'll know it worked

`python3 -m pytest test/test_latency_report.py -v` passes, including the
new slow-session-table test; the record's bug-candidates section
cross-references #187 for the reused pattern and carries at least one
complete new file-ready description block for the pattern #187 doesn't
cover.
