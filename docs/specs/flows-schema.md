# `spawn.py flows --json` schema

Frozen contract for issue #172, based on the approved proposal
`docs/issue-172/proposals/flows-json.md` §2-§3. This document is the
data-contract reference for the `flows` verb output; it does not describe
`flows`' implementation.

## 1. Top-level object

```json
{
  "schema_version": 1,
  "generated_at": "<ISO 8601 UTC>",
  "repo": "<owner/name>",
  "decision_queue": [ ... ],
  "flows": [ ... ],
  "sessions": [ ... ],
  "ledger": [ ... ],
  "hygiene": { ... }
}
```

| field | type | notes |
|---|---|---|
| `schema_version` | integer | see §4 |
| `generated_at` | string | ISO 8601 UTC timestamp of payload generation |
| `repo` | string | `owner/name` of the target board repo |
| `decision_queue` | array | see §2.1 |
| `flows` | array | see §2.2 |
| `sessions` | array | see §2.3 |
| `ledger` | array | see §2.4 |
| `hygiene` | object | see §2.5 |

## 2. Section schemas

### 2.1 `decision_queue[]`

One entry per open PR awaiting phase 1 or phase 2 approval.

```json
{
  "issue": 172,
  "pr": 201,
  "phase": 1,
  "role": "implementation",
  "opened_at": "2026-07-30T09:12:00Z",
  "age_hours": 26.3,
  "awaiting": "approve-scope"
}
```

| field | type | notes |
|---|---|---|
| `issue` | integer | subject issue number |
| `pr` | integer | PR number |
| `phase` | integer | `1` or `2` |
| `role` | string | role name (e.g. `implementation`) |
| `opened_at` | string | ISO 8601 UTC |
| `age_hours` | number | hours since `opened_at` |
| `awaiting` | string | `"approve-scope"` (phase 1) or `"approve-full"` (phase 2) |

### 2.2 `flows[]`

One entry per subject.

```json
{
  "issue": 172,
  "stage": "implementing",
  "stage_derived": true,
  "roles": [
    { "role": "implementation", "loop_state": "scope-approved", "verdict": "progressed" }
  ],
  "prs": [201],
  "plan": null
}
```

| field | type | notes |
|---|---|---|
| `issue` | integer | subject issue number |
| `stage` | string | one of `"proposal"`, `"approved"`, `"implementing"`, `"delivered"`, `"closed"`, OR the raw `loop_state` string when unmapped (see below) |
| `stage_derived` | boolean | `true` when `stage` was mapped from a rulebook-defined `loop_state`→stage rule; `false` when no mapping exists and `stage` holds the raw `loop_state` string verbatim |
| `roles` | array of `{role, loop_state, verdict}` | per-role status within the subject |
| `prs` | array of integers | numbers of currently-open PRs whose branch name matches `issue-<subject>/<role>`, for any role — independent of whether that role has a board record (`docs/issue-<n>/reports/<role>.md`) merged to main yet |
| `plan` | `array<{step, roles, done}>` \| `null` | parsed from the subject's issue body `## 실행 계획` block (issue #189); `null` when the issue body has no such block; otherwise a list — possibly empty if the header is present with no valid step lines — of `{"step": <int>, "roles": [<string>, ...], "done": <bool>}`, one entry per `- [ ]`/`- [x]` step line |

When a subject's `loop_state` has no rulebook-defined mapping to one of
the five named stages, `flows[].stage` is **not** forced into the
nearest bucket — it is set to the raw `loop_state` string and
`stage_derived` is `false`. Consumers must treat `stage_derived: false`
as "this value is not one of the five enum members" and handle it
distinctly (e.g. render as unknown/raw rather than mapping to a fixed
color/label).

`flows[].prs` and `decision_queue` (§2.1) are both derived from the same
open-PR-by-branch-name source, so for any subject that has a `flows[]`
entry, the two never disagree about which PRs are open for it: a PR
number appearing in `decision_queue` for that subject also appears in
its `flows[].prs` (issue #248 — `prs` previously re-filtered by `roles`,
board records, and dropped PRs for roles with no merged record yet).
This does not extend to a subject with **no** `flows[]` entry at all —
`flows[]` is scoped to subjects with at least one merged board record or
an open issue carrying a `## 실행 계획` block (§2.2 `all_subjects`
construction, unchanged by this fix), while `decision_queue` has no such
gate (issue #216) and can list a PR for a subject that never appears in
`flows[]` — there is nothing there for that PR to "appear in".

### 2.3 `sessions[]`

One entry per active roster row.

```json
{
  "role": "implementation",
  "issue": 172,
  "elapsed_min": 14.2,
  "pid": 48213,
  "alive": true,
  "verdict": "pending",
  "last_activity": { "ts": "2026-07-31T12:03:44Z", "kind": "tool_use",
                     "detail": "Write roles/data-modeling.json" }
}
```

| field | type | notes |
|---|---|---|
| `role` | string | role name |
| `issue` | integer | subject issue number |
| `elapsed_min` | number | minutes elapsed since session start |
| `pid` | integer | process id |
| `alive` | boolean | whether the process is currently running |
| `verdict` | string | `"pending"` when `alive: true`; otherwise looked up from the newest matching ledger entry for this role/issue |
| `last_activity` | object \| `null` | see below; `null` when the roster entry has no `log` path, the log file is missing, or its tail could not be parsed |

`last_activity` is derived from the tail of the session's `.session.log` (the
raw `stream-json` transcript) — parsing happens only inside `flows`
(contract provider side); consumers still read only this JSON field, never
the log itself.

