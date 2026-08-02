# Survey — issue #189: execution-observation of PR #193 (`implementation` role, phase 2)

## Scope

Observed: role `implementation`, subject `issue-189`. Sessions landed as PR #190
(`product-discovery`, merge `08c0e7b`), PR #191 (`implementation` phase 1, merge
`3b4efdf`), PR #193 (`implementation` phase 2, merge `41b2051`). Code commit under
observation: `b60843f47a194bee278ee93a03044ca7a03d4501`. The observed role's own
phase-2 record commit: `8d2c96abc119d1a2a75a0fdd38223b1a28fb2702`. This survey
focuses on requirement 4 (`flows[].plan` visibility), since that is where the
orchestrating prompt flagged two specific claimed defects against acceptance
criterion 4.4 item 1; the remaining acceptance criteria (1.1-1.3, 2.1-2.4, 3.1-3.4,
5.1-5.5) are scoped for a separate phase-2 pass — see the accompanying proposal.

## Scope skip record (scout-directive)

Scouting is skipped. Skip condition: "the spec literally leaves no design decision
open." This role's own directive fully specifies the verification methodology (a
three-level outcome/trajectory/step verdict, citation-adjacency, a blameless
four-part finding shape, and the record file path), and the acceptance criteria to
check against are already enumerated in the approved `execution-plan.md`. There is
no open product/design choice here to scout industry practice for; this is a
mechanical evidence-gathering task against a fixed spec.

## What was read this session

