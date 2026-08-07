#!/usr/bin/env python3
"""spec 문서 드리프트 게이트 (issue #336).

`docs/specs/reconciled-index.md` 는 spec-shaped 문서 목록과 각 문서의
SHA256 을 기록한다. 이 게이트는 그 해시를 다시 계산해 기록과 비교한다 —
목록에 있는 문서 중 하나라도 내용이 바뀌었는데 인덱스가 갱신되지 않았으면
차단한다. 의미론적 모순 탐지가 아니라 결정론적 드리프트 탐지다: "이 문서가
바뀌었다"는 사실만 검사하고, 바뀐 내용이 다른 문서와 실제로 모순되는지는
사람이 인덱스를 열어 판단한다.

  python3 gates/spec_index.py [<repo 경로>]              # 검사 모드 (기본, CI)
  python3 gates/spec_index.py [<repo 경로>] --update      # 인덱스 재생성
  종료 코드 0 통과(또는 --update 완료) / 1 차단
"""
from __future__ import annotations
import hashlib
import re
import sys
from pathlib import Path

_INDEX_PATH = "docs/specs/reconciled-index.md"
_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_index(index_path: Path) -> list[tuple[str, str]]:
    """인덱스 문서의 "Tracked documents" 표에서 (경로, 기록된 해시) 목록을 뽑는다."""
    rows = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        m = _ROW_RE.match(line)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


def check(repo: Path) -> list[str]:
    """차단 사유 목록. 비어 있으면 통과."""
    index_path = repo / _INDEX_PATH
    if not index_path.exists():
        return [f"{_INDEX_PATH} 없음 — spec 인덱스가 기록되지 않았다"]
    bad = []
    for rel_path, recorded_hash in parse_index(index_path):
        target = repo / rel_path
        if not target.exists():
            bad.append(f"{rel_path}: 인덱스에 있지만 파일이 없다")
            continue
        actual_hash = _sha256(target)
        if actual_hash != recorded_hash:
            bad.append(
                f"{rel_path}: 내용이 바뀌었는데 {_INDEX_PATH} 의 기록된 해시와 "
                f"다르다 (기록={recorded_hash[:12]}…, 실제={actual_hash[:12]}…) — "
                f"의도된 변경이면 `python3 gates/spec_index.py --update` 로 "
                f"재생성하고 관련 있다면 \"Resolved ambiguities\" 도 갱신하라"
            )
    return bad


def update(repo: Path) -> None:
    """인덱스 표의 각 행을 현재 파일 내용의 해시로 재작성한다."""
    index_path = repo / _INDEX_PATH
    lines = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
    out = []
    for line in lines:
        m = _ROW_RE.match(line.rstrip("\n"))
        if m:
            rel_path = m.group(1)
            target = repo / rel_path
            new_hash = _sha256(target)
            out.append(f"| `{rel_path}` | `{new_hash}` |\n")
        else:
            out.append(line)
    index_path.write_text("".join(out), encoding="utf-8")


def main() -> int:
    argv = sys.argv[1:]
    do_update = "--update" in argv
    positional = [a for a in argv if a != "--update"]
    repo = Path(positional[0] if positional else ".").resolve()
    if do_update:
        update(repo)
        print(f"{_INDEX_PATH} 갱신됨")
        return 0
    bad = check(repo)
    if bad:
        print("게이트 차단:")
        for b in bad:
            print(f"  - {b}")
        return 1
    print("통과: 모든 spec 문서가 기록된 해시와 일치한다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
