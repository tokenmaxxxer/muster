# Issue #80 — Coding Record

loop_state: landed
code_under_review: 783a739 + phase-2 commit (this record's commit)
subject: issue-80
approval: single-account mode, PR #81 author JiwonJung94 == approvers.md entry; phase-2 execution per role-handoff contract v3 s19.

## Why

Follow-up to `docs/issue-76/reports/reflect.md` §1a/§1b (backlog item 1): two zero-cite
approval-string restatement sites drift from the contract independently (the core#18 incident
showed citation-plus-restated-prose still drifts), so 1a adds the missing `(contract v3 s19)`
citations and 1b removes the restated rule prose from the informing hook, replacing it with a
pointer to the authoritative site.

## What was done

Executed the approved proposal (`docs/issue-80/proposals/coding.md`) exactly:

- `orchestrate/hooks/directive.sh:71-79` — replaced the restated approval/acceptance/refusal
  comment-form prose with a pointer to `/orchestrate:run` step 6 `(contract v3 s19)`. The
  literal string `APPROVE issue-<n>/<role>` no longer appears in this file — nothing left to
  drift out of sync with the authoritative source (per the core#18 incident this issue follows
  up on).
- `orchestrate/commands/run.md:187` — added `(contract v3 s19)` immediately after the existing
  approval-comment instruction. Instruction text (the `gh pr comment ... "APPROVE issue-<n>/<역할>"`
  command form) left verbatim, per the proposal's constraint that this is the authoritative detail
  site directive.sh's pointer sends readers to.

Write set matched the frozen proposal exactly: only these two files touched, no `core/` path.

## Verification (closed_checks)

- `grep -n 'APPROVE issue-<n>' orchestrate/hooks/directive.sh` → no match (confirms 1a: string no
  longer restated at the informing-hook site).
- `git diff --stat` → only `orchestrate/hooks/directive.sh` and `orchestrate/commands/run.md`
  changed; no `core/` path touched.
- Manual read of both diffs against the proposal's "Proposed replacement" / "Proposed" blocks:
  wording matches verbatim.

## What did not work

(none — proposal wording applied directly without deviation)

## Open findings

None outstanding. Carried-forward, out-of-scope items from the proposal (not this record's
findings, no action needed here):
- Filing a core-repo issue for `core/hooks/directive.sh`'s analogous drift.
- Sharpening `run.md:11`'s generic `(contract v3)` cite to a section number.
- Consolidating `run.md`'s other accreted obligations (reflect.md §2).
