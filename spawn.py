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
import string
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER_SETTINGS = Path.home() / ".claude" / "settings.json"


MARKETPLACES = Path.home() / ".claude" / "plugins" / "marketplaces"
KNOWN = MARKETPLACES.parent / "known_marketplaces.json"


def _mkt(d: Path) -> Path:
    return d / ".claude-plugin" / "marketplace.json"


def registered(name: str) -> dict:
    """등록부에 이미 있는 마켓플레이스 항목. 없으면 {}."""
    try:
        return json.loads(KNOWN.read_text()).get(name, {})
    except (OSError, ValueError):
        return {}


def rulebook_source(spec: dict) -> dict:
    """룰북을 어디서 가져올지. **로컬 체크아웃이 있으면 그쪽이 이긴다.**

    로컬 우선인 이유는 개발이다 — 룰북을 고치면서 muster 로 돌려볼 때 커밋·푸시를
    거치게 하면 아무도 안 쓴다. 없으면 github 에서 받는다. 비공개 레포도 된다(실측).
    """
    p = spec.get("path")
    if p and _mkt(Path(p)).exists():
        return {"source": "directory", "path": p}
    if spec.get("repo"):
        return {"source": "github", "repo": spec["repo"]}
    sys.exit(f"룰북을 어디서 가져올지 모른다. 역할 파일에 repo 나 path 가 필요하다: {spec}")


def rulebook_dir(spec: dict) -> Path | None:
    """`marketplace.json` 을 실제로 읽을 수 있는 디렉터리. 아직 없으면 None.

    클론 자리를 짐작하기 전에 **등록부의 installLocation 을 먼저 본다.** 이름이
    이미 등록돼 있으면 `--settings` 의 extraKnownMarketplaces 는 무시되고 등록된
    쪽이 그대로 쓰인다 — muster 가 github 를 달라고 해도 등록부가 directory 면
    클론은 영영 안 생긴다. 실측 2026-07-26: 룰북 9개 중 8개는 이름만으로 받아졌고
    coding 만 실패했는데, 원인은 레포가 아니라 어제 로컬 경로로 등록해 둔
    `tokenmaxxxer-coding` 항목이었다.
    """
    p = spec.get("path")
    if p and _mkt(Path(p)).exists():
        return Path(p)
    loc = registered(spec["marketplace"]).get("installLocation")
    if loc and _mkt(Path(loc)).exists():
        return Path(loc)
    clone = MARKETPLACES / spec["marketplace"]
    return clone if _mkt(clone).exists() else None


def ensure_rulebook(role: str, spec: dict) -> Path:
    """룰북을 손에 넣는다. github 소스면 한 번 받아와야 목록을 읽을 수 있다.

    닭과 달걀: `enabledPlugins` 를 쓰려면 플러그인 이름이 필요하고, 이름은
    `marketplace.json` 에 있고, 그 파일은 클론이 있어야 읽는다. 그래서 마켓플레이스
    등록만 담은 설정으로 한 번 돌려 받아오고, 그 다음에 목록을 읽는다.
    """
    d = rulebook_dir(spec)
    if d:
        # 등록부가 이미 다른 출처를 물고 있으면 그쪽이 이긴다. 조용히 넘어가면
        # "github 에서 받은 룰북으로 돌렸다"고 믿으면서 실제로는 커밋 안 된
        # 로컬 체크아웃으로 돈다 — ablation 이 어느 룰북을 쟀는지 말할 수 없게 된다.
        want = rulebook_source(spec)
        reg = registered(spec["marketplace"])
        if reg.get("source") and reg["source"] != want:
            print(f"[{role}] 등록부가 이 마켓플레이스를 다르게 물고 있다: "
                  f"{reg['source']} (역할 파일은 {want}). 이름이 이미 등록돼 있으면 "
                  f"등록된 쪽이 이기므로 세션에 붙는 것은 "
                  f"{reg.get('installLocation', '?')} 다.", file=sys.stderr)
        return d
    print(f"[{role}] 룰북을 받는 중: {spec.get('repo')}", file=sys.stderr)
    warm = {"extraKnownMarketplaces": {spec["marketplace"]: {"source": rulebook_source(spec)}}}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(warm, f)
        warm_path = f.name
    try:
        # 두 번 돌린다. 한 번으로 받아지는 게 보통이지만 안 받아지고 끝나는 경우를
        # 실측했다(2026-07-26, 같은 마켓플레이스가 한 번은 되고 한 번은 안 됨).
        # 실패가 조용해서 다음 줄이 "룰북 없음"으로 멈춰 세우는 것 말고는 표시가 없다.
        for _ in range(2):
            subprocess.run(["claude", "-p", "--settings", warm_path],
                           input="ok", text=True, capture_output=True)
            d = rulebook_dir(spec)
            if d:
                return d
    finally:
        os.unlink(warm_path)
    sys.exit(
        f"[{role}] 룰북을 받지 못했다: {spec.get('repo') or spec.get('path')}\n"
        + _fetch_hint(spec))


