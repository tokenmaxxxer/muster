# Survey — issue #450: silent exclude-guard write failure in `issue_workspace()`

`code_under_review:` `36f3a21a7bc8cc7c11dca7f2eef845265f2fe554` (main tip at session start).

## Upstream record

Follow-up from #445 finding 1 (`docs/issue-445/proposals/2026-08-08-spawn-path-silent-failure-hunt.md`
item 1, reproduced in `docs/issue-445/reports/defect-verification.md`). The
repro test already landed on main:
`test/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning`
(lines 51-83). This issue's job is to make that test assert the *fixed*
behavior (a surfaced warning) instead of the *broken* one, per the issue's
Acceptance section.

## Current state (measured)

`spawn.py` `issue_workspace()`, the new-clone branch (spawn.py:2955-2983):

```
    try:
        ex = work / ".git" / "info" / "exclude"
        ex.parent.mkdir(parents=True, exist_ok=True)
        existing = ex.read_text() if ex.exists() else ""
        lines = [".muster-cache/"]
        ...
        lines += [".bashrc", ".bash_profile", ".profile", ".zshrc",
                  ".zprofile", ".gitconfig", ".gitmodules", ".mcp.json",
                  ".claude/", ".idea", ".vscode", ".ripgreprc"]
        missing = [ln for ln in lines if ln.rstrip("/") not in existing]
        if missing:
            with ex.open("a") as fh:
                for ln in missing:
                    fh.write(ln + "\n")
    except OSError:
        pass
```

The whole block (read existing, compute missing, append) is wrapped in one
`try/except OSError: pass`. Any failure — `ex.parent.mkdir`, `ex.read_text`,
or the `ex.open("a")` append — is swallowed identically; nothing is printed
to stdout/stderr, no return value or exception marks the workspace as
degraded. `issue_workspace()` returns `str(work)` a few lines later
regardless (spawn.py:2988-2994, after the unrelated `_fetch_or_halt` call).

Other diagnostic-output conventions already used nearby in the same
function / file, for consistency:
- `sys.exit(f"...: {detail}")` for fail-closed halts (e.g. origin mismatch
  at spawn.py:2949-2950, clone failure at spawn.py:2957-2958).
- Plain `print(..., file=sys.stderr)` is used elsewhere in `spawn.py` for
  non-fatal warnings that don't halt the run (grep confirms the pattern
  exists — e.g. doctor/version-drift warnings). A warning here should
  follow that non-fatal-print convention, not `sys.exit`, since the issue's
  Acceptance explicitly allows either "surfaced" or "refuse the spawn... if
  judged safer" but only *requires* surfacing.

## Test surface

`test/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning`
(lines 51-83) currently asserts the *silent* behavior:
```
assert "exclude" not in captured.out.lower()
assert "exclude" not in captured.err.lower()
```
Per the issue's Acceptance ("test updated to assert the surfaced warning
(red today)"), this test must flip to assert a warning naming the
workspace path and the skipped entries is present in captured
stdout/stderr, and (implicitly) that the write-fails case does not crash
the whole spawn — issue_workspace() still returns a workspace, just with a
surfaced warning instead of a silent skip.

`test/test_spawn.py` is the existing regression suite for `spawn.py`;
Acceptance requires it stay green with the write succeeding (i.e. behavior
on the happy path is unchanged).

## Write set

- `spawn.py` — the `except OSError: pass` block in `issue_workspace()`
  (spawn.py:2964-2983), changed to catch the specific write operations,
  and print a warning naming the workspace and the missing/skipped exclude
  entries before returning.
- `test/test_silent_failure_repros.py` — flip
  `test_attempt_1_exclude_write_swallowed_no_warning` to assert the warning
  is surfaced (rename retained per issue wording: "attempt-1 test
  updated").

No new dependency, no new env var, no schema/migration.

## Scouting

Skipped. Reason: pure bugfix against an existing, fully-specified
Acceptance section — no open product/design decision (surface a warning
naming workspace + skipped entries; wording/exact format is an
implementation detail, not a direction choice). Skip condition: "the
change is a pure bugfix."