| field | type | notes |
|---|---|---|
| `ts` | string | ISO 8601 UTC — the log file's mtime, not a record timestamp (the CLI transcript carries none) |
| `kind` | string | `"tool_use"`, `"text"`, or `"result"` — the type of the last meaningful transcript record found in the tail |
| `detail` | string | human-readable one-liner, truncated to 80 chars: tool name + its most salient input (e.g. `"Write roles/data-modeling.json"`, `"pytest test_spawn.py 실행"`) for `tool_use`; first non-empty line of the message for `text`; the result/subtype string for `result` |

Only the last 64KiB of the log is read (tail-based, not a full scan) and any
read/decode/parse failure yields `last_activity: null` rather than an
error.

### 2.4 `ledger[]`

Aggregated **per issue** (not a raw per-session dump).

```json
{
  "issue": 172,
  "sessions": 3,
  "cost_usd_total": 4.87,
  "outcomes": { "progressed": 2, "refused": 1 }
}
```

| field | type | notes |
|---|---|---|
| `issue` | integer | subject issue number, derived from each raw ledger entry's `board_delta` path (`docs/issue-<n>/...`) |
| `sessions` | integer | count of raw ledger entries attributed to this issue |
| `cost_usd_total` | number | summed cost across attributed sessions |
| `outcomes` | object | map of outcome label → count, keys open-ended (e.g. `progressed`, `refused`, ...) |

Sessions whose raw ledger entry has no derivable issue (empty
`board_delta`) are **not** dropped and **not** guessed onto an issue.
They are aggregated into a separate `unattributed` bucket, documented
alongside `ledger[]` (not one of its per-issue entries):

```json
"unattributed": { "sessions": 1, "cost_usd_total": 0.42 }
```

`unattributed` sits at the same nesting level as `ledger` (an
adjacent top-level-ish field next to the `ledger` array), not inside
any `ledger[]` entry. See the worked example in §6 for exact
placement.

### 2.5 `hygiene`

Single object, not an array.

```json
{
  "closure_sweep": [ /* find_violations() output structure, reused verbatim */ ],
  "unapproved_open_prs": [
    { "issue": 172, "pr": 201, "role": "implementation", "opened_at": "2026-07-30T09:12:00Z" }
  ]
}
```

| field | type | notes |
|---|---|---|
| `closure_sweep` | array | verbatim output of `gates.closure_sweep.find_violations()` — structure owned by that module, passed through unchanged |
| `unapproved_open_prs` | array of `{issue, pr, role, opened_at}` | open PRs past phase 1 (`loop_state` already `scope-approved` or later) with neither a matching `APPROVE issue-<n>/<role>` comment from an approvers.md account nor a PR review Approve from a different approvers.md account |

## 3. Versioning policy

- `schema_version` is a **bare integer**, not semver. There is exactly
  one consumer (repo-status-board), so minor/patch granularity is not
  needed.
- Bump `schema_version` **only** on a breaking change: a field is
  removed, a field is renamed, or a field's type changes.
- Additive changes — a new field appended to an existing object, a new
  optional key, a new section — **never** bump `schema_version`.

Examples:

| change | breaking? | version bump? |
|---|---|---|
| add `pr_url` field to `decision_queue[]` entries | no | no |
| rename `flows[].stage` to `flows[].status` | yes | yes |
| change `ledger[].cost_usd_total` from number to string | yes | yes |
| add a new top-level `notes` array | no | no |
| remove `sessions[].pid` | yes | yes |
| add a new outcome key to `ledger[].outcomes` | no | no |

## 4. GitHub API call-count contract

This is a **load-bearing contract**, not incidental detail — the
dashboard consuming `flows --json` polls this command repeatedly, so
the call count must stay flat as the number of roles grows and linear
(not quadratic) as the number of subjects grows.

