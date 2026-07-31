#!/usr/bin/env python3
"""역할별 플러그인 환경으로 에이전트를 띄운다. on-the-record 의 핵심 동작 하나.

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
import contextlib
import re
import fcntl
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

# 공식 공개 패키지 레지스트리 호스트 — role_settings() 가 모든 역할의
# allowedDomains 에 병합한다(이슈 #38). 캐시 미스 시의 폴백 경로이므로
# 미러/CDN 없이 레지스트리 본체만 좁게 유지한다.
PACKAGE_REGISTRY_HOSTS = [
    "registry.npmjs.org",
    "pypi.org",
    "files.pythonhosted.org",
    "proxy.golang.org",
    "sum.golang.org",
    "crates.io",
    "static.crates.io",
    "repo.maven.apache.org",
]

# 호스트에 이미 있는 패키지 캐시 디렉터리 후보 — 존재하면 읽기 전용으로
# 샌드박스에 마운트한다(이슈 #38). (env_var, default_path) 쌍이며, env_var 가
# os.environ 에 있으면 그 값을, 없으면 default_path 를 role_settings() 와
# 동일한 방식(os.path.expanduser/os.path.expandvars)으로 해석한다.
PACKAGE_CACHE_DIRS = [
    ("GOMODCACHE", "~/go/pkg/mod"),
    ("NPM_CONFIG_CACHE", "~/.npm"),
    ("PIP_CACHE_DIR", "~/.cache/pip"),
    (None, "~/.cargo/registry"),
    ("MAVEN_REPO", "~/.m2/repository"),
]

# WebSearch/WebFetch 목적지는 사전에 열거할 수 없다(이슈 #58) — 모든 역할에
# 적용된다(operator 결정: option B). Claude Code 샌드박스의 도메인 매처(Kat())는
# 리터럴 "*" 항목을 모든 호스트에 매칭시킨다(cli.js 확인, 2.1.220) — 그래서
# 하나짜리 와일드카드 상수로 충분하고, 등록되지 않은 호스트 목록을 만들 필요가
# 없다.
WEB_ACCESS_DOMAINS = ["*"]

# Open every remaining default-deny sandbox switch surveyed for issue #72
# (docs/issue-72/reports/coding/survey.md) — the sandbox itself (`enabled`)
# and `allowUnsandboxedCommands=False` stay untouched; those two alone keep
# the sandbox mandatory. macOS-only keys (`allowMachLookup`,
# `allowAppleEvents`) are no-ops on Linux.
SANDBOX_OPEN_NETWORK = {
    "allowAllUnixSockets": True,
    "allowLocalBinding": True,
    "allowMachLookup": ["*"],
}
SANDBOX_OPEN_TOP_LEVEL = {
    "enableWeakerNetworkIsolation": True,
    "allowAppleEvents": True,
    "enableWeakerNestedSandbox": True,
}


def go_proxy_layer(s: dict) -> str | None:
    """호스트 GOMODCACHE 가 읽기 전용으로 마운트됐으면(이슈 #38) GOPROXY 에 그
    캐시를 file:// 소스로 앞세운다.

    role_settings() 는 캐시 디렉터리를 sandbox.filesystem.allowRead 에
    추가할 뿐, spawn() 이 그 뒤 GOMODCACHE 를 워크스페이스로 재지정하므로
    (spawn.py 의 .muster-cache 리다이렉션) 마운트된 호스트 캐시가 조용히
    무시된다 — Go 는 GOMODCACHE 를 쓰기 캐시로만 쓰고 두 캐시를 겸하지
    않기 때문. GOPROXY 는 여러 소스를 순서대로 시도하므로, 호스트 캐시를
    읽기 전용 첫 소스로 앞세우고 GOMODCACHE 는 워크스페이스에 남겨 쓰기는
    그대로 승인 없이 돈다.
    """
    env_var, default_path = next(p for p in PACKAGE_CACHE_DIRS if p[0] == "GOMODCACHE")
    host_path = os.path.expanduser(os.path.expandvars(os.environ.get(env_var, default_path)))
    allow_read = s.get("sandbox", {}).get("filesystem", {}).get("allowRead", [])
    if host_path not in allow_read:
        return None
    return f"file://{host_path}/cache/download,https://proxy.golang.org,direct"


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

    로컬 우선인 이유는 개발이다 — 룰북을 고치면서 on-the-record 로 돌려볼 때 커밋·푸시를
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
    쪽이 그대로 쓰인다 — on-the-record 가 github 를 달라고 해도 등록부가 directory 면
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
    on-the-record 가 자기 밑에 클론해 둔다.

    설치를 거치지 않는다. 설치 경로에는 실측된 함정이 셋 있고 전부 조용하다:
    캐시와 클론이 갈라지고(`claude plugin update` 는 버전 문자열만 본다),
    캐시를 지워도 등록부에 유령 항목이 남고, 이름이 이미 등록돼 있으면
    `--settings` 의 extraKnownMarketplaces 가 무시된다. 셋 다 결과는 같다 —
    **의도한 것과 다른 커밋이 세션에 붙는데 아무도 모른다.** 실측
    2026-07-27: drive 가 띄운 qa 세션이 방금 고친 보안 결함이 그대로 있는
    e940cbe 로 돌았다(머지된 main 은 1195ace).

    on-the-record 소유 클론이라 무엇이 돌았는지 sha 로 말할 수 있고, 나중에 특정
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
    where = "로컬" if _path(spec) and _mkt(Path(_path(spec))).exists() else "on-the-record 클론"
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
    """왜 못 받았는지 on-the-record 가 실제로 알 수 있는 원인부터 말한다.

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

    # 패키지 레지스트리 호스트를 병합한다(이슈 #38) — 샌드박스가 켜진 역할만.
    # 역할이 선언한 도메인은 지우지 않고, 이미 있는 호스트는 중복 추가하지 않는다.
    if sb0 := s.get("sandbox", {}):
        if sb0.get("enabled"):
            net = sb0.setdefault("network", {})
            domains = net.setdefault("allowedDomains", [])
            for host in PACKAGE_REGISTRY_HOSTS:
                if host not in domains:
                    domains.append(host)
            # 웹 접근 도메인도 같은 방식으로 병합한다(이슈 #58) — 켜져 있는
            # 역할이 선언한 도메인이나 레지스트리 호스트를 지우지 않고,
            # 중복 추가도 하지 않는다.
            for host in WEB_ACCESS_DOMAINS:
                if host not in domains:
                    domains.append(host)
            # 나머지 기본값이 제한적인 샌드박스 스위치를 전부 연다(이슈 #72) —
            # sandbox.enabled 와 allowUnsandboxedCommands=False 는 그대로 둔다.
            for key, val in SANDBOX_OPEN_NETWORK.items():
                if key not in net:
                    net[key] = val
            for key, val in SANDBOX_OPEN_TOP_LEVEL.items():
                if key not in sb0:
                    sb0[key] = val

    # 호스트 패키지 캐시를 읽기 전용으로 마운트한다(이슈 #38). 존재하는
    # 디렉터리만 추가한다 — 없으면 조용히 건너뛴다(에러도 출력도 없음).
    # 여기서 쓰는 GOMODCACHE 등은 호스트의 실제 캐시 소스이며, 아래
    # .muster-cache 쓰기 리다이렉션(spawn_cmd 호출부, 별도 함수)과는
    # 별개의 관심사다 — 섞지 않는다.
    if sb0 := s.get("sandbox", {}):
        if sb0.get("enabled"):
            for env_var, default_path in PACKAGE_CACHE_DIRS:
                raw = os.environ.get(env_var, default_path) if env_var else default_path
                cache_path = os.path.expanduser(os.path.expandvars(raw))
                if os.path.isdir(cache_path):
                    fs2 = sb0.setdefault("filesystem", {})
                    allow_read = fs2.setdefault("allowRead", [])
                    if cache_path not in allow_read:
                        allow_read.append(cache_path)

    # 전역 플러그인은 전부 끈다. 켜야 할 것을 적는 게 아니라 꺼야 할 것을
    # 빠짐없이 적는 쪽이라, 전역에 플러그인이 새로 깔려도 새지 않는다.
    s["enabledPlugins"] = {}
    try:
        globals_ = json.loads(USER_SETTINGS.read_text()).get("enabledPlugins", {})
    except (OSError, ValueError):
        globals_ = {}
    for name in globals_:
        s.setdefault("enabledPlugins", {}).setdefault(name, False)

    # WebSearch/WebFetch 는 두 층에서 막힌다(이슈 #65, #58 후속). #58 은 샌드박스
    # NETWORK 층(allowedDomains)만 열었다 — TOOL-PERMISSION 층은 별개로, headless
    # 세션은 --permission-mode acceptEdits 로 뜨고 답할 사람이 없어서
    # permissions.allow 에 규칙이 없는 도구는 그냥 거부된다(#58 조사가 놓친 지점).
    # 모든 역할에 적용한다(#58 과 동일한 operator 결정: option B) — 샌드박스
    # 활성 여부와 무관하다, 이 층은 샌드박스가 아니라 CLI 권한 프롬프트이므로.
    # Read/Grep/Glob 도 같은 이유로 추가한다(이슈 #153) — 읽기 전용 조회이고
    # 도달 가능한 경로는 여전히 sandbox.filesystem.allowRead/denyRead 가 정한다;
    # 이 층은 그 경계를 넓히지 않는다. Bash 하위 패턴은 "읽기 전용"으로 안전하게
    # 한정할 수 없어 제외한다(survey 3절).
    allow = s.setdefault("permissions", {}).setdefault("allow", [])
    for tool in ("WebSearch", "WebFetch", "Read", "Grep", "Glob"):
        if tool not in allow:
            allow.append(tool)

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
            # 아홉 개가 한꺼번에 붙는다 — on-the-record 가 막으려는 그 오염을 on-the-record 가
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
    0개로 조용히 돈다 — on-the-record 는 "플러그인 1개"라고 출력하고, 에이전트는 룰북
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
        # 워밍업도 대상 레포에서 돈다. cwd 를 안 넘기면 on-the-record 자신의 디렉터리에서
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
    """설치가 왜 안 됐는지 on-the-record 가 실제로 알 수 있는 원인부터 말한다.

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


# 역할 순서. 보드를 읽을 때 이 순서로 보여준다.
ROLES = ("product-discovery", "interaction-design", "technical-feasibility",
         "implementation", "execution-observation", "conformance-review",
         "defect-verification", "issue-retrospective", "release-engineering",
         "user-discovery", "requirements-engineering", "refactoring-legacy",
         "test-authoring", "observability", "incident-response",
         "capacity-planning", "knowledge-management",
         "ux-engineering", "api-design", "architecture", "security-threat-model",
         "data-modeling", "performance-engineering", "accessibility", "secure-coding",
         "ml-engineering", "data-engineering",
         "market-analysis", "finance-unit-economics", "pricing", "sales", "marketing",
         "growth-analytics", "customer-support", "partnerships-bd", "pr-communications",
         "risk-management", "legal-compliance",
         "technical-writing", "brand-design", "content-design", "localization", "devrel")
BOARD = "docs"                          # v3: subject trees live at docs/issue-<n>/
MARKER = "docs/specs/approvers.md"      # 보드 opt-in + 승인자 allowlist (v3)
# 계약 v1 이 쓰던 자리. 아직 v2 로 안 옮긴 레포를 **말해주기 위해서만** 본다
LEGACY = {"conformance-review": "review-record.md",
          "technical-feasibility": "feasibility-record.md",
          "release-engineering": "state.md",
          "product-discovery": "product-record.md"}


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

    **on-the-record 의 샌드박스는 이걸 못 막는다.** 설정 우선순위는
    `--settings` > `<레포>/.claude/settings.json` > `~/.claude/settings.json` 인데,
    on-the-record 는 양 끝만 읽고 가운데를 안 본다. 그리고 `hooks` 는 덮어쓰기가 아니라
    **더해지고**, 훅 명령은 선언한 `sandbox.filesystem` 정책을 받지 않는다.

    실측 2026-07-27. `denyWrite` 와 `denyRead` 를 선언한 역할 설정으로 띄웠는데,
    레포가 커밋해 둔 SessionStart 훅이 **denyWrite 경로에 쓰고 denyRead 인
    `~/.claude/settings.json` 을 읽어냈다.** 사용자 권한 그대로, 프롬프트 없이,
    `env={**os.environ}` 을 통째로 들고. 레포를 클론해서 on-the-record 를 겨눈 것만으로
    성립한다.

    계약 파일과 같은 처분을 한다 — 경고가 아니라 정지, 그리고 명시적 opt-out.
    사고가 아니라 결정이 되게.

    신뢰는 **내용 해시에 고정**된다: --trust-repo-config 로 한 번 통과시키면
    그 시점의 .claude/ 내용 다이제스트를 기록하고, 이후 스폰은 내용이 같을
    때만 자동 통과한다. 내용이 바뀌면 다시 멈춘다 — "어제 읽어본 훅"이 아닌
    "오늘 바뀐 훅"이 무검토로 도는 일을 막는다.
    """
    root = Path(cwd).resolve()
    rogue = [p for p in REPO_CONFIG if (root / p).exists()]
    if not rogue:
        return

    import hashlib
    h = hashlib.sha256()
    for rel in sorted(rogue):
        p = root / rel
        h.update(rel.encode())
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    h.update(str(f.relative_to(p)).encode())
                    h.update(f.read_bytes())
        else:
            h.update(p.read_bytes())
    digest = h.hexdigest()

    pins = Path.home() / ".tokenmaxxxer" / "trusted-repo-config.json"
    try:
        table = json.loads(pins.read_text())
    except (OSError, ValueError):
        table = {}
    key = str(root)

    if override:
        table[key] = digest
        pins.parent.mkdir(parents=True, exist_ok=True)
        pins.write_text(json.dumps(table, indent=2))
        print(f"[trust] 레포 설정을 이 내용({digest[:12]})으로 신뢰 고정했다: "
              f"{', '.join(rogue)}", file=sys.stderr)
        return
    if table.get(key) == digest:
        return          # 전에 읽고 신뢰한 그 내용 그대로다

    changed = key in table
    sys.exit(
        f"대상 레포가 자기 Claude 설정을 들고 있다: {', '.join(rogue)}\n"
        f"  {root}\n"
        + ("  전에 신뢰했던 내용에서 **바뀌었다** — 다시 읽어보고 판단해야 한다.\n"
           if changed else "")
        + f"  그 훅들은 on-the-record 가 선언한 샌드박스 경계를 **받지 않는다**. 띄우면\n"
        f"  denyRead 로 막은 경로까지 읽힌다(실측). 내용을 직접 읽어보고,\n"
        f"  믿을 수 있으면 --trust-repo-config 로 명시한다 — 이 내용 해시로\n"
        f"  고정되어, 같은 내용인 동안은 다시 묻지 않는다.")


def _approvers(root: Path) -> set[str]:
    """`docs/specs/approvers.md` 한 줄에 하나씩 적힌 GitHub 로그인."""
    p = root / MARKER
    if not p.is_file():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*(\S+)", line)
        if m:
            out.add(m.group(1))
    return out


def _repo_slug(root: Path) -> str | None:
    r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner",
                        "-q", ".nameWithOwner"], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def _pr_for_branch(root: Path, branch: str) -> int | None:
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number", "-q", ".[0].number"],
                       cwd=root, capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else None


