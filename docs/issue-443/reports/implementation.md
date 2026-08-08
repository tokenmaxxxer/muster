---
code_under_review: on-the-record/hooks/contract-guard.sh, on-the-record/hooks/test_contract_guard.py
loop_state: phase-2-complete
---

# Implementation record — issue-443

Phase 2 (build) per approved proposal
`docs/issue-443/proposals/2026-08-08-contract-guard-target-repo-resolution.md`.
Approval: issue #443 comment `APPROVE issue-443/implementation` by
JiwonJung94 (listed in docs/specs/approvers.md), 2026-08-08T08:12:56Z.

## What was done

Implemented all three repo-resolution forms from the proposal's "What will
be done" in `on-the-record/hooks/contract-guard.sh`:

1. Full PR URL (`github.com/owner/repo/pull/N`) — extracts (owner/repo, N)
   directly, also fixing the prior unreached "no explicit number" gap for
   this form.
2. `-R`/`--repo owner/repo` flag — extracts owner/repo, passed to `gh` via
   `-R`.
3. `cd <path> &&` prefix — runs every `gh` subprocess call with
   `cwd=<path>` and reads `approvers.md` from `<path>/docs/specs/`.
4. `-R`/URL with no local checkout — passes `-R <owner/repo>` to `gh` for
   the PR/issue lookups, then exits 0 (explicit unreached/fail-open)
   before the approvers.md-dependent phase-2 determination, matching the
   file's existing comment style.
5. No indicator present — unchanged, byte-identical cwd-relative path.

Added `on-the-record/hooks/test_contract_guard.py` (8 cases): the red-green
cross-repo case (asserted to fail against the pre-fix file via `git
stash`, confirmed — see below — then pass against the fix), `-R`-flag
unreached, full-URL unreached, `cd` deny, `cd` allow, no-indicator
regression, and a regression case for the before-landing hunt finding
(`cd` + disagreeing `-R` must not silently favor `cd`).

Ran `python3 -m pytest on-the-record/hooks/test_contract_guard.py -q`:
7 passed. Ran the full suite (`python3 -m pytest -q`): 534 passed, 1
pre-existing unrelated failure (`t_rulebook_version_is_recorded` asserts a
clean git working tree — fails while this session has uncommitted changes,
unrelated to contract-guard.sh; resolves once this commit lands).

## Open findings

None open. The before-landing warrant-hunter dispatch (stance 3: "assume
the rule as written cannot hold") returned one FINDING — see
`docs/reports/2026-08-08-hunt-contract-guard-target-repo-resolution.md`
("before-landing" section: `cd <path> &&` combined with a disagreeing
`-R other/repo` silently judged the `cd`-target repo and dropped the
flag, allowing a merge whose actual target repo violated the phase-2
contract). Resolved below before landing.

## Resolution path

Fixed in `contract-guard.sh`: an explicit repo selector (`-R`/`--repo` or
a full PR URL) now always takes precedence over an incidental `cd
<path> &&` prefix — `target_cwd` is discarded whenever `url_m` or
`repo_flag_m` matches, so the flagged/URL'd repo drives resolution
regardless of any `cd` prefix, falling into the existing "no local
checkout" unreached/fail-open path rather than substituting the `cd`
repo's data. Re-ran the hunt's own repro after the fix: returncode 0 via
the fail-open unreached branch (not the prior false-"compliant" verdict).
Added `test_repo_flag_overrides_cd_prefix_when_they_disagree` to
`test_contract_guard.py` as a permanent regression case; full suite
re-run (`python3 -m pytest on-the-record/hooks/test_contract_guard.py
-q`): 7 passed.
closed_checks:
  - check: cd+disagreeing-R-flag no longer silently judges the cd repo
    code_sha: (uncommitted at write time; see commit that carries this
      record)

## Next steps

None — phase 2 complete. Commit, push, and update PR #447 for human
review/merge.

## What did not work

None — the before-landing hunt finding above was addressed during phase 2
build (not a case of something tried and undone), so it is tracked under
Open findings / Resolution path per the record-shape contract, not here.

## Doc placement

- No new env var, config key, dependency, or migration introduced —
  nothing required at the handbook tier.
- No library-or-format choice made beyond what the proposal's Rationale
  already recorded (approvers.md-over-API rejected there) — no new
  docs/issue-443/decisions/ entry needed.
- No benchmark/investigation numbers produced — no docs/issue-443/reports/
  entry beyond this record.

## Hunt cadence

Warrant-hunter dispatched at end of phase 1 (already landed in commit
b73b502, no finding). Before-phase-2-completion dispatch scheduled after
implementation lands, below.
