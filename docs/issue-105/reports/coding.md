---
kind: coding-record
subject: issue-105
loop_state: landed
code_under_review: 08affba31b4a5a45e535bf4f87bca7876626d7f4
---

## Why

PR #107 (Phase-1 proposal for #105) was approved and merged. Two silent
routing killers observed on live boards — a record committed without
well-formed `---`-delimited frontmatter, and a record with leaked
tool-tag residue (e.g. `</content>`) — needed a write-time, fail-closed
gate check, same direction #100's `record_enums` already established.
This record implements exactly what that proposal specified.

## What was done

Implemented `record_wellformed` and `record_no_tool_residue` in
`gates/gates.py`, independent of `issue-100/coding`'s unmerged
`record_enums` (per the proposal, since that branch isn't on `main`):

- `gates/gates.py`: added `RECORD_PATH` (local copy, since #100's isn't on
  `main`), `_changed_records()`, and the two checks, each split into a
  `*_in(work)` core (shared by router and CI call shapes) and a
  `(d, cfg)` wrapper for `ALL`/router use. `record_wellformed` blocks on
  missing opening `---` or missing closing `---`. `record_no_tool_residue`
  scans body lines outside fenced code blocks for a line that is only an
  XML-ish tag (`_TOOL_TAG` regex), reporting file:line:tag.
- Registered both in `ALL`.
- `gates/ci.py::check()`: wired both via the `*_in(repo)` shared core (CI
  passes the repo path directly, not `d/"work"` — same duplication
  pattern already used there for `deps`/`writeset`).
- `test_gates.py`: 7 new cases — missing-open, missing-close, valid-pass,
  leaked-tag-blocks, fenced-tag-allowed, clean-pass, both-defects-block-
  independently.

## What did not work

- First test run: `t_record_no_tool_residue_blocks_leaked_tag` asserted
  the tag landed on line 5; actual line was 6 (blank line after the `---`
  closer counted). Fixed the assertion to the actual line number.

## closed_checks

- code_sha: 08affba31b4a5a45e535bf4f87bca7876626d7f4
- check: `python3 test_gates.py` run directly in the working tree after
  the edits — all new `t_record_*` cases pass. One pre-existing,
  unrelated failure (`t_repo_local_claude_config_stops_the_spawn`,
  `OSError: Read-only file system` writing
  `~/.tokenmaxxxer/trusted-repo-config.json`) is a sandbox environment
  issue, not touched by this change.

## How it was verified

Ran `python3 test_gates.py`; all `t_record_wellformed_*` and
`t_record_no_tool_residue_*` cases pass. Manually traced both trigger
cases from the issue text through the new functions: a record missing
`---` is blocked with a message naming the file, and a record with a
trailing `</content>` line is blocked naming file + line + tag.

## Out of scope (unchanged from proposal)

No `roles/*.json` change, no retroactive scan of already-merged records
on `main`, no PreToolUse-time check in `tokenmaxxxer-core`, no dependency
on `issue-100/coding` landing first.

## open findings

None.