For one board repo with `S` open subjects, `R` roles per subject, and
`P` open PRs, a full `flows --json` run makes:

- **1** call — `gh repo view` (cached)
- **1** call — `gh pr list --state all --json number,headRefName,createdAt,state,body,reviews --limit <cap>`, repo-wide; this single call's results are matched locally (by parsing `headRefName` against `issue-<n>/<role>`) to cover `decision_queue`, `flows[].prs`, and the PR-review side of `hygiene.unapproved_open_prs`
- **1** call — `gh issue list --state all --json number,state,body --limit 1000`, repo-wide (issue #189); results are matched locally by issue number to prefetch each subject's issue `state` (reused by `hygiene.closure_sweep`, see below) and to parse `flows[].plan` from each issue's body, and to find open issues carrying a `## 실행 계획` block with no board record yet (the union-expansion subjects)
- **up to `S`** calls — `gh issue view`, one per subject — in the steady state this call is **not** made: `hygiene.closure_sweep` (`closure_sweep.find_violations`) is passed the issue-state map already fetched by the repo-wide `gh issue list` call above and skips its own `gh issue view` for any subject whose issue is in that map. This call is now only a fallback path, for a subject whose issue number falls outside the prefetched set (e.g. the `--limit 1000` cap)
- **up to `S`** calls — `gh api .../comments`, one per subject, for phase-1/2 comment-approval detection

Total: **linear in `S`, flat in `R`** (independent of both `R` and
`P`). The naive per-branch approach this replaces was `O(S×R)`.

## 5. Data provenance: `sessions[]` and `ledger[]` are local-orchestrator data

`sessions[]` and `ledger[]` are sourced from `spawn.py`'s **own**
`runs/` directory (`runs/active.json` and `runs/ledger.jsonl`) — local
state of the orchestrator checkout that ran the sessions. They are
**not** derived from the target board repo passed via `-C`.

A consumer reading only the board repo (its issues, PRs, and
`docs/issue-<n>/...` files) cannot reconstruct `sessions[]` or
`ledger[]` — that data only exists in the orchestrator's local `runs/`
directory and is not written back to the board repo. Any dashboard or
downstream tool relying on these two sections must talk to the same
orchestrator checkout that ran the sessions being reported.

## 6. Non-goals

- **Read-only.** `flows --json` never mutates the board repo and never
  posts comments, matching `status()`'s documented invariant.
- **No exit-code-as-alert semantics.** Hygiene violations are data in
  the payload (`hygiene.closure_sweep`, `hygiene.unapproved_open_prs`),
  not a non-zero exit code. Non-zero exit is reserved for hard failures
  (not-a-board, `gh` auth failure). This is a separate concern from
  `closure-sweep`'s own `--post`/exit-1 behavior, which stays a
  distinct verb.
- **No dashboard polling-cadence guidance.** How often a consumer polls
  this command is the consumer's concern, not part of this schema.

## 7. Worked example

One subject, one PR, one session, one ledger entry, one hygiene
violation:

```json
{
  "schema_version": 1,
  "generated_at": "2026-07-31T08:00:00Z",
  "repo": "tokenmaxxxer/on-the-record",
  "decision_queue": [
    {
      "issue": 172,
      "pr": 201,
      "phase": 2,
      "role": "implementation",
      "opened_at": "2026-07-30T09:12:00Z",
      "age_hours": 22.8,
      "awaiting": "approve-full"
    }
  ],
  "flows": [
    {
      "issue": 172,
      "stage": "implementing",
      "stage_derived": true,
      "roles": [
        { "role": "implementation", "loop_state": "scope-approved", "verdict": "pending" }
      ],
      "prs": [201],
      "plan": null
    }
  ],
  "sessions": [
    {
      "role": "implementation",
      "issue": 172,
      "elapsed_min": 9.5,
      "pid": 48213,
      "alive": true,
      "verdict": "pending"
    }
  ],
  "ledger": [
    {
      "issue": 172,
      "sessions": 2,
      "cost_usd_total": 3.14,
      "outcomes": { "progressed": 1, "refused": 1 }
    }
  ],
  "unattributed": { "sessions": 0, "cost_usd_total": 0.0 },
  "hygiene": {
    "closure_sweep": [
      {
        "issue": 170,
        "violation": "closed_without_delivered_stage",
        "detail": "issue closed while role implementation loop_state=scope-proposed"
      }
    ],
    "unapproved_open_prs": [
      {
        "issue": 172,
        "pr": 201,
        "role": "implementation",
        "opened_at": "2026-07-30T09:12:00Z"
      }
    ]
  }
}
```
