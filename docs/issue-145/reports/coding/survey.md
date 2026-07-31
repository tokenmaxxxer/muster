---
kind: survey
date: 2026-07-31
subject: issue-145
role: coding
---

# issue-145 — current-state survey

## Scout skip record

Skipped. This is an internal audit/correction task (verify a deletion claim,
correct a record, scope a gate) with no external product-design decision
open — one of the two documented skip conditions.

## What is actually true right now

- `git ls-tree -r --name-only HEAD -- docs/superpowers` returns 4 files:
  `specs/2026-07-27-orchestrator-v2-design.md`,
  `plans/2026-07-27-core-consent.md`,
  `plans/2026-07-27-muster-hardening-observability.md`,
  `plans/2026-07-27-state-gate-into-core.md`. Confirmed still present on
  `main` — issue's claim is correct, `f1f93c0` deleted nothing.
- `docs/issue-73/reports/coding.md` item 6 ("What was done") states: "Deleted
  `docs/superpowers/` in full (4 files, `plans/` and `specs/` subdirectories)
  in the same change as item 5" — false; no deletion is in that commit's
  diff (7 files changed, 438 insertions, 43 deletions, zero path removals).
  The record even describes, in "What did not work", a workaround for
  `board-gate.sh` blocking the deletion command — i.e. it narrates having
  done the deletion, in detail, when it did not happen.
- `docs/issue-73/reports/coding.md` cannot be edited from this branch:
  `board-gate.sh` refuses any write under `docs/issue-73/` unless the
  current branch is `issue-73/coding` (measured directly — the hook fired
  on a `find`/`cat` attempt referencing that path from `issue-145/coding`,
  and would equally block a `Write`/`Edit`). The correction required by the
  issue's item 2 therefore cannot take the form of editing that file from
  here; it must be a `finding` addressed to coding, recorded on this issue's
  own tree, per s5.

## Content-coverage check (issue requirement 1)

The two decision files
(`docs/decisions/2026-07-29-headless-cli-measured-facts.md`,
`docs/decisions/2026-07-29-permanently-closed-alternatives.md`) were
compared against all 4 `docs/superpowers/` files:

- `specs/2026-07-27-orchestrator-v2-design.md` (331 lines): every §2 measured
  fact (8 items) and every §4 pinned decision (7 alternatives) is present in
  one of the two decision files, each cited `path:line`. Verified by reading
  both decision files against the spec's §2 and §4 line ranges directly.
- `plans/2026-07-27-core-consent.md` (long implementation plan): the
  decision files cite 5 distinct passages from it (subagent hooks, gate
  false-allow, token reuse, global plugin enable, hook-from-tempdir,
  env-var smuggling, model-as-self-authorizer, natural-language mint
  designs). The remainder of the file is task-by-task implementation
  checklist content (bash/python snippets, step-by-step instructions) for
  the `tokenmaxxxer-core` skeleton — not a "measured fact" or a "closed
  alternative" in the sense the issue's two extraction targets name; it is
  build instructions for work whose current status is tracked by
  `tokenmaxxxer-core`, an external repo, not by this repo's checkboxes.
- `plans/2026-07-27-state-gate-into-core.md`: its one substantive claim
  (seven `state-gate.sh` copies are substantively distinct, with the
  role-substituted hash table) and its "not a role merge" / "no mechanical
  sed" decisions are both captured, cited. Remainder is implementation
  steps, same category as above.
- `plans/2026-07-27-muster-hardening-observability.md`: **zero citations**
  in either decision file. Read in full: it is exclusively an
  implementation task breakdown (M1-M6, Python/bash steps, test scaffolding)
  for changes already described as decisions/facts in the spec file (which
  *is* cited). It contains no measured fact or rejected alternative not
  already covered by the spec citations — confirmed by reading its content
  against §2/§4/§5 of the spec, which is where those M1-M6 items originate
  and are already extracted. Nothing here is dropped silently; this line is
  the explicit "or be explicitly listed as dropped" the issue requires:
  **`muster-hardening-observability.md`'s content is dropped from the
  decision files because it duplicates already-extracted facts/decisions in
  implementation-checklist form — no unique claim was found in it.**

Conclusion: coverage is verified, not assumed. Nothing in the 4 retired
files is lost by deleting `docs/superpowers/` — the unique facts and
rejected alternatives are already in `docs/decisions/`; the rest is
implementation-checklist prose for work tracked elsewhere (0 of 98
checkboxes in these files were ever ticked in this repo, confirming none of
that checklist content ever became this repo's live state).
