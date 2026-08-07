---
status: proposed
files:
  - on-the-record/hooks/orchestrator-state.sh
  - on-the-record/hooks/orchestrator-gate.sh
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/hooks.json
  - tests/run-orchestrator-gates-tests.sh
  - tests/run-orchestrate-tests.sh
  - on-the-record/commands/run.md
---

References #298.

## Request

The orchestrator has 8+ PreToolUse gates constraining role sessions and
exactly one constraining itself (`deliverable-guard`, write-scope only).
Every other procedural obligation it carries — read the proposal before
relaying an APPROVE, verify a PR's checks before merging, give the
no-checks-exist case an explicit recorded path instead of a silent pass —
exists only as prose in `commands/run.md` and cannot fail loudly. Build
the same enforcement surface the house already uses elsewhere
(`execution-observation`'s eo-state read-marker + a consuming gate), and
fix `deliverable-guard`'s own two defects from #287 (fail-open on
unparseable payload; `tests/` plural uncovered) while touching this file
for another reason.

## Constraints

- `on-the-record` has no dependency on the `core` plugin today (survey
  confirmed: no plugin dependency declared, `deliverable-guard.sh` is
  fully self-contained bash+python). New hooks stay self-contained,
  matching `deliverable-guard.sh`'s existing style — no new dependency
  introduced.
- The orchestrator juggles multiple issues/PRs in flight (the mission
  board loop is explicitly multi-flow); the state must be per-subject
  (per issue number for reads, per PR number for checks), not a single
  global marker like eo-state's.
- `gh pr merge <n>` and `gh issue comment ... APPROVE issue-<n>/<role>`
  are the two acts the issue's acceptance criteria names explicitly —
  scope stays to those two, not every conceivable GitHub act (raw
  API/graphql spellings of merge are a plausible hardening follow-up, out
  of this proposal).
- Both gates apply only to the orchestrator's own session
  (`CLAUDE_ROLE` unset) — a role session never runs these Bash commands
  itself (`gh-guard.sh` in `core` already refuses that at the role-gate
  layer); this proposal does not touch role-session gates.
- Marker producer and refusing gate stay two separate hooks (SessionStart
  reset + PostToolUse mark vs. PreToolUse refuse), mirroring eo-state's
  split rather than fusing detection and refusal into one script.

## Rationale

**Chosen approach**: a single per-session JSON state file
(`.claude/.orchestrator-state.json`) written by a new PostToolUse hook
(`orchestrator-state.sh`) on a best-effort substring match against the
raw tool-call payload (Read of `docs/issue-<n>/proposals/`, or a `gh`
Bash call naming that issue/PR), reset at SessionStart. A new PreToolUse
hook (`orchestrator-gate.sh`) reads that file before allowing the two
named `gh` acts.

**Alternative considered and rejected: extend `deliverable-guard.sh`
itself to also cover these two acts.** Rejected because it already
guards a completely different tool surface (Write/Edit/MultiEdit/
NotebookEdit, write-scope) with a different trigger shape (file-path
matching, not Bash-command matching); folding an unrelated Bash-based
refusal into it would make one script responsible for two independently
testable behaviors with no shared logic, breaking the "separate producer/
consumer hooks" pattern the rest of the house already follows and making
the eventual test suite harder to reason about (one file's test failures
would conflate two unrelated defect classes). Fixing `deliverable-guard`'s
own #287 defects stays in that file because those *are* its own logic;
the new enforcement is a new, unrelated concern and gets its own files.

**Alternative considered and rejected: vendor/depend on `core/hooks/lib/
gate-lib.sh`.** Rejected per the Constraints above — `on-the-record` has
no `core` dependency today, and introducing one is a structural decision
bigger than this issue, which the survey's write-set freeze already
ruled out. The *shape* (fail-closed trap, narrowed kill switch,
deny/allow) is adopted directly into the new self-contained scripts
instead.

