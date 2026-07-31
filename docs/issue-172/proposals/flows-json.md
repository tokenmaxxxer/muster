---
role: implementation
subject: issue-172
loop_state: scope-proposed
---

# Proposal — `spawn.py flows [--json]` + `docs/specs/flows-schema.md`

Survey: [[survey.md]](../reports/implementation/survey.md).

## 1. CLI surface

Add `flows` as a new `a.role` branch in `main()`, next to the existing
`ps`/`closure-sweep`/`watchdog` verbs (same dispatch pattern,
spawn.py:1999+). No new argparse group needed — reuse `-C/--cwd`. New
flag: `--json` (default off → human table via existing `status()`-style
printing; on → the schema payload below to stdout, nothing else on
stdout). Non-zero exit only on hard failure (not-a-board, gh auth
failure) — hygiene violations are data in the payload, not an exit-code
signal (closure-sweep's own `--post`/exit-1 behavior stays a separate
verb; `flows` never mutates and never posts).

## 2. Schema (`docs/specs/flows-schema.md`)

Top-level object, versioned:

```json
{
  "schema_version": 1,
  "generated_at": "<ISO 8601 UTC>",
  "repo": "<owner/name>",
  "decision_queue": [ /* (a) */ ],
  "flows": [ /* (b) */ ],
  "sessions": [ /* (c) */ ],
  "ledger": [ /* (d) */ ],
  "hygiene": { /* (e) */ }
}
```

- `schema_version`: bare integer, bumped only on breaking change (field
  removed/renamed/type-changed). Additive fields do not bump it — this
  is the versioning convention the survey found missing; picking bare
  int over semver because there is exactly one consumer (repo-status-board)
  and no need for minor/patch granularity.
- **`decision_queue[]`** (a): one entry per open PR awaiting phase 1/2
  approval — `{issue, pr, phase: 1|2, role, opened_at, age_hours,
  awaiting: "approve-scope"|"approve-full"}`. Built from the single
  repo-wide `gh pr list --state open --json number,headRefName,createdAt`
  call (see §3), cross-referenced against board `loop_state` to bucket
  phase 1 (`scope-proposed`) vs phase 2 (post-approval, pre-merge).
- **`flows[]`** (b): one entry per subject — `{issue, stage:
  "proposal"|"approved"|"implementing"|"delivered"|"closed", roles:
  [{role, loop_state, verdict}], prs: [pr numbers]}`. `stage` is derived
  from the board `loop_state` values already read by `board()`; where a
  subject has no rulebook-defined mapping to one of the five issue-named
  stages, `stage` is reported as the raw `loop_state` string with a
  `stage_derived: false` flag rather than forced into the wrong bucket —
  this is a deliberate faithfulness-over-neatness call given survey
  finding that there is no central closed-state enum today.
- **`sessions[]`** (c): one entry per `runs/active.json` row —
  `{role, issue, elapsed_min, pid, alive, verdict}`. `verdict` is
  `"pending"` for any row still `alive` (per survey: verdict is a
  post-hoc ledger concept, a running session cannot honestly report one)
  and is looked up from the newest matching `ledger.jsonl` entry for
  `alive: false` rows.
- **`ledger[]`** (d): aggregated **per issue**, not raw per-session dump —
  `{issue, sessions: n, cost_usd_total, outcomes: {progressed: n,
  refused: n, ...}}`. `issue` is derived from each raw ledger entry's
  `board_delta` paths (`docs/issue-<n>/...`); entries whose `board_delta`
  is empty (e.g. `outcome: refused` with nothing written) go into a
  separate `unattributed: {sessions: n, cost_usd_total}` bucket rather
  than being dropped or guessed onto an issue — dropping would silently
  under-report cost, guessing would mis-attribute it.
- **`hygiene`** (e): `{closure_sweep: [...find_violations() output...],
  unapproved_open_prs: [{issue, pr, role, opened_at}]}`.
  `closure_sweep` is `gates.closure_sweep.find_violations(root)` reused
  verbatim (already structured). `unapproved_open_prs` is new logic: for
  each open PR past phase-1 (i.e. `loop_state` already
  `scope-approved` or later) with no matching `APPROVE issue-<n>/<role>`
  comment from an approvers.md account AND no PR review Approve from a
  different approvers.md account, per the two detection paths in
  `approve_scope`/contract v3 s19.

## 3. Rate-limit design (issue item 3)

One repo-wide call replaces the O(S×R) per-branch pattern the survey
flagged:

```
gh pr list --state all --json number,headRefName,createdAt,state,body,reviews --limit <cap>
```

— one call, matched locally to subjects/roles by parsing `headRefName`
against `issue-<n>/<role>`. This single call's `reviews` field also
covers the two-account Approve-review check for (e), avoiding a second
per-PR `gh pr view --json reviews` loop. Total calls for a full `flows
--json` run: 1 (`gh repo view`, cached) + 1 (`gh pr list`, all sections
draw from it) + S (`gh issue view` per subject, needed by closure-sweep's
existing per-subject issue-state check, reused as-is) + up to S
(`gh api .../comments` per subject, for phase-1/2 comment-approval
detection, reused from `_issue_comments`) — linear in S, flat in R,
where the survey's naive version was O(S×R). This will be stated
explicitly in the schema doc's own header as a documented call-count
contract, since the dashboard will poll this repeatedly.

## 4. Reuse map

| section | reused as-is | new |
|---|---|---|
| (a) decision_queue | `board()`, `_approvers()` | repo-wide PR list, phase bucketing |
| (b) flows | `board()`, `frontmatter()` | stage-mapping (with `stage_derived` fallback) |
| (c) sessions | `_roster_load()`, `_alive()` | verdict lookup from ledger |
| (d) ledger | `runs/ledger.jsonl` reader (new: today only `ledger_write` appends, nothing reads it back) | per-issue aggregation, `unattributed` bucket |
| (e) hygiene | `closure_sweep.find_violations()` verbatim | `unapproved_open_prs` check |

## 5. Tests (issue item 4)

- Schema validity: a fixture payload from a synthetic board (a couple of
  `docs/issue-<n>/reports/<role>.md` fixtures under a tmp repo, `git
  init`'d) validated against a hand-written JSON Schema derived from
  §2 — asserts every top-level key present, `schema_version` is an int,
  `hygiene.closure_sweep`/`unapproved_open_prs` are lists.
- Representative case per section: (a) one open PR mid phase-1; (b) one
  subject per stage value including an unmapped `loop_state` (asserts
  `stage_derived: false` path); (c) one alive + one dead roster entry
  (asserts `pending` vs. looked-up verdict); (d) one ledger entry with
  `board_delta` and one without (asserts `unattributed` bucket, not
  dropped); (e) one closure-sweep violation fixture + one unapproved-PR
  fixture, both exercised through fakes/monkeypatched `subprocess.run`
  for the `gh` calls (matching this repo's existing test style in
  `test_spawn.py`, no live network in tests).

## 6. Non-goals

- No mutation, no posting, no exit-code-as-alert semantics — read-only,
  matching `status()`'s own documented invariant (protocol.md §1).
- No dashboard-side polling cadence decision — that is repo-status-board's
  concern, not this schema's.
