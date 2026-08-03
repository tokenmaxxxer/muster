# Current-state survey — issue #228

## Scout skip record

Scouting (product/prior-art sweep) is skipped for this deliverable. Reason:
this is a conformance bugfix to a contract already fully decided —
issue-189 already fixed the target behavior ("계획 소진 판단은 체크박스+보드
상태로만, `gh issue close`는 사람이 확인한 뒤에만") and issue-228 itself
spells out the four requirements the fix must satisfy. There is no external
product category comparable to this repo's bespoke `## 실행 계획` markdown
contract + PR-body closing-keyword gate — the applicable "field" is this
repo's own prior decisions, which this survey covers in depth (issue-126,
issue-135, issue-189, issue-197). Both mandatory skip conditions apply in
combination: the spec (issue-189's decision + issue-228's four requirements)
leaves no external-benchmarking design decision open, and the change is a
conformance fix to code that doesn't yet match an already-adopted contract.

## What exists today

### `gates/pr_reference.py` (issue-126)

- `check_body(issue: int, body: str, phase: str) -> list[str]` — pure,
  network-free. `phase == "phase2"` unconditionally requires
  `_CLOSES_REF` (`Closes|Fixes|Resolves #<issue>`) in the PR body,
  regardless of any execution plan on the issue (`gates/pr_reference.py:26-40`).
  `phase1` requires a plain `#<issue>` ref and (per comment only, not
  enforced by code) forbids `Closes` — the code never actually checks for
  a forbidden `Closes` in the phase-1 branch; it only checks presence of
  a plain ref.
- `check(repo, pr, issue, phase)` fetches the **PR** body via
  `gh pr view --json body,title` (`_pr_view`, line 43) and delegates to
  `check_body`. It never fetches the **issue** body — no plan visibility
  today.
- `_CLOSES_REF = re.compile(r"(?i)\b(closes|fixes|resolves)\s+#(\d+)")` —
  a plain `re.search` over the raw body string, **no code-fence
  awareness**. Verified empirically this session: a `Closes #999` line
  wrapped in a ``` fence still matches. This is the *correct* property
  for this regex's purpose (GitHub parses closing keywords wherever they
  appear, fenced or not, so the gate must not skip fenced content when
  hunting for a real closing reference) — requirement 3 is already
  satisfied by reusing `_CLOSES_REF` unchanged; it must not be wrapped in
  any new fence-skip logic.
- `main()` CLI: `phase = sys.argv[3] if ... else "phase1"` — CLI-level
  default, separate from `gates/ci.py`'s own default (below).

### `gates/flows.py` (issue-189, fence-fixed by issue-197)

- `_plan_from_body(body: str) -> list[dict] | None` (line 79) — parses
  `## 실行 계획` (a literal Korean header, exact code:
  `## 실행 계획`) blocks into `[{step: int, roles: [str], done: bool}, ...]`.
  Returns `None` when no such header exists, `[]` (not `None`) when the
  header exists but no valid step lines follow. Already skips code-fenced
  content in both the header search and the step-collection loop
  (`in_fence` toggle, same pattern as `gates/gates.py`'s
  `record_no_tool_residue_in`) — this is requirement 4's reuse target,
  confirmed working as-is.
- Consumed today only by `flows_payload()` (board-wide reporting,
  read-only) — no gate currently reads `_plan_from_body`'s output to
  make a pass/block decision. This will be the first gate consumer.

### `gates/ci.py` — the CI entry point and the named adjacent defect

