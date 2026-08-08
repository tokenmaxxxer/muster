#!/usr/bin/env python3
"""issue #415 — 능력/계약 부재 주장의 저장소 범위 게이트.

`spawn.py` 는 역할마다 저장소 클론을 하나만 준다(쓰기 격리, 의도된 설계).
"능력 X 가 없다"는 주장이 어느 클론을 근거로 하는지 밝히지 않으면, 그
주장은 실제로는 형제 저장소에만 있는 기능을 "부재"로 잘못 결론낼 수 있다
(사고 사례: `thaki-agent-security-controller` 이슈-234).

이 게이트는 주장의 **진실**을 검사하지 않는다 — 형제 저장소를 실제로 읽을
방법이 이 함수에는 없다(그 자체가 이슈의 미결 결정 1번). 검사하는 건
**범위 표시의 존재**뿐이다: 능력/계약 부재 문장에 저장소·시점을 명시하는
인접 문구(`as of <sha>`, `in <repo>`, `checked <repo path>` 등)가 있는지.
파일 경로가 문장 안에 이미 있는(파일-단위) 주장은 검사 대상이 아니다 —
그건 이미 스코프가 있는 주장이다.

알려진 한계(after-proposal warrant hunt, stance: bypass, 재현됨): 아래
`_ABSENCE_PHRASES` 는 고정·폐쇄 목록이다. 이 목록 밖의 동의어/축약형으로
쓰인 부재 주장("isn't implemented", "존재 안 함")은 부재 주장으로
인식되지 않아 스코프 검사 자체에 도달하지 않고 조용히 통과한다 — 스코프가
있어서 통과하는 게 아니라, 이 검사가 그 문장을 부재 주장으로 보지
못해서다. 이건 고쳐야 할 버그가 아니라 이미 진술된 천장의 두 번째, 더
좁은 경계다.
"""
from __future__ import annotations
import re


class Violation:
    def __init__(self, sentence: str, reason: str):
        self.sentence = sentence
        self.reason = reason

    def __repr__(self) -> str:
        return f"Violation({self.sentence!r}, {self.reason!r})"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Violation)
                and self.sentence == other.sentence
                and self.reason == other.reason)


_ABSENCE_PHRASES = [
    r"does not exist", r"is not implemented", r"has not been implemented",
    r"is not present", r"is absent", r"was not found", r"is not available",
    r"존재하지 않는다", r"구현되지 않았다", r"없다",
]
_ABSENCE_RE = re.compile("|".join(_ABSENCE_PHRASES), re.IGNORECASE)

_SCOPE_PHRASES = [
    r"as of\s+[0-9a-f]{6,40}",
    r"\bin\s+`?[\w./-]+`?\s+as of",
    r"\bin\s+the\s+[\w./-]+\s+repo",
    r"checked\s+`?[\w./-]+`?",
    r"as of\s+the\s+.+\s+checkout",
]
_SCOPE_RE = re.compile("|".join(_SCOPE_PHRASES), re.IGNORECASE)

# 파일 경로가 이미 문장 안에 있으면(백틱으로 감싼 경로, 또는 `foo.py:12`
# 형태) 이미 파일-단위로 스코프된 주장 — repo-스코프 검사 대상이 아니다.
_FILE_ANCHOR_RE = re.compile(r"`[^`]*\.[a-zA-Z0-9]+(:\d+)?`")

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def check_repo_scope(text: str) -> list[Violation]:
    """능력/계약 부재 문장에 저장소 범위 표시가 있는지 검사한다.

    문장 단위로 나눠(줄바꿈 또는 마침표 뒤) 부재 어구가 있는 각 문장을
    본다. 파일 경로가 이미 그 문장에 있으면 건너뛴다(이미 파일-스코프,
    이슈 결정 3의 두 번째 예시). 남은 문장 중 스코프 어구가 없는 것만
    Violation 으로 낸다."""
    violations: list[Violation] = []
    for sentence in _SENTENCE_SPLIT.split(text or ""):
        sentence = sentence.strip()
        if not sentence:
            continue
        if not _ABSENCE_RE.search(sentence):
            continue
        if _FILE_ANCHOR_RE.search(sentence):
            continue
        if _SCOPE_RE.search(sentence):
            continue
        violations.append(Violation(
            sentence,
            "capability/contract 부재 주장에 저장소 범위 표시(`as of <sha>`, "
            "`in <repo>`, `checked <repo path>` 등)가 없다 — 이 클론에서만 "
            "확인한 결과일 수 있다."))
    return violations
