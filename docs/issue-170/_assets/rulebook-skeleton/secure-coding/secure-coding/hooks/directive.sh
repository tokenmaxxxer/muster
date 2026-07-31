#!/usr/bin/env bash
# SessionStart: secure-coding's role directive — how this role fills the core
# lifecycle. Kill switch: export SECURE_CODING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${SECURE_CODING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "secure-coding" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[secure-coding] Role directive (on top of core's protocol):

YOU DECIDE: 구현이 공격에 견디는가

USE_WHEN: 인증/입력처리 코드 랜딩 후

PRODUCES (required record fields): ASVS checklist, pentest finding list w/ severity

WRITE_SCOPE: [] (report-only role — no code/doc write outside the record itself)

HAND-OFF: 설계 단계 위협표면 재검토가 필요하면 → security-threat-model

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/secure-coding.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
