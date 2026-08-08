---
proposal: docs/issue-517/proposals/2026-08-09-record-lint-and-scaffolder.md
---

# Hunt record — record-lint-and-scaffolder

## after-proposal — stance 4: assume the write set this proposal freezes cannot actually carry the work — find a path the build will need that the proposal's `files:` list does not include.

Verdict: FINDING — proposal offers record-scaffold.sh as "a PreToolUse (or on-demand CLI) generator" but if built as a PreToolUse hook it must be registered in on-the-record/hooks/hooks.json, which is not in the frozen files: list.
Kind: design-error
Seed: docs/issue-517/proposals/2026-08-09-record-lint-and-scaffolder.md ("What will be done" bullet for on-the-record/hooks/record-scaffold.sh)
cap_seconds: 120
tier: default
diff_stat_lines: 2 files changed (docs-only, both newly created)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:02:00Z

### Reproduce
grep -n "record-claim-guard" on-the-record/hooks/hooks.json
cat on-the-record/hooks/hooks.json

### Observed
Every existing hook script in on-the-record/hooks/ (self-update.sh, directive.sh, retry-loop-bound.sh, deliverable-guard.sh, contract-guard.sh, pr-preflight.sh, spec-index-preflight.sh, record-claim-guard.sh, stop-gate.sh, role-test-claim-guard.sh, decision-queue-stopgate.sh, report-framing-check.sh) has a corresponding entry under a lifecycle event (PreToolUse/PostToolUse/Stop/etc.) in on-the-record/hooks/hooks.json's "hooks" map with a "command" pointing at ${CLAUDE_PLUGIN_ROOT}/hooks/<script>. record-scaffold.sh has no such entry and hooks.json is absent from the proposal's files: list, so if the scaffolder is built as a PreToolUse-triggered hook (one of the two forms the proposal explicitly names) it would never actually fire in a plugin-installed session -- it would sit unregistered like an orphaned script, indistinguishable from every wired hook by directory location alone.

### Expected
on-the-record/hooks/hooks.json should be in the files: write set (or the proposal should commit unambiguously to the "on-demand CLI" form only, dropping the PreToolUse option), since the aggregator's own stated constraint is "must work in plugin-installed sessions" and plugin session wiring for hooks in this repo runs entirely through hooks.json.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — record-claim-guard.sh's new `import record_lint` gives every claim check a live crash path that exits 1 (non-blocking) instead of 2 (blocking), because the script's own fail-closed trap disarms itself (`trap - EXIT`) immediately before propagating that exit code.
Kind: composition
Seed: on-the-record/hooks/record-claim-guard.sh (rewired to `sys.path.insert(0, os.environ["RCG_GATES_DIR"]); import record_lint` instead of pure-stdlib inline regexes)
cap_seconds: 180
tier: default (size:diff>200 lines/>5 files)
diff_stat_lines: on-the-record/hooks/record-claim-guard.sh: 19 insertions, 52 deletions (part of larger multi-file delivery)
started_at: 2026-08-09T01:01:13+09:00
ended_at: 2026-08-09T01:04:29+09:00

### Reproduce
Symlink the hook script somewhere its `../../gates` math no longer resolves (a realistic deployment shape for a relocated/symlinked plugin hook), then feed it a payload for a report-path write containing a bare, uncited count claim such as "3 of 5 tests pass." with no derived: tag or code fence.

```
ln -s <repo>/on-the-record/hooks/record-claim-guard.sh /tmp/elsewhere/record-claim-guard.sh
printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"<a report path under docs/issue-N/reports/>.md","content":"3 of 5 tests pass."},"cwd":"/tmp/rcg_test"}' \
  | ORCHESTRATE_OFF=0 bash /tmp/elsewhere/record-claim-guard.sh
echo "exit=$?"
```

### Observed
```
/tmp/.../elsewhere/record-claim-guard.sh: line 38: cd: .../elsewhere/../../gates: No such file or directory
Traceback (most recent call last):
  File "<string>", line 4, in <module>
ModuleNotFoundError: No module named 'record_lint'
exit=1
```
The same payload run against the unmodified script in its real location denies with `record-claim-guard: 레코드에 근거 없는 개수 주장 (issue #333): ...` and exit 2, so the violation is genuinely a bare-count-claim violation the gate is supposed to catch. Once the `cd "$script_dir/../../gates"` resolution fails for any reason (relocated/symlinked hook script, or a plugin install where `on-the-record/` is not exactly two directories under a `gates/` sibling), the identical violating content sails through with exit 1 instead.

### Expected
The header comment claims "Fails closed (trap remaps non-0/2 exit to 2)" via `trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT`. But the tail does:
```
RCG_PAYLOAD="$payload" RCG_GATES_DIR="$gates_dir" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
```
`trap - EXIT` disarms the fail-closed remap immediately before `exit "$rc"` runs, so the trap never gets a chance to catch this exit — it only would fire on some other, unplanned exit path. Before this diff the inline python imported only stdlib (json, os, posixpath, re, sys), so a module-import crash was not a reachable failure mode; nothing routinely triggered the crash-to-1 escape hatch. Now `import record_lint` depends on `RCG_GATES_DIR`/`gates_dir` being derived correctly on every single invocation, and any miss silently turns a would-be-denied write into an unblocked one (with a stderr traceback most callers never inspect). Expected: any crash prior to reaching `deny()`/`sys.exit(0)` should still exit 2, matching the documented fail-closed contract.
