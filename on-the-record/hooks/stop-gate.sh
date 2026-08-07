#!/usr/bin/env bash
# Stop: orchestrator-only structural check on last_assistant_message.
# Issue #411 — nothing previously inspected what the orchestrator says to
# the operator. This checks one structural subset of #318's approval-
# request shape: does an approval-shaped reply name its issue (#<n>),
# state a change, and state a risk/tradeoff. Substance (is the stated risk
# the real risk) is out of reach for a structural check and not claimed.
#
# Only fires when the reply looks approval-shaped (an approval trigger
# phrase present) — ordinary turns pass through untouched, zero
# false-positive risk on non-approval text.
#
# On violation: hookSpecificOutput.additionalContext naming the missing
# clause(s) — a same-turn correction requirement, not decision:"block".
# A structural heuristic misfiring on an unusually-phrased legitimate
# reply should not discard the whole turn (see proposal Rationale).
#
# Fails closed (trap remaps non-0/2 exit to 2), matching
# deliverable-guard.sh's house style. Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, sys

try:
    e = json.loads(os.environ.get("STOP_PAYLOAD", ""))
except ValueError:
    sys.exit(2)
if not isinstance(e, dict):
    sys.exit(2)

msg = e.get("last_assistant_message")
if not isinstance(msg, str) or not msg:
    sys.exit(0)

TRIGGER = re.compile(
    r"(승인\s*요청|승인해|request(ing)? approv|please approve|"
    r"seeking approval|APPROVE issue-)",
    re.IGNORECASE,
)
if not TRIGGER.search(msg):
    sys.exit(0)

ISSUE_RE = re.compile(r"#\d+")
CHANGE_RE = re.compile(
    r"(변경|바뀌|수정|change|changes?:|will (do|change|add|remove|update))",
    re.IGNORECASE,
)
RISK_RE = re.compile(
    r"(위험|리스크|우려|risk|trade-?off|tradeoff|downside|caveat)",
    re.IGNORECASE,
)

missing = []
if not ISSUE_RE.search(msg):
    missing.append("issue reference (#<n>)")
if not CHANGE_RE.search(msg):
    missing.append("change statement (what changes)")
if not RISK_RE.search(msg):
    missing.append("risk/tradeoff statement")

if not missing:
    sys.exit(0)

out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "stop-gate: this approval-shaped reply is missing: "
            + "; ".join(missing)
            + ". Restate the approval request with all three present "
              "(issue reference, what changes, what risk/tradeoff) before "
              "stopping."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

STOP_PAYLOAD="$payload" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
