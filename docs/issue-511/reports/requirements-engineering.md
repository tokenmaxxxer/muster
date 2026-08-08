---
name: requirements-engineering-511
description: Phase-2 execution record for issue #511's approved multi-axis impact classification proposal.
---

# issue #511 — requirements-engineering record (phase 2)

## What was done
Executed the approved proposal
(`docs/issue-511/proposals/2026-08-08-multi-axis-impact-classification.md`,
now `status: landed`) in full:

- `gates/risk_report.py` — added the four-axis classifier
  (`blast_radius_grade`, `reversibility_grade`, `propagation_grade`,
  `existing_signal_grade`, all anchored/machine-checkable, all
  fail-closed to `AXIS_MAX` on empty/unparseable input), `classify_axes()`
  applying the dominant-axis rule (`requires_individual_approval =
  reversibility_grade == AXIS_MAX`, never summed/averaged with the other
  three), and `batch_blocked()` as the batch-approval decision point.
  `classify()`/`report()` (issue #319) untouched.
- `gates/test_risk_report.py` — new axis/dominant-axis/fail-closed tests
  plus issue #319's original suite consolidated in (see the proposal's
  What did not work section). Reproduced this session:
  ```
  $ python3 -m pytest gates/test_risk_report.py -q
  ...............................                                          [100%]
  31 passed in 0.05s
  ```
- `docs/specs/impact-classification.md` (new) and
  `docs/specs/standing-decisions.md` (new, carries the contract v3 s19
  amendment text — `grep -q "standing"` matches).
- `docs/specs/enforcement-boundary.md` — `risk_report.py`'s row moved
  from `n/a (infrastructure)` to `contract`; added a row for the new
  `impact-guard.sh`.
- `on-the-record/hooks/impact-guard.sh` (new) + registration in
  `on-the-record/hooks/hooks.json`'s `PreToolUse`/`Bash` group: denies a
  Bash command batching 2+ `gh pr merge` calls when the target repo's own
  open proposals include one requiring individual approval.
- `on-the-record/hooks/test_impact_guard.py` (new) — live-fired against
  the real script. Reproduced this session:
  ```
  $ python3 on-the-record/hooks/test_impact_guard.py
    ok  t_batch_of_only_low_impact_proposals_is_allowed
    ok  t_batch_with_high_impact_proposal_is_denied
    ok  t_kill_switch_reverts_the_wiring_and_allows_the_same_batch
    ok  t_single_merge_is_not_treated_as_a_batch

  4 passed
  ```

Full suite, also reproduced this session:
```
$ python3 -m pytest gates/ on-the-record/hooks/ -q
........................................................................ [ 26%]
........................................................................ [ 52%]
........................................................................ [ 79%]
........................................................                 [100%]
272 passed in 9.75s
```

## Traceability matrix
| ID | Description | Source | Downstream link |
|---|---|---|---|
| 1 | Four-axis structural classification, no text interpretation | issue #511 req. 1 | `gates/risk_report.py` (`classify_axes`) |
| 2 | Anchored grades; unparseable/undecidable to highest grade | issue #511 req. 2 | `gates/risk_report.py` (`*_grade` functions) |
| 3 | Dominant-axis rule (no summing/averaging) | issue #511 req. 3 | `gates/risk_report.py` (`classify_axes`, field `requires_individual_approval`) |
| 4 | Standing decisions (ITIL standard change) + s19 amendment | issue #511 req. 4 | `docs/specs/standing-decisions.md` |
| 5 | risk_report wired into approval flow as a blocking path | issue #511 req. 5 | `on-the-record/hooks/impact-guard.sh` |
| 6 | No grade exempts a verification gate | issue #511 req. 6 | `docs/specs/standing-decisions.md` (Escalation default section) |
| 7 | Zero-install, target-repo-anchored | issue #511 req. 7 | `on-the-record/hooks/impact-guard.sh` (`_checkout_resolve`) |
| 8 | Phase-1 survey of ITIL/FMEA/CVSS | issue #511 req. 8 | `docs/issue-511/proposals/2026-08-08-multi-axis-impact-classification.md` (Methodology survey section) |

Full per-item detail, each with its own explicit verification condition
(IDs match the table above):

REQ-511-1 — Four-axis structural classification (blast radius,
reversibility, propagation, existing signals), no text interpretation.
Source: issue #511 requirement 1.
Verification: `gates/test_risk_report.py`, test classes
`ReversibilityGrade`, `BlastRadiusGrade`, `PropagationGrade`,
`ExistingSignalGrade`, all included in the 31-passed reproduction above.
Downstream: `gates/risk_report.py` (`classify_axes`);
`docs/specs/impact-classification.md` (Axes section).

