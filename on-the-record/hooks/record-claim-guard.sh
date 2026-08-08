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
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, sys

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

# #310/#331 mirror: unverifiable: escapes need a real reason.
for m in re.finditer(r"(?im)^\s*[-*]?\s*unverifiable\s*:\s*(.*)$", content):
    reason = m.group(1).strip()
    if not reason:
        bad.append("`unverifiable:` 줄에 이유가 없다 (issue #310) — "
                    "`unverifiable: <이유>` 형태로 왜 기계 검사가 불가능한지 "
                    "적어야 한다.")

_CHECKED_CLAIM_LINE = re.compile(
    r"^\s*[-*]\s*.+—\s*checked:\s*(\S+)\s*—\s*"
    r"result:\s*(pass|fail|unverifiable)(?::\s*(.+))?\s*$")
for ln in content.splitlines():
    cm = _CHECKED_CLAIM_LINE.match(ln)
    if not cm:
        continue
    result, reason = cm.group(2), cm.group(3)
    if result == "unverifiable" and not (reason and reason.strip()):
        bad.append("Acceptance verification 의 `unverifiable` 항목에 이유가 "
                    f"없다 (issue #331): {ln.strip()!r}")

# #333 mirror: bare "N of M"/"N items" counts need derived: or a fence.
in_fence = False
_COUNT_RATIO = re.compile(r"\d+\s*(?:of|/)\s*\d+")
_COUNT_NOUN = re.compile(
    r"\d+\s+(?:detection\s+)?(?:items?|works?|checks?|cases?|tests?)\b")
_DERIVED_TAG = re.compile(r"`derived:\s*\S.*?`")
for line in content.splitlines():
    stripped = line.strip()
    if stripped.startswith("```"):
        in_fence = not in_fence
        continue
    if in_fence:
        continue
    for pat in (_COUNT_RATIO, _COUNT_NOUN):
        for cm in pat.finditer(line):
            tail = line[cm.end():]
            if _DERIVED_TAG.match(tail.lstrip()):
                continue
            bad.append("레코드에 근거 없는 개수 주장 (issue #333): "
                       f"{line.strip()!r} — 숫자가 코드펜스 재현이나 "
                       "`derived: ...` 인용 없이 그냥 타이핑되어 있다.")
            break

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
    _PATH_REF = re.compile(
        r"`((?:src|test|tests|docs|gates|on-the-record)/[^`\s]+)`")
    for m in _PATH_REF.finditer(content):
        ref = m.group(1)
        if any(ch in ref for ch in ("*", "?", "<", ">")):
            continue
        if not os.path.exists(os.path.join(root, ref)):
            bad.append(f"레코드가 존재하지 않는 경로를 참조한다 (issue #330): "
                       f"`{ref}` — 리치(reach)가 끊긴 참조다.")

if bad:
    deny("\n".join(bad))
sys.exit(0)
PY

RCG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
