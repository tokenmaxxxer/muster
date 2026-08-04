#!/usr/bin/env python3
"""issue #245 — 계획-인지 Closes 게이트 강제 배선(ci.py 추가분)의 단위 테스트.

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
import ci
import pr_reference


def t_issue_from_branch_matches_convention():
    assert ci._issue_from_branch("issue-245/implementation") == 245
    assert ci._issue_from_branch("issue-245/execution-observation") == 245
    assert ci._issue_from_branch("issue-7/technical-writing") == 7


def t_issue_from_branch_rejects_unrecognized_names():
    assert ci._issue_from_branch("patch-1") is None
    assert ci._issue_from_branch("dependabot/npm_and_yarn/foo-1.2.3") is None
    assert ci._issue_from_branch("main") is None
    assert ci._issue_from_branch("issue-245") is None  # 슬래시 뒤 role 없음


def t_phase_from_body_closes_keyword_is_phase2():
    assert ci._phase_from_body("Closes #245", 245) == "phase2"
    assert ci._phase_from_body("closes #245", 245) == "phase2"
    assert ci._phase_from_body("Fixes #245 and more", 245) == "phase2"


def t_phase_from_body_wrong_issue_number_is_phase1():
    # Closes 키워드가 있어도 *다른* 이슈를 향하면 이 이슈에겐 phase1이다.
    assert ci._phase_from_body("Closes #999", 245) == "phase1"


def t_phase_from_body_no_closes_keyword_is_phase1():
    assert ci._phase_from_body("see #245 for context", 245) == "phase1"
    assert ci._phase_from_body("no reference here", 245) == "phase1"


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
    # `.finditer()`로 전체를 훑어야 하는 이유. 이게 실패하면 무해해 보이는
    # 앞쪽 참조 하나만 끼워 넣어 phase-1 PR의 실제 Closes를 게이트가 못 보게
    # 만들 수 있다.
    body = "This also fixes a side issue, Fixes #999, and Closes #245 as the main delivery."
    bad = ci._phase1_mismatch(body, 245)
    assert bad and "closing 키워드" in bad[0], bad
    assert ci._phase_from_body(body, 245) == "phase2", \
        "앞쪽의 무관한 #999 참조에 가려 #245 를 향한 Closes 를 놓쳤다"


def t_phase1_mismatch_matches_inside_fenced_quote():
    # GitHub 자신이 코드펜스 안 인용도 closing 키워드로 파싱한다(실물 사고:
    # repo-status-board PR #26가 백틱 인용까지 파싱돼 이슈가 또 닫혔다,
    # docs/issue-245/reports/implementation/survey.md 참조). phase2 쪽은
    # `test_gates.py::t_pr_reference_phase2_fenced_closes_still_blocks_when_incomplete`
    # 로 이미 지켜진다 — 같은 정규식을 재사용하는 phase1 mismatch 검사도
    # 같은 성질을 상속하는지 확인한다.
    body = "설명 중 인용:\n```\nCloses #245\n```\n"
    bad = ci._phase1_mismatch(body, 245)
    assert bad and "closing 키워드" in bad[0], bad


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


def t_autodetect_success_derives_issue_and_phase():
    orig_branch = ci._pr_head_ref
    orig_body = pr_reference._pr_view
    ci._pr_head_ref = lambda repo, pr: "issue-245/implementation"
    pr_reference._pr_view = lambda repo, pr: "no closing keyword, see #245"
    try:
        result = ci._autodetect_issue_phase(Path("."), 1, None, None)
    finally:
        ci._pr_head_ref = orig_branch
        pr_reference._pr_view = orig_body
    assert result == (245, "phase1"), result


def t_autodetect_respects_explicit_issue_and_phase():
    # --issue/--phase 가 명시로 주어졌으면 자동추정은 건드리지 않는다.
    result = ci._autodetect_issue_phase(Path("."), 1, 999, "phase2")
    assert result == (999, "phase2"), result


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
    # — 이게 이 모드의 존재 이유다. `gh pr view` 를 몽키패치해 네트워크 없이
    # 확인한다.
    original = pr_reference._pr_view
    pr_reference._pr_view = lambda repo, pr: "Closes #245, more context"
    try:
        bad = ci.check(Path("."), pr=1, issue=245, phase="phase1", closes_only=True)
    finally:
        pr_reference._pr_view = original
    assert any("closing 키워드" in b for b in bad), bad


def t_ci_check_closes_only_passes_clean_phase1_body():
    original = pr_reference._pr_view
    pr_reference._pr_view = lambda repo, pr: "proposal for #245, no closing keyword"
    try:
        bad = ci.check(Path("."), pr=1, issue=245, phase="phase1", closes_only=True)
    finally:
        pr_reference._pr_view = original
    assert bad == [], bad


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
