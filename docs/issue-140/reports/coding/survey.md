# issue-140 — phase 1: current-state survey

subject: issue-140 (role catalogue upkeep — remove routing residue, sharpen
boundary wording)

## Write set (projected)

- `roles/coding.json`, `roles/feasibility.json`, `roles/ops.json`,
  `roles/product.json`, `roles/qa.json`, `roles/reflect.json`,
  `roles/review.json`, `roles/ux-design.json`, `roles/verify.json` —
  wording-only edits to `produces`/`use_when`/`decides`. No schema change:
  `record_fields`, `marketplace`, `repo`, `path`, `sandbox` keys untouched.
- No new file, no new dependency, no env var, no migration.

## Per-file findings (routing/wake residue, ambiguous wording)

1. **`roles/ux-design.json`** — `produces`: `"screen/flow/wireframe 스펙
   (reviewed 가 coding 을 깨운다)"`. This is routing prose: it names which
   role wakes next off which `loop_state` value. This is the exact residue
   issue #140 reports — the #120 wake-removal sweep (`test_vocab_coherence.py`,
   `wakes.py`, `docs/specs/wake-routing.md` deleted; see
   `docs/issue-120/reports/coding.md`) covered rulebook/spec prose but never
   touched `roles/*.json`. **Action: delete the parenthetical**, keep only
   what the artifact is (screen/flow/wireframe spec).

2. **`roles/coding.json`, `roles/feasibility.json`, `roles/ops.json`,
   `roles/product.json`, `roles/reflect.json`** — no routing/wake vocabulary
   found (no "깨운다", "wakes", next-role naming, or loop-table references).
   `record_fields.loop_state` enums are state labels, not routing — a role
   naming its own states is not "who runs next", so these are in bounds and
   left alone content-wise.

3. **Verification-trio boundary (`qa.json` / `review.json` / `verify.json`)**
   — the issue asks that these three's `use_when` distinguish qa=실행 관찰,
   review=명세 대비 감사, verify=적대적 독립 재현 from each other. Current
   text:
   - `qa.use_when`: "실행 가능한 산출물이 랜딩됐을 때. 실행 없는 판정 금지,
     고치지 않음" — already scoped to execution-observation, but doesn't say
     *why* it's not verify's job when execution results are in dispute.
   - `review.use_when`: "coding 커밋이 랜딩됐고 요구사항 대비 감사가
     필요할 때. 빌더 의도는 안 읽는다" — scoped to spec-vs-artifact audit,
     already distinct from qa/verify in subject matter (spec compliance,
     not runtime behavior).
   - `verify.use_when`: "주장을 눈으로 검증할 수 없을 때(실행 결과 주장,
     복잡한 변경). coding·qa·review 가 놓친 것을 적대적으로 찾는다" —
     the parenthetical "(실행 결과 주장, ...)" overlaps qa's execution-result
     territory in wording, without stating the actual trigger difference
     (qa can observe directly; verify is called when direct observation
     alone can't settle the claim, e.g. a contested/expensive/hard-to-repro
     result). This is the ambiguity issue #140 flags: the boundary is
     substantively already correct in scope, but the wording doesn't make
     the three mutually exclusive on its face.
   **Action**: reword `verify.use_when` to state the trigger relative to
   qa/review's own observation, not just "can't verify with eyes" — e.g.
   distinguish "결과를 직접 관찰(qa)/명세 대조(review)로 결론낼 수 없을
   때" so a reader doesn't need outside context to see why verify differs.
   No substantive/behavioral change — wording only, per issue scope.

4. **Other role fields checked for vagueness**: `feasibility.use_when`,
   `product.use_when`, `ops.use_when` name their own triggers (risk
   presence, hypothesis-stage requirement, deploy/incident timing)
   without referencing another role's wake condition — no routing residue.

## Vocab-sweep gap (issue #140's item 3)

- `grep -rli "roles/"` in `test_gates.py`/`test_spawn.py` shows only
  path-existence and directory-shape checks (`test_gates.py:363-468`,
  `test_spawn.py:369`, `spawn.py:194`) — none inspect the JSON *content*
  (`decides`/`use_when`/`produces` strings) for vocabulary.
- `test_vocab_coherence.py` (the #120-era vocab test) was deleted outright
  in #120, not narrowed — per `docs/issue-120/reports/coding.md` item 1, it
  was one of four files removed because it tested the wake-routing table
  itself, which no longer exists. It never covered `roles/*.json` content
  even before deletion (confirmed: `roles/` has no historical entry in that
  deleted test's coverage per the #120 record's own file list).
- **Conclusion for the gap question**: the #120 sweep missed `roles/*.json`
  because that sweep's own scope was the wake-routing *mechanism*
  (`wakes.py` and its direct consumers), not a vocabulary-coherence pass
  over every role-describing file in the repo; `roles/*.json` was never in
  either sweep's grep target list.
- Whether a `test_vocab_coherence`-style check should now cover `roles/`
  content is a decision, not a survey fact — carried into the proposal.

## Scout-skip record

Skipping external scouting for this issue. Reason: this is an internal
documentation/vocabulary-consistency edit within an existing role catalogue
schema — there is no external product category or comparable system to
benchmark wording against, and the spec (issue #140 itself) already names
the exact three actions required (strip routing prose, sharpen the
verification-trio wording, decide on test coverage). Internal precedent
(`docs/issue-120/reports/coding.md`, `protocol.md`) was read directly
instead, as noted above.
