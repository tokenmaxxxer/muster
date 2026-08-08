"""기계 게이트 — 결정론적, LLM 0회.

리뷰 에이전트의 판단력에 기대지 않고 막을 수 있는 것만 여기서 막는다.
게이트가 막으면 재시도가 아니라 에스컬레이션이다(사람 호출).

원칙: **불확실하면 막는다.** 매니페스트를 파싱하지 못했거나 write-set 이 없으면
"검사할 게 없다"가 아니라 "검사할 수 없다"이고, 둘은 정반대 처분을 받아야 한다.

소급 금지 원칙(#362): 게이트는 아티팩트가 작성될 당시 준수했던 규칙을 나중에
바뀐 규칙으로 다시 검사해 실패시키지 않는다 — 작성자가 작성 시점에 대응할 수
없었던 이유로 실패하는 것은 재시도로 고칠 수 없는 실패이고, 그건 게이트가 아니라
함정이다. 판정은 항상 아티팩트 작성 시점의 규칙 기준이어야 한다.
"""
from __future__ import annotations
import fnmatch
import json
import os
import re
import shlex
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
PROTECTED_ROOT_FILES = {"protocol.md", "protocol.ko.md", "spawn.py",
                        "jenkinsfile", ".gitlab-ci.yml"}
# 역할 정의와 배선. 루트의 것만 — 앱의 src/roles/ 는 정상 자산이다.
PROTECTED_ROOT_DIRS = {"roles", "gates", "agents", "images", "profiles"}
# gates.py는 자신이 놓인 on-the-record 체크아웃을 이 파일의 위치로
# 찾는다 — spawn.py의 ROOT와 같은 자기위치 해석. 검사 대상 레포(work
# repo)의 경로와는 무관하다: roles/ 는 on-the-record 자산이지 보드
# 자산이 아니다.
ON_THE_RECORD_ROOT = Path(__file__).resolve().parent.parent
# 인증 계열은 좁게(auth.py 는 막고 author.py 는 통과), 자격증명 계열은 넓게.
# 자격증명의 미탐 비용은 유출이고 오탐 비용은 사람 확인 한 번이다.
PROTECTED_GLOBS = ["*.pem", "*.key", "*.p12", ".env", ".env.*",
                   "auth.*", "auth_*", "*secret*", "*credential*", "*.keystore"]

# docs/issue-<n>/reports/<role>.md — 보드 레코드 경로 형태. #100 의 record_enums
# 와 같은 형태를 쓴다 (아직 main 에 없어 여기서 독립 정의).
RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")
# 코드펜스 밖에서, 한 줄 전체가 태그 하나뿐인 경우만 잔여물로 본다.
_TOOL_TAG = re.compile(r"^\s*</?[A-Za-z][\w-]*(?:\s+[^<>]*)?/?>\s*$")

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


def _committed_changes_with_status(work: Path) -> list[tuple[str, str, str | None]]:
    """`_committed_changes` 와 같은 diff 를 status 를 보존한 채 낸다.

    (status, path, old_path) — rename/copy 는 old_path 에 원본 경로가 들어간다.
    그 외 상태는 old_path=None. record_fulfils_diff 가 A/D/R/C 를 구분해야 해서
    status 를 버리는 `_committed_changes` 로는 부족하다 — 같은 `-z` 파싱 루프를
    중복하지 않기 위해 별도 함수로 뺀다. 실패 시 예외를 던져 fail closed."""
    p = subprocess.run(
        ["git", "-C", str(work), "diff", "--name-status", "-z", f"{BASE}...HEAD"],
        capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            f"{BASE} 기준 diff 확인 불가 (fail closed): {p.stderr.strip()[:200]}")
    recs, out, i = p.stdout.split("\0"), [], 0
    while i < len(recs):
        status = recs[i]
        i += 1
        if not status or i >= len(recs):
            continue
        path = recs[i]
        i += 1
        old = None
        if status[0] in ("R", "C"):          # 다음 필드가 원본 경로
            old = path
            if i < len(recs):
                path = recs[i]
            i += 1
        out.append((status, path, old))
    return out


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


RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")


