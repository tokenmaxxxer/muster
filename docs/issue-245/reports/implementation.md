---
code_under_review:
  - gates/ci.py
  - gates/test_closes_gate_ci.py
  - .github/workflows/plan-aware-closes-gate.yml
loop_state: in-progress
---

# Implementation record — issue #245

Phase 2, executing the approved proposal
(`docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md`,
approved via issue-level comment `APPROVE issue-245/implementation`,
single-account mode, role-handoff contract v3, PR author and approver
both jjongkwann) plus 2 items of feedback posted on PR #257 (2026-08-03,
separate from the approval): (1) name the PR-metadata extraction
mechanism and decide fail-open vs fail-closed with the trade-off; (2)
justify blocking branch-protection admin bypass under the single-account
model, including the residual bypass surface.

## What was done

`gates/ci.py`:
1. `_ISSUE_BRANCH = re.compile(r"^issue-(\d+)/")` and pure functions
   `_issue_from_branch(branch)`, `_closes_ref_for_issue(body, issue)`,
   `_phase_from_body(body, issue)`, `_phase1_mismatch(body, issue)` —
   network-free, unit-tested directly (matching this codebase's existing
   split between `pr_reference.check_body`, pure/tested, and
   `pr_reference.check`, the thin network wrapper).
2. `_autodetect_issue_phase(repo, pr, issue, phase)` — wires the pure
   functions to `_pr_head_ref`/`pr_reference._pr_view` (both pre-existing).
   Derives the issue number from the PR's head branch name
   (`issue-<n>/<role>`, already the contract-mandated naming convention —
   reuses `gates.gates.BRANCH_ROLE`'s established convention, not a new
   one) rather than the PR body, and phase from whether the body has a
   Closes/Fixes/Resolves keyword pointed at that issue number. Fails
   closed (returns blocking-reason strings, not silent pass) when the
   branch doesn't match the convention or the PR/body can't be read.
   Full mechanism + fail-open/closed trade-off write-up (feedback item 1):
   `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`
   §1.
3. `check()` gained a `closes_only: bool = False` parameter (default
   preserves 100% of prior behavior — existing tests untouched). When
   `True`, only the plan-aware Closes gate (`pr_reference.check`) plus
   the new phase1 closing-keyword mismatch check run;
   `gates.role_scope`/`record_*`/`deps`/protected-path checks are
   skipped. This is a deviation from the approved proposal's literal
   design — see "Rationale for deviations" below.
