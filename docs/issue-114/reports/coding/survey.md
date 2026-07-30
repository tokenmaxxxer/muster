# issue-114 current-state survey

## What exists today

- `spawn.py:_spawn_one` streams the role session's `stream-json` output
  line by line, tees each line to `<workspace>.session.log`, and only
  inspects `type == "result"` to build the final exit summary
  (`spawn.py:1872-1890`). Nothing in that loop reacts to intermediate
  content, so a PR opened mid-session is invisible until the loop ends
  and `ensure_pushed` runs (`spawn.py:1737-1781`) or the role's own
  `gh pr create` output happens to scroll past in the tee.
- `ensure_pushed` itself only fires once, after the process exits
  (`spawn.py:1913`), and only prints the "PR 을 열었다" line to stderr at
  that point — this is the exit-time report the issue says already
  works; the gap is everything before exit.
- `on-the-record/hooks/directive.sh` is the orchestrator's per-prompt
  steering (UserPromptSubmit hook). Its "PROGRESS CHECKS" paragraph
  (lines 71-74) is purely reactive: "when the user asks how it is
  going, tail that log" — there is no instruction to check unprompted.
- Wake routing (`wakes.py`, referenced via `spawn.py` import at
  `_spawn_one`) reads merged main only; this issue explicitly leaves
  that untouched.

## Write set (frozen)

- `spawn.py` — inside `_spawn_one`'s stream-json read loop
  (`spawn.py:1872-1881`): add detection of a PR URL appearing in a
  stream line and an immediate print to both the live log file and
  spawn stderr output. No new function needed; the loop already has an
  open file handle (`lf`) and iterates `proc.stdout`.
- `on-the-record/hooks/directive.sh` — extend the existing "PROGRESS
  CHECKS" bullet (lines 71-74) with the unprompted-check instruction:
  when a session runs unusually long, or when the user's decision
  queue is empty, check live logs and report material mid-run events
  (PR opened, gate refusal, silent stall).

No other files need touching: no new dependency, no new env var, no
schema change, no migration. Contract is a single new log-line shape:
`[<role>] PR opened mid-run: <url>` — frozen here so both sides (the
producer in spawn.py, the consumer instruction in directive.sh) agree
on what the orchestrator is told to look for.

## Scout: skipped

This is a two-file internal-tooling change to an existing log/directive
pipeline with no product-facing surface and no open design choice (the
issue names the exact two mechanisms and their boundary) — skip
condition "spec leaves no design decision open" applies. No exemplar
sweep run.
