---
code_under_review: gates/pr_reference.py, gates/test_closes_gate_ci.py, test_gates.py
loop_state: done
---

# issue-280 phase 2 — implementation record

Approved proposal: `docs/issue-280/proposals/2026-08-07-full-closing-keyword-set.md`
(APPROVE issue-280/implementation on the issue).

## Why

`gates/pr_reference._CLOSES_REF` matched only 3 of GitHub's 9 closing-keyword
inflections (`closes|fixes|resolves`), so a phase-1 body like "Fixed #19"
passed `--closes-only` with zero approval and GitHub auto-closed the issue
on merge — defeating the phase-1/phase-2 approval gate. Approved proposal
widens the regex to the full set.

## What was done

- Widened `gates/pr_reference._CLOSES_REF` from
  `\b(closes|fixes|resolves)\s+#(\d+)` to
  `\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)` — all 9 GitHub
  closing-keyword inflections, case-insensitive (`(?i)`), same two capture
  groups (group 1 = keyword, group 2 = issue number), `\b` boundary kept.
- Added `t_phase1_mismatch_detects_full_closing_keyword_set` and
  `t_phase1_mismatch_ignores_near_miss_words` to
  `gates/test_closes_gate_ci.py` — sweeps 9 keywords x 3 case variants
  through `ci._phase1_mismatch`, plus `unclosed`/`prefixes` word-boundary
  negatives.
- Added `t_pr_reference_phase2_full_closing_keyword_set`,
  `t_pr_reference_phase2_fenced_closing_keyword_matches`, and
  `t_pr_reference_phase1_does_not_gate_closing_keywords_itself` to
  `test_gates.py` — same 27-variant sweep through
  `pr_reference.check_body(..., "phase2")`, a fenced-code-block case, and a
  test documenting that `check_body`'s phase1 branch does not itself gate
  closing keywords (that's `ci._phase1_mismatch`'s job).
- Ran `gates/test_closes_gate_ci.py` (30 passed) and the closing-keyword
  portion of `test_gates.py` (all new + existing `pr_reference`/`ci` tests
  passed) — see Closed checks. `test_gates.py` as a whole hits an
  unrelated pre-existing sandbox failure (`t_repo_local_claude_config_stops_the_spawn`
  tries to write `/home/jwjung/.tokenmaxxxer/trusted-repo-config.json`,
  read-only in this sandbox); confirmed unrelated by stashing this diff and
  reproducing the identical crash on the pre-change tree.
- Manually confirmed the regex against all 9 keywords x 3 cases plus
  `unclosed`/`prefixes` negatives via a standalone script, and via a
  hunt-agent (assume-incomplete-coverage stance) that additionally checked
  `closeup`, `fixture`, `resolveder`, `closing` false positives (all
  correctly rejected) and grepped for a second keyword list that might
  drift — none found; `gates/closure_sweep.py` reuses the same compiled
  `_CLOSES_REF` object rather than duplicating the pattern.

## What will be done (from proposal, tracked here)

- Widen `pr_reference._CLOSES_REF` to all 9 GitHub closing-keyword
  inflections, case-insensitive, same two capture groups.
- Add regression sweeps: `gates/test_closes_gate_ci.py` (phase-1 path via
  `ci._phase1_mismatch`) and `test_gates.py` (phase-2 path via
  `pr_reference.check_body`).
- Run both suites, fix anything broken, confirm manually before commit.

## What did not work

None.

## Doc-placement ladder

- No new env var / config key / dependency / migration / public-signature
  change — regex-only widening, no handbook or decisions/ entry required.

## Open findings

None. Hunt run (assume-incomplete-coverage stance) reported no blocking
finding.

## Next steps

None — delivery complete. Commit, push, and the PR carries `Closes #280`.

## Open-finding resolution path

None open; nothing to resolve.

## Closed checks

- `_CLOSES_REF` 9-keyword-set correctness (all forms match, near-misses
  rejected: `unclosed`, `prefixes`, `closeup`, `fixture`, `resolveder`,
  `closing`) — code_under_review: gates/pr_reference.py,
  gates/test_closes_gate_ci.py, test_gates.py.
- No second keyword list elsewhere in repo drifted out of sync
  (`gates/closure_sweep.py` reuses the same compiled regex object) —
  code_under_review: gates/pr_reference.py, gates/test_closes_gate_ci.py,
  test_gates.py.
- `gates/test_closes_gate_ci.py` full suite: 30/30 passed —
  code_under_review: gates/pr_reference.py, gates/test_closes_gate_ci.py,
  test_gates.py.
- `test_gates.py` `pr_reference`/closing-keyword tests: all passed (suite's
  one failure, `t_repo_local_claude_config_stops_the_spawn`, is a
  pre-existing sandbox read-only-fs issue unrelated to this diff, confirmed
  via git stash reproduction) — code_under_review: gates/pr_reference.py,
  gates/test_closes_gate_ci.py, test_gates.py.
