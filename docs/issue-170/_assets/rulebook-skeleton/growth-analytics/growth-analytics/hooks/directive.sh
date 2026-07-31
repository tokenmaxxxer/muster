#!/usr/bin/env bash
# SessionStart: growth-analytics's role directive — how this role fills the core
# lifecycle. Kill switch: export GROWTH_ANALYTICS_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${GROWTH_ANALYTICS_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "growth-analytics" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[growth-analytics] Role directive (on top of core's protocol):

YOU DECIDE: 퍼널 병목과 실험 결과가 실제 개선인지

USE_WHEN: 퍼널 분석 또는 A/B 실험 해석이 걸릴 때

PRODUCES (required record fields): funnel diagnosis, experiment trust verdict (SRM/pre-registration check)

WRITE_SCOPE: []

HAND-OFF: 캠페인 메시지 변경이 필요하면 → marketing

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/growth-analytics.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
