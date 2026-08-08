# Current-state survey — issue-444

## Write surfaces (repo layout as of 0fa8a2c)

- **Deployed plugin surface** (`.claude-plugin/marketplace.json` → plugin `on-the-record`, `source: ./on-the-record`): only `on-the-record/commands/**` and `on-the-record/hooks/**` ship to a consumer install. This is category 1.
- **Repo-local, category 2**: `gates/*.py`, `.github/workflows/*.yml`, and root-level files not under `on-the-record/` (`spawn.py`, `shape_contracts.py`, `test_*.py`, `conftest.py`, `roles/`, `ledger/`, `scripts/`, `bench/`, `tests/`, `test/`). None of these travel with a plugin install — a consumer project gets no copy.
- **Prose-only, category 3**: anything satisfied by a doc under `docs/` (a spec, a decision record, a protocol section) or a memory/contract clause with no artifact that fails on regression — the #310 failure shape named directly in the issue.

## Scope: closed requirement issues in range #310–#441

`gh issue list --state closed` filtered to 310 ≤ n ≤ 441 returns 57 issues (includes #310, #341, #407 named explicitly, and the #318–#336 batch in full). List captured in this survey's sibling proposal's Sources; the working table itself is phase-2 output (`docs/issue-444/reports/conformance-review.md`, written only after Approve, per contract v3 s19).

## Gaps / unknowns this survey did not resolve

- Per-issue fix-mechanism location (file path in `on-the-record/` vs `gates/`/`.github/workflows/` vs doc-only) is **not** determined here — that requires reading each issue's closing PR diff, which is phase-2 execution work, not phase-1 scoping.
- Some issues in range may not be "requirements" in the audit's sense (e.g. pure regression-fix issues #432/#435 restate an existing requirement rather than add a new one) — phase 2 must decide whether such issues get their own row or are folded into the requirement they regress, and say which, to satisfy "every closed requirement issue in scope appears exactly once."
- No exemplar/scout sweep was run for this task: it is an internal compliance audit against acceptance criteria the issue itself enumerates exhaustively (classification taxonomy, evidence requirement, follow-up requirement) — there is no external "how do other projects audit deploy-surface portability" question left open that changes what gets built. Skip condition: spec leaves no design decision open beyond methodology, which the proposal covers.
