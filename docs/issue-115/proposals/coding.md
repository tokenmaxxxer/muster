# Proposal — issue-115: scope-approval interface

Reference: #115

## Request (paraphrased)

Humans express scope approval as a GitHub comment, never by hand-editing a
record. A new `spawn.py` command reads that comment, verifies the author
against the approvers allowlist, and writes the promotion commit itself —
closing the gap that previously made orchestrators hand-edit
`loop_state: scope-approved` into the front record.

## Constraints

- Decision stays human-only (a role, including coding, never self-approves
  scope); only the *mechanics* of reflecting that decision become tool-owned.
- Must reuse the existing s19 exact-string comment convention, not invent a
  new decision channel.
- Must not weaken write-time record validation for role-produced values —
  the exemption is scoped to this one human-only value, by name, the same
  way `scope-approved` is already scoped in `docs/specs/loop-state-vocab.md`.
- Phase 1 only: this PR stops after proposal + survey. No code, no
  `approve-scope` implementation, in this PR.

## Files (frozen write set for phase 2)

- `spawn.py` — new `approve-scope` subcommand:
  - `spawn.py approve-scope --issue <n> [-C <repo>]`
  - Resolves the subject's front record path via the same logic as
    `wakes.py:_front` (or a shared helper), reads its GitHub PR (the PR that
    delivered the `scope-proposed` record), fetches PR-level and issue-level
    comments via `gh api`/`gh pr view --json comments`, and looks for the
    exact string `APPROVE issue-<n>/scope` (or the s19 convention's existing
    string shape — exact string TBD at build time, matching s19's
    `APPROVE issue-<n>/<role>` pattern) posted by a login listed in
    `docs/specs/approvers.md`.
  - On a match: writes `loop_state: scope-approved` into the front record's
    frontmatter (a tool-written commit on `main` via the normal PR path —
    or directly if the record already lives on `main`, matching how other
    tool-written infra files are committed) and prints confirmation.
  - On no match: exits non-zero with a message naming what's missing
    (no matching comment / commenter not in approvers.md).
- `docs/specs/wake-routing.md` — reword the "First-build approval guard"
  section (~line 57-62) so the decision/mechanics split is explicit: front
  record reaching `scope-approved` is still the sole human-only *decision*
  path (no role can trigger it), but the *write* is performed by
  `spawn.py approve-scope`, not a hand-edit.
- `wakes.py` — reword `HUMAN_ONLY["사전 승인 게이트"]` (`wakes.py:47-48`) to
  match the same decision/mechanics split, matching the doc wording change.
- `docs/specs/loop-state-vocab.md` — clarify the existing
  `## Human-only allowlist` entry for `scope-approved` (~line 50-56) to name
  `spawn.py approve-scope` as the sole writer, so `test_vocab_coherence.py`'s
  existing exemption is confirmed to cover this tool-written value with no
  weakening of role-produced enum checks.
- A test file covering `approve-scope`'s comment/allowlist verification
  (author-match and non-match cases) — exact path decided at build time
  following this repo's existing top-level `test_*.py` convention
  (e.g. `test_vocab_coherence.py` sits at repo root, no `test/` subdir).

## What will be done (phase 2, on Approve)

1. Implement `approve-scope` in `spawn.py` per the design above.
2. Reword `wake-routing.md` and `wakes.py`'s `HUMAN_ONLY` entry.
3. Confirm/extend `loop-state-vocab.md`'s exemption wording.
4. Write and run tests for the new subcommand's verification logic.

## Out of scope

- Any change to the existing `approve` stub (PR-level GitHub Approve flow) —
  untouched, unrelated.
- Designing or changing the s19 exact-string convention itself beyond
  extending it to a `scope`-flavored string.
- Any other role's record fields.

## How you'll know it worked

- `spawn.py approve-scope --issue <n>` refuses when no matching comment
  exists or the commenter isn't in `approvers.md`, and succeeds (writes
  `loop_state: scope-approved`) when both hold — verified by the new test.
- `test_vocab_coherence.py` still passes with `scope-approved` in the
  human-only allowlist, unchanged in shape, now naming the tool as writer.
- No hand-edit is required anywhere in the flow.