def _issue_comments(root: Path, number: int) -> list[dict]:
    """`number` 앞으로 달린 코멘트. GitHub 는 이슈든 PR 이든 같은
    `/issues/<n>/comments` 로 대화 코멘트를 낸다 — PR 리뷰 코멘트가 아니라
    일반 코멘트가 필요하므로 이 엔드포인트로 충분하다."""
    slug = _repo_slug(root)
    if not slug:
        return []
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{number}/comments"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return []
    return [{"login": c.get("user", {}).get("login", ""), "body": c.get("body", "")}
            for c in data]


_UPSTREAM_PATH = re.compile(r"^\s*-\s*path:\s*(\S+)", re.M)


def _record_upstream(record: Path) -> dict[str, str]:
    """기록의 `upstream:` 목록에서 path 만 뽑는다 (첫 빌드 판별용).

    frontmatter 의 중첩 블록이라 frontmatter() 의 평면 파서로는 안 잡힌다.
    """
    try:
        text = record.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)
    if len(block) < 3:
        return {}
    return {m.group(1): "" for m in _UPSTREAM_PATH.finditer(block[1])}


def _front_role(root: Path, subject: str, roles: dict) -> str | None:
    """그 subject 의 front record — subject 를 처음 연 역할 (첫 빌드 승인 게이트).

    upstream 이 빈 역할이 하나뿐이면 그게 체인 루트다. 못 가리면 관례 순서
    (product, 아니면 feasibility)로 물러난다.
    """
    rootless = [r for r in roles
                if not _record_upstream(root / BOARD / subject / "reports" / f"{r}.md")]
    if len(rootless) == 1:
        return rootless[0]
    for r in ("product-discovery", "technical-feasibility"):
        if r in roles:
            return r
    return None


