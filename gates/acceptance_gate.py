#!/usr/bin/env python3
"""수용기준 실행가능성 게이트 — 이슈의 `## Acceptance` 절이 실행가능한
산출물(테스트/게이트/CI job)을 가리키는지, 또는 명시적으로
`unverifiable:` 로 이유를 대는지 검사한다(issue-310).

프로즈만 있는 Acceptance 는 통과가 아니다 — 문장 하나로 요구사항을
"닫는" 네 가지 우회(약속/메모/리스트 한 줄/문서 문장) 중 마지막 형태를
막는 것이 이 게이트의 목적이다. `gh` 호출이 없어 네트워크 없이
단위테스트 가능하다(`record_enums`/`classify()` 와 같은 관례).

  python3 gates/acceptance_gate.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")
_ARTIFACT_REF = re.compile(
    r"`[^`]*(?:test/|gates/)[^`]*`"
    r"|^\s*[-*]?\s*(gate|check)\s*:\s*\S+",
    re.IGNORECASE | re.MULTILINE,
)
_UNVERIFIABLE = re.compile(r"^\s*[-*]?\s*unverifiable\s*:\s*\S",
                            re.IGNORECASE | re.MULTILINE)
# issue-416: 행동 주장(실행가능 산출물 참조)에 붙는 두 필드. 둘 다 존재-검사만
# 한다 — 값의 진실은 검사하지 않는다(모듈 docstring/decision doc 에 명시).
_EMPTY_STATE = re.compile(
    r"^\s*[-*]?\s*empty state\s*:\s*\S", re.IGNORECASE | re.MULTILINE)
_PROVENANCE = re.compile(
    r"^\s*[-*]?\s*provenance\s*:\s*(executed-live|executed-unit|read)\b",
    re.IGNORECASE | re.MULTILINE)


def _acceptance_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    `## Acceptance`(또는 임의 레벨 헤딩의 "acceptance") 절이 아예 없으면
    검사 불가 — fail closed, 통과가 아니라 위반으로 취급한다. 절이
    있으면 실행가능한 산출물 참조(백틱으로 감싼 `test/`/`gates/` 아래
    경로, 또는 `gate:`/`check:` 줄) 또는 `unverifiable:` 로 시작하는
    명시적 이유 줄 중 하나를 요구한다. `.github/workflows/` 는 #460 으로
    저장소에서 완전히 삭제되어 더 이상 실행가능한 산출물이 될 수 없으므로
    받아들이지 않는다(issue-499).
    """
    body = body or ""
    section = _acceptance_section(body)
    if section is None:
        return [f"이슈 #{issue} 본문에 '## Acceptance' 절이 없다 — "
                f"수용기준 없이는 실행가능성을 검사할 수 없고, 검사 불가는 "
                f"통과가 아니다."]
    if _UNVERIFIABLE.search(section):
        return []
    if not _ARTIFACT_REF.search(section):
        return [f"이슈 #{issue}의 'Acceptance' 절이 프로즈뿐이다 — 실행가능한 "
                f"산출물(백틱으로 감싼 test/, gates/ 경로, 또는 'gate:'/'check:' "
                f"줄)을 가리키거나, 검증 불가능한 이유를 "
                f"'unverifiable: <이유>' 로 명시해야 한다."]
    # issue-416: 실행가능 산출물 참조가 있으면(=행동 주장) empty state/provenance
    # 존재를 추가로 요구한다. unverifiable: 은 위에서 이미 둘 다 면제했다.
    bad = []
    if not _EMPTY_STATE.search(section):
        bad.append(
            f"이슈 #{issue}의 'Acceptance' 절이 실행가능 산출물을 참조하지만 "
            f"'empty state: <경로 또는 설명>' 줄이 없다 — 초기/빈 상태가 "
            f"코퍼스에 있는지 명시해야 한다(또는 "
            f"'empty state: not applicable — <이유>')."
        )
    if not _PROVENANCE.search(section):
        bad.append(
            f"이슈 #{issue}의 'Acceptance' 절이 실행가능 산출물을 참조하지만 "
            f"'provenance: executed-live|executed-unit|read' 줄이 없다 — "
            f"행동 주장이 실제 실행으로 확인됐는지, 읽기로만 판단했는지 "
            f"명시해야 한다(읽기(`read`)로 판단했다면 그 사실도 명시적이어야 "
            f"한다 — 이 게이트는 `read` 를 금지하지 않고 보이게만 만든다)."
        )
    return bad


def _issue_view_body(repo: Path, issue: int) -> str | None:
    r = subprocess.run(["gh", "issue", "view", str(issue), "--json", "body"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    data = json.loads(r.stdout)
    return data.get("body", "")


def check(repo: Path, issue: int) -> list[str]:
    body = _issue_view_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh issue view` 실패) — "
                f"검사 불가는 통과가 아니다."]
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: acceptance_gate.py <issue-number> [--repo <경로>]")
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
