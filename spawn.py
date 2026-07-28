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
from __future__ import annotations
import argparse
import re
import hashlib
import json
import os
import string
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER_SETTINGS = Path.home() / ".claude" / "settings.json"


MARKETPLACES = Path.home() / ".claude" / "plugins" / "marketplaces"
KNOWN = MARKETPLACES.parent / "known_marketplaces.json"


def _mkt(d: Path) -> Path:
    return d / ".claude-plugin" / "marketplace.json"


def _path(spec: dict) -> str:
    """역할 파일의 `path` 를 푼다. `~` 와 `$VAR` 를 편다. 못 풀면 빈 문자열.

    절대경로를 그대로 적으면 그 레포는 **한 사람의 홈 디렉터리를 담은 채로**
    공개된다. 그리고 남의 기계에는 그 경로가 없으니 조용히 github 로 떨어지는데,
    왜 로컬 체크아웃이 안 잡히는지는 아무 데도 안 나온다.

    안 풀린 변수를 남기지 않고 빈 문자열로 돌려주는 것이 중요하다 —
    `$TOKENMAXXXER_RULEBOOKS/...` 같은 문자열이 그대로 경로로 쓰이면 없는
    디렉터리를 가리키고, 그건 "설정 안 함"이 아니라 "잘못 설정함"이 된다.
    """
    p = spec.get("path")
    if not p:
        return ""
    p = os.path.expanduser(os.path.expandvars(p))
    return "" if "$" in p else p


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
    p = _path(spec)
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
    p = _path(spec)
    if p and _mkt(Path(p)).exists():
        return Path(p)
    loc = registered(spec["marketplace"]).get("installLocation")
    if loc and _mkt(Path(loc)).exists():
        return Path(loc)
    clone = MARKETPLACES / spec["marketplace"]
    return clone if _mkt(clone).exists() else None


def rulebook_checkout(role: str, spec: dict) -> Path:
    """세션에 **실제로 붙일** 룰북 체크아웃. 로컬이 있으면 그것, 없으면
    muster 가 자기 밑에 클론해 둔다.

    설치를 거치지 않는다. 설치 경로에는 실측된 함정이 셋 있고 전부 조용하다:
    캐시와 클론이 갈라지고(`claude plugin update` 는 버전 문자열만 본다),
    캐시를 지워도 등록부에 유령 항목이 남고, 이름이 이미 등록돼 있으면
    `--settings` 의 extraKnownMarketplaces 가 무시된다. 셋 다 결과는 같다 —
    **의도한 것과 다른 커밋이 세션에 붙는데 아무도 모른다.** 실측
    2026-07-27: drive 가 띄운 qa 세션이 방금 고친 보안 결함이 그대로 있는
    e940cbe 로 돌았다(머지된 main 은 1195ace).

    muster 소유 클론이라 무엇이 돌았는지 sha 로 말할 수 있고, 나중에 특정
    sha 로 고정하는 것도 여기서만 하면 된다.
    """
    p = _path(spec)
    if p and _mkt(Path(p)).exists():
        return Path(p)

    repo = spec.get("repo")
    if not repo:
        sys.exit(f"[{role}] 로컬 체크아웃도 repo 도 없다: roles/{role}.json")
    d = ROOT / "runs" / "rulebooks" / spec["marketplace"]
    if _mkt(d).exists():
        subprocess.run(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                       capture_output=True)
        return d
    d.parent.mkdir(parents=True, exist_ok=True)
    print(f"[{role}] 룰북을 받는 중: {repo}", file=sys.stderr)
    r = subprocess.run(["git", "clone", "-q", f"https://github.com/{repo}.git", str(d)],
                       capture_output=True, text=True)
    if not _mkt(d).exists():
        sys.exit(f"[{role}] 룰북을 받지 못했다: {repo}\n  {r.stderr.strip()[:200]}")
    return d


def checkout_version(role: str, spec: dict) -> str:
    """세션에 붙는 체크아웃이 **실제로 무엇인지**. 설치본이 없으니 갈라질 것도
    없다 — 이 문자열이 그 run 이 잰 룰북이다."""
    d = rulebook_checkout(role, spec)

    def git(*a: str) -> str:
        p = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else ""

    sha = git("rev-parse", "--short", "HEAD") or "?"
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    dirty = " (커밋 안 된 변경 있음)" if git("status", "--porcelain") else ""
    where = "로컬" if _path(spec) and _mkt(Path(_path(spec))).exists() else "muster 클론"
    return f"{sha} ({branch}, {where}){dirty}"