- `check(repo, pr=None, issue=None, phase="phase1")` (line 43): calls
  `pr_reference.check(repo, pr, issue, phase)` **only when both** `pr`
  and `issue` are given (line 48) — `phase` defaults silently to
  `"phase1"` if the caller passes `--pr`/`--issue` but omits `--phase`.
  Confirmed empirically: `--phase` is **never** passed anywhere in this
  repo's actual usage (`grep -rn "\-\-phase phase[12]"` across the whole
  tree returns zero call sites — only the docstring and issue-126's own
  report mention the flag). There is no `.github/workflows/` in this
  repo (confirmed by issue-222's survey too) — `gates/ci.py` is invoked
  by convention as `python3 gates/ci.py .` (no `--pr`/`--issue` at all)
  by phase-2 sessions as a final self-check (`docs/issue-178/reports/implementation.md:129`,
  `docs/issue-180/reports/implementation.md:147`, `docs/issue-222/reports/implementation.md:96`).
  So today, `pr_reference`'s phase-2 Closes requirement is **not
  mechanically enforced by any automation** — it exists as a documented
  contract (role-handoff directive text, phase-1/phase-2 PR conventions)
  that a human or a future CI wiring would have to invoke correctly
  (with `--phase phase2`) to actually block on. The silent default is
  exactly the trap: a future caller who passes `--pr`/`--issue` intending
  a phase-2 check, but forgets `--phase`, gets a silent phase-1 check
  instead — the same failure class this issue is fixing would resurface
  through this second door.
- No existing test exercises `ci.check()`'s `pr`/`issue`/`phase` path at
  all (`test_gates.py`'s only `ci.check` test, `t_ci_check_wires_record_fulfils_diff`,
  calls `ci.check(work)` with no pr/issue).

### Empirical check against this repo's own live issues (hunt pass, this session)

Fetched all 77 issues (`gh issue list --state all --json number,title,body --limit 200`)
and ran `flows._plan_from_body` against each. 11 have >=2 plan steps:

| issue | steps (step, done) | incomplete | "only last step incomplete"? |
|---|---|---|---|
| #228 (this one) | (1,F)(2,F) | 2 | no |
| #227 | (1,F)(2,F) | 2 | no |
| #224 | (1,F)(2,F) | 2 | no |
| #223 | (1,F)(2,F) | 2 | no |
| #222 | (1,T)(2,F) | 1 | **yes** |
| #221 | (1,F)(2,F) | 2 | no |
| #218 | (1,T)(2,F) | 1 | **yes** |
| #205 | (1,T)(2,T) | 0 | n/a (all done) |
| #204 | (1,T)(2,T) | 0 | n/a (all done) |
| #197 | (1,**F**)(2,**T**) | 1 | no (out of order) |
| #189 | (1,T)(2,T)(3,T) | 0 | n/a (all done) |

Two live findings:

1. **#222 and #218 confirm the intended convention actually holds in
   practice**: step 1's checkbox is `[x]` by the time step 2 (the last
   step) is the only one open, matching `run.md`'s documented rule
   ("그 스텝의 체크박스는 줄 위 모든 역할이 머지될 때까지 미완료로
   남는다" — checked once all roles on that line have merged). A
   heuristic that requires the closing keyword exactly when "the plan's
   only incomplete step is the highest-numbered step" reproduces the
   correct answer for both real multi-step issues currently at their
   last step.
2. **#197 is a real counter-example to naive checkbox trust**: it is
   *closed*, its step 1 (`implementation`) is still `[ ]`, but step 2
   (`execution-observation`, the later step) is `[x]` — an
   out-of-order, stale checkbox left over from authoring. If this were
   live and step 2's PR were being gated, a heuristic that only checks
   "is there any incomplete step" would misjudge it. This is a real
   risk to name in the proposal's Rationale: checkbox hygiene is not
   perfectly reliable, so the design must fail toward *blocking* (safe,
   matches this file's existing "검사 불가는 통과가 아니다" / "fail
   closed" convention seen at `pr_reference.py:57` and `ci.py:53`), never
   toward silently allowing a premature Closes.

### Existing tests (`test_gates.py`)

- `pr_reference.check_body` phase1/phase2 tests: lines 605-627, 4 cases,
  none pass a plan argument today (function has no such parameter yet).
- `closure_sweep.py` (issue-135) already imports `pr_reference._CLOSES_REF`/
  `_PLAIN_REF` directly for a different purpose (post-merge consistency
  sweep, not a pre-merge gate) — untouched by this issue, confirmed by
  reading `gates/closure_sweep.py` in full; it does not call `check_body`
  and has no phase/plan awareness to change.
- Baseline run this session: `python3 -m pytest test_gates.py -q` →
  61 passed, 1 failed (`t_repo_local_claude_config_stops_the_spawn`,
  a `PermissionError` writing outside this sandbox's allowed paths —
  pre-existing, unrelated to this issue, not touched by the frozen write
  set below).

## Write set this issue will touch

- `gates/pr_reference.py` — `check_body` gains an optional `plan`
  parameter; `check()` gains an issue-body fetch + `flows._plan_from_body`
  call, gated to `phase == "phase2"` only.
- `gates/ci.py` — close the adjacent silent-default defect: require an
  explicit `--phase` whenever `--pr`/`--issue` are both given, instead of
  defaulting to `"phase1"`.
- `test_gates.py` — new cases for both.
- `docs/issue-228/decisions/` — one entry noting the `check_body` public
  signature change (doctrine ladder: changed public signature).

No changes to `gates/flows.py` (requirement 4: reuse `_plan_from_body`,
not reimplement — confirmed nothing in it needs to change for this issue)
or to phase-1 gate logic (constraint: phase-1 rules stay as-is).
