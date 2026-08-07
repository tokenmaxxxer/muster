---
proposal: docs/issue-331/proposals/checked-claims-gate.md
---

# Hunt record — checked-claims-gate

## after-proposal — stance 4: proposal-write-set-cannot-carry-this-work

Verdict: FINDING — wiring `record_checked_claims` into `gates/ci.py`'s default (non-`--closes-only`) check list has no effect on the only CI path that actually runs, because that path always invokes `check()` with `closes_only=True`, which skips the entire block the new gate would join.
Kind: design-error
Seed: docs/issue-331/proposals/checked-claims-gate.md (frozen write set: gates/gates.py, gates/ci.py, test_gates.py, gates/test_closes_gate_ci.py, docs/issue-331/decisions/*, docs/issue-331/reports/implementation.md)
cap_seconds: 120
tier: size:21-200-line diff (proposal doc)
diff_stat_lines: n/a (proposal is a new file, ~140 lines)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:02:00Z

### Reproduce
```
cat .github/workflows/plan-aware-closes-gate.yml   # the sole workflow that runs gates/ci.py in CI
# -> run: python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only

grep -n "if not closes_only" gates/ci.py
# 244:    if not closes_only:
# 245-246:        bad = [... is_protected(f) ...]
grep -n "if closes_only" gates/ci.py
# 267:    if closes_only:
#   -> returns early with only the plan-aware Closes gate + phase1-mismatch check

sed -n '229,280p' gates/ci.py
```

### Observed
`gates/ci.py`'s `check()` only runs `record_enums`, `record_wellformed_in`,
`record_no_tool_residue_in`, `record_fulfils_diff` (and, per the proposal,
would run the new `record_checked_claims`) inside the `if not closes_only:`
branch (lines ~244-278). The repository's one GitHub Actions workflow that
invokes `gates/ci.py`, `.github/workflows/plan-aware-closes-gate.yml`, calls
it with `--closes-only` unconditionally — the workflow file has no other
mode and no `--pr ... --autodetect` invocation without that flag anywhere in
the repo (checked spawn.py, `.claude/hooks`, `on-the-record/hooks`: none of
them invoke `gates/ci.py` at all). `check()`'s own docstring/comment
(gates/ci.py ~229-243) even explains *why* `--closes-only` is the only mode
wired as a required check today — a pre-existing `_always_writable()`
proposal-glob mismatch would block every future PR if the full bundle were
required, so issue #245 deliberately narrowed the enforced check to
`closes_only` only. `record_checked_claims` — reading `roles/<role>.json`,
requiring `## Acceptance verification`, cross-checking
`gh pr view --json statusCheckRollup` — would be dead code in CI: it can be
called manually (`python3 gates/ci.py . --pr N --issue M --phase phase2`)
but nothing enforces that call happening, so the "mechanically checked,
not merely asserted" goal in the proposal's own Request section does not
hold under the write set as scoped.

### Expected
The proposal's write set should either (a) include
`.github/workflows/plan-aware-closes-gate.yml` (or a new workflow) so the
non-`--closes-only` bundle — now containing `record_checked_claims` — is
actually invoked by CI on every PR, or (b) explicitly document in "Reach
beyond this proposal's own acceptance criteria" that the new gate, like
the rest of the non-`closes_only` bundle it joins, has no CI enforcement
point today and is advisory-only until a future issue wires it (mirroring
how issue #245's decision doc treats this exact gap for the pre-existing
gates). As written, the proposal presents "wire it into the default check
list" as sufficient without naming or flagging this gap, leaving readers to
believe the check is enforced once landed when it is not.