def plugin_dirs(role: str, spec: dict) -> list[Path]:
    """세션에 붙일 플러그인 디렉터리들.

    `<role>-agent-env` 번들은 뺀다 — 번들의 dependencies 는 이 경로로도
    해결되지 않고, 번들 자체에는 내용이 없다. 개별로 붙이는 이유가 그거다
    (A/B 실측: 번들만 켠 세션은 doctrine 의 SessionStart 훅이 안 돌았다).
    """
    d = rulebook_checkout(role, spec)
    out = []
    for p in json.loads(_mkt(d).read_text())["plugins"]:
        if p["name"].endswith("-agent-env"):
            continue
        src = (p.get("source") or f"./{p['name']}")
        if not isinstance(src, str):
            continue                      # {source: github, ...} 같은 원격 지정
        sub = (d / src.lstrip("./")).resolve()
        if (sub / ".claude-plugin" / "plugin.json").is_file():
            out.append(sub)
        else:
            print(f"[{role}] 플러그인 디렉터리가 없다: {src} — 건너뛴다",
                  file=sys.stderr)
    if not out:
        sys.exit(f"[{role}] 붙일 플러그인이 없다: {_mkt(d)}")
    return out


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
    """역할의 샌드박스 경계 + 전역 플러그인 차단.

    **룰북을 켜는 일은 여기서 하지 않는다.** 그건 `--plugin-dir` 이 한다
    (plugin_dirs 참고). 설정으로 켜려면 마켓플레이스를 등록하고 설치해야
    하는데, 그 경로에는 조용한 함정이 셋 있고 전부 "의도한 것과 다른 커밋이
    붙는다"로 끝난다.

    남는 일은 두 가지다: 역할이 선언한 샌드박스를 펼치는 것, 그리고 사용자
    전역 플러그인을 빠짐없이 끄는 것. 후자는 `--settings` 가 교체가 아니라
    **병합**이라 필요하다 — 안 끄면 qa 룰북만 적은 세션에 전역 17개가 딸려
    온다.
    """
    f = ROOT / "roles" / f"{role}.json"
    if not f.exists():
        have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
        sys.exit(f"모르는 역할: {role}  (있는 것: {have})")
    spec = json.loads(f.read_text())

    s = {k: v for k, v in spec.items() if k not in ("marketplace", "path", "repo")}

    # 역할 파일의 env 는 **기본값**이지 강제가 아니다. 이미 환경에 있으면 그쪽이 이긴다 —
    # 안 그러면 bench 처럼 격리된 워크스페이스를 넘기려는 호출이 조용히 무시되고,
    # 실행이 실제 워크스페이스에 쓰게 된다(실제로 그렇게 오염시켰다).
    # 역할 파일이 기본값으로 적은 값 자체에도 `~` 와 `$VAR` 가 들어갈 수 있다 —
    # 절대경로를 박지 않으려면 그래야 한다. 여기서 먼저 펴지 않으면 아래의
    # safe_substitute 는 한 번만 도므로 `$QA_WORKSPACE` → `$HOME/...` 로 끝나고,
    # 안 풀린 `$` 때문에 역할이 아예 안 뜬다(실측 2026-07-27: qa 가 그랬다).
    for k in list(s.get("env", {})):
        if k in os.environ:
            s["env"][k] = os.environ[k]
        else:
            v = s["env"][k]
            if isinstance(v, str):
                s["env"][k] = os.path.expanduser(os.path.expandvars(v))

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

    # 전역 플러그인은 전부 끈다. 켜야 할 것을 적는 게 아니라 꺼야 할 것을
    # 빠짐없이 적는 쪽이라, 전역에 플러그인이 새로 깔려도 새지 않는다.
    s["enabledPlugins"] = {}
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
    if issue is not None:
        br = checkout_issue_branch(cwd, issue, role)
        task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
                f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n\n") + task
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


