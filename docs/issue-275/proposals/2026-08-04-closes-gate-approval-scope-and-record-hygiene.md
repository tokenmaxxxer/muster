files: gates/ci.py, gates/test_closes_gate_ci.py, docs/handbooks/operations.md, test_spawn.py, docs/issue-271/reports/implementation.md

## Request

Issue #275 follows up four findings (F1-F4) that a #271 execution-
observation session (`docs/issue-271/reports/execution-observation.md`,
2026-08-04) recorded against the landed PR #273. Three are documentation
or citation hygiene; one, F3, is a real fail-open gap: `gates/ci.py`'s
`_phase_from_approval` reads comments from both the issue and the PR's
own conversation thread when deciding whether a `phase2`-opening approval
exists, but contract v3 §19's single-account path recognizes only an
issue-level `APPROVE issue-<n>/<role>` comment — anything posted on the
PR thread is supposed to count as feedback, not approval. Because
GitHub serves both issue comments and PR conversation comments from the
same `/issues/<n>/comments` endpoint, the second fetch (keyed on the PR
number) silently returns PR-thread comments and folds them into the
approval check. The four asks: narrow that predicate's input back to
just the issue-level surface with a red-green pin (F3); bring the
Korean half of `docs/handbooks/operations.md`'s merge-gate section back
into agreement with its English mirror, which currently describes the
post-#271 approval-event phase signal while the Korean half still
describes the deleted keyword-derived phase (F2); correct two stale
line-number citations left behind by a mid-review rebase in the restored
drain-guard test and its landed record (F1), making a call on citation
style informed by issue #227's prior observation about citation drift;
and replace requirement 4's recorded "red" proof — currently an
`AttributeError` from a not-yet-existing symbol, which shows only that
new code didn't exist yet — with an artifact that actually demonstrates
the pre-#271 gate passing a commit-message-only closing keyword through
(F4).

## Constraints

- From the issue: the `#271` landing structure — the three-surface
  (body/title/commit-message) phase-1 mismatch check, and the fact that
  phase is derived from an approval event rather than from closing-
  keyword presence — stays as-is; this issue is alignment and hygiene,
  not a redesign.
- From the issue: `closes-gate`'s required-status-check context name and
  main's branch-protection configuration do not change.
- From investigation: F2's Korean-text fix cannot precede F3's code fix
  in dependency order, because the current English text it would
  otherwise mirror (`operations.md:785-786`) documents F3's bug ("issue/PR
  comment"). The proposal below sequences F3 before F2 for that reason,
  though both land in the same phase-2 PR.
- From investigation: F3's fix touches only `gates/ci.py`; the same
  comment-union shape exists in two other places in this codebase
  (`gates/flows.py`'s status-dashboard `comments_for`, and `spawn.py`'s
  `approve_scope` for the unrelated `scope-approved` gate) that issue
  #275 does not name and this proposal does not touch — see Out of
  scope.

## Rationale

