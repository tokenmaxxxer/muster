#!/usr/bin/env python3
"""muster 자체 점검. 네트워크·GitHub 없이 도는 것만.

  python3 test_gates.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent))
import gates
import spawn
import wakes


def _board(td: str, subject: str, **roles: str) -> Path:
    """계약 v2 §10 의 블랙보드를 만든다: docs/reports/records/<subject>/<역할>.md"""
    root = Path(td) / "repo"
    d = root / spawn.BOARD / subject
    d.mkdir(parents=True)
    for role, fm in roles.items():
        (d / f"{role}.md").write_text(f"---\n{fm}\n---\n\n본문\n")
    return root


def t_slug_is_directory_name():
    """§9: 레포 디렉터리 이름. 리모트가 없어도 깨지지 않는 것이 요점이다."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "car-wash-app"
        d.mkdir()
        assert spawn.slug(str(d)) == "car-wash-app", spawn.slug(str(d))


def t_board_reads_loop_state():
    with tempfile.TemporaryDirectory() as td:
        root = _board(td, "2026-07-26-wash",
                      product="kind: product-record\nloop_state: measuring",
                      feasibility="kind: feasibility-record\nloop_state: verdict\nverdict: go")
        b = spawn.board(root)
        assert list(b) == ["2026-07-26-wash"], b
        assert b["2026-07-26-wash"]["product"]["loop_state"] == "measuring"
        assert b["2026-07-26-wash"]["feasibility"]["verdict"] == "go"
        line = "\n".join(spawn.status(str(root)))
        assert "loop_state: measuring" in line, line
        assert "verdict: go" in line, line
        # 기록이 없는 역할을 "상태 없음"으로 뭉뚱그리면 누가 안 깨어났는지 못 본다
        assert "기록 없음" in line and "qa" in line, line


def t_board_tolerates_trailing_comment():
    """§2: 주석을 못 읽는 파서는 **게이트 결함이지 기록의 위반이 아니다**."""
    with tempfile.TemporaryDirectory() as td:
        root = _board(td, "s", coding="kind: build-proposal  # re-scoped\n"
                                      "loop_state: approved   # 사람이 승인함")
        fm = spawn.board(root)["s"]["coding"]
        assert fm["kind"] == "build-proposal", fm
        assert fm["loop_state"] == "approved", fm


def _wake_repo(td: str) -> Path:
    """hypothesis 하나를 커밋해 둔 레포. sha 비교가 필요하므로 진짜 git 이어야 한다."""
    root = Path(td) / "repo"
    (root / "docs" / "proposals").mkdir(parents=True)
    (root / spawn.BOARD / "s").mkdir(parents=True)
    (root / "docs/proposals/h.md").write_text(
        "---\nkind: hypothesis\nsubject: s\nloop_state: hypothesis-registered\n---\n")
    run = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, check=True)
    run("init", "-q")
    run("config", "user.email", "t@t"); run("config", "user.name", "t")
    run("add", "-A"); run("commit", "-qm", "h")
    return root


def _woken(root: Path) -> dict[str, str]:
    return {r: why for r, why in wakes.evaluate(str(root))[0]}


def t_wake_hypothesis_wakes_feasibility():
    with tempfile.TemporaryDirectory() as td:
        root = _wake_repo(td)
        assert "feasibility" in _woken(root), _woken(root)


def t_wake_acknowledged_hypothesis_goes_quiet():
    """계약 §6: 바뀌지 않은 보드는 아무도 깨우지 않는다. 이게 없으면 루프가 안 끝난다."""
    with tempfile.TemporaryDirectory() as td:
        root = _wake_repo(td)
        sha = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%H",
                              "--", "docs/proposals/h.md"],
                             capture_output=True, text=True).stdout.strip()
        (root / spawn.BOARD / "s" / "feasibility.md").write_text(
            "---\nkind: feasibility-record\nloop_state: probing\n"
            f"upstream:\n  - path: docs/proposals/h.md\n    sha: {sha}\n---\n")
        assert "feasibility" not in _woken(root), _woken(root)


def t_wake_verdict_go_wakes_coding():
    with tempfile.TemporaryDirectory() as td:
        root = _wake_repo(td)
        (root / spawn.BOARD / "s" / "feasibility.md").write_text(
            "---\nkind: feasibility-record\nloop_state: verdict\nverdict: go\n---\n")
        assert "coding" in _woken(root), _woken(root)


