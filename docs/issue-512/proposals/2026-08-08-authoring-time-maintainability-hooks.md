---
status: proposed
files:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/call-shape-guard.sh
  - on-the-record/hooks/accumulation-claim-guard.sh
  - on-the-record/hooks/test_call_shape_guard.py
  - on-the-record/hooks/test_accumulation_claim_guard.py
  - gates/accumulation.py
  - gates/test_accumulation.py
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
  - spawn.py
  - docs/specs/enforcement-boundary.md
---

# Proposal: authoring-time hooks for the #419/#424 maintainability checks

Subject: #512

## Request

Port the #419 call-shape checks (`subprocess_call_shape_divergence`,
`sibling_mention_check`) and the #424 accumulation-claim check
(`check_accumulation_claim`) out of `gates/ci.py`/`gates/accumulation.py`
— both effectively unreachable now that GitHub Actions is retired — into
deployed `PreToolUse`/`Stop` plugin hooks that fire while a session is
authoring code on an arbitrary target repository, anchored to that
target's own project root, with no assumption the session is running
inside the `on-the-record` marketplace repo. Address the local-diff vs
repo-wide coverage gap this move creates, and evaluate two follow-on
questions: strengthening the accumulation gate to required-field
presence, and adding an advisory maintainability-trend report on the
existing watchdog tick. This is a phase-1 proposal only.

## Constraints

- GitHub Actions is not an enforcement channel (contract, per the issue).
- Hooks must work zero-install on any target repo the plugin is deployed
  to — no `import gates`, no assumption of `on-the-record`'s own tree
  layout, root discovered by walking up from the hook payload's `cwd`.
- The accumulation gate stays a two-shape, evidence-backed check (shape 1:
  inline subprocess/`gh` call growth; shape 5: `roles/*.json`-style
  repeated one-line edits) — the general structural-duplication detector
  was rejected in #419/#424 for false-positive flood and that rejection
  is not reopened here.
- Per contract §14, the accumulation strengthening may check field
  *presence*, never interpret free-text content for correctness.
- `docs/specs/enforcement-boundary.md` must stay complete: every new hook
  row and every changed verdict gets recorded (`gates/test_boundary.py`
  fails the build otherwise).

## Rationale

**Chosen approach: mirror `record-claim-guard.sh`'s pattern** — inline
Python re-implementation of the check logic inside a standalone bash
hook script, shipped in `on-the-record/hooks/`, root found by walking up
from `cwd` for a `.git` directory. This is the only pattern in this repo
that has already solved "runs zero-install on an arbitrary target repo"
(`docs/specs/enforcement-boundary.md`'s `record-claim-guard.sh`,
`pr-preflight.sh`, and `spec-index-preflight.sh` rows all use it), so
reusing it costs no new design risk and keeps the hook set internally
consistent.

**Rejected alternative 1: have the hook `import gates`/`import
accumulation` from the plugin's own installed copy of this repo.** This
was considered because it would avoid duplicating the check logic in two
places (the CI-callable Python module and the hook). Rejected because a
plugin install on a target repo has no guarantee `gates/` ships alongside
`on-the-record/hooks/` at a stable relative path the hook can locate —
the plugin's install layout is `on-the-record/` (commands + hooks) only;
`gates/` is this marketplace repo's own tooling, not part of the shipped
plugin surface. `record-claim-guard.sh` already made and recorded this
same call for the #457 port; diverging here would leave two different
answers to the same question live in one hooks directory.

**Rejected alternative 2: give `sibling_mention_check` and
`check_accumulation_claim` full repo-wide reach at `PreToolUse` time by
having the hook shell out to `git log`/`gh` for the current record or
proposal text on every matching write.** Considered because it would give
authoring-time enforcement the same input reach `gates/ci.py` had running
against a whole PR. Rejected: a `PreToolUse` hook fires on every matching
tool call in a session (potentially dozens of writes), and both checks'
missing input (a specific PR's record text, a specific PR's proposal
body) genuinely doesn't exist yet at authoring time in the common case —
the record and the proposal are usually still being written in the same
session. Paying a `gh`/network round trip per write for input that is
frequently absent trades latency for no additional detection power; the
proposal below instead reads the *local working-tree copy* of the
record/proposal file the session itself is writing, which is both
cheaper and closer to what the session actually intends to submit.