- `gh issue view 189 --json body,comments` — the full current issue body
  (including both the `방향` section's fenced grammar-illustration block and the
  issue's own real `## 실행 계획 (이 이슈 자체 — 요구 1의 첫 적용 사례)` block) and
  its two comments (`APPROVE issue-189/product-discovery`,
  `APPROVE issue-189/implementation`).
- `git log --oneline --all --graph` — merge topology `08c0e7b` (#190) →
  `3b4efdf` (#191) → `41b2051` (#193), all merged into `main`.
- `git log --oneline --follow -- gates/flows.py` — confirms `b60843f` is the tip
  commit touching this file (only prior touch: `de58ad8`, issue #178, an
  unrelated file-move); current `HEAD` (`41b2051`) matches `origin/main`, so no
  commit after `b60843f` has altered `_plan_from_body`/`flows_payload`.
- `docs/specs/approvers.md` — approver accounts `JiwonJung94`, `jjongkwann`.
- `gh pr list --head issue-189/execution-observation` and
  `gh pr list --search 189` — confirm no PR yet exists for
  `issue-189/execution-observation`, and the issue's two APPROVE comments name
  only `product-discovery` and `implementation`, not `execution-observation`.
- `docs/issue-189/reports/implementation.md` (the observed role's own phase-2
  record, commit `8d2c96a`) — full text. It states explicitly that a *manual*
  `flows --json` reproduction against a real repo was not run ("이 워크스페이스에
  GitHub 레포 쓰기·`gh` 인증 스코프가 없어 실행하지 않았다"), and that
  `test_spawn.py::FlowsPayload.test_flows_plan_only_issue_with_no_board_record_still_gets_entry`
  stood in as the verification evidence for the "Manual check" line in
  `implementation-plan.md`'s "How you'll know it worked" instead.
- `docs/issue-189/reports/implementation/survey.md` (the observed role's own
  phase-1 survey) — full text.
- `docs/issue-189/proposals/execution-plan.md` (approved via
  `APPROVE issue-189/product-discovery`, merged PR #190) — full text,
  acceptance criteria 1.1-5.5.
- `docs/issue-189/proposals/implementation-plan.md` (approved via
  `APPROVE issue-189/implementation`, merged PR #191) — full text.
- `git show b60843f --stat` and `git show b60843f -- gates/flows.py` (full
  diff) — the only commit touching `_plan_from_body` / `_issue_list_all` /
  `flows_payload`'s subject enumeration.
- `git show 8d2c96a --stat` — confirms this commit only adds
  `docs/issue-189/reports/implementation.md`; no code changed.

## Current-state facts relevant to the two claimed defects (traced statically, not executed)

Both traces below come from reading the `b60843f` diff of `_plan_from_body`
(`gates/flows.py`) against the raw issue #189 body text already captured above.
No code was executed to produce either trace.

**Claimed defect 1 (code-fence not skipped).** `_plan_from_body`'s step-scan loop
(`for line in lines[start:]: ... if stripped.startswith("##"): break ...`)
contains no check for a ``` ``` ``` fence delimiter anywhere in the diff. The
issue body's `방향` section wraps a grammar-illustration block in a
triple-backtick ` ```markdown ` fence, and that fenced block's own first content
line is `## 실행 계획` verbatim.

**Claimed defect 2 (exact-match header).** The header scan
(`if line.strip() == "## 실행 계획": start = i + 1; break`) is a literal `==`
comparison, no `startswith`/regex tolerance. The issue's own real plan section
header is `## 실행 계획 (이 이슈 자체 — 요구 1의 첫 적용 사례)` — a superstring of
the exact-match target, not the target itself.

**Combined static trace against issue #189's actual body, line by line.** The
header scan walks the body's lines in document order and returns on the *first*
exact match. The fenced example's `## 실행 계획` line precedes the real block in
the body (it sits in the `방향` section, several sections before the issue's own
`## 실행 계획 (...)` section), and the real block's header never exact-matches
regardless of fence handling. Continuing the trace past `start`: the fenced
example's four `- [ ] step <N> <role>[ ‖ ...]` lines all match `_PLAN_STEP_RE`;
the closing fence line and a blank line do not match the regex and are silently
skipped (not treated as a scan terminator, since only a `##`-prefixed line
terminates the scan); the scan terminates at the real block's header line
(which does start with `##`). This traces to a 4-step, all-`done: false` plan
(`product-discovery`; `architecture ‖ security-threat-model`; `implementation`;
`execution-observation ‖ conformance-review`) — the *illustration's* content —
rather than the issue's actual 3-step recorded plan (`product-discovery` done,
`implementation` done, `execution-observation` not done).

**Tension against the approved spec, noted but not resolved here.**
`execution-plan.md` §1.1 states the block header is "exact, literal"
(`## 실행 계획`) as the grammar the *orchestrator must write*, which matches the
parser's literal-`==` design — meaning the exact-match behavior may be
spec-conformant on its own terms, and the issue body's own real header (with
trailing parenthetical text) may itself be the artifact that departs from
§1.1's frozen grammar, rather than the parser being wrong on that specific
point. The fence-skip gap has no corresponding sentence anywhere in §1.1 or in
`implementation-plan.md`'s "What will be done" — the frozen spec is silent on
fenced illustration blocks. Whether either or both of these read as a genuine
acceptance-criterion violation (vs. a spec gap, vs. an issue-body authoring
inconsistency) is a judgment deferred to phase 2 — this role's phase-1 facet
prohibits verdict language.

**The observed role's own verification did not exercise this path.**
`docs/issue-189/reports/implementation.md`'s §검증 substitutes a synthetic test
fixture for a live `flows --json` run and states the live run was skipped for
environment reasons (no `gh` write scope). Whether that fixture's body text
includes a fenced illustration block or a non-exact-match header is a fact
`test_spawn.py`'s actual new-test bodies will show; not read this session —
reserved for phase 2's step-level check.

## Other candidates surfaced while reading the diff (not evaluated)

Flagged while tracing the diff, as phase-2 check candidates only — no judgment
rendered:

- `_issue_list_all` caps at `--limit 1000`; behavior for a repo with more than
  1000 issues is unstated in the diff and not documented in
  `flows-schema.md`'s §4 update.
- `_PLAN_STEP_RE = re.compile(r"^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$")`
  requires exactly one space after `-` and `\s+` (one-or-more) elsewhere;
  whether this matches every checkbox-spacing variant GitHub's own renderer
  normalizes to is unchecked.
- The role-token text inside a plan step's `(.+)$` capture is passed through
  unvalidated against `spawn.py`'s `ROLES` tuple — this matches
  `implementation-plan.md`'s stated out-of-scope item, so it reads as
  spec-conformant, not a candidate defect, but is listed for completeness.
