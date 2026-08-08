---
status: proposed
files:
  - docs/issue-444/reports/conformance-review.md
---

## Intent

For every closed requirement issue in the #310–#441 range (the #318–#336 batch, its follow-ups, and the operator-correction issues #310/#341/#407 named in the issue), classify how it was actually fixed — deployed plugin surface, repo-local only, or prose-only — so the operator can tell which of today's "closed" requirements will actually hold once the plugin is installed on another machine against a different target project.

## Constraints

- Classification is by located mechanism, not by reading the closing PR's stated intent (#416's rule: intent-reading never discharges a verdict).
- Category boundary is structural: `on-the-record/commands/**` and `on-the-record/hooks/**` are the only paths that ship with a consumer plugin install (per `.claude-plugin/marketplace.json`); `gates/`, `.github/workflows/`, and other repo-root paths are repo-local only (the #441 boundary the issue names); anything with no artifact that fails on regression is prose-only (#310's failure shape).
- Every one of the 57 closed issues in scope must appear exactly once in the final table, with a file-path citation as evidence.
- Every category-2/3 row must carry a follow-up recommendation: move to deployed surface, cover via #441's delivery mechanism, or a stated justification for why repo-local/prose coverage is sufficient.

## What will be done (phase 2, after Approve)

1. For each of the 57 issues, locate its closing PR/commit and the file(s) it actually changed.
2. Classify each by where those files live (deployed surface / repo-local / prose-only), citing the concrete path.
3. For regression-fix issues that restate an existing requirement (e.g. #432, #435) rather than add a new one, fold them into the requirement row they regress and note the fold explicitly, so the "exactly once" criterion is satisfied without inventing a duplicate requirement.
4. Write the full table plus the category-2/3 follow-up list to `docs/issue-444/reports/conformance-review.md`.

## Out of scope

- Fixing any category-2/3 item (moving code, adding gates) — this issue produces the classification and recommendation only; remediation is separate follow-up work for the owning role.
- Issues outside 310–441, and any issue in that range that is not closed.

## How you'll know it worked

- `docs/issue-444/reports/conformance-review.md` contains 57 rows (fewer if folds are applied, each fold noted), each with classification + file-path citation.
- Every category-2/3 row has a follow-up recommendation.
- No row's classification rests on a stated intent with no located file.

## What did not work

(none yet — phase 2 not started)
