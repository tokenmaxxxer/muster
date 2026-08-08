#!/usr/bin/env bash
# Stop: surface aged decision_queue items so an operator decision does not
# sit unread across an unlimited number of new orchestrator turns.
# Issue #466 (class-B row from the #464 ADR), carrying the #374 proposal's
# design (docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md)
# into this issue's acceptance-named file.
#
# Two age tiers, read fresh every turn from `spawn.py flows --json`'s
# decision_queue (already-correct data, per #374's survey — nothing new is
# computed here):
#   age_hours >= 1 -> additionalContext reminder, non-blocking.
#   age_hours >= 4 -> decision:"block", forcing one more turn.
# Below tier 1, or an empty queue -> silent (exit 0, no output).
#
# Resolves the on-the-record checkout the same way directive.sh does.
# Kill switches: ORCHESTRATE_OFF=1, CLAUDE_ROLE set (spawned role session).
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
payload="$(cat 2>/dev/null || true)"

_checkout_resolve() {
  if [ -n "${TOKENMAXXXER_CHECKOUT:-}" ] && [ -f "${TOKENMAXXXER_CHECKOUT}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_CHECKOUT}"; return 0
  fi
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  own="$HOME/.claude/tokenmaxxxer/on-the-record"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  old="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$old/spawn.py" ]; then printf '%s' "$old"; return 0; fi
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || exit 2

REPO="$(pwd -P)"
FLOWS_JSON="$(python3 "$CHECKOUT/spawn.py" flows --json -C "$REPO" 2>/dev/null || true)"
[ -n "$FLOWS_JSON" ] || { trap - EXIT; exit 0; }

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, sys

try:
    flows = json.loads(os.environ.get("STOPGATE_FLOWS_JSON", ""))
except ValueError:
    sys.exit(0)
if not isinstance(flows, dict):
    sys.exit(0)

queue = flows.get("decision_queue")
if not isinstance(queue, list) or not queue:
    sys.exit(0)

tier1, tier2 = [], []
for item in queue:
    if not isinstance(item, dict):
        continue
    age = item.get("age_hours")
    if not isinstance(age, (int, float)):
        continue
    if age >= 4:
        tier2.append(item)
    elif age >= 1:
        tier1.append(item)

if not tier1 and not tier2:
    sys.exit(0)


def _name(item):
    issue = item.get("issue")
    pr = item.get("pr")
    age = item.get("age_hours")
    parts = []
    if issue is not None:
        parts.append(f"#{issue}")
    if pr is not None:
        parts.append(f"PR#{pr}")
    label = "/".join(parts) if parts else "(unnamed)"
    return f"{label} ({age:.1f}h)"


if tier2:
    names = ", ".join(_name(i) for i in tier2)
    out = {
        "decision": "block",
        "reason": (
            "decision-queue-stopgate: decision-queue items have aged "
            "past 4h with no operator decision: " + names + ". "
            "Address the queue (approve, defer explicitly, or state why "
            "not yet) before continuing new work."
        ),
    }
    sys.stdout.write(json.dumps(out))
    sys.exit(0)

names = ", ".join(_name(i) for i in tier1)
out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "decision-queue-stopgate: decision-queue items waiting on an "
            "operator decision: " + names + "."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

STOPGATE_FLOWS_JSON="$FLOWS_JSON" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
