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

## before-landing — stance: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `result: unverifiable: <any non-empty text>` (and likewise `result: fail`) claims are accepted with zero verification, so a session can fabricate an entire `## Acceptance verification` section that proves nothing and still cross a terminal `loop_state`.
Kind: silent-failure
Seed: `gates/gates.py:record_checked_claims` (and its CI mirror `gates/ci.py:_checked_ci_claims_bad`)
cap_seconds: 180
tier: default
diff_stat_lines: (per dispatcher: default tier, >200 lines / >5 files)
started_at: 2026-08-07T14:20:17+09:00
ended_at: 2026-08-07T14:33:00+09:00

### Reproduce
`gates/gates.py` lines ~589-601:
```python
for ln in lines:
    cm = _CHECKED_CLAIM_LINE.match(ln)
    ...
    target, result, reason = cm.group(1), cm.group(2), cm.group(3)
    if result == "unverifiable" and not (reason and reason.strip()):
        bad.append(...)
        continue
    parsed.append((target, result))
for target, result in parsed:
    if result != "pass" or "::" not in target:
        continue          # <-- unverifiable and fail claims never reach the
                            #     existence/definition check below at all
    ...
```
Same structural gap in `gates/ci.py:_checked_ci_claims_bad` (line 147-148):
```python
claims = [(f, target) for f, target, result, _ in gates.parse_checked_claims(repo)
          if result == "pass" and "::" not in target]
```
— only `result == "pass"` claims are cross-checked against `statusCheckRollup`; `unverifiable`/`fail` claims are never looked at again anywhere in the pipeline.

Concretely, invoking `record_checked_claims` on a terminal-`loop_state` record whose entire acceptance section is:
```
## Acceptance verification

- everything works — checked: nothing-real — result: unverifiable: trust me bro
```
returns `[]` (no findings) regardless of whether "nothing-real" refers to anything, and regardless of whether the claim is true. I reproduced this directly against the gate function (monkeypatching `changed_files` to avoid needing a live git/PR harness, since the check under test only touches the record text and role config):

```python
import sys
from pathlib import Path
sys.path.insert(0, "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-331-implementation")
import gates.gates as g

REL = "docs/" + "issue-999" + "/reports/defect-verification.md"
root = Path("/tmp/claude-1000/gt3/fakework")
target = root / REL
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(
    "---\nloop_state: cleared\n---\n\n## Acceptance verification\n\n"
    "- everything works — checked: nothing-real — result: unverifiable: trust me bro\n"
)
g.changed_files = lambda work: [REL]
print(g.record_checked_claims(root, {}))
```
(`defect-verification` role's terminal `loop_state` is `cleared`, per `roles/defect-verification.json`: `"record_fields": {"loop_state": ["cleared"]}`.)

### Observed
```
bad findings: []
```
The gate passes the record even though the "checked" target (`nothing-real`) does not correspond to any test, file, or CI check, and the reason (`trust me bro`) is accepted merely because it is non-empty text — the gate only checks that a reason string exists, never what it says.

### Expected
A record claiming a terminal `loop_state` with an acceptance-verification line that names no real, checkable artifact (or whose `unverifiable` reason is not itself independently checked/attested by something outside the authoring session) should not pass a gate whose stated purpose (per its own docstring) is to require that "완료 주장은 기계로 확인되지 않으면 터미널 상태로 못 간다" (a completion claim that isn't machine-verified cannot reach terminal state). As implemented, `result: unverifiable` is a universal escape hatch: it satisfies the regex, satisfies the "non-empty reason" check, and is never touched by the CI cross-check or the test-existence check, so it is functionally indistinguishable from having no gate at all for any claim a session chooses to mark `unverifiable` instead of `pass`.
