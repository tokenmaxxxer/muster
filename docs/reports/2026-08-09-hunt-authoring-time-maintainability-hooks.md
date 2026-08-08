---
proposal: docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md
---

# Hunt record — authoring-time-maintainability-hooks

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — call-shape-guard.sh (and by identical construction accumulation-claim-guard.sh) only fires on PreToolUse for Write|Edit|MultiEdit; the same denied .py content written via the Bash tool (shell redirection, `python3 -c`, `sed -i`, etc.) is never inspected and is allowed through.
Kind: composition
Seed: on-the-record/hooks/call-shape-guard.sh, on-the-record/hooks/accumulation-claim-guard.sh, on-the-record/hooks/hooks.json (PreToolUse matcher "Write|Edit|MultiEdit" for both new hooks, vs. the separate "Write|Edit|MultiEdit|Bash" matcher used by retry-loop-bound.sh in the same file)
cap_seconds: 180
tier: default
diff_stat_lines: (not measured — hunt scoped to the 7 files listed in the transition prompt)
started_at: 2026-08-09T00:20:00+09:00
ended_at: 2026-08-09T00:35:00+09:00

### Reproduce
Built two PreToolUse payloads with byte-identical divergent-subprocess-call content (two `subprocess.run(["cmd","sub",...])` calls to the same command with different semantic flag sets, `-X` vs `--field`), one shaped as a `Write` tool call and one shaped as a `Bash` tool call that writes the same file via `cat > gates/newtool.py <<'PYEOF' ... PYEOF`:

```
# payload_write = {"tool_name":"Write","tool_input":{"file_path":"gates/newtool.py","content":<content>},"cwd":<repo>}
# payload_bash  = {"tool_name":"Bash","tool_input":{"command":"cat > gates/newtool.py <<'PYEOF'\n<content>PYEOF\n"},"cwd":<repo>}

bash on-the-record/hooks/call-shape-guard.sh < write.json   # exit 2, denied
bash on-the-record/hooks/call-shape-guard.sh < bash.json    # exit 0, allowed
```

### Observed
```
$ bash on-the-record/hooks/call-shape-guard.sh < write.json
call-shape-guard: 명령 'cmd sub' 의 호출부들이 flag 모양이 다르다 (gates/newtool.py:2, gates/newtool.py:3) — 같은 명령이 서로 다른 의미로 호출되는, #388 과 같은 모양의 재발일 수 있다 (issue #419).
exit=2

$ bash on-the-record/hooks/call-shape-guard.sh < bash.json
(no output)
exit=0
```
The hook script itself gates on `e.get("tool_name") in ("Write","Edit","MultiEdit")` (sys.exit(0) otherwise), and hooks.json's PreToolUse registration for both new hooks uses matcher `"Write|Edit|MultiEdit"` — no `Bash` arm, unlike the sibling `retry-loop-bound.sh` entry in the same hooks.json which is registered against `"Write|Edit|MultiEdit|Bash"`. A session can write the exact same divergent-call-shape (or, by the identical `tool_name` check in accumulation-claim-guard.sh, the same false accumulation claim) into a tracked `.py` file by using the Bash tool (heredoc redirection, `python3 -c "open(p,'w').write(...)"`, `sed -i`, etc.) instead of Write/Edit/MultiEdit, and neither new PreToolUse hook will ever see the call.

### Expected
Either the PreToolUse matcher for both new hooks should include `Bash` (as `retry-loop-bound.sh` does), or the hooks should themselves refuse to no-op when `tool_name == "Bash"` and the command shape looks like a file write to a `.py` path — otherwise the deny-only guard is trivially bypassed by routing the same file write through a different tool, with no error or warning that content it would have denied went in unchecked.
