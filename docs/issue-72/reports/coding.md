# Coding record — issue-72

loop_state: landed

## What was done
Executed the approved phase-1 proposal (`docs/issue-72/proposals/coding.md`),
built on the phase-1 survey (`docs/issue-72/reports/coding/survey.md`),
flipping the sandbox posture from default-deny (opened one switch at a time
across #38/#58/#65/#69) to default-open for every remaining restriction
switch the sandbox schema exposes, minus `allowGitConfig` (dropped — not a
real settings-writable schema field, per the survey) and `allowPty`
(explicitly excluded from this approved scope even though an earlier draft
proposal mentioned it):

- `spawn.py`: added two module-level constants right after
  `WEB_ACCESS_DOMAINS = ["*"]` (around line 72) —
  `SANDBOX_OPEN_NETWORK = {"allowAllUnixSockets": True, "allowLocalBinding":
  True, "allowMachLookup": ["*"]}` and `SANDBOX_OPEN_TOP_LEVEL =
  {"enableWeakerNetworkIsolation": True, "allowAppleEvents": True,
  "enableWeakerNestedSandbox": True}`. Extended the existing merge block in
  `role_settings()` (the `if sb0 := s.get("sandbox", {}): if
  sb0.get("enabled"):` block, originally spawn.py:353-365) with two more
  additive/no-clobber loops right after the `WEB_ACCESS_DOMAINS` merge,
  reusing the already-bound `net` variable — `sb0["enabled"]` and
  `sb["allowUnsandboxedCommands"] = False` (near the former spawn.py:412)
  are untouched.
- `test_spawn.py`: added a new `SandboxDefaultOpenAccess` test class (mirrors
  the `WebToolPermissionAccess`/`PackageRegistryAccess` style) with two
  tests: `test_open_switches_set_for_every_sandboxed_role` (checks all six
  opened keys plus `sandbox.enabled is True` and
  `sandbox.allowUnsandboxedCommands is False` for every `roles/*.json` with
  `sandbox.enabled`) and `test_role_declared_values_not_clobbered` (same
  no-clobber pattern as the issue-38/58 tests: a role's own explicit
  `enableWeakerNetworkIsolation`/`allowLocalBinding` values survive the
  merge).
- `README.md`: in `## Isolation — a sandbox, not a container`, deleted the
  "Trade-off, explicit:" paragraphs under "Package-registry access (issue
  #38)" and "Web access (issues #58, #65)" (kept the numbered mechanism
  descriptions above them), and added a new `### Default-open posture (issue
  #72)` subsection right after "Web access" stating the posture: every
  switch open except `filesystem.allowWrite`/`denyWrite` and the
  board-gate/gh-guard hooks, naming all six opened keys, and explaining why
  the sandbox stays `enabled: true` and `allowUnsandboxedCommands` stays
  `false` regardless (headless Bash auto-allow depends on the sandbox
  existing, not on its internal switches).
- `README.ko.md`: checked via `grep -n "Trade-off\|Isolation"` — zero
  matches, no equivalent Isolation section exists in the Korean translation
  to mirror. Skipped, per the task's own fallback instruction.
- `roles/*.json` — untouched, out of scope per the approved proposal.

## Why
Upstream basis: issue #72 + approved proposal `docs/issue-72/proposals/coding.md`
+ phase-1 survey `docs/issue-72/reports/coding/survey.md`. The survey
enumerated the full sandbox-schema restriction-switch inventory (grepped
from the installed CLI binary's zod schema) and classified every switch
against the issue's three keep-reasons (headless Bash auto-allow, workspace
write scoping, rulebook/gate separation). None of the opened switches serve
any of the three reasons, so all were cleared to open — merged at the same
site and in the same additive/no-clobber shape as the #38/#58 precedents,
applied uniformly to every sandboxed role (no per-role opt-in).

## What did not work
Nothing reverted. No deviations from the approved proposal — `allowPty` was
intentionally left out (excluded from the approved scope), and
`allowGitConfig`/`allowRead`/`denyRead`/`ignoreViolations`/
`mandatoryDenySearchDepth`/`tlsTerminate` were left untouched as instructed.

## Verification
```
$ python3 -m pytest test_spawn.py -v
...
56 passed in 3.29s
```
56/56 pass, including the two new `SandboxDefaultOpenAccess` tests and all
54 pre-existing tests (unaffected).

## Closed checks
- closed_checks: sandbox-open-switches-merged (verified via
  `role_settings(role)` output for every `roles/*.json` with
  `sandbox.enabled` — all six keys present with the expected open values,
  `sandbox.enabled`/`allowUnsandboxedCommands` untouched).
- closed_checks: no-clobber (role-declared values for
  `enableWeakerNetworkIsolation`/`allowLocalBinding` survive the merge,
  verified by `test_role_declared_values_not_clobbered`).
- closed_checks: no-scope-creep (diff touches only `spawn.py`,
  `test_spawn.py`, `README.md`, this record file — `roles/*.json`,
  `allowPty`, `allowGitConfig`, `allowRead`/`denyRead`, `ignoreViolations`,
  `mandatoryDenySearchDepth`, `tlsTerminate` all untouched, per the approved
  scope).

## Hunt
warrant-hunter not dispatched: change is a same-shape extension of the
already-landed, already-tested merge block (issues #38/#58), with new tests
asserting both the merge and the no-clobber property directly.

## Open findings
None.
