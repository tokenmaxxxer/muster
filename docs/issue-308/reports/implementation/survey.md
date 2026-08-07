# issue-308 current-state survey

## Scope of the complaint

An orchestrator judged "not started" from a GitHub issue being open, spawned
duplicate work already delivered that morning (PR #146 vs already-merged #123/#127),
and separately left completed issues unclosed. Root cause named in the issue: three
sources answer "is this done?" partially and nothing composes them — `spawn.py -C`
(board only, blind to open PRs/live sessions), GitHub issue open/closed (depends on
someone remembering to close), `spawn.py ps` (live sessions only, blind to finished
work). Four acceptance items follow directly from the issue body.

## What exists today

**`gates/flows.py` already answers the composed question.** Built across #172, #178,
#189, #197, #216, #222 (`git log --oneline -- gates/flows.py`) — this is not new
ground. `flows.flows(cwd, json)` (gates/flows.py, invoked at spawn.py:2529-2532)
returns, per subject: `flows[].stage` (untouched/in-flight/awaiting/closed — the exact
four-way split acceptance #1 asks for), `sessions` (live, from roster), and
`decision_queue` (PRs awaiting human approve-scope). The schema is documented at
`docs/specs/flows-schema.md`. **Acceptance #1's "one documented command" already
exists** — `python3 spawn.py flows --json` (or the human-table form without
`--json`) — it is not built by this issue, only pointed at.

**The contract does not point at it.** `docs/handbooks/operations.md:391` shows the
"read the board" step as `python3 spawn.py` (no role arg) — the bare `status()`
call (spawn.py:1147-1183), not `flows`. That is the weak view the issue's table
row 1 describes: `board()` (spawn.py:1124-1144) only reads
`docs/issue-<n>/reports/<role>.md` files already merged to main — blind to open PRs
and live sessions by construction, same as the issue's diagnosis. Line 345 of the
same handbook also uses "read the board" as loose task-string prose passed to a
spawned session, not a pointer to `flows`.

**`status()`'s default output buries its own signal (acceptance #3).** For every
subject with any role record, `status()` appends a `(기록 없음: ...)` line listing
every one of the `ROLES` tuple's 42 entries (spawn.py:775-788, confirmed count) minus
whichever few the subject actually has. A subject with one role recorded prints 41
role names as noise on every board read. `flows --json`'s human-table counterpart
(non-`--json` branch of `flows.flows`) does not have this problem — it reports per
subject `stage` and only the roles present, so pointing the contract at `flows`
(acceptance #1) also substantially addresses #3 as a side effect, but `status()`
itself is unchanged and still the thing `spawn.py` (no args) prints by default
(spawn.py main(), the fallback when `a.role` is `None` — confirmed by reading
`main()`: no explicit `a.role is None` branch calls `status`; the CLI's own
docstring for `role` says "생략하면 상태만 보여준다", so the no-args path is where
`status()` is reached). This is the second half of #1/#3: even after the contract
document points humans/orchestrators at `flows`, the bare invocation still emits the
noisy view.

**Acceptance #2 (mechanical refusal at spawn time) has no code today.**
`spawn_cmd()` (spawn.py:2409-2469) builds the `claude -p` argv/env for a role
session. Nothing between argument parsing (`main()`, spawn.py:2489 on) and the
session launch consults `flows.flows()` or `roster_ps()`'s live-session list before
minting. `--issue` (spawn.py:2494-2495) is accepted and threaded into the branch
name / prompt with no existence or state check against the board. This is the literal
duplicate-spawn path the issue's incident describes, and the issue explicitly cross-
references it as "the same shape as #298's approval finding: the check exists, the
spawn path never asks" — `flows` (the check) exists; spawn time never asks it.

**Acceptance #4 (`hygiene.closure_sweep` catches merged-but-open) is already true
and already tested**, contrary to the issue's "confirm it actually detects the case"
framing being an open question. `gates/closure_sweep.py:24` defines
`MERGED_DELIVERY_ISSUE_OPEN`; `classify()` (closure_sweep.py:38) returns it for
exactly (issue OPEN, PR MERGED, PR body carries a closing reference). `test_gates.py:779-781`
(`t_closure_sweep_merged_delivery_issue_open_violates`) exercises this directly:
`classify("OPEN", "MERGED", "Closes #135", 135) == MERGED_DELIVERY_ISSUE_OPEN`. The
issue's own example transcript (`hygiene.closure_sweep: []`) reported empty because,
per `classify()`'s docstring (closure_sweep.py:41-52), a phase-1 proposal PR (merged,
plain `#n` reference only, issue still open) is explicitly the **intended** shape —
not a violation — and the incident's duplicate PR #146 was itself still open, not
merged, so `closure_sweep` had nothing to flag in that specific transcript. No
construction gap found here; the acceptance item's "verify it detects the case"
already resolves to yes by existing test — see `docs/issue-308/proposals/` for how
this is folded into the delivered scope (documented as already-satisfied rather than
rebuilt).

## Boundary against overlapping open issues

Checked by reading each issue directly (no `docs/issue-<n>/` tree exists yet for
any of these, confirmed by directory listing):
- **#374** ("items waiting on operator decision have no floor/clock") — about
  `decision_queue` staleness/priority, a different field of the same `flows` output.
  Does not touch `stage` derivation or the spawn-time refusal this issue asks for.
  No overlap.
- **#325** (closed) — "issues filed and never spawned" — a *different* gap
  (nothing ever spawns) from #308's (something spawns *again*, redundantly). #325's
  delivered `gates/spawn_coverage.py` detects *uncovered* open issues; it does not
  touch duplicate-spawn refusal or the `flows`-vs-`status()` default-view question.
  No code overlap (different files: `gates/spawn_coverage.py` vs this issue's
  `spawn.py` default path and spawn_cmd).
- **#390** ("green attests to state verified, not state landed") — about
  re-establishing gate results after landing, orthogonal to which command tells an
  orchestrator whether work already exists. No overlap.
- **#398** (root `test_gates.py` vs `gates/test_gates.py` collision) — pure test
  infrastructure, already noted as fix-in-flight by the invoking prompt; irrelevant
  to `flows`/`status`/`spawn_cmd` content. No overlap; the baseline command used for
  this survey is `python3 -m pytest -q --ignore=gates` per that note.

None of the four open issues checked own the write set this issue needs
(`docs/handbooks/operations.md`, `spawn.py`'s default-status path, `spawn_cmd`'s
pre-mint check). The boundary is: #308 owns "point the contract at the composed
view, collapse the noisy default, and make duplicate-spawn mechanically refused";
adjacent issues own decision-queue aging (#374) and coverage-of-never-spawned (#325,
closed/delivered) as separate concerns.

## Write set implied by the above

- `docs/handbooks/operations.md` — repoint the documented "read the board" step at
  `flows`.
- `spawn.py` — `status()`/default no-args path (either replace its board-only body
  with a `flows`-backed one, or collapse the missing-role enumeration); `spawn_cmd()`
  or its caller in `main()` — add the pre-mint `flows` consult + refusal/override.
- `test_spawn.py` — coverage for the new refusal behavior and for the default-path
  change.
- `docs/issue-308/reports/implementation.md` — this role's phase-2 record (not
  written this session; phase 1 stops here).

No new dependency, no new env var, no schema/migration.