def approve_scope(cwd: str, issue: int) -> int:
    """s19 의 정확한 문자열 댓글을 승인자 allowlist 로 검증하고, front record 를
    `scope-approved` 로 올리는 커밋을 직접 쓴다 (이슈 #115).

    승인은 여전히 사람의 몫이다 — 이 함수는 그 결정을 **표현하는 방법**(댓글)에서
    **기록에 반영하는 방법**(커밋)으로 옮길 뿐, 어느 역할도 스스로 승인하지
    못한다는 규칙은 그대로 둔다.
    """
    root = Path(cwd).resolve()
    subject = f"issue-{issue}"
    approvers = _approvers(root)
    if not approvers:
        sys.exit(f"승인자 목록이 비어 있다: {root / MARKER}")

    roles = board(root).get(subject)
    if not roles:
        sys.exit(f"{subject} 의 보드 기록이 없다: {root / BOARD / subject / 'reports'}")

    front = _front_role(root, subject, roles)
    if not front:
        sys.exit(f"{subject} 의 front record 를 판별할 수 없다.")

    record_path = root / BOARD / subject / "reports" / f"{front}.md"
    fm = frontmatter(record_path)
    state = fm.get("loop_state")
    if state == "scope-approved":
        print(f"이미 scope-approved 다: {record_path}")
        return 0
    if state != "scope-proposed":
        sys.exit(f"{record_path} 의 loop_state 가 scope-proposed 가 아니다 "
                 f"(지금: {state or '(없음)'}) — 승인 대상이 아니다.")

    needle = f"APPROVE {subject}/scope"
    pr = _pr_for_branch(root, f"{subject}/{front}")
    # 이슈 댓글이 승인 정본이다 — 먼저 본다. PR 댓글은 PR 이 있을 때만 보는
    # fallback 이지 대등한 소스가 아니다(issue-126: 위치 드리프트로 승인을
    # 놓친 사례가 있었다). 순서를 바꾸지 말 것.
    comments = _issue_comments(root, issue)
    if pr:
        comments += _issue_comments(root, pr)
    match = next((c for c in comments
                  if c["body"].strip() == needle and c["login"] in approvers), None)
    if not match:
        where = f"이슈 #{issue}" + (f" 또는 PR #{pr}" if pr else "")
        sys.exit(f"승인 코멘트를 못 찾았다: 정확히 \"{needle}\" 를 "
                 f"{', '.join(sorted(approvers))} 중 한 계정이 {where} 에 달아야 한다.")

    text = record_path.read_text(encoding="utf-8")
    new_text = re.sub(r"(?m)^loop_state:.*$", "loop_state: scope-approved", text, count=1)
    if new_text == text:
        sys.exit(f"{record_path} 에서 loop_state 줄을 찾지 못해 고치지 못했다.")
    record_path.write_text(new_text, encoding="utf-8")

    # git add/commit 이 중간에 실패하면(정체성 없음, 훅 거부, 락, 디스크 없음)
    # 파일은 scope-approved 인데 커밋은 없는 상태가 남는다 — 다음 호출이
    # idempotency 가드(state == "scope-approved")에 걸려 커밋 없이 성공을
    # 보고한다(실측: warrant-hunter, 2026-07-30). 파일 쓰기를 되돌려 그 상태를
    # 만들지 않는다.
    rel = str(record_path.relative_to(root))
    try:
        subprocess.run(["git", "-C", str(root), "add", rel],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m",
                        f"{subject}: scope-approved (approved by {match['login']} "
                        f"via spawn.py approve-scope)"],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        record_path.write_text(text, encoding="utf-8")
        sys.exit(f"커밋 실패 — 기록을 되돌렸다({record_path}), 다시 시도해도 된다: "
                 f"{e.stderr.strip() if e.stderr else e}")

    print(f"{subject}: {front} 기록을 scope-approved 로 올리고 커밋했다 — "
          f"{match['login']} 의 승인. push 는 별도로 한다.")
    return 0


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

    상태는 에이전트의 것이다. on-the-record 가 이걸 고치기 시작하면 룰북의 전이 게이트를
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

    **막지는 않는다.** 세션이 끝난 뒤라 되돌릴 수 없고, on-the-record 는 판정하지 않는다.
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
        if role == "technical-feasibility" and rest.startswith("spikes/"):
            continue
        if role == "release-engineering" and rest.startswith("postmortems/"):
            continue
        bad.append(f"  - {p} (다른 역할의 기록)")
    if not bad:
        return []
    return [f"[소유권] {role} 이 자기 것이 아닌 보드 경로를 건드렸다 — "
            f"세션 안의 게이트가 안 돌았다는 뜻이다 (계약 §11):"] + bad


