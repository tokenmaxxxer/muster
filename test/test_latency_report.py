"""Issue #501 — reusable latency-breakdown computation + regression tests.

Extracts the ad-hoc measurement script behind
docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md into tested,
reusable functions, so the pre-registered step-2 before/after metric (median
inter-session idle gap per (repo, issue, role)) can be re-run against a later
ledger pull without re-deriving the grouping logic from scratch — the exact
mistake the after-proposal warrant hunt caught once already (grouping by
issue number alone merges same-numbered issues across repos).

Also satisfies the issue's step-1 acceptance check: every row of the
delivered breakdown cites a ledger/log source.
"""
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROPOSAL_PATH = ROOT / "docs" / "issue-501" / "proposals" / "2026-08-08-session-latency-breakdown.md"


def compute_idle_gaps(rows: list[dict]) -> list[dict]:
    """Inter-session idle gaps, keyed by (repo, issue, role) — not issue alone
    (issue #501 resolved_finding: issue numbers repeat across repos).

    `rows` are ledger.jsonl-shaped dicts with `cwd`, `ts`, `duration_s`,
    `role`. Returns one dict per consecutive same-key session pair with a
    non-negative gap: {key, idle_s}. Overlapping pairs (parallel dispatch)
    are excluded, matching the proposal's own methodology.
    """
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        cwd = r.get("cwd", "")
        m = re.search(r"-issue-(\d+)-", cwd)
        if not m:
            continue
        repo = cwd.split("/work/", 1)[-1].split("-issue-")[0]
        key = (repo, m.group(1), r.get("role"))
        groups.setdefault(key, []).append(r)

    gaps = []
    for key, sessions in groups.items():
        sessions.sort(key=lambda r: r["ts"])
        for prev, nxt in zip(sessions, sessions[1:]):
            next_start = nxt["ts"] - nxt["duration_s"]
            idle = next_start - prev["ts"]
            if idle >= 0:
                gaps.append({"key": key, "idle_s": idle})
    return gaps


def median_idle_s(rows: list[dict]) -> float | None:
    gaps = [g["idle_s"] for g in compute_idle_gaps(rows)]
    return statistics.median(gaps) if gaps else None


def test_idle_gap_grouping_keys_by_repo_and_issue_not_issue_alone():
    """Regression for the fixed methodology bug: same issue number in two
    different repos must never be treated as one session pair."""
    rows = [
        {"cwd": "/w/repo-a-issue-171-implementation", "ts": 1000, "duration_s": 100, "role": "implementation"},
        {"cwd": "/w/repo-b-issue-171-implementation", "ts": 1050, "duration_s": 20, "role": "implementation"},
    ]
    gaps = compute_idle_gaps(rows)
    assert gaps == []  # different repos, same issue number -> no pair at all


def test_idle_gap_computes_non_negative_gap_within_same_key():
    rows = [
        {"cwd": "/w/repo-a-issue-171-implementation", "ts": 1000, "duration_s": 100, "role": "implementation"},
        {"cwd": "/w/repo-a-issue-171-implementation", "ts": 2000, "duration_s": 50, "role": "implementation"},
    ]
    gaps = compute_idle_gaps(rows)
    assert len(gaps) == 1
    # next_start = 2000 - 50 = 1950; prev ts = 1000 -> idle = 950
    assert gaps[0]["idle_s"] == 950


def test_idle_gap_excludes_overlapping_pairs():
    rows = [
        {"cwd": "/w/repo-a-issue-171-implementation", "ts": 1000, "duration_s": 100, "role": "implementation"},
        {"cwd": "/w/repo-a-issue-171-implementation", "ts": 1010, "duration_s": 2000, "role": "implementation"},
    ]
    gaps = compute_idle_gaps(rows)
    assert gaps == []  # next_start = 1010 - 2000 < 0 relative window -> negative idle, excluded


def test_median_idle_s_empty_input():
    assert median_idle_s([]) is None


def test_delivered_breakdown_cites_ledger_and_log_sources():
    """Step-1 acceptance check: every measured row in the delivered
    breakdown cites a ledger/log source, not an unsourced assertion."""
    text = PROPOSAL_PATH.read_text(encoding="utf-8")
    assert "runs/ledger.jsonl" in text
    assert "duration_api_ms" in text
    # every numbered term in the breakdown table names its source column
    table_start = text.index("| term | source")
    table = text[table_start:text.index("\n\n", table_start)]
    for line in table.splitlines()[2:]:  # skip header + separator
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        assert cols[1], f"breakdown row missing a source: {line}"
