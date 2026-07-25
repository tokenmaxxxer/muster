#!/usr/bin/env python3
"""라우터·게이트 자체 점검. 네트워크·GitHub 없이 도는 것만.

  python3 test_orchestrator.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "gates"))
import gates
import main

main.C = {
    "stages": {
        "plan":   {"next": "build",  "contract": "spec.md"},
        "build":  {"next": "review", "contract": "summary.md", "on_fail": "build"},
        "review": {"next": "qa",     "contract": "verdict.json", "verdict": True},
        "qa":     {"next": "done",   "contract": "run.md"},
    },
    "max_attempts": 3,
}


def t_stage_of():
    assert main.stage_of({"pipeline:build"}) == ("build", False)
    assert main.stage_of({"pipeline:build:running"}) == ("build", True)
    assert main.stage_of({"bug", "attempt:2"}) == (None, False)
    # 배차 대기와 배차됨이 동시에 있으면 배차됨이 이긴다 (중복 스폰 방지)
    assert main.stage_of({"pipeline:qa", "pipeline:qa:running"}) == ("qa", True)


def t_attempt():
    assert main.attempt_of({"pipeline:build"}) == 0
    assert main.attempt_of({"attempt:2", "pipeline:build"}) == 2


def t_verdict():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "out").mkdir()
        # codex 는 코드펜스로 감싸 내보내는 경우가 있다 — 관대하게 파싱해야 한다
        (d / "out" / "verdict.json").write_text(
            '설명\n```json\n{"approved": false, "reason": "요구사항 3 누락"}\n```')
        ok, why = main.verdict_ok(d, "review")
        assert ok is False and "요구사항 3" in why, (ok, why)

        (d / "out" / "verdict.json").write_text('{"approved": true, "reason": "ok"}')
        assert main.verdict_ok(d, "review")[0] is True
        # verdict 스테이지가 아니면 항상 통과
        assert main.verdict_ok(d, "qa")[0] is True


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


def t_verdict_strict_bool():
    # 리뷰어가 기각하려고 낸 산출물이 머지로 이어지면 안 된다.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td); (d / "out").mkdir()
        v = d / "out" / "verdict.json"
        for payload in ['{"approved": "false", "reason": "미충족"}',
                        '{"approved": "no"}', '{"approved": 0.0}',
                        '{"approved": {}}', '{"reason": "판정 없음"}']:
            v.write_text(payload)
            assert main.verdict_ok(d, "review")[0] is False, payload
        v.write_text('{"approved": true, "reason": "ok"}')
        assert main.verdict_ok(d, "review")[0] is True
        # 깨진 JSON 은 예외가 아니라 기각으로 (회수 루프를 죽이면 안 된다)
        v.write_text('{"approved": tru')
        assert main.verdict_ok(d, "review")[0] is False


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


def t_redact():
    # push 실패 메시지에는 명령줄이 통째로 실린다. 자격증명이 트래커로 새면 안 된다.
    leak = ("git push https://x-access-token:gho_AAAAAAAAAAAAAAAAAAAAAAAA@github.com/o/r\n"
            "fatal: Authentication failed")
    out = main.redact(leak)
    assert "gho_" not in out and "x-access-token:" not in out, out
    assert "Authentication failed" in out, "진단 정보까지 지우면 안 된다"


def t_protected_paths():
    # 미탐: 루트에 있어도 막아야 한다
    for p in ["auth.py", "migrations/001.sql", ".env", "config/.env.prod",
              ".github/workflows/ci.yml", "adapters.yml", "app/secrets.pem",
              "lib/credentials.json"]:
        assert gates.is_protected(p), f"놓침: {p}"
    # 오탐: 평범한 설정 변경까지 막으면 게이트가 꺼진다
    for p in ["docker-compose.yml", "openapi.yaml", "app/settings.yaml",
              "calc.py", "src/handlers/user.py", "README.md"]:
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
