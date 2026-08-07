#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit|NotebookEdit): deny-only. In an
# orchestrator session (this plugin enabled, no CLAUDE_ROLE), deliverables
# are ROLE WORK — the coding-rulebook lesson, enforced mechanically after
# a live session authored a requirements doc itself despite the directive.
#
# Denied: writes under a target repo's src/, test/, or docs/ trees (and
# tests/, issue #287 S5 — the far more common layout, previously never
# matched). Also denied: an unparseable stdin payload (empty, non-JSON,
# non-dict JSON, missing file_path) — issue #287 S4: a delivery failure
# on stdin must not silently become an ALLOW.
# Allowed: docs/specs/approvers.md (the one file the orchestrator is
# sanctioned to write, with the user's confirmation), and anything outside
# those trees (scratch files, the muster checkout itself).
# Kill switch: ORCHESTRATE_OFF=1. Fail closed on non-0/2 (now including
# parse failure, not just crashes — the previous header claim here was
# false for the parse-failure path; issue #287 S4).
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

# No fast-path skip on "doesn't look like src/test/docs" here anymore:
# that shortcut used to also skip empty/malformed payloads straight to
# ALLOW (issue #287 S4), since those don't contain the substring either.
# python3 below re-derives the real allow/deny decision from tool_name,
# file_path, and the same tree regex — it is the single source of truth.
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

def deny(msg):
    sys.stderr.write("orchestrate: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("ORCH_PAYLOAD", ""))
except ValueError:
    deny("stdin payload is not valid JSON — cannot verify this write is "
         "safe, denying rather than silently allowing it through.")
if not isinstance(e, dict):
    deny("stdin payload is not a JSON object — cannot verify this write is "
         "safe, denying rather than silently allowing it through.")
if (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
p = ti.get("file_path") or ti.get("notebook_path") if isinstance(ti, dict) else None
if not isinstance(p, str) or not p:
    deny("tool_input is missing file_path/notebook_path — cannot verify "
         "this write's target, denying rather than silently allowing it "
         "through.")

n = posixpath.normpath(p.replace("\\", "/"))
m = re.search(r"(^|/)(src|tests?|docs)/", n)
if not m:
    sys.exit(0)
if n.endswith("docs/specs/approvers.md"):
    sys.exit(0)
# Only guard writes inside a git repo that is a board or plausibly a target
# (has docs/specs/approvers.md or an issue tree); a random project the user
# is hand-editing in the same session is not this gate's business.
cwd = e.get("cwd") or os.getcwd()
root = None
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None or not os.path.isfile(os.path.join(root, "docs", "specs", "approvers.md")):
    sys.exit(0)

deny("this is an orchestrator session and %s is a deliverable path in a "
     "board repo. Deliverables are role work: draft the issue, get the "
     "user's confirmation, and spawn the role (spawn.py <role> ... "
     "--issue <n>). You author only confirmed issues, PR comments, and "
     "docs/specs/approvers.md." % n)
PY

ORCH_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
