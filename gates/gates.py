"""기계 게이트 — 결정론적, LLM 0회.

리뷰 에이전트의 판단력에 기대지 않고 막을 수 있는 것만 여기서 막는다.
게이트가 막으면 재시도가 아니라 에스컬레이션이다(사람 호출).

원칙: **불확실하면 막는다.** 매니페스트를 파싱하지 못했거나 write-set 이 없으면
"검사할 게 없다"가 아니라 "검사할 수 없다"이고, 둘은 정반대 처분을 받아야 한다.
"""
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

# 비교 기준. 라우터는 항상 origin/main 에서 워크트리를 만들지만, CI 에서는 PR 의
# base 가 main 이 아닐 수 있다. 하드코딩하면 그런 PR 에서 diff 가 통째로 실패하고
# fail closed 가 발동해 **정상 PR 이 전부 막힌다** — 게이트가 꺼지는 경로다.
BASE = os.environ.get("GATE_BASE", "origin/main")

# 변경되면 무조건 사람에게. 경로를 세그먼트로 쪼개 판정한다 — fnmatch 를 전체 경로에
# 쓰면 `**` 를 이해하지 못해 루트 파일을 놓치고, `*.yml` 류는 정상 설정까지 막는다.
# 비교는 전부 소문자로 (SecretConfig.py 를 놓치지 않기 위해).
PROTECTED_DIRS = {".github", ".circleci", "migrations", "auth"}
# 파이프라인이 자기 규칙을 다시 쓸 수 없어야 한다.
PROTECTED_ROOT_FILES = {"protocol.md", "spawn.py", "jenkinsfile", ".gitlab-ci.yml"}
# 역할 정의와 배선. 루트의 것만 — 앱의 src/roles/ 는 정상 자산이다.
PROTECTED_ROOT_DIRS = {"roles", "gates", "agents", "images", "profiles"}
# 인증 계열은 좁게(auth.py 는 막고 author.py 는 통과), 자격증명 계열은 넓게.
# 자격증명의 미탐 비용은 유출이고 오탐 비용은 사람 확인 한 번이다.
PROTECTED_GLOBS = ["*.pem", "*.key", "*.p12", ".env", ".env.*",
                   "auth.*", "auth_*", "*secret*", "*credential*", "*.keystore"]

REGISTRY = {
    "requirements.txt": "https://pypi.org/pypi/{}/json",
    "package.json": "https://registry.npmjs.org/{}",
}
# 따라갈 수 없는 간접 참조. 검사 불가이므로 통과시키지 않는다.
INDIRECT = re.compile(r"^\s*(-r|--requirement|-c|--constraint)\b")
# 레지스트리 범위 형태만 허용 (^1.2.3, ~1.0, 1.x, >=2 <3, latest, *, workspace:* ...).
# git+https:// / file: / tarball URL / github:owner/repo 같은 직접 참조는 이름은
# 레지스트리에 있어도 실제 설치되는 코드가 임의 출처라 이름 검사를 우회한다.
NPM_RANGE = re.compile(r"^(workspace:)?[\w.\-+*<>=~^| ]+$")


def is_protected(path: str) -> bool:
    parts = path.lower().split("/")
    if PROTECTED_DIRS & set(parts[:-1]):
        return True
    if len(parts) > 1 and parts[0] in PROTECTED_ROOT_DIRS:
        return True
    if len(parts) == 1 and parts[0] in PROTECTED_ROOT_FILES:
        return True
    return any(fnmatch.fnmatch(parts[-1], g) for g in PROTECTED_GLOBS)


def _committed_changes(work: Path) -> list[str]:
    """origin/main...HEAD 커밋 diff. rename 은 원본/대상 둘 다 낸다.

    `git status` 만 보면 워커가 자기 작업을 커밋해버린 순간 게이트가 못 본다 —
    write-set/보호 경로 검사가 통째로 무력화된다(실제 재현 확인됨). 그래서 커밋된
    변경도 따로 훑는다. `--name-status -z` 는 `git status -z` 와 필드 구성이 달라서
    상태와 경로가 같은 레코드가 아니라 별도 NUL 필드다 — rename 은
    `R100\0old\0new\0` 세 필드로 나온다.

    origin/main 을 못 찾거나 diff 자체가 실패하면 "변경 없음"이 아니라 "검사
    불가"다. 워킹트리만 보고 조용히 넘어가면 fail-open 이 되므로 예외를 던져
    호출자가 막게 한다.
    """
    p = subprocess.run(
        ["git", "-C", str(work), "diff", "--name-status", "-z", f"{BASE}...HEAD"],
        capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            f"{BASE} 기준 diff 확인 불가 (fail closed): {p.stderr.strip()[:200]}")
    recs, files, i = p.stdout.split("\0"), [], 0
    while i < len(recs):
        status = recs[i]
        i += 1
        if not status or i >= len(recs):
            continue
        files.append(recs[i])
        i += 1
        if status[0] in ("R", "C"):          # 다음 필드가 원본 경로
            if i < len(recs) and recs[i]:
                files.append(recs[i])
            i += 1
    return files


def _worktree_changes(work: Path) -> list[str]:
    """워킹트리/인덱스 변경. rename 은 원본과 대상을 **둘 다** 낸다.

    `--porcelain` 의 사람용 표기는 rename 을 `R  old -> new` 한 줄로 접는데, 그걸
    경로 하나로 취급하면 `git mv allowed.txt .github/x.js` 가 보호 경로 검사와
    write-set 검사를 동시에 빠져나간다(문자열이 `allowed*` 에는 매치되고, 세그먼트
    분리로는 `.github` 가 나오지 않는다). `-z` 는 접지 않고 따옴표도 쓰지 않는다.
    """
    out = subprocess.run(
        ["git", "-C", str(work), "status", "--porcelain", "-z", "-uall"],
        capture_output=True, text=True).stdout
    recs = out.split("\0")
    files, i = [], 0
    while i < len(recs):
        rec = recs[i]
        i += 1
        if not rec:
            continue
        status, path = rec[:2], rec[3:]
        files.append(path)
        if "R" in status or "C" in status:   # 다음 레코드가 원본 경로
            if i < len(recs) and recs[i]:
                files.append(recs[i])
            i += 1
    return files


