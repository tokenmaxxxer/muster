#!/usr/bin/env bash
# SessionStart: market-analysis's role directive — how this role fills the core
# lifecycle. Kill switch: export MARKET_ANALYSIS_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${MARKET_ANALYSIS_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "market-analysis" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[market-analysis] Role directive (on top of core's protocol):

YOU DECIDE: 경쟁 구도에서 이 스펙이 서는가

USE_WHEN: product 스펙 확정 후, 경쟁 구도가 걸린 결정일 때

PRODUCES (required record fields): five-forces summary, competitor list w/ evidence links, JTBD-landscape verdict

WRITE_SCOPE: []

HAND-OFF: 가격 정책이 걸리면 → pricing; 포지셔닝 메시지가 걸리면 → marketing

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/market-analysis.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
