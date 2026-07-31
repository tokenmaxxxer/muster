---
kind: report
date: 2026-07-31
subject: issue-155
role: coding
---

# current-state survey — issue-155

## Motivating incident (already on main)

`docs/issue-73/reports/coding.md` claimed commit `f1f93c0` deleted
`docs/superpowers/`; `git show f1f93c0 --stat` shows 7 files touched, 0
path removals. Nothing in the pipeline caught the mismatch —
`gates/gates.py` has `record_wellformed`, `record_no_tool_residue`, and
`record_enums`, none of which read record *content* against the commit
diff. Fixed after the fact by `docs/issue-145/reports/coding.md`, which
also filed this issue's request as its own out-of-scope item.

## What exists today (`gates/gates.py`)

- `changed_files(work)` — union of committed (`origin/main...HEAD`) and
  working-tree changes, rename-aware, `-z`-safe. This already gives
  per-path presence; it does not currently expose the `git diff
  --name-status` **status letter** (A/M/D/R/C) to callers — `writeset()`
  etc. only need "was this path touched at all."
- `_committed_changes()` reads `--name-status -z` internally and already
  parses rename pairs (`R100\0old\0new`), so the status letter is present
  in the raw subprocess output but discarded before it reaches
  `changed_files()`.
- `_write_scope_overrides()` / `writeset()` already parse a `- write:
  <value>` line convention out of markdown bodies with a plain regex —
  this is the precedent for a low-parse-cost, line-scoped marker.
- `RECORD_PATH` / `record_frontmatter()` / `_changed_records()` already
  locate and read changed `docs/issue-<n>/reports/<role>.md` files each
  gate run — a new gate reuses this, not a new file-discovery path.
- `ALL` registry + `check(names, d, cfg)` is the extension point; a new
  gate is one function added to `ALL`.

## Record claim types found in the wild (this repo's records)

Surveying `docs/issue-73/reports/coding.md`, `docs/issue-145/reports/coding.md`,
`docs/issue-153/reports/coding.md` for the shape of "What was done" prose,
claims fall into:

1. **File deleted** ("삭제했다", "removed") — diff-checkable: path must
   show status `D` (or `R` as the old side) in `changed_files`' underlying
   `--name-status` output.
2. **File created** ("작성했다", "new file") — diff-checkable: path must
   show status `A`.
3. **File moved/renamed** — diff-checkable: `R<score>` with both old and
   new path present.
4. **Content added inside an existing file** ("X 함수를 추가했다") —
   diff-checkable only as "path was modified" (`M`); claiming a specific
   symbol/line inside the file is not diff-comparable without re-parsing
   the file, which is out of this issue's scope per its own instruction
   not to parse natural language broadly.
5. **Test run / command executed** ("테스트를 돌렸다", "빌드 확인함") —
   **not diff-checkable at all**: a diff shows file state, not process
   execution. Verifying this needs a captured log/exit-code artifact, a
   different mechanism than commit-diff comparison. Out of scope for this
   gate; flagged as a known gap below.
6. **Gate/finding closure** ("closed_checks:") — already structured
   (`code_sha:` field per issue-145's record above) but not currently
   cross-checked against the actual current SHA. Related but a separate
   concern from file-mutation claims; not this issue's stated scope
   (issue text names "파일 삭제/생성/이동 주장, 테스트 실행 주장").

## Machine-checkable subset (this issue's target)

Only claim types 1–3 are directly comparable to a `git diff
--name-status` line with no additional evidence-capture mechanism. Type 5
(test execution) needs a fundamentally different verification input (a
log/exit-code, not a diff) and is out of scope for a diff-comparison gate
— recorded here as a gap, not silently dropped, per the issue's request
for a side-effect analysis.

## Unknowns going into the proposal
- Whether unmarked prose claims should be rejected (forbid) or merely
  left unchecked (warn/no-op) — issue #155 item 3 asks this explicitly;
  addressed in the proposal's side-effect analysis section.
- Marker placement: body line (like `- write:`) vs. a frontmatter list
  field (like `record_fields` enums) — frontmatter fields are enum-only
  today (`record_enums`); a per-claim list is a different shape and fits
  the body-line convention better (arbitrary path values, not a closed
  enum).
