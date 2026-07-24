#!/usr/bin/env bash
# plan 실행자(결정론). 계약: $OUT/spec.md
set -euo pipefail

if [ "${SCENARIO:-happy}" = "nocontract" ]; then
  echo "산출물 없이 정상 종료 — 계약 위반 경로 확인용"
  exit 0
fi

# badpkg 시나리오만 requirements.txt 를 write-set 에 넣는다.
# (그래야 writeset 이 아니라 deps 게이트가 차단하는 것을 확인할 수 있다)
extra=""
[ "${SCENARIO:-happy}" = "badpkg" ] && extra="- write: requirements.txt"

cat > "$OUT/spec.md" <<EOF
# spec — 이슈 #$ISSUE: $TITLE

## 요구사항
1. \`calc.py\` 에 \`multiply(a, b)\` 를 추가한다.
2. \`test_calc.py\` 에 \`multiply\` 검증 테스트를 추가한다.

## write-set
- write: calc.py
- write: test_calc.py
$extra
EOF
echo "spec 작성 완료"
