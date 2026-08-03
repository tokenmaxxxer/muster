#!/usr/bin/env python3
"""기계 게이트의 CI 진입점. LLM 0회, 결정론적.

라우터 진입점(`gates.check`)과 나뉘는 이유는 **spec 의 유무**다. 라우터는 plan
스테이지가 만든 `spec.md` 를 갖고 있어 write-set 대조가 성립하지만, 사람이 연 PR 에는
spec 이 없다. spec 없음을 라우터 규칙에 그대로 넣으면 fail closed 가 발동해 **모든
사람 PR 이 차단된다** — 게이트가 죽는 가장 흔한 방식이 이것이다(막아야 할 것을 놓치는
게 아니라, 막지 말아야 할 것을 막아 사람이 게이트를 꺼버리게 만드는 것).

그래서 여기서는 spec 없이 성립하는 검사만 돌린다. write-set 대조는 plan 스테이지가
생기면 추가한다 — 그때까지 있지도 않은 spec 을 상대하는 코드를 두지 않는다.

PR 이슈참조 검사(issue-126)는 별도 옵션이다: PR 번호와 이슈 번호는 로컬
checkout에 없고 `gh pr view`로만 얻어지므로, `check(repo)`의 로컬-전용
시그니처에 넣지 않고 `--pr`/`--issue`가 주어졌을 때만 켠다(주어지지 않으면
이 검사는 그냥 스킵된다 — PR 컨텍스트 없이 도는 다른 호출부를 막지 않기
위해서다).

  python3 gates/ci.py [<repo 경로>] [--pr <n> --issue <n> [--phase phase1|phase2]]
  종료 코드 0 통과 / 1 차단
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates
import pr_reference


def _pr_head_ref(repo: Path, pr: int) -> str | None:
    """PR 의 head 브랜치 이름. CI 체크아웃은 보통 detached HEAD 라 로컬
    `git branch --show-current` 로는 못 얻는다 — `gh pr view` 로만 나온다."""
    import json
    import subprocess
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "headRefName"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout).get("headRefName")


def check(repo: Path, pr: int | None = None, issue: int | None = None,
          phase: str = "phase1") -> list[str]:
    """차단 사유 목록. 비어 있으면 통과."""
    bad = [f"보호 경로 변경: {f}" for f in gates.changed_files(repo)
           if gates.is_protected(f)]
    if pr is not None and issue is not None:
        bad += pr_reference.check(repo, pr, issue, phase)
    if pr is not None:
        branch = _pr_head_ref(repo, pr)
        if branch is None:
            bad.append(f"PR #{pr} 의 head 브랜치를 읽을 수 없다 (fail closed)")
        else:
            bad += gates.role_scope(repo, branch)
    bad += gates.record_enums(repo, {})
    bad += gates.record_wellformed_in(repo)
    bad += gates.record_no_tool_residue_in(repo)
    bad += gates.record_fulfils_diff(repo, {})

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
    argv = sys.argv[1:]
    opts = {}
    positional = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--pr", "--issue", "--phase"):
            opts[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            positional.append(argv[i])
            i += 1
    repo = Path(positional[0] if positional else ".").resolve()
    pr = int(opts["pr"]) if "pr" in opts else None
    issue = int(opts["issue"]) if "issue" in opts else None
    phase = opts.get("phase", "phase1")
    try:
        bad = check(repo, pr, issue, phase)
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
