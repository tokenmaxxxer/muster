#!/usr/bin/env python3
"""플로우 종결-일관성 스윕 게이트 — 보드의 이슈-PR 쌍이 함께 닫히는지 훑는다(issue-135).

`pr_reference.py`(PR 하나, 로컬 판정)와 달리 이 게이트는 보드 전체(여러
subject x role)를 훑고, 위반을 **보고만** 한다 — 아무것도 닫지 않는다
(계약 v3: GitHub 종결은 사람/오케스트레이터의 몫).

  python3 gates/closure_sweep.py [--repo <경로>] [--post]
  종료 코드 0 (위반 없음) / 1 (위반 있음, --post 없이도 보고는 stdout 에 찍는다)
"""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import pr_reference  # noqa: E402
import spawn  # noqa: E402
import ci  # noqa: E402

OPEN_PR_ON_CLOSED_ISSUE = "open-pr-on-closed-issue"
MERGED_DELIVERY_ISSUE_OPEN = "merged-delivery-issue-open"

_SWEEP_COMMENT_MARKER = "[on-the-record] closure-sweep: {digest}"


def _refs_issue(body: str, issue: int) -> tuple[bool, bool]:
    """(plain 참조 있음, Closes/Fixes/Resolves 참조 있음) — 이 이슈 번호로 한정."""
    body = body or ""
    has_closes = any(int(m.group(2)) == issue
                      for m in pr_reference._CLOSES_REF.finditer(body))
    has_plain = issue in {int(n) for n in pr_reference._PLAIN_REF.findall(body)}
    return has_plain, has_closes


def classify(issue_state: str, pr_state: str, pr_body: str, issue: int,
             has_record_evidence: bool = False) -> str | None:
    """네트워크 없는 순수 판정 (테스트 용이) — 상태 문자열과 PR 본문만으로 결정한다.

    phase-1 제안 PR(merged, plain-ref 뿐, 이슈는 열림)은 **의도된 모양**이라
    violation 이 아니다 — 계약 v3 s19. Closes/Fixes/Resolves 로 실제 인도를
    약속했을 때만 '머지됐는데 이슈는 열림'이 위반이다.

    `has_record_evidence`(issue #383)는 closes-gate가 #284에서 받아들인
    것과 같은 대안 증거다 — 브랜치의 phase-2 기록 파일이 존재하고
    `loop_state`가 채워져 있으면, PR 본문에 Closes/Fixes/Resolves가
    없어도 실제 인도로 본다. #284가 그 키워드를 선택사항으로 만든
    이후로는 키워드 부재만으로 '인도 아님'을 단정할 수 없다 — 키워드도
    기록 증거도 없을 때만 위반이 아니다."""
    has_plain, has_closes = _refs_issue(pr_body, issue)
    if issue_state == "CLOSED" and pr_state == "OPEN" and (has_plain or has_closes):
        return OPEN_PR_ON_CLOSED_ISSUE
    if pr_state == "MERGED" and issue_state == "OPEN" and (has_closes or has_record_evidence):
        return MERGED_DELIVERY_ISSUE_OPEN
    return None


def _issue_view(root: Path, issue: int) -> str | None:
    r = subprocess.run(["gh", "issue", "view", str(issue), "--json", "state",
                        "-q", ".state"], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def _pr_view_state_body(root: Path, pr: int) -> tuple[str, str] | None:
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "state,body"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    return data.get("state", ""), data.get("body", "") or ""


def find_violations(root: Path, subjects: dict | None = None,
                     issue_states: dict[int, str] | None = None) -> list[dict]:
    """보드의 각 subject x role 브랜치에 대해 이슈/PR 상태를 읽고 위반을 모은다.

    `subjects` 는 `spawn.board(root)` 와 같은 모양(subject -> role -> ...) —
    안 주면 직접 읽는다. `issue_states` 는 이슈번호 -> state 사전(선택,
    issue #189) — 주어지고 그 subject 의 이슈가 안에 있으면 `_issue_view`
    호출을 건너뛰고 그 값을 그대로 쓴다(레포 전체 한 번짜리 프리페치 재사용,
    새 `gh` 호출 종류를 추가하지 않는다). 네트워크(`gh`)만 쓰고 아무것도
    쓰지 않는다.
    """
    if subjects is None:
        subjects = spawn.board(root)
    violations = []
    for subject, roles in subjects.items():
        m = subject.split("-", 1)
        if len(m) != 2 or not m[1].isdigit():
            continue
        issue = int(m[1])
        if issue_states is not None and issue in issue_states:
            issue_state = issue_states[issue]
        else:
            issue_state = _issue_view(root, issue)
        if issue_state is None:
            continue
        for role in roles:
            branch = f"{subject}/{role}"
            pr = spawn._pr_for_branch(root, branch)
            if pr is None:
                continue
            view = _pr_view_state_body(root, pr)
            if view is None:
                continue
            pr_state, pr_body = view
            has_record_evidence = ci._phase2_record_evidence(root, pr, branch, issue)
            kind = classify(issue_state, pr_state, pr_body, issue, has_record_evidence)
            if kind:
                violations.append({"issue": issue, "pr": pr, "role": role, "kind": kind})
    return violations


def format_report(violations: list[dict]) -> str:
    return "\n".join(f"issue #{v['issue']} / PR #{v['pr']}: {v['kind']}"
                     for v in violations)


def _violations_digest(violations: list[dict]) -> str:
    key = sorted((v["issue"], v["pr"], v["kind"]) for v in violations)
    return hashlib.sha256(json.dumps(key).encode("utf-8")).hexdigest()[:12]


def post_sweep_comments(root: Path, violations: list[dict]) -> None:
    """위반이 있는 이슈마다, 그 이슈의 위반 집합에 대해 한 번만 코멘트를 단다.

    마커에 위반 집합의 해시를 넣어 — 위반 집합이 바뀌면 새 코멘트, 그대로면
    무음(`_post_crash_comment` 와 같은 read-then-check 패턴).
    """
    by_issue: dict[int, list[dict]] = {}
    for v in violations:
        by_issue.setdefault(v["issue"], []).append(v)
    for issue, vs in by_issue.items():
        marker = _SWEEP_COMMENT_MARKER.format(digest=_violations_digest(vs))
        if any(marker in c.get("body", "") for c in spawn._issue_comments(root, issue)):
            continue
        slug = spawn._repo_slug(root)
        if not slug:
            continue
        body = f"{marker}\n\n" + format_report(vs)
        subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                        "-f", f"body={body}"], cwd=root, capture_output=True, text=True)


def main() -> int:
    root = Path(".").resolve()
    argv = sys.argv[1:]
    if "--repo" in argv:
        root = Path(argv[argv.index("--repo") + 1]).resolve()
    post = "--post" in argv

    violations = find_violations(root)
    if not violations:
        print("종결 일관성 스윕: 위반 없음")
        return 0
    print("종결 일관성 스윕: 위반 발견")
    print(format_report(violations))
    if post:
        post_sweep_comments(root, violations)
    return 1


if __name__ == "__main__":
    sys.exit(main())
