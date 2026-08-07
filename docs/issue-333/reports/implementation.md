---
code_under_review:
  - gates/gates.py
  - test_gates.py
loop_state: landed
---

# Implementation record — issue #333

Phase 2, executing the approved proposal
(`docs/issue-333/proposals/derived-record-counts.md`, approved via
issue-level comment `APPROVE issue-333/implementation`, single-account
mode, role-handoff contract v3).

## What was done

1. `gates/gates.py`: added `record_derived_counts_in(work)` /
   `record_derived_counts(d, cfg)`, following the
   `record_no_tool_residue_in`/`record_no_tool_residue` split (fence-
   tracking loop, `_changed_records()` scope, fail-closed on
   `RuntimeError`). Two count shapes are checked outside fenced code
   blocks: a ratio (`_COUNT_RATIO = r"\d+\s*(?:of|/)\s*\d+"`) and a bare
   count noun-phrase (`_COUNT_NOUN = r"\d+\s+(?:detection\s+)?
   (?:items?|works?|checks?|cases?)\b"` — covers the issue's own "107
   detection items" motivating example, which the ratio pattern alone
   does not match). A match is a violation unless immediately followed
   by a `` `derived: <text>` `` tag (`_DERIVED_TAG`).
2. Registered `record_derived_counts` in `gates.ALL` (`gates/gates.py`),
   next to `record_no_tool_residue`.
3. `test_gates.py`: added five tests mirroring the
   `t_record_no_tool_residue_*` family —
   `t_record_derived_counts_blocks_bare_ratio`,
   `t_record_derived_counts_blocks_bare_count_noun`,
   `t_record_derived_counts_allows_fenced_number`,
   `t_record_derived_counts_allows_tagged_number`,
   `t_record_derived_counts_passes_clean_record`.

## Why (upstream basis)

Approved proposal `docs/issue-333/proposals/derived-record-counts.md`,
itself grounded in `docs/issue-333/reports/implementation/survey.md`
(phase 1). The proposal's `## Rationale` explains the structural
(fence-or-tag) detection choice over prose-signal detection, and the
kept-separate decision vs #303 — not restated here; see that file.

## What did not work

None.

## Doc placement

- No env var, config key, new dependency, or migration was introduced —
  nothing to place in a handbook.
- No library/format choice or changed public signature/wire format
  beyond what the approved proposal's `## Rationale` already recorded in
  `docs/issue-333/proposals/derived-record-counts.md` — no new
  `docs/issue-333/decisions/` entry needed.
- No benchmark/investigation numbers produced — no
  `docs/issue-333/reports/` entry beyond this record itself.

## What this reaches beyond its own acceptance criteria (per #330)

The acceptance bar in the proposal ("How you'll know it worked") is: the
five new `test_gates.py` tests pass, and the gate is a pure, reusable
function following the existing `record_*` shape. Beyond that:

- The check is symmetric — it also passes records with **no** count
  claim at all (`t_record_derived_counts_passes_clean_record`), so it
  cannot be satisfied by simply deleting all numbers from a record; it
  only fires on the specific unbacked-assertion shape.
- It reuses the same `_changed_records()` scoping every other `record_*`
  gate uses, so it composes with `record_wellformed` and
  `record_no_tool_residue` without any new traversal or new failure
  mode for the router/CI dual-entry callers.
- It does **not** verify a `derived:` tag's truth — only presence. That
  boundary is explicit in the proposal's Out of scope and restated here
  so a reader doesn't assume more coverage than exists: a record could
  cite a `derived: pytest test_gates.py` tag next to a number that tag
  does not actually produce, and this gate would still pass it. Catching
  that is a human/verify-role concern, per the proposal.

## Out of scope, not done here (matches the approved proposal)

