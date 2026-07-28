#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit|NotebookEdit): deny-only. In an
# orchestrator session (this plugin enabled, no CLAUDE_ROLE), deliverables
# are ROLE WORK — the coding-rulebook lesson, enforced mechanically after
# a live session authored a requirements doc itself despite the directive.
#
# Denied: writes under a target repo's src/, test/, or docs/ trees.
# Allowed: docs/specs/approvers.md (the one file the orchestrator is
# sanctioned to write, with the user's confirmation), and anything outside
# those trees (scratch files, the muster checkout itself).
# Kill switch: ORCHESTRATE_OFF=1. Fail closed on non-0/2.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

case "$payload" in
  *src/*|*test/*|*docs/*) ;;
  *) trap - EXIT; exit 0 ;;
esac

command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

def deny(msg):
    sys.stderr.write("orchestrate: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("ORCH_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)
if (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
p = ti.get("file_path") or ti.get("notebook_path") if isinstance(ti, dict) else None
if not isinstance(p, str) or not p:
    sys.exit(0)

n = posixpath.normpath(p.replace("\\", "/"))
m = re.search(r"(^|/)(src|test|docs)/", n)
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
