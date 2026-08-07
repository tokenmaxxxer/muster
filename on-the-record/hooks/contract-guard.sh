#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-effect gate on gh pr merge — issue #441.
#
# Zero-install baseline (contract, not CI-supplement): this script ships
# with the plugin like deliverable-guard.sh; it needs no gates/ checkout in
# the consumer repo, only `gh` on PATH, because the checks it runs
# (ci.py/pr_reference.py/closure_sweep.py single-PR case/landing_readiness.py
# per the proposal's item-1 table, docs/issue-441/proposals/
# 2026-08-07-contract-enforcement-boundary.md) are all read-only `gh`
# lookups against GitHub, not local-checkout diffs.
#
# Scope: intercepts only `gh pr merge` (the delivering act). It folds in
# the phase-2 "Closes/Fixes/Resolves #<issue>" requirement (pr_reference.py
# phase2 path, closure_sweep.py single-PR case's specific violating act) —
# the requirement a consumer without any local install would otherwise
# never see enforced at all. Phase is determined the same way
# gates/ci.py._approved_roles_on_issue does: an `APPROVE issue-<n>/<role>`
# comment from an approvers.md account on the issue means phase-2.
#
# Fail-open by design difference from deliverable-guard.sh: deliverable-guard
# denies WRITES (cheap to re-attempt, high blast radius if wrong-allowed).
# This gates a PR MERGE (expensive to undo, and `gh`/network failures are
# common in sandboxed sessions) — so a lookup failure here is reported and
# passed through rather than blocking an unrelated command. What must never
# happen is silently approving a merge this script positively determined
# violates the contract; that path is the only one that exits 2.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

def deny(msg):
    sys.stderr.write("contract-guard: %s\n" % msg)
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

if not re.search(r"\bgh\s+pr\s+merge\b", cmd):
    sys.exit(0)
rest = re.split(r"\bgh\s+pr\s+merge\b", cmd, maxsplit=1)[1]
num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
if not num_m:
    # `gh pr merge` with no explicit number merges the PR for the current
    # branch — can't resolve that without a repo checkout, which this
    # zero-install hook does not assume. Recorded honestly as unreached
    # rather than guessed at.
    sys.exit(0)
pr = num_m.group(1)

def gh_json(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None

pr_data = gh_json("pr", "view", pr, "--json", "body,number")
if pr_data is None:
    sys.exit(0)  # gh lookup failed — fail-open per header note, not a verdict
body = pr_data.get("body") or ""

_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")
_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
closes_m = _CLOSES_REF.search(body)
plain_refs = [int(n) for n in _PLAIN_REF.findall(body)]
issue = int(closes_m.group(2)) if closes_m else (plain_refs[0] if plain_refs else None)
if issue is None:
    sys.exit(0)  # no issue reference at all — pr_reference.py's own scope, not this hook's new ground

approvers_path = os.path.join(os.getcwd(), "docs", "specs", "approvers.md")
approvers = set()
if os.path.isfile(approvers_path):
    for line in open(approvers_path, encoding="utf-8"):
        mm = re.match(r"^\s*-\s*(\S+)", line)
        if mm:
            approvers.add(mm.group(1))

comments = gh_json("issue", "view", str(issue), "--json", "comments", "-q", ".comments") or []
prefix = "APPROVE issue-%d/" % issue
phase2 = any(
    (c.get("body") or "").strip().startswith(prefix)
    and c.get("author", {}).get("login") in approvers
    and (c.get("body") or "").strip()[len(prefix):]
    for c in comments
)
if not phase2:
    sys.exit(0)  # phase-1 PR: no closing-keyword obligation (pr_reference.py phase1 path)

if not closes_m or int(closes_m.group(2)) != issue:
    deny(f"PR #{pr} merges against a phase-2 issue (#{issue}) with no "
         f"'Closes #{issue}' (or Fixes/Resolves) in its body. Per run.md / "
         f"gates/pr_reference.py phase-2 rule: a phase-2 delivering PR must "
         f"close its issue explicitly. Denied before the merge executes.")
PY

CG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
