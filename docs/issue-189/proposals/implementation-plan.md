files:
- on-the-record/commands/run.md
- gates/flows.py
- gates/closure_sweep.py
- docs/specs/flows-schema.md
- test_spawn.py
- test_gates.py

## Request

Build the already-approved `docs/issue-189/proposals/execution-plan.md`
(merged via PR #190, approved by `APPROVE issue-189/product-discovery`):
(1) `run.md` prose covering plan grammar/agreement (§1), minimal auditable
edits (§2), no-auto-progress (§3) — plus one rule the approval conversation
added that §3.1 didn't cover: in a `‖` step, a rejected role's PR does not
invalidate already-merged roles in the same step; only the rejected role is
re-spawned, repeated until it passes, and the step stays incomplete until
every role on the line has merged — and plan-exhaustion → human-confirmed
closure (§5); (2) `gates/flows.py` — expand subject enumeration to
`spawn.board()` ∪ (open issues with a plan block), add `flows[].plan`
(`null` or a list of `{step, roles, done}`), consolidate the `gh` calls this
needs into one repo-wide `gh issue list --json number,state,body` call, no
new call class; (3) `docs/specs/flows-schema.md` §2.2 documents the new
field additively, `schema_version` stays `1` per that doc's own §3 policy.

## Constraints

- Grammar, field shape, and the requirement-4 mechanism are frozen by the
  approved proposal's §1.1 and §4.3 — this proposal does not reopen them.
- No new file, board record, or gate/hook (D1/D2/D3, §3.3, §5.5 of the
  approved proposal all say so independently).
- `schema_version` stays `1` — additive only.
- The call-count acceptance criterion (approved proposal §4.4 item 3): "No
  new gh API call class is added; the total per-subject `gh issue view`-
  class call count stays at or below what §4 already documents." This is
  read literally, not loosely — see Rationale.
- Every existing test must keep passing without a behavior change to any
  case it already covers; new tests only exercise the new behavior.

## Rationale

**Whether `gates/closure_sweep.py` may be touched.** The task-level framing
of this implementation stage names only `run.md` / `flows.py` /
`flows-schema.md`. Considered leaving `closure_sweep.py` untouched and
simply adding the new repo-wide `gh issue list` call *alongside* its
existing per-subject `_issue_view` calls (net new call, old calls
unchanged) — rejected: the approved proposal's §4.3 states "No new gh API
call class is added" as its own unqualified clause (separate from the
"per-subject... stays at or below" clause that follows it), and explicitly
names `closure_sweep._issue_view`'s call shape as one of two anticipated
edit targets for satisfying it ("whether `closure_sweep._issue_view` is
changed to accept pre-fetched state, or `flows_payload` special-cases
this... is implementation's call"). An adversarial review pass over this
exact question (dispatched against the approved proposal's text and the
current code, standing in for the unavailable `warrant-hunter` agent type —
confirmed absent from this session's registered agents) confirmed: leaving
`closure_sweep.py` untouched fails §4.4 item 3 on its literal wording. Per
the survey's "Open question this survey resolves" section, `closure_sweep.py`
is therefore in this stage's write set — narrowly, on the exact function the
approved proposal itself names.

**Which of the two named mechanisms.** Considered reimplementing violation
detection inline in `flows.py` using `closure_sweep.classify()` directly
(the other option §4.3 names) instead of touching `find_violations()` —
rejected: `classify()` needs `pr_state` to include `"MERGED"` to detect the
`MERGED_DELIVERY_ISSUE_OPEN` kind, but `flows.py`'s own `_pr_list_all()`
fetches only open PRs today (`--state open`, no `state` field) — an inline
reimplementation would need to *also* widen that call to `--state all` with
a `state` field, which is a second, unrelated pre-existing doc/code drift
(`docs/specs/flows-schema.md` §4 already documents the wider call;
`flows.py:41-42`'s actual code doesn't match it) that is not this issue's
concern to fix. Chosen instead: add one optional keyword parameter,
`issue_states: dict[int, str] | None = None`, to `find_violations()`. When
provided and a subject's issue number is a key, skip the `_issue_view` call
and use the prefetched state. Default `None` preserves every existing
caller's behavior exactly (`closure_sweep.main()` calls it with zero
kwargs). This is the smaller, self-contained edit, and it matches this
repo's own precedent in `docs/issue-182/proposals/proposal.md`'s Rationale
(threading an already-resolved value through an existing parameter rather
than re-deriving it elsewhere).

**Why the new `gh issue list` call fetches `--state all`, not `--state
open`.** Considered `--state open` (matching the approved proposal's own
example command literally, and `_pr_list_all`'s existing `--state open`
convention) — rejected after the adversarial review flagged it: fetching
only open issues means an already-*closed* subject's `plan` field cannot be
distinguished from "issue not in the fetched set" versus "issue has no plan
block" — both would read as `flows[].plan: null`, silently losing plan
visibility exactly when requirement 5 (closure) needs it most. `--state
all` costs nothing extra (still one call) and removes the ambiguity: every
subject already in `spawn.board()` gets its `plan` field populated
correctly regardless of open/closed state; only the *union-expansion* (a
plan-only subject with no board record at all) stays restricted to `state
== "OPEN"`, matching the approved proposal's §4.4 item 1 literally ("any
**open** issue with a `## 실행 계획` block").

## What will be done

**`gates/flows.py`:**
- Add `_issue_list_all(root)`: one `gh issue list --state all --json
  number,state,body --limit 1000` call, same error-handling shape as the
  existing `_pr_list_all` (empty list on non-zero exit or JSON decode
  failure).
- Add `_plan_from_body(body)`: find the line matching exactly `## 실행
  계획` (after `.strip()`); if absent, return `None`. If present, scan
  subsequent lines until one starting with `##` or body end, matching
  `- [ ] step <N>  <role>[ ‖ <role2> ...]` (checkbox `[ ]`/`[x]`/`[X]`);
  return the parsed `[{"step": int, "roles": [str, ...], "done": bool},
  ...]` list (possibly empty if the header exists with no valid step
  lines — still not `None`, since the block itself is present).
- In `flows_payload`: call `_issue_list_all`, build `issue_state_by_n` and
  `plan_by_issue` (`int -> list|None`) from it. Build `all_subjects =
  dict(b)`; for every issue with `state == "OPEN"` and a non-`None` parsed
  plan, add `all_subjects.setdefault(f"issue-{n}", {})`. Iterate
  `sorted(all_subjects.items())` in place of `sorted(b.items())`. Each
  `flows[]` entry gains `"plan": plan_by_issue.get(issue_n)`. The
  `closure_sweep.find_violations` call becomes `find_violations(root,
  subjects=b, issue_states=issue_state_by_n)` — `subjects` stays the
  original board-only `b` (closure-consistency checks are meaningless for a
  subject with no role records yet).

**`gates/closure_sweep.py`:**
- `find_violations(root, subjects=None, issue_states=None)`: when
  `issue_states` is given and `issue in issue_states`, use that value in
  place of calling `_issue_view(root, issue)`. No other behavior changes.

**`docs/specs/flows-schema.md`:**
- §2.2: add `plan` to the field table (`array<{step, roles, done}> |
  null`), with the null/list semantics stated per the approved proposal's
  §4.3, and a `"plan": null` line added to the §2.2 JSON snippet and the §7
  worked example for consistency.
- §4: document the new `gh issue list --state all --json number,state,body
  --limit 1000` call (1, repo-wide), and update the "up to `S` calls — `gh
  issue view`" line to note it now applies only to a subject whose issue
  falls outside the prefetched set (fallback path), not the steady state.
- `schema_version` unchanged at `1`.

**`on-the-record/commands/run.md`:**
- New `## 실행 계획 (Execution Plan)` section, inserted after step-list item
  6 and before `## 띄우기 전에 확인할 것` (the one unambiguous slot after
  the full numbered loop + Mission Board close, per the survey). Covers, in
  order: (a) the frozen grammar block verbatim from the approved proposal's
  §1.1; (b) the agreement procedure, cross-referenced from step 2
  (classification) — plan proposed in conversation when >1 role session is
  anticipated, written only after explicit go-ahead, via `gh issue create
  --body` or `gh issue edit --body`, optional for single-role issues; (c)
  minimal/auditable edits — `gh issue edit --body` only, one plan-only
  change per call, no new audit file (GitHub's own edit history is the
  record), only the orchestrator edits the plan block, never a spawned role
  session; (d) no auto-progress — a step is complete only when every role on
  its line has reached PR merge, reporting composes with the existing
  step-5 PR-explain obligation, the *next* step's spawn still needs the
  user's explicit go-ahead in that turn (reusing step 6's "침묵은 동의가
  아니다" principle by reference, not restating it), and issue #120's
  per-spawn reasoning requirement stands unchanged; (e) the new parallel-
  step partial-rejection rule, stated explicitly as an elaboration of (d):
  already-merged roles in a `‖` step are not redone when a sibling role's PR
  is rejected; only the rejected role is re-spawned, and each re-spawn
  follows the *same* step-3/4 judgment-and-go-ahead procedure as any other
  spawn (not an automatic retry loop — this composes with, not overrides,
  (d)'s go-ahead requirement); the step's checkbox stays unchecked until
  every role on the line has merged; (f) plan exhaustion → human-confirmed
  closure — detected from checkbox + board state (no new signal), reported
  as its own distinct statement (not folded into a step's own
  approval/merge prompt), `gh issue close` only after the user's explicit
  confirmation in that conversation, `closure_sweep.py`'s detect-only
  contract unchanged.
- One added sentence inside existing step 2 pointing to the new section for
  the multi-role case.

**Tests:**
- `test_gates.py`: two new tests on `closure_sweep.find_violations` —
  passing `issue_states` covering a subject's issue skips `_issue_view`
  entirely (monkeypatch `_issue_view` to raise if called, monkeypatch
  `spawn._pr_for_branch` to return `None` so the per-role loop exits before
  any PR call is needed); omitting `issue_states` (or an issue missing from
  it) still calls `_issue_view` as today (regression guard against the new
  parameter silently changing default behavior).
- `test_spawn.py` (`FlowsPayload` class): update the two existing
  `closure_sweep.find_violations` monkeypatch lambdas
  (test_spawn.py:1743, :1853) to accept `issue_states=None` — otherwise
  `flows_payload`'s new keyword call raises `TypeError` against the old
  two-argument lambdas, breaking every existing test in the class. Add
  `self._patch(flows, "_issue_list_all", lambda root: [])` to `setUp` so
  existing tests stay deterministic (mirrors the existing `_pr_list_all`
  patch). New tests: `flows[].plan` is `null` with no plan block in an
  issue body; a plan block parses to the expected `{step, roles, done}`
  list; an open issue with a plan block and no board record still produces
  a `flows[]` entry (roles `[]`, plan populated) — the requirement-4 gap
  this issue exists to close.

## Out of scope

- Everything the approved proposal already places out of scope: D1 (no loop
  syntax), D2 (no automated `gh issue close`), D3 (no `repo-status-board`
  repo change), redefining the 6-value `stage` vocabulary, a rendering
  treatment of `plan`, making plans mandatory for single-role issues.
- Fixing `_pr_list_all`'s pre-existing `--state open`/no-`--limit` drift
  against what `docs/specs/flows-schema.md` §4 documents for the PR-list
  call — identified during survey, not this issue's concern, not touched.
- Role-token validation against `spawn.py`'s `ROLES` tuple inside the
  `flows.py` parser — that constraint governs what the orchestrator *writes*
  (run.md prose), not what the read-only reporter accepts; `flows.py`
  passes role tokens through unvalidated, consistent with its existing
  raw-passthrough handling of unmapped `loop_state` values.
- `doctor()`'s probe extension, `_pr_list_all`/`_issue_list_all` unification,
  or any other refactor not named above.

## How you'll know it worked

- `python3 -m pytest test_spawn.py test_gates.py -x -q` passes, including
  the new tests listed above, with no existing test's assertions changed.
- Manual check: `python3 spawn.py flows --json -C <repo-with-a-plan-only-
  issue>` includes a `flows[]` entry for that issue with `plan` populated
  and `roles: []`, and every other subject's `plan` is `null` or correctly
  populated regardless of open/closed state.
- `docs/specs/flows-schema.md` §2.2/§4 read consistently with the actual
  `flows.py` behavior after the change; `schema_version` still reads `1`.
- `run.md`'s new section, read on its own, gives an orchestrator enough to
  propose a plan, edit it minimally, avoid auto-progressing (including the
  parallel-partial-rejection case), and close an exhausted plan only on
  explicit user confirmation — without inventing anything not stated there.
