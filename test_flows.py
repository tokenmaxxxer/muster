#!/usr/bin/env python3
"""issue #222: `gates/flows.py`의 `_STAGE_MAP` 5값 도출 + `closed` 우선 규칙.

`test_spawn.py::FlowsPayload`가 `gates/flows.py`의 기존 테스트 홈이지만,
issue #222 본문이 `test_spawn.py`를 명시적으로 금지한다(issue #218이
동시 수정 중). `FlowsPayload.setUp`의 몽키패치 패턴을 이 파일에 그대로
복제한다 — `test_spawn.py`를 import하지 않으므로 그쪽이 어떻게 바뀌든
이 파일은 영향받지 않는다.

  python3 -m pytest test_flows.py
"""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent))
import spawn
import flows
import closure_sweep


def t_stage_for_scope_proposed_maps_to_proposal():
    assert flows._stage_for("scope-proposed") == ("proposal", True)


def t_stage_for_scope_approved_maps_to_approved():
    assert flows._stage_for("scope-approved") == ("approved", True)


def t_stage_for_in_progress_maps_to_implementing():
    assert flows._stage_for("in-progress") == ("implementing", True)


def t_stage_for_landed_maps_to_delivered():
    assert flows._stage_for("landed") == ("delivered", True)


def t_stage_for_issue_closed_maps_to_closed():
    assert flows._stage_for(None, "CLOSED") == ("closed", True)


def t_stage_for_unmapped_loop_state_reports_raw():
    stage, derived = flows._stage_for("some-downstream-state")
    assert stage == "some-downstream-state"
    assert derived is False


def t_stage_for_closed_wins_over_in_progress_loop_state():
    # closed는 loop_state가 아직 안 끝난 것처럼 보여도(예: in-progress)
    # GitHub 이슈 자체의 상태에서 나오는 종결 상태라 매핑 조회보다 이긴다.
    assert flows._stage_for("in-progress", "CLOSED") == ("closed", True)


class FlowsStageMapping(unittest.TestCase):
    """`flows_payload()` 경유 통합 케이스 — `FlowsPayload.setUp`(test_spawn.py)과
    동일한 몽키패치 패턴을 이 파일 안에서 자체 정의한다."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.addCleanup(self.td.cleanup)
        self._patched = []
        self._patch(spawn, "_repo_slug", lambda root: "acme/repo")
        self._patch(spawn, "_issue_comments", lambda root, n: [])
        self._patch(spawn, "_roster_load", lambda: {})
        old_root = spawn.ROOT
        spawn.ROOT = self.root
        self.addCleanup(setattr, spawn, "ROOT", old_root)
        self._patch(flows, "_pr_list_all", lambda root: [])
        self._issues = []
        self._patch(flows, "_issue_list_all", lambda root: self._issues)
        self._patch(closure_sweep, "find_violations",
                    lambda root, subjects=None, issue_states=None: [])

    def _patch(self, obj, name, fn):
        orig = getattr(obj, name)
        setattr(obj, name, fn)
        self.addCleanup(setattr, obj, name, orig)

    def _write_record(self, subject, role, loop_state):
        rec = self.root / spawn.BOARD / subject / "reports"
        rec.mkdir(parents=True, exist_ok=True)
        (rec / f"{role}.md").write_text(
            f"---\nloop_state: {loop_state}\n---\n", encoding="utf-8")

    def test_flows_section_stage_mapping_and_unmapped_fallback(self):
        # test_spawn.py::FlowsPayload의 동명 테스트와 같은 동작을 이 새
        # 파일에서도 확인한다 — 원본은 손대지 않음, 이번 변경으로 무회귀.
        self._write_record("issue-10", "product-discovery", "scope-proposed")
        self._write_record("issue-11", "product-discovery", "some-downstream-state")
        payload = flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[10]["stage"], "proposal")
        self.assertTrue(by_issue[10]["stage_derived"])
        self.assertEqual(by_issue[11]["stage"], "some-downstream-state")
        self.assertFalse(by_issue[11]["stage_derived"])

    def test_closed_issue_wins_over_open_loop_state(self):
        self._write_record("issue-12", "implementation", "in-progress")
        self._issues = [{"number": 12, "state": "CLOSED", "body": ""}]
        payload = flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[12]["stage"], "closed")
        self.assertTrue(by_issue[12]["stage_derived"])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
    unittest.main()
