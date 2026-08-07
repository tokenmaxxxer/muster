#!/usr/bin/env python3
"""원장 — 되풀이되는 운영자 교정이 기록으로 남는가를 잰다.

  python3 ledger/decisions.py [<레포 경로>] [--json]

issue #322: 운영자가 승인/거부/피드백으로 남기는 판단은 노하우인데, 시스템은
그걸 한 번 쓰고 버린다. #310 의 "patch-instead-of-structure" 교정이 하루에
네 번 반복된 뒤에야 사람이 알아채고 문서화했다 — 처음 교정에서 배웠다면 두
번째는 없었을 것이다.

읽는 것은 role 세션이 이미 record-shape-gate 강제로 쓰는
`docs/issue-*/reports/implementation.md` (및 다른 role 의 동종 기록 파일)의
`## What did not work` / `## Rationale for deviations` 절이다 — 새 데이터
수집 경로 없이, 이미 커밋된 텍스트만 읽는다.

한 줄을 정규화해서 *서로 다른 subject* 에 걸쳐 threshold(기본 2)번 이상
나타나면, 그 정규화 키를 인용하는 `docs/decisions/*.md` 항목이 있는지 본다.
없으면 후보로 찍고 비정상 종료(exit 1) — 있으면 이미 확인된 결정이므로
통과. LLM 분류가 아니라 부분일치 카운트라서, 왜 찍혔는지 운영자가 그 자리에서
읽을 수 있다(issue #322 본문: "mined pattern is a *proposal*, never a fact").
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BOARD = "docs"
THRESHOLD = 2

SECTION_RE = re.compile(
    r"^##\s*(What did not work|Rationale for deviations)\s*$", re.M)
BULLET_RE = re.compile(r"^\s*[-*]\s+(.*\S)\s*$", re.M)

# 이 토큰들은 subject/issue 마다 달라서 같은 교정이 다른 텍스트로 보이게 만든다.
# 정규화에서 지운다 — "issue-245 에서 ..." 와 "issue-310 에서 ..." 가 같은
# 교정이면 같은 키로 묶여야 한다.
_STRIP_RE = re.compile(r"#\d+|issue-\d+|\b[0-9a-f]{7,40}\b")
_WS_RE = re.compile(r"\s+")


def normalize(line: str) -> str:
    """불릿 한 줄을 subject-무관 키로 정규화."""
    t = line.lower()
    t = _STRIP_RE.sub("", t)
    t = re.sub(r"[^\w\s가-힣]", " ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def extract_bullets(text: str) -> list[str]:
    """`## What did not work` / `## Rationale for deviations` 절의 불릿만 뽑는다."""
    out = []
    headers = list(SECTION_RE.finditer(text or ""))
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[start:end]
        # 다음 '##' 헤더 전까지만 (하위 heading 은 절 안에 없다고 가정하지 않고,
        # 있으면 거기서 자른다)
        next_h2 = re.search(r"^##\s", body, re.M)
        if next_h2:
            body = body[:next_h2.start()]
        out += [b for b in BULLET_RE.findall(body)]
    return out


def history(repo: Path, path: str) -> list[str]:
    """오래된 순으로 각 커밋 시점의 파일 내용."""
    log = subprocess.run(
        ["git", "-C", str(repo), "log", "--reverse", "--format=%H", "--", path],
        capture_output=True, text=True)
    out = []
    for sha in log.stdout.split():
        blob = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{path}"],
                              capture_output=True, text=True)
        if blob.returncode == 0:
            out.append(blob.stdout)
    return out


def _subject_of(rel: str) -> str:
    """docs/issue-<n>/reports/implementation.md -> issue-<n>."""
    parts = Path(rel).parts
    for p in parts:
        if p.startswith("issue-"):
            return p
    return rel


def records(repo: Path) -> list[str]:
    """스캔할 role 기록 파일들의 레포 상대 경로."""
    board = repo / BOARD
    if not board.is_dir():
        return []
    return sorted(str(p.relative_to(repo))
                  for p in board.glob("issue-*/reports/*.md") if p.is_file())


def decisions_citations(repo: Path) -> set[str]:
    """`docs/decisions/*.md` 전체 본문(정규화)을 하나의 텍스트로 모아, 각
    후보 키가 그 안에 부분 문자열로 등장하는지 검사할 때 쓴다."""
    d = repo / "docs" / "decisions"
    if not d.is_dir():
        return set()
    texts = []
    for p in d.glob("*.md"):
        try:
            texts.append(normalize(p.read_text()))
        except OSError:
            continue
    return set(texts)


def cited(key: str, decision_texts: set[str]) -> bool:
    if not key:
        return False
    return any(key in t for t in decision_texts)


def collect(repo: Path, threshold: int = THRESHOLD) -> dict:
    rels = records(repo)
    # key -> {subject -> [(rel, occurrence_text), ...]}
    occurrences: dict[str, dict[str, list[str]]] = {}
    for rel in rels:
        subject = _subject_of(rel)
        seen_texts = set(history(repo, rel))
        cur = repo / rel
        if cur.exists():
            text = cur.read_text()
            seen_texts.add(text)
        subject_keys: set[str] = set()
        for text in seen_texts:
            for bullet in extract_bullets(text):
                key = normalize(bullet)
                if not key or key in ("none", "없음", "none."):
                    continue
                subject_keys.add(key)
        for key in subject_keys:
            occurrences.setdefault(key, {}).setdefault(subject, []).append(rel)

    decision_texts = decisions_citations(repo)
    candidates = []
    for key, by_subject in sorted(occurrences.items()):
        if len(by_subject) < threshold:
            continue
        if cited(key, decision_texts):
            continue
        candidates.append({
            "key": key,
            "subjects": sorted(by_subject.keys()),
            "count": len(by_subject),
        })

    return {"repo": str(repo), "records": rels, "threshold": threshold,
            "candidates": candidates}


def report(d: dict) -> str:
    if not d["records"]:
        return (f"{d['repo']}\n  docs/issue-*/reports/*.md 없음 — 검사할 role "
                f"기록이 없다.")
    out = [d["repo"], f"  기록 {len(d['records'])}개, threshold {d['threshold']}"]
    if not d["candidates"]:
        out.append("  후보 없음 — 반복 교정 중 미확인 상태인 것이 없다.")
        return "\n".join(out)
    out.append(f"  ⚠ 미확인 반복 교정 후보 {len(d['candidates'])}건:")
    for c in d["candidates"]:
        out.append(f"    - \"{c['key']}\" — subject {c['count']}개: "
                   f"{', '.join(c['subjects'])}")
    out.append("  docs/decisions/*.md 에 이 패턴을 인용하는 항목을 (운영자 확인 후)"
               " 쓰면 통과한다.")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--threshold", type=int, default=THRESHOLD)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    if not (repo / ".git").exists():
        sys.exit(f"git 레포가 아니다: {repo}")
    d = collect(repo, a.threshold)
    print(json.dumps(d, ensure_ascii=False, indent=2) if a.json else report(d))
    return 1 if d["candidates"] else 0


if __name__ == "__main__":
    sys.exit(main())