def changed_files(work: Path) -> list[str]:
    """변경된 경로 전부: 커밋(origin/main...HEAD) + 워킹트리 합집합.

    커밋 diff 가 실패하면(주로 origin/main 부재) RuntimeError 를 던진다 — 호출자가
    fail closed 로 처리해야 한다.
    """
    return list(dict.fromkeys(_committed_changes(work) + _worktree_changes(work)))


def writeset(d: Path, cfg: dict) -> list[str]:
    """보호 경로 변경 차단 + spec 이 선언한 write-set 준수.

    write-set 이 선언되지 않으면 fail closed 다. 자율 머지 파이프라인에서 "범위를
    말하지 않았으니 아무 데나 써도 된다"는 성립하지 않는다.
    """
    try:
        files = changed_files(d / "work")
    except RuntimeError as e:
        return [str(e)]
    bad = [f"보호 경로 변경: {f}" for f in files if is_protected(f)]

    spec = d / "spec.md"
    if not spec.exists():
        return bad + ["spec 이 없어 write-set 을 검사할 수 없다"] if files else bad
    allowed = re.findall(r"^\s*[-*]\s*write:\s*(\S+)", spec.read_text(), re.M)
    if not allowed:
        return bad + ["spec 에 write-set 선언이 없다 (fail closed)"]
    bad += [f"write-set 이탈: {f} (허용: {', '.join(allowed)})"
            for f in files if not any(fnmatch.fnmatch(f, a) for a in allowed)]
    return bad


def dep_names(manifest: str, text: str) -> set[str]:
    """매니페스트 본문 → 의존성 이름 집합. 파싱 불가면 ValueError.

    줄 단위 diff 파싱보다 형식 변화에 강하다. 빈 집합과 "못 읽었다"를 구분하는 것이
    핵심 — 깨진 package.json 을 빈 집합으로 취급하면 새 의존성이 0개로 보여 통과한다.
    버전 스펙이 레지스트리 범위가 아닌 경우도 "못 읽었다"와 같은 취급이다 — 이름만
    보고 통과시키는 `deps()` 가 실제 설치 출처를 못 보게 되므로 여기서 막아야
    `dep_names` 가 반환하는 이름 집합이 "레지스트리에서 받는 게 맞다"를 보장한다.
    """
    if manifest == "package.json":
        try:
            j = json.loads(text or "{}")
        except json.JSONDecodeError as e:
            raise ValueError(f"package.json 파싱 실패: {e}") from e
        names = set()
        for key in ("dependencies", "devDependencies",
                    "optionalDependencies", "peerDependencies"):
            for name, spec in j.get(key, {}).items():
                if not NPM_RANGE.match(str(spec)):
                    raise ValueError(f"레지스트리 범위가 아님: {name}={spec}")
                names.add(name)
        return names
    names = set()
    for line in (text or "").splitlines():
        if INDIRECT.match(line):
            raise ValueError(f"따라갈 수 없는 간접 참조: {line.strip()}")
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        if "://" in line:   # 바로 URL 이거나 `pkg @ https://...` 직접 참조
            raise ValueError(f"레지스트리가 아닌 직접 참조: {line}")
        names.add(re.split(r"[=<>!~\[; ]", line)[0].strip())
    return names - {""}


def parse_new_deps(work: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """(새 의존성 목록, 파싱 실패 사유). 실패는 통과가 아니라 차단 사유다."""
    out, errs = [], []
    try:
        changed = changed_files(work)
    except RuntimeError as e:
        return out, [str(e)]
    for path in changed:
        manifest = path.split("/")[-1]
        if manifest not in REGISTRY:
            continue
        base = subprocess.run(
            ["git", "-C", str(work), "show", f"{BASE}:{path}"],
            capture_output=True, text=True).stdout
        current = (work / path).read_text() if (work / path).exists() else ""
        try:
            new = dep_names(manifest, current) - dep_names(manifest, base)
        except ValueError as e:
            errs.append(f"{path}: {e}")
            continue
        out += [(manifest, n) for n in sorted(new)]
    return out, errs


def registry_status(url: str) -> str:
    """HTTP 상태 코드 문자열. curl 을 쓰는 이유는 시스템 CA 저장소를 그대로 쓰기
    위해서다 — urllib 은 macOS 파이썬에서 CA 번들이 없어 실존 패키지도 검증 실패로
    떨어뜨렸다(= 모든 의존성을 막는 오탐)."""
    p = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
         "--max-time", "10", "-I", url],
        capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else f"err:{p.stderr.strip()[:80]}"


def deps(d: Path, cfg: dict) -> list[str]:
    """환각 패키지 차단 — 레지스트리 실존 확인. 불확실하면 막는다."""
    new, bad = parse_new_deps(d / "work")
    for manifest, name in new:
        code = registry_status(REGISTRY[manifest].format(name))
        if code == "404":
            bad.append(f"존재하지 않는 패키지: {name} ({manifest})")
        elif not code.startswith("2"):
            bad.append(f"레지스트리 확인 불가: {name} → {code}")
    return bad


ALL = {"writeset": writeset, "deps": deps}


def check(names: list[str], d: Path, cfg: dict) -> list[str]:
    bad = []
    for n in names:
        bad += ALL[n](d, cfg)
    return bad