def _fetch_hint(spec: dict) -> str:
    """왜 못 받았는지 muster 가 실제로 알 수 있는 원인부터 말한다.

    같은 이름이 사용자 전역 `~/.claude/settings.json` 의 extraKnownMarketplaces 에
    이미 선언돼 있으면 **그쪽이 `--settings` 를 이긴다.** 그 선언이 망가져 있으면
    (실측: `source: github` 인데 `path` 가 같이 들어 있던 항목) 클론은 몇 번을
    돌려도 생기지 않고, 세션은 매번 정상 종료한다. 자격증명 문제로 오진하면
    영영 못 찾는다 — 실제로 그렇게 한 시간을 썼다.
    """
    name = spec["marketplace"]
    try:
        declared = json.loads(USER_SETTINGS.read_text()).get("extraKnownMarketplaces", {})
    except (OSError, ValueError):
        declared = {}
    if name in declared:
        return (f"  전역 설정이 같은 이름을 이미 선언하고 있고, 그쪽이 이긴다:\n"
                f"    {USER_SETTINGS} → extraKnownMarketplaces.{name}\n"
                f"    {json.dumps(declared[name], ensure_ascii=False)}\n"
                f"  이 항목을 지우거나 고친 뒤 다시 시도한다.")
    return "  비공개 레포면 git 자격증명이 필요하다. `gh auth status` 로 확인한다."


def role_settings(role: str) -> dict:
    """역할 설정 + 룰북 플러그인 펼침 + 전역 플러그인 차단을 합친 것."""
    f = ROOT / "roles" / f"{role}.json"
    if not f.exists():
        have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
        sys.exit(f"모르는 역할: {role}  (있는 것: {have})")
    spec = json.loads(f.read_text())

    # 룰북의 marketplace.json 을 읽어 플러그인을 **하나씩** 켠다.
    #
    # `<role>-agent-env` 번들만 켜는 방식은 안 된다 — 번들의 dependencies 는
    # `--settings` 의 enabledPlugins 로는 해결되지 않는다(A/B 실측: 번들만 켠 세션은
    # doctrine 의 SessionStart 훅이 안 돌아 docs/ 버킷이 안 생겼고, 개별로 켠 세션은
    # 생겼다). 번들이 켜졌다는 사실만 보고 넘어가면 룰북 0개로 도는 세션을
    # "성공"으로 착각한다.
    #
    # 목록을 손으로 적지 않고 마켓플레이스에서 읽는 이유는 룰북에 플러그인이
    # 추가돼도 여기를 안 고치기 위해서다. env 번들 자체는 내용이 없으므로 제외한다.
    names = [p["name"] for p in json.loads(_mkt(ensure_rulebook(role, spec)).read_text())["plugins"]
             if not p["name"].endswith("-agent-env")]

    s = {k: v for k, v in spec.items() if k not in ("marketplace", "path", "repo")}

    # 역할 파일의 env 는 **기본값**이지 강제가 아니다. 이미 환경에 있으면 그쪽이 이긴다 —
    # 안 그러면 bench 처럼 격리된 워크스페이스를 넘기려는 호출이 조용히 무시되고,
    # 실행이 실제 워크스페이스에 쓰게 된다(실제로 그렇게 오염시켰다).
    for k in list(s.get("env", {})):
        if k in os.environ:
            s["env"][k] = os.environ[k]

    # 샌드박스 경로는 그 env 를 **참조**해야 한다. 같은 값을 두 곳에 적으면 위의
    # 덮어쓰기가 조용히 무력화된다 — env 는 격리된 경로를 가리키는데 경계는 원래
    # 경로만 허용하는 상태가 되고, 그건 "격리했다고 믿는 오염"이다.
    # 해석된 env 를 기준으로 펼친다: 역할 파일이 선언했지만 os.environ 에 없는
    # 값도 있고, 환경이 이긴 값도 여기 이미 반영돼 있다.
    resolved = {**os.environ, **s.get("env", {})}
    fs = s.get("sandbox", {}).get("filesystem", {})
    for key in ("allowWrite", "denyWrite", "denyRead"):
        if key in fs:
            fs[key] = [string.Template(p).safe_substitute(resolved) for p in fs[key]]
            unresolved = [p for p in fs[key] if "$" in p]
            if unresolved:
                # 안 풀린 변수를 그대로 넘기면 경계가 존재하지 않는 경로를 가리킨다.
                sys.exit(f"[{role}] sandbox.filesystem.{key} 의 변수를 풀 수 없다: "
                         f"{', '.join(unresolved)}")

    s["extraKnownMarketplaces"] = {
        spec["marketplace"]: {"source": rulebook_source(spec)}}
    s["enabledPlugins"] = {f"{n}@{spec['marketplace']}": True for n in names}

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


