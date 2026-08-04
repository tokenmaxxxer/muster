#!/usr/bin/env python3
"""issue #245/#271 — 계획-인지 Closes 게이트 강제 배선(ci.py 추가분)의 단위 테스트.

네트워크·GitHub 없이 도는 것만(`test_gates.py`와 같은 관례). 별도 파일로
둔 이유: 이 세션(issue-245/implementation)의 승인된 쓰기범위가
`docs/issue-245/`, `.github/`, `gates/` 아래로 한정돼 저장소 루트의
`test_gates.py`는 건드리지 않는다 — `docs/issue-245/reports/implementation.md`
"Rationale for deviations" 참조.

  python3 gates/test_closes_gate_ci.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import ci
import pr_reference
import spawn


def t_issue_and_role_from_branch_matches_convention():
    assert ci._issue_and_role_from_branch("issue-245/implementation") == (245, "implementation")
    assert ci._issue_and_role_from_branch("issue-245/execution-observation") == (245, "execution-observation")
    assert ci._issue_and_role_from_branch("issue-7/technical-writing") == (7, "technical-writing")


def t_issue_and_role_from_branch_rejects_unrecognized_names():
    assert ci._issue_and_role_from_branch("patch-1") is None
    assert ci._issue_and_role_from_branch("dependabot/npm_and_yarn/foo-1.2.3") is None
    assert ci._issue_and_role_from_branch("main") is None
    assert ci._issue_and_role_from_branch("issue-245") is None  # 슬래시 뒤 role 없음


def t_phase1_mismatch_detects_closes_keyword():
    bad = ci._phase1_mismatch("Closes #245", 245)
    assert bad and "closing 키워드" in bad[0], bad


def t_phase1_mismatch_passes_plain_reference():
    assert ci._phase1_mismatch("see #245 for context", 245) == []


def t_phase1_mismatch_ignores_other_issue_closes():
    # PR #257이 "Closes #999"를 담아도 이슈 245 검사엔 안 걸린다 — 이 검사는
    # *이* 이슈를 향한 closing 키워드만 본다(다른 이슈를 향한 것은 그 이슈의
    # 검사가 볼 몫).
    assert ci._phase1_mismatch("Closes #999", 245) == []


def t_phase1_mismatch_catches_closes_after_an_earlier_unrelated_reference():
    # 회귀 가드(hunt finding, assume-incomplete-coverage): 본문이 다른
    # 이슈를 먼저 언급하면 `.search()`(첫 매치 하나만)는 그 앞쪽 매치에서
    # 멈춰 뒤쪽의 진짜 "Closes #245"를 놓친다 — `_closes_ref_for_issue`가
    # `.finditer()`로 전체를 훑어야 하는 이유.
    body = "This also fixes a side issue, Fixes #999, and Closes #245 as the main delivery."
    bad = ci._phase1_mismatch(body, 245)
    assert bad and "closing 키워드" in bad[0], bad


def t_phase1_mismatch_matches_inside_fenced_quote():
    # GitHub 자신이 코드펜스 안 인용도 closing 키워드로 파싱한다(실물 사고:
    # repo-status-board PR #26가 백틱 인용까지 파싱돼 이슈가 또 닫혔다,
    # docs/issue-245/reports/implementation/survey.md 참조).
    body = "설명 중 인용:\n```\nCloses #245\n```\n"
    bad = ci._phase1_mismatch(body, 245)
    assert bad and "closing 키워드" in bad[0], bad


def t_phase1_surface_mismatch_catches_title_closes_keyword():
    # issue #271 요구사항 1, row B: PR 제목도 GitHub 이 공식 문서화한
    # closing 표면이다 — 본문은 clean 이어도 제목에 있으면 잡아야 한다.
    bad = ci._phase1_surface_mismatch(245, [("본문", "see #245"), ("제목", "Closes #245")])
    assert bad and "제목에" in bad[0] and "closing 키워드" in bad[0], bad


def t_phase1_surface_mismatch_catches_commit_message_closes_keyword():
    # issue #271 요구사항 1, row C: 실물 2건 사고의 벡터 — 본문·제목은
    # clean 이어도 브랜치 커밋 메시지에 있으면 잡아야 한다.
    bad = ci._phase1_surface_mismatch(
        245, [("본문", "see #245"), ("제목", "phase 1"),
              ("커밋 메시지", "wip"), ("커밋 메시지", "Closes #245")])
    assert bad and "커밋 메시지에" in bad[0] and "closing 키워드" in bad[0], bad


def t_phase1_surface_mismatch_passes_all_clean_surfaces():
    bad = ci._phase1_surface_mismatch(
        245, [("본문", "see #245"), ("제목", "phase 1"), ("커밋 메시지", "wip")])
    assert bad == [], bad


def t_phase1_surface_mismatch_body_takes_priority_over_later_surfaces():
    # 본문에서 이미 걸리면 그 사유만 보고한다 — 표면마다 중복 사유를
    # 쌓지 않는다(첫 매치에서 멈춘다).
    bad = ci._phase1_surface_mismatch(
        245, [("본문", "Closes #245"), ("제목", "Closes #245")])
    assert len(bad) == 1 and "본문에" in bad[0], bad


def t_autodetect_fail_closed_on_unrecognized_branch():
    original = ci._pr_head_ref
    ci._pr_head_ref = lambda repo, pr: "patch-1"
    try:
        result = ci._autodetect_issue_phase(Path("."), 1, None, None)
    finally:
        ci._pr_head_ref = original
    assert isinstance(result, list), result
    assert any("추출할 수 없다" in b for b in result), result


def t_autodetect_fail_closed_on_unreadable_branch():
    original = ci._pr_head_ref
    ci._pr_head_ref = lambda repo, pr: None
    try:
        result = ci._autodetect_issue_phase(Path("."), 1, None, None)
    finally:
        ci._pr_head_ref = original
    assert isinstance(result, list), result
    assert any("head 브랜치를 읽을 수 없다" in b for b in result), result


def t_autodetect_respects_explicit_issue_and_phase():
    # --issue/--phase 가 명시로 주어졌으면 자동추정은 건드리지 않는다.
    result = ci._autodetect_issue_phase(Path("."), 1, 999, "phase2")
    assert result == (999, "phase2"), result


def t_phase_from_approval_no_signal_is_phase1():
    # 승인 이벤트가 전혀 없으면(코멘트도 리뷰도) phase1 — closing 키워드
    # 유무는 이 판정에 관여하지 않는다(issue #271 요구사항 2, #245 관찰 F1).
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = lambda repo, n: []
    ci._pr_reviews = lambda repo, pr: []
    try:
        assert ci._phase_from_approval(Path("."), 1, 245, "implementation") == "phase1"
    finally:
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews


def t_phase_from_approval_qualifying_issue_comment_is_phase2():
    # single-account mode: 정확한 문자열 "APPROVE issue-<n>/<role>" 코멘트가
    # 승인자 계정에서 이슈에 달리면 phase2.
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = (
        lambda repo, n: [{"login": "jjongkwann", "body": "APPROVE issue-245/implementation"}]
        if n == 245 else [])
    ci._pr_reviews = lambda repo, pr: []
    try:
        assert ci._phase_from_approval(Path("."), 1, 245, "implementation") == "phase2"
    finally:
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews


def t_phase_from_approval_non_approver_comment_is_phase1():
    # 문자열이 정확히 맞아도 승인자 allowlist 밖 계정이면 무효.
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = (
        lambda repo, n: [{"login": "not-an-approver", "body": "APPROVE issue-245/implementation"}]
        if n == 245 else [])
    ci._pr_reviews = lambda repo, pr: []
    try:
        assert ci._phase_from_approval(Path("."), 1, 245, "implementation") == "phase1"
    finally:
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews


def t_phase_from_approval_wrong_role_comment_is_phase1():
    # role 세그먼트가 다르면(다른 역할을 향한 승인) 이 role 의 phase 판정엔
    # 안 걸린다.
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = (
        lambda repo, n: [{"login": "jjongkwann", "body": "APPROVE issue-245/execution-observation"}]
        if n == 245 else [])
    ci._pr_reviews = lambda repo, pr: []
    try:
        assert ci._phase_from_approval(Path("."), 1, 245, "implementation") == "phase1"
    finally:
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews


def t_phase_from_approval_pr_review_approve_from_differing_account_is_phase2():
    # two-account mode: PR review 의 Approve 가 승인자 계정에서 오면 코멘트
    # 없이도 phase2 (contract v3 s19).
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = lambda repo, n: []
    ci._pr_reviews = lambda repo, pr: [{"state": "APPROVED", "author": {"login": "jjongkwann"}}]
    try:
        assert ci._phase_from_approval(Path("."), 1, 245, "implementation") == "phase2"
    finally:
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews


def t_phase_from_approval_pr_thread_comment_is_not_issue_level_is_phase1():
    # F3 (issue #275) red-green: contract v3 s19's single-account path
    # recognizes only an issue-level comment — a qualifying APPROVE-shaped
    # comment posted on the PR's own conversation thread (mocked here as
    # `spawn._issue_comments(repo, pr=1)`, distinct from the issue-level
    # `spawn._issue_comments(repo, issue=245)`, which stays empty) must
    # not open phase2. Pre-fix, `_phase_from_approval` unioned
    # `spawn._issue_comments(repo, pr)` into its input and this exact
    # arrangement returned "phase2"; post-fix (the second fetch removed)
    # it stays "phase1".
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = (
        lambda repo, n: [{"login": "jjongkwann", "body": "APPROVE issue-245/implementation"}]
        if n == 1 else [])
    ci._pr_reviews = lambda repo, pr: []
    try:
        assert ci._phase_from_approval(Path("."), 1, 245, "implementation") == "phase1"
    finally:
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews


def t_autodetect_success_derives_issue_role_and_phase_from_approval():
    # --autodetect 는 이제 phase 를 본문 키워드가 아니라 승인 이벤트에서
    # 끌어낸다 — 본문에 closing 키워드가 있어도 승인이 없으면 phase1.
    orig_head_ref = ci._pr_head_ref
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    ci._pr_head_ref = lambda repo, pr: "issue-245/implementation"
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = lambda repo, n: []
    ci._pr_reviews = lambda repo, pr: []
    try:
        result = ci._autodetect_issue_phase(Path("."), 1, None, None)
    finally:
        ci._pr_head_ref = orig_head_ref
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews
    assert result == (245, "phase1"), result


def t_pr_commit_messages_paginates_and_flattens():
    # warrant-hunter(silent-failure stance) 발견: gh api 의 커밋 목록
    # 엔드포인트는 페이지당 30개로 잘린다 — --paginate --slurp 없이는
    # 31번째 이후 커밋의 closing 키워드가 조용히 안 걸린다. 페이지 두 장을
    # 흉내 내 평탄화가 실제로 되는지, 호출 인자에 두 플래그가 실제로
    # 실리는지 확인한다.
    import subprocess as _subprocess

    class FakeResult:
        returncode = 0
        stdout = ('[[{"commit": {"message": "first"}}], '
                  '[{"commit": {"message": "second"}}]]')

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return FakeResult()

    orig_run = _subprocess.run
    orig_slug = spawn._repo_slug
    _subprocess.run = fake_run
    spawn._repo_slug = lambda repo: "tokenmaxxxer/on-the-record"
    try:
        result = ci._pr_commit_messages(Path("."), 1)
    finally:
        _subprocess.run = orig_run
        spawn._repo_slug = orig_slug
    assert result == ["first", "second"], result
    assert "--paginate" in calls[0] and "--slurp" in calls[0], calls


def t_ci_check_closes_only_skips_write_scope_and_protected_path_bundle():
    # closes_only=True 는 gates.changed_files()가 필요 없는 검사(write_scope,
    # protected-path, deps, record)를 전부 건너뛴다 — origin/main 이 없는
    # 저장소에서 RuntimeError 없이 통과하는 것으로 확인한다(pr/issue 없음).
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        subprocess.run(["git", "init", "-q"], cwd=work, check=True)
        assert ci.check(work, closes_only=True) == []


def t_ci_check_closes_only_still_enforces_phase1_mismatch():
    # closes_only=True 라도 계획-인지 Closes 게이트(+phase1 mismatch)는 돈다
    # — 이게 이 모드의 존재 이유다. 네트워크 없이 확인한다.
    orig_body = pr_reference._pr_view
    orig_title, orig_commits = ci._pr_title, ci._pr_commit_messages
    pr_reference._pr_view = lambda repo, pr: "Closes #245, more context"
    ci._pr_title = lambda repo, pr: "issue-245: phase 1"
    ci._pr_commit_messages = lambda repo, pr: []
    try:
        bad = ci.check(Path("."), pr=1, issue=245, phase="phase1", closes_only=True)
    finally:
        pr_reference._pr_view = orig_body
        ci._pr_title, ci._pr_commit_messages = orig_title, orig_commits
    assert any("closing 키워드" in b for b in bad), bad


def t_ci_check_closes_only_passes_clean_phase1_body():
    orig_body = pr_reference._pr_view
    orig_title, orig_commits = ci._pr_title, ci._pr_commit_messages
    pr_reference._pr_view = lambda repo, pr: "proposal for #245, no closing keyword"
    ci._pr_title = lambda repo, pr: "issue-245: phase 1 proposal"
    ci._pr_commit_messages = lambda repo, pr: ["wip", "phase 1 work"]
    try:
        bad = ci.check(Path("."), pr=1, issue=245, phase="phase1", closes_only=True)
    finally:
        pr_reference._pr_view = orig_body
        ci._pr_title, ci._pr_commit_messages = orig_title, orig_commits
    assert bad == [], bad


def t_autodetect_reachability_fix_blocks_closes_keyword_without_approval():
    # 요구사항 2 재현성 수정의 핵심 red-green 증거: pre-fix 에서는 phase
    # 가 closing 키워드 자체에서 유도돼 이 시나리오("승인 없음 + 본문에
    # Closes 키워드")가 phase2 로 오판되고, phase1-mismatch 검사가 phase1
    # 분기 안에서만 돌아 구조적으로 도달 불가했다(#245 관찰 F1). post-fix
    # 에서는 phase 가 승인 이벤트로만 결정돼 phase1 로 남고, 검사가
    # 실제로 도달해 차단한다 — 배선된 `--autodetect --closes-only` 형태
    # 그대로 증명한다.
    orig_head_ref = ci._pr_head_ref
    orig_body = pr_reference._pr_view
    orig_title, orig_commits = ci._pr_title, ci._pr_commit_messages
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    ci._pr_head_ref = lambda repo, pr: "issue-245/implementation"
    pr_reference._pr_view = lambda repo, pr: "Closes #245"
    ci._pr_title = lambda repo, pr: "issue-245: phase 1"
    ci._pr_commit_messages = lambda repo, pr: []
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = lambda repo, n: []
    ci._pr_reviews = lambda repo, pr: []
    try:
        detected = ci._autodetect_issue_phase(Path("."), 1, None, None)
        assert detected == (245, "phase1"), detected
        issue, phase = detected
        bad = ci.check(Path("."), pr=1, issue=issue, phase=phase, closes_only=True)
    finally:
        ci._pr_head_ref = orig_head_ref
        pr_reference._pr_view = orig_body
        ci._pr_title, ci._pr_commit_messages = orig_title, orig_commits
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews
    assert any("본문에" in b and "closing 키워드" in b for b in bad), bad


def t_phase1_mismatch_pre_271_body_only_gate_missed_commit_message_keyword():
    # F4 (issue #275) — behavioral red proof for requirement 4, replacing
    # the original record's proof (docs/issue-271/reports/implementation.md
    # closed_checks red entry), which showed only an `AttributeError` from
    # a not-yet-existing symbol (evidence the new API didn't exist yet,
    # not evidence of old behavior). The pre-#271 gate shape is still
    # live: `_phase1_mismatch` (gates/ci.py:169, kept at its pre-#271
    # single-surface shape because older unit tests call it directly)
    # only ever inspected the PR body — a closing keyword sitting only in
    # a commit message passed it silently, regardless of the commit
    # messages' actual content. Pairs with
    # t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body
    # below, which drives the real post-#271 multi-surface check
    # (`_phase1_surface_mismatch` via `--autodetect --closes-only`)
    # against the identical scenario and shows it blocking.
    clean_body = "no closing keyword, see #245"
    assert ci._phase1_mismatch(clean_body, 245) == []


def t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body():
    # requirement 4 회귀: 본문·제목 clean + 승인 없음 + 커밋 메시지에
    # closing 키워드 → --autodetect --closes-only 배선 그대로 차단.
    # #245/#262/#266 관찰의 실물 사고(commit-message 벡터)를 동형 재현한다.
    orig_head_ref = ci._pr_head_ref
    orig_body = pr_reference._pr_view
    orig_title, orig_commits = ci._pr_title, ci._pr_commit_messages
    orig_approvers, orig_comments, orig_reviews = spawn._approvers, spawn._issue_comments, ci._pr_reviews
    ci._pr_head_ref = lambda repo, pr: "issue-245/implementation"
    pr_reference._pr_view = lambda repo, pr: "no closing keyword, see #245"
    ci._pr_title = lambda repo, pr: "issue-245: phase 1 proposal"
    ci._pr_commit_messages = lambda repo, pr: ["proposal work", "Closes #245"]
    spawn._approvers = lambda repo: {"jjongkwann"}
    spawn._issue_comments = lambda repo, n: []
    ci._pr_reviews = lambda repo, pr: []
    try:
        detected = ci._autodetect_issue_phase(Path("."), 1, None, None)
        assert detected == (245, "phase1"), detected
        issue, phase = detected
        bad = ci.check(Path("."), pr=1, issue=issue, phase=phase, closes_only=True)
    finally:
        ci._pr_head_ref = orig_head_ref
        pr_reference._pr_view = orig_body
        ci._pr_title, ci._pr_commit_messages = orig_title, orig_commits
        spawn._approvers, spawn._issue_comments, ci._pr_reviews = orig_approvers, orig_comments, orig_reviews
    assert any("커밋 메시지에" in b and "closing 키워드" in b for b in bad), bad


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