**F3 — narrow the input, don't filter the response.** The chosen fix is
to delete `comments += spawn._issue_comments(repo, pr)` from
`_phase_from_approval` and read only the issue's comments. The
alternative seriously considered was making `spawn._issue_comments`
(or a new wrapper) discriminate a true issue-level comment from a
PR-conversation comment by checking, via `gh api
repos/<slug>/issues/<n>`, whether the target number carries a
`pull_request` key — i.e. push the fix down into the shared fetch layer
so it can't be gotten wrong again. This was rejected on two grounds: it
answers a question the caller already knows the answer to (every call
site passes either an `issue` or a `pr` parameter by construction, never
an ambiguous "number"), so the extra `gh api` round-trip buys nothing;
and `_issue_comments` is a genuinely shared helper with other legitimate
PR-number callers for other purposes (`approve_scope`'s scope-approval
gate, the status dashboard's `comments_for`) — narrowing its contract to
serve one caller's correctness bug would either break those callers or
require a parameter threading its way through a function that has
stayed a one-argument fetch since before this issue. A second
alternative — keep both fetches but filter the PR-number response for
"issue-shaped" comments — was rejected on a factual rather than a style
ground: every comment `/issues/<PR-number>/comments` returns was, by
GitHub's data model, posted on that PR's own conversation tab; there is
no subset of that response that is ever a true issue-level comment for a
different number, so filtering the wrong fetch cannot recover the right
one. Deleting the second fetch outright is both the minimal diff and the
only version of the fix that is actually correct.

**F3's test scope.** The red-green pin belongs on `_phase_from_approval`
(or the wired `--autodetect --closes-only` composition) directly, not on
a re-mock of the existing five cases at `gates/test_closes_gate_ci.py:129-197`
— those already mock `spawn._issue_comments` as `lambda repo, n: [...]
if n == 245 else []`, which is exactly the shape that let this bug ship
unnoticed (the PR-number branch always answers `[]`, so removing the
second call wouldn't change any existing assertion). The new case must
mock the PR-number branch to return a qualifying-looking comment and
assert the result stays `phase1`.

**F1 — two artifact classes, two citation styles, no new third style.**
Considered and rejected: sha-qualifying every corrected citation,
including the `test_spawn.py` in-code comment. This repo already has two
live conventions and this proposal uses the one that already fits each
artifact: this repo's `*.py` comments never carry a commit sha for
same-file self-references (e.g. `spawn.py:1944`'s own citation of
`session_end_verdict()` a few hundred lines up) — introducing one here
would mean keeping a line range and a sha in sync on every future touch,
for no reader who already has the file open. `docs/issue-271/reports/
implementation.md`'s `closed_checks` `ref:` fields are a different kind
of artifact — a landed, `loop_state: landed` record asserting a claim
about a specific historical tree state — and this repo's execution-
observation reports (including the one that raised F1) already use a
sha-qualified `` `file:line` @ `sha` `` style for exactly that kind of
claim. Issue #227's own execution-observation record
(`docs/issue-227/reports/execution-observation.md:265-268`) already
named unpinned-citation drift as a known, recurring, and previously
forgiven cost of this repo's dominant convention — this proposal doesn't
try to eliminate that cost repo-wide (out of scope, a much bigger
sweep), it picks the already-established sha-qualified style for the one
artifact class here where the convention already exists and the claim
is genuinely historical.

**F2 — corrected-target parity, not verbatim mirroring.** The rejected
alternative was translating today's English paragraphs
(`operations.md:784-795`, `:797-804`) into Korean as the fix. That would
propagate F3's bug into the Korean text the moment it's written
("issue/PR comment"), immediately re-creating the same KO/EN divergence
this finding exists to close, just with the roles of "stale" and
"current" reversed. The Korean section must describe the post-F3-fix,
issue-only behavior.

**F4 — reuse the still-live pre-fix predicate instead of reverting
code.** The rejected alternative was checking out the pre-`1cab34b` tree
and running the old test suite against it to capture a literal red run.
Rejected as unnecessary process overhead: `gates/ci.py:165-169` still
defines `_phase1_mismatch(body, issue)`, the single-surface (body-only)
predicate, kept at its pre-#271 shape specifically because older unit
tests call it directly. Calling it live, in the same test file, with a
clean body and a commit-message-only keyword and asserting `== []` is
the same behavioral evidence a historical checkout would give, without
a throwaway checkout step or a second test-running context.

## What will be done

- **F3.** In `gates/ci.py`'s `_phase_from_approval`, remove the
  `comments += spawn._issue_comments(repo, pr)` line so the function
  reads only `spawn._issue_comments(repo, issue)`. Add a red-green case
  to `gates/test_closes_gate_ci.py` alongside the existing five
  `_phase_from_approval` cases (`:129-197`) that mocks the PR-number
  branch of `spawn._issue_comments` to return a qualifying
  `APPROVE issue-<n>/<role>`-shaped comment from an approvers.md login,
  and asserts `_phase_from_approval` still returns `"phase1"`.
- **F2.** Rewrite the Korean `## 머지 게이트 (CI)` section
  (`docs/handbooks/operations.md:743-760`) so its phase-derivation
  sentence states the approval-event mechanism (issue comment or
  two-account PR review Approve) instead of the deleted keyword-
  derivation, and add Korean counterparts to the two English-only
  paragraphs at `:784-795` and `:797-804`, written to match the
  post-F3-fix wording (issue comment only, not "issue/PR comment").
- **F1.** In `test_spawn.py`'s
  `test_follow_prioritizes_pending_session_end_over_pid_check`
  (currently `:3749-3788`), correct the comment's two citations:
  `spawn.py:1884-1894` → `spawn.py:1943-1953` (the drain-priority
  block), and `test_spawn.py:3480-3485` →
  `test_spawn.py:3719-3747` (the sibling
  `test_follow_detects_dead_session_and_returns_crash_rc`). In
  `docs/issue-271/reports/implementation.md`, correct both
  `ref: test_spawn.py:3497` entries (`:23`, `:27`) to
  `ref: test_spawn.py:3749 @ c6c4363` (the sha-qualified form this
  proposal's Rationale settles on for `closed_checks` refs).
- **F4.** Add a case to `gates/test_closes_gate_ci.py` that calls the
  still-live `ci._phase1_mismatch` with a clean body and a separately-
  supplied commit-message list containing a closing keyword, asserts
  the body-only call returns `[]` (the pre-#271 gate's actual
  behavior — it never looked at commit messages), and cross-references
  the existing green case
  (`t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body`,
  `:322-348`) that shows the post-fix multi-surface check blocking the
  identical scenario. Update `docs/issue-271/reports/implementation.md`'s
  `closed_checks` red-proof entry (`:7-12`) to point at this new case
  instead of describing the `AttributeError`.

## Out of scope

- No code, test, or documentation implementation happens in this PR —
  this is a phase-1 proposal only; the write set above is for the
  future phase-2 session.
- `closes-gate`'s required-status-check context name and main's branch-
  protection configuration are not touched, per the issue's constraint.
- The #271 landing structure — the three-surface phase-1 mismatch check
  and the approval-event phase signal itself — is not redesigned, only
  the F1-F4 alignment/hygiene items are addressed.
- The same comment-union shape in `gates/flows.py`'s status-dashboard
  `comments_for()` (feeds `decision_queue`/`unapproved_open_prs`,
  informational, non-blocking) and in `spawn.py`'s `approve_scope()`
  (the separate `scope-approved` gate, issue #115/#224) is not touched.
  Both are structurally the same widening F3 fixes, but issue #275 names
  only `_phase_from_approval`; fixing either would be scope creep this
  proposal declines to take on unilaterally. Left as a flagged
  follow-on for a human to open as its own issue if warranted.
- No attempt to repo-wide-eliminate unpinned line citations (the cost
  issue #227's execution-observation already named as a recurring,
  accepted property of this repo's dominant record convention) — this
  proposal only picks a citation style for the specific artifacts F1
  names.

## How you'll know it worked

- **F3.** The new red-green case in `gates/test_closes_gate_ci.py`
  fails (returns `"phase2"`) against the pre-fix `_phase_from_approval`
  and passes (returns `"phase1"`) after the `comments +=
  spawn._issue_comments(repo, pr)` line is removed — an
  `APPROVE`-shaped string posted as a PR comment no longer opens phase
  2. The full `gates/test_closes_gate_ci.py` suite still passes
  (currently 26/26; one case added).
- **F2.** A side-by-side read of `docs/handbooks/operations.md`'s
  Korean and English `## 머지 게이트 (CI)` / `## Merge gate (CI)`
  sections shows the same claims in both languages: issue/role from
  branch name, phase from approval event (not closing keyword), and the
  three-surface expansion — no sentence in either language contradicts
  the other.
- **F1.** `test_spawn.py`'s corrected comment citations resolve exactly
  to the drain-priority block and the sibling test at HEAD (spot-check:
  open `spawn.py:1943-1953` and `test_spawn.py:3719-3747` and confirm
  they are what the comment says they are). `docs/issue-271/reports/
  implementation.md`'s two corrected `ref:` fields resolve to
  `test_spawn.py:3749` at the cited sha.
- **F4.** The new `_phase1_mismatch` case actually fails
  (`AssertionError`, not `AttributeError`) if temporarily asserted
  against a body-and-commit-message scenario where the keyword sits
  only in the body (proving the case is exercising real behavior, not a
  vacuous pass), and passes as written against the true pre-#271
  scenario (keyword only in commit messages) — pairing it with the
  existing green case gives an actual red/green pair for requirement 4,
  not an import-time crash.
