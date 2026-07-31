---
role: implementation
subject: issue-172
loop_state: survey
---

# Current-state survey — `flows --json` (issue #172)

## What exists today

- `spawn.py` `main()` dispatches on `a.role` as a pseudo-subcommand switch
  (`init`, `ps`, `watchdog`, `closure-sweep`, `kill`, `watch`, `clean`,
  `update`, `doctor`, `approve-scope`, `drive`, no-arg status). There is no
  `argparse` subparsers object — each verb is an `if a.role == "..."` branch
  in `main()` (spawn.py:1999-2100+). A new `flows`/`flows --json` verb slots
  into the same pattern.
- **Board read** (`board(root)`, spawn.py:967): walks `docs/issue-<n>/`,
  reads `reports/<role>.md` frontmatter per role via `frontmatter()`
  (spawn.py:947, shallow top-level `---` block parser, comments after `#`
  stripped). Returns `{subject: {role: {frontmatter-dict}}}`. `status()`
  (spawn.py:986) is the existing human-readable renderer over this — flow
  state and per-role `loop_state`/`verdict` come straight from here.
- **PR discovery**: `_pr_for_branch(root, branch)` (spawn.py:808) does one
  `gh pr list --head <branch> --state all --json number` call per branch
  (`issue-<n>/<role>`). `_repo_slug` (spawn.py:802) and `_issue_comments`
  (spawn.py:816, one `gh api repos/<slug>/issues/<n>/comments` call) are the
  other GitHub-hitting primitives already in the file. No existing function
  lists **all** open PRs for a repo in one call — `_pr_for_branch` is
  branch-scoped only, and would be O(subjects × roles) calls if reused
  as-is for a decision-queue view. A `gh pr list --state open --json
  number,title,headRefName,createdAt,body` (repo-wide) is a single call and
  cheaper.