4. `_phase1_mismatch`: the requirement-2 fix (phase-1 "Closes forbidden"
   rule now has a real mechanical check). `pr_reference.check_body`'s
   phase1 branch (frozen, #228-owned) only checks for a plain `#N`
   reference and never checks for absence of a closing keyword despite
   its own error message claiming otherwise (survey §1) — this
   orchestration-layer check reuses `pr_reference._CLOSES_REF` (already
   reused the same way by `closure_sweep.py`) to close that gap without
   touching the frozen file.
5. CLI: `--closes-only` and `--autodetect` boolean flags in `main()`.

`gates/test_closes_gate_ci.py` (new, 17 tests, all passing): covers the
4 pure functions above (branch parsing, phase derivation, mismatch
detection — including the two hunt-driven regression tests, see Hunt)
and `check(..., closes_only=...)`'s scoping behavior, with
`pr_reference._pr_view`/`ci._pr_head_ref` monkeypatched for the
network-touching integration tests (no real `gh` calls in the test
suite itself, matching `test_gates.py`'s own "no network" convention).
Kept as a separate file rather than added to the root `test_gates.py`
because this session's approved write set is `docs/issue-245/`,
`.github/`, `gates/` only.

`.github/workflows/plan-aware-closes-gate.yml` (new): runs on
`pull_request` (opened/edited/synchronize/reopened) against `main`,
checks out `main` itself (never the PR's own head — a PR can't edit
`gates/ci.py` to defeat its own check, and this also means fork PRs are
handled safely with only `contents: read`/`pull-requests: read`/
`issues: read`), and runs
`python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only`
with `PR_NUMBER` passed via `env:` (never interpolated into the shell
string directly, even though it's numeric GitHub metadata — no runtime-
derived value reaches the shell as text).

`docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`
(new): full write-up for both PR #257 feedback items — extraction
mechanism + fail-closed decision + cost of each direction (§1); admin-
bypass justification including the residual "an admin can still edit
the branch-protection rule itself" surface, grounded in this repo's
real collaborator permissions (`gh api .../collaborators`: both
approvers.md accounts hold `admin: true`) and a re-read of
`gh-guard.sh`'s actual rule list (§2).

## What was NOT done: branch protection activation

The proposal's design (and issue #245 requirement 1) isn't actually
*enforced* until main's branch protection rule requires this workflow's
check and has "Do not allow bypassing the above settings" on. I did not
flip this on. `gh auth status` confirms this session's token
(`jjongkwann`, scope `repo`) is technically capable of the API call, so
this isn't an authority gap in the narrow sense — but per this turn's
instruction ("브랜치 보호 활성화가 권한 밖이면 정확한 절차를 기록에
남기고 사람 몫으로 넘겨라") and the system-level guidance to confirm
before hard-to-reverse, shared-infrastructure changes in an unattended
headless run, I'm handing this off rather than acting unilaterally.
It's also the proposal's own stated boundary — its "Out of scope"
section already named this exact step as something to "perform after
human approval" within phase 2, separate from the one approval already
given for starting phase 2 at all.

**Procedure for the human to run** (idempotent to re-run; `gh` CLI,
repo admin required):

```bash
gh api -X PUT repos/tokenmaxxxer/on-the-record/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks.strict=false \
  -f 'required_status_checks.contexts[]=closes-gate' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='' \
  -f restrictions=''
```

(The exact check "context" name GitHub records is the job id in the
workflow — `closes-gate`, per `.github/workflows/plan-aware-closes-gate.yml`
`jobs.closes-gate` — confirm the literal string via `gh api
repos/tokenmaxxxer/on-the-record/commits/main/check-runs` after this PR
merges and the workflow has run at least once, since GitHub only offers
a status check as selectable/required after it has reported at least
once against the branch.) `enforce_admins=true` is the "Do not allow
bypassing the above settings" toggle (feedback item 2). Verify with
`gh api repos/tokenmaxxxer/on-the-record/branches/main/protection` (should
no longer 404).

**Recommended regression check after activating**, before trusting it:
open a throwaway PR from a branch named `issue-245/implementation`-shaped
(or any real open issue with an incomplete plan) whose body contains
`Closes #<n>` and confirm the merge button is actually blocked and shows
`closes-gate` as a failing required check; then confirm a clean PR (no
closing keyword, plan-shaped branch) shows it passing. This is the
"실물 확인" issue #245 requirement 3 asks for — I verified the
underlying check logic end-to-end against real GitHub data (below) but
did not create an actual test PR or drive a live required-status-check
UI state, since doing so pushes to shared branches/PRs, which is exactly
the kind of act this session is deferring to the human.

## What did not work

- First read of the approved proposal's "what will be done" section
  said to wire `.github/workflows/` to call
  `gates/ci.py --pr <n> --issue <n> --phase <phase1|phase2>` — the full
  `ci.check()` bundle, not a scoped-down one. Before writing any
  workflow YAML I dry-ran that literal invocation against this session's
  own real PR #257 (`python3 gates/ci.py . --pr 257 --issue 245 --phase
  phase1`, unmodified pre-change code). Expected: passes (or blocks for
  a reason relevant to issue #245). Actual: blocked on
  `write_scope 이탈: docs/issue-245/proposals/2026-08-03-plan-aware-closes-gate-wiring.md
  (역할 implementation, 허용: src/**, test/**, docs/issue-*/reports/implementation.md,
  docs/issue-*/reports/implementation/**, docs/issue-*/proposals/implementation.md)`
  — a pre-existing, unrelated defect: `gates/gates.py`'s
  `_always_writable()` hardcodes the proposal-file pattern as
  `docs/issue-*/proposals/<role>.md`, but every phase-1 proposal in this
  repo's actual history (including this issue's own,
  `2026-08-03-plan-aware-closes-gate-wiring.md`) uses a dated-slug
  filename per the proposal-shape convention, not `<role>.md`. Wiring
  the full bundle as a required, non-bypassable check would have
  self-locked the repo — including this very delivery PR — the moment
  branch protection went live, on a defect this issue never asked me to
  fix and that's outside its frozen write set (`gates/gates.py`, not
  `gates/ci.py`/`.github/`/`docs/issue-245/`). See "Rationale for
  deviations" and "Open findings".
- First cut of `_phase_from_body`/`_phase1_mismatch` used
  `_CLOSES_REF.search(body)` (first match only). The adversarial hunt
  (assume-incomplete-coverage stance, below) found this breaks when a
  body mentions an unrelated issue's closing keyword before the real
  one — e.g. `"Fixes #999, ... Closes #245"` — `.search()` stops at the
  `#999` match, sees it doesn't match the target issue, and reports no
  closing keyword at all, even though `Closes #245` is right there.
  Expected: any closing-keyword-for-this-issue anywhere in the body gets
  caught. Actual: only the *first* closing-keyword match in the whole
  body was ever inspected, regardless of which issue it targeted — an
  attacker (or an accidental co-mention) could plant one earlier,
  unrelated `Fixes #N` to blind the check to a real `Closes #245` later
  in the same body. Fixed by adding `_closes_ref_for_issue()`, which
  scans all matches (`.finditer()`) and returns the first one that
  targets the given issue, and rewiring both `_phase_from_body` and
  `_phase1_mismatch` through it. 2 new regression tests added
  (`t_phase1_mismatch_catches_closes_after_an_earlier_unrelated_reference`,
  `t_phase1_mismatch_matches_inside_fenced_quote`); full 17-test suite
  re-run clean after the fix.
- First commit attempt (`gates/`, `.github/`, `docs/issue-245/` only,
  per this session's stated write-set boundary) was mechanically refused
  by `handbook-trigger-gate.sh`: any commit touching a
  `.github/workflows/*.yml` operational surface must touch a
  `docs/handbooks/<component>.md` in the same commit (contract §21).
  Expected: the write set for this session stays inside `docs/issue-245/`,
  `.github/`, `gates/` as this turn's instructions stated. Actual: a
  harness-enforced gate outside my judgment required a
  `docs/handbooks/operations.md` edit before any commit could land at
  all — added a small bilingual "머지 게이트 (CI)"/"Merge gate (CI)"
  subsection there (see Doc-placement ladder) rather than leave the
  delivery uncommitted.

## Rationale for deviations

Two deviations from the approved proposal's "What will be done", both
forced by the write_scope discovery above (same root cause):

1. **The required check runs `gates/ci.py --closes-only`, not the full
   bundle the proposal named.** The proposal's own "Constraints" section
   already restricts `gates/pr_reference.py`'s judgment logic to
   unchanged; it says nothing about scoping `ci.check()`'s *other*,
   unrelated checks (`role_scope`/`deps`/`record_*`) in or out. Making
   those newly hard-required for every future PR — including ones that
   have nothing to do with the Closes gate — is a materially bigger,
   separate policy change than "wire the Closes gate", and, as measured
   above, is actively broken today for a reason unconnected to this
   issue. `closes_only=True` keeps the delivered check scoped to exactly
   what issue #245 requirement 1 asks for (the plan-aware Closes gate +
   requirement 2's phase1-mismatch fix), leaves `role_scope`/`deps`/
   `record_*` exactly as un-required as they already were (no new
   exposure, no regression), and avoids needing to touch
   `gates/gates.py` at all — which is outside this issue's approved
   write set. The `_always_writable()` defect itself is not fixed here;
   see "Open findings" item 1.
2. **Branch protection is not activated in this session** — see "What
   was NOT done" above. This is a scope-boundary call, not a code
   change, so it doesn't touch the frozen write set question, but it is
   a divergence from the proposal's phase-2 design being fully executed
   end-to-end within this PR.

## Open findings

Two items are real but outside this issue's frozen write set (approved
proposal's phase-2 design: `.github/workflows/*.yml`, `gates/ci.py`'s
phase1-mismatch addition — not `gates/gates.py`, not
`pr_reference.check`'s internals):

1. **`gates/gates.py`'s `_always_writable()` proposal-file pattern
   doesn't match this repo's real proposal-naming convention.** It
   hardcodes `docs/issue-*/proposals/<role>.md`, but every phase-1
   proposal actually written in this repo (including this issue's own)
   uses a dated-slug filename
   (`docs/issue-<n>/proposals/<date>-<slug>.md`) per the
   proposal-shape-directive. Discovered by dry-running the approved
   proposal's literal design (the full `ci.check()` bundle, not
   `closes_only`) against this session's own real PR #257 — it blocked
   on a `write_scope 이탈` for the phase-1 proposal file itself. Left
   unfixed here (see "Rationale for deviations" item 1); resolution
   path is a follow-up issue against `gates/gates.py`'s
   `_always_writable()` (or `_write_scope_overrides`), scoped to fixing
   the pattern-vs-convention mismatch, not to this issue's Closes-gate
   wiring.
2. **No atomic snapshot across the up-to-3 separate `gh pr view` body
   fetches within one `--autodetect --closes-only` run** (hunt finding
   2, below) — a body edited mid-run could produce an inconsistent
   read. Accepted as a residual risk sharing the same unsynchronized-
   multi-fetch class `pr_reference.check`'s already-frozen phase2 path
   has (body fetch, then a separate issue-body fetch) without ever
   being flagged as a defect in #228. Resolution path, if ever pursued:
   thread a single fetched body through `check()`'s pr+issue+phase
   branch instead of letting `_autodetect_issue_phase`,
   `pr_reference.check`, and `_phase1_mismatch` each fetch
   independently — deferred because closing it requires either touching
   frozen `pr_reference.check` internals or adding body-threading
   plumbing for a race that needs an adversary to time an edit within a
   single CI run.

## Next steps

1. Human runs the branch-protection activation procedure in "What was
   NOT done" above (`gh api -X PUT .../branches/main/protection`,
   `enforce_admins=true`), after confirming the exact required-check
   context string once this PR has merged and the workflow has reported
   at least once against `main`.
2. Human runs the recommended post-activation regression check (a
   throwaway closing-keyword PR against a plan-incomplete issue actually
   gets blocked by a live required check; a clean PR passes) — this is
   what closes out issue #245 requirement 3's "실물 확인" completely;
   this session verified the logic end-to-end against real GitHub data
   but did not drive a live required-status-check UI state (see
   "Verification run").
3. File a follow-up issue against `gates/gates.py`'s
   `_always_writable()` for the proposal-file pattern mismatch (Open
   findings item 1) — needed before the *full* `ci.check()` bundle
   (role_scope/deps/record checks) could ever safely become a required
   check; not needed for this issue's own delivery, which stays scoped
   to `closes_only=True`.
4. Open findings item 2 (multi-fetch race) has no assigned follow-up —
   accepted residual risk, revisit only if `pr_reference.check` is ever
   restructured for other reasons.

Once steps 1-2 land, `loop_state` moves to `landed` and
`docs/handbooks/operations.md` picks up the standing CI/gates
description per "Doc-placement ladder" below.

## Doc-placement ladder

- Format/library choice over a named alternative -> `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`:
  (a) issue-number extraction source (branch name, not PR body — body
  rejected for ambiguity when multiple issues are mentioned) + fail-open
  vs fail-closed on extraction failure (fail-closed chosen, costs of
  both directions recorded); (b) admin-bypass block justification under
  single-account mode + the residual "admin can still edit the
  protection rule itself" surface that remains open regardless.
- No new env var / dependency / migration -> N/A. `GH_TOKEN` in the
  workflow is `secrets.GITHUB_TOKEN`, a GitHub Actions built-in, not a
  manually-configured variable; no `.env.example` entry needed.
- Setup step (new CI workflow) -> `docs/handbooks/operations.md`, new
  bilingual "머지 게이트 (CI)"/"Merge gate (CI)" subsection (added same
  commit as `.github/workflows/plan-aware-closes-gate.yml` — see "What
  did not work": the first commit attempt was mechanically refused by
  `handbook-trigger-gate.sh` for touching a `.github/workflows/*.yml`
  operational surface without a handbook update, which is what actually
  forced this entry to land now rather than after activation as I'd
  first planned). States plainly that nothing is blocked yet and points
  to this record's activation procedure — not overclaiming enforcement
  that isn't live.
- No benchmark/investigation numbers produced -> no additional
  `docs/issue-245/reports/` entry beyond this record and the phase-1
  survey/scout-brief.

## Verification run

`python3 gates/test_closes_gate_ci.py` — 17/17 pass (new tests, no
network). `python3 test_gates.py` — the 2 pre-existing tests that
exercise `ci.check()` (`t_ci_check_missing_phase_with_pr_and_issue_blocks`,
`t_ci_check_wires_record_fulfils_diff`) both still pass unchanged; the
suite's `__main__` runner stops at the first failure and hits one
unrelated pre-existing failure (`t_repo_local_claude_config_stops_the_spawn`,
`PermissionError` writing to `~/.tokenmaxxxer/trusted-repo-config.json` —
this sandbox's write allowlist doesn't cover that path) before reaching
later tests alphabetically — confirmed this identical failure occurs on
the unmodified baseline too (observed verbatim before any edits this
session), so it predates and is unrelated to this change. I did not get
a full pass/fail count for every test after that point in a single
`python3 test_gates.py` run because of it; ad-hoc workarounds (writing a
skip-and-continue runner script outside the repo) were blocked by this
session's tool-approval gate (headless, no interactive approver
available) rather than by anything in the code. What I did confirm
directly: nothing in this change touches any function exercised by
tests other than the two named above (the diff is additive — new
functions, a new optional `closes_only` parameter defaulting to the old
behavior, 2 new CLI flags — no existing code path's behavior changed
for existing callers).

Real-environment check (issue #245 requirement 3, "실물... 확인"):
ran `python3 gates/ci.py . --pr 257 --issue 245 --phase phase1
--closes-only` and `python3 gates/ci.py . --pr 257 --autodetect
--closes-only` against the actual PR #257 and issue #245 over a real
network connection (real `gh pr view`/`gh issue view`) — both pass
(`게이트 통과`), confirming the autodetect pipeline correctly reads
PR #257's real head branch (`issue-245/implementation` -> issue 245) and
real body (no closing keyword -> phase1) end-to-end. Separately, with
only `pr_reference._pr_view` monkeypatched (so `gh issue view 245` still
hit the real API and read issue #245's actual, live, currently-incomplete
plan — both plan steps unchecked), confirmed a synthetic phase-2 PR body
claiming `Closes #245` is blocked
(`계획에 미완 스텝이 남아 있다...`) and a synthetic phase-1 PR body with
an errant `Closes #245` is blocked by the new mismatch check
(`phase-1 제안 PR 본문에 closing 키워드(Closes)가 있다...`). This
confirms the wiring blocks both dangerous real-world shapes against this
issue's own real, live plan state. Not done: an actual GitHub Actions
run or a live required-status-check UI block, since that needs branch
protection active (deferred, see above) and/or a real throwaway PR
(deferred to the human's post-activation regression check, also above).

## Hunt

Stance: **assume-incomplete-coverage** (rotated — issue-223's record
states its own hunt used adversarial-self and that adversarial-self was
then the least-recently-used of {adversarial-self, assume-incomplete-
coverage, assume-broken, composition-regression}, implying the recency
order at that point was assume-broken (216/218/235/236, most recent) >
composition-regression (221/222) > assume-incomplete-coverage
(220/232) > adversarial-self (229, then LRU, used by 223). With
adversarial-self now used again by 223, assume-incomplete-coverage
becomes the new LRU). No registered `warrant-hunter` subagent type is
available in this harness (same gap issue-223 and earlier records note)
— `general-purpose` dispatched in its place with an explicit
assume-incomplete-coverage brief (assume the tests/design have untried
inputs, go find them). Dispatched foreground (synchronous) against the
uncommitted diff before delivery.

Findings:

1. **CONFIRMED, fixed.** `_phase_from_body`/`_phase1_mismatch` used
   `_CLOSES_REF.search()` (first match only) instead of scanning all
   matches — a body mentioning an unrelated issue's closing keyword
   before the real one (`"Fixes #999, ... Closes #245"`) blinded both
   functions to the actual `Closes #245` reference. Empirically
   reproduced by the hunter before I fixed it. Fixed via
   `_closes_ref_for_issue()` (`.finditer()`, first match *targeting the
   given issue*); 2 regression tests added; full suite re-run clean.
   See "What did not work".
2. **PLAUSIBLE, accepted, out of scope to fully close.** No atomic
   snapshot across the up-to-3 separate `gh pr view` body fetches within
   one `--autodetect --closes-only` run (autodetect's own fetch,
   `pr_reference.check`'s internal fetch, `_phase1_mismatch`'s fetch) —
   a body edited between fetches could produce an inconsistent read.
   Narrow window (each edit also independently re-triggers the workflow
   via the `edited` event type), and the *same class* of unsynchronized
   multi-fetch already exists in `pr_reference.check`'s frozen phase2
   path (body fetch, then a separate issue-body fetch) without ever
   being flagged as a defect in #228 — not treating this as a new
   correctness bar this issue must clear that the codebase doesn't
   already hold itself to elsewhere. See "Open findings" item 2.
3. **Checked, no fix needed.** No fenced/blockquote-blind gap beyond
   what phase2's already-tested sibling path has —
   `t_phase1_mismatch_matches_inside_fenced_quote` added to close the
   coverage gap the hunter flagged (behavior was already correct, just
   untested).
4. **Checked, no bug.** Hand-traced `main()`'s argv loop against the
   exact workflow invocation (`--pr "$PR_NUMBER" --autodetect
   --closes-only`) and the split-explicit-args case in
   `_autodetect_issue_phase` (one of `--issue`/`--phase` given, the
   other not) — both parse and branch correctly.
5. **Checked, no bug.** Workflow `permissions:` block
   (`contents/pull-requests/issues: read`) is sufficient for both
   `gh pr view` and `gh issue view` under the default `pull_request`
   (not `pull_request_target`) trigger's `GITHUB_TOKEN`.
