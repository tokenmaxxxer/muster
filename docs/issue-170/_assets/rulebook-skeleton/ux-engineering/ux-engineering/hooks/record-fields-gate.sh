#!/usr/bin/env bash
__fc(){ rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then echo "fail-closed: gate aborted (rc=$rc)" >&2; exit 2; fi; }
trap __fc EXIT
# PreToolUse gate (Write|Edit|MultiEdit) — contract v3 s20, ux-engineering's own
# required-field set (adapted per issue-170 from roles/ux-engineering.json's
# `produces`, NOT copied from another role's field set).
#
# On a write whose resolved target is this role's own record
# docs/issue-<n>/reports/ux-engineering.md, require a section per required field
# below. Missing any => refuse. Skeleton: field-presence checks are a
# placeholder (substring/heading match) — harden before treating as
# load-bearing.
set -uo pipefail

case "${UX_ENGINEERING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac

deny() { echo "ux-engineering: refused — $*" >&2; exit 2; }

command -v python3 >/dev/null 2>&1 || deny "record-fields-gate.sh requires python3, which is not on PATH; denying rather than guessing."

payload="$(cat 2>/dev/null || true)"
[ -n "$payload" ] || exit 0

UX_ENGINEERING_PAYLOAD="$payload" python3 <<'PY'
import json, os, sys

REQUIRED_FIELDS = ["token-set", "rule-doc", "migration-note"]
RECORD_SUFFIX = "docs/issue-" # + "<n>/reports/ux-engineering.md"

def deny(msg):
    sys.stderr.write("ux-engineering: refused — %s\n" % msg)
    sys.exit(2)

payload = os.environ.get("UX_ENGINEERING_PAYLOAD", "")
try:
    event = json.loads(payload)
except Exception:
    sys.exit(0)

ti = event.get("tool_input") if isinstance(event, dict) else None
target = None
if isinstance(ti, dict):
    for k in ("file_path", "notebook_path"):
        v = ti.get(k)
        if isinstance(v, str):
            target = v
            break
if not target or not target.replace("\\", "/").endswith("/reports/ux-engineering.md"):
    sys.exit(0)

content = ""
if isinstance(ti, dict):
    content = ti.get("content") or ti.get("new_string") or ""

missing = [f for f in REQUIRED_FIELDS if f.replace("-", " ") not in content.lower() and f not in content.lower()]
if missing:
    deny("ux-engineering.md is missing required produces field(s): " + ", ".join(missing))
sys.exit(0)
PY