**Alternative considered and rejected: per-subject marker *files*
(`.claude/.orchestrator-read-<n>` etc.) instead of one JSON file.**
Rejected because the checks-marker needs to carry a *status* (pass/fail/
no-checks), not just presence/absence — a bare file-exists marker (like
eo-state's) cannot distinguish "checks were consulted and passed" from
"checks were consulted and failed," which the merge-gate's acceptance
criteria requires it to distinguish. One JSON file with `reads: {}` and
`checks: {}` keys carries that status cleanly and is still a single
atomic read/write per hook invocation.

## What will be done

- `on-the-record/hooks/orchestrator-state.sh` (new): `SessionStart reset`
  deletes `.claude/.orchestrator-state.json`. `PostToolUse mark` reads
  the tool-call payload from stdin and:
  - on a `Read` of a path matching `docs/issue-([0-9]+)/proposals/`, or a
    `Bash` command matching `gh pr (view|diff) .*<n>` / `gh issue view
    <n>` where `<n>` is extractable from the payload, records
    `reads[n] = now` for that issue number.
  - `orchestrator-state.sh` does NOT record checks-status itself — a
    PostToolUse hook only sees the command line, not `gh pr checks`'s own
    output, so trusting a self-reported result would repeat the "trust
    what the payload claims" gap eo-state accepts as a known limitation
    for read markers, which a merge-safety gate cannot accept for check
    status. Checks-status is instead written by `orchestrator-gate.sh`
    itself at refusal time (next bullet), by re-running `gh pr checks <n>`
    directly rather than trusting an earlier, already-stale observation.
  - Kill switch: `ORCHESTRATE_OFF=1` (same variable `deliverable-guard.sh`
    already uses for this plugin).
- `on-the-record/hooks/orchestrator-gate.sh` (new), `PreToolUse` on
  `Bash`, active only when `CLAUDE_ROLE` is unset:
  - Matches `gh issue comment <n> --body "APPROVE issue-<n>/<role>"`
    (via the same exact-string convention `approval-gate.sh` reads back
    on the role side). Denies unless `.claude/.orchestrator-state.json`
    has a `reads[n]` entry from this session.
  - Matches `gh pr merge <n>`. On match, runs `gh pr checks <n>` itself
    (fail-closed on a `gh` invocation error — same "cannot check = deny"
    posture `approval-gate.sh` already uses) and classifies the result:
    any check not in a passing/neutral conclusion -> deny ("checks are
    failing"); `gh pr checks` reporting no checks configured for this PR
    (distinct exit/stderr shape, confirmed live during survey) -> the
    **explicit exemption path**: write `checks[n] = {status: "no-checks",
    at: now}` to the state file and allow the merge, so the exemption is
    a recorded fact rather than a silent pass; all checks passing ->
    write `checks[n] = {status: "pass", at: now}` and allow.
  - Fail-closed trap (non-0/2 exit remapped to 2), kill switch
    `ORCHESTRATE_OFF=1`.
- `on-the-record/hooks/deliverable-guard.sh` (edit): the embedded python's
  `except ValueError: sys.exit(0)` becomes `deny(...)`; non-dict payload
  and missing/non-string `file_path`/`notebook_path` become `deny(...)`
  instead of `sys.exit(0)`; the path regex changes from
  `(^|/)(src|test|docs)/` to `(^|/)(src|tests?|docs)/` and the bash
  prefilter's `*test/*` becomes `*test*` (covers both `test/` and
  `tests/`).
- `on-the-record/hooks/hooks.json` (edit): add `SessionStart ->
  orchestrator-state.sh reset` (alongside the existing `self-update.sh`
  entry), `PostToolUse(Read|Bash) -> orchestrator-state.sh mark`, and
  `PreToolUse(Bash) -> orchestrator-gate.sh` (alongside the existing
  `PreToolUse(Write|Edit|MultiEdit|NotebookEdit)` entry for
  `deliverable-guard.sh` — both stay as separate matcher entries under
  the same hook-event arrays).
- `tests/run-orchestrator-gates-tests.sh` (new): mirrors
  `tests/run-orchestrate-tests.sh`'s harness shape (temp `git init`
  fixture, stdin JSON payload, exit-code assertion via a `report()`
  helper) for the two new hooks — covers: APPROVE denied with no read
  marker, allowed with one; merge denied with no checks-query marker,
  denied when `gh pr checks` (faked via a `CORE_GH`-equivalent
  seam/stub) reports failing, allowed and recorded when it reports
  passing, allowed-with-recorded-exemption when it reports no checks;
  role-session pass-through (`CLAUDE_ROLE` set -> both gates no-op);
  kill switch.
- `tests/run-orchestrate-tests.sh` (edit): add two `guard` cases for the
  `deliverable-guard.sh` fix — a malformed-JSON payload now denies
  (previously allowed), and a `tests/` (plural) board-repo write now
  denies (previously allowed).
- `on-the-record/commands/run.md` (edit): append one short parenthetical
  to each of the four obligations already listed in step 5 and step 6
  (read-before-approve, checks-before-merge) noting each is now
  mechanically enforced by `orchestrator-gate.sh`, not just this
  document's prose. No procedural change to the steps themselves.

## Out of scope

- Raw REST/GraphQL spellings of merge/approve (`gh api .../merge`,
  GraphQL `mergePullRequest`) — `gh-guard.sh`'s pattern for this exists
  on the role side; extending the new orchestrator gate to the same
  breadth is a follow-up, not required by this issue's acceptance
  criteria.
- "Re-read the board after a merge" and "relay only what the user said"
  from the issue body's obligation list — these are not independently
  checkable against an artifact the way "was this file read" or "was
  this command run" are (there is no marker for "the board was
  re-read *correctly*" or "this text matches what the user actually
  said" without a much larger natural-language-verification build). Per
  the issue's own fix direction ("whatever remains unenforceable must at
  minimum be *recorded*"), these stay prose-only in this proposal; a
  future issue could add a recorded-but-unverified checkpoint for them if
  wanted.
- Depending on/vendoring `core/hooks/lib/gate-lib.sh` (see Rationale).
- Changing any role-session gate (`core`, rulebooks) — out of this repo's
  write reach and out of the issue's stated scope (orchestrator only).

## How you'll know it worked

- `tests/run-orchestrator-gates-tests.sh` passes: an APPROVE comment
  attempt with no proposal read this session is denied (exit 2); after a
  `Read` of that issue's proposal file, the same comment is allowed.
- The same suite: a `gh pr merge <n>` attempt with checks never queried
  is denied; with `gh pr checks` faked to report a failing check, denied;
  with it faked to report all-passing, allowed and `checks[n].status ==
  "pass"` in the resulting state file; with it faked to report no checks
  configured, allowed and `checks[n].status == "no-checks"` — the
  exemption is on disk, not silent.
- `tests/run-orchestrate-tests.sh`'s existing `guard` cases still pass,
  plus the two new ones: malformed payload denies, `tests/`-plural board
  write denies.
- Both new gates no-op (exit 0 immediately) when `CLAUDE_ROLE` is set,
  confirming they never touch role sessions.
- `ORCHESTRATE_OFF=1` disables both new hooks; any other value (including
  a typo) leaves them active.
