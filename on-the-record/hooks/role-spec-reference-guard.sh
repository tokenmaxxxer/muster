#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): deny-only reference-resolution guard
# for the 6 batch-1 verification-family roles (issue #521, realizing the
# #515 template's reference_resolution rule).
#
# Each of execution-observation/conformance-review/defect-verification/
# security-threat-model/accessibility/secure-coding's roles/specs/*.spec.json
# declares: every ref/ref[]-typed field value must resolve to an existing
# repo path, commit sha, or line-anchored citation (issue-515 invariant 2).
# A role's record is markdown prose, not the raw spec JSON, so this hook
# checks the same shape record-claim-guard.sh already checks for docs/
# issue-*/reports/** generally (backtick-quoted relative paths resolve in
# the working tree) — scoped here to just the 6 verification-family
# roles' own record files (gates/role_spec_shape.py:record_path_role),
# via gates/role_spec_shape.py:reference_resolution_check.
#
# Zero-install: same pattern as record-claim-guard.sh — one Python
# one-liner reading the PreToolUse payload from env, walking up from cwd
# for .git to find repo root.
#
# Fails closed (trap remaps non-0/2 exit to 2). Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gates_dir="$(cd "$script_dir/../../gates" && pwd)"

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, sys

sys.path.insert(0, os.environ["RSRG_GATES_DIR"])
import role_spec_shape

def deny(msg):
    sys.stderr.write("role-spec-reference-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("RSRG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict):
    sys.exit(0)
if (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
if not isinstance(ti, dict):
    sys.exit(0)
p = ti.get("file_path")
if not isinstance(p, str) or not p:
    sys.exit(0)

n = posixpath.normpath(p.replace("\\", "/"))
if role_spec_shape.record_path_role(n) is None:
    sys.exit(0)

content_parts = []
nc = ti.get("content")
if isinstance(nc, str):
    content_parts.append(nc)
ns = ti.get("new_string")
if isinstance(ns, str):
    content_parts.append(ns)
edits = ti.get("edits")
if isinstance(edits, list):
    for ed in edits:
        if isinstance(ed, dict) and isinstance(ed.get("new_string"), str):
            content_parts.append(ed["new_string"])
content = "\n".join(content_parts)
if not content.strip():
    sys.exit(0)

cwd = e.get("cwd") or os.getcwd()
root = None
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    sys.exit(0)

bad = role_spec_shape.reference_resolution_check(content, root)
if bad:
    deny("\n".join(bad))
sys.exit(0)
PY

RSRG_PAYLOAD="$payload" RSRG_GATES_DIR="$gates_dir" python3 -c "$GUARD"
rc=$?
exit "$rc"