def ensure_installed(role: str, want: list[str], settings: str, cwd: str) -> None:
    # 스폰 경로에서는 더 이상 쓰지 않는다 — 세션은 `--plugin-dir` 로 체크아웃을
    # 직접 붙는다(plugin_dirs 참고). 마켓플레이스 설치를 여전히 쓰는 사람을
    # 위해 `update` 쪽에 남겨 둔다.
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
        # 워밍업도 대상 레포에서 돈다. cwd 를 안 넘기면 muster 자신의 디렉터리에서
        # 돌아 노출이 역할 세션과 달라진다 — 같은 경계로 재현되어야 실측이 뜻을 갖는다.
        subprocess.run(["claude", "-p", "--settings", settings], cwd=cwd,
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
BOARD = "docs"                          # v3: subject trees live at docs/issue-<n>/
MARKER = "docs/specs/approvers.md"      # 보드 opt-in + 승인자 allowlist (v3)
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


def init_board(cwd: str, login: str | None = None) -> int:
    """대상 레포를 보드로 선언한다: docs/specs/approvers.md 를 만든다.

    v3: 계약 심기는 폐지됐다 — 정본은 core 플러그인에만 있고, 레포 사본은
    해시 검사로 강제 동일해져 정보량이 0이었다. 보드 표식이자 승인자
    allowlist 인 approvers.md 만 있으면 된다. **사용자의 파일이다** —
    이미 있으면 절대 덮지 않는다.
    """
    root = Path(cwd).resolve()
    dest = root / MARKER
    if dest.exists():
        print(f"이미 있다: {dest}")
        return 0
    if not login:
        r = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                           capture_output=True, text=True)
        login = r.stdout.strip() if r.returncode == 0 else ""
    if not login:
        sys.exit("승인자 로그인을 모른다. gh auth login 을 하거나 "
                 "init --login <github-login> 으로 준다.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"- {login}\n", encoding="utf-8")
    print(f"보드로 선언했다: {dest}  (approver: {login})")
    return 0


def require_board(cwd: str, override: bool) -> None:
    """대상 레포가 보드인지(approvers.md 가 있는지) 본다. 없으면 멈춘다.

    core 의 게이트가 어차피 보드·실행 쓰기를 거부하므로, 세션을 태우기 전에
    같은 사실을 말해주는 것뿐이다 — 버려질 세션에 과금하지 않는다.
    """
    root = Path(cwd).resolve()
    if (root / MARKER).is_file():
        return
    if override:
        return
    sys.exit(
        f"대상 레포에 {MARKER} 가 없다: {root}\n"
        f"  이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:\n"
        f"    python3 spawn.py init -C {root}\n"
        f"  보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.")


REPO_CONFIG = (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks",
               ".claude/agents", ".mcp.json")


def require_no_repo_config(cwd: str, override: bool) -> None:
    """대상 레포가 자기 Claude 설정을 들고 있으면 멈춘다.

    **muster 의 샌드박스는 이걸 못 막는다.** 설정 우선순위는
    `--settings` > `<레포>/.claude/settings.json` > `~/.claude/settings.json` 인데,
    muster 는 양 끝만 읽고 가운데를 안 본다. 그리고 `hooks` 는 덮어쓰기가 아니라
    **더해지고**, 훅 명령은 선언한 `sandbox.filesystem` 정책을 받지 않는다.

    실측 2026-07-27. `denyWrite` 와 `denyRead` 를 선언한 역할 설정으로 띄웠는데,
    레포가 커밋해 둔 SessionStart 훅이 **denyWrite 경로에 쓰고 denyRead 인
    `~/.claude/settings.json` 을 읽어냈다.** 사용자 권한 그대로, 프롬프트 없이,
    `env={**os.environ}` 을 통째로 들고. 레포를 클론해서 muster 를 겨눈 것만으로
    성립한다.

    계약 파일과 같은 처분을 한다 — 경고가 아니라 정지, 그리고 명시적 opt-out.
    사고가 아니라 결정이 되게.
    """
    if override:
        return
    root = Path(cwd).resolve()
    rogue = [p for p in REPO_CONFIG if (root / p).exists()]
    if not rogue:
        return
    sys.exit(
        f"대상 레포가 자기 Claude 설정을 들고 있다: {', '.join(rogue)}\n"
        f"  {root}\n"
        f"  그 훅들은 muster 가 선언한 샌드박스 경계를 **받지 않는다**. 띄우면\n"
        f"  denyRead 로 막은 경로까지 읽힌다(실측). 내용을 직접 읽어보고,\n"
        f"  믿을 수 있으면 --trust-repo-config 로 명시한다.")


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
    """Read the board: subject (issue-<n>) -> role -> frontmatter (v3 s10).

    A subject is a docs/issue-<n>/ tree; role records sit in its reports/.
    """
    docs = root / BOARD
    if not docs.is_dir():
        return {}
    found = {}
    for d in sorted(p for p in docs.iterdir()
                    if p.is_dir() and re.match(r"^issue-[0-9]+$", p.name)):
        rep = d / "reports"
        roles = {r: frontmatter(rep / f"{r}.md") for r in ROLES
                 if (rep / f"{r}.md").is_file()}
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

    if not (root / MARKER).is_file():
        out.append(f"⚠ {MARKER} 없음 — 보드 opt-in 이자 승인자 allowlist 다. "
                   f"`spawn.py init` 으로 만든다.")
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
        out.append("  이 레포는 v3 이전 판이다. v3 는 docs/issue-<n>/reports/<역할>.md 다.")
    else:
        out.append("보드 없음 (docs/issue-<n>/). 아직 아무 역할도 기록을 쓰지 않았다.")
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


def ownership_report(cwd: str, role: str, delta: list) -> list[str]:
    """이 세션이 **자기 것이 아닌** 보드 경로를 건드렸는지 사후로 본다.

    세션 안에서는 룰북과 core 의 게이트가 막는다. 이건 그 게이트가 어떤
    이유로든 안 돌았을 때 흔적이라도 남기려는 것이다 — 새 훅이 trap 을
    빠뜨려 fail-open 이 되거나, 룰북 하나가 아직 마이그레이션 안 됐거나.
    막지는 않는다(이미 쓴 뒤다). 대신 조용히 넘어가지도 않는다.
    """
    bad = []
    for p in delta:
        m = re.match(r"^docs/(issue-[0-9]+)/reports/(.+)$", p)
        if not m:
            continue
        rest = m.group(2)
        if rest == f"{role}.md" or rest.startswith(f"{role}/"):
            continue
        if role == "feasibility" and rest.startswith("spikes/"):
            continue
        if role == "ops" and rest.startswith("postmortems/"):
            continue
        bad.append(f"  - {p} (다른 역할의 기록)")
    if not bad:
        return []
    return [f"[소유권] {role} 이 자기 것이 아닌 보드 경로를 건드렸다 — "
            f"세션 안의 게이트가 안 돌았다는 뜻이다 (계약 §11):"] + bad


def board_snapshot(cwd: str) -> dict[str, str]:
    """보드 파일들의 내용 해시. 세션 전후를 비교해 §6 의 '바뀐 보드'를 잰다.

    git 이 아니라 파일 내용을 재는 이유: 세션이 커밋했든 안 했든 바뀐 것은
    바뀐 것이고, 계약 §6 의 단위는 커밋이 아니라 보드다.
    """
    base = Path(cwd).resolve()
    docs = base / BOARD
    if not docs.is_dir():
        return {}
    out: dict[str, str] = {}
    for d in sorted(docs.glob("issue-*")):
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(base))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def session_result(stdout: str) -> dict:
    """--output-format json 의 결과 오브젝트. 파싱 불가면 빈 dict — 모르는
    것을 성공으로 취급하지 않는다."""
    try:
        got = json.loads(stdout)
        return got if isinstance(got, dict) else {}
    except ValueError:
        return {}


