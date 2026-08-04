# Scout brief — issue #271 step 2 (execution-observation)

Pass: **1 sweep stage, 3 angles, genuinely parallel** (three `Explore`
subagents dispatched in one message, web-search only). 0 deepening
stages — judge point 2 after the sweep: no further round would change a
check decision (each angle already returned the method that settles its
survey unknown), so deepening stopped under the saturation rule, well
inside the 5-stage / 3-min budget. Angles were aimed at survey §5's
method-unknowns (S5, S2/S3, S7), not at the issue text.

## Category must-bes (what a strong audit of this deliverable class assumes)

- **Input-surface completeness is the headline dimension** for auditing an
  enforcement control: enumerate every way the state can be produced, not
  just the documented path. GitHub's own linking doc is the authoritative
  surface list and adds two facts the enumeration must survive: a
  commit-message keyword closes the issue but the PR does **not** appear as
  a linked PR, and manual sidebar linking is a third, text-free surface
  (https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
- **Fail-closed by construction, checked branch by branch** — explicit-grant
  structure, every error branch handled, default state on unexpected
  failure named (https://authzed.com/blog/fail-open).
- **Dead-branch / tautology defects are a named class**: CWE-561 dead code,
  reachable only through CWE-570/571 always-false/always-true expressions —
  which is exactly the shape of a guard routed by the predicate it checks
  (https://cwe.mitre.org/data/definitions/561.html).
- **Design vs. operating-effectiveness are separate tests** in control
  audits; confirming the control exists as documented does not establish it
  operated (https://linfordco.com/blog/design-vs-operating-effectiveness/).
- **"Will the test fail when the code is broken?" is a reviewer's own
  question**, answered from the code, not deferred to the author
  (https://google.github.io/eng-practices/review/reviewer/looking-for.md).
- **Rotten green tests** are the formal name for a test that passes without
  exercising the code it names — including the arrangement-drift variant
  where a refactor leaves the assertion in an untaken branch
  (https://arxiv.org/pdf/1912.07322); mutation testing is the execution-based
  version of "delete the guard, the test must fail"
  (https://en.wikipedia.org/wiki/Mutation_testing).
- **`git range-diff old_base..old_head new_base..new_head` is the canonical
  rebase-integrity tool** (https://andrewlock.net/verifiying-tricky-git-rebases-with-range-diffs/,
  https://discourse.llvm.org/t/force-push-and-rebase/73766). It is
  **unavailable here**: it needs the vanished pre-rebase range, and GitHub
  exposes no public reflog once a force-pushed head is unreachable
  (https://github.com/orgs/community/discussions/64693). Substitute the
  field actually uses: re-review `git diff main...pr` three-dot as if the
  branch were a brand-new PR, and reason explicitly about **semantic
  conflicts** — changes that merge textually clean but are logically wrong,
  a known manual-review blind spot (https://arxiv.org/pdf/2310.02395).

## Performance axes this observation will compete on

1. Surface-completeness of the enumeration it audits (and whether the
   audit itself re-derives the surface list from the authoritative doc).
2. Fail-closed / dead-branch reasoning per branch, not per feature.
3. Honesty about the execution boundary — what the diff can settle vs.
   what only a run could, stated rather than blurred.

## Adopt / skip

- **Adopt**: three-dot re-review against the merge base as the substitute
  for the impossible `range-diff`, with the semantic-conflict question asked
  explicitly on each file the rebase touched.
- **Adopt**: the rotten-green structural test — does the arrangement still
  route through the guarded branch, is the assertion unconditional — as the
  diff-only ceiling for S2/S3, with the execution boundary stated.
- **Skip**: mutation testing / re-running the suite. It is the formally
  correct kill-evidence and it is prohibited for this role (re-executing the
  observed role's work), so the brief records it as the named limit instead.
- **Skip**: control operating-effectiveness sampling over a period — the
  gate has been live for hours, not a period; design-level review only.

## Gap line

Already met by the current state (from survey §2): the observed proposal's
row-A–H enumeration covers body / title / commit / squash / rebase / merge
commit / manual retype / manual UI link, and rows G–H name what regex
cannot reach — the field's surface-completeness must-be looks satisfied on
its face and needs verification, not invention. Missing from the current
state: no `range-diff` baseline exists (S5), so rebase integrity has no
first-class tool and must be reconstructed; and the discriminating-test
must-be (S2/S3) has no diff-only proof, only the author's own red-green
claim — the two places this observation has to substitute method for
evidence, and say so.

Sources: all URLs inline above.
