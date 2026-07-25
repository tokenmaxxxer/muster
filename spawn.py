#!/usr/bin/env python3
"""역할별 플러그인 환경으로 에이전트를 띄운다. muster 의 핵심 동작 하나.

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


def slug(cwd: str) -> str | None:
    """origin 리모트에서 <owner>-<repo>. 룰북이 프로젝트를 식별하는 방식과 같다."""
    p = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None
    parts = p.stdout.strip().removesuffix(".git").replace(":", "/").split("/")
    return "-".join(parts[-2:]) if len(parts) >= 2 else None


def status(cwd: str) -> list[str]:
    """각 역할이 노출한 상태를 **읽는다**. 쓰지 않는다 (protocol.md §1).

    상태는 에이전트의 것이다. muster 가 이걸 고치기 시작하면 룰북의 전이 게이트를
    우회하게 된다 — qa-cycle 은 state.md 쓰기를 가로채 막지만, 그 파일을 밖에서
    고치면 문지기를 안 거친다.
    """
    # 역할 → 상태 파일. 대부분의 사이클은 프로젝트 디렉터리에 기록을 두고,
    # qa 만 중앙 워크스페이스를 쓴다(여러 프로젝트를 한 곳에서 추적하므로).
    IN_PROJECT = {"review": "review-record.md", "feasibility": "feasibility-record.md",
                  "ops": "state.md", "product": "product-record.md"}
    root, s = Path(cwd).resolve(), slug(cwd)
    out = [f"프로젝트: {s or '(git 리모트 없음)'}   경로: {root}"]

    def frontmatter(p: Path) -> str:
        parts = p.read_text().split("---")
        return " / ".join(l.strip() for l in (parts[1] if len(parts) > 2 else "").splitlines()
                          if l.strip()) or "(frontmatter 없음)"

    qa_ws = os.environ.get("QA_WORKSPACE") or json.loads(
        (ROOT / "roles/qa.json").read_text()).get("env", {}).get("QA_WORKSPACE", "")
    qa_st = Path(qa_ws) / "projects" / (s or "") / "state.md" if qa_ws and s else None
    out.append(f"[qa] {frontmatter(qa_st)}" if qa_st and qa_st.exists()
               else f"[qa] 진행 중 아님{'' if qa_ws else ' (QA_WORKSPACE 미설정)'}")

    for role, name in sorted(IN_PROJECT.items()):
        hits = [p for p in (root / name, root / "docs" / name) if p.exists()]
        out.append(f"[{role}] {frontmatter(hits[0])}" if hits else f"[{role}] 진행 중 아님")
    out.append("[coding] 상태기계 없음 — 스티어링만 한다")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", nargs="?", help="역할. 생략하면 상태만 보여준다")
    ap.add_argument("task", nargs="?", help="맡길 일. 룰북 커맨드면 '/plugin:command 인자'")
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
    ap.add_argument("--dry-run", action="store_true", help="합쳐진 설정만 보고 안 띄운다")
    a = ap.parse_args()

    if not a.role:
        print("\n".join(status(a.cwd)))
        print("\n역할: " + ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json"))))
        return 0
    if not a.task:
        sys.exit("맡길 일이 없다. 사용법: spawn.py <역할> \"<맡길 일>\" [-C <경로>]")

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