def classify(rc: int, result: dict, delta: list, blocked: list) -> str:
    """세션 하나의 처분. 판정하지 않는다 — 이름만 붙인다 (보고 전용).

    순서가 곧 의미다. 보드가 움직였으면 일부가 막혔어도 그 run 은
    progressed 이고(거부 건수는 따로 찍힌다), 사람 게이트가 서 있으면 그게
    가장 행동 가능한 사실이다.

    refused 와 silent-failure 를 가르는 이유: 게이트가 막아서 아무것도 안
    바뀐 것은 **시스템이 작동한 것**이고, 아무것도 안 바뀌었는데 막힌 것도
    없는 것은 아무도 이유를 모르는 것이다. 실측 2026-07-27 — reflect 를
    띄웠더니 룰북 게이트가 §20 필수 섹션 없음을 이유로 쓰기를 거부했고,
    세션은 그 이유를 또렷이 말하고 끝났는데 분류는 '침묵-사망'이라고 했다.
    이 레포의 원칙("검사 불가와 이상 없음은 정반대 처분을 받아야 한다")이
    여기에도 그대로 적용된다.
    """
    if rc != 0 or result.get("is_error"):
        return "errored"
    if delta:
        return "progressed"
    if blocked:
        return "waiting-on-human"
    if result.get("permission_denials"):
        return "refused"
    return "silent-failure"


def ledger_write(entry: dict) -> Path:
    """runs/ledger.jsonl 에 한 줄. runs/ 는 gitignore 되어 있다 — 측정 데이터는
    소스가 아니다."""
    d = ROOT / "runs"
    d.mkdir(exist_ok=True)
    p = d / "ledger.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return p


def core_root() -> Path:
    """tokenmaxxxer-core 체크아웃 루트. 없으면 멈춘다.

    core 는 상호작용 프로토콜의 게이트(보드·승인·gh-guard)와 정본 계약을
    들고 있다. 없이 띄우면 역할은 그대로 돌지만 아무도 이탈을 막지 않는다 —
    조용히 보호가 사라지는 쪽이라 경고가 아니라 정지다.
    """
    for cand in (os.environ.get("TOKENMAXXXER_CORE"),
                 "$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core",
                 str(ROOT.parent / "tokenmaxxxer-core")):
        if not cand:
            continue
        p = Path(os.path.expanduser(os.path.expandvars(cand)))
        if "$" in str(p):
            continue
        if (p / "core" / ".claude-plugin" / "plugin.json").is_file():
            return p
    # 로컬 체크아웃이 없으면 룰북과 같은 길: muster 소유 클론을 받아 쓴다.
    # 로컬 우선은 개발용 오버라이드일 뿐이다.
    d = ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"
    if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
        subprocess.run(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                       capture_output=True)
        return d
    try:
        d.parent.mkdir(parents=True, exist_ok=True)
        print("[core] tokenmaxxxer-core 를 받는 중", file=sys.stderr)
        subprocess.run(["git", "clone", "-q",
                        "https://github.com/tokenmaxxxer/tokenmaxxxer-core.git",
                        str(d)], capture_output=True, text=True)
    except OSError:
        pass
    if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
        return d
    sys.exit(
        "tokenmaxxxer-core 를 찾지 못했고 받지도 못했다. 역할 세션은 core 없이\n"
        "  뜨지 않는다 — 프로토콜 게이트와 정본 계약이 거기 있다.\n"
        "  네트워크를 확인하거나 체크아웃을 두고 $TOKENMAXXXER_CORE 로 가리켜라.")


def core_plugin_dirs() -> list[Path]:
    """core 마켓플레이스의 네 플러그인 전부 — core, terse, freelunch, scout.

    마켓플레이스 설치가 아니라 `--plugin-dir` 로 붙인다(실측 2026-07-27,
    CLI 2.1.220: 디렉터리로 넘긴 플러그인의 훅이 headless 에서 그대로
    발화한다). 설치를 거치지 않으므로 캐시·클론 갈라짐도 유령 등록 항목도
    이 경로에는 없다.
    """
    root = core_root()
    return [root / n for n in ("core", "terse", "freelunch", "scout")
            if (root / n / ".claude-plugin" / "plugin.json").is_file()]


