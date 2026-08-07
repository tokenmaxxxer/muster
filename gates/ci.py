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
sys.path.insert(0, str(Path(__file__).parent.parent))
import flows
import gates
import pr_reference
import spawn

# `issue-<n>/<role>` 브랜치 명명 규칙(role-handoff contract v3, gates.BRANCH_ROLE
# 과 같은 관례)에서 이슈 번호와 role 세그먼트를 함께 뽑는다 — CI 트리거
# 시점엔 사람이 --issue 를 못 주므로(issue #245 survey §10 미해결 질문),
# 이미 강제되는 이 명명 규칙을 재사용한다. role 은 issue #271 요구사항 2의
# 승인-이벤트 phase 신호(`APPROVE issue-<n>/<role>`)에 필요해 이 이슈에서
# 추가한다.
_ISSUE_ROLE_BRANCH = re.compile(r"^issue-(\d+)/([^/]+)$")


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


def _issue_and_role_from_branch(branch: str) -> tuple[int, str] | None:
    """순수 함수(네트워크 없음) — `_autodetect_issue_phase`/테스트가 공유."""
    m = _ISSUE_ROLE_BRANCH.match(branch)
    return (int(m.group(1)), m.group(2)) if m else None


def _pr_title(repo: Path, pr: int) -> str | None:
    """PR 제목 — issue #271 요구사항 1 row B(GitHub 이 closing 키워드를
    공식 문서화한 표면이지만, `pr_reference._pr_view`는 지금까지 fetch 만
    하고 버렸다). `pr_reference.py`의 body-only 시그니처는 #228 소유라
    무변경 — 이 오케스트레이션 계층에서 별도로 읽는다."""
    import json
    import subprocess
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "title"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout).get("title")


