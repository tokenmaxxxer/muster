#!/usr/bin/env python3
"""issue #424 — 축적 비용(accumulation cost) 게이트.

#467 ADR 이 이 행에 준 문구("N번 더 같은 모양이 반복되면 코드베이스가
어떻게 되는지 proposal 이 말해야 한다")는 구체 모듈을 지정하지 않은
최소-명세 행이다. #419 proposal 이 이미 확립한 근거(단일 일반
구조-유사도 탐지기는 이 저장소에서 오탐 홍수를 낸다, "structurally
similar" 는 결정 불가능 문제다)를 재사용해, 일반 축적 탐지기가 아니라
survey(`docs/issue-424/reports/architecture/survey.md`)가 실제 반복
증거(N>1)를 댄 두 모양만 검사한다:

- **모양 1** — 공유 헬퍼 없이 같은 파일에 인라인 `subprocess`/`gh` 호출
  지점이 계속 늘어난다(`gates/ci.py`가 실물 사례: 6곳, #424 survey
  instance 1).
- **모양 5** — `roles/*.json` 같은, 구조가 똑같은 파일들에 똑같은
  한 줄짜리 수정이 반복된다(#424 survey instance 5: 43개 파일).

이 두 모양 중 하나를 건드리는 변경은 레코드가 아니라 **proposal 본문**에
`## Accumulation` 줄이 있어야 한다 — proposal 이 "N번 더 이런 변경이
오면 이 파일/목록이 어떻게 되는지"를 스스로 말하게 강제한다. 이 게이트도
그 필드의 *존재*만 본다(#416 이 이미 확립한 존재-검사 관례) — 서술
내용이 실제로 맞는 예측인지는 검사하지 않는다.

survey가 이름한 나머지 인스턴스(2, 3, 4)는 이 저장소 역사에 N>1 반복
증거가 없어 이 모듈이 검사하지 않는다 — 명시적으로 다루지 않는 것으로
남긴다(proposal Out of scope).
"""
from __future__ import annotations
import ast
import re
import subprocess
from pathlib import Path

_ACCUMULATION_HEADING = re.compile(r"^##\s*Accumulation\b", re.M | re.I)

# 모양 1: 이미 이만큼 인라인 subprocess/gh 호출이 있으면 "공유 헬퍼 없는
# 반복"으로 본다 — gates/ci.py의 실물 6곳 중 최소 3곳 이상이면(#419가 쓴
# 것과 같은 판단 문턱은 아니고, "이미 여러 곳 있는데 하나 더" 라는 존재
# 신호만 본다).
_SHAPE_1_THRESHOLD = 3


def _is_subprocess_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    fn = node.func
    return (
        (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
         and fn.value.id == "subprocess"
         and fn.attr in ("run", "check_output", "check_call", "Popen"))
        or (isinstance(fn, ast.Name) and fn.id in ("run", "check_output",
                                                     "check_call", "Popen")))


def _inline_subprocess_call_count(text: str) -> int:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    return sum(1 for node in ast.walk(tree) if _is_subprocess_call(node))


def _touches_shape_1(work: Path, changed: list[str]) -> bool:
    """바뀐 파일 중, subprocess 호출 지점이 이미 `_SHAPE_1_THRESHOLD`
    이상인 파일이 있으면 모양 1(공유 헬퍼 없는 인라인 호출 누적)을
    건드린다고 본다."""
    for rel in changed:
        if not rel.endswith(".py"):
            continue
        f = work / rel
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _inline_subprocess_call_count(text) >= _SHAPE_1_THRESHOLD:
            return True
    return False


def _touches_shape_5(changed: list[str]) -> bool:
    """`roles/*.json` 처럼 구조가 같은 파일들에 반복되는 한 줄 수정 모양을
    건드리는지 — 바뀐 파일이 `roles/*.json` 에 하나라도 있으면 그 클래스에
    속한다고 본다(survey instance 5 의 실물 파일군)."""
    return any(re.match(r"^roles/[^/]+\.json$", rel) for rel in changed)


def check_accumulation_claim(work: Path, body: str) -> list[str]:
    """proposal 본문(`body`)이, 작업트리(`work`)의 바뀐 파일이 모양 1/5 중
    하나를 건드릴 때 `## Accumulation` 줄을 갖고 있는지 검사한다.

    `work` 는 프로포절이 아니라 코드 트리를 봐야 모양 1/5 를 판정할 수
    있어 proposal 이 지정한 `check_accumulation_claim(body: str)` 시그니처를
    `(work, body)` 로 넓혔다 — 근거는
    `docs/issue-474/reports/implementation.md`의 "Rationale for
    deviations"."""
    p = subprocess.run(["git", "-C", str(work), "diff", "--name-only", "HEAD"],
                       capture_output=True, text=True)
    committed = subprocess.run(
        ["git", "-C", str(work), "diff", "--name-only", "--cached"],
        capture_output=True, text=True)
    if p.returncode != 0 and committed.returncode != 0:
        # `work` 가 git 저장소가 아니거나 git 호출 자체가 실패하면 "변경
        # 없음"이 아니라 "검사 불가"다 — 조용히 []를 내면 진짜 위반을
        # 검사 불가 뒤에 숨긴다(before-landing warrant hunt, stance:
        # malformed-input-goes-silent, 재현됨). fail closed.
        return [
            f"{work} 에서 git diff 를 확인할 수 없다(fail closed) — "
            f"축적-비용 모양 검사를 건너뛸 수 없다: {p.stderr.strip()[:200] or committed.stderr.strip()[:200]}"
        ]
    changed = sorted(set(
        (p.stdout.splitlines() if p.returncode == 0 else [])
        + (committed.stdout.splitlines() if committed.returncode == 0 else [])))
    if not changed:
        # 워킹트리 diff 가 비었으면(예: 커밋된 상태의 파일트리를 그대로
        # 검사) 전체 트리 파일을 "바뀐 것"으로 보되, subprocess 호출은
        # 파일 하나만 있어야 신호가 명확하다 — 그래서 여기서는 전체
        # 트리에서 모양 1/5 후보를 훑는다.
        p_all = subprocess.run(["git", "-C", str(work), "ls-files"],
                               capture_output=True, text=True)
        if p_all.returncode != 0:
            return [f"{work} 에서 git ls-files 를 확인할 수 없다(fail closed) — "
                    f"축적-비용 모양 검사를 건너뛸 수 없다: {p_all.stderr.strip()[:200]}"]
        changed = p_all.stdout.splitlines()
    if not (_touches_shape_1(work, changed) or _touches_shape_5(changed)):
        return []
    if _ACCUMULATION_HEADING.search(body or ""):
        return []
    return [
        "변경이 축적-비용 모양(공유 헬퍼 없는 인라인 subprocess/gh 호출 "
        "누적, 또는 roles/*.json 류 반복 파일에 대한 동일 한 줄 수정)을 "
        "건드리지만, proposal 본문에 '## Accumulation' 줄이 없다 — "
        "이런 변경이 N번 더 오면 이 파일/목록이 어떻게 되는지 명시해야 "
        "한다."
    ]
