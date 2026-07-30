#!/usr/bin/env python3
"""기계 게이트의 CI 진입점. LLM 0회, 결정론적.

라우터 진입점(`gates.check`)과 나뉘는 이유는 **spec 의 유무**다. 라우터는 plan
스테이지가 만든 `spec.md` 를 갖고 있어 write-set 대조가 성립하지만, 사람이 연 PR 에는
spec 이 없다. spec 없음을 라우터 규칙에 그대로 넣으면 fail closed 가 발동해 **모든
사람 PR 이 차단된다** — 게이트가 죽는 가장 흔한 방식이 이것이다(막아야 할 것을 놓치는
게 아니라, 막지 말아야 할 것을 막아 사람이 게이트를 꺼버리게 만드는 것).

그래서 여기서는 spec 없이 성립하는 검사만 돌린다. write-set 대조는 plan 스테이지가
생기면 추가한다 — 그때까지 있지도 않은 spec 을 상대하는 코드를 두지 않는다.

  python3 gates/ci.py [<repo 경로>]     # 기본값: 현재 디렉터리
  종료 코드 0 통과 / 1 차단
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates


def check(repo: Path) -> list[str]:
    """차단 사유 목록. 비어 있으면 통과."""
    bad = [f"보호 경로 변경: {f}" for f in gates.changed_files(repo)
           if gates.is_protected(f)]
    bad += gates.record_enums(repo, {})

    # ponytail: gates.deps() 와 같은 판정을 반복한다. gates.deps 가 라우터의
    # 디렉터리 배치(d/"work")를 전제해서 그대로 못 부른다. 라우터 은퇴 시
    # gates.deps 를 repo 경로 인자로 바꾸고 이 블록을 그쪽으로 합친다.
    new, errs = gates.parse_new_deps(repo)
    bad += errs                       # 파싱 실패는 통과가 아니라 차단 사유다
    for manifest, name in new:
        code = gates.registry_status(gates.REGISTRY[manifest].format(name))
        if code == "404":
            bad.append(f"존재하지 않는 패키지: {name} ({manifest})")
        elif not code.startswith("2"):
            bad.append(f"레지스트리 확인 불가: {name} → {code}")
    return bad


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        bad = check(repo)
    except RuntimeError as e:
        # 검사 자체가 불가능한 경우. 통과가 아니라 차단이다 — 트레이스백 대신
        # 왜 못 봤는지를 읽히게 낸다 (대개 base 브랜치 미확보).
        print(f"게이트 차단:\n  - {e}")
        return 1

    if not bad:
        print("게이트 통과")
        return 0
    print("게이트 차단:")
    for b in bad:
        print(f"  - {b}")
    # 게이트 실패는 재시도가 아니라 정지다. 사람이 보고 판단한다.
    return 1


if __name__ == "__main__":
    sys.exit(main())
