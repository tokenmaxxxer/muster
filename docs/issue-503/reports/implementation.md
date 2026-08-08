---
code_under_review: HEAD
loop_state: landed
---

# Implementation record — issue #503

## Summary of work

Delivered the approved phase-1 proposal
(`docs/issue-503/proposals/2026-08-08-streaming-per-unit-landing-norm.md`):

- `on-the-record/commands/run.md` — new "스트리밍 랜딩이 기본이다" subsection,
  placed next to the #407 per-PR-landing text and "병렬 스텝의 부분 반려",
  stating streaming per-unit landing (verify → merge → re-scan on each
  completion) is the structural default, with a batch barrier allowed
  only for a plan-named cross-unit dependency — applies to both the
  top-level coordinator loop and role sessions that fan out their own
  sub-work.
- `gates/test_boundary.py` — new `t_run_md_streaming_landing_is_default_norm`
  asserting the section exists and its body carries the disposition as
  contiguous affirmative phrases, not independent substrings anywhere in
  the section (see Closed checks / hunt below).
- `test_spawn.py` — new `StreamingLanding` test class: a green test
  proving `spawn.roster_reconcile()`'s existing per-entry loop acts on
  each unit as it arrives rather than after collecting all entries, a
  red-control test proving a naive collect-then-act harness fails the
  same interleaving assertion, and a static-source test pinning
  `roster_reconcile`'s per-entry-act shape.
- No `spawn.py` change: per the proposal's contingency clause, the
  fixture confirms `roster_reconcile` already streams (loops and acts
  in the same iteration), so no code fix was needed there.
- No separate "spec index" file was found beyond
  `docs/specs/enforcement-boundary.md` (already governed by
  `gates/test_boundary.py`, unrelated to this section); nothing else to
  regenerate — matches the survey's finding of no other spec-index
  mechanism.

## Why

Approved on the open PR #504 branch per the operator's phase-2-approved
directive (issue-503 phase 2: approved, 2026-08-08). See the proposal's
Rationale for the three alternatives considered and rejected (extending
#407's paragraph in place, a new standalone spec-index gate module,
pre-emptively editing spawn.py).

## Upstream basis

docs/issue-503/proposals/2026-08-08-streaming-per-unit-landing-norm.md

## Closed checks

- `python3 gates/test_boundary.py` — 13/13 passed, code_under_review: HEAD.
- `python3 test_spawn.py` — 292/292 passed, code_under_review: HEAD.
- before-landing warrant hunt, stance 0 (assume the gate just touched is
  bypassable), cap 120s, tier default:
  `docs/reports/2026-08-08-hunt-streaming-per-unit-landing-norm.md`.
  Verdict: FINDING — the gate's three independent substring checks
  ("배치 배리어", "기본이 아니다", "이름 붙인") passed even against a
  section body that explicitly argues *against* the streaming-default
  norm, as long as the three substrings appeared somewhere inside the
  negating prose. **Resolved**: rewrote the assertion to require two
  contiguous affirmative phrases
  ("완료한 단위마다 즉시 처리한다…배치 배리어는 기본이 아니다" and
  "배치 배리어는 예외적으로만 정당하다…이름 붙인 단위 간 실제 의존성")
  matched via regex with bounded gaps, mirroring exactly what the hunt's
  own "Expected" section named as the fix. Re-ran the hunt's reproduction
  script verbatim after the fix: the gate now fails on the injected
  negated text (confirmed manually — `disposition_re.search()` returns
  no match on the adversarial body) and passes on the real section.
  A materially narrower residual risk remains (an adversarial rebuttal
  reusing my exact clause wording word-for-word could still pass); this
  is out of scope for an internal contract-text presence gate and not
  the reported finding's shape.

## What did not work

- Running the hunt's reproduction script (which ends in
  `git checkout -- on-the-record/commands/run.md`) against the working
  tree twice reverted my own uncommitted `run.md` edit both times, since
  the edit was never yet committed when the script ran — expected: the
  repro script only touches run.md transiently and restores it; actual:
  "restore" meant "restore to last commit," which discarded my
  uncommitted section both times. Reapplied the edit after each run;
  no data lost, just redone. Lesson embedded in this record for any
  future re-read: commit before running any hunt reproduction script
  that ends in `git checkout --` on a file you have pending edits in.

## Open findings

None open — the one finding from the before-landing hunt is resolved
above (closed_checks entry) and the fix was re-verified against the
hunt's own reproduction script.

## Next steps

None — phase 2 complete. Commit, push, open PR against main with
`Closes #503`.

## Resolution path

N/A — no open findings.
