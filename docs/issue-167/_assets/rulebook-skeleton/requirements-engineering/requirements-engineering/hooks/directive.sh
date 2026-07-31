#!/usr/bin/env bash
# SessionStart: requirements-engineering's role directive — how this role fills the core
# lifecycle. Kill switch: export REQUIREMENTS_ENGINEERING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${REQUIREMENTS_ENGINEERING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "requirements-engineering" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[requirements-engineering] Role directive (on top of core's protocol):

YOU DECIDE: 요구사항이 검증가능·일관·추적 가능하게 명세되었는가

USE_WHEN: product 가설이 확정되어 정식 스펙으로 전환할 때

PRODUCES (required record fields): structured requirements doc, traceability matrix, ambiguity list resolved

WRITE_SCOPE: [] (report-only role — no code/doc write outside the record itself)

HAND-OFF: 화면/플로우 설계는 → interaction-design

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/requirements-engineering.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
