#!/usr/bin/env bash
# PreToolUse (Bash): deny a batch of `gh pr merge` invocations in one Bash
# command when the TARGET repo's own currently-open proposals include a
# high-reversibility one — issue #511, requirement 5 ("high-impact
# proposals cannot be batch-approved").
#
# Scope, deliberately narrower than mapping each merged PR number to its
# proposal (that would need a `gh pr view`/branch lookup per PR, which the
# zero-install baseline avoids the same way contract-guard.sh already
# limits its own network calls): a Bash command is treated as a *batch*
# approval act when it contains two or more `gh pr merge` invocations in
# one tool call. When one is found, this hook classifies every
# `status: proposed` proposal currently open in the TARGET repo
# (docs/specs/impact-classification.md's four-axis rule, via
# gates/risk_report.py:batch_blocked()) and denies the whole command if
# any of them requires individual approval — the batch cannot proceed
# while a high-impact item is still sitting in the same open-proposal set
# it would be approved alongside.
#
# Deployment target (issue #511 requirement 7): classification logic is
# read from the on-the-record CHECKOUT (resolved the same way
# decision-queue-stopgate.sh does, zero-install, git-clone fallback), but
# every path it classifies is anchored to the TARGET repo — `pwd -P` at
# hook-invocation time, never this checkout's own tree. No marketplace-repo
# path is assumed to exist inside the target.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as contract-guard.sh).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

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
[ -n "$CHECKOUT" ] || exit 0

TARGET_REPO="$(pwd -P)"

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, sys
from pathlib import Path

def deny(msg):
    sys.stderr.write("impact-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("IG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

merge_count = len(re.findall(r"\bgh\s+pr\s+merge\b", cmd))
if merge_count < 2:
    sys.exit(0)  # single merge — ordinary individually-approved act, not a batch

checkout = os.environ.get("IG_CHECKOUT")
target = os.environ.get("IG_TARGET")
sys.path.insert(0, os.path.join(checkout, "gates"))
try:
    import risk_report
except ImportError:
    sys.exit(0)  # checkout unusable — fail-open on the classifier itself,
                 # same posture as contract-guard.sh's gh-lookup failures

root = Path(target)
proposals = risk_report.scan_open_proposals(root)
blocked = risk_report.batch_blocked(proposals, root)
if not blocked:
    sys.exit(0)

names = ", ".join(f"{b['path']} (reversibility={b['axes']['reversibility']})"
                   for b in blocked)
deny(f"batch of {merge_count} `gh pr merge` calls denied before executing: "
     f"{len(blocked)} open proposal(s) require individual approval per "
     f"docs/specs/impact-classification.md's dominant-axis rule: {names}. "
     f"Merge them one at a time so each gets its own individual approval.")
PY

IG_PAYLOAD="$payload" IG_CHECKOUT="$CHECKOUT" IG_TARGET="$TARGET_REPO" python3 -c "$GUARD"
rc=$?
exit "$rc"
