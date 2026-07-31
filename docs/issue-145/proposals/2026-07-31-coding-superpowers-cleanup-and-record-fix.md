---
kind: proposal
date: 2026-07-31
subject: issue-145
role: coding
---

# issue-145 — delete docs/superpowers/, correct the false deletion claim

files: docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md (delete),
docs/superpowers/plans/2026-07-27-core-consent.md (delete),
docs/superpowers/plans/2026-07-27-muster-hardening-observability.md (delete),
docs/superpowers/plans/2026-07-27-state-gate-into-core.md (delete),
docs/issue-145/reports/coding.md (phase-2 record, includes the s5 finding
addressed to coding about issue-73's record)

## Request (paraphrased intent, secrets stripped)

`docs/issue-73/reports/coding.md` claims `f1f93c0` deleted
`docs/superpowers/`; it did not — the directory (4 files, ~3,282 lines, 0/98
checkboxes ticked) is still on `main`. Finish the deletion the old record
falsely claimed, verify nothing is lost first, and correct the record so it
stops asserting a deletion that never happened.

## Constraints

- `docs/issue-73/reports/coding.md` cannot be edited from this branch —
  `board-gate.sh` refuses any write under `docs/issue-73/` unless the
  current branch is `issue-73/coding` (measured in this session). The
  correction is therefore a `finding` per s5, addressed to coding, recorded
  in this issue's own tree — not a direct edit of the old file.
- Item 3 of the issue (a gate checking that a phase-2 record's per-clause
  fulfilment markers correspond to the commit) is explicitly scoped by the
  issue itself to "its own proposal" — out of scope here. This proposal
  only files the follow-up (see Out of scope).

## What will be done

1. Delete `docs/superpowers/` in full (the 4 files listed above). Coverage
   of their content by `docs/decisions/2026-07-29-*.md` is already verified
   in `docs/issue-145/reports/coding/survey.md` — nothing new to check
   before deleting.
2. Write `docs/issue-145/reports/coding.md` (the phase-2 record) containing
   a `finding` (s5, addressed to coding) stating: `docs/issue-73/reports/
   coding.md`'s item 6 claims a deletion `f1f93c0` did not perform, and its
   "What did not work" section narrates a `board-gate.sh` workaround for a
   deletion that never happened. The finding states the correction in
   place of editing the unreachable file: the deletion issue-73 claimed is
   actually delivered by this issue's commit, not `f1f93c0`.
3. File a new GitHub issue for item 3 (the per-clause-fulfilment gate),
   referencing #145, since it is out of scope for this proposal's write set
   per the issue's own instruction.

## Out of scope

- Editing `docs/issue-73/reports/coding.md` directly (blocked by
  `board-gate.sh` from this branch).
- Building the per-clause-fulfilment gate itself (issue item 3) — filed as
  a separate issue instead.

## How you'll know it worked

- `git ls-tree -r --name-only HEAD -- docs/superpowers` → empty, on the
  merged commit.
- `docs/issue-145/reports/coding.md` contains the finding and cites
  `f1f93c0`'s actual diff (no deletions) as evidence.
- A new issue exists for the item-3 gate, referenced from this PR/issue.