def _pr_commit_messages(repo: Path, pr: int) -> list[str] | None:
    """PR 브랜치 각 커밋의 전체 메시지 — issue #271 요구사항 1 row C(실물
    2건 사고의 벡터). `gh api repos/<slug>/pulls/<n>/commits`, 이슈가 직접
    제안한 메커니즘.

    이 엔드포인트는 페이지당 30개로 잘린다(GitHub 기본값) — `--paginate`
    만 쓰면 페이지마다 별도 JSON 배열이 순차 출력돼 다중 페이지 응답이
    유효한 단일 JSON이 아니게 되므로(`json.loads`가 `ValueError`로 죽어
    아래 except 가 통째로 삼킨다), `spawn._issue_comments`(spawn.py:836,
    같은 문제를 이미 고친 전례)와 같이 `--slurp`(페이지들을 바깥 배열
    하나로 감싼다)를 같이 쓰고 평탄화한다 — warrant-hunter(silent-failure
    stance, 2026-08-04)가 실측: 30개 넘는 커밋의 PR에서 뒤쪽 커밋의
    closing 키워드가 이 함수 하나만 예외적으로 안 걸리고 있었다."""
    import json
    import subprocess
    slug = spawn._repo_slug(repo)
    if not slug:
        return None
    r = subprocess.run(["gh", "api", f"repos/{slug}/pulls/{pr}/commits",
                        "--paginate", "--slurp"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    data = [c for page in data for c in page]
    return [c.get("commit", {}).get("message", "") for c in data]


def _pr_reviews(repo: Path, pr: int) -> list[dict] | None:
    """PR 리뷰 목록(state, author.login) — two-account 승인 신호
    (`flows._pr_approved`)에 필요하다."""
    import json
    import subprocess
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "reviews"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout).get("reviews")


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


def _phase_from_approval(repo: Path, pr: int, issue: int, role: str) -> str:
    """phase2 를 closing 키워드가 아니라 승인 이벤트로 판정한다 — 없으면
    phase1(issue #271 요구사항 2, #245 관찰 F1 술어 결합 해소). contract
    v3 s19 의 두 경로 그대로: 정확한 `APPROVE issue-<n>/<role>` 이슈
    코멘트(single-account, 승인자 allowlist) 또는 differing-account PR
    리뷰 Approve(two-account) — closing 키워드 유무는 이 판정에 전혀
    관여하지 않는다. `flows._pr_approved`(issue #172, 상황판이 이미 같은
    두 경로를 검증하는 코드, `flows.py:130`)를 그대로 재사용한다 —
    새로 손으로 짜지 않는다. `spawn._approvers`/`spawn._issue_comments`
    를 `gates/` 에서 쓰는 것은 `closure_sweep.py:21`의 기존 전례를
    따른다. issue 번호로만 조회한다 — PR 번호로 `spawn._issue_comments`
    를 다시 부르면 GitHub 가 `/issues/<n>/comments` 한 엔드포인트로
    이슈·PR 대화 코멘트를 함께 서빙하는 성질 때문에 PR 자신의 대화
    스레드에 달린 APPROVE 형태 코멘트까지 승인으로 계산돼 버린다 —
    contract v3 s19 의 single-account 경로가 인정하는 건 이슈-레벨
    코멘트뿐이다(issue #275 F3, #271 관찰이 남긴 fail-open 결함)."""
    subject = f"issue-{issue}"
    approvers = spawn._approvers(repo)
    comments = spawn._issue_comments(repo, issue)
    reviews = _pr_reviews(repo, pr)
    pr_dict = {"reviews": reviews or []}
    approved = flows._pr_approved(pr_dict, comments, approvers, subject, role)
    return "phase2" if approved else "phase1"


def _phase2_record_evidence(repo: Path, branch: str, issue: int) -> bool:
    """phase-2 기록 파일의 존재 + 비어있지 않은 `loop_state` 를 closing 의도의
    대안 증거로 인정한다(issue #284 승인된 제안) — 승인 이후 phase 가 뒤바뀐
    PR을 본문을 다시 쓰지 않고도 통과시킨다. `loop_state` 의 *값*은 보지
    않는다: `record-shape-directive` 가 이미 모든 phase-2 기록에 이 필드를
    강제하므로 존재 자체가 새 의무가 아니고, `roles/implementation.json` 의
    선언 enum과 실제 기록 값(`phase-2-complete`)이 어긋나 있어(값 검사는
    #337 류 기록을 오탐 차단한다 — 자세한 근거는
    `docs/issue-284/decisions/record-evidence-as-closing-intent.md`) 존재
    검사만이 오늘 실제로 참인 것이다."""
    detected = _issue_and_role_from_branch(branch)
    if detected is None:
        return False
    _, role = detected
    record_path = repo / f"docs/issue-{issue}/reports/{role}.md"
    if not record_path.exists():
        return False
    text = record_path.read_text(encoding="utf-8-sig", errors="replace")
    fm = gates.record_frontmatter(text)
    return bool(fm.get("loop_state", "").strip())


def _pr_is_cross_repo(repo: Path, pr: int) -> bool | None:
    """PR이 실제로 fork(다른 저장소) 발원인지 — 브랜치명이 관례를 안 따르는
    "형태가 잘못된 내부 PR"과 구분하기 위해 필요하다. 이 구분이 없으면
    내부 PR이 본문에 이슈 참조를 적어 넣는 것만으로 브랜치 명명 강제를
    우회해 role-blind PR-review-Approve 경로로 phase2 에 도달할 수 있다
    (after-proposal warrant hunt, stance 0 실측)."""
    import json
    import subprocess
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "isCrossRepository"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout).get("isCrossRepository")
    except ValueError:
        return None


def _fork_issue_from_body(repo: Path, pr: int) -> int | None:
    """확인된 cross-repo(포크) PR에 한해, 본문의 평문 `#N` 참조로 이슈
    번호를 뽑는다(issue #284 fork 폴백) — phase1이 모든 PR 본문에 이미
    요구하는 것과 같은 패턴(`pr_reference._PLAIN_REF`)을 재사용한다.
    cross-repo 가 아니면(또는 판정 불가면) 아예 시도하지 않는다 — 그
    호출부(`_autodetect_issue_phase`)가 이어서 fail closed 한다."""
    if not _pr_is_cross_repo(repo, pr):
        return None
    body = pr_reference._pr_view(repo, pr)
    if not body:
        return None
    refs = pr_reference._PLAIN_REF.findall(body)
    return int(refs[0]) if refs else None


def _phase1_mismatch(body: str, issue: int) -> list[str]:
    """phase1 문서 규칙("Closes/Fixes/Resolves 금지")의 기계 검사 — 순수 함수,
    본문 한 표면만 본다. `_phase1_surface_mismatch`의 단일-표면 특수형 —
    기존 단위테스트가 이 시그니처를 직접 부르므로 그대로 유지한다."""
    return _phase1_surface_mismatch(issue, [("본문", body)])


