---
status: landed
files:
  - gates/gates.py
  - gates/ci.py
  - test_gates.py
  - docs/decisions/2026-08-07-measured-claim-line.md
  - docs/issue-332/proposals/2026-08-07-claim-evidence-at-write-time.md
---

## Request

The operator's diagnosis (#332): a claim recorded without evidence at the
moment it's made accumulates at the rate work is produced, and the debt
surfaces only in bulk, as a week of pure audit. The specific unevidenced-claim
generators from the operator's report are already filed as their own issues
(#333 denominator drift, #334 skipped-tests-counted-as-passing, #335
fake/real drift, #331 success declared without completion). What #332 itself
owns is the generator, not any one instance: a general, reusable mechanism so
a *new* kind of quantitative claim defaults to carrying its own evidence,
instead of each future defect needing its own issue and its own bespoke gate.

## Constraints

- Per #310: acceptance must name an executable artifact that fails on
  regression. A doc, a memory note, or a list edit does not discharge this.
- Per #330: state what this reaches beyond its own acceptance criteria,
  including already-on-disk state it invalidates.
- Must not duplicate #333/#334/#335/#331's own mechanisms — those are each
  issue-scoped fixes for one generator; #332 is the shared plumbing underneath
  future ones, not a sixth instance-specific gate.
- Role-handoff contract v3 s19 phase gating: this PR is phase 1 only (survey +
  proposal); no gate code is written until a human approver Approves.

## Rationale

**Chosen approach: extend the existing `fulfils:` marker-line convention
(issue #155, `gates/gates.py::record_fulfils_diff`) with a `count` kind**,
e.g. `fulfils: count <derivation-command-or-path> <N>`, checked by
mechanically re-running the named derivation and comparing to N — instead of
inventing a second, parallel claim-line syntax.

**Alternative considered and rejected: a free-text linter over record prose**
that flags any bare number without an adjacent citation. Rejected because the
false-positive surface is unbounded (issue numbers, ports, dates, line counts
all contain digits) and there is no fixed evidence format to validate a
citation against — the gate would either fail-open (a linter nobody trusts,
providing no actual check) or fail-closed on nearly everything a record
legitimately writes (unusable, gets disabled — `gates/ci.py`'s own docstring
already names this exact failure mode as the common way a gate dies: blocking
what shouldn't be blocked until a human turns it off). A structured
marker-line, by contrast, is opt-in per claim and only activates the check
where a writer has explicitly claimed a derivable number.

**Why extend `fulfils:` rather than add a sibling `measured:` marker
entirely from scratch:** `fulfils:` already has the parser, the fail-closed
handling of malformed lines, the "opt-in — untouched records aren't affected"
posture, and test coverage precedent in `test_gates.py`. Reusing its kind-verb
grammar (`fulfils: <kind> <args>`) is smaller surface than a second marker
line with its own frontmatter conventions, and keeps "claim in a phase-2
record checked against a mechanical derivation" as one convention instead of
two.

## What will be done

1. `docs/decisions/2026-08-07-measured-claim-line.md`: record the `fulfils:
   count <derivation> <N>` grammar as a decision — what `<derivation>` may be
   (a shell command whose stdout is expected to be an integer, or a glob/path
   whose match-count is taken), how it's re-run, and why `count` extends
   `fulfils:` rather than becoming a new marker.
2. `gates/gates.py`: extend `_FULFILS_LINE` parsing (or add a sibling regex
   consistent with the existing one) to accept `count`, and extend
   `record_fulfils_diff` (or a new function following its exact shape) to
   re-run the named derivation in the work tree and fail the record when the
   result doesn't equal the claimed N. Register in `ALL`.
3. `gates/ci.py`: wire the new/extended check into whatever check-list call
   site currently carries `record_fulfils_diff`, so it runs on the same
   trigger (CI PR check), not as a separate opt-in path.
4. `test_gates.py`: unit tests mirroring the existing `record_fulfils_diff`
   tests — a record with a correct count passes, a wrong count fails, a
   malformed `count` line fails closed, records without any `count` line are
   untouched.

## Out of scope

- Fixing any of the specific generators #333/#334/#335/#331 name — those stay
  in their own issues with their own mechanisms.
- A free-text/prose claim linter (rejected above).
- Retrofitting the `count` marker onto any already-merged record — this only
  changes what a *new* record can get away with going forward; it does not
  audit or invalidate existing unevidenced claims already on disk (see next
  section).
- Any claim shape other than "a number matches a re-runnable derivation" —
  qualitative claims ("완료됨", "동작함") are not addressed by this mechanism;
  #331 owns that generator.

## How you'll know it worked

`python3 -m pytest test_gates.py -k fulfils` (extended with the new `count`
cases) exercises the new check deterministically: a record asserting `fulfils:
count <cmd> <N>` where the re-run derivation disagrees with N fails the gate
(non-zero), and `gates/ci.py`'s check list runs it on a PR touching a phase-2
record the same way `record_fulfils_diff` already runs today — verifiable by
`git log --grep 'fulfils: count'` once phase 2 lands a real usage, and by the
new pytest cases passing in CI.

### What this change reaches beyond its own acceptance (per #330)

- It does **not** retroactively invalidate any already-merged record's
  unevidenced claims — those stay unverified until each is re-audited or its
  owning generator issue (#333/#334/#335/#331) is fixed. This proposal
  narrows only what a *future* record can silently get away with; it is not
  itself the audit.
- It extends `_FULFILS_LINE`/`record_fulfils_diff`, both used by every role
  writing a phase-2 record today. A malformed `count` line will fail-closed
  the same way a malformed `delete`/`create`/`move` line already does — any
  role that starts writing `fulfils: count ...` incorrectly is newly blocked
  by this, which is the intended effect but is a behavior change to a
  currently-passing gate path.
- `gates/ci.py`'s check-list wiring is shared CI surface — adding a check
  there affects every PR that touches a phase-2 record, not just this issue's
  own future PRs.

### Skip-condition note (survey-order-directive)

Not applicable: `docs/issue-332/reports/implementation/survey.md` was written
before this proposal, so no skip condition is being invoked.

### Post-proposal hunt finding (docs/reports/2026-08-07-hunt-claim-evidence-at-write-time.md)

The only workflow that runs `gates/ci.py` as a required PR check
(`.github/workflows/plan-aware-closes-gate.yml`) calls it with
`--closes-only`, and `gates/ci.py::check()` returns before ever reaching
`record_fulfils_diff` in that mode. So the *existing* `fulfils:` gate
(#155) already does not run in enforced CI today — extending it with a
`count` kind inherits that gap and would not be mechanically enforced on
real PRs either, only in local/`pytest` runs. Phase 2 must either widen
`.github/workflows/plan-aware-closes-gate.yml`'s invocation (adding it to
the write set) or explicitly scope this proposal's "how you'll know it
worked" down to pytest-only enforcement and say so — it must not claim CI
enforcement it doesn't have. This is flagged here for the approver to
weigh, not silently fixed by widening the write set pre-approval.
