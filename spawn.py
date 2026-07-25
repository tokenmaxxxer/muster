#!/usr/bin/env python3
"""역할별 플러그인 환경으로 에이전트를 띄운다. harness 의 핵심 동작 하나.

  python3 spawn.py <역할> <맡길 일> [-C <작업 디렉터리>] [--dry-run]
  python3 spawn.py review "PR 12 를 리뷰해라"
  python3 spawn.py qa "/testrun:testrun smoke" -C ~/work/some-repo

**왜 스크립트가 필요한가**: `--settings` 는 덮어쓰기가 아니라 **병합**이다. 역할
파일에 qa 플러그인만 적어도 사용자 전역 설정의 플러그인 17개가 그대로 딸려온다 —
"코딩 에이전트가 qa 룰북까지 본다"는 원래 문제의 다른 얼굴이다. 전역 목록을 읽어
역할이 켜지 않은 것을 전부 `false` 로 덮어야 격리가 성립한다(실측 확인).

`--settings` 는 사용자 설정보다 우선순위가 높으므로 이 덮어쓰기가 이긴다.

**CLAUDE_CONFIG_DIR 로 통째 격리하지 않는 이유**: 설정은 완전히 갈리지만 macOS
키체인 항목이 설정 디렉터리에 묶여 있어 인증이 끊긴다("Not logged in"). 인증을
그대로 쓰는 것이 컨테이너 대신 샌드박스를 고른 이유이므로, 그 이점을 버리지 않는다.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER_SETTINGS = Path.home() / ".claude" / "settings.json"


def role_settings(role: str) -> dict:
    """역할 설정 + 전역 플러그인 차단을 합친 것."""
    f = ROOT / "roles" / f"{role}.json"
    if not f.exists():
        have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
        sys.exit(f"모르는 역할: {role}  (있는 것: {have})")
    s = json.loads(f.read_text())

    # 역할이 켜지 않은 전역 플러그인은 전부 끈다. 켜야 할 것을 적는 게 아니라
    # 꺼야 할 것을 빠짐없이 적는 쪽이라, 전역에 플러그인이 새로 깔려도 새지 않는다.
    try:
        globals_ = json.loads(USER_SETTINGS.read_text()).get("enabledPlugins", {})
    except (OSError, ValueError):
        globals_ = {}
    for name in globals_:
        s.setdefault("enabledPlugins", {}).setdefault(name, False)

    # 자격증명 마스킹은 TLS 종료가 없으면 sentinel 값만 흘러 도구 인증이 깨진다.
    sb = s.get("sandbox", {})
    if sb.get("credentials", {}).get("envVars") and "tlsTerminate" not in sb.get("network", {}):
        sb.setdefault("network", {})["tlsTerminate"] = {}

    # 샌드박스 밖 재실행을 막는다. 기본값이 허용이라, 명령이 경계에 막히면 에이전트가
    # 그대로 샌드박스를 끄고 다시 돌린다 — 실측에서 denyRead 로 막은 ~/.claude 를
    # 그렇게 읽어냈다. 그러면 경계가 아니라 권고다.
    sb["allowUnsandboxedCommands"] = False
    s["sandbox"] = sb
    return s


def assert_installed(role: str, want: list[str]) -> None:
    """역할의 플러그인이 실제로 설치돼 있는지 확인. 없으면 멈춘다.

    첫 스폰은 마켓플레이스를 **등록만** 하고 플러그인은 다음 실행부터 붙는다
    (실측). 그 사이 세션은 룰북 0개로 조용히 돌아간다 — 겉보기엔 성공이라
    ablation 결과를 통째로 오염시킨다. 조용한 실패를 시끄러운 실패로 바꾼다.
    """
    try:
        have = set(json.loads(
            (Path.home() / ".claude/plugins/installed_plugins.json").read_text())["plugins"])
    except (OSError, ValueError, KeyError):
        have = set()
    missing = [p for p in want if p not in have]
    if missing:
        sys.exit(
            f"[{role}] 플러그인이 아직 설치되지 않았다: {', '.join(missing)}\n"
            f"  마켓플레이스 등록만 된 상태로 띄우면 룰북 0개로 돈다.\n"
            f"  한 번 더 실행하거나 `claude` 세션에서 /plugin 으로 설치한 뒤 다시 시도한다.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("role")
    ap.add_argument("task", help="맡길 일. 룰북 커맨드면 '/plugin:command 인자'")
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
    ap.add_argument("--dry-run", action="store_true", help="합쳐진 설정만 보고 안 띄운다")
    a = ap.parse_args()

    s = role_settings(a.role)
    on = [k for k, v in s.get("enabledPlugins", {}).items() if v]
    if a.dry_run:
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return 0
    assert_installed(a.role, on)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(s, f)
        settings = f.name
    try:
        print(f"[{a.role}] 플러그인 {len(on)}개, 작업 디렉터리 {a.cwd}", file=sys.stderr)
        # 맡길 일은 stdin 으로 넘긴다. 인자로 주면 가변 인자 플래그가 삼키고,
        # 셸 보간을 거치면 신뢰할 수 없는 값의 $(…) 가 실행된다.
        return subprocess.run(
            ["claude", "-p", "--settings", settings],
            cwd=a.cwd, input=a.task, text=True,
            env={**os.environ, "CLAUDE_ROLE": a.role},
        ).returncode
    finally:
        os.unlink(settings)


if __name__ == "__main__":
    sys.exit(main())
