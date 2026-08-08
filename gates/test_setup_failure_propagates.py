#!/usr/bin/env python3
"""issue-416 finding 3 — 셋업 단계 실패가 스위트 성패로 전파되는지 검사.

`tests/run-orchestrate-tests.sh` 의 모양(헤어독 셋업 단계 → 종료코드
검사 → 실제 어서션들)을 임시 사본으로 재현해, 셋업 단계를 고의로 깨서
하니스 자체의 종료코드가 0이 아닌지 확인한다. 사고 배경: 8-고루틴/10회
동시성 테스트를 통과한 CAS 수정이 신규-설치(빈 상태) 리그레션을
냈다 — 코퍼스가 빈 초기 상태를 한 번도 담지 않았기 때문. 이 테스트는
그 사고의 더 좁은 절반(셋업 실패 은폐)만 재현한다: 코퍼스에 빈 상태
케이스가 있는지는 검사하지 않는다(존재-검사만 하는 `empty state:` 필드로
별도 대응).

네트워크 없이, 임시 스크립트를 실제로 실행해 종료코드를 확인한다.

  python3 gates/test_setup_failure_propagates.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

_HARNESS = """#!/usr/bin/env bash
set -uo pipefail
pass=0; fail=0

# setup step, shaped like tests/run-orchestrate-tests.sh's first block:
# a heredoc step whose exit code is checked before any real assertion.
python3 - <<'PY'
import sys
sys.exit({setup_exit})
PY
[ $? -eq 0 ] && pass=$((pass+1)) || fail=$((fail+1))

# a real assertion that would otherwise pass on its own
[ 1 -eq 1 ] && pass=$((pass+1)) || fail=$((fail+1))

echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
"""


def _run_harness(setup_exit: int) -> int:
    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "harness.sh"
        script.write_text(_HARNESS.format(setup_exit=setup_exit))
        script.chmod(0o755)
        r = subprocess.run(["bash", str(script)], capture_output=True, text=True)
        return r.returncode


def t_broken_setup_step_makes_harness_exit_nonzero():
    rc = _run_harness(setup_exit=1)
    assert rc != 0, ("a failing setup step must make the harness's own exit "
                     f"code nonzero, got {rc}")


def t_healthy_setup_step_makes_harness_exit_zero():
    rc = _run_harness(setup_exit=0)
    assert rc == 0, f"a healthy setup step must not fail the harness, got {rc}"


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("t_") and callable(f)]
    _run(tests)