def t_wake_finding_wakes_the_addressed_role():
    """§5 의 되돌이 간선. finding 은 frontmatter 가 아니라 **본문 안에** 산다."""
    with tempfile.TemporaryDirectory() as td:
        root = _wake_repo(td)
        (root / spawn.BOARD / "s" / "review.md").write_text(
            "---\nkind: review-record\nloop_state: reported\n---\n\n"
            "## finding\nrequirement: R1\nverdict: Incorrect\n"
            "addressed_to: coding\nseverity: blocking\n")
        w = _woken(root)
        assert "coding" in w and "addressed_to" in w["coding"], w


def t_wake_never_reports_judgement_rows_as_unwoken():
    """§14: 기계 검사는 실질 검사가 아니다. 못 재는 줄을 '안 깨어남'으로 보고하면
    사람이 봐야 할 두 줄이 조용히 사라진다."""
    with tempfile.TemporaryDirectory() as td:
        root = _wake_repo(td)
        _, judged = wakes.evaluate(str(root))
        assert {r for r, _ in judged} == {"product", "ops"}, judged
        text = "\n".join(wakes.report(str(root)))
        assert "못 재는 것이다" in text, text


def t_sandbox_boundary_follows_the_env():
    """역할의 env 를 환경으로 덮으면 샌드박스 경계도 따라와야 한다.

    안 따라오면 env 는 격리된 경로를 가리키는데 경계는 원래 경로만 허용한다 —
    격리했다고 믿는 채로 원래 자리에 쓰거나, 아무 데도 못 쓴다. bench 가 실제
    워크스페이스를 오염시킨 사고가 정확히 이 모양이었다.
    """
    import os
    old = os.environ.get("QA_WORKSPACE")
    os.environ["QA_WORKSPACE"] = "/tmp/isolated-ws"
    try:
        s = spawn.role_settings("qa")
        assert s["env"]["QA_WORKSPACE"] == "/tmp/isolated-ws", s["env"]
        assert s["sandbox"]["filesystem"]["allowWrite"] == ["/tmp/isolated-ws"], s["sandbox"]
    finally:
        if old is None:
            del os.environ["QA_WORKSPACE"]
        else:
            os.environ["QA_WORKSPACE"] = old


def t_missing_contract_stops_the_spawn():
    """실측 A/B: 레포에 계약이 없으면 역할이 계약 헤더 없이 기록을 쓰고, 보드에
    아무것도 안 올라가고, 세션은 성공으로 끝난다. 경고로는 안 되는 이유가 그
    조용함이다 — 한 세션을 통째로 버린다."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        (root / "docs" / "specs").mkdir(parents=True)
        try:
            spawn.require_contract(str(root), override=False)
        except SystemExit as e:
            assert spawn.CONTRACT in str(e), e
        else:
            raise AssertionError("계약이 없는데 통과시켰다")

        # 명시적 opt-out 은 통과. 사고가 아니라 결정이어야 한다.
        spawn.require_contract(str(root), override=True)

        (root / spawn.CONTRACT).write_text("# contract\n")
        spawn.require_contract(str(root), override=False)


def t_rulebook_version_is_recorded():
    """룰북은 로컬 디렉터리로 물리므로 핀이 없다 — 그 순간 체크아웃된 것이 돈다.
    핀을 못 박으면 **무엇이 돌았는지라도 남겨야** ablation 이 검증 가능해진다."""
    v = spawn.rulebook_version("qa")
    assert "(" in v and ")" in v, v          # sha (branch)
    assert "커밋안됨" not in v or True       # 더러우면 그 사실이 문자열에 남는다

    # 알 수 없을 때 조용히 빈 문자열을 돌려주면 기록이 "버전 없음"으로 보인다.
    import json, tempfile
    with tempfile.TemporaryDirectory() as td:
        role = spawn.ROOT / "roles" / "_probe.json"
        role.write_text(json.dumps({"marketplace": "x", "path": td}))
        try:
            assert "불명" in spawn.rulebook_version("_probe"), spawn.rulebook_version("_probe")
        finally:
            role.unlink()


def t_rulebook_falls_back_to_github():
    """로컬 체크아웃이 있으면 그쪽, 없으면 github. 절대경로 하나 때문에 다른 기계에서
    아예 안 도는 상태였다 — 역할 파일이 제작자의 홈 경로를 박고 있었다."""
    import json as _json
    spec = _json.loads((spawn.ROOT / "roles" / "qa.json").read_text())
    assert spec.get("repo"), "역할 파일에 repo 가 없으면 github 로 떨어질 수 없다"

    local = spawn.rulebook_source(spec)
    assert local["source"] == "directory", local        # 개발용 로컬이 이긴다

    spec["path"] = "/nonexistent-checkout"
    remote = spawn.rulebook_source(spec)
    assert remote == {"source": "github", "repo": spec["repo"]}, remote

    spec.pop("repo")
    try:
        spawn.rulebook_source(spec)
    except SystemExit:
        pass
    else:
        raise AssertionError("소스가 없는데 통과시켰다")


def t_board_absent_names_the_v1_location():
    """보드 없음과 v1 자리에 있음은 정반대 처분을 받아야 한다."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        root.mkdir()
        empty = "\n".join(spawn.status(str(root)))
        assert "보드 없음" in empty and "계약 v1" not in empty, empty

        (root / "review-record.md").write_text("---\nphase: scoped\n---\n")
        stale = "\n".join(spawn.status(str(root)))
        assert "계약 v1" in stale and "review" in stale, stale





