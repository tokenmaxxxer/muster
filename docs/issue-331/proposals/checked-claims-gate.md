files:
- gates/gates.py
- gates/ci.py
- .github/workflows/plan-aware-closes-gate.yml
- test_gates.py
- gates/test_closes_gate_ci.py
- docs/issue-331/decisions/2026-08-07-checked-claim-marker.md
- docs/issue-331/reports/implementation.md

## Request

The operator observes that roles frequently report success without
having completed what was asked, and nothing independently checks the
claim — a silent failure the operator can only catch by re-deriving the
work themselves. Per #310, an acceptance criterion must already name an
executable artifact; #331 adds the missing second half — that the
record's *claim* of having satisfied that artifact is itself checked
mechanically, not merely asserted in prose, before a record can declare
a terminal `loop_state`.

## Constraints

- No re-execution of arbitrary repository commands inside the gate.
  `gates/gates.py` functions are pure, diff-only, and run inside a
  PreToolUse hook and a CI job with no execution sandbox contract — a
  gate that shells out to whatever a record's prose names would turn a
  record write into an arbitrary-command trigger.
- Must follow the existing opt-in-marker, fail-closed-on-parse-failure
  shape already established by `record_fulfils_diff`
  (`gates/gates.py:411-462`) — no new marker syntax invented from
  scratch where an existing one already fits the shape.
- Must not weaken `record_fulfils_diff`, `record_wellformed`,
  `record_no_tool_residue`, or `record_enums` — additive only.
- Must read the terminal `loop_state` value from `roles/<role>.json`
  (`record_fields.loop_state`), never hardcode `"landed"` — confirmed in
  the survey that the terminal value differs from role to role in
  principle even though several currently share the string.
- Per #310, where a criterion is genuinely unverifiable, the record must
  say so and say why; the gate must accept that explicit declaration as
  satisfying the check for that one criterion, not force a `pass`.

## Rationale