REQ-511-2 — Anchored, machine-checkable grades; unparseable/undecidable
input takes the highest grade.
Source: issue #511 requirement 2.
Verification: `gates/test_risk_report.py`, test class
`FailClosedUnparseable` — every axis returns `AXIS_MAX` on an empty
write-set, included in the same reproduction above.
Downstream: `gates/risk_report.py` (`*_grade` functions' fail-closed
branches).

REQ-511-3 — Dominant-axis rule: axes never summed/averaged; worst
reversibility grade alone forces individual approval.
Source: issue #511 requirement 3.
Verification: `gates/test_risk_report.py`, test class `DominantAxisRule`
— includes the mild-axes-do-not-average-away-severe-reversibility case,
included in the reproduction above.
Downstream: `gates/risk_report.py` (`classify_axes`'s
`requires_individual_approval` field).

REQ-511-4 — Standing decisions modeled as ITIL standard change:
pre-defined, pre-approved change types with objective conditions;
out-of-condition escalates automatically. Contract v3 s19 amendment
filed.
Source: issue #511 requirement 4.
Verification: `grep -q "standing" docs/specs/standing-decisions.md`
exits 0 (verified this session).
Downstream: `docs/specs/standing-decisions.md` (Amendment text, Registry
format, Escalation default sections).

REQ-511-5 — risk_report classification wired into the approval flow as a
blocking path; high-impact proposals cannot be batch-approved.
Source: issue #511 requirement 5.
Verification: `on-the-record/hooks/test_impact_guard.py` — the red case
(`t_batch_with_high_impact_proposal_is_denied`) denies with exit 2; the
green case (`t_kill_switch_reverts_the_wiring_and_allows_the_same_batch`)
proves the deny came from live wiring by reverting it through the hook's
own kill switch, not a stub. Both included in the 4-passed reproduction
above.
Downstream: `gates/risk_report.py` (`batch_blocked`);
`on-the-record/hooks/impact-guard.sh`.

REQ-511-6 — No classification grade, including a standing-decision
match, exempts any existing verification gate; classification only
reallocates human attention.
Source: issue #511 requirement 6.
Verification: `docs/specs/standing-decisions.md`'s Escalation default
section states the empty-registry fail-closed default explicitly; no
code path in `impact-guard.sh` or `batch_blocked` skips an existing gate
— it only denies a Bash command before it runs.
Downstream: `docs/specs/standing-decisions.md`;
`docs/issue-511/proposals/2026-08-08-multi-axis-impact-classification.md`
(Constraints section).

REQ-511-7 — All enforcement fires zero-install in a plugin-installed
session against an arbitrary target repo; paths anchored to the target
root, nothing hardcoded to this marketplace checkout.
Source: issue #511 requirement 7.
Verification: `on-the-record/hooks/test_impact_guard.py` runs the real
hook against a bare synthetic `tmp_path` target with no on-the-record
checkout of its own, included in the 4-passed reproduction above.
Downstream: `on-the-record/hooks/impact-guard.sh`
(`_checkout_resolve`/`pwd -P` split, mirrors
`on-the-record/hooks/decision-queue-stopgate.sh`).

REQ-511-8 — Phase-1 proposal surveys ITIL/FMEA/CVSS with adopt/reject
rationale each, rejected alternatives, and a named failure signal.
Source: issue #511 requirement 8.
Verification: read
`docs/issue-511/proposals/2026-08-08-multi-axis-impact-classification.md`'s
Methodology survey section — present, unchanged since phase-1 approval
(this is the one requirement verified by reading, not running, because
it is a phase-1 authoring requirement already satisfied before this
phase-2 turn).
Downstream:
`docs/issue-511/proposals/2026-08-08-multi-axis-impact-classification.md`
(Methodology survey section).

## Acceptance-clause mapping
| issue #511 acceptance clause | fulfilled by |
|---|---|
| `pytest gates/test_risk_report.py -q` exits 0, incl. four-axis + dominant-axis + fail-closed tests | reproduced above, 31 passed |
| s19 amendment text present, `grep -q "standing"` exits 0 | `docs/specs/standing-decisions.md` Amendment text section |
| test proves high-impact proposal cannot pass batch approval, fails when wiring reverted | `on-the-record/hooks/test_impact_guard.py`, reproduced above, 4 passed |
| provenance: executed-unit | all commands above were run in this session, not read-only-claimed |

## Why
Issue #511 is the deferred structural half of #319: the shipped
`risk_report.py`/stop-gate/decision-queue-stopgate made approval fatigue
*visible* but reduced nothing. The low/high binary let one large-but-safe
diff swamp a one-line contract-file edit at the same "high" tier, and
nothing blocked a batch approval action even when it contained a
severe-reversibility item. The four-axis + dominant-axis design closes
both: axes stay unsummed (FMEA-RPN's and CVSS-v4-Scope's retirement is
why — averaging masks a severe axis under three mild ones), and the
worst reversibility grade alone gates individual approval and blocks
batching.

