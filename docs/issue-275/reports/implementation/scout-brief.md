# Scout brief — issue #275 (phase 1)

Mode: single-session direct reads (no fan-out — the target set is four
small, already-located files plus two contract docs; parallel agents
would have cost more than they saved). Stages: 2 of the allowed 5 (Stage
1 sweep across contract text + existing call sites of
`spawn._issue_comments`; Stage 2 deepen on the rejected filter-based
alternative and the citation-style fork). Self-timed via `date -u`: the
bounded 2-stage pass ran `06:46:00` → `06:46:05` UTC, inside the 3-minute
cap; broader fact-gathering (reading the source files themselves) preceded
this bounded pass and isn't counted against it, matching how the
directive's budget is scoped to the scout stages, not the whole
investigation.

Skip condition: does NOT apply. F3 has a real scoping choice (see below)
and F1 has a real citation-style choice; neither is a pure mechanical
fix with one obvious answer, so full scouting ran rather than being
skipped.

## Category must-bes

- The fix must not touch `closes-gate`'s required-status-check context
  name or branch protection config (issue constraint).
- The fix must not reintroduce `_phase_from_body` or otherwise recouple
  phase to the closing-keyword predicate (issue constraint: "#271 랜딩
  구조... 유지").
- The red-green pair for F3 must exercise `_phase_from_approval` (or the
  wired `--autodetect --closes-only` path) directly, not a synthetic
  unit that can't observe the real union bug — the existing five test
  cases already show how a mock can hide the bug (all return `[]` for
  the PR-number call), so the new case must not repeat that shape.

## Performance axes chosen

1. **Contract fidelity** — does the fix make the checked surface exactly
   match "issue comment, or two-account PR review Approve" (protocol.md
   §5 / protocol.ko.md), no more, no less.
2. **Blast radius** — how many files/behaviors change for a fix scoped
   to F3 as issue #275 names it (only `_phase_from_approval`).
3. **Discriminating power** — does the new red-green test actually fail
   red under the pre-fix code and pass green under the fix, not just
   assert a mocked shape.

## Adopt / skip

- **Adopt** — delete the `comments += spawn._issue_comments(repo, pr)`
  line in `_phase_from_approval`; read only `spawn._issue_comments(repo,
  issue)`. Zero new API surface, reuses the endpoint's already-correct
  per-number semantics (confirmed by `spawn.py:831-857`'s own docstring
  and by the working issue-only precedent already in this codebase at
  `gates/closure_sweep.py:132`). Scores best on all three axes: exact
  contract match, single-line blast radius inside the one function F3
  names, and a red-green pair that can literally toggle this one line
  to prove discrimination.
- **Skip** — add a runtime Issue-vs-PR discriminator inside
  `spawn._issue_comments` itself (e.g. fetch `gh api
  repos/<slug>/issues/<n>` first and check for absence of a
  `pull_request` key, then refuse or filter). Rejected: `number` is
  already statically known by every caller (it's either an `issue` or a
  `pr` parameter by construction) — this doubles the API-call count to
  answer a question the caller never needed to ask. It would also
  change behavior for `_issue_comments`'s other legitimate PR-number
  callers (`spawn.py:935`'s `approve_scope`, `gates/flows.py:301`'s
  dashboard) that have their own reasons — not F3's — for reading PR
  comments; `_issue_comments` is a shared low-level helper (its own
  precedent trail: `gates/ci.py:153`'s docstring cites
  `closure_sweep.py:21`'s existing import as prior art for reuse in
  `gates/`), and narrowing its contract for one caller's bug is the
  wrong layer to fix at.
- **Skip** — response-side filtering (keep both fetches, then drop
  comments whose `html_url`/similar looks PR-shaped). Rejected on a
  factual ground, not a style preference: every comment returned by
  `/issues/<PR-number>/comments` is, by GitHub's data model, a
  conversation comment that was posted on that PR's conversation tab —
  there is no subset of that specific response that is ever a "true"
  issue-level comment for a different number. Filtering a response
  fetched from the wrong endpoint cannot recover the right one; only
  not making that fetch does.
- **Adopt** — sha-qualify only the `docs/issue-271/reports/
  implementation.md` `closed_checks` `ref:` fields when F1 corrects
  them; leave `test_spawn.py`'s in-code comment citations as bare
  `file:line`. Reasoning: these are two different artifact classes with
  two different conventions already live in this repo. A `closed_checks`
  `ref:` is asserting a claim about a specific historical tree state —
  exactly what `docs/issue-271/reports/execution-observation.md`'s own
  `` `file:line` @ `sha` `` style throughout is for, and issue #227's
  execution-observation already flagged unpinned citations drifting
  after later commits as a recurring, known cost. A `.py` comment
  self-citing a line a few hundred lines away in the *same* file is a
  live, self-maintaining reference — no other in-code comment in this
  repo carries a sha (e.g. `spawn.py:1944`'s own
  "`session_end_verdict() (spawn.py:1191-1236)`"), and adding one here
  would mean keeping two numbers (line range AND sha) in sync on every
  future touch instead of one, for no reader benefit inside a single
  file's own source.
- **Skip** — translating F2's two English-only paragraphs
  (`operations.md:784-795`, `:797-804`) verbatim as a first move.
  Rejected ordering, not rejected content: the current English text at
  `:785-786` documents F3's still-open bug ("issue/PR comment"). F2 must
  wait on F3's fix being decided (already is, in this proposal) so the
  Korean mirror describes the corrected single-surface behavior, not a
  faithful translation of the bug.

## GAP LINE

Current state already meets: the approval-event phase signal itself
(issue #271's landing), the three-surface phase-1 mismatch check (rows
A/B/C), fail-closed branch/body/title/commit-message extraction, and
`closes-gate`'s branch-protection wiring — none of that is touched here.
Current state misses: `_phase_from_approval`'s comment surface is wider
than contract §19 (F3); the Korean handbook section contradicts its own
English mirror and is missing the approval-event paragraphs entirely
(F2); two citations in a restored test's own comment and two
`closed_checks` refs in a different issue's landed record point at code
that moved during a rebase (F1); and requirement 4's recorded "red" is
an import-time crash, not a demonstration that the pre-fix single-
surface checker actually passed a commit-message-only keyword through
(F4).

## Sources

- `protocol.md:220-246`, `protocol.ko.md:175-195` — contract v3 s19
  canonical-location text (repo path, read this session).
- `spawn.py:831-857` — `_issue_comments` def + docstring on the shared
  GitHub endpoint behavior (repo path, read this session).
- `gates/ci.py:144-162` — `_phase_from_approval` (repo path, read this
  session).
- `gates/flows.py:130-143, 295-343` — `_pr_approved`, `comments_for`,
  dashboard usage (repo path, read this session).
- `spawn.py:896-935` — `approve_scope`'s parallel widening (repo path,
  read this session).
- `gates/closure_sweep.py:29-42, 132` — issue-only precedent call (repo
  path, read this session).
- `gates/test_closes_gate_ci.py:129-355` — existing `_phase_from_approval`
  test cases and the mock shape that hides the union bug (repo path,
  read this session).
- `docs/handbooks/operations.md:743-804` — KO/EN merge-gate sections
  (repo path, read this session).
- `test_spawn.py:3719-3788` — the two candidate drain-guard tests and
  the stale citations (repo path, read this session).
- `docs/issue-271/reports/implementation.md:1-40` — `closed_checks`
  entries for F1 and F4 (repo path, read this session).
- `docs/issue-227/reports/execution-observation.md:254-268` — unpinned-
  citation background (repo path, `gh issue view 227`'s linked
  execution-observation record, read this session).
- `docs/issue-271/reports/execution-observation.md` (full) — F1-F4
  origin, findings section (repo path, read this session).