def record_frontmatter(text: str) -> dict[str, str]:
    """`spawn.frontmatter()` 와 동일한 얕은 `---` 파서. 의존성 없는 gates.py 가
    spawn.py 를 import 하지 않기 위해 여기서 따로 둔다(모듈 두 개가 서로 다른
    layout 가정을 갖는 이유는 gates.py 파일 상단 docstring 참고)."""
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


def record_enums(d: Path, cfg: dict) -> list[str]:
    """변경된 `docs/issue-<n>/reports/<role>.md` 의 frontmatter 필드가
    roles/<role>.json 의 record_fields 로 선언한 enum 안에 있는지 검사한다.

    선언되지 않은 필드는 검사하지 않는다(자유 텍스트로 남는다) — 선언된
    값만 write-time 에 강제하는 것이 요청의 범위다. role 정의를 못 읽으면
    "검사할 게 없다"가 아니라 "검사할 수 없다": 차단한다."""
    root = d / "work" if (d / "work").exists() else d
    try:
        files = changed_files(root)
    except RuntimeError as e:
        return [str(e)]
    bad = []
    for f in files:
        m = RECORD_PATH.match(f)
        if not m:
            continue
        role = m.group(1)
        role_file = ON_THE_RECORD_ROOT / "roles" / f"{role}.json"
        try:
            role_cfg = json.loads(role_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            bad.append(f"역할 정의를 읽을 수 없어 enum 을 검사할 수 없다: "
                       f"{role_file} (on-the-record 체크아웃: "
                       f"{ON_THE_RECORD_ROOT}) ({e})")
            continue
        declared = role_cfg.get("record_fields", {})
        record_file = root / f
        fm = record_frontmatter(
            record_file.read_text(encoding="utf-8-sig", errors="replace")
            if record_file.exists() else "")
        for field, allowed in declared.items():
            if field not in fm:
                continue
            value = fm[field]
            if value not in allowed:
                bad.append(
                    f"레코드 enum 위반: {f} 의 {field}={value!r} — "
                    f"roles/{role}.json 이 선언한 값 ({allowed}) 이 아니다")
    return bad


def _changed_records(work: Path) -> list[str]:
    """변경 파일 중 docs/issue-<n>/reports/<role>.md 형태만. 실패는 fail closed."""
    files = changed_files(work)
    return [f for f in files if RECORD_PATH.match(f)]


def record_wellformed_in(work: Path) -> list[str]:
    """`record_wellformed` 의 실질 검사. 라우터(d/"work")와 CI(repo 직접) 양쪽에서
    같은 로직을 쓰기 위해 작업 디렉터리를 인자로 받는다."""
    try:
        records = _changed_records(work)
    except RuntimeError as e:
        return [str(e)]
    bad = []
    for path in records:
        f = work / path
        if not f.exists():
            continue
        text = f.read_text()
        if not text.startswith("---"):
            bad.append(f"레코드 frontmatter 파싱 불가: {path} — 시작 구분자(`---`) "
                       "없음. loop_state/verdict 를 읽을 수 없어 오케스트레이터가 "
                       "이 기록을 조용히 못 읽는다.")
            continue
        if len(text.split("---", 2)) < 3:
            bad.append(f"레코드 frontmatter 파싱 불가: {path} — 닫는 구분자 없음. "
                       "loop_state/verdict 를 읽을 수 없어 오케스트레이터가 이 "
                       "기록을 조용히 못 읽는다.")
    return bad


def record_wellformed(d: Path, cfg: dict) -> list[str]:
    """변경된 docs/issue-<n>/reports/<role>.md 가 well-formed `---`
    frontmatter 블록을 가졌는지 검사한다. 파싱 실패는 '검사할 필드 없음'이
    아니라 차단 사유다."""
    return record_wellformed_in(d / "work")


def record_no_tool_residue_in(work: Path) -> list[str]:
    """`record_no_tool_residue` 의 실질 검사. 라우터/CI 양쪽에서 공유한다."""
    try:
        records = _changed_records(work)
    except RuntimeError as e:
        return [str(e)]
    bad = []
    for path in records:
        f = work / path
        if not f.exists():
            continue
        in_fence = False
        for lineno, line in enumerate(f.read_text().splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = _TOOL_TAG.match(line)
            if m:
                bad.append(f"레코드에 툴 태그 잔여물: {path}:{lineno} — "
                           f"{line.strip()!r}. 에이전트 툴 출력이 레코드 본문에 "
                           "새어들어왔다.")
    return bad


def record_no_tool_residue(d: Path, cfg: dict) -> list[str]:
    """레코드 본문에 툴 호출 트랜스크립트가 새어들어온 흔적(고립된 XML 태그
    한 줄)이 있는지 검사한다. 코드펜스 안은 제외한다."""
    return record_no_tool_residue_in(d / "work")


_DERIVED_TAG = re.compile(r"`derived:\s*\S.*?`")
_COUNT_RATIO = re.compile(r"\d+\s*(?:of|/)\s*\d+")
_COUNT_NOUN = re.compile(
    r"\d+\s+(?:detection\s+)?(?:items?|works?|checks?|cases?)\b")


def record_derived_counts_in(work: Path) -> list[str]:
    """`record_derived_counts` 의 실질 검사. 라우터/CI 양쪽에서 공유한다."""
    try:
        records = _changed_records(work)
    except RuntimeError as e:
        return [str(e)]
    bad = []
    for path in records:
        f = work / path
        if not f.exists():
            continue
        in_fence = False
        for lineno, line in enumerate(f.read_text().splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for pat in (_COUNT_RATIO, _COUNT_NOUN):
                for m in pat.finditer(line):
                    tail = line[m.end():]
                    if _DERIVED_TAG.match(tail.lstrip()):
                        continue
                    bad.append(
                        f"레코드에 근거 없는 개수 주장: {path}:{lineno} — "
                        f"{line.strip()!r}. 숫자가 코드펜스로 재현되지도, "
                        "`derived: ...` 인용도 없이 그냥 타이핑되어 있다.")
    return bad


def record_derived_counts(d: Path, cfg: dict) -> list[str]:
    """변경된 레코드 본문에서 "N of M"/"N items" 류 개수 주장이 코드펜스
    재현이나 `derived: ...` 인용 없이 맨몸으로 타이핑되어 있는지 검사한다
    (issue #333). 펜스 안 숫자는 도구 출력 재현으로 간주해 제외한다."""
    return record_derived_counts_in(d / "work")


_FULFILS_LINE = re.compile(r"^\s*[-*]?\s*fulfils:\s*(\S+)\s+(.*)$")
# `count <derivation> <N>` — derivation 은 마지막 공백-분리 토큰(정수) 앞의
# 나머지 전부다. glob/명령 둘 다 내부에 공백을 가질 수 있어(명령의 인자)
# `_FULFILS_LINE`처럼 `\S+`로 자를 수 없다.
_COUNT_CLAIM = re.compile(r"^(.*\S)\s+(-?\d+)$")


def _count_derivation(work: Path, derivation: str) -> int | None:
    """`count` claim 의 derivation 을 재실행해 정수를 낸다. 실행/파싱 불가면 None
    (호출자가 fail closed 로 처리한다).

    glob 메타문자(`*?[`)가 있으면 워크트리 기준 매치 개수. 없으면 셸 명령으로
    본다 — `shlex.split` 로 토큰화해 `shell=True` 없이 실행한다(파이프 등 셸
    문법은 지원하지 않는다 — no-footgun: 런타임 값으로 구성한 문자열을 셸에
    넘기지 않는다). stdout 이 정수가 아니면 파생을 신뢰할 수 없어 None."""
    if any(c in derivation for c in "*?["):
        return len(list(work.glob(derivation)))
    try:
        argv = shlex.split(derivation)
    except ValueError:
        return None
    if not argv:
        return None
    p = subprocess.run(argv, cwd=work, capture_output=True, text=True)
    if p.returncode != 0:
        return None
    out = p.stdout.strip()
    return int(out) if re.fullmatch(r"-?\d+", out) else None


def record_fulfils_diff(d: Path, cfg: dict) -> list[str]:
    """변경된 phase-2 레코드의 `fulfils: delete|create|move ...` 라인이 실제
    커밋 diff 와 일치하는지 검사한다 (issue #155).

    파싱 안 되는 `fulfils:` 라인은 "검사할 게 없다"가 아니라 그 자체로 차단
    사유다 (`dep_names()` 와 같은 fail-closed 원칙). `fulfils:` 라인이 하나도
    없는 레코드는 이 게이트가 아예 건드리지 않는다 — opt-in 마커다."""
    root = d / "work" if (d / "work").exists() else d
    try:
        records = _changed_records(root)
        status_changes = _committed_changes_with_status(root)
    except RuntimeError as e:
        return [str(e)]

    deleted = {p for s, p, old in status_changes if s[0] == "D"}
    created = {p for s, p, old in status_changes if s[0] == "A"}
    renamed_old = {old for s, p, old in status_changes if s[0] in ("R", "C") and old}
    renamed_pairs = {(old, p) for s, p, old in status_changes
                      if s[0] in ("R", "C") and old}

    bad = []
    for path in records:
        f = root / path
        if not f.exists():
            continue
        for lineno, line in enumerate(f.read_text().splitlines(), start=1):
            m = _FULFILS_LINE.match(line)
            if not m:
                continue
            kind, rest = m.group(1), m.group(2).strip()
            loc = f"{path}:{lineno}"
            if kind == "delete":
                claim_path = rest
                if not claim_path or not (claim_path in deleted or
                                           claim_path in renamed_old):
                    bad.append(f"fulfils 불일치: {loc} — 'delete {claim_path}' "
                               "claim 이 커밋 diff 에 D(또는 rename 원본)로 없다")
            elif kind == "create":
                claim_path = rest
                new_paths = created | {p for _, p in renamed_pairs}
                if not claim_path or claim_path not in new_paths:
                    bad.append(f"fulfils 불일치: {loc} — 'create {claim_path}' "
                               "claim 이 커밋 diff 에 A(또는 rename 대상)로 없다")
            elif kind == "move":
                mv = re.match(r"^(\S+)\s*->\s*(\S+)$", rest)
                if not mv or (mv.group(1), mv.group(2)) not in renamed_pairs:
                    bad.append(f"fulfils 불일치: {loc} — 'move {rest}' claim 이 "
                               "커밋 diff 의 rename 쌍과 일치하지 않는다")
            elif kind == "count":
                cm = _COUNT_CLAIM.match(rest)
                if not cm:
                    bad.append(f"fulfils 파싱 불가: {loc} — 'count {rest}' claim 이 "
                               "'<derivation> <N>' 형식이 아니다 (fail closed)")
                    continue
                derivation, n_str = cm.group(1), cm.group(2)
                actual = _count_derivation(root, derivation)
                if actual is None:
                    bad.append(f"fulfils 불일치: {loc} — 'count {derivation}' "
                               "파생을 재실행할 수 없다 (glob 매치 없음, 명령 실패, "
                               "또는 stdout 이 정수가 아니다)")
                elif actual != int(n_str):
                    bad.append(f"fulfils 불일치: {loc} — 'count {derivation} "
                               f"{n_str}' claim 이 재실행 결과({actual})와 다르다")
            else:
                bad.append(f"fulfils 파싱 불가: {loc} — 알 수 없는 claim 종류 "
                           f"{kind!r} (delete/create/move/count 만 허용, fail closed)")
    return bad


_REQ_HEADING = re.compile(r"^##\s+(R\d+)\s*$")
_REQ_FIELD = re.compile(r"^([a-z_]+):\s*(.*)$")
_REQ_REQUIRED = ("quote", "source_issue", "check", "status")


def _parse_requirements(text: str) -> tuple[list[dict[str, str]], list[str]]:
    """`docs/specs/requirements.md` 를 파싱한다. 필수 필드 누락은 "검사할 게
    없다"가 아니라 그 자체로 차단 사유다 (fail closed, issue #321)."""
    entries: list[dict[str, str]] = []
    bad: list[str] = []
    current_id: str | None = None
    current: dict[str, str] = {}

    def flush() -> None:
        if current_id is None:
            return
        missing = [f for f in _REQ_REQUIRED if f not in current]
        if missing:
            bad.append(f"요구사항 등록 파싱 불가: {current_id} — 필수 필드 누락 "
                       f"({', '.join(missing)})")
            return
        entries.append({"id": current_id, **current})

    for line in text.splitlines():
        m = _REQ_HEADING.match(line)
        if m:
            flush()
            current_id, current = m.group(1), {}
            continue
        m = _REQ_FIELD.match(line.strip())
        if m and current_id is not None:
            current[m.group(1)] = m.group(2).strip()
    flush()
    return entries, bad


def requirement_registry(d: Path, cfg: dict) -> list[str]:
    """`docs/specs/requirements.md` 의 각 항목이 가리키는 `check` 실행 가능
    아티팩트가 HEAD 에 실제로 존재하는지 검사한다 (issue #321).

    `check` 이 `UNVERIFIABLE: <reason>` 리터럴이면 경로 존재를 요구하지
    않는다 — #310 이 이미 인정한, 기계적으로 검사 불가능한 규칙의 표시다.
    레지스트리 파일이 없으면 "검사할 게 없다"로 통과시킨다 — 이 게이트
    자신이 그 파일을 만드는 최초 커밋에서 아직 없을 수 있기 때문이다.
    파싱 실패(필수 필드 누락)는 차단 사유다."""
    root = d / "work" if (d / "work").exists() else d
    reg = root / "docs" / "specs" / "requirements.md"
    if not reg.exists():
        return []
    entries, bad = _parse_requirements(
        reg.read_text(encoding="utf-8-sig", errors="replace"))
    for e in entries:
        check = e["check"]
        if check.startswith("UNVERIFIABLE:"):
            continue
        path = check.split("::", 1)[0].strip()
        if not path or not (root / path).exists():
            bad.append(f"요구사항 체크 소실: {e['id']} (issue #{e['source_issue']}) "
                       f"— check={check!r} 이 가리키는 경로가 HEAD 에 없다")
    return bad


_CHECKED_CLAIM_LINE = re.compile(
    r"^\s*[-*]\s*.+—\s*checked:\s*(\S+)\s*—\s*"
    r"result:\s*(pass|fail|unverifiable)(?::\s*(.+))?\s*$")
_ACCEPTANCE_HEADER = re.compile(r"^##\s*Acceptance verification\s*$", re.M)
_NEXT_HEADING = re.compile(r"^##\s+\S", re.M)
_TEST_DEF = re.compile(r"^def\s+(\w+)", re.M)


def _acceptance_section(text: str) -> str | None:
    """`## Acceptance verification` 헤딩 다음, 다음 `## ` 헤딩 전까지의 본문.
    헤딩이 없으면 None (섹션 자체가 없다는 뜻 — 빈 문자열과 구분해야 한다)."""
    m = _ACCEPTANCE_HEADER.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[:nxt.start()] if nxt else rest


def _terminal_loop_state(role_cfg: dict) -> str | None:
    """role_cfg 의 `record_fields.loop_state` 선언 목록에서 터미널 값.

    role 정의는 어떤 값이 터미널인지 별도 마킹하지 않는다 — 목록 순서 자체가
    진행 순서다(예: technical-feasibility 의 measuring→verdict, implementation
    의 scope-proposed→...→landed). 그래서 목록의 마지막 값을 터미널로 읽는다;
    단일 값 목록(예: defect-verification 의 cleared)도 그 하나가 곧 마지막이라
    같은 규칙으로 맞는다. 선언 자체가 없으면 None — 이 게이트가 그 레코드를
    건드리지 않는다(터미널을 모르면 강제할 기준이 없다)."""
    states = role_cfg.get("record_fields", {}).get("loop_state")
    return states[-1] if states else None


def parse_checked_claims(work: Path) -> list[tuple[str, str, str, str | None]]:
    """변경된 터미널 레코드의 `## Acceptance verification` 라인을 평탄화한다:
    (record_path, checked 대상, result, reason) 튜플 목록.

    구조 오류(섹션 없음/파싱 불가/unverifiable 사유 없음)는 여기서 걸러내지
    않는다 — `record_checked_claims` 가 그 사유로 이미 차단한다. 이 함수는
    `ci.py`의 CI 체크 크로스체크가 재사용할 파싱만 담당한다(중복 파싱 루프를
    두 번 만들지 않기 위해)."""
    try:
        files = changed_files(work)
    except RuntimeError:
        return []
    out = []
    for f in files:
        m = RECORD_PATH.match(f)
        if not m:
            continue
        role = m.group(1)
        role_file = ON_THE_RECORD_ROOT / "roles" / f"{role}.json"
        try:
            role_cfg = json.loads(role_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        terminal = _terminal_loop_state(role_cfg)
        if terminal is None:
            continue
        record_file = work / f
        text = (record_file.read_text(encoding="utf-8-sig", errors="replace")
                if record_file.exists() else "")
        if record_frontmatter(text).get("loop_state") != terminal:
            continue
        section = _acceptance_section(text)
        if section is None:
            continue
        for ln in section.splitlines():
            if not ln.strip():
                continue
            cm = _CHECKED_CLAIM_LINE.match(ln)
            if cm:
                out.append((f, cm.group(1), cm.group(2), cm.group(3)))
    return out


def record_checked_claims(d: Path, cfg: dict) -> list[str]:
    """변경된 phase-2 레코드가 role 의 터미널 `loop_state` 를 선언하면
    `## Acceptance verification` 섹션을 요구하고, 그 라인이 기계로 falsifiable
    한지 검사한다 (issue #331).

    `record_fulfils_diff` 와 달리 opt-in 마커가 아니다 — 터미널 상태 자체가
    이미 "이 작업이 끝났다"는 시스템 신호(스폰/보드가 그대로 읽는다)라서,
    그 신호에는 섹션 부재 자체가 차단 사유다. 여기서는 실행 없이 검증
    가능한 것만 본다: `path::test_name` 형태는 파일을 파싱해 정의 존재만
    확인한다(실행 아님) — CI 체크 이름의 statusCheckRollup 크로스체크는
    `ci.py` 쪽(레포 diff 만으로는 GitHub API 를 못 부른다)에서 한다."""
    root = d / "work" if (d / "work").exists() else d
    try:
        files = changed_files(root)
    except RuntimeError as e:
        return [str(e)]
    bad = []
    for f in files:
        m = RECORD_PATH.match(f)
        if not m:
            continue
        role = m.group(1)
        role_file = ON_THE_RECORD_ROOT / "roles" / f"{role}.json"
        try:
            role_cfg = json.loads(role_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            bad.append(f"역할 정의를 읽을 수 없어 checked-claims 를 검사할 수 "
                       f"없다: {role_file} (on-the-record 체크아웃: "
                       f"{ON_THE_RECORD_ROOT}) ({e})")
            continue
        terminal = _terminal_loop_state(role_cfg)
        if terminal is None:
            continue
        record_file = root / f
        text = (record_file.read_text(encoding="utf-8-sig", errors="replace")
                if record_file.exists() else "")
        if record_frontmatter(text).get("loop_state") != terminal:
            continue
        section = _acceptance_section(text)
        if section is None:
            bad.append(f"{f}: loop_state={terminal!r}(터미널)인데 "
                       "'## Acceptance verification' 섹션이 없다 — 완료 주장은 "
                       "기계로 확인되지 않으면 터미널 상태로 못 간다")
            continue
        lines = [ln for ln in section.splitlines() if ln.strip()]
        if not lines:
            bad.append(f"{f}: '## Acceptance verification' 섹션에 파싱 가능한 "
                       "라인이 없다")
            continue
        parsed = []
        for ln in lines:
            cm = _CHECKED_CLAIM_LINE.match(ln)
            if not cm:
                bad.append(f"{f}: Acceptance verification 라인 파싱 불가: "
                           f"{ln.strip()!r}")
                continue
            target, result, reason = cm.group(1), cm.group(2), cm.group(3)
            if result == "unverifiable" and not (reason and reason.strip()):
                bad.append(f"{f}: unverifiable 항목에 이유가 없다: "
                           f"{ln.strip()!r}")
                continue
            parsed.append((target, result))
        for target, result in parsed:
            if result != "pass" or "::" not in target:
                continue
            path, _, name = target.partition("::")
            test_file = root / path
            if not test_file.exists():
                bad.append(f"{f}: checked 대상 파일이 없다: {target}")
                continue
            defs = _TEST_DEF.findall(test_file.read_text())
            if name not in defs:
                bad.append(f"{f}: checked 대상 테스트가 파일에 없다: {target}")
    return bad


BRANCH_ROLE = re.compile(r"^issue-[^/]+/([^/]+)$")
# 항상 허용되는 레코드 경로 — 어떤 write_scope 선언·오버라이드도 이걸 못
# 지운다 (issue-149 item 5: 기록 의무는 무조건 살아남는다).
_WRITE_SCOPE_OVERRIDE = re.compile(
    r"^\s*[-*]\s*write:\s*([^:\s]+)\s*:\s*(\S+)", re.M)


def _always_writable(role: str) -> list[str]:
    return [f"docs/issue-*/reports/{role}.md",
            f"docs/issue-*/reports/{role}/**",
            "docs/issue-*/proposals/**"]


def _write_scope_overrides(work: Path) -> dict[str, list[str]]:
    """보드 레포 루트의 `docs/specs/write_scope.md` 를 파싱한다.

    `writeset()` 가 이미 쓰는 `- write: <값>` 줄 형태를 역할 접두어로 확장한
    것 — 새 포맷을 만들지 않고 검증된 파싱을 재사용한다."""
    f = work / "docs" / "specs" / "write_scope.md"
    if not f.exists():
        return {}
    out: dict[str, list[str]] = {}
    for role, glob in _WRITE_SCOPE_OVERRIDE.findall(f.read_text()):
        out.setdefault(role, []).append(glob)
    return out


def role_scope(work: Path, branch: str) -> list[str]:
    """PR diff 가 브랜치로 선언된 역할의 `write_scope` 안에 있는지 검사한다.

    역할을 브랜치 이름(`issue-<n>/<role>`)에서 구조적으로 해석한다 —
    `board-gate.sh`/`record_enums()` 가 이미 쓰는 같은 방식. 브랜치가 그
    형태가 아니거나, 해당 role 정의를 못 읽거나, `write_scope` 가 선언되지
    않았으면 "검사할 게 없다"가 아니라 "검사할 수 없다": fail closed.
    보드 레포의 `docs/specs/write_scope.md` 오버라이드가 있으면 그 역할의
    글롭 목록을 통째로 대체하지만, 레코드/제안 경로(`_always_writable`)는
    오버라이드 뒤에도 항상 합집합으로 남는다 — 어떤 오버라이드도 기록 의무를
    지울 수 없다."""
    m = BRANCH_ROLE.match(branch)
    if not m:
        return [f"브랜치 이름에서 역할을 해석할 수 없다 (fail closed): "
                f"{branch!r} — issue-<n>/<role> 형태가 아니다"]
    role = m.group(1)
    role_file = ON_THE_RECORD_ROOT / "roles" / f"{role}.json"
    try:
        role_cfg = json.loads(role_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"역할 정의를 읽을 수 없어 write_scope 를 검사할 수 없다: "
                f"{role_file} (on-the-record 체크아웃: {ON_THE_RECORD_ROOT}) ({e})"]
    if "write_scope" not in role_cfg:
        return [f"roles/{role}.json 에 write_scope 선언이 없다 (fail closed)"]
    overrides = _write_scope_overrides(work)
    allowed = overrides.get(role, list(role_cfg["write_scope"]))
    allowed = allowed + _always_writable(role)
    try:
        files = changed_files(work)
    except RuntimeError as e:
        return [str(e)]
    return [f"write_scope 이탈: {f} (역할 {role}, 허용: {', '.join(allowed)})"
            for f in files if not any(fnmatch.fnmatch(f, a) for a in allowed)]


def orphaned_references(work: Path, base: str = BASE) -> list[tuple[str, str]]:
    """PR 이 삭제·개명(구경로)한 경로가 diff 밖 어딘가에서 아직 참조되는지 찾는다.

    (issue #330) 세 사고(#285→#296/#297, #297→#313, #140→#147) 공통점: 각
    PR 은 자기 write-set 만 검사했고, 그 write-set 밖에서 옛 경로를 참조하는
    코드는 아무도 보지 않았다. `_committed_changes_with_status` 로 삭제(D)
    또는 rename 의 구경로를 모으고, PR 이 건드리지 않은 나머지 추적 파일에서
    그 경로 문자열을 그렙한다 — 발견되면 (구경로, 참조한 파일) 쌍을 낸다.

    grep 실패(파일이 바이너리이거나 읽기 불가)는 조용히 건너뛴다 — 이 게이트가
    잡으려는 건 텍스트 참조지 바이너리 매치가 아니다."""
    changes = _committed_changes_with_status(work)
    old_paths = [old if old is not None else path
                 for (status, path, old) in changes
                 if status.startswith("D") or old is not None]
    if not old_paths:
        return []
    touched = {path for _, path, _ in changes} | {old for _, _, old in changes if old}
    p = subprocess.run(
        ["git", "-C", str(work), "ls-files"],
        capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"저장소 파일 목록 확인 불가 (fail closed): {p.stderr.strip()[:200]}")
    tracked = [f for f in p.stdout.splitlines() if f and f not in touched]
    hits: list[tuple[str, str]] = []
    for old_path in old_paths:
        g = subprocess.run(
            ["git", "-C", str(work), "grep", "-l", "-F", old_path, "--"] + tracked,
            capture_output=True, text=True)
        if g.returncode not in (0, 1):
            continue
        for ref_file in g.stdout.splitlines():
            if ref_file:
                hits.append((old_path, ref_file))
    return hits


def reach_check(work: Path, record_text: str, base: str = BASE) -> list[str]:
    """`orphaned_references` 의 각 히트가 `## Reach` 섹션에 이름으로 언급됐는지 검사.

    (issue #330) #310 이 요구하는 실행 가능한 산출물 — "리치를 적어라"는 프로즈
    조언이 아니라, 옛 경로가 실제로 diff 밖에서 참조되는데 레코드가 그걸 언급하지
    않으면 이 함수가 실패 문자열을 낸다. 매칭은 옛 경로 전체 문자열 또는 그 상위
    디렉토리 이름이 `## Reach` 섹션 본문에 등장하는지로 판단한다 — 정확한 문장
    형식을 강제하지 않는다(그러면 프로즈 파싱 취약점이 된다), 언급 자체만 본다."""
    hits = orphaned_references(work, base)
    if not hits:
        return []
    m = re.search(r"^##\s*Reach\s*$(.*?)(?=^##\s|\Z)", record_text, re.M | re.S)
    reach_body = m.group(1) if m else ""
    bad = []
    for old_path, ref_file in hits:
        parent = old_path.rsplit("/", 1)[0] if "/" in old_path else old_path
        if old_path not in reach_body and parent not in reach_body:
            bad.append(
                f"미언급 리치: {ref_file} 가 삭제/개명된 경로 {old_path} 를 "
                f"참조하지만 레코드의 `## Reach` 섹션에 언급되지 않았다")
    return bad


_TEST_BASENAME = re.compile(r"^(test_.+|.+_test)\.py$")


def duplicate_test_basenames(root: Path) -> list[str]:
    """저장소 전체를 훑어, `__init__.py` 없는(= pytest가 패키지 경계 없이
    최상위 이름공간에 얹는) 디렉터리들 사이에서 같은 테스트 모듈 베이스네임이
    겹치는지 찾는다.

    (issue #398) diff 가 아니라 파일트리 전체를 본다 — merge 가 일어나기
    전에도, PR 단독으로도 이 충돌 모양을 잡아야 한다는 이슈의 요구사항
    그대로. `gates/test_gates.py` 와 루트 `test_gates.py` 충돌(#330/#337)이
    각 PR 단독 검사에서는 안 보이고 merge 후에야 `pytest -q` 수집 자체가
    깨지는 걸로 드러났다."""
    by_basename: dict[str, list[str]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        if "__init__.py" in filenames:
            continue
        rel_dir = os.path.relpath(dirpath, root)
        for fn in filenames:
            if _TEST_BASENAME.match(fn):
                rel_path = fn if rel_dir == "." else f"{rel_dir}/{fn}"
                by_basename.setdefault(fn, []).append(rel_path)
    bad = []
    for basename, paths in sorted(by_basename.items()):
        if len(paths) > 1:
            bad.append(
                f"중복 테스트 모듈 베이스네임: {basename} — "
                f"{', '.join(sorted(paths))} (패키지 경계(`__init__.py`) 없이 "
                "같은 이름이라 pytest 수집이 충돌한다)")
    return bad


def duplicate_test_basenames_gate(d: Path, cfg: dict) -> list[str]:
    return duplicate_test_basenames(d / "work")


ALL = {"writeset": writeset, "deps": deps,
       "record_enums": record_enums,
       "record_wellformed": record_wellformed,
       "record_no_tool_residue": record_no_tool_residue,
       "record_derived_counts": record_derived_counts,
       "record_fulfils_diff": record_fulfils_diff,
       "duplicate_test_basenames": duplicate_test_basenames_gate,
       "requirement_registry": requirement_registry,
       "record_checked_claims": record_checked_claims}


def check(names: list[str], d: Path, cfg: dict) -> list[str]:
    bad = []
    for n in names:
        bad += ALL[n](d, cfg)
    return bad
