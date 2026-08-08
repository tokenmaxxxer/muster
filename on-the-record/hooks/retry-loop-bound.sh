#!/usr/bin/env bash
# PreToolUse/PostToolUse pair: bound identical-denial retry loops within one
# session. Issue #507, design in
# docs/issue-507/proposals/2026-08-08-retry-loop-bound.md.
#
# Mode is selected by $1:
#   post -- observes a deny-shaped tool_response (the
#           `PreToolUse:<tool> hook error: [<gate>: refused -- ...]` shape
#           already parsed post-hoc by spawn.py's _GATE_HOOK_RE/_GATE_DENY_RE)
#           and bumps the per-session counter for this (tool, target)
#           signature. Identical target => identical signature, independent
#           of the exact reason text (the deny reason for a fixed target from
#           a fixed gate is itself deterministic, so keying on (tool, target)
#           is equivalent to keying on (tool, target, reason) here without
#           needing to know the reason before the gate has run).
#   pre  -- looks up the incoming request's signature before the underlying
#           gates run. count in [K, 2K) -> allow (exit 0) plus
#           hookSpecificOutput.additionalContext quoting the last deny
#           reason and any extracted expected-branch value. count >= 2K ->
#           deny outright (exit 2), aborting that signature for the rest of
#           the session; the underlying gate is never consulted again for it.
#
# K (and 2K = 2*K) are tunable via OTR_RETRY_BOUND_K (default 5).
# State: ${OTR_RETRY_BOUND_STATE_DIR:-$TMPDIR/otr-retry-bound}/<session_id>.json
#
# Fails OPEN on any parse/state error or missing session_id -- this hook
# only adds behavior on top of the existing gates, never instead of them.
trap 'exit 0' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

MODE="${1:-}"
case "$MODE" in pre|post) ;; *) trap - EXIT; exit 0 ;; esac

command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

PAYLOAD="$(cat 2>/dev/null || true)"
[ -n "$PAYLOAD" ] || { trap - EXIT; exit 0; }

STATE_DIR="${OTR_RETRY_BOUND_STATE_DIR:-${TMPDIR:-/tmp}/otr-retry-bound}"
mkdir -p "$STATE_DIR" 2>/dev/null || true

OTR_RB_PAYLOAD="$PAYLOAD" OTR_RB_MODE="$MODE" OTR_RB_STATE_DIR="$STATE_DIR" \
  OTR_RB_K="${OTR_RETRY_BOUND_K:-5}" python3 - <<'PY'
import hashlib
import json
import os
import re
import sys

payload_raw = os.environ.get("OTR_RB_PAYLOAD", "")
mode = os.environ.get("OTR_RB_MODE", "")
state_dir = os.environ.get("OTR_RB_STATE_DIR", "")
try:
    K = int(os.environ.get("OTR_RB_K", "5"))
except ValueError:
    K = 5
if K < 1:
    K = 1
TWO_K = K * 2

try:
    payload = json.loads(payload_raw)
except ValueError:
    sys.exit(0)
if not isinstance(payload, dict):
    sys.exit(0)

session_id = payload.get("session_id")
if not isinstance(session_id, str) or not session_id:
    sys.exit(0)
safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
state_path = os.path.join(state_dir, safe_session + ".json")

tool_name = payload.get("tool_name")
tool_input = payload.get("tool_input")
if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
    sys.exit(0)


def _load():
    try:
        with open(state_path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _save(data):
    try:
        tmp = state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, state_path)
    except OSError:
        pass


def _target(tool_input):
    for key in ("file_path", "path", "notebook_path"):
        val = tool_input.get(key)
        if isinstance(val, str):
            return os.path.normpath(val)
    val = tool_input.get("command")
    if isinstance(val, str):
        return val
    return json.dumps(tool_input, sort_keys=True)


def _signature(tool_name, target):
    h = hashlib.sha256()
    h.update("\x1f".join([tool_name, target]).encode("utf-8", "replace"))
    return h.hexdigest()


GATE_HOOK_RE = re.compile(r"^PreToolUse:\S+ hook error: \[([^\]]*)\]")
GATE_DENY_RE = re.compile(r"(\S+):\s*refused\s*\xe2\x80\x94\s*(.*)", re.DOTALL)
EXPECTED_BRANCH_RE = re.compile(r"requires branch (\S+)")

target = _target(tool_input)
sig = _signature(tool_name, target)

if mode == "post":
    resp = payload.get("tool_response")
    if isinstance(resp, str):
        text = resp
    elif resp is not None:
        text = json.dumps(resp)
    else:
        text = ""
    m = GATE_HOOK_RE.search(text)
    if not m:
        sys.exit(0)
    body = m.group(1)
    deny_m = GATE_DENY_RE.search(body)
    reason = deny_m.group(2).strip() if deny_m else body.strip()

    data = _load()
    entry = data.get(sig)
    if not isinstance(entry, dict):
        entry = {"count": 0, "last_reason": "", "aborted": False}
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last_reason"] = reason
    entry["tool_name"] = tool_name
    entry["target"] = target
    data[sig] = entry
    _save(data)
    sys.exit(0)

# mode == "pre"
data = _load()
entry = data.get(sig)
if not isinstance(entry, dict):
    sys.exit(0)
count = int(entry.get("count", 0))
reason = entry.get("last_reason", "")

if entry.get("aborted") or count >= TWO_K:
    if not entry.get("aborted"):
        entry["aborted"] = True
        data[sig] = entry
        _save(data)
    sys.stderr.write(
        "retry-loop-bound: aborted -- %s on %r denied %d identical times "
        "this session (signature %s). This action class is blocked for "
        "the rest of the session; the underlying gate will not be "
        "consulted again for this exact request. Last deny reason: %s"
        % (tool_name, target, count, sig[:12], reason)
    )
    sys.exit(2)

if count >= K:
    expected_m = EXPECTED_BRANCH_RE.search(reason)
    expected = (
        " Expected: requires branch %s." % expected_m.group(1)
        if expected_m
        else ""
    )
    ctx = (
        "retry-loop-bound: this exact %s on %r has been denied %d times "
        "this session with no change between attempts. Last deny reason: "
        "%s.%s Retrying identically will abort this action class after "
        "%d denials." % (tool_name, target, count, reason, expected, TWO_K)
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": ctx,
            "additionalContext": ctx,
        }
    }
    sys.stdout.write(json.dumps(out))
    sys.exit(0)

sys.exit(0)
PY
rc=$?
trap - EXIT
exit "$rc"
