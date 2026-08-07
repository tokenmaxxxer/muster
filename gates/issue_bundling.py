#!/usr/bin/env python3
"""이슈 뭉개기(bundling) 게이트 — 하나의 이슈에 서로 무관한 여러 문제가
섞여 있는지 검사한다(issue-328).

on-the-record 가 이슈 제목/본문을 직접 짓는 코드 호출부는 없다(설문 확인
— `spawn.py` 는 기존 이슈에 댓글만 단다) — 그래서 이 게이트는 title/body
텍스트에 대한 사후 기계 검사로 둔다, 다른 게이트(`gates/pr_reference.py`)
와 같은 모양으로: 네트워크 없는 순수 `check_*(text) -> list[str]` +
`gh issue view` 로 실 텍스트를 읽는 얇은 CLI.

`gates/gates.py` 의 "불확실하면 막는다" 철학을 따른다: `## Acceptance`
섹션을 못 찾거나 이슈 본문을 못 읽으면 "검사할 게 없다"가 아니라 "검사할
수 없다" — 차단한다.

세 가지 tell 중 이 게이트가 기계적으로 검사하는 것은 둘뿐이다:
제목의 접속사(conjunction), 그리고 Acceptance 항목들의 경로 분산
(path spread). 세 번째 — "서로 다른 role 이 작업할 것" — 은 이슈 텍스트에
구조화된 role 배정 데이터가 없어 검사 불가하다(#310 요구대로 여기 명시:
의도적으로 검사하지 않는다, 조용히 커버된 척하지 않는다).

  python3 gates/issue_bundling.py <issue-number> [--repo <경로>]
  종료 코드 0 통과 / 1 차단
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

# 인용구/코드펜스 안의 " and "/" 및 "/" 그리고 " 는 접속사가 아니라 인용된
# 문구일 수 있다(예: 커맨드 예시, 파일명) — 백틱/큰따옴표 스팬 밖에서만 본다.
_QUOTED_SPAN = re.compile(r"`[^`]*`|\"[^\"]*\"")
_CONJUNCTION = re.compile(r"\s(and|및|그리고)\s")

_ACCEPTANCE_HEADING = re.compile(r"(?m)^#{1,6}\s*Acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s+\S")
_BULLET = re.compile(r"(?m)^\s*[-*]\s+(.*)$")
# 인라인 백틱 안의 경로 형태 토큰 — 최소 한 개의 `/` 또는 `.` 를 포함해야
# "경로 비슷한" 것으로 취급한다 (단어 하나만 백틱에 감싼 경우는 제외).
_BACKTICK_PATH = re.compile(r"`([^`]+)`")


def _strip_quoted(text: str) -> str:
    """접속사 검사 전, 백틱/큰따옴표로 인용된 구간을 지운다."""
    return _QUOTED_SPAN.sub(" ", text)


def check_title(title: str) -> list[str]:
    """제목에 인용구 밖 등위 접속사(and/및/그리고)가 있으면 뭉개기 신호로
    본다. 서술적 제목("check permissions and validate input" 처럼 단일
    메커니즘을 나열하는 경우)까지 잡는 과탐이 있을 수 있음을 알고, 이슈가
    스스로 명시한 tell 을 그대로 매칭한다 — 더 깊은 의미 분석은 하지
    않는다(제안의 Rationale 참조: 결정론성이 목표다)."""
    title = title or ""
    m = _CONJUNCTION.search(_strip_quoted(title))
    if not m:
        return []
    return [f"제목에 접속사({m.group(1)!r})로 이어진 절이 있다 — 서로 "
            f"무관한 문제가 하나의 이슈로 뭉개졌을 수 있다: {title!r}"]


def _acceptance_section(body: str) -> str | None:
    """`## Acceptance` (임의 헤딩 레벨) 섹션 본문만 잘라낸다. 못 찾으면
    None — 호출자가 fail-closed 로 처리한다."""
    m = _ACCEPTANCE_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[:nxt.start()] if nxt else rest


def _path_root(token: str) -> str | None:
    """백틱 토큰이 경로 형태(`/` 또는 `.` 포함)면 최상위 세그먼트를 낸다.
    확장자만 있는 단어(예: `foo.py` 단독 파일도 루트는 자기 자신)와
    디렉터리 접두 경로(`on-the-record/hooks/x.py` -> `on-the-record`) 를
    같은 방식으로 다룬다."""
    if "/" not in token and "." not in token:
        return None
    return token.split("/")[0]


def check_body(body: str) -> list[str]:
    """`## Acceptance` 아래 최상위 불릿들이 서로 다른 최상위 경로 루트를
    가리키면(공통 루트 없이 둘 이상) 뭉개기 신호로 본다. `## Acceptance`
    섹션 자체를 못 찾으면 "검사할 게 없다"가 아니라 "검사할 수 없다" —
    차단한다(`gates/gates.py` 의 fail-closed 원칙과 동일)."""
    body = body or ""
    section = _acceptance_section(body)
    if section is None:
        return ["`## Acceptance` 섹션을 찾을 수 없다 — 뭉개기 검사를 "
                "수행할 수 없다 (fail closed)."]

    roots: set[str] = set()
    for bullet in _BULLET.findall(section):
        for token in _BACKTICK_PATH.findall(bullet):
            root = _path_root(token)
            if root:
                roots.add(root)

    if len(roots) >= 2:
        return [f"Acceptance 항목들이 서로 다른 최상위 경로({', '.join(sorted(roots))}) "
                f"를 가리킨다 — 공통 루트가 없는 무관한 문제가 하나의 이슈로 "
                f"뭉개졌을 수 있다."]
    return []


def _issue_view(repo: Path, issue: int) -> tuple[str, str] | None:
    r = subprocess.run(
        ["gh", "issue", "view", str(issue), "--json", "title,body"],
        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    data = json.loads(r.stdout)
    return data.get("title", ""), data.get("body", "")


def check(repo: Path, issue: int) -> list[str]:
    """`gh issue view` 로 제목/본문을 읽어 `check_title`/`check_body` 에
    위임한다. 읽기 자체가 실패하면 fail-closed 차단."""
    got = _issue_view(repo, issue)
    if got is None:
        return [f"이슈 #{issue} 를 읽을 수 없다(`gh issue view` 실패) — "
                f"검사 불가는 통과가 아니다."]
    title, body = got
    return check_title(title) + check_body(body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: issue_bundling.py <issue-number> [--repo <경로>]")
        return 1
    issue = int(sys.argv[1])
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    bad = check(repo, issue)
    if not bad:
        print("게이트 통과")
        return 0
    print("게이트 차단:")
    for b in bad:
        print(f"  - {b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