def _plugin_names(spec: dict) -> list[str]:
    d = rulebook_dir(spec)
    if d is None:
        return []
    return [f"{p['name']}@{spec['marketplace']}"
            for p in json.loads(_mkt(d).read_text())["plugins"]
            if not p["name"].endswith("-agent-env")]


def _installed_sha(plugin: str) -> str:
    try:
        e = json.loads((Path.home() / ".claude/plugins/installed_plugins.json")
                       .read_text())["plugins"][plugin]
        return e[0].get("gitCommitSha", "")[:7]
    except (OSError, ValueError, KeyError, IndexError):
        return ""


def update(roles: list[str]) -> int:
    """룰북을 지금 원격에 있는 것으로 갱신한다.

    **지우고 다시 까는 것 말고는 길이 없다.** `claude plugin update` 는
    plugin.json 의 `version` **문자열**만 보는데 룰북 아홉 개가 전부 0.1.0 에
    머물러 있어서, 커밋이 몇 개 앞서 있든 "이미 최신"이라고 답한다. 마켓플레이스
    클론을 갱신해도 설치본은 그대로다 — 그 둘은 다른 자리다(실측 2026-07-27:
    클론 2018d54 / 설치본 7107a49, 방금 머지한 게이트 수정이 세션에 안 붙었다).
    """
    rc = 0
    for role in roles:
        spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())
        # 역할 파일에 로컬 path 가 있어도 클론을 갱신한다. 설치는 등록부가 가리키는
        # 자리에서 이뤄지고, 등록부가 github 이면 로컬 체크아웃을 아무리 당겨도
        # 설치본은 안 움직인다 — 그러면 "안 움직였다" 의 원인을 local scope 로
        # 잘못 지목하게 된다(실측 2026-07-27).
        subprocess.run(["claude", "plugin", "marketplace", "update", spec["marketplace"]],
                       capture_output=True, text=True)
        names = _plugin_names(spec)
        if not names:
            print(f"[{role}] 룰북이 없다 — 먼저 한 번 띄워서 받는다", file=sys.stderr)
            rc = 1
            continue
        before = {n: _installed_sha(n) for n in names}
        head = subprocess.run(["git", "-C", str(rulebook_dir(spec)), "rev-parse", "--short=7", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        for n in names:
            subprocess.run(["claude", "plugin", "uninstall", n], capture_output=True, text=True)
            subprocess.run(["claude", "plugin", "install", n], capture_output=True, text=True)
            # `install` 은 전역 settings.json 의 enabledPlugins 에 그 플러그인을
            # **켠 채로** 남긴다. 그대로 두면 사용자가 여는 보통 세션마다 룰북
            # 아홉 개가 한꺼번에 붙는다 — muster 가 막으려는 그 오염을 muster 가
            # 만드는 꼴이다(실측 2026-07-27: 갱신 한 번에 22개가 전역에 켜졌다).
            # 필요한 것은 **설치**지 활성화가 아니다. 켜는 일은 역할 세션의
            # `--settings` 가 한다.
            subprocess.run(["claude", "plugin", "disable", n, "--scope", "user"],
                           capture_output=True, text=True)
        for n in names:
            after = _installed_sha(n)
            if not after:
                print(f"[{role}] {n}: 설치 실패", file=sys.stderr)
                rc = 1
            elif after != before[n]:
                print(f"[{role}] {n}: {before[n] or '없음'} -> {after}")
            elif head and not (head.startswith(after) or after.startswith(head)):
                # 지웠다 깔았는데 안 움직였다. 대개 그 플러그인을 물고 있는 번들이
                # **local scope** 로 깔려 있어서다 — user scope 의 uninstall 은
                # 성공했다고 답하고 항목은 그대로 남는다(실측 2026-07-27).
                # "그대로"로 넘기면 고친 룰북을 못 쓰는 채로 다 됐다고 믿게 된다.
                print(f"[{role}] {n}: {after} 에서 **안 움직였다** (클론은 {head}). "
                      f"local scope 설치가 물고 있을 수 있다: "
                      f"claude plugin uninstall <번들> --scope local", file=sys.stderr)
                rc = 1
            else:
                print(f"[{role}] {n}: {after} (그대로)")
    return rc


def rulebook_version(role: str) -> str:
    """역할이 **실제로 물고 도는** 룰북의 커밋. 못 읽으면 그렇다고 말한다.

    클론이 아니라 **설치본**을 본다. 세션은 `~/.claude/plugins/cache/` 의 설치본을
    읽고, 마켓플레이스 클론을 갱신해도 그쪽은 안 따라온다. 클론의 sha 를 보고하면
    고쳐진 줄 알고 안 고쳐진 것을 돌린다 — 이 함수가 막으려던 바로 그 착각이다.

    로컬 체크아웃이든 github 클론이든 ref 나 sha 로 고정되지 않는다 — **그 순간
    거기 있는 것이 그대로 돈다.** 다른 브랜치든, 몇 커밋 뒤처졌든, 커밋 안 한 수정이
    있든. 플러그인 레지스트리도 `lastUpdated` 타임스탬프만 남기고 커밋은 안 남기며,
    github 클론은 자동 갱신되지도 않는다(실측: 클론 5faa9a7 / 로컬 6c6e358).

    핀을 박을 수는 없으니 **무엇이 돌았는지 기록한다.** 이게 없으면 ablation 이
    "룰북 켜고 끄고"를 쟀다고 하면서 어느 룰북인지 말하지 못한다. 실제로 로컬이
    8커밋 뒤처진 채로 반대 결론을 낸 적이 있다(2026-07-26).
    """
    spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())
    d = rulebook_dir(spec)
    if d is None:
        return "버전 불명 (룰북이 아직 없다)"
    def git(*a: str) -> str:
        p = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else ""
    sha = git("rev-parse", "--short", "HEAD")
    if not sha:
        return "버전 불명 (git 레포가 아니다)"
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "?"
    dirty = "+커밋안됨" if git("status", "--porcelain") else ""

    # 도는 것은 설치본이다. 클론과 갈리면 **클론이 아니라 설치본**을 앞세운다.
    live = {s for s in (_installed_sha(n) for n in _plugin_names(spec)) if s}
    if not live:
        return f"{sha}{dirty} ({branch}) — 설치본 없음"
    if len(live) > 1:
        return f"설치본이 서로 다르다: {', '.join(sorted(live))} / 클론 {sha} ({branch})"
    installed = live.pop()
    if not sha.startswith(installed) and not installed.startswith(sha):
        return (f"{installed} (도는 것) ≠ {sha}{dirty} ({branch}, 클론) "
                f"— `spawn.py update {role}` 로 맞춘다")
    return f"{installed}{dirty} ({branch})"


def _installed() -> set[str]:
    """실제로 **디스크에 있는** 플러그인. 이름만 등록된 것은 세지 않는다.

    세션은 마켓플레이스 클론이 아니라 `~/.claude/plugins/cache/<마켓>/<플러그인>/
    <버전>/` 에서 플러그인을 읽는다. `installed_plugins.json` 은 그 installPath 를
    적어 두는데, **디렉터리가 사라져도 항목은 남는다.** 실측 2026-07-26: 역할 9개
    중 6개가 등록만 있고 캐시가 없었다.

    이름만 세면 ensure_installed 가 "이미 설치됨"으로 통과시키고, 세션은 룰북
    0개로 조용히 돈다 — muster 는 "플러그인 1개"라고 출력하고, 에이전트는 룰북
    없이 그럴듯한 답을 내놓는다. 이 함수가 막으려던 실패가 한 겹 아래에서 그대로
    일어난다. 그래서 기록이 아니라 **산출물**을 확인한다.
    """
    try:
        d = json.loads(
            (Path.home() / ".claude/plugins/installed_plugins.json").read_text())["plugins"]
    except (OSError, ValueError, KeyError):
        return set()
    return {name for name, entries in d.items()
            if isinstance(entries, list)
            and any(Path(e.get("installPath", "")).is_dir()
                    for e in entries if isinstance(e, dict))}


def ensure_installed(role: str, want: list[str], settings: str) -> None:
    """역할의 룰북이 실제로 설치되게 만든다. 안 되면 멈춘다.

    첫 스폰은 마켓플레이스를 **등록만** 하고 플러그인은 다음 실행부터 붙는다(실측).
    그 사이 세션은 룰북 0개로 조용히 돌아간다 — 겉보기엔 성공이라 ablation 결과를
    통째로 오염시킨다.

    그래서 미설치면 **워밍업 실행 한 번**으로 등록시키고 다시 확인한다. 확인만 하고
    멈추면 등록할 기회가 영영 없어 교착이다(실제로 그렇게 만들었다가 재현했다).
    워밍업 뒤에도 없으면 그때는 진짜로 멈춘다 — 룰북 없이 도는 것보다 낫다.
    """
    missing = [p for p in want if p not in _installed()]
    if not missing:
        return
    print(f"[{role}] 룰북 설치 중: {', '.join(missing)}", file=sys.stderr)
    # 처음 보는 마켓플레이스는 **두 번** 걸린다 — 1회차가 등록하고 2회차가 설치한다
    # (실측). 한 번만 돌리고 포기하면 사용자가 같은 명령을 두 번 쳐야 한다.
    for _ in range(2):
        subprocess.run(["claude", "-p", "--settings", settings],
                       input="ok", text=True, capture_output=True)
        missing = [p for p in want if p not in _installed()]
        if not missing:
            return
    sys.exit(
        f"[{role}] 룰북을 설치하지 못했다: {', '.join(missing)}\n"
        f"  이대로 띄우면 룰북 0개로 돈다.\n" + _install_hint(missing))


def _install_hint(missing: list[str]) -> str:
    """설치가 왜 안 됐는지 muster 가 실제로 알 수 있는 원인부터 말한다.

    `installed_plugins.json` 에 항목이 남아 있으면 이미 설치된 것으로 보고
    **재설치를 건너뛴다.** 캐시 디렉터리가 사라져도 항목은 남으므로, 그 상태는
    스스로 풀리지 않는다 — 몇 번을 돌려도 설치되지 않고, 항목이 있으니 아무도
    이상하다고 말하지 않는다. 실측 2026-07-26: 유령 항목 6개를 지우자 같은
    호출이 그대로 성공했다.
    """
    reg = Path.home() / ".claude/plugins/installed_plugins.json"
    try:
        entries = json.loads(reg.read_text())["plugins"]
    except (OSError, ValueError, KeyError):
        entries = {}
    ghosts = [m for m in missing if m in entries]
    if ghosts:
        return (f"  등록부에는 이 항목들이 **설치된 것으로 남아 있다.** 그래서 재설치를\n"
                f"  건너뛰고, 캐시가 없으니 세션에는 아무것도 안 붙는다:\n"
                + "".join(f"    {g}\n" for g in ghosts)
                + f"  {reg} 에서 그 항목을 지운 뒤 다시 시도한다.")
    return "  `claude` 세션에서 /plugin 으로 설치한 뒤 다시 시도한다."


# 계약 §3 의 WAKES-ON 표 순서. 보드를 읽을 때 이 순서로 보여준다.
ROLES = ("product", "ux-design", "feasibility", "coding", "qa",
         "review", "verify", "reflect", "ops")
BOARD = "docs/reports/records"          # 계약 v2 §10. 전부 대상 레포 안에 있다
CONTRACT = "docs/specs/role-handoff-contract.md"   # 레포-로컬 계약. 룰북 게이트가 찾는 자리
# 계약 v1 이 쓰던 자리. 아직 v2 로 안 옮긴 레포를 **말해주기 위해서만** 본다
LEGACY = {"review": "review-record.md", "feasibility": "feasibility-record.md",
          "ops": "state.md", "product": "product-record.md"}


def slug(cwd: str) -> str:
    """레포 디렉터리 이름 (계약 v2 §9).

    v1 은 origin 리모트에서 <owner>-<repo> 를 뽑았는데, 그건 폐지된
    `$QA_WORKSPACE` 의 레포 간 경로 때문에만 있던 것이다. 리모트 없는 레포에서
    깨지지 않는 것이 §9 가 이 규칙을 고른 이유다.
    """
    return Path(cwd).resolve().name


CANONICAL = ROOT / "contract" / "role-handoff-contract.md"


def _digest(p: Path) -> str:
    import hashlib
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except OSError:
        return ""


def contract_drift(cwd: str) -> str | None:
    """대상 레포의 계약이 정본과 다르면 그 사실을 돌려준다.

    계약은 authority 문서인데 frontmatter 가 `status: final` 뿐이고 **버전이 없다.**
    그래서 두 판이 나란히 `final` 을 선언하면서 188줄 다를 수 있었고, 실제로 그랬다
    (2026-07-26: 345줄판 3개 / 533줄판 3개). 버전이 없으면 내용 해시가 유일하게
    남는 판별 수단이다 — 문서를 고치지 않고도 갈라짐을 볼 수 있다.
    """
    theirs = _digest(Path(cwd).resolve() / CONTRACT)
    ours = _digest(CANONICAL)
    if not theirs or not ours or theirs == ours:
        return None
    return f"{theirs} (정본 {ours})"


def init_contract(cwd: str) -> int:
    """대상 레포에 정본 계약을 심는다. **muster 가 남의 레포에 쓰는 유일한 경우다.**

    보드 기록은 절대 쓰지 않는다(protocol.md §1) — 그건 역할의 것이고, 밖에서
    고치면 전이 게이트를 우회한다. 계약 파일은 상태가 아니라 **전제조건**이고,
    없으면 역할이 조용히 계약 밖에서 도는 것이 실측으로 확인됐다.
    """
    root = Path(cwd).resolve()
    dest = root / CONTRACT
    if dest.exists():
        drift = contract_drift(cwd)
        if drift is None:
            print(f"이미 정본과 같다: {dest}")
            return 0
        print(f"이미 계약이 있는데 정본과 다르다: {drift}\n"
              f"  {dest}\n"
              f"  덮어쓰지 않는다 — 그 레포가 의도적으로 다른 판을 쓰는 중일 수 있다.",
              file=sys.stderr)
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(CANONICAL.read_bytes())
    print(f"계약을 심었다: {dest}  ({_digest(dest)})")
    return 0


def require_contract(cwd: str, override: bool) -> None:
    """대상 레포에 레포-로컬 계약이 있는지 본다. 없으면 멈춘다.

    실측 A/B (2026-07-26, 같은 프롬프트·같은 역할, 표적만 다름):

      계약 없음  → product 가 `status: hypothesis-registered` 만 쓴다. 계약 §1 의
                   공통 헤더(kind/subject/produced_by/upstream/loop_state)가
                   **하나도 없어서** 보드에 아무것도 안 올라가고 다음 역할이
                   영영 안 깨어난다.
      계약 있음  → 프롬프트가 계약을 언급하지 않아도 전부 갖춰 쓴다. 감시자가
                   다음 역할을 지목한다.

    가르는 변수는 **파일 하나**다. 그리고 없을 때의 실패가 조용하다 — 세션은
    종료 0 이고 산출물도 그럴듯해서, 파이프라인이 시작조차 안 했다는 것을
    아무것도 말해주지 않는다. 한 세션을 통째로 버리는 값이다.

    그래서 경고가 아니라 정지다. 계약을 안 쓰는 레포(그냥 코드만 짜게 하는
    경우)는 --no-contract 로 **명시적으로** 빠져나간다 — 사고가 아니라 결정이 되게.
    """
    if override:
        return
    root = Path(cwd).resolve()
    if (root / CONTRACT).is_file():
        return
    sys.exit(
        f"대상 레포에 {CONTRACT} 가 없다: {root}\n"
        f"  이대로 띄우면 역할이 계약 v2 헤더 없이 기록을 쓴다. 보드에 아무것도\n"
        f"  올라가지 않고 다음 역할이 안 깨어나는데, 세션은 성공으로 끝난다(실측).\n"
        f"  `python3 spawn.py init -C {cwd}` 로 정본을 심거나,\n"
        f"  보드를 안 쓸 작업이면 --no-contract 로 명시한다.")


def frontmatter(p: Path) -> dict[str, str]:
    """맨 앞 `---` 블록만 얕게 읽는다. 값의 트레일링 주석은 떼어낸다 —
    계약 §2: 주석을 허용하지 않는 파서는 **게이트 결함이지 기록의 위반이 아니다**."""
    try:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    body = text.split("---", 2)
    if len(body) < 3:
        return {}
    out = {}
    for line in body[1].splitlines():
        k, sep, v = line.partition(":")
        if sep and k.strip() and not k.startswith((" ", "-", "\t")):
            out[k.strip()] = v.split("#")[0].strip()
    return out


def board(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    """블랙보드를 읽는다: subject → 역할 → frontmatter (계약 v2 §10)."""
    recs = root / BOARD
    if not recs.is_dir():
        return {}
    found = {}
    for d in sorted(p for p in recs.iterdir() if p.is_dir()):
        roles = {r: frontmatter(d / f"{r}.md") for r in ROLES if (d / f"{r}.md").is_file()}
        if roles:
            found[d.name] = roles
    return found


def status(cwd: str) -> list[str]:
    """보드를 **읽는다**. 쓰지 않는다 (protocol.md §1).

    상태는 에이전트의 것이다. muster 가 이걸 고치기 시작하면 룰북의 전이 게이트를
    우회하게 된다 — 게이트는 기록 쓰기를 가로채 막지만, 그 파일을 밖에서 고치면
    문지기를 안 거친다.
    """
    root = Path(cwd).resolve()
    out = [f"프로젝트: {slug(cwd)}   경로: {root}"]

    if not (root / CONTRACT).is_file():
        out.append(f"⚠ {CONTRACT} 없음 — 역할이 계약 헤더 없이 기록을 쓴다(실측). "
                   f"`spawn.py init` 으로 심는다.")
    elif (drift := contract_drift(cwd)):
        # 계약에 버전 필드가 없어서 해시가 유일한 판별 수단이다.
        out.append(f"⚠ 이 레포의 계약이 정본과 다르다: {drift}")
    b = board(root)
    if b:
        for subject, roles in b.items():
            out.append(f"subject: {subject}")
            for r in ROLES:
                fm = roles.get(r)
                if fm is None:
                    continue
                bits = [f"loop_state: {fm.get('loop_state', '(없음)')}"]
                if fm.get("verdict"):          # feasibility. coding 이 여기 깨어난다(§3)
                    bits.append(f"verdict: {fm['verdict']}")
                out.append(f"  [{r}] " + "   ".join(bits))
            missing = [r for r in ROLES if r not in roles]
            if missing:
                out.append(f"  (기록 없음: {', '.join(missing)})")
        return out

    # 보드가 없다. "아무 일도 없다"와 "옛 자리에 있다"는 정반대 처분을 받아야 한다.
    stale = sorted(r for r, name in LEGACY.items()
                   if (root / name).exists() or (root / "docs" / name).exists())
    if stale:
        out.append(f"보드 없음. 계약 v1 자리에 기록이 있다: {', '.join(stale)}")
        out.append(f"  이 레포는 아직 계약 v2 로 안 옮겨졌다. v2 는 {BOARD}/<subject>/<역할>.md 다.")
    else:
        out.append(f"보드 없음 ({BOARD}/). 아직 아무 역할도 기록을 쓰지 않았다.")
    return out


def _base(cwd: str) -> str:
    """비교 기준 ref. origin/HEAD 가 가리키는 기본 브랜치를 우선 쓴다."""
    p = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                       capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.strip():
        return p.stdout.strip()
    for cand in ("origin/main", "origin/master"):
        if subprocess.run(["git", "-C", cwd, "rev-parse", "--verify", "-q", cand],
                          capture_output=True).returncode == 0:
            return cand
    return "origin/main"          # 없으면 그대로 실패시켜 "검사 불가"로 보고한다


def gate_report(cwd: str) -> list[str]:
    """세션이 무엇을 건드렸는지 결정론적으로 본다. LLM 0회.

    **막지는 않는다.** 세션이 끝난 뒤라 되돌릴 수 없고, muster 는 판정하지 않는다.
    대신 조용히 넘어가지도 않는다 — 보호 경로(인증·시크릿·마이그레이션·CI 설정)를
    건드렸거나 실재하지 않는 패키지를 넣었으면 사람이 알아야 한다.

    게이트가 못 돌아도 그것을 "이상 없음"으로 말하지 않는다. 검사 불가와 통과는
    정반대 처분을 받아야 한다는 게 게이트의 원칙이고, 보고에도 같이 적용된다.
    """
    sys.path.insert(0, str(ROOT / "gates"))
    try:
        import ci, gates
        # 비교 기준을 레포에서 찾는다. origin/main 을 고정하면 기본 브랜치가
        # master·develop 인 레포에서 매번 "검사 불가"가 뜨고, 그러면 게이트가
        # 있으나 마나가 된다.
        gates.BASE = os.environ.get("GATE_BASE") or _base(cwd)
        bad = ci.check(Path(cwd).resolve())
    except Exception as e:                       # git 아님, base 부재, import 실패 등
        return [f"[게이트] 검사 불가 — {type(e).__name__}: {str(e)[:120]}"]
    return ["[게이트] 이상 없음"] if not bad else \
           ["[게이트] 확인 필요:"] + [f"  - {b}" for b in bad]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", nargs="?", help="역할. 생략하면 상태만 보여준다")
    ap.add_argument("task", nargs="?", help="맡길 일. 룰북 커맨드면 '/plugin:command 인자'")
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
    ap.add_argument("--dry-run", action="store_true", help="합쳐진 설정만 보고 안 띄운다")
    ap.add_argument("--no-contract", action="store_true",
                    help="대상 레포에 계약이 없어도 띄운다. 보드를 안 쓸 작업에만")
    a = ap.parse_args()

    if a.role == "init":
        # 계약을 심는다. muster 가 남의 레포에 쓰는 유일한 경우.
        return init_contract(a.cwd)
    if a.role == "update":
        # 룰북을 원격 최신으로. 인자를 비우면 전부.
        return update([a.task] if a.task else list(ROLES))
    if a.role == "wake":
        # 계약 §3 의 표를 기계로 평가하고, **누구를 열지**를 말한다.
        # 띄우지 않는다 — 무엇을 맡길지는 그 줄을 만족시킨 사건이 정하지 않는다.
        import wakes
        print("\n".join(status(a.cwd)))
        print()
        print("\n".join(wakes.report(a.cwd)))
        return 0
    if not a.role:
        print("\n".join(status(a.cwd)))
        print("\n역할: " + ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json"))))
        print("보드가 누구를 깨우는지: spawn.py wake")
        return 0
    if not a.task:
        sys.exit("맡길 일이 없다. 사용법: spawn.py <역할> \"<맡길 일>\" [-C <경로>]")

    # --dry-run 은 세션을 안 태운다. 계약 검사는 버려질 세션을 막으려는 것이므로
    # 아무것도 안 띄우는 호출까지 막을 이유가 없다.
    require_contract(a.cwd, a.no_contract or a.dry_run)
    s = role_settings(a.role)
    on = [k for k, v in s.get("enabledPlugins", {}).items() if v]
    if a.dry_run:
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return 0

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(s, f)
        settings = f.name
    try:
        # 설정 파일이 있어야 워밍업이 그 마켓플레이스를 등록할 수 있다.
        ensure_installed(a.role, on, settings)
        print(f"[{a.role}] 플러그인 {len(on)}개, 룰북 {rulebook_version(a.role)}, "
              f"작업 디렉터리 {a.cwd}", file=sys.stderr)
        # 맡길 일은 stdin 으로 넘긴다. 인자로 주면 가변 인자 플래그가 삼키고,
        # 셸 보간을 거치면 신뢰할 수 없는 값의 $(…) 가 실행된다.
        rc = subprocess.run(
            ["claude", "-p", "--settings", settings],
            cwd=a.cwd, input=a.task, text=True,
            env={**os.environ, "CLAUDE_ROLE": a.role},
        ).returncode
    finally:
        os.unlink(settings)

    for line in gate_report(a.cwd):
        print(line, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
