
## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: docs/issue-459/proposals/2026-08-08-pr-and-spec-index-preflight-hooks.md (cc64173), write set: on-the-record/hooks/pr-preflight.sh, on-the-record/hooks/test_pr_preflight.py, on-the-record/hooks/spec-index-preflight.sh, on-the-record/hooks/test_spec_index_preflight.py, on-the-record/hooks/hooks.json, docs/specs/enforcement-boundary.md
cap_seconds: 120
tier: default
diff_stat_lines: 284 (docs-only, 2 new files)
started_at: 2026-08-08T00:00:00+09:00
ended_at: 2026-08-08T00:15:00+09:00

Checked and ruled out as omissions:
- `docs/specs/reconciled-index.md`: not needed — `docs/specs/enforcement-boundary.md` is not among its tracked documents (`grep -n "enforcement-boundary" docs/specs/reconciled-index.md` — no match), so editing it per this proposal does not trip `gates/spec_index.py`'s own hash check.
- `on-the-record/hooks/hooks.json` schema: the `PreToolUse`/`Bash` matcher block's `hooks` array already supports multiple `{type, command}` entries in principle (each existing matcher currently has exactly one, but nothing in the schema or `contract-guard.sh`'s wiring forbids a second/third entry in the same array) — adding `pr-preflight.sh` and `spec-index-preflight.sh` as two more entries in the existing `Bash` matcher's `hooks` array is consistent with the format.
- `gates/test_boundary.py::t_all_gates_modules_recorded`: derives its required-mechanism set by globbing `on-the-record/hooks/*.sh` on disk and requires a row in `docs/specs/enforcement-boundary.md` — both new `.sh` files are in the write set and the proposal explicitly adds rows for both; ran `python3 gates/test_boundary.py` on current tree (5/5 pass) to confirm the gate's actual scan behavior matches what the proposal accounts for.
- `on-the-record/UNENFORCED-CLAUSES.md` (`t_unenforced_clauses_file_matches_spec_exactly`): only requires rows for mechanisms whose enforcement-boundary.md verdict contains "CI-supplement" or "out of scope — operator decision"; the proposal's two new rows are plain "contract" verdicts, so this file correctly does not need editing.
- CI test discovery (`.github/workflows/on-the-record-tests.yml` runs bare `pytest -q`): no test-file manifest to update: `on-the-record/hooks/test_pr_preflight.py` / `test_spec_index_preflight.py` will be auto-discovered like the existing sibling `on-the-record/hooks/test_contract_guard.py` (verified via `pytest --collect-only` picking up the existing file with no registration elsewhere).
- No parity/sync test ties `contract-guard.sh` (or any hook) to its ported-from `gates/*.py` module's logic (`grep -rn "parity|in sync|drift"` across gates/*.py and hooks/*.py — no hits), so the proposal's inline-reimplementation approach isn't silently required to also touch `gates/pr_reference.py` or `gates/spec_index.py`.
- `gates/pr_reference.check_body` and `flows._plan_from_body` (the functions the proposal says it ports logic from) both exist with the signatures the proposal assumes.

Did not find a build-required path the write set omits within the cap. No reproduction to report.
