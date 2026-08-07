# Survey — issue #377 (stale self-description)

## Existing precedent checked

- `gates/gates.py::record_fulfils_diff` (line ~411): opt-in marker shape —
  a `fulfils: delete|create|move <path>` line in a phase-2 record is
  mechanically checked against the commit's actual diff. Scope is narrow:
  file-operation claims inside phase-2 records only. Does not read prose
  in code comments/docstrings/role JSON, so it does not already cover
  #377's four instances. Its *shape* (marker → paired mechanical check,
  opt-in, unmatched prose untouched) is the right precedent to reuse.
- #330 (reach check): impact analysis for *code* reach (what a change
  touches elsewhere), not for verifying that a prose claim about
  behaviour is still true. No overlap in mechanism found; #330 has not
  landed a reach-check artifact yet to extend.
- #333 (derived-numbers): requires numbers in records to be computed, not
  asserted — same *principle* (claim must be backed by a run, not typed
  by hand) applied to a different surface (numeric fields in records vs.
  free prose in comments/docstrings). No shared code path to extend;
  noting the principle-level kinship only.

## The four instances, re-verified against current tree (not just the issue text)

1. **`.github/workflows/plan-aware-closes-gate.yml`** (comment above the
   `checkout gate script from main` step): still present verbatim —
   "closes-only 모드는 PR의 파일 diff를 전혀 보지 않고 ... 메타데이터만
   읽으므로, PR의 코드 변경분을 체크아웃할 필요 자체가 없다." Traced the
   actual `closes_only=True` path in `gates/ci.py::check()` (lines
   291-347): it calls `_phase2_record_evidence()` (line 169), added by
   #284, which does `record_path = repo / f"docs/issue-{issue}/reports/
   {role}.md"` and `record_path.read_text(...)` — a filesystem read
   inside the checked-out tree. The claim "PR의 파일 diff를 전혀 보지
   않는다" is mixed: the *no-checkout-of-PR-code* half still holds
   (`ref: main` is unchanged and `_phase2_record_evidence` only reads
   paths under the pinned `main` checkout, never the PR branch), but the
   *only reads gh metadata* half is now false — it also reads a local
   file. Mixed claim, exactly the shape the issue calls out.
2. **`roster_watchdog` docstring** (`spawn.py:1545`): describes a polling
   discipline #325 was filed to make real. This is a promise about
   future behaviour, not a checkable property of current code — the
   issue itself says prose cannot be the fix here. Out of mechanical
   reach by design; confirmed by reading #325 is still open.
3. **`roles/implementation.json`** line 20: `"loop_state": ["scope-
   proposed", "scope-approved", "in-progress", "landed"]`. Confirmed by
   grep that no record on disk uses any of those four values;
   `_phase2_record_evidence`'s own docstring (line 174) names
   `phase-2-complete` as a real value the enum doesn't list. Cleanly
   checkable: declared enum vs. actual `loop_state` values found in
   `docs/issue-*/reports/*.md` frontmatter (parseable via the existing
   `gates.record_frontmatter` helper).
4. **`gates/gates.py::writeset()`** docstring (line 172): "spec 이
   선언한 write-set 준수" in the present tense. Confirmed by `find` that
   no `spec.md` exists anywhere in the tree, and by grep that no code
   writes one — only `gates/gates.py`, `gates/ci.py`, and
   `test_gates.py` even mention the filename, all as *readers*. The
   docstring's premise (a spec-producing stage exists) is checkable as
   "is there any producer of `spec.md` in the repo" — currently false.

## What this means for scope

Two of four (#3, #4) are cleanly checkable today with a small, generic
marker-based mechanism in `record_fulfils_diff`'s shape. One (#2) is
explicitly out of mechanical reach — the issue itself rules out
"strengthen the prose" as a fix, and no code-level check can verify a
docstring's promise about a component that has not yet built the
discipline it describes (that is #325's job, not #377's). One (#1) is a
mixed claim; the proposal below marks and checks only its checkable
half, leaving the trust-boundary intent sentence untouched in prose, per
the issue's own instruction not to force intent claims into a test.
