"""기계 게이트 — 결정론적, LLM 0회.

리뷰 에이전트의 판단력에 기대지 않고 막을 수 있는 것만 여기서 막는다.
게이트가 막으면 재시도가 아니라 에스컬레이션이다(사람 호출).

원칙: **불확실하면 막는다.** 매니페스트를 파싱하지 못했거나 write-set 이 없으면
"검사할 게 없다"가 아니라 "검사할 수 없다"이고, 둘은 정반대 처분을 받아야 한다.
"""
import fnmatch
import json
import re
import subprocess
from pathlib import Path

# 변경되면 무조건 사람에게. 경로를 세그먼트로 쪼개 판정한다 — fnmatch 를 전체 경로에
# 쓰면 `**` 를 이해하지 못해 루트 파일을 놓치고, `*.yml` 류는 정상 설정까지 막는다.
# 비교는 전부 소문자로 (SecretConfig.py 를 놓치지 않기 위해).
PROTECTED_DIRS = {".github", ".circleci", "migrations", "auth"}
PROTECTED_ROOT_FILES = {"adapters.yml", "adapters.e2e.yml", "pipeline.md",
                        "jenkinsfile", ".gitlab-ci.yml"}
PROTECTED_ROOT_DIRS = {"profiles"}          # 루트의 것만. 앱의 src/profiles/ 는 정상
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


def is_protected(path: str) -> bool:
    parts = path.lower().split("/")
    if PROTECTED_DIRS & set(parts[:-1]):
        return True
    if len(parts) > 1 and parts[0] in PROTECTED_ROOT_DIRS:
        return True
    if len(parts) == 1 and parts[0] in PROTECTED_ROOT_FILES:
        return True
    return any(fnmatch.fnmatch(parts[-1], g) for g in PROTECTED_GLOBS)


def changed_files(work: Path) -> list[str]:
    """변경된 경로 전부. rename 은 원본과 대상을 **둘 다** 낸다.

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


def writeset(d: Path, cfg: dict) -> list[str]:
    """보호 경로 변경 차단 + spec 이 선언한 write-set 준수.

    write-set 이 선언되지 않으면 fail closed 다. 자율 머지 파이프라인에서 "범위를
    말하지 않았으니 아무 데나 써도 된다"는 성립하지 않는다.
    """
    files = changed_files(d / "work")
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
    """
    if manifest == "package.json":
        try:
            j = json.loads(text or "{}")
        except json.JSONDecodeError as e:
            raise ValueError(f"package.json 파싱 실패: {e}") from e
        names = set()
        for key in ("dependencies", "devDependencies",
                    "optionalDependencies", "peerDependencies"):
            names |= set(j.get(key, {}))
        return names
    names = set()
    for line in (text or "").splitlines():
        if INDIRECT.match(line):
            raise ValueError(f"따라갈 수 없는 간접 참조: {line.strip()}")
        line = line.split("#")[0].strip()
        if line and not line.startswith("-"):
            names.add(re.split(r"[=<>!~\[; ]", line)[0].strip())
    return names - {""}


def parse_new_deps(work: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """(새 의존성 목록, 파싱 실패 사유). 실패는 통과가 아니라 차단 사유다."""
    out, errs = [], []
    for path in changed_files(work):
        manifest = path.split("/")[-1]
        if manifest not in REGISTRY:
            continue
        base = subprocess.run(
            ["git", "-C", str(work), "show", f"origin/main:{path}"],
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
