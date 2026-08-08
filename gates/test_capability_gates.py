#!/usr/bin/env python3
"""issue-376 — capability reachability gates.

`ci_reachable_gates` (a gate registered in `gates.ALL` but not reachable
under `gates/ci.py::check()`'s real call graph is a dead gate) and
`schema_field_orphans` (a `docs/specs/*.md` schema field with no reader
outside its own producer/tests/spec is a dead field). Both are
purely-derived — no hand-maintained list to drift from.

  python3 -m pytest -q gates/test_capability_gates.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates


def t_ci_reachable_gates_flags_never_called():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "gates").mkdir()
        (d / "gates" / "ci.py").write_text(
            "def check(repo, closes_only=False):\n"
            "    bad = []\n"
            "    if closes_only:\n"
            "        return bad\n"
            "    return bad\n",
            encoding="utf-8",
        )
        orig_root = gates.ON_THE_RECORD_ROOT
        orig_all = gates.ALL
        try:
            gates.ON_THE_RECORD_ROOT = d
            gates.ALL = {"writeset": lambda d, cfg: []}
            bad = gates.ci_reachable_gates(d, {})
        finally:
            gates.ON_THE_RECORD_ROOT = orig_root
            gates.ALL = orig_all
    assert any("writeset" in b and "전혀 호출되지 않는다" in b for b in bad), bad


def t_ci_reachable_gates_flags_past_closes_only_guard():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "gates").mkdir()
        (d / "gates" / "ci.py").write_text(
            "def check(repo, closes_only=False):\n"
            "    bad = []\n"
            "    if closes_only:\n"
            "        return bad\n"
            "    bad += gates.record_enums(repo, {})\n"
            "    return bad\n",
            encoding="utf-8",
        )
        orig_root = gates.ON_THE_RECORD_ROOT
        orig_all = gates.ALL
        try:
            gates.ON_THE_RECORD_ROOT = d
            gates.ALL = {"record_enums": lambda d, cfg: []}
            bad = gates.ci_reachable_gates(d, {})
        finally:
            gates.ON_THE_RECORD_ROOT = orig_root
            gates.ALL = orig_all
    assert any("record_enums" in b and "가드 이후에만" in b for b in bad), bad


def t_ci_reachable_gates_passes_when_wired_before_guard():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "gates").mkdir()
        (d / "gates" / "ci.py").write_text(
            "def check(repo, closes_only=False):\n"
            "    bad = []\n"
            "    bad += gates.record_enums(repo, {})\n"
            "    if closes_only:\n"
            "        return bad\n"
            "    return bad\n",
            encoding="utf-8",
        )
        orig_root = gates.ON_THE_RECORD_ROOT
        orig_all = gates.ALL
        try:
            gates.ON_THE_RECORD_ROOT = d
            gates.ALL = {"record_enums": lambda d, cfg: []}
            bad = gates.ci_reachable_gates(d, {})
        finally:
            gates.ON_THE_RECORD_ROOT = orig_root
            gates.ALL = orig_all
    assert bad == [], bad


def t_schema_field_orphans_flags_documented_unread_field():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "docs" / "specs").mkdir(parents=True)
        (d / "docs" / "specs" / "example-schema.md").write_text(
            "## 1. Top-level\n\n"
            "| `decision_queue` | array | see below |\n",
            encoding="utf-8",
        )
        (d / "producer.py").write_text(
            "decision_queue = []\n"
            "decision_queue.append(1)\n",
            encoding="utf-8",
        )
        bad = gates.schema_field_orphans(d, {})
    assert any("decision_queue" in b for b in bad), bad


def t_schema_field_orphans_passes_when_field_is_read_elsewhere():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "docs" / "specs").mkdir(parents=True)
        (d / "docs" / "specs" / "example-schema.md").write_text(
            "## 1. Top-level\n\n"
            "| `decision_queue` | array | see below |\n",
            encoding="utf-8",
        )
        (d / "producer.py").write_text(
            "decision_queue = []\n",
            encoding="utf-8",
        )
        (d / "consumer.py").write_text(
            "payload = {}\n"
            "print(len(payload['decision_queue']))\n",
            encoding="utf-8",
        )
        bad = gates.schema_field_orphans(d, {})
    assert bad == [], bad


def t_actual_tree_ci_reachable_gates_catches_writeset_and_record_enums():
    root = Path(__file__).resolve().parent.parent
    bad = gates.ci_reachable_gates(root, {})
    assert any("gates.writeset" in b for b in bad), bad
    assert any("gates.record_enums" in b for b in bad), bad


def t_actual_tree_schema_field_orphans_catches_alive():
    """`decision_queue` was the orphaned field when this test was written,
    but issue-466's `decision-queue-stopgate.sh` (landed on main since) now
    reads it, so it's no longer orphaned — a real fix, not a regression.
    `alive` (also in `docs/specs/flows-schema.md`) remains unread outside
    its producer/test, so it stays a stable fixture for "the gate catches a
    real orphaned field in the actual tree"."""
    root = Path(__file__).resolve().parent.parent
    bad = gates.schema_field_orphans(root, {})
    assert any("alive" in b for b in bad), bad


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