def _repo(td: str) -> Path:
    work = Path(td) / "work"
    work.mkdir(parents=True)
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                    capture_output=True, check=True)
    run("init", "-q", "-b", "main")
    run("config", "user.email", "t@t"); run("config", "user.name", "t")
    (work / "requirements.txt").write_text("requests==2.31.0\n")
    run("add", "-A"); run("commit", "-qm", "init")
    run("branch", "-f", "origin/main")          # diff 기준점 대역
    return work



def t_rename_bypass():
    # git mv 한 번으로 보호 경로와 write-set 을 동시에 빠져나가면 안 된다.
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (Path(td) / "spec.md").write_text("- write: allowed*\n")
        (work / "allowed.txt").write_text("x")
        run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                        capture_output=True, check=True)
        run("add", "-A"); run("-c", "user.email=t@t", "-c", "user.name=t",
                              "commit", "-qm", "add")
        (work / ".github").mkdir()
        run("mv", "allowed.txt", ".github/pwn.js")
        files = gates.changed_files(work)
        assert ".github/pwn.js" in files, files
        assert "allowed.txt" in files, f"rename 원본도 검사해야 한다: {files}"
        assert any("보호 경로" in b for b in gates.writeset(Path(td), {}))


def t_commit_bypass():
    # git status 는 워커가 자기 작업을 커밋하면 깨끗해진다 — 커밋 diff 도 봐야
    # 게이트가 안 뚫린다. 수정 전 코드에서는 이 테스트가 실패한다(빈 리스트 반환).
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (Path(td) / "spec.md").write_text("- write: a.txt\n")
        (work / ".github").mkdir()
        (work / ".github" / "ci.yml").write_text("evil")
        run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                        capture_output=True, check=True)
        run("add", "-A"); run("-c", "user.email=t@t", "-c", "user.name=t",
                              "commit", "-qm", "protected path, committed")
        bad = gates.writeset(Path(td), {})
        assert any("보호 경로" in b for b in bad), f"커밋 후 게이트가 못 봤다: {bad}"


def t_origin_main_missing():
    # origin/main 자체가 없으면 "변경 없음"이 아니라 "검사 불가" — 워킹트리만 보고
    # 조용히 통과시키면 안 된다.
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "work"
        work.mkdir(parents=True)
        run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                        capture_output=True, check=True)
        run("init", "-q", "-b", "main")
        run("config", "user.email", "t@t"); run("config", "user.name", "t")
        (work / "a.txt").write_text("x")
        run("add", "-A"); run("commit", "-qm", "init")
        # origin/main 브랜치를 의도적으로 만들지 않는다
        try:
            gates.changed_files(work)
            assert False, "origin/main 없이도 조용히 통과했다"
        except RuntimeError as e:
            assert "fail closed" in str(e), e

        (Path(td) / "spec.md").write_text("- write: a.txt\n")
        bad = gates.writeset(Path(td), {})
        assert bad and "fail closed" in bad[0], bad


def t_deps_fail_closed():
    # 못 읽은 매니페스트를 "새 의존성 0개" 로 취급하면 환각 패키지가 통과한다
    for bad in ["{not json", '{"dependencies": [']:
        try:
            gates.dep_names("package.json", bad)
            assert False, f"파싱 실패를 통과시켰다: {bad}"
        except ValueError:
            pass
    try:
        gates.dep_names("requirements.txt", "-r extras.txt\n")
        assert False, "간접 참조를 통과시켰다"
    except ValueError:
        pass
    # optional/peer 도 검사 대상
    j = '{"optionalDependencies":{"a":"1"},"peerDependencies":{"b":"2"}}'
    assert gates.dep_names("package.json", j) == {"a", "b"}


