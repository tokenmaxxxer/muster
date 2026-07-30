---
kind: coding-record
subject: issue-100
loop_state: landed
upstream:
  - path: docs/issue-100/proposals/coding.md
    sha: 2c44ac0
---

# issue-100 — phase 2: write-time record-field enum gate

Approval: PR #102 merged (APPROVE issue-100/coding, single-account mode).

## Why

`roles/<role>.json` declares machine-judged fields (`verdict`,
`loop_state`) only as free prose inside `produces`; `wakes.py` exact-
matches specific string values with nothing upstream validating that a
committed record actually uses one of them. An out-of-enum value (e.g.
`verdict: "go (조건부 → ...)"`) silently fails to match and only surfaces
much later as a dead wake branch. This phase implements the approved
proposal's `record_fields` declaration + `record_enums` gate.

## What was done

Executed the approved proposal. Clause -> fulfilling change:

- Proposal §1 (`roles/<role>.json` `record_fields`): `roles/feasibility.json`
  gets `verdict: [go, no-go, conditional]` and `loop_state: [measuring,
  verdict]`; `coding.json` gets `loop_state: [scope-proposed,
  scope-approved, in-progress, landed]`; `qa.json`: `[handed-off]`;
  `review.json`: `[reported]`; `verify.json`: `[cleared]`; `ux-design.json`:
  `[reviewed]`; `product.json`: `[measuring]` — all read off `wakes.py`'s
  existing exact-match literals per the proposal's constraint. `ops.json`
  and `reflect.json` get an empty `record_fields: {}` instead of a
  `loop_state` enum: no existing code path (`wakes.py`, `docs/specs/
  wake-routing.md`) exact-matches a `loop_state` literal for either role,
  so declaring specific values would be fabrication, and declaring
  `loop_state: []` would fail-closed-block any value either role has ever
  legitimately written. This is a deliberate deviation from the
  proposal's "every role file gets at least that key" line — recorded
  under What did not work.
- Proposal §2 (`gates/gates.py` `record_enums`): added `RECORD_PATH`
  regex, `record_frontmatter()` (duplicate shallow `---` parser, matching
  `gates.py`'s existing no-cross-import-from-`spawn.py` stance), and
  `record_enums(d, cfg)`. Resolves `root = d/"work"` if present else `d`
  (same dual-mode shape `writeset`/`deps` already use vs. `ci.py`'s
  repo-root calls), reuses `changed_files()` (fail-closed on diff
  failure), matches changed paths against `docs/issue-*/reports/<role>.md`
  only (per-subrole files like `reports/coding/survey.md` excluded, per
  proposal), loads `roles/<role>.json` and blocks with a named reason if
  unreadable/unparseable, and blocks each `record_fields` key present in
  the record's frontmatter whose value isn't in the declared set.
- Proposal §3 (register + wire CI): added to `gates.py::ALL` as
  `"record_enums"`; `gates/ci.py::check()` now also calls
  `gates.record_enums(repo, {})`.
- Proposal §4 (tests): added to `test_gates.py` — out-of-enum blocks
  (`t_record_enums_out_of_enum_blocks`), in-enum passes
  (`t_record_enums_in_enum_passes`), undeclared field passes
  (`t_record_enums_undeclared_field_passes`), missing role file blocks
  (`t_record_enums_missing_role_file_blocks`), `loop_state` variant blocks
  (`t_record_enums_loop_state_out_of_set_blocks`).
- Proposal §5 ("how we'll know it worked"): manually reproduced the
  issue's exact trigger via `t_record_enums_out_of_enum_blocks` —
  `verdict: go (조건부 → 측정 필요)` against `roles/feasibility.json`'s
  declared `[go, no-go, conditional]` blocks with a message naming the
  field, the bad value, and the allowed set.

## What did not work

- The proposal's line "every role file gets at least that key
  (`loop_state`)" assumed every role has an established `loop_state`
  convention to declare. `ops` and `reflect` don't: nothing in `wakes.py`
  or `docs/specs/wake-routing.md` exact-matches a `loop_state` value for
  either. Declaring invented values would misrepresent an established
  convention that doesn't exist; declaring an empty allowed-list would
  fail-closed-block the field entirely on first legitimate use — worse
  than the issue this proposal fixes. Landed with `record_fields: {}` for
  both instead (no enum declared yet, field stays free-text, matching
  `record_enums`'s own "undeclared field passes" behavior) — a narrower
  scope than the proposal's literal wording, not a contradiction of its
  intent (only declare fields with an actual closed set behind them).

## Hunt

No warrant-hunter dispatch this round: the change is additive (new pure
function + new JSON keys + new tests), touches no existing runtime
branch (`writeset`/`deps`/`wakes.py` logic untouched — confirmed via
`git diff` on those files showing zero non-record_enums-related lines),
and the new code path itself is exercised end-to-end by the 5 new tests
above, including its two fail-closed branches (unreadable role file,
out-of-enum value). Direct test coverage substitutes for a probe here.

## Test plan (verified)

- `python3 test_gates.py`: 5 new `t_record_enums_*` tests pass. Full-run
  hits the same pre-existing sandbox `OSError` in
  `t_repo_local_claude_config_stops_the_spawn` confirmed present on the
  pre-change tree via `git stash` (identical traceback, unrelated to this
  change — matches issue-95's precedent).
- `python3 -c "import ast; ast.parse(...)"` on `gates/gates.py`,
  `gates/ci.py`, `test_gates.py` — syntax OK.

## Open findings

None.
