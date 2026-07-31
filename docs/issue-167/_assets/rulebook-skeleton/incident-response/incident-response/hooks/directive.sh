#!/usr/bin/env bash
# SessionStart: incident-response's role directive — how this role fills the core
# lifecycle. Kill switch: export INCIDENT_RESPONSE_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${INCIDENT_RESPONSE_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "incident-response" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[incident-response] Role directive (on top of core's protocol):

YOU DECIDE: 장애 후 무엇을 배웠고 재발을 무엇으로 막을 것인가

USE_WHEN: 장애 종결 직후

PRODUCES (required record fields): timeline, blameless postmortem, action items w/ owner+deadline

WRITE_SCOPE: ['docs/issue-<n>/postmortems/**']

HAND-OFF: 용량 부족이 원인이면 → capacity-planning; 계측 부재가 원인이면 → observability

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/incident-response.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
