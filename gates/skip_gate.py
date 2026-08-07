#!/usr/bin/env python3
"""issue #334 — 스킵을 통과와 구분하는 게이트.

`pytest`의 종료 코드는 스킵이 있어도 0이다. `-ra`는 요약에 스킵을
*표시*할 뿐 종료 코드를 바꾸지 않으므로, 종료 코드만 읽는 role/CI 는
스킵이 섞인 실행을 깨끗한 통과로 오독한다. 이 스크립트는 `-ra` 요약을
파싱해 스킵이 하나라도 있으면 실행 자체가 0으로 끝났어도 1로 종료한다.

  python3 gates/skip_gate.py [pytest 로 전달할 추가 인자...]
"""
from __future__ import annotations
import re
import subprocess
import sys

_SKIP_LINE_RE = re.compile(r"^SKIPPED(?: \[\d+\])? ([^:]+:\d+)(?:: (.*))?$")


def run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-ra", *args],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def parse_skips(output: str) -> list[tuple[str, str]]:
    skips = []
    for line in output.splitlines():
        m = _SKIP_LINE_RE.match(line.strip())
        if m:
            skips.append((m.group(1), m.group(2) or ""))
    return skips


def main(args: list[str] | None = None) -> int:
    args = list(args) if args is not None else sys.argv[1:]
    returncode, output = run(args)
    print(output, end="")
    skips = parse_skips(output)
    if returncode == 0 and not skips:
        print("skip_gate: 0 skipped — verified", file=sys.stderr)
        return 0
    if skips:
        print(f"skip_gate: {len(skips)} SKIPPED — not verified:", file=sys.stderr)
        for nodeid, reason in skips:
            print(f"  {nodeid}{' — ' + reason if reason else ''}", file=sys.stderr)
    if returncode != 0:
        return returncode
    return 1


if __name__ == "__main__":
    sys.exit(main())