def drive(cwd: str, unattended: bool, limit: int = 12) -> int:
    """보드가 지목하는 역할을 한 번에 하나씩, 멈출 때까지 띄운다.

    감시자가 아니라 **직렬 루프**다. 동시에 둘을 띄우지 않는다 — 보드는 공유
    상태이고, 계약 §3 은 동시 깨움을 정상으로 보지만 muster 가 그걸 중재하지는
    않는다.

    멈추는 자리 넷, 전부 정상 종료다:
      - 기계로 판정되는 줄이 더 없다
      - 띄웠는데 보드가 안 바뀌었다 (§6 — 안 바뀐 보드는 아무도 안 깨운다)
      - 세션이 실패했다
      - limit 에 닿았다 (폭주 방지지 정책이 아니다)

    **자동으로 안 띄우는 것**은 wakes.py 가 이미 전부 열거하고 있다: JUDGEMENT
    두 줄(product·ops 의 내용 판단), §19 에 막힌 줄, HUMAN_ONLY 세 간선.
    여기서 다시 판정하지 않는다 — 판정하는 순간 계약이 사람에게 유보한 자리를
    기계가 가져간다.
    """
    import wakes
    for turn in range(1, limit + 1):
        new, _answered = wakes.fresh(cwd)
        if not new:
            print(f"[drive] 선 줄이 없다. {turn - 1}번 띄우고 멈춘다.", file=sys.stderr)
            return 0
        row = new[0]
        print(f"[drive] {turn}/{limit}  [{row.role}] {row.why}", file=sys.stderr)
        # 보드 요약을 같이 넘긴다 — 안 주면 세션이 탐색으로 보드를 다시
        # 발견하느라 토큰을 쓰고, 그 탐색이 매번 다르게 끝난다.
        m_issue = re.search(r"issue-([0-9]+)", row.key + " " + row.why)
        rc = _spawn_one(cwd, row.role,
                        f"보드가 너를 깨웠다: {row.why}\n\n"
                        f"지금 보드:\n" + "\n".join(status(cwd)) + "\n\n"
                        f"계약과 네 룰북이 요구하는 대로 네 기록을 쓴다.", unattended,
                        int(m_issue.group(1)) if m_issue else None)
        if rc != 0:
            print(f"[drive] {row.role} 이 실패했다 (rc={rc}). 멈춘다.", file=sys.stderr)
            return rc
        if wakes.observed(cwd).get(row.key) != row.sig:
            # consume 은 progressed 일 때만 찍힌다. 안 찍혔다는 것은 보드가 안
            # 바뀌었다는 뜻이고, §6 이 여기서 루프를 끝낸다.
            print(f"[drive] {row.role} 이 보드를 바꾸지 않았다 — §6 으로 멈춘다. "
                  f"위 처분이 사람이 볼 자리를 말해준다.", file=sys.stderr)
            return 0
    print(f"[drive] {limit}번 돌았다. 폭주 방지로 멈춘다 — 더 돌리려면 다시 부른다.",
          file=sys.stderr)
    return 0


def _claude_version() -> str:
    try:
        out = subprocess.run(["claude", "--version"], capture_output=True,
                             text=True, timeout=30)
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def require_doctor(version: str | None = None) -> None:
    """이 CLI 버전에서 훅이 headless 로 도는 것을 doctor 가 실측했는지 본다.

    룰북 집행 전체가 '플러그인 훅이 -p 세션에서 돈다'는 한 문장 위에 서
    있는데, 그 문장은 공식 문서에 없다 — 실측(2026-07-27, 2.1.220)뿐이다.
    CLI 는 자동 업데이트되므로, 버전이 바뀌면 게이트 전부가 소리 없이
    사라질 수 있다. 그래서 버전마다 한 번, 실측을 다시 요구한다.
    """
    v = version if version is not None else _claude_version()
    ok = ROOT / "runs" / "doctor-ok"
    if not v:
        sys.exit("claude --version 을 읽지 못했다. claude 가 PATH 에 있나?")
    if not ok.is_file() or ok.read_text().strip() != v:
        if version is not None:
            # 명시된 버전(테스트 포함)에는 프로브를 태우지 않는다 — 옛 계약
            # 그대로 정지한다.
            sys.exit(
                f"이 CLI({v})에서 훅이 headless 로 도는 것을 아직 실측하지 않았다.\n"
                f"먼저 돌려라: python3 spawn.py doctor   (실 세션 1회, 소액 과금)")
        # 미측정 버전이면 그 자리에서 잰다 — 사용자에게 명령 하나를 더
        # 요구할 이유가 없다. 프로브 세션 1회(하이쿠, 소액)가 돈다.
        print(f"[doctor] CLI {v} 는 아직 실측 전이다 — 훅 발화 프로브를 "
              f"먼저 돌린다 (실 세션 1회, 소액 과금)", file=sys.stderr)
        if doctor() != 0 or not (ok.is_file() and ok.read_text().strip() == v):
            sys.exit(
                f"이 CLI({v})에서 플러그인 훅이 headless 로 발화하지 않는다 — "
                f"게이트 전부가 조용히 사라지는 버전이라 스폰을 막는다.")


