---
kind: proposal
status: approved
date: 2026-07-27
files:
  - roles/qa.json
  - protocol.md
  - protocol.ko.md
  - test_gates.py
---

# muster portability and doc refresh

## 1. Intent

Make muster machine-portable — no hardcoded personal absolute path anywhere in
tracked files, every rulebook location resolved relative to a configurable
root or environment variable — and refresh the docs that now describe a state
of the world that has moved on, so a muster-only checkout installs and runs
correctly on any machine, not just the one it was designed on.

## 2. Grounding (what was actually found)

**Hardcoded absolute paths.** `roles/*.json` already resolve rulebook
locations through `$TOKENMAXXXER_RULEBOOKS/<repo>` (see `coding.json:4`,
`feasibility.json:4`, `ops.json:4`, `product.json:4`, `review.json:4`), which
is documented and env-configurable (`README.md:76-80`, `README.ko.md:71-74`)
and covered by `test_gates.py:290-294`. That part is already portable.

The one personal absolute path still baked into a tracked file is in
**`roles/qa.json:20`**:

```json
"QA_WORKSPACE": "$HOME/workspace/10_WORK/tokenmaxxxer/qa-workspace"
```

`$HOME` expands, so this is not a literal `/Users/jk/...` string, but the
subpath (`workspace/10_WORK/tokenmaxxxer/qa-workspace`) is a specific
person's directory-naming convention hardcoded as the default, not a
generic, machine-portable default. `roles/qa.json:15` also scopes the
sandbox's `filesystem.allowWrite` to this same path. `test_gates.py:256-262`
only asserts no *literal* `/Users/` or `/home/` string appears in role
files — it does not catch an opinionated default hiding behind `$HOME`.

**Stale protocol.md claims.** `protocol.md:83-89` and the mirrored
`protocol.ko.md:80` state, "as of 2026-07-26 no rulebook has landed
[contract v2] and no repository has a board" — this is no longer true: all
eight rulebooks have since landed board/contract v2. `protocol.md:8`'s
"Unsettled" section at lines 211-213 repeats the same now-false premise
("Landing contract v2 in the six rulebooks ... none has landed. Until then
no repository has a board and muster has nothing to read. This is the
prerequisite for everything below it") and needs re-evaluation now that the
prerequisite is satisfied.

**Stale QA_WORKSPACE references.** `protocol.md:91-96` documents
`roles/qa.json`'s `QA_WORKSPACE` / sandbox `allowWrite` as a deliberate,
temporary carry-over "until the qa rulebook lands v2," at which point "that
same `allowWrite` will have to cover the target repo instead, since qa's
evidence moves in-repo. Both changes belong to the same commit as qa's
landing, not to this one." The qa-agent-rulebook's
`2026-07-27-qa-records-in-target-repo` proposal has now landed: QA records
live at the target repo's `docs/reports/records/<subject>/qa.md`, not in an
external `$QA_WORKSPACE` tree. `roles/qa.json` was never updated to match.
`contract/role-handoff-contract.md:281,295` already calls `$QA_WORKSPACE`
"now-abolished," so muster's own role file and protocol doc are the pieces
left behind. (`docs/proposals/2026-07-27-shared-core-and-consent.md:117` and
`spawn.py:192,453` reference `$QA_WORKSPACE` only in prose/comments
describing this same history; they are not in scope for edits here, just
noted as corroborating context.)

## 3. Constraints

- `docs/specs/role-handoff-contract.md` v2 (in `review-agent-rulebook`)
  remains the authority on the board/record format; this proposal does not
  alter it or restate its content, only brings muster's own docs in line
  with the fact that it has landed.
- `spawn.py`'s CLI interface (arguments, invocation shape) does not change.
  Any path-resolution fix is internal to how `roles/qa.json` is read, not to
  how `spawn.py` is called.

## 4. What will be done

1. **`roles/qa.json`**: replace the hardcoded `QA_WORKSPACE` default
   (`$HOME/workspace/10_WORK/tokenmaxxxer/qa-workspace`) and its
   `allowWrite` scoping with whatever qa's landed v2 board actually needs —
   in-repo target-path access (`docs/reports/records/<subject>/qa.md`) as
   the primary case, per the abolition already recorded in
   `contract/role-handoff-contract.md:281,295`. If any external scratch
   path is still genuinely required (e.g. sandboxed run artifacts), its
   default moves out of the tracked file and into an environment variable
   with no personal directory convention baked in, documented in a new
   `.env.example` at the repo root (see below).
2. **`protocol.md` / `protocol.ko.md`**: update the "as of 2026-07-26 no
   rulebook has landed it and no repository has a board" claim (and its
   Korean mirror) to reflect that all eight rulebooks have landed
   board/contract v2. Update the "Unsettled" section's dependent claim
   ("this is the prerequisite for everything below it") accordingly, and
   rewrite `protocol.md:91-96` (the `QA_WORKSPACE` carry-over paragraph) to
   describe the post-landing state instead of a still-pending one.
