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
    assert gates.dep_names("package.json", "깨진 json") == set()
    assert gates.dep_names("requirements.txt",
                           "requests==2.31.0\n# 주석\nhttpx>=0.27\n\n") == {"requests", "httpx"}


def t_parse_new_deps():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (work / "requirements.txt").write_text("requests==2.31.0\nhttpx>=0.27\n")
        (work / "package.json").write_text('{"dependencies": {"left-pad": "^1.0.0"}}')
        subprocess.run(["git", "-C", str(work), "add", "-A"], check=True,
                       capture_output=True)
        found = dict((n, m) for m, n in gates.parse_new_deps(work))
        assert found.get("httpx") == "requirements.txt", found
        assert found.get("left-pad") == "package.json", found
        assert "requests" not in found, "기존 의존성은 새 것으로 잡히면 안 된다"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
