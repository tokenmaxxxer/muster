# Current-state survey — issue-115

## What exists

- **spawn.py CLI** (`spawn.py:1502-1592`, `main()`): flat `argparse`, dispatch via
  sequential `if a.role == "...":` on one positional `role` arg. `approve` is
  already a stub that refuses (`spawn.py:1580-1582`) with a message pointing at
  `gh pr review --approve` — that stub is about PR-level approval, not scope
  approval, and is untouched by this issue.
- **`init_board`** (`spawn.py:659-701`) is the closest existing pattern for a
  command that writes an infra file after a `gh api` call: reads `--login`,
  shells to `gh api user`, writes `docs/specs/approvers.md`.
- **`docs/specs/approvers.md`**: one GitHub login per line, no other fields.
  Already the allowlist named by requirement 2.
- **`frontmatter()`** (`spawn.py:777-793`): shallow parser reading only the
  leading `---` block of a record file into a flat dict.
- **Front record**: `wakes.py:210-224` (`_front`) picks the subject-opening
  role's record path `docs/issue-<n>/reports/<role>.md`. `wake_coding`
  (`wakes.py:266-283`) reads that record's `loop_state` and gates coding's
  first build entry on it equalling exactly `"scope-approved"`.
- **Human-only vocab mechanism already built** (this is the key finding):
  `docs/specs/loop-state-vocab.md`'s `## Human-only allowlist` section
  already lists `scope-approved` (added under issue #103), cross-checked by
  `test_vocab_coherence.py:37,60-64,87` (`HUMAN_ONLY_VALUE`,
  `_parse_vocab_doc`) against `wakes.py:42-56`'s `HUMAN_ONLY` dict. So
  requirement 3 ("human-only values are tool-written and exempted from
  record_enums") has its exemption *shape* already in place for
  `scope-approved` specifically — no generic `record_enums`/`record_fields`
  gate file exists elsewhere in the repo; the vocab-coherence test is the gate
  issue #115 means.
- **`wakes.py:47-48`** (`HUMAN_ONLY["사전 승인 게이트"]`) and
  **`docs/specs/wake-routing.md:57-62`** ("First-build approval guard") both
  currently phrase the whole gate as human-only, with no mention of a tool
  performing the write — this is the wording requirement 4 asks to fix.

## Gaps (what does not exist yet)

- No code anywhere reads GitHub PR/issue comments and checks the author
  against `docs/specs/approvers.md`. The `APPROVE issue-<n>/<role>`
  exact-string convention is documented only in prose
  (`on-the-record/commands/run.md:185`, `docs/specs/wake-routing.md` ~line 91)
  — it has never been implemented for any flow. This must be built from
  scratch for `approve-scope`.
- No `spawn.py approve-scope` subcommand exists.
- No prior hand-edit precedent found in git history for #89/#91 (unrelated
  or missing trees) — nothing to reverse-engineer from; design is new.

## Write surface implied

- `spawn.py`: new `approve-scope` subcommand + argparse wiring.
- `test/` (or repo's existing test layout — `test_vocab_coherence.py` sits at
  repo root, no `test/` dir observed) — a test file for the new subcommand.
- `docs/specs/wake-routing.md` — reword the "First-build approval guard"
  clause (decision human-only, mechanics tool-owned).
- Record enum/vocab exemption: confirm/extend the existing
  `loop-state-vocab.md` human-only allowlist entry for `scope-approved`
  covers writes made by the new tool (it already does by name; may need a
  clarifying line that the tool, not a role, is the writer).
