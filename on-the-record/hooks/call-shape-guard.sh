#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): deny-only, session-side mirror of
# gates.py's subprocess_call_shape_divergence and sibling_mention_check
# (issue #419, ported per issue #512 — gates/ci.py's runner disappeared
# with GitHub Actions retirement, #460).
#
# Zero-install: no `import gates`, root discovered by walking up from the
# hook payload's `cwd` for a `.git` directory, same pattern as
# record-claim-guard.sh (issue #457's port) and this repo's other
# zero-install hooks (docs/specs/enforcement-boundary.md).
#
# Two checks, both scoped to `.py` writes:
#   1. subprocess_call_shape_divergence: repo-wide (git ls-files, not
#      diff-scoped — this check's own logic requires whole-tree grouping
#      to compare call sites for the same command).
#   2. sibling_mention_check: diff-scoped to the file being written,
#      checked against the *local working-tree copy* of the current
#      branch's docs/issue-<n>/reports/<role>.md record (no `gh` fetch).
#      If the branch isn't issue-<n>/<role> shaped or the record doesn't
#      exist yet, this half is a no-op (prospective limitation, same as
#      gates.py's own).
#
# Fails closed (trap remaps non-0/2 exit to 2). Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 2

IFS='' read -r -d '' GUARD <<'PY' || true
import ast, json, os, posixpath, re, subprocess, sys

def deny(msg):
    sys.stderr.write("call-shape-guard: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("CSG_PAYLOAD", ""))
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
if not isinstance(p, str) or not p or not p.endswith(".py"):
    sys.exit(0)

n = posixpath.normpath(p.replace("\\", "/"))
cwd = e.get("cwd") or os.getcwd()
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))

root = None
probe = posixpath.dirname(d)
while probe and probe != "/":
    if os.path.isdir(posixpath.join(probe, ".git")):
        root = probe
        break
    probe = posixpath.dirname(probe)
if root is None:
    sys.exit(0)

# The new content this write would produce for the touched file.
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
new_content = "\n".join(content_parts)
if not new_content.strip():
    sys.exit(0)

rel = os.path.relpath(d, root).replace(os.sep, "/")

# ---- check 1: subprocess_call_shape_divergence (repo-wide) ----
_SEMANTIC_FLAGS = {"-X", "--method", "-f", "--field"}

def _call_flag_set(call):
    if not call.args:
        return None
    first = call.args[0]
    if not isinstance(first, ast.List):
        return None
    elts = []
    for el in first.elts:
        if isinstance(el, ast.Constant) and isinstance(el.value, str):
            elts.append(el.value)
        else:
            return None
    if not elts:
        return None
    return {a for a in elts if a in _SEMANTIC_FLAGS}

def _is_subproc_call(node):
    if not isinstance(node, ast.Call):
        return False
    fn = node.func
    return (
        (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
         and fn.value.id == "subprocess"
         and fn.attr in ("run", "check_output", "check_call", "Popen"))
        or (isinstance(fn, ast.Name) and fn.id in ("run", "check_output",
                                                     "check_call", "Popen")))

def _file_calls(rel_path, text):
    out = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not _is_subproc_call(node):
            continue
        flags = _call_flag_set(node)
        if flags is None or not node.args or not isinstance(node.args[0], ast.List):
            continue
        elts = [el.value for el in node.args[0].elts
                if isinstance(el, ast.Constant) and isinstance(el.value, str)]
        if len(elts) < 2:
            continue
        out.append((rel_path, node.lineno, (elts[0], elts[1]), frozenset(flags)))
    return out

pr = subprocess.run(["git", "-C", root, "ls-files", "*.py"],
                     capture_output=True, text=True)
files = pr.stdout.splitlines() if pr.returncode == 0 else []

calls_by_cmd = {}
for f_rel in files:
    if f_rel == rel:
        continue  # replaced by the pending write's content below
    fpath = os.path.join(root, f_rel)
    try:
        text = open(fpath, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for site in _file_calls(f_rel, text):
        calls_by_cmd.setdefault(site[2], []).append((site[0], site[1], site[3]))
for site in _file_calls(rel, new_content):
    calls_by_cmd.setdefault(site[2], []).append((site[0], site[1], site[3]))

bad = []
for cmd, calls in calls_by_cmd.items():
    if not any(c[0] == rel for c in calls):
        continue  # only deny when THIS write is part of the divergence
    if len(calls) < 2:
        continue
    flagsets = {c[2] for c in calls}
    if len(flagsets) > 1:
        sites = ", ".join(f"{r}:{ln}" for r, ln, _ in calls)
        bad.append(
            f"명령 {' '.join(cmd)!r} 의 호출부들이 flag 모양이 다르다 "
            f"({sites}) — 같은 명령이 서로 다른 의미로 호출되는, #388 과 "
            f"같은 모양의 재발일 수 있다 (issue #419).")

# ---- check 2: sibling_mention_check (diff-scoped to this write) ----
_SIBLING_MARKER = re.compile(r"^\s*#\s*sibling\s*:\s*([\w.]+)\s*$", re.MULTILINE)
_SIBLINGS_SECTION = re.compile(r"^##\s*Siblings\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)

def _marked_defs(text):
    names = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if _SIBLING_MARKER.match(ln):
            for nxt in lines[i + 1:]:
                if nxt.strip() == "" or nxt.strip().startswith("#"):
                    continue
                m = re.match(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)", nxt)
                if m:
                    names.append(m.group(1))
                break
    return names

marked = _marked_defs(new_content)
if marked:
    branch = None
    br = subprocess.run(["git", "-C", root, "branch", "--show-current"],
                        capture_output=True, text=True)
    if br.returncode == 0:
        branch = br.stdout.strip()
    m = re.match(r"^issue-(\d+)/([\w-]+)$", branch or "")
    if m:
        record_path = os.path.join(
            root, "docs", f"issue-{m.group(1)}", "reports", f"{m.group(2)}.md")
        if os.path.isfile(record_path):
            try:
                record_text = open(record_path, encoding="utf-8",
                                    errors="replace").read()
            except OSError:
                record_text = ""
            sm = _SIBLINGS_SECTION.search(record_text)
            section_body = sm.group(1) if sm else ""
            for name in marked:
                if name not in section_body:
                    bad.append(
                        f"{rel} 의 `{name}` 이 `# sibling:` 로 표시됐지만, "
                        f"현재 브랜치 레코드({os.path.relpath(record_path, root)})의 "
                        f"`## Siblings` 섹션에 언급되지 않았다 (issue #419).")

if bad:
    deny("\n".join(bad))
sys.exit(0)
PY

CSG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
