---
kind: coding-record
subject: issue-227
code_under_review: "`on-the-record/commands/run.md`, `docs/handbooks/operations.md`, `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`"
loop_state: landed
closed_checks:
  - name: composition-regression-hunt
    ref: on-the-record/commands/run.md:183
  - name: run-md-operations-md-wording-agreement
    ref: docs/handbooks/operations.md:318-334
  - name: decision-doc-line-citations-current
    ref: docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md:41-56
  - name: issue-224-framing-consistency
    ref: docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md:102-108
  - name: gate-script-line-independence
    ref: on-the-record/commands/run.md:202-215
  - name: 2026-07-29-closed-alternatives-not-reopened
    ref: docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md:80-100
---

# Implementation record — issue #227

Phase 2, executing the approved proposal
(`docs/issue-227/proposals/implementation.md`, approved via issue-level
comment `APPROVE issue-227/implementation`, single-account mode,
role-handoff contract v3, PR author and approver both jjongkwann,
comment posted 2026-08-03T12:26:37Z). Upstream basis: commit `144b413`
(this record's code_under_review file list, above) on branch
`issue-227/implementation`, PR #254.

This session resumed a prior session that stopped mid-phase-2 on usage
limits, with the three content files already fully drafted and staged
(uncommitted). This record picks up from there: verify the staged draft
against the approved proposal, commit, hunt, and write this record.

## Why

Issue #227 (paraphrased): the approval gate recognizes only a comment
whose entire body is the exact string `APPROVE issue-<n>/<role>`, but the
orchestrator playbook had no rule for what to post when the human's
decision is approve-with-feedback in the same breath — two real
repo-status-board incidents (rsb #20, #23) show a mixed token+prose
comment treated as approval despite not matching either real gate
function. The approved proposal's rationale for the chosen fix (a strict
two-comment sequence, token-only then feedback) over the two rejected
alternatives (a looser matcher; a new composite token) and the chosen
non-canonical-near-miss policy (warn, over abort and log-only) is in
`docs/issue-227/proposals/implementation.md`'s own `## Rationale`
section — not restated here; this record documents execution, not a
second rationale pass.

## What was done

Verified the three already-staged files against
`docs/issue-227/proposals/implementation.md`'s "What will be done" section
line by line, found them complete and matching (no edits needed), then
committed them as `144b413`:

- `on-the-record/commands/run.md` step 6: added the **조건부 승인**
  (conditional approval) bullet immediately after the existing "제안 승인"
  bullet — two issue comments in order, comment (a) token-only
  (`APPROVE issue-<n>/<역할>`, never any other text), comment (b) posted
  immediately after with feedback pointing back at (a) rather than
  repeating the token — and the **비정규 형태(warn)** bullet: on an
  approval-shaped near-miss (body contains the literal substring
  `APPROVE` but is not whole-body-identical to the token), post exactly
  one reply pointing at the canonical recipe and keep waiting, never treat
  it as approval, never repeat the reply on the same comment. Both bullets
  close with the issue-#224 cross-reference (code-side, not fixed here).
- `docs/handbooks/operations.md`: mirrored the same two-comment recipe and
  warn policy into the existing canonical-approval-location section
  (~line 309-334), same ordering, same issue-#224 cross-reference.
- `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`
  (new): records the chosen two-comment recipe; the three rejected
  recipe-level alternatives (looser matcher, new composite token,
  PR-review-Approve as default) with reasons; the executed (not just
  inspected) evidence that `gates/flows.py::_pr_approved()` returns
  `False` and `spawn.py::approve_scope()` raises `SystemExit` for both
  real rsb #20/#23 comment bodies; the warn-vs-abort-vs-log-only tradeoff
  table and the chosen warn policy; and the issue-#224 relationship.

`git show --stat 144b413`: 3 files changed, 140 insertions(+), 0
deletions — `docs/handbooks/operations.md` (+18), the new decision doc
(+108, new file), `on-the-record/commands/run.md` (+14). No file outside
the proposal's frozen write set touched.

## What will be done (from proposal)

All five numbered items in the proposal's "What will be done" section are
implemented as specified:

1. Conditional-approval recipe added to `run.md` step 6, immediately
   after "제안 승인" — done, text matches the proposal's specified content
   (token-only comment A, feedback comment B referencing A, no trailing
   text on A ever).
2. Warn policy stated in the same `run.md` addition — done, matches
   specification (near-miss = contains literal substring `APPROVE`, not
   whole-body-identical; one reply, never approval, never repeated).
3. Recipe and warn policy mirrored into `operations.md`'s
   canonical-approval-location section, same ordering — done (verified
   substantively identical wording between the two files; hunt check
   `run-md-operations-md-wording-agreement`, below).
4. New decision doc with the chosen recipe, three rejected alternatives,
   empirical evidence (execution results, not just inspection), and the
   non-canonical-near-miss policy with tradeoff table — done, all present.
5. Issue #224 cross-referenced by number (not content) in both `run.md`
   and the decision doc — done; also present in `operations.md` though
   the proposal only required `run.md` and the decision doc for this
   item.

No gap between what was proposed and what landed; no reword of the
approved plan's substance during this session (the draft was already
complete on pickup — see "What did not work" below for the one point
this session actually double-checked itself on).