**Rejected alternative 3 (requirement 4, trend measurement): a new
standalone gate script polled by a separate cron/schedule.** Considered
because it would decouple trend measurement from `closure_sweep.py`'s own
release cadence. Rejected because `spawn.py`'s `roster_watchdog()` tick
is already the established, contract-recorded home for board-wide,
observe-only measurement (`closure_sweep.py`, `spawn_coverage.py` both
live there per `docs/specs/enforcement-boundary.md`'s `contract,
orchestrator-loop` rows) — adding a second scheduling mechanism for the
same class of measurement (repo-wide, advisory, no blocking) duplicates
infrastructure the watchdog tick already provides for free.

## What will be done

1. **`call-shape-guard.sh`** (`PreToolUse`, matcher `Write|Edit|
   MultiEdit`): on a `.py` file write, discover the target repo root
   (walk up from `cwd` for `.git`), run the ported
   `subprocess_call_shape_divergence` logic against the target repo's
   full `git ls-files *.py` tree (not diff-scoped — this check's own
   docstring requires repo-wide grouping to compare call sites; see
   "Coverage tradeoff" below), and deny (`exit 2`) with the divergent
   call sites if the new content's file would introduce a flag-shape
   mismatch. Scoped to writes touching `.py` files only, same
   fragment-reading pattern as `record-claim-guard.sh`
   (`content`/`new_string`/`edits[].new_string`).
2. **`call-shape-guard.sh`**, second check in the same script:
   `sibling_mention_check`, diff-scoped to the single file being written
   (no `git diff` needed — the file's new content, checked directly for
   `# sibling: <name>` markers), against the **local working-tree copy**
   of `docs/issue-<n>/reports/<role>.md` for the issue/role pair derived
   from the current git branch name (`issue-<n>/<role>`, same derivation
   `gates/ci.py` already uses) if that file exists on disk — never a `gh`
   fetch. If the branch doesn't match `issue-<n>/<role>` or the record
   file doesn't exist yet, this half is a no-op (nothing to check against
   yet), matching `sibling_mention_check`'s own documented prospective
   limitation.
3. **`accumulation-claim-guard.sh`** (`PreToolUse`, matcher `Write|Edit|
   MultiEdit`): on a write to a `.py` file, run shape 1/5 detection
   against the write's resulting file plus the rest of the target repo's
   tracked tree (`git ls-files`, same as `check_accumulation_claim`'s
   fallback path — no working-diff dependency, so it works identically on
   the first write of a session). If a touched shape is detected, look
   for a `## Accumulation` line with a non-empty labeled body in the
   local working-tree proposal file for the current issue (`docs/
   issue-<n>/proposals/*.md`, glob-matched, or `docs/proposals/*.md` for
   the marketplace-repo-internal warrant-directive shape) — if no
   proposal file exists yet on disk, this hook does not block (the
   proposal is still being authored; a `PreToolUse` code-write hook
   cannot demand a field in a document that hasn't been created), which
   is the deliberate boundary point: this hook catches "wrote the
   proposal, then the code, but the field is missing," it doesn't force
   proposal-before-code ordering (the warrant-directive already owns
   that).
4. **`gates/accumulation.py` strengthening (requirement 3):** change
   `_ACCUMULATION_HEADING`'s match from heading-existence to
   heading-plus-non-empty-body — the section must contain at least one
   non-blank line after the `## Accumulation` heading before the next
   `##` heading or EOF. Still no interpretation of what that line says
   (contract §14) — presence of *a* filled field, not a check the
   prediction is correct. Same strengthening applied to
   `accumulation-claim-guard.sh`'s inline copy (kept in lockstep, same
   as `subprocess_call_shape_divergence`/`sibling_mention_check`'s
   CI-module vs hook duplication already established).
