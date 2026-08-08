
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

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — new hook scripts pr-preflight.sh and spec-index-preflight.sh are not executable, so hooks.json's direct command invocation of ${CLAUDE_PLUGIN_ROOT}/hooks/pr-preflight.sh will fail with Permission denied on every Bash tool call, unlike every existing sibling hook script which ships with the executable bit set.
Kind: silent-failure
Seed: on-the-record/hooks/hooks.json (staged), on-the-record/hooks/pr-preflight.sh, on-the-record/hooks/spec-index-preflight.sh (untracked, new)
cap_seconds: 180
tier: size:>5-files
diff_stat_lines: ~400-500 across 6 files
started_at: 2026-08-08T18:00:00+09:00
ended_at: 2026-08-08T18:12:00+09:00

### Reproduce
cd on-the-record/hooks
ls -la pr-preflight.sh spec-index-preflight.sh contract-guard.sh deliverable-guard.sh
printf '{"tool_name":"Bash","tool_input":{"command":"echo hi"}}' | ./pr-preflight.sh
echo "exit: $?"

### Observed
-rwxrwxr-x 1 jwjung jwjung 6955 Aug  8 17:43 contract-guard.sh
-rwxrwxr-x 1 jwjung jwjung 3919 Aug  8 17:43 deliverable-guard.sh
-rw-rw-r-- 1 jwjung jwjung 7915 Aug  8 17:49 pr-preflight.sh
-rw-rw-r-- 1 jwjung jwjung 4243 Aug  8 17:50 spec-index-preflight.sh
/bin/bash: ./pr-preflight.sh: Permission denied
exit: 126

Both new hooks lack the executable bit (mode 664) while every sibling .sh file registered the same way in hooks.json (contract-guard.sh, deliverable-guard.sh, self-update.sh, directive.sh, stop-gate.sh) is mode 775. hooks.json wires them as bare command strings, the same mechanism used for the executable siblings, with no bash/interpreter prefix to work around a missing exec bit.

### Expected
chmod +x on-the-record/hooks/pr-preflight.sh on-the-record/hooks/spec-index-preflight.sh should have been part of the same change that added the files and wired them into hooks.json, so the PreToolUse hooks actually execute instead of erroring out (or being silently skipped, depending on how the harness handles a non-zero/126 exit from a hook command) on every Bash call.
