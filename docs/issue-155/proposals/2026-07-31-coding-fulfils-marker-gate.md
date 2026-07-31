---
kind: proposal
date: 2026-07-31
subject: issue-155
role: coding
---

# proposal — fulfilment-claim gate (issue #155)

files:
- write: gates/gates.py
- write: test_gates.py
- write: docs/handbooks/*.md (if a record-authoring handbook page names
  the marker syntax; only if one already exists — see "Out of scope")

## Request (paraphrased)

A phase-2 record can claim it did something (e.g. "deleted X") that its
own commit diff does not actually contain, and nothing today catches
the mismatch (this happened once, on `docs/issue-73/reports/coding.md`).
Add a gate that checks the machine-checkable subset of a record's
fulfilment claims — file deletion/creation/move — against the PR's real
commit diff, and reject the PR when they disagree.

## Constraints

- No LLM/NLP parsing of record prose (`gates/gates.py`'s stated
  principle: "결정론적, LLM 0회"; issue text: "자연어 전부를 파싱하려
  들지 말 것").
- Fail closed on ambiguity, matching every existing gate in this file
  (unparseable → block, not pass).
- Reuse existing primitives: `changed_files`/`_committed_changes`'s
  `--name-status` parsing, and the `- write: <value>` line-parsing
  convention `_write_scope_overrides` already established.
- Only phase-2 records (`docs/issue-<n>/reports/<role>.md`) carry
  fulfilment claims — phase-1 proposals/surveys make no delivery claims.

## What will be done

**1. Marker syntax** — a body line, one claim per line, inside the
record's `## What was done` prose or anywhere in the body (not
frontmatter — paths aren't a closed enum, so this isn't `record_enums`
territory):

```
fulfils: delete <path>
fulfils: create <path>
fulfils: move <old-path> -> <new-path>
```

Parsed with the same shallow per-line regex style as `- write: <value>`
(`^\s*[-*]?\s*fulfils:\s*(delete|create|move)\s+(.+)$`). No code fence
requirement, no frontmatter change.

**2. `_committed_changes()` gains an optional status-preserving mode** —
today it discards the `--name-status` status letter (A/M/D/R/C) after
using it only to detect renames. Add a sibling function
`_committed_changes_with_status(work) -> list[tuple[str, str, str|None]]`
(status, path, old_path-or-None for renames) so a new gate can read
status without duplicating the `-z` record-parsing loop. Existing
callers (`changed_files`, `_worktree_changes` consumers) are unchanged.

**3. New gate `record_fulfils_diff(d, cfg)`** in `gates/gates.py`,
registered in `ALL`:
- Locate changed records via the existing `_changed_records()` helper.
- For each, extract `fulfils:` lines with the regex above.
- For `delete <path>`: require a `D` status entry for `<path>`, or `<path>`
  appearing as the *old* side of an `R`/`C` entry — in either case
  "gone from the current tree under that name." Missing → blocking
  message naming the claim and the record.
- For `create <path>`: require an `A` status entry for `<path>` (or the
  *new* side of an `R`/`C` — a rename that lands at a genuinely new path
  is accepted as "created" for the purposes of this claim, since the
  path is new even though content moved).
- For `move <old> -> <new>`: require an `R`/`C` entry with exactly that
  old/new pair.
- A `fulfils:` line that doesn't parse (bad claim-type keyword, missing
  arrow on `move`) is a blocking error itself — same fail-closed stance
  as `dep_names()`'s "can't parse ≠ nothing to check."
- Records with zero `fulfils:` lines are not touched by this gate at
  all (see side-effect analysis below — this is the "warn vs forbid"
  answer).

**4. Tests in `test_gates.py`** mirroring the existing `record_enums`/
`record_wellformed` test shape: true-positive (claim matches diff,
passes), false-claim (claim absent from diff, blocked), rename cases,
unparseable claim line (blocked), record with no `fulfils:` lines
(passes, untouched).

## Side-effect analysis (issue #155 item 3, required)

**Burden on record-writing**: opt-in, additive. A record that never
writes a `fulfils:` line is invisible to this gate — exactly today's
behavior, zero new burden for records that only narrate ("What did not
work", investigation notes, etc.) with nothing diff-checkable to claim.
For a record that *does* claim a file mutation, the added cost is one
line per claim, in a syntax the codebase already trains authors on via
`- write:` in specs — not a new convention to learn from scratch.

**Unmarked natural-language claims — chosen: warn, not forbid.**
Forbidding unmarked prose (e.g. requiring every "deleted X" sentence to
carry a matching `fulfils:` line) would need NLP parsing of the record
body to *detect* unmarked claims in the first place — exactly what this
issue's own instruction rules out ("자연어 전부를 파싱하려 들지 말
것"). A gate that can't detect a claim can't consistently forbid it, and
inconsistent enforcement is worse than no enforcement (false confidence:
authors would believe *all* claims are checked once *any* are). So:
unmarked prose claims stay exactly as unverified as they are today — no
regression, no false promise of coverage. The gate's actual guarantee is
narrower and honest: "every `fulfils:` line in this record matches the
commit diff," not "every claim in this record is true." This narrowing
should be stated plainly wherever the marker syntax is documented, so
authors don't over-trust the gate's silence on unmarked prose.

**Test-execution claims — excluded**, per the survey: no diff-comparable
signal exists for "I ran the tests." Left as a documented gap, not
silently dropped.

## Out of scope

- Whether/where to document the `fulfils:` syntax for authors (a
  handbook page). No `docs/handbooks/` page currently documents record
  body conventions like `- write:` either, so adding one here would be
  scope creep beyond this issue's ask; flagged for a follow-up if the
  approver wants it in-line with phase 2.
- `closed_checks:`/`code_sha:` cross-checking (issue text scopes this
  issue to file-mutation and test-run claims, not check-closure
  bookkeeping — noted in the survey as a related-but-separate concern).
- Test-execution claim verification (needs a log/exit-code capture
  mechanism, not a diff-comparison gate — see side-effect analysis).

## How it'll be known to work

`test_gates.py::test_record_fulfils_diff_*` cases pass, including the
false-claim case reproducing issue #145's actual incident shape (a
record claims `delete docs/foo` while the commit diff contains no `D`
status for that path → gate blocks) and a true-claim case (gate passes).