5. **Watchdog-tick trend measurement (requirement 4):** add
   `closure_sweep.py::accumulation_trend(repo)` — scans the currently
   merged tree (not a diff) for shape 1/5 instance counts (inline
   subprocess call sites over the shape-1 threshold, `roles/*.json` file
   count) and reports the counts alongside `find_violations()`'s existing
   observe-only output on each `roster_watchdog()` tick — same wiring as
   `find_violations`/`find_uncovered`, which are actually invoked from
   `spawn.py`'s `_board_wide_sweep()` (called by `roster_watchdog()`), so
   delivering this item also means adding one call there — `spawn.py` is
   in this proposal's write set for that reason. This is a **count report**, not a
   new blocking gate: it tells the board "shape 1 site count moved from N
   to M since the last tick," which is the trend signal a single
   PreToolUse hook (bounded to one session's writes) structurally can't
   produce, because it never sees the whole board's history.
6. Update `docs/specs/enforcement-boundary.md`: add rows for
   `call-shape-guard.sh` and `accumulation-claim-guard.sh` (verdict
   `contract`, zero-install, ships with plugin — same shape as
   `record-claim-guard.sh`'s row); update `accumulation.py`'s existing
   row description to note the field-presence strengthening and the new
   hook that also reaches its logic; add a note to `closure_sweep.py`'s
   row for the new `accumulation_trend` advisory output.
7. Unit tests for both new hook scripts (mirroring
   `test_record_claim_guard.py`'s pattern: feed a synthetic JSON payload
   on stdin, assert exit code and stderr content) and for the
   strengthened `_ACCUMULATION_HEADING` behavior in
   `gates/test_accumulation.py`, and for `accumulation_trend` in
   `gates/test_closure_sweep.py`.

### Coverage tradeoff (requirement 5)

A `PreToolUse` hook only ever sees the file(s) one write touches, plus
whatever the hook chooses to additionally scan on disk at that moment —
never a PR-wide diff and never other sessions' concurrent writes. This
proposal's hooks compensate by scanning the *whole on-disk tree* (`git
ls-files`) rather than a diff for shape/flag comparison, which recovers
`gates/ci.py`'s repo-wide call-shape grouping and accumulation-shape
detection at each write — but it still only sees **this session's local
working tree at write time**, not what has since merged from other
concurrent sessions on other branches. What's lost relative to CI's
repo-wide scan against a merged PR: a divergence introduced by two
different sessions' branches that only becomes visible once both merge
(session A's call site and session B's differently-shaped call site never
coexist in either session's local tree). The watchdog-tick
`accumulation_trend` measurement (item 5) is the compensating mechanism
requirement 5 asks for: it runs against the merged board state each tick,
so a cross-session divergence that no single authoring-time hook could
see becomes visible as a trend-count change at the next tick, reported
advisory (not blocking) to the board.

## Out of scope

- Reopening the general structural-duplication detector rejected in
  #419/#424.
- Making `accumulation_trend` a blocking gate — it stays advisory,
  matching `closure_sweep.py`'s own observe-only contract.
- Retrofitting `gates/ci.py`'s PR-context-dependent inputs (fetching a
  specific PR's record/proposal body over `gh`) into the hooks — the
  hooks read only the local working tree, per the Rationale's rejected
  alternative 2.
- Any change to `_SEMANTIC_FLAGS`, the shape-1 threshold constant, or the
  shape-5 `roles/*.json` pattern — those stay exactly as #419/#424 set
  them.
- Phase-2 implementation. This PR is proposal-only.

## How you'll know it worked

- `docs/specs/enforcement-boundary.md`'s completeness check
  (`gates/test_boundary.py`) passes with the two new hook rows present.
- A synthetic `Write` payload introducing a flag-shape-divergent
  `subprocess.run` call on a target repo with an existing divergent
  sibling call is denied by `call-shape-guard.sh` with exit code 2 and a
  stderr message naming both call sites.
- A synthetic `Write` payload touching a shape-1/shape-5 file with no
  `## Accumulation` field (or an empty one, post-strengthening) in the
  local proposal file is denied by `accumulation-claim-guard.sh`; the
  same payload with a filled field passes.
- `gates/test_accumulation.py` covers the empty-body-after-heading case
  failing where heading-only used to pass.
- `closure_sweep.py`'s watchdog-tick output includes an
  `accumulation_trend` count report, tested in
  `gates/test_closure_sweep.py` against a synthetic repo state.