def _git_head(cwd: str) -> str | None:
    """현재 HEAD 커밋. 아직 커밋이 없는 새 레포면 None (에러로 취급하지
    않는다 — 커밋이 없는 상태도 유효한 시작점이다)."""
    c = subprocess.run(["git", "-C", cwd, "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return c.stdout.strip() if c.returncode == 0 else None


def _is_new_commit(cwd: str, before_head: str | None, after_head: str | None) -> bool:
    """`after_head` 가 `before_head` 위에 실제로 새 커밋을 얹었는지 판단한다.

    단순히 `after_head != before_head` 로는 부족하다 — 기존에 있던 브랜치나
    커밋으로 체크아웃만 해도 HEAD 는 바뀌지만 새 커밋은 없다. before_head 가
    after_head 의 조상(ancestor)인지까지 확인해야 "진짜 새 커밋"이라고 말할 수
    있다. before_head 가 None (아직 커밋이 없던 새 레포)이면 after_head 가
    있는 것만으로 새 커밋이다.
    """
    if after_head is None:
        return False
    if before_head is None:
        return True
    if before_head == after_head:
        return False
    c = subprocess.run(
        ["git", "-C", cwd, "merge-base", "--is-ancestor", before_head, after_head],
        capture_output=True, text=True,
    )
    return c.returncode == 0


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


def session_end_verdict(work: str, now: float | None = None,
                        alive_fn=None) -> str:
    """워크스페이스 하나의 세션-종료 3분법: `normal` / `crashed` / `stalled` /
    `in-progress` (이슈 #132).

    `<work>.events.jsonl` 에서 마지막 `session-start` 를 찾고, 그 뒤에
    `session-end` 가 이미 왔는지부터 본다 — 죽었다고 보고된 pid 가 사실은
    그 찰나에 정상 종료했을 수도 있는 벤인 레이스를, `_alive()` 보다 먼저
    확인해 `normal` 로 되돌린다. 매치가 없을 때만 `_alive()`/로그 mtime 을
    본다.
    """
    now = time.time() if now is None else now
    alive_fn = _alive if alive_fn is None else alive_fn
    events_path = _events_path(work)
    if not events_path.exists():
        return "normal"
    events = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    start_idx = None
    for i in range(len(events) - 1, -1, -1):
        if events[i].get("type") == "session-start":
            start_idx = i
            break
    if start_idx is None:
        return "normal"
    if any(ev.get("type") == "session-end" for ev in events[start_idx + 1:]):
        return "normal"
    detail = events[start_idx].get("detail") or {}
    pid = detail.get("pid")
    if not alive_fn(pid):
        return "crashed"
    log_path = Path(str(work) + ".session.log")
    if log_path.exists():
        silent_min = (now - log_path.stat().st_mtime) / 60
        if silent_min > WATCHDOG_SILENCE_MIN:
            return "stalled"
    return "in-progress"


def fail_closed_downgrade(outcome: str, issue: int | None, blocked: list,
                          new_commit: bool, uncommitted: list,
                          already_delivered: bool = False) -> str:
    """`classify()` 뒤에 붙는 별도 단계 — git 상태로 `progressed` 를
    검증한다. `classify()` 자체는 손대지 않는다: git 상태를 모르고, 기존
    계약(rc/result/delta/blocked)과 기존 테스트를 그대로 둔다.

    `issue is not None` 스폰만 대상이다 — 전용 git 워크스페이스가 있는
    경로만 커밋 여부를 검사할 수 있다.

    `blocked` 를 먼저 확인한다 (hunt-phase1 발견 반영): `classify()` 는
    delta 를 blocked 보다 먼저 보므로, 보드가 움직였고 동시에 사람 게이트가
    아직 서 있는 run 은 오늘도 "progressed" 로 분류된다. 그런 run 을 커밋이
    없다고 FAILED 로 깎으면 정직한 blocked 신호를 완전히 지워버린다 — 그래서
    `blocked` 가 비어있지 않으면 이 다운그레이드는 아예 건드리지 않는다.

    `already_delivered` (issue #129 phase 2): 이 세션 자신의 before→after
    HEAD 델타만 보면, 같은 브랜치에서 이전 phase 가 이미 커밋+PR 을 남긴
    뒤 이번 세션이 검증만 하고 새 커밋 없이 끝난 경우를 "실패"로 오분류한다
    — 브랜치에 이미 PR 이 있다는 사실을 호출부에서 확인해 넘긴다. 미커밋
    변경이 남아있으면(더러운 트리) 여전히 다운그레이드한다: "이미 배달됨" 이
    "이번 세션이 남긴 새 변경도 안전하다"를 의미하지 않는다.
    """
    if outcome != "progressed" or issue is None:
        return outcome
    if blocked:
        return outcome
    if uncommitted:
        return "failed-no-commit"
    if new_commit or already_delivered:
        return outcome
    return "failed-no-commit"


ROSTER = ROOT / "runs" / "active.json"


@contextlib.contextmanager
def _roster_locked():
    """runs/active.json 의 load-mutate-save 구간을 프로세스 간에 직렬화한다."""
    lock_path = ROSTER.with_name(ROSTER.name + ".lock")
    lock_path.parent.mkdir(exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _roster_load() -> dict:
    try:
        return json.loads(ROSTER.read_text())
    except (OSError, ValueError):
        return {}


def _roster_save(d: dict) -> None:
    ROSTER.parent.mkdir(exist_ok=True)
    ROSTER.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def roster_register(key: str, entry: dict) -> None:
    with _roster_locked():
        d = _roster_load()
        d[key] = entry
        _roster_save(d)


def roster_remove(key: str) -> None:
    with _roster_locked():
        d = _roster_load()
        if d.pop(key, None) is not None:
            _roster_save(d)


def roster_ps() -> int:
    """돌고 있는 역할 세션들. 죽은 항목은 표시 후 정리한다."""
    d = _roster_load()
    if not d:
        print("돌고 있는 역할 세션 없음")
        return 0
    dead = []
    for key, e in sorted(d.items()):
        pid = e.get("pid", 0)
        alive = _alive(pid)
        mins = (int(time.time()) - e.get("ts", 0)) // 60
        state = "RUNNING" if alive else "DEAD(정리됨)"
        print(f"{state:14s} {e.get('role','?'):12s} issue-{e.get('issue','?')}  "
              f"{mins}분  pid {pid}")
        print(f"               log: {e.get('log','')}")
        print(f"               work: {e.get('work','')}")
        if not alive:
            dead.append(key)
    for k in dead:
        roster_remove(k)
    return 0


WATCHDOG_STATE = ROOT / "runs" / "watchdog_state.json"
WATCHDOG_SILENCE_MIN = 90     # 이슈 #90 proposal, signal 1
WATCHDOG_NO_COMMIT_MIN = 71   # 이슈 #90 proposal, signal 4 (0.5 * p90 ≈ 142.6)
WATCHDOG_DENIAL_THRESHOLD = 3 # 이슈 #90 proposal, signal 3
_DELEGATION_RE = re.compile(
    r"run_in_background|백그라운드|delegate|background worker", re.IGNORECASE)
_DENIAL_RE = re.compile(r"permission_denial|denied", re.IGNORECASE)


def _watchdog_state_load() -> dict:
    try:
        return json.loads(WATCHDOG_STATE.read_text())
    except (OSError, ValueError):
        return {}


def _watchdog_state_save(d: dict) -> None:
    WATCHDOG_STATE.parent.mkdir(exist_ok=True)
    WATCHDOG_STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def watchdog_check_one(key: str, entry: dict, now: float | None = None,
                       state: dict | None = None) -> list[str]:
    """이슈 #90 phase-2: 살아있는 세션 하나에 대해 관찰만 하는(observe-only)
    이상 신호 목록을 돌려준다. 세션의 프로세스·프롬프트·워크트리는 건드리지
    않는다 — 로그 mtime/내용, 로스터 필드, git 상태만 읽는다.

    `state` 를 넘기면 그 dict 를 제자리에서 갱신하고 저장하지 않는다(테스트
    용). 생략하면 `runs/watchdog_state.json` 을 읽고 쓴다.
    """
    now = time.time() if now is None else now
    anomalies: list[str] = []
    log_path = Path(entry["log"]) if entry.get("log") else None
    work = entry.get("work")
    ts = entry.get("ts", 0)
    elapsed_min = (now - ts) / 60

    # signal 1: 로그 무응답 — 프로포절 §Anomaly-signal-list #1
    if log_path is not None and log_path.exists():
        mtime = log_path.stat().st_mtime
        silent_min = (now - mtime) / 60
        if silent_min > WATCHDOG_SILENCE_MIN:
            anomalies.append(
                f"log-silence: {int(silent_min)}분째 로그 무응답 ({log_path})")

    # 마지막 스캔 이후 새로 쓰인 로그 내용만 본다 — 신호 2/3
    own_state = state if state is not None else _watchdog_state_load()
    st = own_state.get(key, {"offset": 0})
    text = ""
    start_offset = st.get("offset", 0)
    new_offset = start_offset
    if log_path is not None and log_path.exists():
        # 로그가 이전 스캔 오프셋보다 짧아졌다면 그 사이 세션이 재시작되며
        # 로그가 truncate 된 것이다(spawn 은 같은 경로를 "w" 로 다시 연다) —
        # 옛 오프셋을 그대로 쓰면 새 세션의 신호 2/3 이 로그가 옛 길이를
        # 다시 넘어설 때까지 조용히 못 잡힌다. 이 경우 처음부터 다시 읽는다.
        if log_path.stat().st_size < start_offset:
            start_offset = 0
        with log_path.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(start_offset)
            text = fh.read()
            new_offset = fh.tell()
    own_state[key] = {"offset": new_offset}
    if state is None:
        _watchdog_state_save(own_state)

    # signal 2: 백그라운드-위임 언급 — 시점 무관, 매치 즉시 신고
    if _DELEGATION_RE.search(text):
        anomalies.append(f"background-delegation-phrasing: {log_path}")

    # signal 3: 반복된 거부된 도구 호출 (이번 스캔 구간 내)
    new_denials = len(_DENIAL_RE.findall(text))
    if new_denials >= WATCHDOG_DENIAL_THRESHOLD:
        anomalies.append(
            f"denied-tool-calls: 이번 스캔 구간에 {new_denials}건")

    # signal 4: 반환점 지났는데 커밋 없음 — 이슈 스코프 스폰만 (before_head 필요)
    before_head = entry.get("before_head")
    if work and before_head and elapsed_min > WATCHDOG_NO_COMMIT_MIN:
        r = subprocess.run(
            ["git", "-C", str(work), "rev-list", "--count",
             f"{before_head}..HEAD"],
            capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip() == "0":
            anomalies.append(
                f"no-commits-late: {int(elapsed_min)}분 경과, "
                f"{before_head} 이후 커밋 0건")

    return anomalies


def roster_watchdog(auto_respawn: bool = False) -> int:
    """`spawn.py watchdog` — 살아있는 모든 역할 세션을 한 번 스캔해서 이상
    신호를 사람이 읽을 수 있게 출력한다. observe-only: 아무 것도 고치거나
    죽이지 않는다. 오케스트레이터가 10-15분 간격으로 반복 호출한다
    (이슈 #90 phase-2 프로포절).

    `auto_respawn=True` (이슈 #132): 죽은 로스터 엔트리도 스캔 대상에
    넣어(원래는 살아있는 것만 봤다) `session_end_verdict` 를 매겨, `crashed`
    에 한해서만 재스폰/상한-코멘트를 시도한다. `stalled` 는 여전히
    보고만 한다 — 아무 것도 고치거나 죽이지 않는다는 계약은 그대로다."""
    d = _roster_load()
    if not d:
        print("돌고 있는 역할 세션 없음")
        return 0
    state = _watchdog_state_load()
    respawn_state = _respawn_state_load() if auto_respawn else {}
    found_any = False
    for key, e in sorted(d.items()):
        if not _alive(e.get("pid", 0)):
            if auto_respawn:
                _auto_respawn_check(key, e, respawn_state)
            continue
        anomalies = watchdog_check_one(key, e, state=state)
        if anomalies:
            found_any = True
            print(f"[watchdog] {key}: 이상 신호 {len(anomalies)}건")
            for a in anomalies:
                print(f"  - {a}")
        else:
            print(f"[watchdog] {key}: 정상")
    _watchdog_state_save(state)
    if not found_any:
        print("이상 신호 없음")
    return 0


EVENTS_SUFFIX = ".events.jsonl"
OFFSET_SUFFIX = ".events.offset"
WORKSPACE_INDEX = ROOT / "runs" / "workspaces.json"
_PR_URL_RE = re.compile(r"https://github\.com/[^\s\"'\\]+/pull/\d+")


def _events_path(work: str) -> Path:
    return Path(str(work) + EVENTS_SUFFIX)


def _offset_path(work: str) -> Path:
    return Path(str(work) + OFFSET_SUFFIX)


def _append_event(events_path: Path, ev_type: str, detail) -> None:
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": int(time.time()), "type": ev_type,
                              "detail": detail}, ensure_ascii=False) + "\n")


def _prior_event_details(events_path: Path, ev_type: str) -> set:
    """`events_path` 에 이미 남은 `ev_type` 이벤트들의 `detail` 집합.

    프로세스 재시작(같은 워크스페이스로 재스폰)을 건너 `pr-opened` 를
    멱등하게 만드는 데 쓴다 — 이 워크스페이스의 `.events.jsonl` 은
    append-only 이므로 과거 기록을 읽으면 이전 프로세스의 in-memory
    `pr_seen` 을 재구성할 수 있다."""
    if not events_path.exists():
        return set()
    out = set()
    for line in events_path.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict) and ev.get("type") == ev_type:
            out.add(ev.get("detail"))
    return out


RESPAWN_STATE = ROOT / "runs" / "respawn_state.json"
RESPAWN_MAX_ATTEMPTS = 2
_CRASH_COMMENT_MARKER = "[on-the-record] {key}: crashed, 재스폰 상한({cap}) 도달"


def _respawn_state_load() -> dict:
    try:
        return json.loads(RESPAWN_STATE.read_text())
    except (OSError, ValueError):
        return {}


def _respawn_state_save(d: dict) -> None:
    RESPAWN_STATE.parent.mkdir(exist_ok=True)
    RESPAWN_STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _post_crash_comment(root: Path, issue: int, key: str, work: str, log: str) -> None:
    """재스폰 상한(2) 도달 시 이슈에 남기는 코멘트. 멱등: 고정 마커 문자열을
    기존 코멘트에서 먼저 찾는다(`_issue_comments`/`approve_scope` 와 같은
    read-then-check 패턴) — 워치독을 반복 호출해도 두 번째 코멘트는 없다."""
    marker = _CRASH_COMMENT_MARKER.format(key=key, cap=RESPAWN_MAX_ATTEMPTS)
    if any(marker in c.get("body", "") for c in _issue_comments(root, issue)):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    body = (f"{marker}\n\n"
            f"워크스페이스: {work}\n로그: {log}\n\n"
            f"{RESPAWN_MAX_ATTEMPTS}회 자동 재스폰을 모두 소진했다 — 사람이 개입해야 한다.")
    subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)