## Upstream basis
`docs/issue-511/proposals/2026-08-08-multi-axis-impact-classification.md`
(approved via the issue-511 issue comment `APPROVE
issue-511/requirements-engineering` from `JiwonJung94`, a listed
`docs/specs/approvers.md` account — single-account mode, PR author and
approver the same account).

## Ambiguity
Two ambiguities surfaced during phase-2 execution, both resolved (not
escalated):
1. Statement: the proposal's write set names `.claude-plugin/hooks.json`
   as the plugin hook manifest. Candidate readings: (a) create that file
   fresh as a second manifest, or (b) the proposal meant the real
   manifest and mis-transcribed its path. Resolution: (b) — every other
   hook in this delivery's own write set (`impact-guard.sh`) had to
   register somewhere reachable by `spawn.py`'s actual injection path,
   which is `on-the-record/hooks/hooks.json`; a second, unreferenced
   manifest would never fire. Registered there instead; documented as a
   write-set correction in the proposal's What did not work section.
2. Statement: requirement 5's "high-impact proposals cannot be
   batch-approved" — the proposal's own risk_report wiring section left
   open whether the guard must resolve each merged PR to its specific
   originating proposal, or may block on the target repo's open-proposal
   set as a whole. Candidate readings: (a) per-PR mapping (precise, but
   needs a `gh pr view`/branch-lookup round-trip per merge inside a
   zero-install `PreToolUse` hook), or (b) block the batching act itself
   whenever any open proposal in the batch's repo requires individual
   approval. Resolution: (b) — matches requirement 7's zero-install
   constraint and `contract-guard.sh`'s own precedent of limiting network
   calls inside a merge-time hook; recorded as a known conservative
   trade-off, not silently narrowed (see Open findings below).

## Open findings
- **warrant-hunter, before-landing, stance 3 (silent-failure) —**
  `docs/reports/2026-08-09-hunt-issue-511-multi-axis-impact-classification.md`:
  `gates/risk_report.py`'s `scan_open_proposals()` trusts each proposal
  file's `status: proposed` frontmatter with nothing flipping it when the
  proposal's PR actually merges, reproduced by the hunter this session:
  ```
  $ python3 -c "
  import sys; sys.path.insert(0, 'gates')
  import risk_report
  from pathlib import Path
  p = risk_report.scan_open_proposals(Path('.'))
  print('open proposals found:', len(p))
  print('blocked count:', len(risk_report.batch_blocked(p, Path('.'))))"
  open proposals found: 82
  blocked count: 40
  ```
  Many matched proposal files are already-landed (e.g.
  `docs/issue-286/proposals/2026-08-07-fix-event-cursor-integrity.md`,
  merged via PR #404) but still read `status: proposed`. Because
  `batch_blocked()` reads straight off that stale set,
  `on-the-record/hooks/impact-guard.sh` denies essentially every
  2+-`gh pr merge` batch in this repo today, independent of the real
  batch's actual risk — the guard's "still open right now" precondition
  is state nothing in the codebase maintains. This is a pre-existing gap
  in `scan_open_proposals()` (present since issue #319, not introduced by
  this delivery), but issue #511 is what turns it from a cosmetic report
  artifact into a live blocking gate, so it now has real teeth. Fixing it
  (a merge-time or `closure_sweep`-style status flip) is a distinct
  write-set from this proposal's — the fix belongs to a follow-up issue,
  not a silent scope-widen here. Recommend the user file one.
- `docs/specs/standing-decisions.md`'s registry ships empty (no standing
  decisions registered yet) — the proposal scoped populating it as a
  follow-up, not part of #511's acceptance; every write-set still falls
  through to the dominant-axis rule unchanged. Not a defect, but the
  registry format has never round-tripped through a real entry.
- `impact-guard.sh` blocks on any open high-impact proposal in the
  target repo when a batch is attempted, not specifically the proposal(s)
  named in the merged PRs — see ambiguity 2 above and the proposal's
  What did not work section. A repo with an unrelated stale high-impact
  proposal sitting open would block an otherwise-clean batch of two
  low-impact merges; this is conservative (fail-closed) but worth
  tightening if it proves noisy in practice.
- No warrant-hunter finding surfaced against this delivery as of this
  record (dispatch launched per the standing warrant directive; if a
  finding lands after this record is written, it will appear under
  `docs/reports/` per that directive's own file-naming rule).

kind: report
loop_state: landed
