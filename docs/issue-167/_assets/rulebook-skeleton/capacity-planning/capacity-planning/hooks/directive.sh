#!/usr/bin/env bash
# SessionStart: capacity-planning's role directive — how this role fills the core
# lifecycle. Kill switch: export CAPACITY_PLANNING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${CAPACITY_PLANNING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "capacity-planning" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[capacity-planning] Role directive (on top of core's protocol):

YOU DECIDE: 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가

USE_WHEN: 용량 예측/증설 시점 결정이 걸릴 때

PRODUCES (required record fields): capacity forecast, expansion trigger thresholds, cost note

WRITE_SCOPE: [] (report-only role — no code/doc write outside the record itself)

HAND-OFF: 성능 자체의 병목 원인 분석은 → performance-engineering

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/capacity-planning.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
