#!/usr/bin/env python3
"""이슈 뭉개기 게이트 단위 테스트 — 네트워크 없음, 리터럴 문자열만
(issue-328). `test_gates.py` 의 `pr_reference` 테스트와 같은 모양.

  python3 test_issue_bundling.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gates"))
import issue_bundling


def t_title_english_and_flagged():
    bad = issue_bundling.check_title(
        "Fix the login page and rewrite the billing pipeline")
    assert bad, "영어 'and' 접속사 제목이 뭉개기로 잡혀야 한다"


def t_title_korean_conjunctions_flagged():
    for word in ("및", "그리고"):
        bad = issue_bundling.check_title(f"로그인 버그 수정 {word} 결제 파이프라인 재작성")
        assert bad, f"'{word}' 접속사 제목이 뭉개기로 잡혀야 한다"


def t_title_normal_not_flagged():
    assert issue_bundling.check_title(
        "gates/issue_bundling.py 에 새 게이트 모듈 추가") == []


def t_title_quoted_and_not_flagged():
    # 백틱/따옴표 안의 " and " 는 인용된 문구지 접속사가 아니다.
    assert issue_bundling.check_title(
        "rename `foo and bar.py` to `baz.py`") == []


def t_body_missing_acceptance_section_blocks():
    bad = issue_bundling.check_body("no acceptance heading here at all")
    assert bad, "`## Acceptance` 섹션이 없으면 검사 불가로 차단해야 한다"


def t_body_unrelated_path_roots_flagged():
    body = """## Acceptance

- fix `spawn.py`'s retry loop
- rewrite `on-the-record/hooks/foo.py`'s output format
"""
    bad = issue_bundling.check_body(body)
    assert bad, "무관한 최상위 경로(spawn.py vs on-the-record/...)는 뭉개기로 잡혀야 한다"


def t_body_shared_top_level_root_not_flagged():
    # 같은 최상위 디렉터리(gates/) 아래 여러 파일 — 정상적인 단일 메커니즘
    # 다중 파일 변경이 오탐되면 안 된다.
    body = """## Acceptance

- add `gates/issue_bundling.py`
- add tests exercising `gates/issue_bundling.py` alongside `gates/other_helper.py`
"""
    assert issue_bundling.check_body(body) == []


def t_body_no_path_tokens_not_flagged():
    body = """## Acceptance

- the button should be blue
- the button should be clickable
"""
    assert issue_bundling.check_body(body) == []


def t_check_combines_title_and_body():
    good_title, good_body = "single mechanism fix", "## Acceptance\n\n- `gates/x.py`\n"
    assert issue_bundling.check_title(good_title) == []
    assert issue_bundling.check_body(good_body) == []


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
