#!/usr/bin/env bash
# SessionStart: security-threat-model's role directive — how this role fills the core
# lifecycle. Kill switch: export SECURITY_THREAT_MODEL_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${SECURITY_THREAT_MODEL_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "security-threat-model" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[security-threat-model] Role directive (on top of core's protocol):

YOU DECIDE: 신뢰 경계의 위협 표면

USE_WHEN: 스펙에 신뢰 경계·인증·민감데이터가 걸릴 때

PRODUCES (required record fields): STRIDE table, mitigation list per threat, residual risk note

WRITE_SCOPE: [] (report-only role — no code/doc write outside the record itself)

HAND-OFF: 구현 단계 취약점 점검은 → secure-coding; 법적 노출이면 → legal-compliance

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/security-threat-model.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
