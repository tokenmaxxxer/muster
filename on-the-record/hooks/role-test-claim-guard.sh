#!/usr/bin/env bash
# Stop: role-session structural check on last_assistant_message, session-
# local mirror of gates/skip_gate.py (#334) and the stub/full-suite
# integrity lesson behind gates/test_closes_gate_ci.py's #435 scope
# (issue #457 Group C porting).
#
# Fires in ROLE sessions only (CLAUDE_ROLE set) — opposite of stop-gate.sh,
# which is orchestrator-only. These are checks on a role's own test-run
# claims, not on an orchestrator's approval-request shape.
#
# A Stop hook cannot re-run pytest itself (no repo/cwd guarantee, no
# time budget); it can only inspect what the reply already pasted. So
# this is a structural mirror, not a byte-identical port:
#   - #334 mirror: the reply pastes pytest output containing SKIPPED
#     lines, but elsewhere claims a clean pass (통과/all pass/green) with
#     no mention of the skips — the skip-vs-pass conflation skip_gate.py
#     exists to catch, applied to the claim text instead of the exit code.
#   - #435 mirror: the reply pastes a pytest summary line ("N passed") and
#     separately types a different test-count claim by hand — the same
#     "counted by hand, not derived from the real run" defect #333/#435
#     both name, applied specifically to test-run counts.
#
# On violation: hookSpecificOutput.additionalContext (same-turn
# correction, not decision:"block" — a Stop hook cannot un-say what was
# already sent; see stop-gate.sh's precedent).
# Fails closed (trap remaps non-0/2 exit to 2). Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
[ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, sys

try:
    e = json.loads(os.environ.get("RTCG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)

msg = e.get("last_assistant_message")
if not isinstance(msg, str) or not msg:
    sys.exit(0)

_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_SKIP_LINE_RE = re.compile(r"^SKIPPED(?: \[\d+\])? ([^:]+:\d+)(?:: (.*))?$",
                            re.MULTILINE)
_SUMMARY_PASSED = re.compile(r"(\d+)\s+passed\b")
_CLEAN_PASS_CLAIM = re.compile(
    r"(모두\s*통과|전부\s*통과|all\s+(?:tests?\s+)?pass(?:ed|ing)?|"
    r"clean\s+pass|테스트\s*통과)", re.IGNORECASE)
_HAND_COUNT_CLAIM = re.compile(
    r"(\d+)\s*(?:개|tests?)\s*(?:가|이)?\s*(?:통과|pass(?:ed)?)",
    re.IGNORECASE)

missing = []

fenced_blocks = _FENCE.findall(msg)
prose = _FENCE.sub("", msg)
skip_lines_present = any(_SKIP_LINE_RE.search(b) for b in fenced_blocks)
if skip_lines_present and _CLEAN_PASS_CLAIM.search(prose):
    if "skip" not in prose.lower() and "스킵" not in prose:
        missing.append(
            "issue #334: pasted pytest output has SKIPPED lines, but the "
            "reply claims a clean pass without mentioning the skips — "
            "skip is not pass."
        )

for b in fenced_blocks:
    sm = _SUMMARY_PASSED.search(b)
    if not sm:
        continue
    actual = int(sm.group(1))
    for hm in _HAND_COUNT_CLAIM.finditer(prose):
        claimed = int(hm.group(1))
        if claimed != actual:
            missing.append(
                f"issue #435: reply claims {claimed} passed by hand, but "
                f"the pasted pytest summary says {actual} passed — the "
                "count must be derived from the real run, not retyped."
            )
            break

if not missing:
    sys.exit(0)

out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "role-test-claim-guard: " + "; ".join(missing)
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

RTCG_PAYLOAD="$payload" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
