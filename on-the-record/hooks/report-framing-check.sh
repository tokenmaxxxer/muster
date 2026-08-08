#!/usr/bin/env bash
# Stop: checks a PR/board report turn's last_assistant_message for the
# four semantic-effect framing elements (issue #320) — resolved problem,
# prior cost, newly possible, still broken. Detects a report turn by the
# run.md step-5 header (1단계/2단계) or the Mission Board line shape
# (`[이슈 #<n>] ... · <stage> → <next>`). Not a report turn -> no-op.
#
# This checks the live reply directly, complementing the grep-based
# instruction-text check in gates/test_report_framing_check.py (which
# only verifies run.md still carries the instruction, not that a given
# reply complied with it).
#
# Fails closed (trap remaps non-0/2 exit to 2), matching stop-gate.sh's
# house style. Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, sys

try:
    e = json.loads(os.environ.get("REPORT_FRAMING_PAYLOAD", ""))
except ValueError:
    sys.exit(2)
if not isinstance(e, dict):
    sys.exit(2)

msg = e.get("last_assistant_message")
if not isinstance(msg, str) or not msg:
    sys.exit(0)

REPORT_TRIGGER = re.compile(
    r"(1단계|2단계|\[이슈\s*#\d+\].*·.*→)",
)
if not REPORT_TRIGGER.search(msg):
    sys.exit(0)

ELEMENTS = {
    "resolved problem": re.compile(
        r"(해결|제거|고쳐|fix(ed|es)?|resolv(ed|es)|no longer)", re.IGNORECASE),
    "prior cost": re.compile(
        r"(비용|지장|치렀|겪었|used to|cost|previously|고통)", re.IGNORECASE),
    "newly possible": re.compile(
        r"(새로 가능|이제.*가능|newly possible|now (possible|can)|가능해)",
        re.IGNORECASE),
    "still broken": re.compile(
        r"(남았|아직.*(안|못)|여전히|still (broken|open|missing|todo)|"
        r"not (yet|done))", re.IGNORECASE),
}

missing = [name for name, pat in ELEMENTS.items() if not pat.search(msg)]

if not missing:
    sys.exit(0)

out = {
    "decision": "block",
    "reason": (
        "report-framing-check: this PR/board report is missing framing "
        "element(s): " + "; ".join(missing) + ". Per issue-320, frame the "
        "change as resolved problem, prior cost, newly possible, and "
        "still broken — not just an address-only enumeration."
    ),
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

REPORT_FRAMING_PAYLOAD="$payload" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
