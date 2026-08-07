# `fulfils: count <derivation> <N>` — extend, not a new marker

Subject: issue-332

## Decision

Extend the existing `fulfils:` marker-line convention (issue #155,
`gates/gates.py::record_fulfils_diff`) with a fourth claim kind, `count`,
instead of introducing a second, parallel claim-line syntax:

```
fulfils: count <derivation> <N>
```

`<derivation>` is one of:
- a **glob/path** (contains `*`, `?`, or `[`) — the claim is checked
  against the count of paths in the work tree matching that glob
  (`Path.glob`), evaluated at gate time, not against the diff.
- otherwise, a **shell command** — tokenized with `shlex.split` and run
  via `subprocess.run(argv, cwd=work, ...)` with `shell=False` (no shell
  metacharacters, no pipes). Its stdout, stripped, must be a bare integer
  (`^-?\d+$`); anything else (non-zero exit, non-integer stdout) makes the
  derivation unresolvable.

`<N>` is the last whitespace-separated token of the claim and must parse
as an integer; everything before it is `<derivation>` (derivation and
command arguments may themselves contain spaces, so the split anchors on
the trailing integer, not on the first space).

## Re-run semantics

Unlike `delete`/`create`/`move`, which compare a claim against the
*committed diff* (`origin/main...HEAD`), `count` re-runs the derivation
against the *current work tree* — a count is a property of a state, not
of a change. An unresolvable derivation (glob matches nothing where a
glob was expected to exist, command fails, or stdout isn't a bare
integer) is treated the same as a mismatch: fail-closed, same as a
malformed `delete`/`create`/`move` line.

## Why extend `fulfils:` instead of a new marker

`fulfils:` already has the parser, the fail-closed handling of malformed
lines, the opt-in posture (untouched records aren't affected — no
`count` line, no check), and test-coverage precedent in `test_gates.py`.
Reusing the `fulfils: <kind> <args>` grammar keeps "claim in a phase-2
record checked against a mechanical derivation" as one convention.

## Rejected alternative

A free-text linter over record prose flagging any bare number without an
adjacent citation. Rejected: the false-positive surface is unbounded
(issue numbers, ports, dates, line counts all contain digits), and there
is no fixed evidence format to validate a citation against — the gate
would either fail-open (a linter nobody trusts) or fail-closed on nearly
everything a record legitimately writes, the exact failure mode
`gates/ci.py`'s own docstring names as how gates die.

## No shell metacharacters, by design

`_count_derivation` never passes a runtime-constructed string to a shell
(no `shell=True`, no pipes). This means a caller who wants to count
something like "matching log lines" needs a single command (e.g. `grep -c
pattern path`), not a pipeline (`grep pattern path | wc -l`) — a
deliberate narrowing to keep the derivation string from ever reaching a
shell interpreter.

## What this does not do

- Does not retroactively invalidate any already-merged record's
  unevidenced claims — see the proposal's "what this reaches beyond its
  own acceptance" section (docs/issue-332/proposals/2026-08-07-claim-evidence-at-write-time.md).
- Does not add CI enforcement beyond what `record_fulfils_diff` already
  has: `gates/ci.py::check()` only reaches `record_fulfils_diff` when
  `closes_only=False`, and the only required-status-check workflow
  (`.github/workflows/plan-aware-closes-gate.yml`) calls it with
  `--closes-only` (found during the phase-1 hunt,
  docs/reports/2026-08-07-hunt-claim-evidence-at-write-time.md). The
  `count` kind inherits that pre-existing gap: it is exercised by
  `pytest test_gates.py -k fulfils` and by any local/manual
  `gates/ci.py` invocation without `--closes-only`, but not by the
  required PR check today. Widening that workflow's invocation is out of
  this issue's frozen write set.
