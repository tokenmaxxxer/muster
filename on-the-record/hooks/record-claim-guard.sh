#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): deny-only, session-side mirror of
# gates.py's record-claim-integrity checks (issue #457, porting Group A+B
# of docs/issue-457/proposals/2026-08-08-gate-porting-order.md).
#
# gates.py runs these as CI diff-scans against a whole PR; a PreToolUse
# hook only ever sees one write's resulting content, so this is a
# write-time approximation of the same intent, not a byte-identical port:
# catch the claim shape at the moment it is typed, instead of at PR-review
# time days later (#332's generator point).
#
# Ported checks, all scoped to writes under docs/issue-*/reports/** or
# work/docs/issue-*/reports/** (a role's own record):
#   - #333 mirror: a bare "N of M"/"N items" count claim with no code-fence
#     reproduction and no `derived: ...` citation.
#   - #310 mirror: an `unverifiable:` escape line with no reason text.
#   - #331 mirror: an `Acceptance verification` "checked: X — result: ..."
#     line whose result is `unverifiable` but carries no reason.
#   - #330 mirror: a backtick-quoted relative path referenced in the new
#     content that does not exist anywhere in the working tree — an
#     orphaned reference caught at write time instead of PR review.
#
# Fails closed (trap remaps non-0/2 exit to 2), matching this plugin's
# house style. Kill switch: ORCHESTRATE_OFF=1.
#
# issue #517: the four checks below used to carry their own regex copies
# here. They now call into gates/record_lint.py's functions — the same
# ones `record_lint`'s CLI and gates/ci.py use — so there is exactly one
# place each rule's logic lives.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gates_dir="$(cd "$script_dir/../../gates" && pwd)"

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

sys.path.insert(0, os.environ["RCG_GATES_DIR"])
import record_lint

def deny(msg):
    sys.stderr.write("record-claim-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("RCG_PAYLOAD", ""))
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
if not re.search(r"(^|/)docs/issue-[^/]+/reports/", n):
    sys.exit(0)

# The new content: Write carries it directly; Edit/MultiEdit carry only
# the changed fragment(s) — check those fragments (issue #457 Group A/B
# is a write-time approximation, not a full-file re-derivation).
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

bad = []

# #310/#331/#333 mirrors: full-text checks, apply directly to the write's
# content fragment — same functions gates/record_lint.py aggregates.
bad += record_lint.unverifiable_reason_check(content)
bad += record_lint.checked_claim_reason_check(content)
bad += record_lint.bare_count_claim_check(content)

# #330 mirror: a backtick-quoted relative path that resolves nowhere in
# the working tree is an orphaned reference caught at write time.
cwd = e.get("cwd") or os.getcwd()
root = None
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is not None:
    bad += record_lint.orphaned_path_reference_check(
        record_lint.Path(root), content)

if bad:
    deny("\n".join(bad))
sys.exit(0)
PY

RCG_PAYLOAD="$payload" RCG_GATES_DIR="$gates_dir" python3 -c "$GUARD"
rc=$?
# issue #517 before-landing hunt: do NOT disarm the fail-closed trap here.
# `import record_lint` (new) can crash for reasons unrelated to a genuine
# violation (e.g. RCG_GATES_DIR resolving to a bad path) — that crash must
# still fail closed (exit 2), which only happens if the trap stays armed
# through this `exit`.
exit "$rc"
