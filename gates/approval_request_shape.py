#!/usr/bin/env python3
"""issue-472 (issue-467 ADR Batch B, #318 / #363) — 승인 요청 형식(shape)
검사.

`missing_approval_clauses`: `on-the-record/hooks/stop-gate.sh` 의 인라인
heredoc에 있던 절(clause) 감지 정규식을 `gates/` 안의 순수 함수로 이식한
것 — #472 의 write set 은 `gates/*.py` 로 한정되고 `stop-gate.sh` (라이브
Stop 훅)는 포함되지 않으므로, 훅을 재배선하는 대신 동등한 로직을 독립적으로
테스트 가능한 함수로 옮겼다. 두 구현을 동기화해 유지하는 것은 후속 과제로
남겨둔다(#472 phase-2 record 참고).

`has_generator_section`: #363 — "## Generator" 절 헤딩의 존재만 확인한다.
이 함수는 절 아래 내용을 전혀 검사하지 않는다 — 존재 여부만 확인하는
표면적(surface) 체크이고, 그렇게 명시적으로 문서화되어 있다. 자유
텍스트에 대한 키워드/패턴 매칭은 존재 체크와 똑같이 게임 가능하다는
것이 #363 자체의 acceptance 문구가 지적하는 함정이므로 시도하지
않는다.
"""
from __future__ import annotations
import re

ISSUE_RE = re.compile(r"#\d+")
CHANGE_RE = re.compile(
    r"(변경|바뀌|수정|change|changes?:|will (do|change|add|remove|update))",
    re.IGNORECASE,
)
RISK_RE = re.compile(
    r"(위험|리스크|우려|risk|trade-?off|tradeoff|downside|caveat)",
    re.IGNORECASE,
)

_GENERATOR_HEADING_RE = re.compile(
    r"^##\s*(Generator|생성자)\s*$", re.IGNORECASE | re.MULTILINE
)


def missing_approval_clauses(text: str) -> list[str]:
    """승인 요청 형식 텍스트에서 빠진 절을 나열한다 — #318.

    `stop-gate.sh` 와 동일한 세 절(이슈 참조, 변경 서술, 위험/트레이드오프)
    을 검사하고, 없는 절의 라벨을 `stop-gate.sh` 와 같은 문구로 반환한다.
    빈 리스트는 세 절이 모두 있다는 뜻이다. 이 함수는 텍스트가 애초에
    승인 요청 형태인지(trigger phrase) 판단하지 않는다 — 호출자가 그
    판단을 한 뒤에만 호출한다는 전제다(`stop-gate.sh` 가 하는 역할).
    """
    missing = []
    if not ISSUE_RE.search(text):
        missing.append("issue reference (#<n>)")
    if not CHANGE_RE.search(text):
        missing.append("change statement (what changes)")
    if not RISK_RE.search(text):
        missing.append("risk/tradeoff statement")
    return missing


def has_generator_section(proposal_text: str) -> bool:
    """제안서 텍스트에 `## Generator`(또는 `## 생성자`) 헤딩이 있는지만
    본다 — 내용은 검사하지 않는다(#363). "이 변경이 생성기 자체를
    제거하는지, 인스턴스 하나만 고치는지"에 대한 실제 답은 이 함수의
    검사 범위 밖이다."""
    return bool(_GENERATOR_HEADING_RE.search(proposal_text))
