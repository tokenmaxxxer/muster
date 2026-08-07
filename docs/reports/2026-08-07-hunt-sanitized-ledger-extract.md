
## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: docs/issue-291/proposals/2026-08-07-sanitized-ledger-extract.md, docs/issue-291/reports/implementation/survey.md (two new files, no code diff)
cap_seconds: 60
tier: size:small
diff_stat_lines: 2 files added (docs only)
started_at: 2026-08-07T16:20:00+09:00
ended_at: 2026-08-07T16:24:00+09:00

Checked: spawn.ROOT is monkeypatched to a tmpdir in the test classes that
exercise ledger_write (test_spawn.py:1466/1560/3716, test_flows.py:77-84), so
a new `ROOT / "ledger" / "runs_extract.jsonl"` write inside ledger_write()
would land in the tmpdir during tests, not the real tracked file — no hidden
test-time mutation of the repo. Also checked that `ledger/` already exists as
a tracked directory (git ls-files ledger/ -> ledger/collect.py) but
collect.py is an unrelated review-record aggregator with no read/import of
any file under ledger/, so dropping runs_extract.jsonl there causes no
collision. .gitignore only has `runs/`, not `ledger/`, so the new tracked
file would not be silently ignored. No CI workflow
(.github/workflows/plan-aware-closes-gate.yml) references runs/ or ledger/.
No setup.py/pyproject.toml exists to omit the new data file from packaging.
Could not produce a reproduction of a build-required path missing from the
write set within the cap.
