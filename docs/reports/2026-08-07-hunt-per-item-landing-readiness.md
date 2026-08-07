---
proposal: docs/issue-407/proposals/2026-08-07-per-item-landing-readiness.md
---

# Hunt record — per-item-landing-readiness

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: docs/issue-407/proposals/2026-08-07-per-item-landing-readiness.md (frozen write set: gates/landing_readiness.py, gates/test_landing_readiness.py, on-the-record/commands/run.md)
cap_seconds: 120
tier: default
diff_stat_lines: docs-only, ~2 new files proposed at ~21-200 line scale
started_at: 2026-08-07T07:27:52Z
ended_at: 2026-08-07T07:38:00Z

Checked, each with a runnable repro, whether the build needs a path outside the frozen write set:

- pytest discovery: `python3 -m pytest -q --collect-only gates/test_closes_gate_ci.py` collects
  43 tests cleanly with no `__init__.py`/conftest wiring specific to `gates/` beyond the
  repo-root `conftest.py` (which only sets rulebook-checkout env defaults and a leak-detection
  fixture, unrelated to test discovery). `gates/test_landing_readiness.py` would collect the
  same way — no missing conftest/`__init__.py` path.
- `gates.py`'s `REGISTRY`/`PROTECTED_*` sets: `REGISTRY` is a dependency-registry-URL map
  (requirements.txt/package.json), unrelated to gate script registration — `closure_sweep.py`
  and `pr_reference.py` are not referenced anywhere in `gates.py` either, so a new
  `landing_readiness.py` needs no entry there. `PROTECTED_ROOT_DIRS` includes `gates` (any PR
  touching `gates/` gets machine-flagged for human review) but that is pre-existing, unaffected
  by adding a new file under `gates/`.
- CI wiring: `grep -rl "pytest" .github/workflows/` returns nothing — no workflow runs the
  general `pytest -q` suite gated on file lists; the two existing workflows only invoke
  `gates/ci.py` directly. The proposal's "how you'll know it worked" runs pytest manually, not
  via a CI file that would need editing.
- `on-the-record/commands/run.md`'s frontmatter (`allowed-tools: Bash(python3:*), Bash(git:*),
  Bash(gh:*), ...`) already permits invoking `python3 gates/landing_readiness.py` and `gh pr
  checks`/`gh pr diff --name-only` — no allowlist file needs touching.
- Reuse of existing helpers (`spawn.py`, `pr_reference.py`, and `ci.py`'s phase-2
  record-evidence functions for `has_record`/`has_approval`) is import-only, matching
  `closure_sweep.py`'s own pattern (`sys.path.insert` + `import pr_reference`/`import spawn`
  against unmodified files) — reusing an unmodified file is not a missing write-set entry.

Did not find a path the frozen write set omits that the described build (per `classify()` +
`main()` + one `run.md` sentence) mechanically requires. Stopping here rather than reporting a
plausible-but-unreproduced concern (e.g., where `blocking_causes` inputs to `main()` would come
from at runtime is underspecified in the proposal, but that's a design gap inside
`landing_readiness.py` itself, not a missing file outside the write set — no repro shows it
needs a path not listed).
