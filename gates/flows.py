#!/usr/bin/env python3
"""상황판(repo-status-board)을 위한 읽기 전용 flows 데이터 계약 (issue #172).

status()/closure_sweep 과 같은 줄 — 아무것도 안 고치고, 안 posting 한다.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402

FLOWS_SCHEMA_VERSION = 1

_STAGE_MAP = {
    "scope-proposed": "proposal",
    "scope-approved": "approved",
}
# implementing/delivered/closed are role/rulebook-specific downstream states with
# no central enum today (issue #172 survey) — anything not in this map reports
# raw with stage_derived=False rather than being forced into the wrong bucket.

_BRANCH_RE = re.compile(r"^(issue-[0-9]+)/([a-z0-9-]+)$")
_BOARD_DELTA_ISSUE_RE = re.compile(r"docs/issue-([0-9]+)/")


def _stage_for(loop_state: str | None) -> tuple[str, bool]:
    if loop_state in _STAGE_MAP:
        return _STAGE_MAP[loop_state], True
    return (loop_state or "(none)"), False


def _pr_list_all(root: Path) -> list[dict]:
    """Repo-wide open-PR list, one call — replaces an O(subjects x roles)
    `_pr_for_branch` loop for `flows` (issue #172 §3: rate-limit design)."""
    r = subprocess.run(["gh", "pr", "list", "--state", "open", "--json",
                        "number,headRefName,createdAt,body,reviews"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def _pr_approved(pr: dict, comments: list[dict], approvers: set[str],
                 subject: str, role: str) -> bool:
    """Two detection paths from contract v3 s19: an `APPROVE <subject>/<role>`
    comment from an approvers.md login, or a PR review Approve from a
    different approvers.md login (`pr["reviews"]`, already fetched by
    `_pr_list_all` — no second per-PR call needed)."""
    needle = f"APPROVE {subject}/{role}"
    if any(c["body"].strip() == needle and c["login"] in approvers for c in comments):
        return True
    for rv in pr.get("reviews") or []:
        if (rv.get("state") == "APPROVED"
                and (rv.get("author") or {}).get("login") in approvers):
            return True
    return False


def _ledger_read() -> list[dict]:
    p = spawn.ROOT / "runs" / "ledger.jsonl"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _ledger_issue(entry: dict) -> int | None:
    for path in entry.get("board_delta") or []:
        m = _BOARD_DELTA_ISSUE_RE.search(str(path))
        if m:
            return int(m.group(1))
    return None


def _activity_tool_summary(name: str, inp: dict) -> str:
    if not isinstance(inp, dict):
        return name
    for key in ("command", "file_path", "path", "pattern", "query", "description"):
        val = inp.get(key)
        if not val:
            continue
        val = str(val)
        if key == "command":
            return f"{val[:60]} 실행"
        return f"{name} {val}"
    return name


def _session_last_activity(log_path: Path | None) -> dict | None:
    """세션의 session.log 마지막 유의미 레코드를 tail 로 읽어
    `{ts, kind, detail}` 로 요약한다. 로그가 없거나 파싱 불가면 `None` —
    소비자(상황판)는 여전히 JSON만 읽는다, 로그 파싱은 여기서만 한다
    (이슈 #172 FEEDBACK)."""
    if log_path is None:
        return None
    try:
        if not log_path.exists():
            return None
        size = log_path.stat().st_size
        tail_size = min(size, 65536)
        with log_path.open("rb") as fh:
            fh.seek(size - tail_size)
            data = fh.read()
        lines = data.decode("utf-8", errors="replace").splitlines()
        if tail_size < size and lines:
            lines = lines[1:]  # 앞이 잘렸을 수 있는 첫 줄은 버린다
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                           time.gmtime(log_path.stat().st_mtime))
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            rtype = rec.get("type")
            if rtype == "result":
                detail = str(rec.get("result") or rec.get("subtype") or "결과")
                return {"ts": ts, "kind": "result", "detail": detail[:80]}
            if rtype == "assistant":
                content = ((rec.get("message") or {}).get("content")) or []
                for block in reversed(content):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        detail = _activity_tool_summary(
                            block.get("name", ""), block.get("input") or {})
                        return {"ts": ts, "kind": "tool_use", "detail": detail[:80]}
                    if block.get("type") == "text":
                        first_line = (block.get("text") or "").strip().splitlines()
                        if first_line and first_line[0]:
                            return {"ts": ts, "kind": "text",
                                   "detail": first_line[0][:80]}
        return None
    except (OSError, UnicodeError):
        return None


def flows_payload(root: Path) -> dict:
    """Build the `flows --json` payload (issue #172) — read-only, matches
    `status()`'s own invariant (protocol.md §1): no mutation, no posting."""
    b = spawn.board(root)
    approvers = spawn._approvers(root)
    prs = _pr_list_all(root)
    pr_by_branch = {}
    for pr in prs:
        m = _BRANCH_RE.match(pr.get("headRefName") or "")
        if m:
            pr_by_branch[(m.group(1), m.group(2))] = pr
    comments_cache: dict[int, list[dict]] = {}

    def comments_for(subject: str, pr_number: int) -> list[dict]:
        issue_n = int(subject.split("-", 1)[1])
        if issue_n not in comments_cache:
            comments_cache[issue_n] = spawn._issue_comments(root, issue_n)
        out = list(comments_cache[issue_n])
        if pr_number and pr_number not in comments_cache:
            comments_cache[pr_number] = spawn._issue_comments(root, pr_number)
        if pr_number:
            out += comments_cache[pr_number]
        return out

    decision_queue = []
    unapproved_open_prs = []
    flows_out = []

    for subject, roles in sorted(b.items()):
        issue_n = int(subject.split("-", 1)[1])
        role_entries = []
        stage_source = None
        for role, fm in roles.items():
            loop_state = fm.get("loop_state")
            pr = pr_by_branch.get((subject, role))
            role_entries.append({"role": role, "loop_state": loop_state,
                                 "verdict": fm.get("verdict")})
            if spawn._front_role(root, subject, roles) == role:
                stage_source = loop_state
            if not pr:
                continue
            comments = comments_for(subject, pr["number"])
            approved = _pr_approved(pr, comments, approvers, subject, role)
            phase = 1 if loop_state == "scope-proposed" else 2
            if not approved:
                decision_queue.append({
                    "issue": issue_n, "pr": pr["number"], "phase": phase,
                    "role": role, "opened_at": pr.get("createdAt"),
                    "age_hours": _age_hours(pr.get("createdAt")),
                    "awaiting": "approve-scope" if phase == 1 else "approve-full",
                })
            if loop_state and loop_state != "scope-proposed" and not approved:
                unapproved_open_prs.append({
                    "issue": issue_n, "pr": pr["number"], "role": role,
                    "opened_at": pr.get("createdAt"),
                })

        stage, derived = _stage_for(stage_source)
        flows_out.append({
            "issue": issue_n, "stage": stage, "stage_derived": derived,
            "roles": role_entries,
            "prs": sorted({pr_by_branch[(subject, r)]["number"]
                          for r in roles if (subject, r) in pr_by_branch}),
        })

    roster = spawn._roster_load()
    sessions = []
    ledger_entries = _ledger_read()
    for key, e in sorted(roster.items()):
        alive = spawn._alive(e.get("pid", 0))
        elapsed_min = (int(time.time()) - e.get("ts", 0)) // 60
        verdict = "pending"
        if not alive:
            issue_n = e.get("issue")
            matches = [le for le in ledger_entries if _ledger_issue(le) == issue_n]
            verdict = matches[-1].get("outcome") if matches else None
        log_path = Path(e["log"]) if e.get("log") else None
        sessions.append({"role": e.get("role"), "issue": e.get("issue"),
                         "elapsed_min": elapsed_min, "pid": e.get("pid"),
                         "alive": alive, "verdict": verdict,
                         "last_activity": _session_last_activity(log_path)})

    ledger_by_issue: dict[int, dict] = {}
    unattributed = {"sessions": 0, "cost_usd_total": 0.0}
    for entry in ledger_entries:
        issue_n = _ledger_issue(entry)
        cost = entry.get("cost_usd") or 0.0
        outcome = entry.get("outcome") or "unknown"
        if issue_n is None:
            unattributed["sessions"] += 1
            unattributed["cost_usd_total"] += cost
            continue
        agg = ledger_by_issue.setdefault(issue_n, {
            "issue": issue_n, "sessions": 0,
            "cost_usd_total": 0.0, "outcomes": {}})
        agg["sessions"] += 1
        agg["cost_usd_total"] += cost
        agg["outcomes"][outcome] = agg["outcomes"].get(outcome, 0) + 1

    import closure_sweep
    violations = closure_sweep.find_violations(root, subjects=b)

    return {
        "schema_version": FLOWS_SCHEMA_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo": spawn._repo_slug(root),
        "decision_queue": decision_queue,
        "flows": flows_out,
        "sessions": sessions,
        "ledger": sorted(ledger_by_issue.values(), key=lambda d: d["issue"]),
        "unattributed": unattributed,
        "hygiene": {
            "closure_sweep": violations,
            "unapproved_open_prs": unapproved_open_prs,
        },
    }


def _age_hours(created_at: str | None) -> float | None:
    if not created_at:
        return None
    try:
        t = time.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return round((time.time() - time.mktime(t) + time.timezone) / 3600.0, 1)


def flows(cwd: str, as_json: bool) -> int:
    root = Path(cwd).resolve()
    payload = flows_payload(root)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"decision_queue: {len(payload['decision_queue'])}건")
    for d in payload["decision_queue"]:
        print(f"  issue-{d['issue']} PR#{d['pr']} phase{d['phase']} {d['role']} "
              f"{d['age_hours']}시간 대기 — {d['awaiting']}")
    print(f"\nflows: {len(payload['flows'])}건")
    for f in payload["flows"]:
        print(f"  issue-{f['issue']}: {f['stage']}" + ("" if f["stage_derived"] else " (raw)")
              + f"  roles={[r['role'] for r in f['roles']]}  prs={f['prs']}")
    print(f"\nsessions: {len(payload['sessions'])}건")
    for s in payload["sessions"]:
        print(f"  {'RUNNING' if s['alive'] else 'DEAD':8s} {s['role']} "
              f"issue-{s['issue']} {s['elapsed_min']}분 verdict={s['verdict']}")
    print(f"\nledger: {len(payload['ledger'])}건 (미귀속 세션 "
          f"{payload['unattributed']['sessions']}건)")
    for l in payload["ledger"]:
        print(f"  issue-{l['issue']}: 세션 {l['sessions']}건, "
              f"${l['cost_usd_total']:.2f}")
    h = payload["hygiene"]
    print(f"\nhygiene: closure_sweep {len(h['closure_sweep'])}건, "
          f"승인 흔적 없는 열린 PR {len(h['unapproved_open_prs'])}건")
    return 0

