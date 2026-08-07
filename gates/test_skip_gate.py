#!/usr/bin/env python3
"""issue #334 — `gates/skip_gate.py`의 단위 테스트. 네트워크 없이 돈다.

  python3 gates/test_skip_gate.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import skip_gate

_SKIPPING_SUITE = '''
import pytest

def test_a_passes():
    assert True

def test_b_is_skipped():
    pytest.skip("environment-gated, not run here")
'''

_CLEAN_SUITE = '''
def test_a_passes():
    assert True

def test_b_passes():
    assert 1 + 1 == 2
'''


def t_gate_exits_1_on_suite_with_a_skip():
    with tempfile.TemporaryDirectory() as td:
        suite = Path(td) / "test_fixture.py"
        suite.write_text(_SKIPPING_SUITE)
        rc = skip_gate.main([str(suite)])
        assert rc != 0, rc


def t_gate_exits_0_on_suite_with_no_skips():
    with tempfile.TemporaryDirectory() as td:
        suite = Path(td) / "test_fixture.py"
        suite.write_text(_CLEAN_SUITE)
        rc = skip_gate.main([str(suite)])
        assert rc == 0, rc


def t_parse_skips_extracts_location_and_reason():
    output = "SKIPPED [1] test_fixture.py:8: environment-gated, not run here\n"
    skips = skip_gate.parse_skips(output)
    assert skips == [("test_fixture.py:8", "environment-gated, not run here")], skips


def t_parse_skips_handles_reasonless_line():
    output = "SKIPPED [1] test_fixture.py:8\n"
    skips = skip_gate.parse_skips(output)
    assert skips == [("test_fixture.py:8", "")], skips


def t_gate_exits_nonzero_on_hard_failure_even_without_skips():
    with tempfile.TemporaryDirectory() as td:
        suite = Path(td) / "test_fixture.py"
        suite.write_text("def test_fails():\n    assert False\n")
        rc = skip_gate.main([str(suite)])
        assert rc != 0, rc


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
