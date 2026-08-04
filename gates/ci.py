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
  python3 gates/ci.py [<repo 경로>] --pr <n> --autodetect --closes-only
  종료 코드 0 통과 / 1 차단

`--autodetect`(issue #245): `--issue`/`--phase`를 CI 트리거가 못 줄 때, head
브랜치명(`issue-<n>/<role>`)에서 이슈 번호를, 본문의 closing 키워드 유무에서
phase를 끌어낸다. 추출 실패는 fail closed(차단) — 근거와 트레이드오프는
`docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`.
`--closes-only`(issue #245): 계획-인지 Closes 게이트(+phase1 mismatch)만
돌리고 write_scope/protected-path/deps/record 검사는 건너뛴다 — `.github/`
필수 상태체크가 쓰는 모드. 이유는 `check()`의 독스트링과
`docs/issue-245/reports/implementation.md`의 "Rationale for deviations".
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates
import pr_reference

# `issue-<n>/<role>` 브랜치 명명 규칙(role-handoff contract v3, gates.BRANCH_ROLE
# 과 같은 관례)에서 이슈 번호만 뽑는다 — CI 트리거 시점엔 사람이 --issue 를
# 못 주므로(issue #245 survey §10 미해결 질문), 이미 강제되는 이 명명 규칙을
# 재사용한다.
_ISSUE_BRANCH = re.compile(r"^issue-(\d+)/")


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


def _issue_from_branch(branch: str) -> int | None:
    """순수 함수(네트워크 없음) — `_autodetect_issue_phase`/테스트가 공유."""
    m = _ISSUE_BRANCH.match(branch)
    return int(m.group(1)) if m else None


def _closes_ref_for_issue(body: str, issue: int):
    """본문에 *이 이슈를* 향한 closing 키워드 매치가 있으면 그 매치를,
    없으면 None을 돌려준다 — 순수 함수(네트워크 없음).

    `.search()`(첫 매치 하나)가 아니라 `.finditer()`(전체 매치)를 쓴다:
    본문이 다른 이슈를 먼저 언급하면("Fixes #999, ... Closes #245")
    `.search()`는 #999 매치에서 멈춰 진짜 #245 참조를 놓친다 — hunt로
    실측 확인된 회피 경로(assume-incomplete-coverage 스탠스, issue #245
    구현 기록의 Hunt 절 참조): 무해해 보이는 앞쪽 참조 하나만 끼워 넣으면
    phase-1 PR에 실제 `Closes #245`가 있어도 게이트가 못 봤다."""
    for m in pr_reference._CLOSES_REF.finditer(body):
        if int(m.group(2)) == issue:
            return m
    return None


def _phase_from_body(body: str, issue: int) -> str:
    """PR 본문에 이 이슈를 향한 closing 키워드가 있으면 phase2, 없으면
    phase1 — 순수 함수(네트워크 없음). `pr_reference.check_body` 가 이미
    같은 `_CLOSES_REF` 로 판정 분기하는 것과 동일한 신호를 CI 트리거
    시점의 phase 추정에도 재사용한다."""
    return "phase2" if _closes_ref_for_issue(body, issue) else "phase1"


def _phase1_mismatch(body: str, issue: int) -> list[str]:
    """phase1 문서 규칙("Closes/Fixes/Resolves 금지")의 기계 검사 — 순수 함수.

    `pr_reference.check_body`의 phase1 분기(28-62행)는 평문 `#N` 참조만
    보고 closing 키워드 부재는 안 본다: 에러 메시지는 금지를 주장하지만
    실제 판정은 안 한다(issue #245 survey §1, 문서-검사 불일치). `check_body`
    자체는 #228 소유라 무변경 — 이 오케스트레이션 계층에서 같은
    `_CLOSES_REF`(이미 `closure_sweep.py`가 재사용 중인 정규식)로 보완한다."""
    m = _closes_ref_for_issue(body, issue)
    if m:
        return [f"phase-1 제안 PR 본문에 closing 키워드({m.group(1)})가 있다 — "
                f"phase-1 머지가 이슈 #{issue}를 자동으로 닫으면 안 된다."]
    return []


def _autodetect_issue_phase(repo: Path, pr: int, issue: int | None,
                             phase: str | None) -> tuple[int, str] | list[str]:
    """CI 트리거가 못 주는 --issue/--phase 를 PR 메타데이터에서 끌어낸다.

    이슈 번호는 PR 본문이 아니라 head 브랜치명에서 뽑는다: 본문은 이슈를
    여럿 언급할 수 있어 모호하지만, 브랜치명은 이 저장소 전체가 강제하는
    유일한 `issue-<n>/<role>` 규칙이라 모호성이 없다. 브랜치가 그 형태가
    아니면(이슈에 안 연결된 사람 PR 등) 이슈 번호를 알 방법이 없다 —
    통과가 아니라 차단한다(fail closed): 조용히 건너뛰면 #245 가 고치려는
    "강제 지점 없음" 구멍이 이 경로로 그대로 되살아난다. 트레이드오프는
    `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`."""
    if issue is None:
        branch = _pr_head_ref(repo, pr)
        if branch is None:
            return [f"PR #{pr} 의 head 브랜치를 읽을 수 없다 (fail closed)"]
        detected = _issue_from_branch(branch)
        if detected is None:
            return [f"브랜치 {branch!r} 에서 이슈 번호를 추출할 수 없다 "
                    f"(issue-<n>/<role> 형태가 아니다) — fail closed: 이슈에 "
                    f"연결 안 된 PR을 이 검사 없이 통과시키지 않는다. 브랜치를 "
                    f"issue-<n>/<role> 로 바꾸면 재검사된다."]
        issue = detected
    if phase is None:
        body = pr_reference._pr_view(repo, pr)
        if body is None:
            return [f"PR #{pr} 본문을 읽을 수 없다(`gh pr view` 실패) — 검사 불가는 통과가 아니다."]
        phase = _phase_from_body(body, issue)
    return issue, phase


def check(repo: Path, pr: int | None = None, issue: int | None = None,
          phase: str | None = None, closes_only: bool = False) -> list[str]:
    """차단 사유 목록. 비어 있으면 통과.

    `closes_only=True`: 계획-인지 Closes 게이트(+phase1 mismatch 보완)만
    돈다 — write_scope/protected-path/deps/record 검사는 전부 건너뛴다.
    issue #245 필수 상태체크가 쓰는 모드: `gates.role_scope()`가 참조하는
    `_always_writable()`의 제안-파일 패턴(`docs/issue-*/proposals/<role>.md`)이
    이 저장소가 실제로 쓰는 날짜-슬러그 제안 파일명과 안 맞아, 번들 전체를
    필수 체크로 걸면 그 불일치 하나로 미래의 모든 PR(이 PR 포함)이
    막힌다 — 실측 확인됨(`docs/issue-245/reports/implementation.md`
    "Rationale for deviations"). 그 불일치는 `gates/gates.py`의 기존 결함이라
    이 이슈의 승인된 쓰기범위 밖: 고치는 대신, 이 이슈가 실제로 요구한
    범위(계획-인지 Closes 게이트)만 필수 체크로 좁힌다."""
    bad = []
    if not closes_only:
        bad = [f"보호 경로 변경: {f}" for f in gates.changed_files(repo)
               if gates.is_protected(f)]
    if pr is not None and issue is not None:
        if phase is None:
            bad.append("--phase가 필요하다(phase1|phase2) — 생략하면 phase-2 "
                       "검사가 조용히 건너뛰어진다")
        else:
            bad += pr_reference.check(repo, pr, issue, phase)
            if phase == "phase1":
                body = pr_reference._pr_view(repo, pr)
                if body is None:
                    bad.append(f"PR #{pr} 본문을 읽을 수 없다(`gh pr view` 실패) — 검사 불가는 통과가 아니다.")
                else:
                    bad += _phase1_mismatch(body, issue)
    if closes_only:
        return bad
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


_BOOL_FLAGS = ("--closes-only", "--autodetect")


def main() -> int:
    argv = sys.argv[1:]
    opts = {}
    positional = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--pr", "--issue", "--phase"):
            opts[argv[i][2:]] = argv[i + 1]
            i += 2
        elif argv[i] in _BOOL_FLAGS:
            opts[argv[i][2:]] = True
            i += 1
        else:
            positional.append(argv[i])
            i += 1
    repo = Path(positional[0] if positional else ".").resolve()
    pr = int(opts["pr"]) if "pr" in opts else None
    issue = int(opts["issue"]) if "issue" in opts else None
    phase = opts.get("phase")
    closes_only = bool(opts.get("closes-only"))
    if opts.get("autodetect"):
        if pr is None:
            print("게이트 차단:\n  - --autodetect 는 --pr 이 있어야 한다")
            return 1
        detected = _autodetect_issue_phase(repo, pr, issue, phase)
        if isinstance(detected, list):
            print("게이트 차단:")
            for b in detected:
                print(f"  - {b}")
            return 1
        issue, phase = detected
    try:
        bad = check(repo, pr, issue, phase, closes_only=closes_only)
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