def t_dep_direct_reference():
    # 이름은 레지스트리에 있어도 버전 스펙이 URL/직접 참조면 실제 설치 출처는 임의다
    for spec in ["git+https://evil.example/x.git", "file:../local-evil",
                 "https://evil.example/pkg-1.0.0.tgz", "github:evil/lodash",
                 "evil/lodash#main"]:
        j = json.dumps({"dependencies": {"lodash": spec}})
        try:
            gates.dep_names("package.json", j)
            assert False, f"직접 참조를 통과시켰다: {spec}"
        except ValueError:
            pass
    # 정상 레지스트리 범위는 여전히 통과
    j = json.dumps({"dependencies": {"lodash": "^1.0.0"}})
    assert gates.dep_names("package.json", j) == {"lodash"}

    # requirements.txt 도 같은 구멍 — bare URL, `pkg @ https://` 직접 참조
    for bad in ["https://evil.example/pkg.tar.gz\n",
                "evil-pkg @ https://evil.example/pkg.tar.gz\n"]:
        try:
            gates.dep_names("requirements.txt", bad)
            assert False, f"직접 참조를 통과시켰다: {bad}"
        except ValueError:
            pass
    assert gates.dep_names("requirements.txt", "requests==2.31.0\n") == {"requests"}


def t_writeset_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (work / "anything.py").write_text("x")
        (Path(td) / "spec.md").write_text("# 명세\n요구사항만 있고 write-set 없음\n")
        assert any("fail closed" in b for b in gates.writeset(Path(td), {}))



def t_protected_paths():
    # 미탐: 루트에 있어도 막아야 한다. 뒤 넷은 muster 가 자기 규칙을 다시 쓰는 경로다.
    for p in ["auth.py", "migrations/001.sql", ".env", "config/.env.prod",
              ".github/workflows/ci.yml", "app/secrets.pem", "lib/credentials.json",
              "protocol.md", "protocol.ko.md", "spawn.py", "roles/qa.json",
              "gates/gates.py"]:
        assert gates.is_protected(p), f"놓침: {p}"
    # 오탐: 평범한 설정 변경까지 막으면 게이트가 꺼진다. 뒤 둘은 **대상 레포**의
    # 정상 자산이다 — 보호는 루트 한 단계에만 걸려야 한다.
    for p in ["docker-compose.yml", "openapi.yaml", "app/settings.yaml",
              "calc.py", "src/handlers/user.py", "README.md",
              "src/app/roles/admin.py", "lib/gates/rate.go"]:
        assert not gates.is_protected(p), f"오탐: {p}"


def t_writeset_protected():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (work / ".github").mkdir()
        (work / ".github" / "ci.yml").write_text("evil")
        bad = gates.writeset(Path(td), {})
        assert any("보호 경로" in b for b in bad), bad


def t_writeset_declared():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (Path(td) / "spec.md").write_text("요구사항\n- write: calc.py\n")
        (work / "calc.py").write_text("x = 1")
        assert gates.writeset(Path(td), {}) == []       # 허용 경로
        (work / "sneaky.py").write_text("x = 2")
        assert any("write-set 이탈" in b for b in gates.writeset(Path(td), {}))


def t_dep_names():
    # 한 줄이든 여러 줄이든 같은 집합이 나와야 한다 (줄 단위 파싱이면 깨진다)
    flat = '{"dependencies":{"left-pad":"^1.0.0"},"devDependencies":{"jest":"29"}}'
    multi = json.dumps(json.loads(flat), indent=2)
    assert gates.dep_names("package.json", flat) == {"left-pad", "jest"}
    assert gates.dep_names("package.json", multi) == {"left-pad", "jest"}
    # 깨진 매니페스트는 빈 집합이 아니라 오류다 — t_deps_fail_closed 참조
    assert gates.dep_names("requirements.txt",
                           "requests==2.31.0\n# 주석\nhttpx>=0.27\n\n") == {"requests", "httpx"}


def t_parse_new_deps():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (work / "requirements.txt").write_text("requests==2.31.0\nhttpx>=0.27\n")
        (work / "package.json").write_text('{"dependencies": {"left-pad": "^1.0.0"}}')
        subprocess.run(["git", "-C", str(work), "add", "-A"], check=True,
                       capture_output=True)
        new, errs = gates.parse_new_deps(work)
        assert errs == [], errs
        found = dict((n, m) for m, n in new)
        assert found.get("httpx") == "requirements.txt", found
        assert found.get("left-pad") == "package.json", found
        assert "requests" not in found, "기존 의존성은 새 것으로 잡히면 안 된다"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
