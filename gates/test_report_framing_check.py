#!/usr/bin/env python3
"""issue-320 — semantic-effect reporting.

Two checks, each verifying a distinct claim (per the issue-320 proposal):
(1) `run.md`'s step-5 instruction text still carries the four framing
elements (instruction-drift guard); (2)
`on-the-record/hooks/report-framing-check.sh` blocks a live reply that
fails to frame the four elements, and passes one that does.

  python3 gates/test_report_framing_check.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_MD = ROOT / "on-the-record" / "commands" / "run.md"
HOOK = ROOT / "on-the-record" / "hooks" / "report-framing-check.sh"


def _run_hook(msg: str | None) -> tuple[int, dict]:
    payload = json.dumps({"last_assistant_message": msg} if msg is not None else {})
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    env.pop("ORCHESTRATE_OFF", None)
    p = subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True,
                        text=True, env=env)
    out = {}
    if p.stdout.strip():
        out = json.loads(p.stdout)
    return p.returncode, out


def t_run_md_has_framing_instruction():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "의미론적 효과 프레이밍" in text
    for term in ("문제가 해결", "비용", "새로 가능", "남았는가"):
        assert term in text, f"run.md 에 프레이밍 요소 누락: {term}"
    assert "충족하지 않는다" in text


def t_mission_board_has_done_flow_note():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "Done 항목의" in text
    assert "PR 제목을 그대로 반복하지 않는다" in text


def t_address_only_reply_blocked():
    msg = ("1단계 승인 요청: 이슈 #320, PR #481 이 올라왔습니다. "
           "[이슈 #320] 프레이밍 추가 · implementation → merge")
    rc, out = _run_hook(msg)
    assert rc == 0
    assert out.get("decision") == "block", out
    assert "reason" in out


def t_four_element_reply_passes():
    msg = (
        "1단계 승인 요청: 이슈 #320. [이슈 #320] 프레이밍 추가 · "
        "implementation → merge\n"
        "PR 보고를 address-only 로 보내던 문제를 해결했습니다. "
        "그동안 운영자가 매번 원문을 다시 읽어야 하는 비용을 치렀는데, "
        "이제 report-framing-check 훅이 자동으로 검사해 새로 가능해졌습니다. "
        "아직 hooks.json 의 다른 이벤트는 검토가 남았습니다."
    )
    rc, out = _run_hook(msg)
    assert rc == 0
    assert out == {}, out


def t_non_report_reply_noop():
    rc, out = _run_hook("네, 알겠습니다. 다음 단계로 진행하겠습니다.")
    assert rc == 0
    assert out == {}, out


def t_empty_message_noop():
    rc, out = _run_hook(None)
    assert rc == 0
    assert out == {}, out


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
    sys.exit(0)
