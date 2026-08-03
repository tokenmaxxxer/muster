---
kind: decision
date: 2026-08-03
status: landed
subject: issue-228
---

# `check_body` gains a `plan` parameter — plan-aware phase-2 Closes gate

## Decision

`gates/pr_reference.py:check_body(issue, body, phase)` gains a fourth,
optional parameter: `check_body(issue, body, phase, plan=None)`. The
default preserves every existing call site and all four pre-existing
tests unchanged. `gates/pr_reference.py:check(...)` now fetches the
**issue** body (new `_issue_view_body`, mirroring `_pr_view`) and parses
it with `gates/flows.py:_plan_from_body` whenever `phase == "phase2"`,
passing the result as `plan`.

When `plan` is given and has more than one incomplete step, or has
exactly one incomplete step that is not the plan's last step,
`check_body` now **blocks** a `Closes/Fixes/Resolves #<issue>` citation
instead of requiring it — the closing keyword is only required (existing
behavior, unchanged) when the plan has no incomplete steps or when its
one incomplete step is the last one.

## Why (adopted 1 — incomplete-step-count judgment, no role matching)

`incomplete = [s for s in plan if not s["done"]]`; require Closes when
`incomplete` is empty or its one member is `max(step)`, block otherwise.

**Rejected alternative**: match the PR's head-branch role (the
`ci.py:_pr_head_ref` + `gates.role_scope` pattern) against the plan to
identify exactly which step this PR delivers, then require completion of
every *other* step. Rejected because this repo's own issue-197 is a real
counter-example to checkbox trust: it is closed, yet its step 1
(`implementation`) is still `[ ]` while the later step 2
(`execution-observation`) is `[x]` — an out-of-order, stale checkbox left
over from authoring. Precise role-matching would not fix this authoring
gap either, at the cost of a new parameter and a wider `ci.py` ->
`pr_reference.check()` signature. The adopted incomplete-count judgment
instead fails toward *blocking* in this same scenario (over-blocking
step 2, safe), matching this file's existing fail-closed convention
(`pr_reference.py`'s "검사 불가는 통과가 아니다", `ci.py`'s "fail
closed") — and issue-228 itself states closing is still a human's call,
so the cost of an extra confirmation is low. Verified this session
against all 11 of this repo's live multi-step issues (`## 실행 계획`
present): the judgment's answer matches every one's actual state.

## Why (adopted 2 — folding the `gates/ci.py` `--phase` defect into this issue)

`gates/ci.py:check()` gained `phase: str | None = None` (was
`phase: str = "phase1"`); when `pr`/`issue` are both given but `phase` is
omitted, it now blocks with an explicit reason instead of silently
falling back to `"phase1"`. `main()`'s `opts.get("phase", "phase1")`
became `opts.get("phase")` to match.

**Rejected alternative**: leave `ci.py` out of scope and fix only the
`check_body` judgment. Rejected because the exact phase-2 blocking logic
this issue adds only runs when a caller passes `--phase phase2`
explicitly — confirmed this session that no call site in this repo's
history ever has. Leaving the default in place would land dead code: the
same failure class this issue fixes (a documented contract a machine
silently fails to enforce) would simply move one door over.

## Why (adopted 3 — no new plain-`#issue` fallback when blocking)

When a plan is incomplete and closing keywords are blocked, `check_body`
does not additionally require a plain `#issue` reference as a fallback.

**Rejected alternative**: require a plain reference (as phase-1 PRs do)
so traceability isn't lost. Rejected as scope creep — issue-228's
requirement 1 says only "require 대신 차단," and a new reference
requirement wasn't asked for; if wanted, it is a separate issue.

## Unchanged by this decision

- `_CLOSES_REF`'s fence-oblivious matching (`re.search` over the raw
  body, no code-fence skip) stays exactly as-is — GitHub itself parses
  closing keywords inside fenced text, so the gate must not skip fenced
  content when hunting for a real one (verified empirically this
  session: a fenced `Closes #999` line still matches `_CLOSES_REF`).
- `gates/flows.py:_plan_from_body` — reused unmodified (issue-228
  requirement 4).
- phase-1 PR rules (plain `#N` required, `Closes` forbidden) — untouched
  per issue-228's own stated constraint.
