---
status: proposed
files:
  - gates/risk_report.py
  - test_risk_report.py
  - docs/handbooks/risk-classified-approvals.md
---

## Request

The operator reports that every phase-1-to-phase-2 approval demands the same
interruption regardless of stake — a one-line marker migration costs the same
decision as a change to phase-determination logic — and that this makes
approval degrade into an unexamined reflex, which is worse than no gate
because the record then falsely claims a human decided. They ask the role to
investigate (not conclude): risk-proportionate gating, batching related
decisions, and standing decisions stated once and applying until revoked.

## Constraints

- Contract §8 reserves "approving scope changes" to a human, and a
  2026-07-26 proposal that tried to move a different one of those four
  reserved points to an agent was withdrawn (protocol.md:230-234). Nothing in
  this proposal may cause a phase-2 transition to proceed without a fresh,
  distinguishable GitHub approval act from an `approvers.md` login for that
  specific scope change.
- Per #310: acceptance must name an executable artifact that fails on
  regression; a doc sentence or memory note does not discharge the
  requirement.
- Per #330: state what this change reaches beyond its own acceptance
  criteria, including already-on-disk state it invalidates (see below).
- Per issue #319 itself ("filed as its own issue... unrelated problems merged
  into one issue destroy parallelism"): stay inside decision-*volume*, not
  decision-*quality* (better-written approval requests are a separate,
  already-filed issue per the operator's own note).

## Rationale

**Considered: a "standing decision" registry that lets a human pre-authorize
a class of future scope changes once, so matching future proposals skip the
GitHub approval act entirely.** This is the literal reading of the issue's
third suggested direction and would cut decision count the most. Rejected
for this pass: it requires redefining what counts as a valid approval act
under contract v3 s19 (currently exactly two paths: an `APPROVED` PR review
or an issue comment matching `APPROVE issue-<n>/<role>` verbatim) — that is a
role-handoff-contract amendment, decided at the contract, not inside a
coding-role PR, per the same clause that sank the 2026-07-26 attempt. Doing
it anyway here would repeat that withdrawal for a different reserved
judgment point. This is flagged as a follow-up for whoever owns contract
amendments, not built here.

**Considered: teach `gates/gates.py`'s existing dispatch (`check()`) to
compute risk and gate on it directly**, i.e. fold this into the mechanical
gate that already runs in CI. Rejected: `gates.py`'s gates decide pass/fail
for merge; risk classification here is advisory (it changes what the human
sees before deciding, never whether the merge is allowed), and conflating
the two risks turning a presentation aid into a silent auto-pass path for
protected-directory changes — exactly the failure mode the withdrawn
proposal represents. Keeping it a separate, non-blocking tool avoids that
coupling entirely.

**Chosen: a standalone, non-blocking risk classifier + batched report**,
reusing `gates/gates.py:is_protected` and its diff-collection helpers, that
computes a `low`/`high` stake label per open phase-1 proposal from path
protection plus a size threshold (scout finding: path alone is not enough —
see scout-brief.md), and renders one batched summary across all currently
open phase-1 proposals so the operator can see and decide on several
low-stake items together instead of one at a time. It never grants approval
and never changes what `gh-guard`/contract v3 s19 accept as a valid approval
act — it only changes what the human sees before acting.

## What will be done

- Add `gates/risk_report.py`:
  - `classify(paths: list[str], added_lines: int, removed_lines: int) -> str`
    returning `"high"` if any path is protected per `gates.is_protected`, or
    total changed lines exceed a fixed threshold (30 lines — matches the
    existing size-tier reasoning already used elsewhere in this repo's
    `warrant` cadence for its 20/200-line hunt-dispatch tiers, so the number
    is not invented fresh); `"low"` otherwise.
  - `report(proposals: list[dict]) -> str` — given a list of
    `{path, files, added, removed}` proposal records, returns one Markdown
    table batching all of them, grouped `high` first then `low`, so nothing
    low-stake needs its own separate look before the human can see the
    whole set.
  - `scan_open_proposals(root: Path) -> list[dict]` — walks
    `docs/issue-*/proposals/*.md` and `docs/proposals/*.md` with
    `status: proposed` frontmatter, reads each proposal's `files:` list, and
    for git-tracked paths pulls added/removed line counts via
    `git diff --stat` against `origin/main` (reusing the pattern already
    established in `gates/gates.py:_committed_changes`). A proposal file
    with no parseable `files:` list is fail-closed into `"high"` — unknown
    write-set is never classified as safe, matching `gates.py`'s own stated
    principle ("불확실하면 막는다" / when uncertain, block).
- Add `test_risk_report.py` — the executable acceptance artifact — asserting:
  - a proposal touching only `docs/` paths under the size threshold
    classifies `low`;
  - a proposal touching any `PROTECTED_DIRS`/`PROTECTED_ROOT_DIRS`/
    `PROTECTED_GLOBS` path classifies `high` regardless of size;
  - a proposal with no `files:` frontmatter, or an unparseable one,
    classifies `high` (fail-closed regression guard — this is the
    regression the acceptance line targets);
  - `report()` on a mixed batch orders `high` before `low` and includes
    every input proposal exactly once (no silent drop).
  This suite runs with `python3 test_risk_report.py`, same convention as
  `test_gates.py`, and is added to the existing test run the same way (no
  new CI wiring needed — `pytest.ini`/`conftest.py` already discover root
  `test_*.py` files).
- Add `docs/handbooks/risk-classified-approvals.md`: one page describing how
  to run `gates/risk_report.py` before triaging a batch of pending
  approvals, and stating explicitly, in its own text, that the report is
  advisory-only and never substitutes for the GitHub approval act contract
  v3 s19 requires.

## Out of scope

- Any mechanism that lets a proposal proceed to phase 2 without a fresh
  `APPROVED` review or exact `APPROVE issue-<n>/<role>` comment from an
  `approvers.md` login — that is the standing-decision bypass direction, and
  it needs a contract v3 amendment this role cannot make unilaterally (see
  Rationale).
- Wiring `risk_report.py` into `gh-guard`, CI, or `gates.py:check()` as a
  blocking check — it stays advisory/non-blocking in this pass.
- Improving the wording/clarity of individual approval requests — that is
  the separately-filed issue the operator names in the "Note on scope."
- A UI, Slack integration, or scheduled digest for the batched report —
  out of scope; this pass ships the classifier and the report function
  callable by a human or a future automation, not a delivery channel.

## How you'll know it worked

`python3 test_risk_report.py` exits 0 and fails (non-zero, with a specific
assertion message) if: a protected-path proposal is ever classified `low`,
if a proposal with missing/unparseable `files:` frontmatter is ever
classified anything but `high`, or if `report()` drops or misorders an input
proposal. That is the executable regression artifact per #310.

## What this reaches beyond its own acceptance criteria (per #330)

- **Invalidates no on-disk state.** No existing file's meaning changes;
  `gates/gates.py` is read (its `is_protected` function is imported), not
  modified, so every existing gate behavior and every existing test that
  exercises `gates.py` is unaffected.
- **Reaches, but does not resolve:** the operator's underlying complaint —
  approval-volume fatigue — is only partially addressed. This pass gives the
  operator a tool to *see* stake and *batch* low-stake review before
  deciding; it does not reduce the count of required GitHub approval acts,
  because doing that safely requires the contract-level standing-decision
  amendment called out as out-of-scope above. Anyone reading this proposal
  should not conclude the underlying fatigue is solved — only that its
  visibility is improved. The unresolved remainder (true decision-count
  reduction via standing decisions) is the load-bearing gap this proposal
  intentionally leaves open, flagged for contract-level follow-up rather
  than silently declared done.
- **Reaches other roles' consumption of proposals:** any role or human
  script that later wants a machine-readable stake signal for a proposal can
  import `gates/risk_report.py:classify`, so this establishes a shared
  vocabulary (`"low"`/`"high"`) other tooling may come to depend on — a
  later change to the threshold or the protected-path definition it reuses
  from `gates.py` will change classifications for every consumer, not just
  this proposal's own report.
