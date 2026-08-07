---
status: proposed
files:
  - ledger/decisions.py
  - ledger/test_decisions.py
---

## Request
The operator's approvals, refusals, and corrective feedback encode judgment (what counts as adequate evidence, which tradeoffs are acceptable, what is a real fix vs. a patch) that the system currently consumes once and discards. The same correction ("patch-instead-of-structure") had to be repeated four times in one day before a human turned it into a durable artifact. The issue asks what is recoverable from the decision history, whether recurring corrections can be surfaced as candidate rules for the operator to confirm, and how to do that without the system inventing rules the operator never agreed to.

## Constraints
- The operator is the sole author of their own judgment (issue text, contract v3 s19): mining may only *surface a candidate*, never install or assert a rule as fact. Confirmation stays a human act, through the repo's existing approval channel (an operator-authored `docs/decisions/*.md` entry), not a new auto-merge path.
- Per #310 (this session): acceptance must name an executable artifact that fails on regression; a memory note, doc sentence, or promise does not discharge the requirement.
- Per #330 (this session): the change must state what it invalidates or reaches beyond its own acceptance criteria.
- Detection must be mechanical (survey/scout finding): the evidence corpus already lives in git-durable text — role sessions' own `## What did not work` / `## Rationale for deviations` sections (record-shape-gate already forces these to exist, even when empty) — so no new data-collection step or GitHub API dependency is required for a first pass.

## Rationale
Considered building an LLM-based semantic clustering pass over PR review bodies and issue comments (matches how larger orgs do this at scale, per scout brief — Meta's 64k review-comment-pair fine-tuning approach). Rejected: (1) it cannot produce a deterministic, testable regression check — its output would vary run to run, which fails #310's "executable artifact that fails when this regresses" bar outright; (2) it is exactly the failure mode the issue warns against — an opaque classifier's "recurring pattern" is not inspectable by the operator the way a plain keyword/substring match is, so it risks the system asserting a rule the operator cannot audit the reasoning for; (3) it requires a new external data path (GitHub API pull of PR review text) where a mechanical pass over already-committed `docs/**/reports/*.md` sections needs none. A plain normalized-substring recurrence count over the existing `## What did not work` / `## Rationale for deviations` corpus is lower-power but auditable, dependency-free, and matches this repo's existing `ledger/collect.py` shape (read the record, compute something objective, no LLM).

## What will be done
Add `ledger/decisions.py`, structured like `ledger/collect.py`:
1. Walk `docs/issue-*/reports/implementation.md` (and other roles' equivalent record files) for `## What did not work` and `## Rationale for deviations` sections across the full git history of each file (not just HEAD), the same way `ledger/collect.py history()` walks `review-record.md`.
2. Normalize each bullet line (lowercase, strip issue/file-specific tokens) and count occurrences of near-duplicate lines across *different* issues/subjects.
3. When a normalized line recurs at or above a threshold (default 2, i.e. the second occurrence already counts as "the operator paid this cost twice") AND no `docs/decisions/*.md` file exists whose frontmatter or body cites that pattern's normalized key, emit it as a candidate on stdout and exit non-zero.
4. Once the operator (or a role acting on the operator's explicit instruction) writes a `docs/decisions/*.md` entry that cites the candidate's key, the same pattern recurring again no longer fails the run — it is now a confirmed, findable decision, not a silently repeated cost.
Add `ledger/test_decisions.py` with fixture text (paired with the script, matching this repo's existing pattern of a `test_*.py` beside every gate/ledger module) asserting: a single occurrence does not flag; a second occurrence of the same normalized correction flags and exits non-zero with the candidate printed; a recurrence already covered by a matching `docs/decisions/*.md` entry passes.

## Out of scope
- Wiring `ledger/decisions.py` into CI or a merge gate (this proposal builds the detector; whether/how it becomes a blocking gate is a separate decision the operator can make once the detector's output is visible — avoids silently widening this into a new enforcement surface).
- Mining GitHub PR review bodies / issue comments directly via `gh api` — left as a documented follow-up in the script's own module docstring; the `## What did not work` / `## Rationale for deviations` corpus is the highest-signal, lowest-effort source per the survey and is sufficient to satisfy #322's acceptance bar on its own.
- Any LLM-based semantic matching — see Rationale.
- Retroactively backfilling `docs/decisions/*.md` entries for patterns the detector finds on its first run against real history; that data-driven follow-up is out of scope for this build (which only needs to produce the mechanism), and would be a separate proposal since it touches `docs/decisions/` as new write set beyond this one.

## How you'll know it worked
`python3 ledger/test_decisions.py` (or pytest over `ledger/test_decisions.py`) is the executable artifact: it fails today because `ledger/decisions.py` does not exist, and after this build it passes, exercising exactly the regression #322 exists to prevent — a recurring correction with no confirmed decision on file must make the check fail non-zero, not silently pass.
