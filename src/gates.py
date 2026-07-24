"""기계 게이트 — 결정론적, LLM 0회.

리뷰 에이전트의 판단력에 기대지 않고 막을 수 있는 것만 여기서 막는다.
게이트가 막으면 재시도가 아니라 에스컬레이션이다(사람 호출).
"""
import fnmatch
import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

# 변경되면 무조건 사람에게. 파이프라인이 자기 규칙을 다시 쓸 수 없어야 한다.
PROTECTED = [
    ".github/*", "*.yml", "*.yaml",          # CI 설정
    "adapters.yml", "pipeline.md", "profiles/*",  # 파이프라인 자신
    "*.pem", "*.key", ".env*",               # 시크릿
    "**/auth*", "**/migrations/*",           # 인증·마이그레이션
]

REGISTRY = {
    "requirements.txt": "https://pypi.org/pypi/{}/json",
    "package.json": "https://registry.npmjs.org/{}",
}


def changed_files(work: Path) -> list[str]:
    # -uall: 미추적 디렉터리를 접지 않고 파일 단위로 편다. 접히면 write-set 대조가
    # 디렉터리 이름과 비교하게 되어 허용/차단 판정이 둘 다 틀린다.
    p = subprocess.run(["git", "-C", str(work), "status", "--porcelain", "-uall"],
                       capture_output=True, text=True)
    return [ln[3:].strip() for ln in p.stdout.splitlines() if ln.strip()]


def writeset(d: Path, cfg: dict) -> list[str]:
    """보호 경로 변경 차단 + spec 이 선언한 write-set 준수."""
    files = changed_files(d / "work")
    bad = [f"보호 경로 변경: {f}" for f in files
           if any(fnmatch.fnmatch(f, pat) for pat in PROTECTED)]

    spec = d / "spec.md"
    if spec.exists():
        allowed = re.findall(r"^\s*[-*]\s*write:\s*(\S+)", spec.read_text(), re.M)
        if allowed:
            bad += [f"write-set 이탈: {f} (허용: {', '.join(allowed)})"
                    for f in files
                    if not any(fnmatch.fnmatch(f, a) for a in allowed)]
    return bad


def dep_names(manifest: str, text: str) -> set[str]:
    """매니페스트 본문 → 의존성 이름 집합. 줄 단위 diff 파싱보다 형식 변화에 강하다."""
    if manifest == "package.json":
        try:
            j = json.loads(text or "{}")
        except json.JSONDecodeError:
            return set()
        return set(j.get("dependencies", {})) | set(j.get("devDependencies", {}))
    names = set()
    for line in (text or "").splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("-"):
            names.add(re.split(r"[=<>!~\[; ]", line)[0].strip())
    return names - {""}


def parse_new_deps(work: Path) -> list[tuple[str, str]]:
    """base 대비 새로 추가된 의존성만 (manifest, name) 으로. 네트워크 없음."""
    out = []
    for path in changed_files(work):
        manifest = path.split("/")[-1]
        if manifest not in REGISTRY:
            continue
        base = subprocess.run(
            ["git", "-C", str(work), "show", f"origin/main:{path}"],
            capture_output=True, text=True).stdout
        current = (work / path).read_text() if (work / path).exists() else ""
        for name in sorted(dep_names(manifest, current) - dep_names(manifest, base)):
            out.append((manifest, name))
    return out


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
    """환각 패키지 차단 — 레지스트리에 실존하는지 확인. 불확실하면 막는다(fail closed)."""
    bad = []
    for manifest, name in parse_new_deps(d / "work"):
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
