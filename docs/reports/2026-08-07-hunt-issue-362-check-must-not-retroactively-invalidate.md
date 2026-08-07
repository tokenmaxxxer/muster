---
proposal: docs/issue-362/proposals/2026-08-07-check-must-not-retroactively-invalidate.md
---

# Hunt record — check-must-not-retroactively-invalidate

## after-proposal — stance 4: assume the proposal's write set cannot carry the work it commits to

Verdict: NO FINDING
Seed: docs/issue-362/proposals/2026-08-07-check-must-not-retroactively-invalidate.md, docs/issue-362/reports/implementation/survey.md (commit 3d9fb65)
cap_seconds: 120
tier: default
diff_stat_lines: (2 files touched per dispatcher; proposal is new file)
started_at: 2026-08-07T14:34:45+09:00
ended_at: 2026-08-07T14:39:00+09:00

Checked whether the planned verdict-stability test for record_enums needs a
fixture/path outside the frozen write set (real roles/<role>.json under repo
root, a new conftest.py, etc). test_gates.py already has a self-contained
helper `_enum_record_repo` (line 408) that builds a throwaway
`roles/<role>.json` inside a `tempfile.TemporaryDirectory()` and points
`gates.ON_THE_RECORD_ROOT` at it, entirely in-process, saving/restoring the
module global. Existing tests (`t_record_enums_out_of_enum_blocks`,
`t_record_enums_in_enum_passes`, etc.) already exercise the "declare enum
before/after" shape this proposal wants for the xfail verdict-stability test.
No new fixture directory, conftest.py, or real repo-root roles/*.json file is
required — the write set (test_gates.py only) is sufficient to build the
described test. Did not find a path the build needs that the write set omits.
