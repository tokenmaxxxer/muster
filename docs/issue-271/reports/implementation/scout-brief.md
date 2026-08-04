# Scout brief — issue #271

Stage: 1 sweep stage (4 `WebSearch` calls, dispatched in parallel in one
turn) + judgment point 1, then stopped — the returns were conclusive
enough on both open decisions (surface completeness, and whether an
off-the-shelf tool fits) that a second round would not have changed
either build decision (saturation).

## Must-bes (category-common findings, not this repo's own testing)

- GitHub's own documentation states that closing keywords are honored in
  **pull request titles and descriptions, as well as in commit
  messages** — three named surfaces, not two. [Source 1]
- GitHub's built-in safeguard against premature closure is *only*
  "must land on the default branch" — there is no first-class,
  documented way to make GitHub itself ignore a closing keyword once a
  commit carrying one reaches the default branch. [Source 2]
- The GraphQL `closingIssuesReferences` field is widely used by
  tooling as "the" way to ask GitHub what a PR will close, but the
  field itself is documented (and independently reported by other
  projects integrating it) to miss cases where the closing relationship
  comes from a commit message rather than the PR description/manual
  link. [Source 3]

## Performance axes (what comparable tools compete on)

- **Coverage breadth vs. false-positive cost** — every general-purpose
  commit-message/PR-title linting tool found (commitlint, the
  `semantic-pull-request` / `action-semantic-pull-request` GitHub
  Actions) is scoped to *format* conventions (Conventional Commits
  style), not to *closing-keyword* policy specifically — none of them
  ship a rule for "reject a closing keyword in this text." [Source 4]
- **Source of truth vs. re-derivation** — the two live options are (a)
  re-implement the same keyword regex GitHub itself uses, applied to
  every surface GitHub reads, or (b) ask GitHub's own resolution engine
  (`closingIssuesReferences`) and trust its answer. Source 3 establishes
  that (b) alone is insufficient for the commit-message surface
  specifically — confirmed independently by this session's own live
  test against a real incident PR (see survey.md §4b).

## Adopt / Skip

- **Adopt**: treat "which surfaces GitHub itself documents as
  closing-keyword-bearing" as the enumeration's ground truth (title +
  description + commit messages, Source 1) rather than reasoning from
  this repository's own incidents alone — the incidents only ever
  demonstrated the commit-message vector; the title vector was found by
  cross-checking against GitHub's documented surface list, not from a
  local incident.
- **Adopt**: use `closingIssuesReferences` as a *supplementary* signal
  for the one surface no regex can ever reach (a manually-linked issue
  with no keyword text anywhere), not as a replacement for direct
  text-surface checks — matches what Source 3's own gap report implies
  as the safe usage.
- **Skip**: adopting an existing linting bot (commitlint /
  `semantic-pull-request`) as the enforcement mechanism. Neither
  targets closing-keyword policy, and bolting a closing-keyword rule
  onto a Conventional-Commits format checker would add a dependency and
  a second config surface for a check this repository already owns and
  can extend directly (`gates/pr_reference.py`/`gates/ci.py`).

## Segment fit / gap line

This is a narrow, self-built category (an internal merge gate enforcing
a two-phase issue-lifecycle contract specific to this repository) with
no direct off-the-shelf comparable — the closest public prior art
(commit-message/PR-title linting bots) solves a different problem
(style conformance, not closing-keyword suppression) and none was found
to fit. What the category *does* establish, and this repository's
current gate does not yet have: recognition that title and commit
messages are first-class closing surfaces per GitHub's own documentation
(not just an incident-driven afterthought), and the specific,
documented insufficiency of `closingIssuesReferences` as a drop-in
substitute for reading commit messages directly. Both facts feed the
proposal's surface table and its Rationale directly.

Sources:
1. https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
2. https://docs.github.com/en/enterprise/2.16/user/github/managing-your-work-on-github/closing-issues-using-keywords
3. https://github.com/orgs/community/discussions/24706 ; https://github.com/PyGithub/PyGithub/issues/2567
4. https://github.com/marketplace/actions/semantic-pull-request ; https://commitlint.js.org/guides/ci-setup.html