- **Phase 1 vs phase 2 / approval detection**: `approve_scope()`
  (spawn.py:871) and `_front_role()` (spawn.py:855) hold the only existing
  logic for "which record is the chain root" and "is this
  scope-proposed/scope-approved". `loop_state` values seen in the repo's
  own rulebooks/records: `scope-proposed`, `scope-approved`, and
  role-specific downstream states (not enumerated centrally — each
  rulebook's state machine owns its own vocabulary). There is no existing
  central catalog of "closed" states; flows would need to treat unknown
  `loop_state` values as opaque strings, not an exhaustive enum.
  Human-approval detection for **phase 2** entry(the two-account
  Approve-review / single-account `APPROVE issue-<n>/<role>` string) is
  currently only checked inline inside `approve_scope`'s comment scan — no
  reusable "is this issue/PR approved" predicate exists to import.
- **Sessions**: `roster_ps()` (spawn.py:1306) reads `runs/active.json`
  (`ROSTER`, gitignored, in-repo-relative to `on-the-record`'s own working
  tree — **not** the target board repo) via `_roster_load()`. Entries:
  `{role, issue, pid, ts, log, work}`. Liveness via `_alive(pid)`
  (`os.kill(pid, 0)`). No `verdict` field is stored on the roster entry —
  verdict is a `ledger.jsonl` concept (session outcome), not a roster
  concept (session liveness). Issue #172(c) asks for
  "역할, 이슈, 경과, verdict" per session — roster has role/issue/elapsed but
  not verdict; verdict only exists post-hoc in the ledger once the session
  ends, so a *running* session structurally cannot carry a verdict yet
  (`(pending)` is the honest value for `RUNNING` rows).
- **Ledger / accounting**: `ledger_write()` (spawn.py:1728) appends to
  `runs/ledger.jsonl` — one line per finished session:
  `{ts, role, cwd, session_id, cost_usd, turns, rc, outcome, board_delta,
  denials, duration_s, rulebook, gates}`. No `issue` field is stored
  directly — the session's issue must be recovered from `board_delta`
  paths (`docs/issue-<n>/reports/...`) or from `cwd` (workspace naming
  convention `issue-<n>-<role>` under `MUSTER_WORK_DIR`, not guaranteed
  parseable). `runs/` is gitignored (`ledger_write`'s own docstring: "측정
  데이터는 소스가 아니다") and lives under `on-the-record`'s own root
  (`ROOT / "runs"`), not under the target board repo — so per-issue
  cost aggregation is inherently local-to-this-checkout, not something a
  remote dashboard reading only the board repo could ever get; `flows`
  must be the thing that reads `runs/ledger.jsonl` and re-exposes it as
  JSON, since nothing else does.
- **Hygiene / closure-sweep**: `gates/closure_sweep.py` `find_violations()`
  (closure_sweep.py:71) already returns a structured list of violations
  (`OPEN_PR_ON_CLOSED_ISSUE`, `MERGED_DELIVERY_ISSUE_OPEN`) by cross-checking
  `gh issue view`/`gh pr view` state against board subjects. This is
  directly reusable — it already returns data, not just printed text;
  `spawn.py`'s `closure-sweep` verb (spawn.py:2006) just prints
  `format_report()` over it. `flows --json` should call
  `closure_sweep.find_violations(root)` directly and serialize the list,
  not re-derive it.
  "승인 흔적 없는 열린 PR" (open PR with no approval trace) is **not**
  covered by `find_violations` — that function only classifies
  issue/PR-state mismatches, not approval-comment absence. This is new
  logic: for each open PR, check whether any `APPROVE issue-<n>/<role>`
  string match or an approvers.md-account PR review Approve exists,
  reusing `_approvers()` (spawn.py:789) and `_issue_comments()`
  (spawn.py:816) but needing a *review* check too
  (`gh pr view --json reviews` for the two-account path — no existing
  helper reads PR reviews at all; would be new).
- **Schema precedent**: no `docs/specs/*.md` file today defines an
  output-data schema with a version field — `docs/specs/approvers.md` is a
  plain list, not a schema doc. `flows-schema.md` would be the first of
  its kind here; there's no existing versioning convention (semver vs.
  bare integer) to inherit from within this repo. `ledger/collect.py`'s
  `--json` flag (`json.dumps(d, ..., indent=2)`, no version field) is the
  closest sibling precedent for "a `--json` flag next to a human-readable
  default" but does not itself version its output.

## Rate-limit accounting (existing GitHub calls, per invocation)

For **one** board repo with *S* subjects (issues) and *R* roles recorded
per subject, and *P* open PRs:

| existing call | cost | reused by |
|---|---|---|
| `gh repo view` (`_repo_slug`) | 1, cached per process if called once | needed once for any `gh api` call |
| `gh pr list --head <branch>` (`_pr_for_branch`) | 1 per (subject, role) branch | O(S×R) if reused as-is — expensive |
| `gh api .../issues/<n>/comments` (`_issue_comments`) | 1 per subject (or PR) | O(S) or O(S×2) if both issue+PR checked |
| `gh issue view` / `gh pr view` (closure-sweep) | 2 per subject with a PR | O(S) |

A naive `flows --json` that loops subjects and calls `_pr_for_branch` per
role would cost O(S×R) `gh pr list` calls. The cheaper path: **one**
repo-wide `gh pr list --state all --json number,headRefName,...` call,
then match PRs to subjects/roles locally by parsing `headRefName` against
the `issue-<n>/<role>` convention — this replaces O(S×R) list calls with
1, and is the only rate-limit-sensitive design decision this issue asks
to make explicit (item 3 of the issue body).

## Gaps for #172

1. No repo-wide "list all PRs with metadata" helper exists — needed for
   both the decision-queue (a) and flow-status (b) sections; must be
   added, and should replace the per-branch `_pr_for_branch` loop pattern
   to keep call count flat in S and R.
2. No "is this PR/issue approved" predicate is reusable outside
   `approve_scope`'s inline scan; the hygiene section (e) needs one that
   also checks PR reviews (two-account mode), which nothing today reads.
3. No schema/version-field precedent in this repo to imitate; §2 of the
   issue explicitly asks for a new `docs/specs/flows-schema.md`.
4. Ledger entries have no `issue` field — must derive it from
   `board_delta` paths, which is lossy for sessions with zero board delta
   (e.g. immediate `refused` outcome) — those sessions are then
   unattributable to an issue and must be reported as `issue: null` rather
   than dropped or guessed.
5. `runs/ledger.jsonl` and `runs/active.json` are **local to the
   on-the-record checkout that ran the sessions**, not to the target board
   repo — `flows --json -C <board-repo>` must read board data from
   `-C <board-repo>` but session/ledger data from `spawn.py`'s own
   `ROOT / "runs"`, which is a source of confusion worth calling out
   explicitly in the schema doc (a dashboard reading the board repo alone
   cannot get sections (c)/(d) unless it also reaches the orchestrator's
   own `runs/`).

Sources: read directly from spawn.py, gates/closure_sweep.py,
ledger/collect.py, docs/specs/approvers.md in this checkout — no external
scouting; this is a pure-internal API-composition task with an existing
JSON precedent (`ledger/collect.py --json`) to follow, and the issue
itself specifies the exact five output sections, so the scout-directive's
"spec leaves no design decision open" skip condition does not fully apply
(rate-limit strategy and schema shape are open decisions) but external
market scouting is not applicable — there is no comparable public product
to benchmark a two-person internal dashboard contract against.
