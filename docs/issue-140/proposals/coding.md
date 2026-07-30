---
kind: build-proposal
subject: issue-140
---

# issue-140 — phase 1: build proposal

References: #140

## Request (paraphrased)

`roles/ux-design.json` still describes routing ("reviewed 가 coding 을
깨운다" — who wakes next) even though the #120 wake-removal sweep deleted
the routing mechanism itself. Sweep every `roles/*.json` (9 files) for the
same residue, tighten `decides`/`use_when`/`produces` wording so the
verification trio (qa/review/verify) reads as mutually exclusive, and
decide whether a vocab-coherence check should now cover `roles/` content.

## Constraints

- Wording only — no role's actual authority, `record_fields` schema,
  `marketplace`/`repo`/`path`/`sandbox` keys, or behavior changes.
- No new routing/wake mechanism introduced anywhere as a "fix" — the
  point is removing routing prose, not replacing it with different
  routing prose.
- Stay inside `roles/*.json` plus (if item 3 below is adopted) one new
  small test file and its wiring; no other repo area touches.

## What will be done

1. `roles/ux-design.json`: change `produces` from
   `"screen/flow/wireframe 스펙 (reviewed 가 coding 을 깨운다)"` to
   `"screen/flow/wireframe 스펙"` — drop the routing parenthetical
   entirely, per survey finding 1.
2. `roles/verify.json`: reword `use_when` so the verification trio is
   mutually exclusive on its face, without changing verify's actual
   trigger condition:
   from `"주장을 눈으로 검증할 수 없을 때(실행 결과 주장, 복잡한 변경).
   coding·qa·review 가 놓친 것을 적대적으로 찾는다"`
   to `"결과를 직접 관찰(qa)이나 명세 대조(review)만으로 결론낼 수 없을
   때 — 재현이 어렵거나 다투는 실행 결과 주장, 복잡한 변경. coding·qa·
   review 가 놓친 것을 적대적 독립 재현으로 찾는다"`.
   `qa.json`/`review.json` `use_when` text is left as-is — survey finding
   3 found their scope already distinct (execution-observation vs.
   spec-audit); only verify's wording needed the explicit cross-reference
   to read as non-overlapping.
3. The other 7 files (`coding.json`, `feasibility.json`, `ops.json`,
   `product.json`, `qa.json`, `reflect.json`, `review.json`) get no
   content edit — survey found no routing residue and no ambiguity
   needing a wording fix in them.
4. Add `test_vocab_coherence_roles.py`: a small standalone test asserting
   no `roles/*.json` `decides`/`use_when`/`produces` string contains
   routing/wake vocabulary (`"깨운"`, `"wake"`, `"라우팅"`, or a literal
   other-role name paired with a trigger verb) — a narrow regression guard
   so this residue class doesn't recur silently, answering the issue's
   item 3 question in the affirmative but scoped minimally (new small
   test file, not folding into deleted #120 machinery).

## Out of scope

- `protocol.md`/`protocol.ko.md` wake-adjacent canon lines — flagged
  already in #120's record as belonging to whoever owns protocol canon;
  untouched here too.
- Any change to role authority, sandbox config, or `record_fields` enums.
- Re-adding any wake/routing table — explicitly the opposite of this
  issue's intent.

## How it'll be verified (phase 2 self-check)

- `python3 -m json.tool roles/*.json` (or equivalent) — both edited files
  stay valid JSON.
- `grep -rn "깨운\|wakes\|wake" roles/` — zero hits after the edit.
- `python3 -m pytest test_vocab_coherence_roles.py` — new test passes;
  also run against the pre-edit `ux-design.json` mentally/via a quick
  git-stash check to confirm it would have caught the original residue.
