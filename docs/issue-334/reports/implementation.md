---
code_under_review:
  - gates/skip_gate.py
  - gates/test_skip_gate.py
  - docs/handbooks/operations.md
loop_state: phase-2-complete
---

# issue-334 phase 2 — skip-vs-pass gate

## Why

Per #334: a skip means a check did not run; a pass means it ran and was
correct; folding both into one green exit code hides genuinely-untested
code behind a "verified" claim. Per the approved proposal
(`docs/issue-334/proposals/skip-gate.md`), fix this with a standalone
gate script that fails closed on any skip.

## Conditional-approval feedback addressed

The APPROVE comment's follow-up asked to recheck, in phase 2, the
proposal's premise that there were "zero real skips in the suite to
calibrate against" — the full suite currently reads `51 failed` because
of #360 (`test_approve_scope.py` replacing `spawn.subprocess.run`
process-wide with no teardown), and the failed count alone says nothing
about skips.

Recheck performed: `python3 -m pytest -q -ra` was run against the full
suite at `199ddd9` and its output grepped for `SKIPPED` lines. Result:
**zero** `SKIPPED` entries — all 51 failures are hard failures (mostly
`AttributeError`/`AssertionError` from the `spawn.subprocess.run`
monkeypatch leak), none are skips. The allowlist-deferral premise holds;
proceeding with the approved fail-closed design (no allowlist) unchanged.

Per the feedback's explicit instruction, `gates/skip_gate.py` is not
wired as a required CI check — #360 is not yet landed and the suite is
currently red on 51 unrelated failures; a required gate on top of that
would block every PR.

## What was done

- `gates/skip_gate.py` — subprocess-wraps `python3 -m pytest -q -ra`,
  parses the `-ra` short summary for `SKIPPED` lines, exits 0 only if
  the underlying pytest run exited 0 AND zero skips were found. Exits 1
  and prints each skipped nodeid plus a one-line verdict otherwise.
- `gates/test_skip_gate.py` — fixture-suite tests: one temp suite with a
  `pytest.mark.skip`, one without, asserting the gate exits 1 / 0
  respectively. This is the executable regression artifact #310
  requires.
- `docs/handbooks/operations.md` — self-check section updated to mention
  `python3 gates/skip_gate.py`.

## What did not work

None.

## Verification

Per-file: `python3 gates/test_skip_gate.py` — ran clean: `5 passed`
(`t_gate_exits_0_on_suite_with_no_skips`,
`t_gate_exits_1_on_suite_with_a_skip`,
`t_gate_exits_nonzero_on_hard_failure_even_without_skips`,
`t_parse_skips_extracts_location_and_reason`,
`t_parse_skips_handles_reasonless_line`).
Full-suite: `python3 -m pytest -q -ra` — pre-existing 51 failures from
#360 (process-global `spawn.subprocess.run` monkeypatch leak in
`test_approve_scope.py`, no teardown), unrelated to this change; 0 real
skips confirmed at baseline. Any new failure beyond that pre-existing 51
is attributable to this change; none observed.

## Reach beyond acceptance criteria (per #330)

The gate is a standalone script usable by any role session's self-check
manually, not just via this repo's suite — any Python project running
`python3 -m pytest -q -ra` gets the same skip-vs-pass distinction by
invoking `skip_gate.py` directly. It is deliberately not wired into
`gates/ci.py` or CI (out of scope per proposal and per the
conditional-approval feedback), so its reach today is limited to manual
invocation per the updated handbook instruction.

## Hunt

None dispatched this phase. This session's turn is headless/single-shot
(contract v3 s22): a background warrant-hunter dispatch whose result is
not consumed before the turn ends is prohibited under that clause, so
the before-landing hunt is skipped for this transition.

## open findings

None.

## next steps

None — proposal's write set fully delivered; report to PR #346 for
human review/merge.

## resolution path

N/A — no open findings.