def doctor() -> int:
    """프로브 플러그인 하나로 실 세션을 띄워 UserPromptSubmit / PreToolUse 가
    실제로 발화하는지 잰다. 성공하면 runs/doctor-ok 에 CLI 버전을 적는다."""
    v = _claude_version()
    if not v:
        print("claude --version 실패", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        plug = Path(td) / "probe"
        (plug / ".claude-plugin").mkdir(parents=True)
        (plug / "hooks").mkdir()
        (plug / ".claude-plugin" / "plugin.json").write_text(json.dumps(
            {"name": "muster-probe", "version": "0.0.0",
             "description": "hook-firing canary"}))
        ups, pre = Path(td) / "ups", Path(td) / "pre"
        (plug / "hooks" / "hooks.json").write_text(json.dumps({"hooks": {
            "UserPromptSubmit": [{"hooks": [
                {"type": "command", "command": f"touch {ups}"}]}],
            "PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": f"touch {pre}"}]}],
        }}))
        work = Path(td) / "work"
        work.mkdir()
        subprocess.run(["git", "init", "-q", str(work)], check=False)
        # --model haiku: 프로브의 관심사는 훅 로딩이지 모델이 아니다. 싸게 간다.
        subprocess.run(
            ["claude", "-p", "--plugin-dir", str(plug), "--model", "haiku",
             "--max-turns", "2", "--output-format", "json"],
            cwd=work, input="Run this exact bash command and nothing else: echo ok",
            text=True, capture_output=True, timeout=180)
        fired_ups, fired_pre = ups.is_file(), pre.is_file()
    print(f"UserPromptSubmit: {'발화' if fired_ups else '침묵'} / "
          f"PreToolUse: {'발화' if fired_pre else '침묵'}  (CLI {v})")
    if fired_ups and fired_pre:
        d = ROOT / "runs"
        d.mkdir(exist_ok=True)
        (d / "doctor-ok").write_text(v)
        print("doctor-ok 기록. 이 버전에서 스폰이 열린다.")
        return 0
    print("훅이 headless 에서 발화하지 않는다 — 이 CLI 버전으로는 룰북 집행이 "
          "성립하지 않는다. 스폰은 계속 막힌다.", file=sys.stderr)
    return 1


