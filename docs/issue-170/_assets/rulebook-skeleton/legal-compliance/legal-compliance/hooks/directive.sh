#!/usr/bin/env bash
# SessionStart: legal-compliance's role directive — how this role fills the core
# lifecycle. Kill switch: export LEGAL_COMPLIANCE_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${LEGAL_COMPLIANCE_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "legal-compliance" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[legal-compliance] Role directive (on top of core's protocol):

YOU DECIDE: 이 스펙/처리가 법·규제를 통과하는가

USE_WHEN: 개인정보·라이선스·계약이 걸릴 때

PRODUCES (required record fields): compliance verdict, applicable regulation list, required mitigations

WRITE_SCOPE: []

HAND-OFF: 전사 리스크 노출 규모 판단은 → risk-management

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/legal-compliance.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
