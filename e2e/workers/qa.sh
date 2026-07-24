#!/usr/bin/env bash
# qa 실행자(결정론). cwd = 머지된 main. 계약: $OUT/run.md
# 테스트가 깨지면 종료 코드가 0이 아니고, 라우터가 build 로 회귀시킨다.
set -uo pipefail

{
  echo "# run record — 이슈 #$ISSUE"
  echo
  echo '```'
  python3 -m unittest -v 2>&1
  echo '```'
} > "$OUT/run.md"

python3 -m unittest -q >/dev/null 2>&1
rc=$?
echo "unittest rc=$rc"
exit $rc
