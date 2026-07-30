---
kind: coding-record
subject: issue-140
code_under_review: HEAD
loop_state: landed
---

# issue-140 — phase 2: coding record

References: #140. Approved via `APPROVE issue-140/coding` (single-account mode).

## Why

Issue #140: `roles/ux-design.json` still carried routing prose
("reviewed 가 coding 을 깨운다") though #120 deleted the wake-routing
mechanism itself; other `roles/*.json` files needed the same sweep, and
the qa/review/verify trio's `use_when` wording needed sharpening so the
three read as mutually exclusive on their face.

## Upstream basis

- Approved proposal: `docs/issue-140/proposals/coding.md`.
- Current-state survey: `docs/issue-140/reports/coding/survey.md`.
- Prior precedent: `docs/issue-120/reports/coding.md` (wake-routing
  mechanism deletion that this residue sweep completes).

## What was done

1. `roles/ux-design.json`: `produces` routing parenthetical
   `"(reviewed 가 coding 을 깨운다)"` removed — now
   `"screen/flow/wireframe 스펙"`.
2. `roles/verify.json`: `use_when` reworded to state the trigger relative
   to qa/review's own observation instead of a bare "can't verify with
   eyes" — new text: `"결과를 직접 관찰(qa)이나 명세 대조(review)만으로
   결론낼 수 없을 때 — 재현이 어렵거나 다투는 실행 결과 주장, 복잡한
   변경. coding·qa·review 가 놓친 것을 적대적 독립 재현으로 찾는다"`.
   No change to `decides`/`produces`/`record_fields`.
3. Other 7 `roles/*.json` files: no content edit (per proposal item 3 —
   survey found no residue/ambiguity in them).
4. Added `test_vocab_coherence_roles.py`: standalone pytest asserting no
   `roles/*.json` `decides`/`use_when`/`produces` string contains
   routing/wake vocabulary (`깨운`, `wakes`/`wake`, `라우팅`).

## Verification run (self-check, not a review pass)

- `python3 -m json.tool roles/ux-design.json roles/verify.json` — both
  valid JSON.
- `grep -rn "깨운\|wakes" roles/` — zero hits after edit.
- `python3 -m pytest test_vocab_coherence_roles.py -q` — passed (1 test).

## What did not work

(none)

## closed_checks

- routing-residue-removed: grep-confirmed zero `깨운`/`wakes` hits across
  `roles/*.json` post-edit. code_sha: (this commit).
- new-test-passes: `test_vocab_coherence_roles.py` passes against current
  `roles/*.json`. code_sha: (this commit).

## Hunt

warrant-hunter dispatched pre-completion; see below.

## Open Findings

None outstanding.
