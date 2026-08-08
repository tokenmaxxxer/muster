#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on gh pr create/edit — issue #459.
#
# Zero-install baseline (contract, not CI-supplement), same rationale as
# contract-guard.sh (gh pr merge): this script ships with the plugin and
# needs no gates/ checkout in the consumer repo, only `gh` on PATH. It ports
# gates/pr_reference.py::check_body and gates/flows.py::_plan_from_body
# inline rather than importing them, because a zero-install hook cannot
# assume gates/ is on sys.path in the consumer repo.
#
# Scope: intercepts `gh pr create` / `gh pr edit` — the acts that set a PR's
# body BEFORE the PR exists (create) or change it (edit). Unlike
# contract-guard.sh (which reads an existing PR via `gh pr view`), this hook
# extracts the body straight from the command line (--body / --body-file),
# because for `create` there is no PR yet to look up.
#
# Fail-open policy: any parse failure, missing tool, non-matching command,
# absent --body/--body-file, unreadable body-file, non-issue branch, or `gh`
# lookup failure results in exit 0 (pass through). The only path that exits
# 2 is a positive, evidence-backed determination that the body violates the
# phase-appropriate issue-reference rule (gates/pr_reference.py::check_body).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

def deny(msg, hint):
    sys.stderr.write("pr-preflight: %s\n" % msg)
    sys.stderr.write("pr-preflight: expected: %s\n" % hint)
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

if not re.search(r"\bgh\s+pr\s+(create|edit)\b", cmd):
    sys.exit(0)

# --- extract PR body from the command line itself --------------------------
body = None
m = re.search(r"--body(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd)
if m:
    raw = m.group(1)
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        raw = raw[1:-1]
    body = raw
else:
    m = re.search(r"--body-file(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd)
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        try:
            with open(raw, "r", encoding="utf-8") as f:
                body = f.read()
        except OSError:
            sys.exit(0)  # unreadable body-file — nothing to check yet, fail-open

if body is None:
    sys.exit(0)  # no --body/--body-file on the command — nothing to check yet

# --- subject issue number + role from the current branch -------------------
try:
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True, timeout=20)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
branch = r.stdout.strip()
bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
if not bm:
    sys.exit(0)
issue = int(bm.group(1))
role = bm.group(2)

# --- phase determination via issue comments + approvers.md -----------------
def gh_json(*args):
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None

comments = gh_json("issue", "view", str(issue), "--json", "comments", "-q", ".comments")
if comments is None:
    sys.exit(0)  # gh lookup failed — fail-open, not a verdict

approvers_path = os.path.join(os.getcwd(), "docs", "specs", "approvers.md")
approvers = set()
if os.path.isfile(approvers_path):
    for line in open(approvers_path, encoding="utf-8"):
        mm = re.match(r"^\s*-\s*(\S+)", line)
        if mm:
            approvers.add(mm.group(1))

needle = "APPROVE issue-%d/%s" % (issue, role)
phase2 = any(
    (c.get("body") or "").strip() == needle
    and (c.get("author", {}) or {}).get("login") in approvers
    for c in (comments or [])
)
phase = "phase2" if phase2 else "phase1"

# --- plan parsing (ported from gates/flows.py::_plan_from_body) ------------
_PLAN_STEP_RE = re.compile(r"^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$")

def _plan_from_body(issue_body):
    lines = (issue_body or "").splitlines()
    start = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped == "## 실행 계획" or stripped.startswith("## 실행 계획 "):
            start = i + 1
            break
    if start is None:
        return None
    steps = []
    in_fence = False
    for line in lines[start:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped.startswith("##"):
            break
        mm = _PLAN_STEP_RE.match(stripped)
        if not mm:
            continue
        done = mm.group(1) in ("x", "X")
        step_n = int(mm.group(2))
        roles = [r.strip() for r in mm.group(3).split("‖")]
        steps.append({"step": step_n, "roles": roles, "done": done})
    return steps

plan = None
if phase == "phase2":
    issue_body = gh_json("issue", "view", str(issue), "--json", "body", "-q", ".body")
    if issue_body is None:
        sys.exit(0)  # gh lookup failed — fail-open
    plan = _plan_from_body(issue_body)

# --- check_body (ported from gates/pr_reference.py) -------------------------
_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")

def check_body(issue, body, phase, plan=None):
    body = body or ""
    if phase == "phase2":
        if plan:
            incomplete = [s for s in plan if not s["done"]]
            max_step = max(s["step"] for s in plan) if plan else 0
            only_last_incomplete = (
                len(incomplete) == 1 and incomplete[0]["step"] == max_step
            )
            if incomplete and not only_last_incomplete:
                mm = _CLOSES_REF.search(body)
                if mm and int(mm.group(2)) == issue:
                    return ["계획에 미완 스텝이 남아 있다 — 마지막 스텝의 "
                            "phase-2 PR에서만 Closes/Fixes/Resolves를 쓴다."]
                return []
        mm = _CLOSES_REF.search(body)
        if not mm or int(mm.group(2)) != issue:
            return [f"PR 본문에 'Closes #{issue}'(또는 Fixes/Resolves)가 없다 — "
                    f"phase-2 인도 PR은 이슈를 명시적으로 닫아야 한다."]
        return []
    refs = {int(n) for n in _PLAIN_REF.findall(body)}
    if issue not in refs:
        return [f"PR 본문에 '#{issue}' 참조가 없다 — phase-1 제안 PR도 자기 "
                f"이슈를 본문에서 가리켜야 한다(Closes/Fixes/Resolves는 금지: "
                f"phase-1 머지가 이슈를 자동으로 닫으면 안 된다)."]
    return []

bad = check_body(issue, body, phase, plan)
if bad:
    if phase == "phase2":
        hint = f"'Closes #{issue}' (or Fixes/Resolves #{issue}) in the PR body"
    else:
        hint = f"a plain '#{issue}' reference in the PR body (no Closes/Fixes/Resolves)"
    deny(bad[0], hint)
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