3. Re-run `test_gates.py` and, if the hidden-`$HOME`-default gap is worth
   closing generally (not just for this one instance), extend its
   path-hygiene check to flag opinionated subpaths behind `$HOME`/env-var
   expansion, not only literal `/Users/`, `/home/` strings — left as a
   judgment call for the implementer, not mandated here.
4. Strengthen `t_role_files_carry_no_absolute_home_path` (`test_gates.py:255`)
   to also reject `$HOME`-/`~`-prefixed defaults carrying personal directory
   conventions (e.g. `workspace/10_WORK`), so the gate itself catches the
   pattern this proposal removes.

## 5. New environment variable

Proposed: yes, conditionally. If `roles/qa.json` still needs an external
writable scratch path after moving evidence in-repo, that path becomes a new
env var (e.g. `TOKENMAXXXER_QA_SCRATCH`) with a generic default (or no
default, requiring explicit configuration) documented in a new
`.env.example` at the repo root, alongside the existing
`TOKENMAXXXER_RULEBOOKS`. If qa's landed v2 needs no external path at all,
no new variable is introduced and `.env.example` — if created — documents
only `TOKENMAXXXER_RULEBOOKS`. Which case applies is determined by reading
qa-agent-rulebook's landed proposal during implementation, not decided here.

## 6. Out of scope

- Publishing this repo (making it public, license, etc.).
- The rulebook repos themselves (`coding-agent-rulebook`,
  `qa-agent-rulebook`, etc.) — their content, board format, and landed
  proposals are not edited by this work.
- Rewriting `docs/specs/role-handoff-contract.md`'s content.
- Changing `spawn.py`'s CLI surface.

## 7. Success

- `grep -rn "/Users/\|/home/[a-z]" --include="*.json" --include="*.py" --include="*.md" .` (excluding `.git`, and excluding prose that *describes* the anti-pattern, such as `test_gates.py`'s own assertion strings) finds nothing live in `roles/*.json` or config.
- No tracked file bakes in a personal directory-naming convention as a
  default, including behind `$HOME` expansion (i.e. `roles/qa.json` no
  longer defaults `QA_WORKSPACE` to `.../10_WORK/tokenmaxxxer/...`).
- `protocol.md` and `protocol.ko.md` match the current landed state of all
  eight rulebooks — no claim that contract v2 is unlanded, no claim that no
  repository has a board.
- No stale `$QA_WORKSPACE`-as-current-design reference remains in
  `protocol.md`; it either documents the abolition or is silent, consistent
  with `contract/role-handoff-contract.md`.
- `python spawn.py --dry-run` (or the project's equivalent dry-run
  invocation) succeeds from a fresh clone with only `TOKENMAXXXER_RULEBOOKS`
  (and, if introduced, the new qa scratch variable) set — no other
  machine-specific environment state required.
- `t_role_files_carry_no_absolute_home_path` (`test_gates.py:255`) also
  rejects `$HOME`-/`~`-prefixed defaults carrying personal directory
  conventions (e.g. `workspace/10_WORK`), not only literal `/Users/`,
  `/home/` strings.

## What did not work

- Kept `t_sandbox_boundary_follows_the_env` and `t_role_env_defaults_expand`
  as generic, role-file-agnostic tests instead of deleting them — tried
  briefly, dropped it. Both hardcoded `roles/qa.json` and asserted on its
  (now-removed) `QA_WORKSPACE` env default and matching `allowWrite` entry;
  since `qa.json` no longer declares any `env` block, there was no role file
  left in the repo to exercise the "env override reaches the sandbox
  boundary" mechanism against. Building a synthetic role file to keep that
  coverage would mean faking `role_settings`'s `ensure_rulebook`/marketplace
  lookups (it reads `roles/<role>.json` from `spawn.ROOT` directly, no
  injection point), which is out of scope for this proposal's frozen write
  set. Removed both tests instead; the general mechanism they guarded
  (`spawn.py:187-214`) is untouched code, just currently unexercised by any
  role file.
- No new env var was introduced and no `.env.example` was created —
  qa's landed v2 needs no external scratch path (session temp dir is
  sufficient), so §5's conditional branch resolved to "nothing to add."