def spawn_cmd(settings_path: str, role: str, unattended: bool,
              core_plugins: list | None = None,
              plugins: list | None = None) -> tuple[list[str], dict[str, str]]:
    """세션 argv 와 env **추가분**. 호출자가 os.environ 위에 얹는다.

    --permission-mode acceptEdits: 실측 2026-07-27 — 권한 설정 없는 headless 는
    Write 를 조용히 거부한다(permission_denials 에만 남는다). acceptEdits 는
    대답할 사람이 없는 프롬프트를 없앨 뿐이고, 거부는 계속 게이트의 몫이다 —
    PreToolUse exit 2 가 acceptEdits 아래서도 막는 것을 같은 날 실측했다.
    샌드박스 Bash 는 원래 자동 허용이고, 비샌드박스 재실행은 이미
    allowUnsandboxedCommands:false 가 막는다.

    TOKENMAXXXER_SPAWNED: 스폰된 세션의 프롬프트는 오케스트레이터가 쓴
    텍스트이지 사람 턴이 아니다. core 의 mint 훅이 이 도장을 보고 발행을
    거른다. UNATTENDED 와 별개다 — 그쪽은 "사람이 없다"는 사실이고, 겹쳐
    쓰면 attended 스폰이 깨진다.
    """
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "acceptEdits", "--output-format", "json"]
    # 룰북도 core 와 같은 길로 붙는다 — 디렉터리로 넘긴 플러그인의 훅은
    # headless 에서 그대로 발화하고(실측 2026-07-27, CLI 2.1.220), 설치를
    # 안 거치므로 캐시-클론 갈라짐도 유령 등록 항목도 이 경로엔 없다.
    for p in (plugins or []):
        cmd += ["--plugin-dir", str(p)]
    for p in (core_plugins or []):
        cmd += ["--plugin-dir", str(p)]
    env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
    # Two-account model (core README): role sessions act as the AGENT
    # account. MUSTER_AGENT_GH_TOKEN, if set, becomes the session's GH_TOKEN
    # so gh in the container/sandbox authenticates as the agent — never the
    # user. gh-guard denies the human's acts in role sessions regardless.
    agent_token = os.environ.get("MUSTER_AGENT_GH_TOKEN")
    if agent_token:
        env["GH_TOKEN"] = agent_token
    if unattended:
        env["TOKENMAXXXER_UNATTENDED"] = "1"
    return cmd, env


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", nargs="?", help="역할. 생략하면 상태만 보여준다")
    ap.add_argument("task", nargs="?", help="맡길 일. 룰북 커맨드면 '/plugin:command 인자'")
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
    ap.add_argument("--dry-run", action="store_true", help="합쳐진 설정만 보고 안 띄운다")
    ap.add_argument("--no-contract", action="store_true",
                    help="대상 레포에 계약이 없어도 띄운다. 보드를 안 쓸 작업에만")
    ap.add_argument("--trust-repo-config", action="store_true",
                    help="대상 레포의 .claude/ 설정·훅을 신뢰한다. 읽어본 뒤에만")
    ap.add_argument("--issue", type=int,
                    help="이 이슈 번호로 스폰한다: issue-<n>/<역할> 브랜치를 만들고 프롬프트에 명시")
    ap.add_argument("--unattended", action="store_true",
                    help="사람이 없는 실행. mint 는 안 되고, 휴먼 게이트는 선다")
    ap.add_argument("--all", action="store_true",
                    help="wake: 이미 답해진 줄까지 보여준다 (계약 §6 억제를 푼다)")
    ap.add_argument("--limit", type=int, default=12,
                    help="drive: 한 번에 띄울 최대 횟수 (기본 12, 폭주 방지)")
    ap.add_argument("--login", help="init: approvers.md 에 넣을 GitHub 로그인 (기본: gh api user)")
    a = ap.parse_args()

    if a.role == "init":
        # 보드로 선언한다(approvers.md). muster 가 남의 레포에 쓰는 유일한 경우.
        return init_board(a.cwd, a.login)
    if a.role == "update":
        # 룰북을 원격 최신으로. 인자를 비우면 전부.
        return update([a.task] if a.task else list(ROLES))
    if a.role == "doctor":
        # 훅 발화 실측. 버전마다 한 번 — 룰북 집행의 전제조건이다.
        return doctor()
    if a.role == "wake":
        # 계약 §3 의 표를 기계로 평가하고, **누구를 열지**를 말한다.
        # 띄우지 않는다 — 무엇을 맡길지는 그 줄을 만족시킨 사건이 정하지 않는다.
        import wakes
        print("\n".join(status(a.cwd)))
        print()
        print("\n".join(wakes.report(a.cwd, show_answered=a.all)))
        return 0
    if a.role == "approve":
        sys.exit("v3: 승인은 파일 발행이 아니라 GitHub 행위다 — 오케스트레이터가\n"
                 "  사용자와의 대화에서 gh pr review --approve / gh pr merge 로 중계한다.")
    if a.role == "drive":
        # 보드가 지목하는 역할을 하나씩, 멈출 때까지.
        require_board(a.cwd, a.no_contract)
        require_no_repo_config(a.cwd, a.trust_repo_config)
        require_doctor()
        return drive(a.cwd, a.unattended, a.limit)
    if not a.role:
        print("\n".join(status(a.cwd)))
        print("\n역할: " + ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json"))))
        print("보드가 누구를 깨우는지: spawn.py wake")
        return 0
    if not a.task:
        sys.exit("맡길 일이 없다. 사용법: spawn.py <역할> \"<맡길 일>\" [-C <경로>]")

    # --dry-run 은 세션을 안 태운다. 계약 검사는 버려질 세션을 막으려는 것이므로
    # 아무것도 안 띄우는 호출까지 막을 이유가 없다.
    require_board(a.cwd, a.no_contract or a.dry_run)
    # 드라이런도 막는다 — 레포가 자기 훅을 들고 있으면 그건 세션을 띄우기
    # 전에 알아야 할 사실이지, 띄우고 나서 알 일이 아니다.
    require_no_repo_config(a.cwd, a.trust_repo_config)
    if a.dry_run:
        print(json.dumps(role_settings(a.role), indent=2, ensure_ascii=False))
        return 0
    require_doctor()
    return _spawn_one(a.cwd, a.role, a.task, a.unattended, a.issue)


def checkout_issue_branch(cwd: str, issue: int, role: str) -> str:
    """대상 레포에서 issue-<n>/<역할> 브랜치를 만든다(있으면 갈아탄다).

    core 의 board-gate R4 가 보드 쓰기를 이 브랜치에서만 허용하므로, 스폰
    전에 서 있어야 세션이 첫 쓰기부터 막히지 않는다. base 는 원격 기본
    브랜치 — 역할 산출물은 main 에서 갈라져 PR 로만 돌아간다 (계약 v3 s10).
    """
    br = f"issue-{issue}/{role}"
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    git("fetch", "origin")
    if git("rev-parse", "--verify", "-q", br).returncode == 0:
        r = git("checkout", br)
    else:
        base = _base(cwd)
        r = git("checkout", "-b", br, base)
        if r.returncode != 0:      # base 없음(원격 없음 등) — 현 HEAD 에서라도 만든다
            r = git("checkout", "-b", br)
    if r.returncode != 0:
        sys.exit(f"브랜치 {br} 로 못 갈아탔다: {r.stderr.strip()[:200]}")
    return br


def _spawn_one(cwd: str, role: str, task: str, unattended: bool,
               issue: int | None = None) -> int:
    """역할 하나를 띄우고, 무슨 일이 있었는지 원장에 남기고, 처분을 말한다.

    main() 과 drive() 가 같은 몸통을 쓴다 — 드라이버가 따로 스폰 경로를 들고
    있으면 둘이 갈라지고, 갈라진 쪽이 조용히 게이트 하나를 빠뜨린다.
    """
    import wakes          # wakes 가 spawn 을 import 한다 — 여기서만 끌어온다
    spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())
    if issue is not None:
        br = checkout_issue_branch(cwd, issue, role)
        task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
                f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n\n") + task
    if issue is not None:
        br = checkout_issue_branch(cwd, issue, role)
        task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
                f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n\n") + task
    plugins = plugin_dirs(role, spec)
    s = role_settings(role)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(s, f)
        settings = f.name
    try:
        print(f"[{role}] 플러그인 {len(plugins)}개, 룰북 {checkout_version(role, spec)}, "
              f"작업 디렉터리 {cwd}", file=sys.stderr)
        # 맡길 일은 stdin 으로 넘긴다. 인자로 주면 가변 인자 플래그가 삼키고,
        # 셸 보간을 거치면 신뢰할 수 없는 값의 $(…) 가 실행된다.
        cmd, extra_env = spawn_cmd(settings, role, unattended,
                                   core_plugin_dirs(), plugins)
        before = board_snapshot(cwd)
        # 이 세션이 답하러 가는 줄들. 세션이 보드를 실제로 바꾼 뒤에만 소비로
        # 적는다 — §6 은 wake 가 **결과 기록**으로 소비된다고 말한다.
        try:
            answering = [r for r in wakes.fresh(cwd)[0] if r.role == role]
        except Exception:
            answering = []
        t0 = time.monotonic()
        # stdout 만 잡는다 — --output-format json 의 결과 오브젝트가 거기 온다.
        # stderr 는 그대로 흘린다: 진행 로그는 사람 것이다.
        proc = subprocess.run(
            cmd, cwd=cwd, input=task, text=True,
            stdout=subprocess.PIPE,
            env={**os.environ, **extra_env},
        )
        rc = proc.returncode
    finally:
        os.unlink(settings)

    result = session_result(proc.stdout)
    if result.get("result"):
        print(result["result"])                  # 세션의 마지막 답 — 기존 UX
    elif proc.stdout.strip():
        print(proc.stdout, end="")               # JSON 이 아니면 그대로 — 숨기지 않는다

    after = board_snapshot(cwd)
    delta = sorted(p for p in set(before) | set(after)
                   if before.get(p) != after.get(p))
    try:
        _, _, blocked = wakes.evaluate(cwd)
    except Exception:
        blocked = []       # 분류 보조일 뿐, 평가 실패로 스폰 결과를 잃지 않는다

    gates = gate_report(cwd) + ownership_report(cwd, role, delta)
    outcome = classify(rc, result, delta, blocked)
    denials = result.get("permission_denials") or []
    if outcome == "progressed":
        # 계약 §6: wake 는 그 결과 기록이 쓰여야 소비된다. 아무것도 안 썼으면
        # 그 줄은 답해지지 않은 채로 남아 다음 평가에 다시 선다.
        wakes.consume(cwd, answering)
    ledger_write({
        "ts": int(time.time()), "role": role, "cwd": str(Path(cwd).resolve()),
        "session_id": result.get("session_id"),
        "cost_usd": result.get("total_cost_usd"),
        "turns": result.get("num_turns"), "rc": rc, "outcome": outcome,
        "board_delta": delta, "denials": len(denials),
        "duration_s": round(time.monotonic() - t0, 1),
        "rulebook": checkout_version(role, spec),
        "gates": gates,
    })

    for line in gates:
        print(line, file=sys.stderr)
    print(f"[{role}] {outcome}"
          + (f", 보드 변화 {len(delta)}건" if delta else ", 보드 무변화")
          + (f", 비용 ${result.get('total_cost_usd'):.2f}"
             if isinstance(result.get("total_cost_usd"), (int, float)) else ""),
          file=sys.stderr)
    sid = f" (session {result.get('session_id')})" if result.get("session_id") else ""
    if denials:
        print(f"[{role}] 거부된 도구 호출 {len(denials)}건 — 게이트가 막았거나 "
              f"답할 사람이 없어 거부됐다. 무엇을 막았는지는 세션 출력에 있다",
              file=sys.stderr)
    if outcome == "refused":
        print(f"[{role}] 게이트가 막아서 보드가 안 바뀌었다 — 이건 실패가 아니라 "
              f"규칙이 지켜진 것일 수 있다. 위 거부 사유를 읽고 맡길 일을 "
              f"고쳐서 다시 띄워라{sid}", file=sys.stderr)
    if outcome == "silent-failure":
        print(f"[{role}] exit 0 인데 보드도 안 바뀌고 막힌 것도 없다 — 성공이 "
              f"아니라 실측된 침묵-사망 모드다. 세션 로그를 확인하라{sid}",
              file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
