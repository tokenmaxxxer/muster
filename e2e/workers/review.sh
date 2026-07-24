#!/usr/bin/env bash
# review 실행자(결정론). 계약: $OUT/verdict.json
# 실제 표에서는 codex exec (크로스모델) 가 이 자리에 온다.
set -euo pipefail

if [ "${SCENARIO:-happy}" = "reject" ]; then
  echo '{"approved": false, "reason": "요구사항 2(테스트 추가)가 diff 에 없음"}' > "$OUT/verdict.json"
  exit 0
fi

# 코드펜스로 감싸 내보낸다 — 라우터의 관대한 파싱 경로를 함께 확인한다
cat > "$OUT/verdict.json" <<'EOF'
계약 검증 결과:
```json
{"approved": true, "reason": "spec 요구사항 1,2 모두 diff 에 존재"}
```
EOF
echo "verdict 작성 완료"
