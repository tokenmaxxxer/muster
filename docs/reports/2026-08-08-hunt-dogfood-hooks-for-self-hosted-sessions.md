---
proposal: docs/issue-508/proposals/2026-08-08-dogfood-hooks-for-self-hosted-sessions.md
---

# Hunt record — dogfood-hooks-for-self-hosted-sessions

## before-landing — stance 0: assume the gate/mechanism just touched is bypassable — find the bypass.

Verdict: FINDING — self_hosted_hooks() silently returns None (and role_settings then omits "hooks" entirely) whenever the self-hosted target's hooks.json fails to parse or read, so a self-hosted spawn against a corrupted/truncated hooks.json runs with zero hooks injected and no error, exception, or log of any kind — indistinguishable from a healthy run.
Kind: silent-failure
Seed: spawn.py self_hosted_hooks(cwd) + role_settings(role, cwd=None) diff (staged)
cap_seconds: 180
tier: size:large
diff_stat_lines: ~45 (spawn.py hunk) + new test/doc files
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:03:00Z

### Reproduce
mkdir -p /tmp/spoof_test/on-the-record/hooks
printf '{not valid json' > /tmp/spoof_test/on-the-record/hooks/hooks.json

Then run this Python (as a script, e.g. /tmp/check.py):

    import sys
    sys.path.insert(0, "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-508-implementation")
    import spawn
    s = spawn.role_settings("implementation", "/tmp/spoof_test")
    print("hooks" in s, s.get("hooks"))

    python3 /tmp/check.py

### Observed
    False None

`role_settings` returns a settings dict with no "hooks" key at all — the same shape as a genuinely non-self-hosted target — and neither `self_hosted_hooks` nor `role_settings` raises, logs, prints, or otherwise signals that the hooks.json it found (proving self-hosted detection *did* fire, since the file exists and is_file() is true) could not be used. The `except OSError` / `except ValueError` branches in `self_hosted_hooks` both swallow the failure and return `None`, and the caller (`if injected: s["hooks"] = injected`) treats that identically to "not self-hosted, nothing to inject."

This directly undermines the issue's stated goal (deny-before-effect via dogfooded hooks): a corrupted, truncated, or momentarily-being-edited `on-the-record/hooks/hooks.json` in the on-the-record repo itself — the exact target this feature exists to protect — causes every guard (spec-index-preflight, contract-guard, pr-preflight, stop-gate, etc.) to silently drop out of a self-hosted session, with the spawned session's settings.json looking identical to a clean run.

### Expected
A self-hosted target whose hooks.json exists but fails to parse/read should fail loudly (raise, or at minimum emit a clear diagnostic and cause spawn to abort) rather than degrade to "no hooks injected, no evidence anything went wrong."
