#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on git commit spec-index drift — issue #459.
#
# Zero-install baseline (contract, not CI-supplement): this script ships
# with the plugin like contract-guard.sh; it needs no gates/ checkout in
# the consumer repo, only `python3` and `git` on PATH. gates/spec_index.py
# already implements this drift check (parse_index's row regex + a sha256
# comparison), but it runs on the WORKING TREE after a commit has already
# landed (CI-supplement timing). This hook ports the same row-regex and
# hash-comparison logic inline (no import — zero-install, no repo checkout
# guaranteed at hook-invocation time beyond the commit's own cwd) so the
# same class of drift can be caught and DENIED before `git commit` ever
# writes the commit object, using the STAGED content (`git show :<path>`),
# not the working tree, so the check reflects exactly what would land.
#
# Fail-open by design: any environment gap (no python3/git, unreadable
# index, `git diff --cached` failing because this isn't a git repo yet,
# etc.) exits 0 rather than blocking an unrelated or best-effort commit.
# What must never happen is silently allowing a commit this script
# positively determined has drifted a tracked spec file without a matching
# index update in the same staged set; that path is the only one that
# exits 2.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import hashlib, json, os, re, subprocess, sys

def deny(msg):
    sys.stderr.write("spec-index-preflight: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("CG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

if not re.search(r"\bgit\s+commit\b", cmd):
    sys.exit(0)

INDEX_REL = "docs/specs/reconciled-index.md"
_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*$")

cwd = os.getcwd()
index_path = os.path.join(cwd, INDEX_REL)
if not os.path.isfile(index_path) or not os.access(index_path, os.R_OK):
    sys.exit(0)

def parse_rows(text):
    rows = []
    for line in text.splitlines():
        m = _ROW_RE.match(line)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows

try:
    with open(index_path, "r", encoding="utf-8") as f:
        onDisk_rows = parse_rows(f.read())
except OSError:
    sys.exit(0)

try:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, timeout=20, cwd=cwd,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
staged = set(line.strip() for line in r.stdout.splitlines() if line.strip())

def git_show_bytes(rel_path):
    rr = subprocess.run(
        ["git", "show", ":" + rel_path],
        capture_output=True, timeout=20, cwd=cwd,
    )
    if rr.returncode != 0:
        return None
    return rr.stdout

rows = onDisk_rows
if INDEX_REL in staged:
    staged_index_bytes = git_show_bytes(INDEX_REL)
    if staged_index_bytes is not None:
        try:
            rows = parse_rows(staged_index_bytes.decode("utf-8"))
        except UnicodeDecodeError:
            rows = onDisk_rows

mismatches = []
for rel_path, recorded_hash in rows:
    if rel_path not in staged:
        continue
    content = git_show_bytes(rel_path)
    if content is None:
        continue
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != recorded_hash:
        mismatches.append(rel_path)

if mismatches:
    names = ", ".join(mismatches)
    deny(f"staged content changed for tracked spec file(s) [{names}] but "
         f"{INDEX_REL} was not updated to match in the same staged set. "
         f"Regenerate with `python3 gates/spec_index.py --update`, stage "
         f"the updated index, and retry the commit.")
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
