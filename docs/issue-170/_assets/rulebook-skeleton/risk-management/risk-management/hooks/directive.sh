#!/usr/bin/env bash
# SessionStart: risk-management's role directive — how this role fills the core
# lifecycle. Kill switch: export RISK_MANAGEMENT_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${RISK_MANAGEMENT_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "risk-management" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[risk-management] Role directive (on top of core's protocol):

YOU DECIDE: 전사 리스크 노출이 허용 범위인가

USE_WHEN: 재무/운영/전략 리스크가 걸릴 때 (feasibility보다 넓은 범위)

PRODUCES (required record fields): ERM verdict, risk register entry, mitigation owner

WRITE_SCOPE: []

HAND-OFF: 개별 법규 컴플라이언스 세부는 → legal-compliance

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/risk-management.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
