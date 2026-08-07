Subject: issue-319

# Current-state survey

## Approval mechanics today (protocol.md §5, contract v3 s19)

- Every phase-1 -> phase-2 transition needs one GitHub approval act: an
  `APPROVED` PR review, or an issue comment that is exactly
  `APPROVE issue-<n>/<role>`, from a login in `docs/specs/approvers.md`
  (currently `JiwonJung94`, `jjongkwann`). No distinction is made by stake —
  `gates/gates.py` computes a write-set and a protected-path flag
  (`is_protected`, `PROTECTED_DIRS`/`PROTECTED_ROOT_DIRS`/`PROTECTED_GLOBS`,
  gates/gates.py:26-40) but that flag is used for the *closes*/write-scope
  gate, not for the approval-request presentation. A one-line marker rename
  and a rewrite of phase-determination logic both surface as one undifferentiated
  approval request.
- Contract §8 (quoted in protocol.md:219-234) reserves four judgment points to
  a human, including **"approving scope changes."** protocol.md:230-234
  records that a 2026-07-26 proposal tried to move one of the four to an agent
  and was withdrawn — no on-disk decision doc for it was found (`grep -rl
  "2026-07-26" docs/proposals/` — one unrelated hit only), so the withdrawal
  is documented only in protocol.md's own text, not as a linked ADR.
- No existing standing-decision, risk-classification, or approval-batching
  mechanism was found anywhere under `docs/` (`grep -rln "standing decision|
  approval fatigue|risk-proportionate"` — zero hits) or in `gates/`.

## What already exists that's reusable

- `gates/gates.py:is_protected(path)` — a pure function classifying a path as
  protected (touches `.github`, `migrations`, `auth`, `roles`, `gates`,
  secrets-shaped globs, etc.) or not. This is the closest existing primitive
  to a "stake" signal and is battle-tested (used by the write-scope gate).
- `gates/gates.py:writeset(d, cfg)` / `_committed_changes` — compute the
  actual changed-file list for a worktree from a manifest, already handling
  the git-diff-vs-status pitfalls (gates.py:70-103 comments).
- The proposal frontmatter convention (`files:` list, role-handoff contract
  v3 s19 / proposal-shape-gate.sh) already gives a machine-readable write set
  per proposal before any code is touched — the input a risk classifier needs
  already exists in every phase-1 proposal.

## Constraint that bounds the whole design space

Contract §8's four reserved judgment points, including "approving scope
changes," can only be moved by amending the role-handoff contract itself,
"decided there" (protocol.md:230-232) — not by a coding-role PR. Any design
that makes a phase-2 transition proceed *without* a fresh, distinguishable
human GitHub act for that specific scope change would repeat the withdrawn
2026-07-26 attempt. This rules out true bypass ("standing decision skips the
approval act entirely") as in-scope for this issue without a contract
amendment, which is a different decision authority than this role holds.

What stays in scope: tooling that (a) mechanically classifies risk so low-
and high-stake requests are visibly distinguished before the human acts, and
(b) batches multiple pending low-stake requests into one presentation — both
of which reduce reflex-approval risk and decision *count of presentations*
without removing or pre-authorizing the underlying GitHub approval act itself.

## Skip conditions checked

Not a pure bugfix; the issue leaves real design decisions open (what counts
as "low stake," how batching is presented, whether standing decisions are
in scope). Scout directive applies — see scout-brief.md for the sweep.
