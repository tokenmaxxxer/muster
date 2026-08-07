# Survey — issue-427

## Reproduction (offline, no network)

`gates/test_closes_gate_ci.py::t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
(added by #312, `92fb470`) fails deterministically with no network access —
reproduced by running it both at `HEAD` and at the exact commit it was
merged in (`3e30386`), in a scratch worktree, offline:

```
AssertionError: ["이슈 #304 본문에 '## Acceptance' 절이 없다 — 수용기준 없이는
실행가능성을 검사할 수 없고, 검사 불가는 통과가 아니다."]
```

This matches the CI failure text in the issue exactly.

## Mechanism (corrects the issue's framing on one point)

The test does not call `gh` at all — every function `ci.check()` reaches
(`pr_reference._pr_view`, `pr_reference._issue_view_body`, `ci._pr_head_ref`,
`ci._pr_title`, `ci._pr_commit_messages`, `spawn._approvers`,
`spawn._issue_comments`, `ci._pr_reviews`) is monkeypatched to a fixed
lambda before the call. The failure is **not** a live GitHub fetch reaching
into the test; it is a stale/incomplete *local* fixture.

Trace: `pr_reference.check()` (`gates/pr_reference.py:86-107`), for
phase2 + a matching `Closes #<issue>`, calls
`acceptance_gate.check_issue_body(issue, issue_body)` at line 106, where
`issue_body` is exactly the string returned by the stubbed
`pr_reference._issue_view_body` — `"no plan checklist here"`. That string
has no `## Acceptance` heading, so `acceptance_gate.check_issue_body`
(`gates/acceptance_gate.py:34-52`, added by #310, `e90e079`) always
returns the "no Acceptance section" finding for this test, unconditionally
of anything on GitHub.

`e90e079` (#310) predates `3e30386` (#312's merge) by commit graph
position and by wall-clock timestamp (`2026-08-07 14:18` vs `17:00`).
#312's test was therefore born already red against `acceptance_gate`'s
rule — it was not broken *later* by #310 landing "afterwards" as the
issue narrates. What *is* accurate in the issue's framing: the test's
stub body was chosen to model issue #304's real shape at the time (a
plain-prose issue with no Acceptance section, predating #310's rule), so
the same failure *would* recur if the stub were replaced by a genuine
live `gh issue view` call today — the class of defect (mutable external
state silently driving a shape-pinning test) is real, just not yet
literally reached over the network by this specific test today.

## Item 1 trap (#335) — how a recorded fixture is kept from drifting

A frozen string fixture for `_issue_view_body`/`_pr_view` is what this
test already uses — recording once already happened. The #335 risk
(a fake whose shape or content silently diverges from the real interface
and keeps passing while meaning nothing) applies here on two axes:

- **Shape**: the boundary being stubbed is `gh issue view --json body`
  reduced to a single string (module functions `_issue_view_body`/
  `_pr_view` already narrow the JSON envelope down to `data.get("body")`
  before returning). A plain string has no internal shape to drift from —
  this axis is not where #427's bug lives.
- **Content**: an issue body's *content* is not owned by this test and
  changes independently as new gates are added (#310 today, the next
  body-shaped gate tomorrow) — this is the axis that broke. Keeping a
  "realistic" recorded body correct against every unrelated present-and-
  future gate is not tractable (that is precisely the treadmill #427
  names: "every new gate that constrains issue bodies is another way for
  this fixture to go stale").

The fix that avoids re-trading one problem for the other: stop routing
this test's assertion through `acceptance_gate` at all. The test's own
purpose (per #312's docstring) is pinning the *cross-role phase-detection*
shape — whether `_autodetect_issue_phase` correctly resolves role-blind
approval to `phase2` and whether `ci.check` then reaches the closing-
keyword branch, not whether issue #304's body satisfies an unrelated,
independently-evolving content gate. Stubbing
`acceptance_gate.check_issue_body` itself (already an importable,
network-free pure function — see `gates/acceptance_gate.py:34`) to a
fixed `[]` for the duration of this one test scopes the pin to what #312
actually wanted checked, and makes the test immune to every future
Acceptance-shaped (or any other body-content-shaped) gate by
construction — not because the fixture happens to satisfy today's rules,
but because content-shaped gates are structurally out of this test's
reach. `assert bad == []` for a test that also wants to observe that
`acceptance_gate` genuinely fires needs a **second**, separate test:
same phase2/Closes/#304 shape, `acceptance_gate.check_issue_body` left
un-stubbed and fed a fixture body that deliberately lacks `## Acceptance`,
asserting the finding text is present — this is the regression pin
`427`'s acceptance criterion 2 asks for ("fails if the fixture reverts to
a live fetch"), reframed as "fails if this test starts depending on
`acceptance_gate`'s content rule again."

## Item 2 — suite-wide scan for live-GitHub-reading tests

Searched (`grep -rln`) across `gates/test_*.py` for:

- `gh issue view` / `gh pr view` / `subprocess.run(["gh"` literal strings
  — zero hits anywhere in any test file.
- `_issue_view_body` / `_pr_view` / `_pr_head_ref` (the module-level
  functions that wrap the `gh` subprocess calls) — hits only in
  `gates/test_closes_gate_ci.py`; every call site monkeypatches all of
  them to fixed lambdas before invoking `ci.check`/`pr_reference.check`/
  `ci._autodetect_issue_phase` (9 call sites, lines 322, 334, 348, 378,
  425, 585, 605, 711(the one under repair), 745 — each wrapped in a
  try/finally that restores the original).
- `import requests` / `urlopen` / `httpx` / bare `gh ` invocations
  anywhere else in `gates/test_*.py` — zero hits.
- `gates/test_orphaned_references.py` uses `subprocess.run(["git", ...])`
  against a throwaway `tempfile.TemporaryDirectory()` — local git, not
  GitHub, out of scope for this dimension.

Result: **no test in this suite currently reaches the network at
runtime.** The one test #427 opens against is locally stubbed but with
stale *content*, not a live call — see Mechanism above. This is the list
item 2 of #427 asks for; it is empty for literal live calls, and the one
near-miss (content drift on a local stub simulating a since-changed
external contract) is the subject of item 1's fix.

## #367 note (to be posted, not filed as a new issue)

#367's scan searched filesystem paths outside a tmp/fixture root and
correctly found (and fixed) one instance, reporting the list as empty
otherwise. It did not search for network-fetched state (`gh`/GitHub API
calls, or stubs standing in for them) as a separate shape — that
dimension existed and this issue (#427) is what surfaced it, by a
different route than #367's own instance. Recorded as a comment on #367
per #427's Boundary section ("worth recording there"), not as new scope
on #367 itself (#367 is closed and its own acceptance already
discharged for what it searched).

## Write set

- `gates/test_closes_gate_ci.py` — stub `acceptance_gate.check_issue_body`
  in the #312 shape-pin test; add one new test asserting
  `acceptance_gate.check_issue_body` still fires when a phase2/Closes PR's
  issue body genuinely lacks `## Acceptance` (the item-1 regression pin).
- `docs/issue-427/reports/implementation/survey.md` (this file)
- `docs/issue-427/proposals/2026-08-07-isolate-fixture-from-acceptance-gate.md`

## Scout skip record

Skipped per scout-directive's "pure bugfix" condition: the defect,
its mechanism, and the shape of the fix (isolate a shape-pinning unit
test from an unrelated content gate by stubbing the gate's pure
function) are fully determined by reading this repo's own code — no
external category or best-in-class product bears on a repo-internal
test-isolation fix.