- Wiring `record_derived_counts` into the router's/CI's default `names`
  list for `check()` so it actually runs on every PR. Searched for where
  that default list lives: `grep -rn "record_wellformed\|record_no_tool_residue"
  gates/ci.py roles/*.json .claude/hooks 2>/dev/null` inside this clone
  returned no hits wiring either existing `record_*` gate into a default
  `names` list either — the wiring point the proposal expected to find
  and "wire only if small and obvious" was not located inside this
  clone's write set. Per #358: this clone's `runs/` directory is
  gitignored and absent (confirmed via `git check-ignore -v runs` and
  `ls runs` returning "no such file or directory"), and `.claude/hooks.json`
  in this clone declares hook events as configuration, not as evidence
  of what Claude Code supports or of where gate names lists are wired —
  neither was searched as a stand-in for the real wiring point. Not
  finding the wiring point is reported as-is, not folded into a guess.
- Verifying a `derived:` tag's content is true (see above).
- A shared mechanism with #303 — kept as a separate gate per the
  proposal's Rationale.
- Retrofitting existing unenforced records (e.g.
  `docs/issue-170/reports/implementation.md`) — not touched by this PR.

## Test run (executable artifact, per #310)

```
$ python3 test_gates.py 2>&1 | grep -E "record_derived_counts|passed|Traceback"
  ok  t_record_derived_counts_allows_fenced_number
  ok  t_record_derived_counts_allows_tagged_number
  ok  t_record_derived_counts_blocks_bare_count_noun
  ok  t_record_derived_counts_blocks_bare_ratio
  ok  t_record_derived_counts_passes_clean_record
Traceback (most recent call last):
  ...
  File "spawn.py", line 871, in require_no_repo_config
    pins.write_text(json.dumps(table, indent=2))
OSError: [Errno 30] Read-only file system: '/home/jwjung/.tokenmaxxxer/trusted-repo-config.json'
```

The five `record_derived_counts` tests above (`derived: pytest
test_gates.py` is itself the derivation this claim is citing) run and
pass. The suite as a whole stops later at
`t_repo_local_claude_config_stops_the_spawn`, which is a pre-existing,
unrelated failure — reproduced identically on the unmodified `HEAD`
(`git stash; python3 test_gates.py`, same `OSError: Read-only file
system` at the same line, before any change in this PR existed) — caused
by this execution sandbox denying writes to
`/home/jwjung/.tokenmaxxxer/trusted-repo-config.json`, outside this
change's write set and outside this issue's scope. Not claimed as
passing, not silently skipped: the failure is real, pre-existing, and
unrelated to `record_derived_counts` per the isolated grep above and the
stash-diff comparison. No test was skipped to produce this result — per
#334, this is the actual run output, not a curated pass.

## Open findings

Before-landing warrant hunt (stance 0, bypass-the-gate;
`docs/reports/2026-08-07-hunt-derived-record-counts.md`) found that
`_COUNT_NOUN`'s hardcoded noun list (`item(s)/work(s)/check(s)/case(s)`)
lets an untagged, unfenced count claim slip through untouched when
phrased with a synonym outside that list (e.g. "12 findings and 8
instances of drift" returns `[]`). This is a real, reproduced gap, not
dismissed — but it is the exact trade-off the approved proposal's
`## Rationale` names and accepts explicitly: it rejected NLP-style
"does this read like a measurement" detection in favor of a closed,
mechanically-checkable structural signal (fence or `derived:` tag) over
an enumerable noun set scoped to the issue's own motivating example
("107 detection items"), on the stated grounds that free-form prose
detection would itself be unreliable (miss real derivations, accept fake
ones). Widening `_COUNT_NOUN` to more synonyms is a same-shape,
same-file follow-up inside the pattern already chosen, not a design
flaw in the pattern itself — filed as a follow-up rather than expanded
here to keep this PR inside the write set the proposal froze
(`gates/gates.py`, `test_gates.py`,
`docs/issue-333/reports/implementation.md`); expanding the noun list
unbounded was also explicitly named as staying inside "what a count is
written as," never "what the count measures," per the proposal's
Constraints. No blocking finding from verify is currently addressed to
this record.
