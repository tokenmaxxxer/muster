# Survey — issue #189: execution plan in the issue body (implementation stage)

## Scope skip record

Scouting (category best-in-class comparison) is skipped for this survey.
Skip condition: "the spec leaves no design decision open" — the approved
phase-1 proposal `docs/issue-189/proposals/execution-plan.md` already
resolved every product/requirement-level decision for this issue (RICE-scored
candidate selection in §4.2, frozen grammar in §1.1, frozen field shape in
§4.3, acceptance criteria enumerated to §1.1-5.5). What remains is internal
orchestration-tool code shape (which module owns a helper, a regex design) —
not a user-facing surface with a comparable category of best-in-class
products to scout against. This survey instead verifies the approved
proposal's mechanism against the actual current code, since §4.3 left one
concrete refactor choice ("whether `closure_sweep._issue_view` is changed to
accept pre-fetched state, or `flows_payload` special-cases this") to
implementation's judgment.

## `on-the-record/commands/run.md` — where the four requirements attach

`run.md` is one file, prose only (no gates today reference it — it is read
by the orchestrating human/agent conversation, not executed). Structure:

- `## 당신의 루프` (line 15): six numbered steps. Step 2 (line 20) is the
  existing role-classification step the approved proposal's §1.2 ties plan
  proposal to ("When the orchestrator's existing role-classification step...
  anticipates more than one role session..."). Step 3 (line 35) is "누구를
  깨울지" — the per-turn spawn judgment, unenforced by any gate (matches D1:
  "기계가 평가하는 라우팅 표는 없다"). Step 4 (line 41) spawns
  (`run_in_background`). Step 5 (line 50) is the PR-explain obligation,
  including the flow/stage/next structured-context block (issue #54).
- `## 미션 보드` (line 90-167) sits *between* step-list items 5 and 6 in the
  file — item 6 ("사용자의 결정을 중계한다") resumes at line 169, after the
  Mission Board subsection closes. This confirms a full `##`-level section
  can be inserted between numbered-loop items without renumbering; the
  Mission Board is precedent for exactly that pattern.
- Step 6 (line 169) is the decision-relay step: approvals via
  `gh issue comment ... "APPROVE issue-<n>/<role>"`, merges via
  `gh pr merge`, rejections via `gh pr close`. "침묵은 동의가 아니다" is
  stated here (line 191-193) — the proposal's §3.2/§5.3 explicitly reuse
  this exact principle rather than re-stating it.
- `## 띄우기 전에 확인할 것` (line 195) and `## 하지 않는 것` (line 215)
  close the file. Neither currently mentions plans, execution steps, or
  `gh issue close` — confirms requirement 5 (closure) has no existing prose
  home to extend; it needs new prose, not an edit to existing text.

No mechanical gate parses `run.md` — confirmed by `grep -rn "run.md"
gates/*.py` returning zero hits. The additions are pure prose, matching
D1/D3.4/§3.3/§5.5 of the approved proposal (no new hook).

## `gates/flows.py` — subject enumeration and the call-count constraint

`flows_payload()` (flows.py:160-275) is the single function to change.
Confirmed against the actual file (not the proposal's paraphrase, which
cites the same line numbers and matches):

- `b = spawn.board(root)` (flows.py:163) is the *only* subject source today.
  The loop `for subject, roles in sorted(b.items())` (flows.py:188) drives
  every `flows[]` entry. An issue with a plan block and zero merged records
  produces no entry — reproduces the gap the approved proposal's §4.1
  describes, confirmed by reading the code again (not re-trusting the prior
  read).
- `_pr_list_all()` (flows.py:38-50) is the existing precedent for a
  repo-wide, one-call replacement of a would-be per-subject loop — its own
  docstring cites this exact pattern ("replaces an O(subjects × roles)
  ... loop"). The new plan-enumeration call should follow the same shape:
  one `subprocess.run(["gh", ...])`, JSON-decode with a try/except
  `ValueError` guard, return `[]` on any failure — matching `_pr_list_all`'s
  error-handling shape exactly (no new error-handling pattern introduced).
- `closure_sweep.find_violations(root, subjects=b)` (flows.py:259-260) is
  called unconditionally inside `flows_payload`, using the *original*
  board-only `b`. `find_violations` (`gates/closure_sweep.py:71-100`) makes
  its own `_issue_view(root, issue)` call (`closure_sweep.py:53-56`) once
  per subject inside its own loop — this is precisely the "up to `S` calls —
  `gh issue view`, one per subject" line item `docs/specs/flows-schema.md`
  §4 documents, and it is *not* visible anywhere else in `flows.py` (no
  direct `gh issue view` call exists in `flows.py` itself today — it is
  entirely closure_sweep's internal call, indirectly invoked).

**Adversarial check finding (dispatched as this phase's hunt pass, general-
purpose agent standing in for `warrant-hunter` — no such agent type is
registered in this session's available-agent list, confirmed by checking):**
the approved proposal's §4.3 is unambiguous that the new repo-wide
`gh issue list` call must *replace* (not sit alongside) this per-subject
`_issue_view` call — "No new gh API call class is added" is stated as an
unqualified clause, separate from the "per-subject... stays at or below"
clause, and §4.3 explicitly names `closure_sweep._issue_view` as one of two
acceptable edit targets ("whether `closure_sweep._issue_view` is changed to
accept pre-fetched state, or `flows_payload` special-cases this... is
implementation's call"). An initial design that left `closure_sweep.py`
fully untouched and merely added the new call alongside it does not satisfy
this — confirmed by re-reading §4.3's literal text against that design.

Two ways to satisfy this were considered against the actual code:

1. **Thread a pre-fetched issue-state map into `find_violations()`** — add
   one optional keyword parameter, default `None`, so existing callers
   (`closure_sweep.main()` at closure_sweep.py:141, called with no
   `issue_states`) are unaffected. When provided and the subject's issue is
   in the map, skip the `_issue_view` call entirely.
2. **Reimplement violation detection inline inside `flows.py`** using
   `closure_sweep.classify()` (pure, already `gates/closure_sweep.py:39-50`)
   directly, bypassing `find_violations()` altogether.

Checked (2) against the actual data `flows.py` currently has available:
`_pr_list_all()` calls `gh pr list --state open ...` (flows.py:41-42) — no
`state` field, and only open PRs. `classify()` needs to distinguish
`pr_state == "MERGED"` for the `MERGED_DELIVERY_ISSUE_OPEN` violation kind
(`closure_sweep.py:47-48`) — merged PRs never appear in an open-only list.
Route (2) would therefore also require widening `_pr_list_all`'s `--state`
filter to `all` and adding a `state` field — which is itself a *separate*,
pre-existing doc/code drift: `docs/specs/flows-schema.md` §4 already
documents `gh pr list --state all --json number,headRefName,createdAt,
state,body,reviews --limit <cap>`, but the actual `flows.py:41-42` call is
`--state open` with neither a `state` field nor a `--limit`. Fixing that
drift is not this issue's concern and would enlarge the change well past
"minimal." Route (1) is the smaller, self-contained edit and is the one
`docs/issue-182/proposals/proposal.md`'s own precedent style favors
(threading an already-resolved value through an existing parameter, not
re-deriving it) — see that file's Rationale for the same shape of choice on
a prior issue in this repo.

## `gates/closure_sweep.py` — the one function route (1) touches

`find_violations(root, subjects=None)` (closure_sweep.py:71-100) has no
existing test coverage of its own (`test_gates.py` only tests the pure
`classify()` function, lines 618-641 — confirmed via `grep -n "def t_"
test_gates.py`, zero hits for `find_violations`). `test_spawn.py`'s
`FlowsPayload` test class (test_spawn.py:1721+) *always* monkeypatches
`closure_sweep.find_violations` to a replacement lambda before calling
`flows_payload` — it never exercises the real function. Two of those lambdas
have the literal signature `lambda root, subjects=None: []`
(test_spawn.py:1743) and `lambda root, subjects=None: [{"kind": ...}]`
(test_spawn.py:1853). **These will raise `TypeError` the moment
`flows_payload` calls `find_violations(root, subjects=b,
issue_states=issue_state_by_n)`** — a keyword argument the two-argument
lambdas do not accept. This is a hard, mechanical consequence of adding the
parameter, not a judgment call: `test_spawn.py` is therefore part of this
implementation stage's write set, confirmed by reading the exact test code
that would break, not assumed.

## `spawn.py` — subject/role shape the union expansion must stay compatible with

- `board()` (spawn.py:974-991) returns `dict[subject, dict[role,
  frontmatter]]`. `_front_role(root, subject, roles)` (spawn.py:862-875),
  called at flows.py:197, handles an empty `roles` dict safely: `rootless =
  []` (empty iteration), `len(rootless) == 1` is `False`, the two-name
  fallback loop finds neither name `in {}`, returns `None` — confirmed by
  reading the function body directly, not assumed from its docstring. So a
  plan-only subject (`roles = {}`) drives `stage_source = None` →
  `_stage_for(None)` → `("(none)", False)` (flows.py:32-35) with no crash
  and no special-case needed in `flows_payload` beyond the union itself.
- `ROLES` (spawn.py:646-657) is the 41-entry tuple the approved proposal's
  §1.1 requires plan role-tokens to be drawn from — this is a `run.md`-prose
  constraint on what the orchestrator *writes* into a plan, not something
  `gates/flows.py`'s parser needs to validate against (the parser is a
  read-only reporter, consistent with every other raw-passthrough field in
  this payload, e.g. `stage_derived: false` for an unmapped `loop_state`
  reports the raw value rather than rejecting it).

## `docs/specs/flows-schema.md` — the additive edit surface

§2.2 (`flows[]`, lines 62-92) documents the current five fields per entry.
§3 (Versioning policy, lines 188-207) states plainly: "Additive changes — a
new field appended to an existing object... never bump `schema_version`" —
directly settles the approved proposal's §4.3 correction of the issue body's
"필드 추가 = 버전 범프" framing; the schema doc itself, read directly, backs
the proposal's reading. §4 (call-count contract, lines 209-225) needs the
new repo-wide `gh issue list` call documented and the "up to `S` calls — `gh
issue view`" line updated to describe the steady-state (issue found in the
prefetched map → 0 additional calls; issue outside the fetch limit → falls
back to the existing per-subject call). §7 (worked example, lines 254-323)
is illustrative, not normative, but should still show `"plan": null` on its
one `flows[]` entry for internal consistency with §2.2's own field table.

## Open question this survey resolves, not defers

Is `gates/closure_sweep.py` inside this implementation stage's frozen write
set? The issue-level task framing names only `run.md` / `gates/flows.py` /
`docs/specs/flows-schema.md`. But the approved proposal's own §4.3 (part of
the very requirement-4 scope that framing points to) explicitly anticipates
and permits editing `closure_sweep._issue_view`'s call shape as one of two
valid mechanisms, and the call-count acceptance criterion (§4.4 item 3)
cannot be satisfied without touching it or duplicating its logic (rejected
above, see route (2)). Resolved: `gates/closure_sweep.py` is in scope for
this stage, narrowly (one new optional parameter on one function), with the
proposal's own text as the basis, not an independent widening.
