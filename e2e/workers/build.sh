#!/usr/bin/env bash
# build 실행자(결정론). cwd = 워크트리. 계약: $OUT/summary.md
set -euo pipefail

case "${SCENARIO:-happy}" in
  badpkg)
    # 존재하지 않는 패키지 — deps 게이트가 잡아야 한다
    echo "orchestrator-hallucinated-pkg-xyz==1.0.0" >> requirements.txt
    ;;
  protected)
    # 파이프라인이 자기 CI 를 고치려 든다 — writeset 게이트가 잡아야 한다
    mkdir -p .github/workflows
    echo "on: push" > .github/workflows/ci.yml
    ;;
esac

cat >> calc.py <<'PY'


def multiply(a, b):
    return a * b
PY

cat >> test_calc.py <<'PY'


class TestMultiply(unittest.TestCase):
    def test_multiply(self):
        self.assertEqual(calc.multiply(3, 4), 12)
PY

cat > "$OUT/summary.md" <<EOF
\`calc.multiply\` 추가 및 테스트 보강 (이슈 #$ISSUE).

- calc.py: multiply(a, b)
- test_calc.py: TestMultiply
EOF
echo "build 완료"