## What did not work

Nothing was undone or replaced during this session. One thing expected
going in did not hold: the assumption, going into this resumed session,
was that the prior session's staged draft would need active completion
work (per the invocation's framing, "이어받아 검토·완성하고"). On review,
the draft was already complete and matched the proposal exactly — actual
work this session was verification + commit + hunt + record, not
drafting. Noted here since it is an expected-vs-actual gap at the moment
it was discovered (start of this session), even though the resolution
required no rework. Separately: the first commit attempt (content files)
was refused by `trailer-gate.sh` because a `git commit -m "$(cat <<'EOF'
...)"` heredoc-substitution message could not be statically tokenized to
verify the `Subject:` trailer — expected the heredoc form to work since
the literal text included the trailer; actual was a refusal, since the
gate's `shlex.split` tokenizer doesn't resolve `$(...)` command
substitution. Fixed by using multiple `-m` flags instead (one paragraph
per flag, last one exactly `Subject: issue-227`), which the gate's static
tokenizer can read directly. Also: the first draft of this record's
frontmatter used `code_under_review: 144b413` (a bare commit sha) and
`closed_checks[].code_sha`, matching the issue-236 precedent this session
used as a template — expected that format to pass `record-fields-gate.sh`
since prior records used it; actual was a refusal citing
`docs/issue-100/decisions/2026-08-03-record-citation-format-and-kind-convention.md`
(dated after issue-236's record), which supersedes the sha-citation
convention with a file-list `code_under_review` and `ref:`-keyed
`closed_checks` specifically for this role's own record. Fixed by
rewriting the frontmatter to the current convention (this file, as
written).

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step
  introduced -> N/A, nothing to add to a handbook beyond the
  canonical-approval-location section already updated as the proposal's
  own write set (item 3 above).
- Library-or-format choice over a named alternative (the two-comment
  recipe over a looser matcher, a new composite token, or PR-review-
  Approve as default) -> recorded in
  `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`
  (item 4 above) — done in this same commit.
- Benchmark/investigation numbers (the empirical gate-function run
  results) -> recorded in the same decision doc and cross-referenced from
  `docs/issue-227/reports/implementation/survey.md` (phase-1, already
  landed on this branch) — no additional phase-2 report needed beyond
  this record.

## Hunt

Stance: **composition-regression** (rotated — chronologically, the most
recent prior hunts on sibling issues in this repo are issue-223
(2026-08-03T17:49, adversarial-self, itself picked as "least-recently-used
of the 4" at that time), issue-236 (2026-08-03T15:06, assume-broken),
issue-232 (2026-08-03T13:12, assume-incomplete-coverage), issue-222
(2026-08-03T10:35, composition-regression). Of the four rotated stances
(adversarial-self, assume-broken, assume-incomplete-coverage,
composition-regression), composition-regression was last used furthest
back (issue-222) relative to the other three, making it the
least-recently-used entering this session). No registered `warrant-hunter`
subagent type is available in this session (same gap noted in
issue-223/issue-236's records), so `general-purpose` was dispatched in its
place with an explicit adversarial framing, matching that precedent.
Dispatched in the foreground against the committed diff (`144b413`) before
writing this record.

Findings:

1. **Warn bullet's trigger is "encountering an artifact," not "the user's
   stated decision" (CONFIRMED as a textual observation, not blocking).**
   Step 6 opens as "사용자의 결정을 중계한다" and every sibling bullet maps
   a user-stated decision to an action, but the warn bullet
   (`run.md:209-215`) fires on meeting a near-miss comment, not on a user
   decision about that comment. The step closes with a pre-existing,
   unmodified gate (`run.md:219-221`): "승인·머지는 사용자가 이 대화에서
   그 의사를 밝힌 뒤에만." **Disposition: not blocking.** That closing
   gate scopes 승인·머지 (approval/merge) specifically; the warn action is
   neither — it is explicitly designed, in the approved proposal and the
   decision doc, to never grant approval, only to post one clarifying
   reply. This is a deliberate, already-approved design point (proposal
   "What will be done" item 2, decision doc's "Why (adopted — warn...)"
   section), not a defect introduced by this execution. Left as-is,
   consistent with the approved design.
2. **Actor ambiguity — "the session" in the warn text could read as this
   repo's own orchestrator when the primary real-world failure case (the
   two rsb incidents) is actually a role-side session in an out-of-tree
   plugin this repo cannot patch (PLAUSIBLE, not blocking).** Both
   `run.md` and `operations.md` use an unqualified "the session"/"만나면"
   framing. **Disposition: not blocking.** The proposal's own "Out of
   scope" section states explicitly that wiring the warn policy's
   detection code into the out-of-tree role-side plugin is not this
   issue's write set — only documenting the policy is. The generic
   phrasing is consistent with a policy meant to be read by both the
   in-repo orchestrator and (by future adoption) the out-of-tree hook;
   narrowing the wording to name a specific actor this repo doesn't
   control would overstate what this repo can enforce. Left as-is,
   consistent with the approved proposal's stated scope boundary.
3. **`approve-scope` (hyphenated prose) vs `approve_scope()` (function
   name) — cosmetic naming variance across sibling documents (PLAUSIBLE,
   not blocking).** `run.md`/`operations.md` write `approve-scope`
   matching issue #227's own body text; the decision doc cites the
   literal function `approve_scope()` at `spawn.py:917`. **Disposition:
   not blocking.** Both forms are contextually correct — prose reference
   vs. code citation — not an inconsistency introduced by this commit.
   Left as-is.

Clean (checked, nothing wrong — cited so verify can skip re-deriving):

- `run-md-operations-md-wording-agreement`: the two-comment recipe and
  warn policy match substantively between `run.md:202-215` and
  `operations.md:318-334` (order, token-only-forever rule, issue-thread
  location, near-miss definition, one-reply-never-repeated rule, issue
  #224 parenthetical) — no divergence found.
- `decision-doc-line-citations-current`: `gates/flows.py:131-132` and
  `spawn.py:917` in the decision doc match the actual current line
  content in both files, verified by direct read at commit `144b413`.
- `issue-224-framing-consistency`: "code-side, not fixed/touched here"
  framing and defect ordering (approve-scope mismatch, then pagination
  cap) is identical across `run.md`, `operations.md`, and the decision
  doc.
- `gate-script-line-independence`: no `.sh`/`.py`/`.yml`/`.json` file in
  the repo pattern-matches `run.md` or `operations.md` by line number or
  section anchor (grepped for references to both filenames); the only hit
  is an unrelated docstring comment in `test_spawn.py:2988`. The new
  bullets do not break any gate script.
- `2026-07-29-closed-alternatives-not-reopened`: the warn policy's
  "contains the literal substring `APPROVE`" heuristic decides only
  whether to post a clarifying reply, never approval — confirmed the
  exact-match gate (`gates/flows.py:131-132`) is untouched and remains the
  sole approval decision; the heuristic does not reopen the
  natural-language-parsing class `docs/decisions/2026-07-29-permanently-
  closed-alternatives.md` closed.

## Verification run

Documentation-only change, no test harness applies (same as
issue-54/issue-229/issue-236 precedent, and matching the proposal's own
"How you'll know it worked" section, which is a direct-inspection
checklist, not a test suite). Checked each of that section's five points
directly against the committed diff:

1. `run.md` step 6 and `operations.md` both state the same explicit
   two-comment recipe, "comment A is token-only, no exceptions" spelled
   out in both, plus the warn policy — confirmed (hunt check
   `run-md-operations-md-wording-agreement`).
2. Decision doc cites `gates/flows.py:131-132` and `spawn.py:917` by
   line, quotes both real rsb comment bodies verbatim alongside executed
   (not just inspected) results — confirmed by direct read of
   `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`.
3. Decision doc records the warn-vs-abort-vs-log-only policy decision
   with the tradeoff table — confirmed, present.
4. Issue #224 named as related-but-separate, code-side — confirmed in
   all three changed/new files (hunt check
   `issue-224-framing-consistency`).
5. No new approval syntax anywhere in the diff beyond the existing
   `APPROVE issue-<n>/<role>` token — confirmed by direct read of
   `git show 144b413`; the warn policy is a companion reply, never a
   second approval grammar.

## Open findings

Hunt findings 1-3 above are documented, dispositioned as non-blocking
(two trace directly to design choices already made and approved in
`docs/issue-227/proposals/implementation.md`'s own text; the third is
cosmetic and contextually correct in both spellings). No open findings
require resolution before delivery.

## Next steps

None for this issue. The proposal's own "Out of scope" section already
excludes wiring the warn policy's detection code into the out-of-tree
role-side plugin that actually polls for phase-2 approval — that remains
a different repo's future work, not proposed here.

## Open-finding resolution path

No open findings require resolution; none outstanding.