**Re-running the check inside the gate vs. cross-checking an
independently-produced result.** Considered having the gate itself
execute the named test/command from a `checked:` line (e.g. `subprocess.run`
on the referenced pytest node ID) so the gate's own run is the evidence.
Rejected: `gates/gates.py`'s existing functions are all pure and
diff-only — none of them execute repository code, and the file's own
CI entry point (`gates/ci.py`) explicitly avoids anything beyond `gh`
read calls and local diff inspection. Executing an arbitrary string
pulled from record prose inside a PreToolUse hook or CI job is a command
-injection surface (a malformed or adversarial `checked:` line becomes
an arbitrary-command trigger) and duplicates work the PR's own CI
already did. The chosen design instead requires the `checked:` line to
name either (a) a test node ID that the gate verifies *exists* in the
referenced test file by parsing, not executing, it (mirrors
`record_fulfils_diff`'s diff-existence check — falsifiable without
execution: a claim naming a test that isn't in the file is caught), or
(b) a CI check name that `gates/ci.py` cross-checks against
`gh pr view --json statusCheckRollup` (an independently-executed result
already produced by the PR's own CI, not re-run by the gate). Both give
mechanical falsifiability without adding an execution surface to the
gate itself.

**A blanket "no terminal loop_state without a checked: line" rule vs.
requiring the marker only when completion language is present.**
Considered gating on the mere presence of a terminal `loop_state`
value, requiring every such record to carry the marker section
unconditionally. Rejected as the primary trigger, though kept as the
structural backstop: `loop_state: landed` is itself already the
system's terminal-completion signal (protocol v3's phase-2 record is
"phase-2 output like code"), so tying the requirement to that
frontmatter field — rather than scanning prose for "완료"/"성공"/"done"
language, which is fragile against paraphrase and easy to route around
by simply not using the flagged words — makes the gate un-gameable by
wording choice. The frontmatter field is the actual claim the rest of
the system (spawn/board reads it to decide the subject is finished);
checking it structurally is the falsifiable target, not the prose next
to it.

## What will be done

- **`gates/gates.py`**: add `record_checked_claims(d, cfg)`, registered
  in `ALL`. For each changed phase-2 record whose new content sets
  frontmatter `loop_state:` to that role's declared terminal value (read
  from `roles/<role>.json` via the same lookup `record_enums` already
  uses), require a `## Acceptance verification` section with one line
  per item, shaped `- <criterion excerpt> — checked: <test-node-id |
  gate-script-path | ci-check-name> — result: pass|fail|unverifiable:
  <reason>`. Parse failure (section present but no parseable lines, or
  a `result:` value outside the three) is a denial, same fail-closed
  posture as `record_fulfils_diff`'s unknown-`kind` branch
  (`gates/gates.py:459-461`). A terminal `loop_state` with **no**
  `## Acceptance verification` section at all is also a denial — this
  is the mandatory case, unlike `record_fulfils_diff`'s opt-in-only
  marker, because reaching the terminal state is exactly the claim
  #331 says must not go unchecked.
  For `result: pass` lines naming a test-node-id (`path::test_name`
  shape), verify the named test actually exists in the referenced file
  (parse the file's `def test_name` occurrences — no execution).
  Existence-only, not correctness — matches what a diff-based gate can
  falsify without running code.
- **`gates/ci.py`**: wire `record_checked_claims` into the default
  (non-`--closes-only`) check list. Add one more `gh` read next to the
  existing `_pr_reviews`-shaped helpers: `_pr_status_checks(repo, pr)`
  reading `gh pr view --json statusCheckRollup`. For `result: pass`
  lines naming a CI check (not a test-node-id — determined by the
  absence of `::`), require that check to appear in the rollup with a
  passing conclusion; a named check that is missing, pending, or
  failing in the rollup is a denial, with the mismatch reported by
  name so the role can see exactly which claim didn't hold up.
- **`.github/workflows/plan-aware-closes-gate.yml`**: the warrant hunt
  on this proposal (docs/reports/2026-08-07-hunt-checked-claims-gate.md)
  found that this workflow is the repo's only CI caller of
  `gates/ci.py`, and it always passes `--closes-only`
  (`.github/workflows/plan-aware-closes-gate.yml:49`) — the flag that
  skips the entire `if not closes_only:` block
  (`gates/ci.py:244`) the new gate would join. Without editing this
  workflow, wiring the gate into `gates/ci.py`'s default check list has
  no effect on any PR: the new gate would exist and pass unit tests but
  never run in CI, reproducing the exact self-report problem #331
  names. Add a second step to the same job invoking
  `python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect` (no
  `--closes-only`), so the full non-closes-only check list — including
  the new gate — actually runs and reports a named GitHub check on
  every PR. As with `--closes-only`'s own precedent
  (`.github/workflows/plan-aware-closes-gate.yml`'s comment,
  documented in `docs/issue-245/reports/implementation.md`), a reported
  check does not by itself block a merge until it is registered as a
  required status check under Settings > Branches — that registration
  is a manual GitHub-side action this proposal does not perform (see
  Out of scope), matching how #245 left the same step manual for the
  closes-gate check it added.
- **`docs/issue-331/decisions/2026-08-07-checked-claim-marker.md`**:
  records the `checked:`/`## Acceptance verification` convention as a
  contract surface (doctrine ladder: a changed record format is a
  library-or-format choice over a named alternative).
- **`test_gates.py`**: unit tests for `record_checked_claims` — accepts
  a well-formed section, denies a terminal `loop_state` with the
  section missing, denies an unparseable line, denies a `pass` line
  naming a nonexistent test.
- **`gates/test_closes_gate_ci.py`**: CI-context tests for the
  `statusCheckRollup` cross-check — passing rollup accepted, failing/
  pending/missing rollup denied, network-call shape following the
  file's existing `_pr_reviews` test doubles.

## Out of scope

- No change to how issues are authored or how their acceptance criteria
  are worded (#310's territory).
- No impact/regression analysis of what a change reaches beyond its own
  record (#330's territory) — this proposal's own such statement is in
  this document's closing note per today's #330 constraint, not a
  mechanism this proposal builds.
- No change to `gates/ci.py`'s phase-detection logic (#312, #245).
- No registration of the new check as a required branch-protection
  status check (a manual GitHub Settings action, not a repo write —
  same boundary #245 already drew for the closes-gate check).
- No gate that re-executes tests, gate scripts, or shell commands named
  in a record — evidence comes from parse-time existence checks and
  independently-already-run CI results only (see Rationale).
- No retroactive check of records already on `main` with a terminal
  `loop_state` and no `## Acceptance verification` section — this
  proposal is a write-time gate on new writes, not a sweep of history
  (a sweep, if wanted, is a separate unit — `gates/closure_sweep.py`'s
  shape, not this one).
- Non-`implementation` roles are in scope structurally (the gate reads
  `roles/<role>.json` generically, same as `record_enums`), but this
  session verifies against `implementation`'s record surface only —
  the other 42 role definitions are not individually exercised in this
  build.

## How you'll know it worked

- `python3 -m pytest test_gates.py -k record_checked_claims -q` — new
  unit tests pass, and (regression target) fail if the gate is removed
  or its fail-closed branches are loosened: a record setting the
  terminal `loop_state` with no `## Acceptance verification` section,
  or with a `pass` line naming a nonexistent test, must be denied.
- `python3 -m pytest gates/test_closes_gate_ci.py -k checked_claims -q`
  — new CI-context tests pass; a `pass` line naming a CI check absent
  or failing in `statusCheckRollup` must be denied.
- `python3 gates/gates.py` / `python3 gates/ci.py` continue to exit 0 on
  the existing test suite's fixtures with no `checked:` markers present
  (non-terminal records untouched — regression check that the new gate
  is additive, not a new blanket requirement on every record write).

## Reach beyond this proposal's own acceptance criteria (per #310/#330)

This is a phase-1 proposal only — no code lands this session, so
nothing on disk is invalidated yet. Once built, the gate's *scope* of
effect: any phase-2 record across all 43 roles that sets its role's
terminal `loop_state` value gains a new hard requirement it did not
have before (`## Acceptance verification` with parseable lines) — a
role that reaches its terminal state today with a bare prose claim will
be blocked by this gate once wired, until it adds the section. That is
the intended effect (closing exactly the hole #331 names), but it is a
behavior change for every role, not only `implementation`, and is
flagged here so phase-2 approval is made with that reach in view.