def _phase1_surface_mismatch(issue: int, surfaces: list[tuple[str, str]]) -> list[str]:
    """`_phase1_mismatch`를 본문(row A) 외에 제목(row B)·커밋 메시지(row C)
    까지 넓힌 버전 — issue #271 요구사항 1. `surfaces`는 (표면 라벨, 텍스트)
    쌍의 목록이고, 앞쪽 표면부터 순서대로 검사해 처음 걸리는 곳에서 멈춘다
    (표면마다 중복 사유를 쌓지 않는다).

    `pr_reference.check_body`의 phase1 분기(28-62행)는 평문 `#N` 참조만
    보고 closing 키워드 부재는 안 본다: 에러 메시지는 금지를 주장하지만
    실제 판정은 안 한다(issue #245 survey §1, 문서-검사 불일치). `check_body`
    자체는 #228 소유라 무변경 — 이 오케스트레이션 계층에서 같은
    `_CLOSES_REF`(이미 `closure_sweep.py`가 재사용 중인 정규식)로 보완한다."""
    for label, text in surfaces:
        m = _closes_ref_for_issue(text or "", issue)
        if m:
            return [f"phase-1 제안 PR {label}에 closing 키워드({m.group(1)})가 "
                    f"있다 — phase-1 머지가 이슈 #{issue}를 자동으로 닫으면 안 된다."]
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
    `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`.

    phase 는 이제 PR 본문의 closing 키워드가 아니라 승인 이벤트에서
    끌어낸다(issue #271 요구사항 2) — role 세그먼트가 그 판정에 필요해
    브랜치에서 이슈 번호와 함께 뽑는다."""
    role = None
    if issue is None or phase is None:
        branch = _pr_head_ref(repo, pr)
        if branch is None:
            return [f"PR #{pr} 의 head 브랜치를 읽을 수 없다 (fail closed)"]
        detected = _issue_and_role_from_branch(branch)
        if detected is None:
            fork_issue = _fork_issue_from_body(repo, pr)
            if fork_issue is None:
                return [f"브랜치 {branch!r} 에서 이슈 번호를 추출할 수 없다 "
                        f"(issue-<n>/<role> 형태가 아니다) — fail closed: 이슈에 "
                        f"연결 안 된 PR을 이 검사 없이 통과시키지 않는다. 내부 "
                        f"PR이면 브랜치를 issue-<n>/<role> 로 바꾸면 재검사된다; "
                        f"확인된 fork PR이면 본문에 '#<이슈번호>'를 적으면 "
                        f"재검사된다(role 은 None 으로 남는다)."]
            if issue is None:
                issue = fork_issue
        else:
            detected_issue, role = detected
            if issue is None:
                issue = detected_issue
    if phase is None:
        phase = _phase_from_approval(repo, pr, issue, role)
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
            ref_bad = pr_reference.check(repo, pr, issue, phase)
            if phase == "phase2":
                closes_msg = (f"PR 본문에 'Closes #{issue}'(또는 Fixes/Resolves)가 "
                              f"없다 — phase-2 인도 PR은 이슈를 명시적으로 닫아야 한다.")
                if closes_msg in ref_bad:
                    branch = _pr_head_ref(repo, pr)
                    if branch is not None and _phase2_record_evidence(repo, branch, issue):
                        # 승인 이벤트가 phase 를 뒤집었을 뿐 본문은 phase-1
                        # 시점 그대로인 PR(issue #284) — 기록 파일의 존재가
                        # closing 의도의 대안 증거이므로 본문 편집 없이
                        # 통과시킨다.
                        ref_bad = [b for b in ref_bad if b != closes_msg]
                    else:
                        ref_bad = [closes_msg + " (대안: 이슈에 연결된 phase-2 "
                                   "기록 파일이 loop_state 를 채워 존재하면 "
                                   "통과한다)" if b == closes_msg else b
                                   for b in ref_bad]
            bad += ref_bad
            if phase == "phase1":
                body = pr_reference._pr_view(repo, pr)
                if body is None:
                    bad.append(f"PR #{pr} 본문을 읽을 수 없다(`gh pr view` 실패) — 검사 불가는 통과가 아니다.")
                title = _pr_title(repo, pr)
                if title is None:
                    bad.append(f"PR #{pr} 제목을 읽을 수 없다(`gh pr view` 실패) — 검사 불가는 통과가 아니다.")
                commit_messages = _pr_commit_messages(repo, pr)
                if commit_messages is None:
                    bad.append(f"PR #{pr} 커밋 목록을 읽을 수 없다(`gh api` 실패) — 검사 불가는 통과가 아니다.")
                if body is not None and title is not None and commit_messages is not None:
                    surfaces = ([("본문", body), ("제목", title)]
                                + [("커밋 메시지", m) for m in commit_messages])
                    bad += _phase1_surface_mismatch(issue, surfaces)
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