def _auto_respawn_check(key: str, entry: dict, state: dict) -> None:
    """죽은 로스터 엔트리 하나에 대해 `crashed` 인지 판정하고, 그렇다면 상한
    안에서 재스폰을 시도하거나(2회 미만) 상한 코멘트를 남긴다(2회 도달).
    `stalled`/`normal`/`in-progress` 는 그냥 보고만 하고 끝난다(관찰-전용
    계약 유지, 이슈 #132)."""
    work = entry.get("work")
    issue = entry.get("issue")
    role = entry.get("role")
    if not work or issue is None or not role:
        return
    verdict = session_end_verdict(work)
    print(f"[watchdog] {key}: {verdict}")
    if verdict != "crashed":
        return
    events_path = _events_path(work)
    events = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if isinstance(ev, dict):
                events.append(ev)
    start_ts = None
    for ev in reversed(events):
        if ev.get("type") == "session-start":
            start_ts = (ev.get("detail") or {}).get("ts")
            break
    already_claimed = any(
        ev.get("type") == "respawn-attempt"
        and isinstance(ev.get("detail"), dict)
        and ev["detail"].get("session_start_ts") == start_ts
        for ev in events)
    if already_claimed:
        return
    attempts = state.get(key, {}).get("attempts", 0)
    root = Path(work)
    if attempts >= RESPAWN_MAX_ATTEMPTS:
        _post_crash_comment(root, issue, key, work, entry.get("log", ""))
        return
    # 위의 already_claimed 은 events.jsonl 을 읽기만 한다 — 두 watchdog
    # 프로세스가 동시에 이 지점에 도달하면 둘 다 통과한다(실측: warrant-hunter
    # 리포트, 스레드 두 개로 재현: 둘 다 _spawn_one 을 호출해 같은 워크스페이스
    # 에 중복 세션이 뜬다). 실제 락은 이 원자적 파일 생성 하나뿐이다 —
    # O_CREAT|O_EXCL 은 POSIX 에서 프로세스 간에도 원자적이라, 두 워치독 중
    # 정확히 하나만 이 파일을 만들 수 있다.
    claim_path = Path(str(work) + f".respawn-claim-{start_ts}")
    try:
        fd = os.open(str(claim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        return
    task_path = Path(str(work) + ".task.txt")
    if not task_path.exists():
        print(f"[watchdog] {key}: crashed 인데 {task_path} 가 없어 재스폰 불가 "
              f"— 사람이 직접 재스폰해야 한다", file=sys.stderr)
        return
    task = task_path.read_text(encoding="utf-8")
    attempt_n = attempts + 1
    _append_event(events_path, "respawn-attempt",
                  {"session_start_ts": start_ts, "attempt": attempt_n})
    state[key] = {"attempts": attempt_n}
    _respawn_state_save(state)
    print(f"[watchdog] {key}: crashed — 재스폰 시도 {attempt_n}/{RESPAWN_MAX_ATTEMPTS}",
          file=sys.stderr)
    _spawn_one(work, role, task, unattended=True, issue=issue, bounded=True)


def _read_offset(offset_path: Path) -> int:
    try:
        return int(offset_path.read_text().strip())
    except (OSError, ValueError):
        return 0


def _event_count(events_path: Path) -> int:
    """events.jsonl 의 줄 수 — offset 과 같은 단위(줄)다."""
    try:
        return len(events_path.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0


def _origin_pr_prefix(cwd) -> str | None:
    """이 레포 자신의 PR URL 접두사. 판별 못 하면 None(=범위 검사 생략)."""
    try:
        out = subprocess.run(["git", "-C", str(cwd), "remote", "get-url", "origin"],
                             capture_output=True, text=True)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    m = re.search(r"github\.com[:/]+([^/\s]+/[^/\s]+?)(?:\.git)?\s*$", out.stdout)
    return f"https://github.com/{m.group(1)}/pull/" if m else None


def _write_offset(offset_path: Path, n: int) -> None:
    offset_path.write_text(str(n))


def _workspace_index_load() -> dict:
    try:
        return json.loads(WORKSPACE_INDEX.read_text())
    except (OSError, ValueError):
        return {}


def _workspace_index_put(issue: int, role: str, work: str, log: str) -> None:
    WORKSPACE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    d = _workspace_index_load()
    d[f"issue-{issue}/{role}"] = {"work": work, "log": log}
    WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _await_bounded(events_path: Path, offset_path: Path, stall_timeout_min: float,
                    log_path: Path) -> int:
    """이벤트 하나가 뜨거나 stall 시간이 다 찰 때까지 — 둘 중 먼저 오는
    쪽에서 리턴한다. 무한정 블록하지 않는다 (이슈 #114 proposal).

    stall 은 events.jsonl 에 안 남고 offset 도 안 미룬다 — 다음 watch 가
    같은 미보고 구간을 다시 본다.
    """
    limit_s = stall_timeout_min * 60
    seen = _read_offset(offset_path)
    try:
        last_size = log_path.stat().st_size
    except OSError:
        last_size = 0
    last_change = time.monotonic()
    while True:
        if events_path.exists():
            lines = events_path.read_text(encoding="utf-8").splitlines()
            if len(lines) > seen:
                ev = json.loads(lines[seen])
                _write_offset(offset_path, seen + 1)
                print(f"[watch] {ev['type']}: {ev['detail']}")
                # exit 0 는 "스폰이 리턴했다"이지 "세션이 끝났다"가 아니다.
                # 호출자가 그 둘을 추론하게 두면 오케스트레이터가 사람에게
                # 끝났다고 오보한다 — 이 저장소가 가장 비싸게 치는 실패다
                # (이슈 #142). session-end 만이 종료를 뜻한다.
                if ev["type"] != "session-end":
                    print("[watch] 스폰은 리턴했지만 세션은 계속 돈다 — "
                          "상태는 spawn.py ps, 이어보려면 spawn.py watch",
                          file=sys.stderr)
                return 0
        try:
            size = log_path.stat().st_size
        except OSError:
            size = last_size
        if size != last_size:
            last_size = size
            last_change = time.monotonic()
        if time.monotonic() - last_change >= limit_s:
            secs = int(time.monotonic() - last_change)
            print(f"[watch] stall: 세션 로그 {secs}초째 무변화 — 이벤트 없이 "
                  f"멈춘다. 다시 spawn.py watch 로 재무장하라", file=sys.stderr)
            return 0
        time.sleep(2)


def _watch(issue: int, role: str | None, stall_timeout_min: float) -> int:
    idx = _workspace_index_load()
    if role:
        entry = idx.get(f"issue-{issue}/{role}")
    else:
        matches = [(k, v) for k, v in idx.items() if k.startswith(f"issue-{issue}/")]
        if len(matches) > 1:
            sys.exit(f"이슈 {issue} 에 역할이 여럿 기록돼 있다 — 역할을 지정하라: "
                     + ", ".join(k.split("/", 1)[1] for k, _ in matches))
        entry = matches[0][1] if matches else None
    if entry is None:
        print(f"[watch] issue-{issue}{'/' + role if role else ''}: 기록 없음 — "
              f"아직 스폰된 적이 없다", file=sys.stderr)
        return 1
    work = entry["work"]
    return _await_bounded(_events_path(work), _offset_path(work),
                           stall_timeout_min, Path(entry["log"]))


def roster_kill(issue: int, role: str) -> int:
    d = _roster_load()
    key = f"issue-{issue}/{role}"
    e = d.get(key)
    if not e:
        print(f"로스터에 없다: {key}", file=sys.stderr)
        return 1
    pid = e.get("pid", 0)
    if _alive(pid):
        os.kill(pid, 15)
        print(f"종료 신호를 보냈다: {key} (pid {pid}). 워크스페이스와 라이브 "
              f"로그는 남는다 — 재스폰이 이어받는다.")
    else:
        print(f"이미 죽어 있다: {key}")
    roster_remove(key)
    return 0


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
    # 로컬 체크아웃이 없으면 룰북과 같은 길: on-the-record 소유 클론을 받아 쓴다.
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
    """드라이버의 유일한 계약상 임무: 더 띄울 게 없으면 멈춘다.

    "누구를 다음에 띄울지"는 기계가 평가하는 라우팅 표가 아니라 오케스트레이터가
    보드(기록, loop_state)를 직접 읽고 내리는 판단이다(이슈 #120) — 그래서
    drive 는 스스로 역할을 고르지 않는다. 자동으로 고를 표가 없으므로 이
    호출은 항상 즉시 멈춘다; 남은 인자는 향후 호출부 호환을 위해 받되 쓰지
    않는다.
    """
    print("[drive] 다음 역할을 자동으로 고르는 라우팅 표는 없다 — "
          "오케스트레이터가 보드를 읽고 판단한다. 띄울 게 없다고 보고 멈춘다.",
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


ROLE_MODEL_CONFIG = ROOT / "role_model.txt"


def read_role_model_config() -> str:
    """이슈#60: repo-root role_model.txt 에서 기본 모델 값을 읽는다. 파일이
    없거나 읽기 오류가 나면 미설정과 동일하게 "" 를 돌려준다."""
    try:
        return ROLE_MODEL_CONFIG.read_text().strip()
    except (OSError, UnicodeDecodeError):
        return ""


def resolved_role_model() -> str:
    """이슈#93: env > config > built-in default("sonnet"). MUSTER_ROLE_MODEL 이
    (strip 후) 비어 있지 않으면 그것이 이긴다 — config 는 그때는 아예 안 읽힌
    값처럼 무시된다. 둘 다 비어 있으면 "sonnet" — --model 이 항상 붙는다,
    호출자의(비쌀 수 있는) 세션 모델을 조용히 물려받지 않도록."""
    env_value = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()
    if env_value:
        return env_value
    return read_role_model_config() or "sonnet"


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
           "--permission-mode", "acceptEdits",
           "--output-format", "stream-json", "--verbose"]
    # 룰북도 core 와 같은 길로 붙는다 — 디렉터리로 넘긴 플러그인의 훅은
    # headless 에서 그대로 발화하고(실측 2026-07-27, CLI 2.1.220), 설치를
    # 안 거치므로 캐시-클론 갈라짐도 유령 등록 항목도 이 경로엔 없다.
    for p in (plugins or []):
        cmd += ["--plugin-dir", str(p)]
    for p in (core_plugins or []):
        cmd += ["--plugin-dir", str(p)]
    # MUSTER_ROLE_MODEL / role_model.txt (이슈#93): 역할 세션이 쓰는 모델을
    # 고정한다. env > config > built-in "sonnet". 둘 다 비어있어도 built-in
    # 이 이겨 --model 이 항상 붙는다 — haiku 프로브(doctor())는 이 함수를
    # 거치지 않으므로 영향 없다.
    role_model = resolved_role_model()
    if role_model:
        cmd += ["--model", role_model]
    env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
    # Two-account model (core README): role sessions act as the AGENT
    # account. MUSTER_AGENT_GH_TOKEN, if set, becomes the session's GH_TOKEN
    # so gh in the container/sandbox authenticates as the agent — never the
    # user. gh-guard denies the human's acts in role sessions regardless.
    # 샌드박스 안에서는 macOS 키링이 안 보여 gh 토큰이 무효로 읽힌다(실측).
    # 그래서 토큰을 env 로 명시 주입한다: 에이전트 토큰이 있으면 그것,
    # 없으면(1계정 기본) 사용자의 gh 토큰을 꺼내 넘긴다. gh-guard 가
    # 역할 세션의 사람-행위 명령은 어차피 막는다.
    agent_token = os.environ.get("MUSTER_AGENT_GH_TOKEN")
    if not agent_token:
        try:
            t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                               text=True, timeout=15)
            agent_token = t.stdout.strip() if t.returncode == 0 else ""
        except Exception:
            agent_token = ""
    if agent_token:
        env["GH_TOKEN"] = agent_token
        env["GIT_TERMINAL_PROMPT"] = "0"
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
    ap.add_argument("--limit", type=int, default=12,
                    help="drive: 한 번에 띄울 최대 횟수 (기본 12, 폭주 방지)")
    ap.add_argument("--login", help="init: approvers.md 에 넣을 GitHub 로그인 (기본: gh api user)")
    ap.add_argument("--stall-timeout", type=float, default=5.0,
                    help="분 단위. role task/watch 가 이벤트 없이 블록하는 최대 시간 (기본 5)")
    ap.add_argument("--role", dest="watch_role",
                    help="watch: 같은 이슈에 역할이 여럿 기록돼 있을 때 지정")
    ap.add_argument("--auto-respawn", action="store_true",
                    help="watchdog: crashed 세션에 한해 최대 2회 자동 재스폰, "
                         "상한 도달 시 이슈 코멘트 (기본 off, 관찰-전용 유지)")
    ap.add_argument("--post", action="store_true",
                    help="closure-sweep: 위반을 해당 이슈에 코멘트로도 남긴다 (기본은 stdout 만)")
    a = ap.parse_args()

    if a.role == "init":
        # 보드로 선언한다(approvers.md). on-the-record 가 남의 레포에 쓰는 유일한 경우.
        return init_board(a.cwd, a.login)
    if a.role == "ps":
        return roster_ps()
    if a.role == "watchdog":
        return roster_watchdog(auto_respawn=a.auto_respawn)
    if a.role == "closure-sweep":
        # 보드 전체를 훑어 이슈-PR 종결 불일치를 보고한다 — 명시적 단발 호출
        # (approve-scope 와 마찬가지로 watchdog 틱에 자동으로 안 물린다, 이슈 #135).
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import closure_sweep
        root = Path(a.cwd).resolve()
        violations = closure_sweep.find_violations(root)
        if not violations:
            print("종결 일관성 스윕: 위반 없음")
            return 0
        print("종결 일관성 스윕: 위반 발견")
        print(closure_sweep.format_report(violations))
        if a.post:
            closure_sweep.post_sweep_comments(root, violations)
        return 1
    if a.role == "kill":
        if not a.task or a.issue is None:
            sys.exit("사용법: spawn.py kill <역할> --issue <n>")
        return roster_kill(a.issue, a.task)
    if a.role == "watch":
        if a.issue is None:
            sys.exit("사용법: spawn.py watch --issue <n> [--role <역할>] "
                     "[--stall-timeout <분>]")
        return _watch(a.issue, a.watch_role, a.stall_timeout)
    if a.role == "clean":
        # 안전한 것만 지운다: 미커밋 변경 없음 + origin 에 없는 커밋 없음.
        base = os.environ.get("MUSTER_WORK_DIR")
        wb = Path(base) if base else Path.home() / ".tokenmaxxxer" / "work"
        roster = _roster_load()
        live = {}
        for e in roster.values():
            if _alive(e.get("pid", 0)):
                live[Path(e["work"]).resolve()] = e
        removed = kept = 0
        for w in sorted(wb.glob("*")) if wb.is_dir() else []:
            if not (w / ".git").is_dir():
                continue
            e = live.get(w.resolve())
            if e is not None:
                print(f"남김 (실행 중인 세션 있음): {w.name}"
                      f"  [issue-{e.get('issue', '?')}/{e.get('role', '?')}, "
                      f"pid {e.get('pid', '?')}]")
                kept += 1
                continue
            st = subprocess.run(["git", "-C", str(w), "status", "--porcelain"],
                                capture_output=True, text=True).stdout.strip()
            ahead = subprocess.run(
                ["git", "-C", str(w), "log", "--branches", "--not", "--remotes",
                 "--oneline"], capture_output=True, text=True).stdout.strip()
            if st or ahead:
                print(f"남김 (미보존 작업 있음): {w.name}"
                      + (f"  [미커밋 {len(st.splitlines())}건]" if st else "")
                      + (f"  [미push 커밋 {len(ahead.splitlines())}건]" if ahead else ""))
                kept += 1
                continue
            import shutil
            shutil.rmtree(w)
            log = Path(str(w) + ".session.log")
            if log.exists():
                log.unlink()
            print(f"지움: {w.name}")
            removed += 1
        print(f"정리 끝 — 지움 {removed}, 남김 {kept}")
        return 0
    if a.role == "update":
        # 룰북을 원격 최신으로. 인자를 비우면 전부.
        return update([a.task] if a.task else list(ROLES))
    if a.role == "doctor":
        # 훅 발화 실측. 버전마다 한 번 — 룰북 집행의 전제조건이다.
        return doctor()
    if a.role == "approve":
        sys.exit("v3: 승인은 파일 발행이 아니라 GitHub 행위다 — 오케스트레이터가\n"
                 "  사용자와의 대화에서 gh pr review --approve / gh pr merge 로 중계한다.")
    if a.role == "approve-scope":
        if a.issue is None:
            sys.exit("사용법: spawn.py approve-scope --issue <n> [-C <레포>]")
        return approve_scope(a.cwd, a.issue)
    if a.role == "drive":
        # 보드가 지목하는 역할을 하나씩, 멈출 때까지.
        require_board(a.cwd, a.no_contract)
        require_no_repo_config(a.cwd, a.trust_repo_config)
        require_doctor()
        return drive(a.cwd, a.unattended, a.limit)
    if not a.role:
        print("\n".join(status(a.cwd)))
        print("\n역할:")
        for p in sorted((ROOT / "roles").glob("*.json")):
            try:
                meta = json.loads(p.read_text())
            except ValueError:
                meta = {}
            print(f"  {p.stem:12s} {meta.get('decides','')}  — {meta.get('use_when','')}")
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
        out = role_settings(a.role)
        # MUSTER_ROLE_MODEL / role_model.txt (이슈#93): spawn_cmd 는 이
        # dry-run 경로를 안 타므로(세션을 안 띄우니까) --model 부착 여부가
        # 여기 안 보이면 이슈#31 acceptance 커맨드(`--dry-run`)로는 이 기능을
        # 검증할 수 없다(실측:
        # docs/reports/2026-07-29-hunt-muster-role-model-build.md). resolved_role_model()
        # 로 spawn_cmd 와 동일한 env > config > built-in "sonnet" 경로를 태워,
        # 둘 다 비어있어도 built-in 값을 키에 넣는다.
        role_model = resolved_role_model()
        if role_model:
            out["model"] = role_model
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if role_model:
            # 실제 스폰 시 spawn_cmd 가 argv 에 붙이는 것과 같은 두 토큰을
            # 여기서도 보여준다 — 이슈#31 acceptance("--dry-run 이 --model
            # sonnet 을 보여준다")가 겨냥하는 문구 그대로.
            print(f"--model {role_model}")
        return 0
    require_doctor()
    return _spawn_one(a.cwd, a.role, a.task, a.unattended, a.issue,
                      bounded=a.issue is not None,
                      stall_timeout_min=a.stall_timeout)


def issue_workspace(cwd: str, issue: int, role: str) -> str:
    """이슈 스폰마다 on-the-record 소유의 격리 클론을 만든다.

    산출물이 PR 로만 돌아오는 모델에서 역할 세션이 사용자의 체크아웃을
    공유할 이유가 없다 — 공유하면 동시 스폰 둘이 같은 .git/index 와 현재
    브랜치를 두고 경합한다(실측: issue-45 와 issue-59 coding 세션이 한
    트리에서 충돌 직전까지 갔다). 로컬에서 클론하고 origin 을 실제 원격으로
    되돌려 push/gh 가 GitHub 로 가게 한다. 재스폰이면 기존 작업 디렉토리를
    fetch 로 재사용한다 — 진행 중이던 브랜치 작업을 버리지 않는다.
    """
    src = Path(cwd).resolve()
    r = subprocess.run(["git", "-C", str(src), "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    origin = r.stdout.strip()
    # 샌드박스는 HTTP 프록시만 뚫려 있다 — ssh(22번)는 나갈 수 없으므로
    # 작업 클론의 origin 은 기본으로 https 로 정규화한다. 회사 정책이 ssh
    # 원격만 허용하면 MUSTER_KEEP_SSH=1 로 끈다 — 그 경우 세션 안 push 는
    # 실패하지만, 세션 뒤 on-the-record 가 호스트 환경(사용자의 ssh 키)에서
    # push/PR 를 대신한다(아래 ensure_pushed).
    if os.environ.get("MUSTER_KEEP_SSH", "") not in ("", "0", "false", "no", "off"):
        pass
    else:
        m = re.match(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$", origin)
        if m:
            origin = "https://github.com/%s.git" % m.group(1)
    if not origin:
        sys.exit(f"대상 레포에 origin 원격이 없다: {src} — 이슈/PR 모델은 "
                 f"GitHub 원격이 전제다 (계약 v3 s10)")
    # 보호 경로 밖이어야 한다: on-the-record 가 ~/.claude/plugins/ 아래 설치되면
    # ROOT/runs/work 도 그 아래가 되는데, 거긴 Claude Code 의 전역 sensitive
    # 경로라 역할 세션의 Write 가 전부 거부된다(실측: phase 2 가 코드 한 줄
    # 못 쓰고 $2.68 을 태웠다). 기본은 ~/.tokenmaxxxer/work, 오버라이드는
    # MUSTER_WORK_DIR.
    base = os.environ.get("MUSTER_WORK_DIR")
    work_base = Path(base) if base else Path.home() / ".tokenmaxxxer" / "work"
    # 이름은 origin 의 레포명에서 뽑는다 — 디렉토리 이름(slug)을 쓰면
    # 워크스페이스를 -C 로 다시 넘겼을 때 이름이 이중으로 붙는다(실측:
    # ...-issue-45-coding-issue-45-coding). origin 은 위에서 이미 읽었다.
    repo_name = re.sub(r"\.git$", "", origin.rstrip("/").rsplit("/", 1)[-1]) or slug(cwd)
    work = work_base / f"{repo_name}-issue-{issue}-{role}"
    # cwd 가 이미 이 (이슈,역할)의 워크스페이스면 그대로 쓴다 — 중첩 금지.
    if src == work.resolve():
        subprocess.run(["git", "-C", str(src), "fetch", "-q", "origin"],
                       capture_output=True, text=True)
        return str(src)
    if (work / ".git").exists():
        subprocess.run(["git", "-C", str(work), "fetch", "-q", "origin"],
                       capture_output=True, text=True)
        return str(work)
    work.parent.mkdir(parents=True, exist_ok=True)
    c = subprocess.run(["git", "clone", "-q", str(src), str(work)],
                       capture_output=True, text=True)
    if c.returncode != 0:
        sys.exit(f"작업 클론을 만들지 못했다: {c.stderr.strip()[:200]}")
    subprocess.run(["git", "-C", str(work), "remote", "set-url", "origin",
                    origin], capture_output=True, text=True)
    # https push 자격증명: 디스크에 토큰을 남기지 않고 env(GH_TOKEN)를 읽는
    # credential helper 를 작업 클론에만 심는다.
    try:
        ex = work / ".git" / "info" / "exclude"
        ex.parent.mkdir(parents=True, exist_ok=True)
        if ".muster-cache" not in (ex.read_text() if ex.exists() else ""):
            with ex.open("a") as fh:
                fh.write(".muster-cache/\n")
    except OSError:
        pass
    subprocess.run(["git", "-C", str(work), "config", "credential.helper",
                    "!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f"],
                   capture_output=True, text=True)
    subprocess.run(["git", "-C", str(work), "fetch", "-q", "origin"],
                   capture_output=True, text=True)
    return str(work)


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


def ensure_pushed(work: str, issue: int, role: str) -> None:
    """세션이 남긴 커밋을 호스트 환경에서 push 하고, PR 이 없으면 연다.

    샌드박스의 GitHub egress 는 환경마다 다르게 막힌다(https 프록시 403,
    ssh-only 정책, 키링 불가시 등 — 전부 실측). 산출물이 로컬 커밋으로만
    남으면 보드에 존재하지 않는 것과 같으므로, on-the-record 가 세션 종료 후
    바깥에서 릴레이한다. 역할이 스스로 push/PR 에 성공했으면 전부 no-op.
    """
    br = f"issue-{issue}/{role}"
    def git(*a):
        return subprocess.run(["git", "-C", work, *a], capture_output=True, text=True)
    if git("rev-parse", "--verify", "-q", br).returncode != 0:
        return
    ahead = git("rev-list", "--count", f"origin/{br}..{br}")
    unborn = ahead.returncode != 0          # 원격에 브랜치 자체가 없음
    n = ahead.stdout.strip() if ahead.returncode == 0 else "?"
    if unborn or n not in ("", "0"):
        r = git("push", "-q", "-u", "origin", br)
        if r.returncode != 0:
            print(f"[{role}] 호스트 push 실패: {r.stderr.strip()[:200]}", file=sys.stderr)
            return
        print(f"[{role}] 호스트에서 push 했다: {br}", file=sys.stderr)
    # "PR 있음" 판정은 OPEN 만 센다 — gh pr view <브랜치> 는 같은 브랜치의
    # 머지된 과거 PR(phase 1)도 잡아서, phase 2 의 새 PR 생성을 조용히
    # 건너뛰게 했다(실측: #60 머지 후 phase 2 커밋이 PR 없이 남았다).
    pr = subprocess.run(["gh", "pr", "list", "--head", br, "--state", "open",
                         "--json", "number", "--jq", "length"],
                        capture_output=True, text=True, cwd=work)
    has_open = pr.returncode == 0 and pr.stdout.strip() not in ("", "0")
    if not has_open:
        # 참조만 한다 — Closes 를 박으면 record PR 하나가 머지되는 순간
        # 이슈가 조기에 닫힌다(실측 직전 발견). 이슈 닫기는 라운드가 끝났을
        # 때 사람의 행위다 (계약 s8).
        body = (f"Part of #{issue}.\n\nOpened by on-the-record on behalf of the "
                f"{role} role session (sandbox egress relay); the branch "
                f"content is the role's own work.")
        c = subprocess.run(["gh", "pr", "create", "--head", br,
                            "--title", f"[{br}]",
                            "--body", body],
                           capture_output=True, text=True, cwd=work)
        if c.returncode == 0:
            print(f"[{role}] PR 을 열었다: {c.stdout.strip().splitlines()[-1] if c.stdout.strip() else br}",
                  file=sys.stderr)
        else:
            print(f"[{role}] PR 생성 실패: {c.stderr.strip()[:200]}", file=sys.stderr)


def _spawn_one(cwd: str, role: str, task: str, unattended: bool,
               issue: int | None = None, bounded: bool = False,
               stall_timeout_min: float = 5.0) -> int:
    """역할 하나를 띄우고, 무슨 일이 있었는지 원장에 남기고, 처분을 말한다.

    main() 과 drive() 가 같은 몸통을 쓴다 — 드라이버가 따로 스폰 경로를 들고
    있으면 둘이 갈라지고, 갈라진 쪽이 조용히 게이트 하나를 빠뜨린다.
    """
    spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())
    if issue is not None:
        # 격리 작업 클론에서 돈다 — 사용자의 체크아웃은 건드리지 않고,
        # 동시 스폰들이 서로의 index/브랜치를 밟지 않는다.
        cwd = issue_workspace(cwd, issue, role)
        br = checkout_issue_branch(cwd, issue, role)
        print(f"[{role}] 격리 작업 디렉토리: {cwd}  (브랜치 {br})", file=sys.stderr)
        # 원본(프리픽스 붙기 전) 맡길 일을 한 번만 저장 — 재스폰(다른 spawn.py
        # 프로세스일 수 있다)이 이걸 읽어 그대로 넘기면, 아래에서 프리픽스를
        # 다시 붙여도 중복되지 않는다 (이슈 #132).
        task_path = Path(str(cwd) + ".task.txt")
        if not task_path.exists():
            task_path.write_text(task, encoding="utf-8")
        task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
                f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n"
                f"완료의 정의: 변경이 이 브랜치에 **커밋**되고 push 되어 PR 로\n"
                f"제출된 상태다. 미커밋 변경은 존재하지 않는 것과 같다 —\n"
                f"세션을 끝내기 전에 반드시 커밋하라. push/PR 이 네트워크로\n"
                f"막히면 커밋까지는 해 둬라: on-the-record 가 밖에서 릴레이한다.\n"
                f"경고: 이 턴은 headless 이고 단발이다 — 세션이 끝나면 이 프로세스도\n"
                f"끝난다. run_in_background 로 넘긴 작업은 부모 턴이 끝나는 순간 함께\n"
                f"죽는다(백그라운드 워커가 커밋·push 를 대신 끝내줄 것이라고 가정하지\n"
                f"마라 — 실측된 실패 패턴이다). 모든 작업은 이 턴 안에서 직접 끝내라.\n\n") + task
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
        if issue is not None:
            # 툴체인 캐시를 워크스페이스 안으로 — go 등이 홈(~/Library/...)에
            # 캐시·설정을 쓰려다 샌드박스에 막혀 빌드가 승인 프롬프트로
            # 빠졌다(실측: phase 2 가 go build 를 한 번도 못 돌림). 쓰기가
            # 전부 cwd 아래로 오면 샌드박스 안에서 승인 없이 돈다.
            wcache = os.path.join(cwd, ".muster-cache")
            extra_env.update({
                "GOCACHE": os.path.join(wcache, "go-build"),
                "GOMODCACHE": os.path.join(wcache, "gomod"),
                "GOENV": os.path.join(wcache, "goenv"),
                "GOPATH": os.path.join(wcache, "gopath"),
                "XDG_CACHE_HOME": os.path.join(wcache, "xdg"),
                "npm_config_cache": os.path.join(wcache, "npm"),
                "PIP_CACHE_DIR": os.path.join(wcache, "pip"),
            })
            proxy = go_proxy_layer(s)
            if proxy:
                extra_env["GOPROXY"] = proxy
        before = board_snapshot(cwd)
        before_head = _git_head(cwd) if issue is not None else None
        t0 = time.monotonic()
        # stream-json 을 줄 단위로 받아 라이브 로그에 tee 한다 — "지금 뭐
        # 하는 중인가"가 세션이 끝나기 전에도 보이게. 최종 result 이벤트가
        # 옛 --output-format json 의 결과 오브젝트와 같은 필드를 든다.
        log_path = (Path(str(cwd) + ".session.log") if issue is not None
                    else ROOT / "runs" / "last-session.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{role}] 라이브 로그: {log_path}", file=sys.stderr)
        result = {}
        roster_key = f"issue-{issue}/{role}" if issue is not None else f"adhoc/{role}/{os.getpid()}"
        events_path = _events_path(cwd)
        offset_path = _offset_path(cwd)
        is_parent_return = False
        if bounded and issue is not None:
            _workspace_index_put(issue, role, str(cwd), str(log_path))
            # 부모(호출한 CLI 콜)는 이벤트 하나 또는 stall 시간까지만 기다리고
            # 리턴한다 — 자식이 세션을 끝까지 몰고 간다 (이슈 #114). setsid 로
            # 자식을 새 세션에 놓아, 부모가 속한 프로세스 그룹에 신호가 가도
            # 자식은 안 죽는다. settings 임시파일은 자식이 아직 쓰는 중이라
            # 부모 쪽 finally 에서 지우면 안 된다 (is_parent_return 이 막는다).
            #
            # 기다리기 전에 offset 을 지금의 파일 끝으로 민다. events.jsonl 은
            # append-only 이고 같은 워크스페이스로 재스폰하면 이전 세션의 줄이
            # 그대로 남아 있어서, offset 이 그 앞을 가리키면 새 스폰이 **과거
            # 이벤트**로 즉시 리턴한다 — 세션은 계속 도는데 호출자는 끝났다고
            # 듣는다. 실측 2026-07-30(core issue-53 phase 2): 78분 전 phase 1 이
            # 남긴 pr-opened 로 복귀했다. 이 스폰이 소비할 수 있는 것은 이
            # 세션이 낸 이벤트뿐이어야 한다 (이슈 #142).
            _write_offset(offset_path, _event_count(events_path))
            child_pid = os.fork()
            if child_pid > 0:
                is_parent_return = True
                return _await_bounded(events_path, offset_path,
                                       stall_timeout_min, log_path)
            os.setsid()
            # 부모(호출자)가 물려준 stdout/stderr 를 그대로 두면, 곧 띄울
            # claude 서브프로세스가 Popen() 에서 stdout/stderr 를 안 지정해도
            # 그 fd 를 그대로 상속해 세션 끝까지 파이프를 쥐고 있는다 —
            # 부모가 bounded 리턴으로 먼저 나가도, 호출자가 그 파이프의 EOF
            # 를 기다리고 있었다면 여전히 세션 끝까지 블록한다 (실측: 헌트로
            # 발견). devnull 로 갈아치워 파이프 소유권을 끊는다.
            devnull_fd = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull_fd, 0)
            os.dup2(devnull_fd, 1)
            os.dup2(devnull_fd, 2)
            os.close(devnull_fd)
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, env={**os.environ, **extra_env}, start_new_session=True,
        )
        roster_register(roster_key, {
            "pid": proc.pid, "role": role,
            "issue": issue, "ts": int(time.time()),
            "work": str(cwd), "log": str(log_path),
            "before_head": before_head,  # 이슈 #90 watchdog signal 4 재료
        })
        if issue is not None:
            # 크래시가 roster_remove/종료 이벤트 사이에서 나면 이 이전엔
            # events.jsonl 에 아무 흔적도 안 남았다(실측: survey.md 사건 #2) —
            # append-only 라 크래시에도 살아남는 이 기록이 session_end_verdict
            # 의 기준선이다 (이슈 #132).
            _append_event(events_path, "session-start",
                          {"pid": proc.pid, "ts": int(time.time())})
        try:
            proc.stdin.write(task)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        pr_seen = _prior_event_details(events_path, "pr-opened") if issue is not None else set()
        gate_refusal_seen = False
        # A URL the session **read** is indistinguishable from a PR it
        # **opened** unless the owner/repo is checked: octocat/Hello-World/pull/1
        # is GitHub's own documentation example and appears in gh help output.
        # 실측 2026-07-30 — 그 URL 하나로 pr-opened 가 서고 스폰이 조기 복귀했다
        # (이슈 #142). origin 을 못 읽으면 접두사는 None 이고 예전처럼 전부 받는다.
        pr_prefix = _origin_pr_prefix(cwd) if issue is not None else None
        with open(log_path, "w", encoding="utf-8") as lf:
            for line in proc.stdout:
                lf.write(line)
                lf.flush()
                if issue is not None:
                    for m in _PR_URL_RE.findall(line):
                        if pr_prefix and not m.startswith(pr_prefix):
                            continue
                        if m not in pr_seen:
                            pr_seen.add(m)
                            _append_event(events_path, "pr-opened", m)
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict) and obj.get("type") == "result":
                    result = obj
                    denials = result.get("permission_denials") or []
                    if issue is not None and not gate_refusal_seen and denials:
                        gate_refusal_seen = True
                        _append_event(events_path, "gate-refusal", str(denials)[:200])
        rc = proc.wait()
        roster_remove(roster_key)
    finally:
        if not is_parent_return:
            os.unlink(settings)
    if result.get("result"):
        print(result["result"])                  # 세션의 마지막 답 — 기존 UX
    elif not result:
        print(f"[{role}] 결과 이벤트를 받지 못했다 — 라이브 로그를 봐라: {log_path}",
              file=sys.stderr)

    after = board_snapshot(cwd)
    delta = sorted(p for p in set(before) | set(after)
                   if before.get(p) != after.get(p))
    # 사람 게이트에 막힌 줄을 자동으로 판별하던 표는 없다(이슈 #120) —
    # classify() 는 이제 이 경로로는 waiting-on-human 을 못 낸다.
    blocked: list = []

    uncommitted = []
    after_head = None
    if issue is not None:
        after_head = _git_head(cwd)
        st = subprocess.run(["git", "-C", cwd, "status", "--porcelain"],
                            capture_output=True, text=True)
        uncommitted = [l for l in st.stdout.splitlines() if l.strip()]
        if uncommitted:
            print(f"[{role}] 세션이 미커밋 변경 {len(uncommitted)}건을 남기고 "
                  f"끝났다 — 커밋되지 않은 작업은 PR 에 존재하지 않는다. "
                  f"같은 이슈로 재스폰하면 이 워크스페이스를 이어받아 커밋부터 "
                  f"끝낼 수 있다:\n  " + "\n  ".join(uncommitted[:10]),
                  file=sys.stderr)
        ensure_pushed(cwd, issue, role)
    gates = gate_report(cwd) + ownership_report(cwd, role, delta)
    outcome = classify(rc, result, delta, blocked)
    if outcome == "silent-failure" and uncommitted:
        outcome = "uncommitted-work"
    new_commit = issue is not None and _is_new_commit(cwd, before_head, after_head)
    already_delivered = False
    if issue is not None and outcome == "progressed" and not blocked and not new_commit:
        branch = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
        if branch:
            already_delivered = _pr_for_branch(Path(cwd), branch) is not None
    downgraded = fail_closed_downgrade(outcome, issue, blocked, new_commit, uncommitted,
                                       already_delivered)
    if downgraded != outcome:
        print(f"[{role}] 페일-클로즈드: progressed 로 자기보고 했지만 "
              f"새 커밋이 없고(before {before_head}, after {after_head})"
              + (f" 미커밋 변경 {len(uncommitted)}건도 남았다" if uncommitted else "")
              + f" — {outcome} 를 failed-no-commit 으로 깎는다. 기대한 것: "
              f"이 세션이 끝나기 전에 실제 커밋. 관찰한 것: 커밋 없음"
              + (" + 더러운 트리" if uncommitted else "") + ".",
              file=sys.stderr)
        outcome = downgraded
    denials = result.get("permission_denials") or []
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
    if bounded and issue is not None:
        # 자식(detach 된 프로세스)만 여기 닿는다 — 부모는 이미 fork 직후
        # _await_bounded 에서 리턴했다. 마지막 사건을 남기고 그대로 끝낸다.
        _append_event(events_path, "session-end", outcome)
        os._exit(rc if isinstance(rc, int) else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
