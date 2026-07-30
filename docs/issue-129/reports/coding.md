---
subject: issue-129
role: coding
phase: 2
---

# Build record — issue-129

loop_state: done

code_under_review: spawn.py, test_spawn.py

## Why

Phase-1 survey (`docs/issue-129/reports/coding/survey.md`) and the
approved proposal (`docs/issue-129/proposals/coding.md`, approved via
issue-129 comment `APPROVE issue-129/coding`) confirmed four code-level
root causes for watch false positives: (1) `pr-opened` re-reported per
process since dedup only lived in an in-process `pr_seen` set, (2)
`gate-refusal` misfired from a raw-text regex scan matching JSON key
names/echoed text rather than actual denial structure, (3) same regex
misfired on unrelated mid-session tool output, (4) `failed-no-commit`
fired for sessions with no *new* commit even when a prior session on the
same branch already delivered a commit+PR. This record implements the
fixes the proposal specified for each.

## What was done

1. Idempotent `pr-opened` — `_prior_event_details(events_path, ev_type)`
   reads existing events of a given type from the workspace's own
   `.events.jsonl` and returns their `detail` set. `_spawn_one` seeds
   `pr_seen = _prior_event_details(events_path, "pr-opened")` at startup
   instead of an empty set, so a URL already recorded by an earlier
   process on the same workspace is never re-appended by a later one —
   zero new network calls.
2. Structural `gate-refusal` — the in-flight raw-text `_DENIAL_RE` scan
   over every stdout line was removed. `gate_refusal_seen` is now set
   only inside the existing `json.loads`-parsed branch, when a
   `result`-type stream-json object carries a non-empty
   `permission_denials` list — the same structured field `classify()`
   already trusts, never a substring match over echoed text or JSON key
   names. `_DENIAL_RE` itself is untouched (still used by the unrelated
   watchdog signal-3 scan, out of scope).
3. Honest `failed-no-commit` — `fail_closed_downgrade()` gains an
   `already_delivered: bool = False` parameter; when true and the tree
   is clean, a `progressed` outcome with no *new* commit is left alone
   instead of downgraded. The call site in `_spawn_one` computes it only
   in the `progressed`/no-blocked/no-new-commit case, via the existing
   `_pr_for_branch(Path(cwd), branch)` helper (already used for
   scope-approval elsewhere in this file) — if that call fails or the
   branch has no PR yet, `already_delivered` stays `False` and behavior
   falls back to today's downgrade, never toward a new blocking wait.
4. `test_spawn.py`: 8 new cases — `FailClosedDowngrade` gained
   `test_already_delivered_branch_exempts_verify_only_session` and
   `test_already_delivered_with_dirty_tree_still_downgrades`; a new
   `PriorEventDetails` class covers `_prior_event_details` directly; a
   new `EventReporting` class runs `_spawn_one` end-to-end (via the
   existing `cat`-as-`spawn_cmd` fixture pattern from `IssueScopedPrompt`)
   against literal fixtures from the survey: issue-46/49's `end_turn`
   result carrying the literal key `permission_denials`, issue-126's
   echoed `_DENIAL_RE` source line, a real denial (control case), and
   issue-123's repeated PR #124 URL across two respawns of the same
   workspace.

`classify()`'s precedence order/contract is untouched (all existing
`Classify`/`FailClosedDowngrade` cases still pass unmodified); `_await_bounded`
is untouched — no new network call was added inside its wait loop.

## What did not work

(none — implementation matched the proposal on the first pass; no false
start to record)

## closed_checks

- check: "python3 -m pytest test_spawn.py -q — full suite" — code_sha: HEAD
  (89 passed: 81 pre-existing + 8 new, run once locally before this commit)
- check: "python3 -m py_compile spawn.py" — code_sha: HEAD (clean)

## Warrant hunt

Dispatched `coding:warrant-hunter` at end of phase 1 (see PR #130). Given
this session's write set is a single tightly-coupled unit inside one
function (`_spawn_one`/`fail_closed_downgrade`), width=1 under the
freelunch threshold rule — no fan-out occurred, and no second hunt was
dispatched before this phase-2 completion beyond the phase-1 one already
recorded on the branch; noting this plainly rather than fabricating a
second hunt.

## Open findings

None outstanding. No blocking finding from verify/review is currently
addressed to this record.

## Open finding resolution path

No open findings exist at commit time. Should verify or review raise a
blocking finding against this record, the resolution path is: address it
on this same branch, append a `resolved_findings:` entry to this record
naming the finding and the fix commit, and let the finder re-clear before
any further build commit on this branch proceeds.

## Next steps

None from this role — scope is complete per the approved proposal.
Follow-on verification/review is the next layer's job, not a coding
next-step.

## How it was confirmed

`python3 -m pytest test_spawn.py -q` run once locally before this commit;
all 89 cases, including the 8 new ones, passed.
