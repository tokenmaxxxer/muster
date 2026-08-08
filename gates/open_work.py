#!/usr/bin/env python3
"""issue-472 (issue-467 ADR Batch B, #379) — 제약을 고정된 선택지로
프레이밍하기 전에 열린 이슈/PR 을 확인했는지 검사하기 위한 쿼리 구성.

`build_open_work_query` 는 `gh issue list --search` / `gh pr list
--search` 에 넘길 쿼리 파라미터만 만든다 — 네트워크 호출은 하지 않는다.
실제로 열린 이슈/PR 이 존재하는지 찾아내는 것(라이브 조회)은 이 함수의
검사 범위 밖이다: #379 자체의 acceptance 문구가 명시하는 한계이고,
유닛 테스트 안에서 라이브 네트워크를 단언하지 않는다는 제약과도
일치한다. 호출자가 이 함수가 반환한 파라미터를 `subprocess` 로 넘겨
실제 조회를 수행한다."""
from __future__ import annotations


def build_open_work_query(keyword: str) -> dict:
    """제약 키워드 하나에 대해 `gh issue list` / `gh pr list` 검색
    파라미터를 구성한다.

    빈(또는 공백만 있는) 키워드는 거부한다 — 빈 키워드로 만든 쿼리는
    "열린 작업이 없다"를 의미 없이 참으로 만들어버려 #379 가 막으려는
    바로 그 실수(확인 없이 고정된 선택지로 프레이밍)를 검사 자체가
    재현하게 된다."""
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError("keyword must be a non-empty string")
    stripped = keyword.strip()
    search = f"is:open {stripped}"
    return {
        "issue_search": search,
        "pr_search": search,
        "issue_args": ["gh", "issue", "list", "--state", "open", "--search", search],
        "pr_args": ["gh", "pr", "list", "--state", "open", "--search", search],
    }
