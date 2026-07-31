---
kind: report
date: 2026-07-31
subject: issue-155
role: coding
---

# scout brief — issue-155

Mode: batched web search, 1 stage (3 queries in one batch), stopped at judge
point 1 — the field converged fast on one pattern and a second round would
not change the design.

## must-bes (from the field)
- A claim marker must be **structured and line-scoped** (key: value), not
  free text — git trailers (`Fixes:`, `Signed-off-by:`) and Conventional
  Commits footers both use `Token: value` on its own line specifically so
  tooling can regex/parse it without an NLP pass.
- Verification must compare against the **actual artifact**, not the
  claim's author — SLSA provenance and `changeset status --since=main`
  both fail the check (exit nonzero / reject) when the declared claim and
  the measured diff disagree, rather than trusting the stated claim.
- Unclaimed/undeclared changes are the default failure mode of these
  systems: `changeset status` fails CI when a PR touches release-worthy
  files with **no** changeset — i.e., missing declaration is itself
  flagged, not silently accepted.

## performance axes
- Parse cost: trailer-style tools are pure regex/line-match — no LLM
  involved, matching this repo's `gates/gates.py` "결정론적, LLM 0회"
  constraint already.
- Coverage: SLSA covers arbitrary build claims via cryptographic
  attestation (out of reach here — no signer, no transparency log);
  git-trailer-style tools only cover what's declared, which is the right
  ceiling for a repo gate.

## adopt / skip
- Adopt: `key: value` trailer-line syntax for the fulfilment marker
  (`fulfils: delete <path>`), one claim per line, parsed the same shallow
  way `gates/gates.py` already parses `- write: <path>` in
  `writeset()`/`_write_scope_overrides()` — reuse, not a new parser.
- Skip: SLSA-style signed attestation — no signer/transparency-log
  infra in this repo, and the issue scopes this to diff comparison, not
  cryptographic provenance.

## segment fit
This is an internal CI gate for solo/small-team agent workflows, not a
public supply-chain artifact — the closest fit is `changeset status`'s
CI-gate shape (line-declared claim, checked against the actual diff),
not SLSA's cross-org attestation shape.

## gap line
Current state (`gates/gates.py`) already has the diff-collection
primitive (`changed_files()`, rename-aware) and the shallow trailer-style
parser pattern (`_write_scope_overrides`) — the missing piece is only a
claim vocabulary (delete/create/move) and a gate function comparing
declared claims to `changed_files()`'s status. No new infra needed.

Sources:
- https://calebhearth.com/tally-git-trailers
- https://www.conventionalcommits.org/en/v1.0.0/
- https://slsa.dev/spec/v1.0/verifying-artifacts
- https://github.com/changesets/changesets/discussions/1119
- https://github.com/changesets/changesets/blob/main/docs/checking-for-changesets.md
