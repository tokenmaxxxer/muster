---
status: proposed
files:
  - docs/specs/reconciled-index.md
  - gates/spec_index.py
  - test_spec_index.py
  - gates/ci.py
  - docs/handbooks/on-the-record.md
  - docs/handbooks/operations.md
---

## Request

The operator reported that repos build against the engine's spec
without anyone having read it end to end, so contradictions between
documents survive indefinitely and get resolved differently by each
reader — four wrong decisions in one day traced to this. Something
must own a reconciled reading of the spec so a contradiction is found
once, not re-discovered by every consumer.

## Constraints

- Per #310: acceptance must name an executable artifact that fails on
  regression; a doc edit or promise does not discharge this.
- Per #328: stay inside "who owns the reconciled reading" — do not
  fold in #321 (requirement dilution across operator turns) or general
  doc-quality cleanup; those are separate root causes.
- Write set stays inside what phase 1 can commit to: one new
  authoritative index document, one gate script, one test, one gate
  wiring point, and the two files already known to contain the
  confirmed contradiction (survey.md).

## Rationale

Two approaches were considered.

**A — semantic contradiction detection** (an agent periodically
re-reads all spec-shaped docs and reports disagreements). Rejected:
this recreates the exact failure mode the issue describes — a
process that "reads the fragment it needs at the moment it needs it"
— just on a schedule instead of on demand. It also isn't mechanically
checkable in the #310 sense: an LLM's judgment call about whether two
paragraphs "contradict" is not a regression test, it's another
opinion to be re-litigated. Two independent runs of the same detector
could disagree with each other.

**B — content-hash manifest + CI gate** (chosen): a single document,
`docs/specs/reconciled-index.md`, lists every spec-shaped document and
records a SHA256 of its current content plus, for topics known to have
been ambiguous across documents, a one-line resolved statement citing
which document is authoritative. `gates/spec_index.py` recomputes each
listed file's hash and fails (nonzero exit) the moment any listed
file's content diverges from what's recorded, until a human
re-generates the recorded hash — which requires opening the index and
looking at what changed. This is the pattern doc-drift tooling
(fiberplane/drift, Fern's API-governance model — see scout-brief.md)
already converges on: bind a source of truth to the artifacts it
governs and gate on divergence, rather than trying to detect
contradictions semantically. It fits the repo's existing convention:
`gates/` already holds deterministic, zero-LLM checks run after every
session (`docs/handbooks/on-the-record.md:26`).

B was chosen over A because it is the only one of the two that
satisfies #310's "fails on regression" requirement without introducing
a new class of unverifiable LLM-judgment gate.

## What will be done

1. Write `docs/specs/reconciled-index.md`: a table of every spec-shaped
   document (`protocol.md`, `protocol.ko.md`, `README.md`,
   `README.ko.md`, `docs/specs/approvers.md`,
   `docs/specs/flows-schema.md`, `docs/handbooks/on-the-record.md`,
   `docs/handbooks/operations.md`, `docs/handbooks/setup.md`,
   `on-the-record/commands/run.md`) with its recorded SHA256, plus a
   "Resolved ambiguities" section that fixes the one confirmed
   contradiction found in survey.md: the ledger's canonical storage is
   `runs/ledger.jsonl` (per operations.md, flows-schema.md, run.md);
   `ledger/collect.py` is an aggregator over that file, not itself
   storage.
2. Correct the misleading line in `docs/handbooks/on-the-record.md`
   (both language variants) so its architecture diagram no longer
   implies `ledger/` is the storage location — reword to name it as
   the aggregator, matching what's now recorded in the index. Same
   correction is not needed in `operations.md` (already correct);
   confirm no other file needs the same fix during implementation.
3. Write `gates/spec_index.py`: recomputes each listed file's hash
   against `docs/specs/reconciled-index.md` and exits nonzero listing
   every mismatch, in the two modes other gates in this repo already
   use — check mode (default, used in CI) and an update mode
   (`--update`) that rewrites the recorded hashes, so fixing drift
   requires a human to run it deliberately and see the diff in the PR.
4. Wire `gates/spec_index.py` into `gates/ci.py` alongside the existing
   gate calls so it runs on every CI invocation, the same as other
   `gates/*.py` checks.
5. Write `test_spec_index.py`: asserts the gate exits 0 against the
   current repo state (baseline), and asserts it exits nonzero when a
   listed file's on-disk content is mutated relative to what's
   recorded (regression case), using a temp copy so the test doesn't
   depend on mutating real repo files.

## Out of scope

- Semantic/NLP contradiction detection between documents (approach A,
  rejected above).
- Reconciling every possible ambiguity across all ~10 documents in one
  pass — only the confirmed ledger-location contradiction is resolved
  here; the index's job going forward is to force future edits to be
  looked at, not to retroactively audit everything today.
- #321 (requirement dilution across operator turns) and #328 (issue
  bundling) — named as related context by the issue, not folded in.
- Any change to `roles/` rulebooks or role-session behavior.

## How you'll know it worked

`pytest test_spec_index.py` is the executable artifact: it fails today
(file doesn't exist yet) and, once built, fails again if a listed
spec-shaped document is edited without `docs/specs/reconciled-index.md`
being regenerated to match — i.e. it fails on exactly the regression
the issue describes (a spec doc drifting out from under its recorded,
reconciled reading). `gates/spec_index.py` run standalone (`python
gates/spec_index.py`) gives the same signal outside pytest, and its
inclusion in `gates/ci.py` means CI itself blocks a PR that edits a
spec-shaped doc without updating the index.
