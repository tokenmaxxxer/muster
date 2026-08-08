#!/usr/bin/env python3
"""주장 언어 스캐너 — issue #476 H1.

레코드/PR 본문에 "reproduced"/"verified"/"passed" 류 주장이 나오면, 그
주장이 실행 가능한 근거(코드펜스 또는 `Repro:`/`Verify:` 줄)를 곁에
데리고 있는지, 그리고 그 근거가 실제 diff/repo 안의 대상(파일 경로,
함수/모듈 이름)을 가리키는지를 실행 전에 검사한다. 둘 중 하나라도
없으면 hard fail — after-proposal hunt 가 재현한 "인접 커맨드 없는
주장" bypass 를 실행 이전 단계에서 닫는다.

  python3 gates/claim_scan.py <파일> [--repo <경로>]
  python3 gates/claim_scan.py --pr <번호> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# 근거를 찾는 창 — 주장 줄 기준 앞뒤 몇 줄까지 인접으로 본다.
ADJACENCY_LINES = 5

CLAIM_RE = re.compile(
    r"\b(reproduced|verified|confirmed|passed|tests?\s+pass(?:es|ed)?|"
    r"repro(?:duces|duced)?)\b",
    re.IGNORECASE,
)
EVIDENCE_MARKER_RE = re.compile(r"^\s*(repro|verify)\s*:", re.IGNORECASE)
# 근거가 가리키는 "대상" 후보: 파일 경로, 점 표기 모듈/함수, 언더스코어를
# 포함한 식별자. 커맨드 자체(예: `python3 -m pytest`)가 아니라 그 커맨드가
# 지목하는 구체적 대상을 뽑아 diff/repo 존재 여부를 검사하기 위해서다.
TARGET_RE = re.compile(
    r"[A-Za-z0-9_./-]*(?:/[A-Za-z0-9_.-]+|[A-Za-z0-9_]+\.[A-Za-z0-9_]+|"
    r"[A-Za-z0-9_]{3,}::[A-Za-z0-9_]+)"
)
FENCE_RE = re.compile(r"^\s*```")


@dataclass(frozen=True)
class Finding:
    claim: str
    line_no: int
    line_text: str
    reason: str


def _fence_spans(lines: list[str]) -> list[tuple[int, int]]:
    """코드펜스로 감싸인 (시작, 끝) 줄 번호(0-based, inclusive) 목록."""
    spans = []
    start = None
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            if start is None:
                start = i
            else:
                spans.append((start, i))
                start = None
    return spans


def _in_fence(spans: list[tuple[int, int]], i: int) -> bool:
    return any(s <= i <= e for s, e in spans)


def _nearby_evidence(lines: list[str], idx: int, spans: list[tuple[int, int]]
                      ) -> str | None:
    """`idx` (0-based) 주변 ADJACENCY_LINES 안에서 근거 텍스트를 찾는다.
    코드펜스 안이거나 `Repro:`/`Verify:` 로 시작하는 줄이면 근거로 본다."""
    lo = max(0, idx - ADJACENCY_LINES)
    hi = min(len(lines) - 1, idx + ADJACENCY_LINES)
    chunks = []
    for i in range(lo, hi + 1):
        if _in_fence(spans, i) or EVIDENCE_MARKER_RE.match(lines[i]):
            chunks.append(lines[i])
    return "\n".join(chunks) if chunks else None


def _targets(text: str) -> set[str]:
    return {m.group(0) for m in TARGET_RE.finditer(text) if len(m.group(0)) >= 3}


def _dotted_to_file(target: str) -> str | None:
    """`module.function`/`module.Class.method` 형태의 첫 세그먼트를
    `module.py` 로 되짚는다. 점 표기 대상이 `_repo_targets()` 가 절대
    내놓지 않는 형태라 항상 미스매치되는 case(honest2)를 닫는다."""
    if "/" in target or target.count(".") < 1:
        return None
    module = target.split(".", 1)[0]
    if not module or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", module):
        return None
    return f"{module}.py"


def _cite_matches(cited: set[str], repo_targets: set[str]) -> bool:
    if cited & repo_targets:
        return True
    for c in cited:
        derived = _dotted_to_file(c)
        if derived is None:
            continue
        if derived in repo_targets:
            return True
        # 중첩 모듈(`pkg/module.py`)을 위한 basename 매치 — 여러 디렉터리에
        # 같은 이름의 파일이 있으면 어느 걸 가리키는지 모호하므로, 후보가
        # 정확히 하나일 때만 인정한다(같은 이름의 무관한 diff 파일이 있으면
        # 매칭시키지 않는다 — before-landing hunt finding).
        candidates = [rt for rt in repo_targets if rt.endswith("/" + derived)]
        if len(candidates) == 1:
            return True
    return False


def scan_text(text: str, repo_targets: set[str] | None = None) -> list[Finding]:
    """`text` 안의 주장 언어를 스캔한다.

    `repo_targets` 가 주어지면(diff/repo 에서 실제로 등장하는 경로·식별자
    집합), 근거가 지목하는 대상이 그 집합 안에 있는지까지 검사한다. 주어지지
    않으면(순수 텍스트 단위 테스트) 근거 존재/부재만 판정한다 — 대상
    추적성은 `--repo` 를 아는 CLI 경로에서만 확정할 수 있다."""
    lines = text.splitlines()
    spans = _fence_spans(lines)
    findings: list[Finding] = []
    for i, line in enumerate(lines):
        m = CLAIM_RE.search(line)
        if not m:
            continue
        evidence = _nearby_evidence(lines, i, spans)
        if evidence is None:
            findings.append(Finding(
                claim=m.group(0), line_no=i + 1, line_text=line,
                reason="인접한 코드펜스나 Repro:/Verify: 줄이 없다"))
            continue
        if repo_targets is not None:
            cited = _targets(evidence)
            if not _cite_matches(cited, repo_targets):
                findings.append(Finding(
                    claim=m.group(0), line_no=i + 1, line_text=line,
                    reason="근거가 지목하는 대상이 diff/repo 에 없다"))
    return findings


class BaseResolutionError(RuntimeError):
    """`--base` 가 주어졌지만 diff 를 낼 수 없을 때 — whole-repo
    `git ls-files` 로 조용히 넘어가면 case0 이 다시 열리므로, 호출부가
    hard-fail 하도록 신호만 던진다(폴백하지 않는다)."""


def _repo_targets(repo: Path, base: str | None = None) -> set[str]:
    """`base` 가 없으면 작업 트리 전체 경로(`git ls-files`) — 기존
    동작 그대로. `base` 가 있으면 diff-scoped 로 좁힌다
    (`git diff --name-only <base>...HEAD`, 바뀐 경로만): case0 처럼
    diff 와 무관한 "실재하지만 무관한" 파일을 인용해 추적성 검사를
    통과하는 걸 막는다. `base` 가 주어졌는데 diff 커맨드 자체가 실패하면
    (알 수 없는 ref, shallow clone 등) whole-repo 로 폴백하지 않고
    `BaseResolutionError` 를 던진다."""
    targets: set[str] = set()
    if base is not None:
        r = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=repo, capture_output=True, text=True)
        if r.returncode != 0:
            raise BaseResolutionError(
                f"git diff --name-only {base}...HEAD 실패: {r.stderr.strip()}")
        targets.update(line.strip() for line in r.stdout.splitlines()
                       if line.strip())
        return targets
    r = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True,
                       text=True)
    if r.returncode == 0:
        targets.update(line.strip() for line in r.stdout.splitlines()
                       if line.strip())
    return targets


def main(argv: list[str]) -> int:
    repo = Path(".").resolve()
    if "--repo" in argv:
        i = argv.index("--repo")
        repo = Path(argv[i + 1]).resolve()
        argv = argv[:i] + argv[i + 2:]
    base = None
    if "--base" in argv:
        i = argv.index("--base")
        base = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if not argv:
        print("claim_scan: 검사할 파일 경로가 필요하다")
        return 2
    path = Path(argv[0])
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as e:
        print(f"claim_scan: {path} 를 읽을 수 없다 ({e})")
        return 2
    try:
        repo_targets = _repo_targets(repo, base=base)
    except BaseResolutionError as e:
        print(f"claim_scan: --base {base} 해석 실패, whole-repo 로 넘어가지 "
              f"않는다 ({e})")
        return 2
    findings = scan_text(text, repo_targets)
    for f in findings:
        print(f"{path}:{f.line_no}: 주장 '{f.claim}' — {f.reason}")
        print(f"    {f.line_text.strip()}")
    if findings:
        return 1
    print(f"claim_scan: {path} — 주장 근거/추적성 이상 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
