#!/usr/bin/env bash
# SessionStart: api-design's role directive — how this role fills the core
# lifecycle. Kill switch: export API_DESIGN_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${API_DESIGN_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "api-design" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[api-design] Role directive (on top of core's protocol):

YOU DECIDE: 서비스 경계의 인터페이스 형태

USE_WHEN: 여러 소비자가 걸리는 API 표면을 설계/변경할 때

PRODUCES (required record fields): interface spec (endpoints/schema/versioning), lifecycle/deprecation plan

WRITE_SCOPE: [] (report-only role — no code/doc write outside the record itself)

HAND-OFF: 컴포넌트 경계 자체가 바뀌면 → architecture; 스키마 신설/변경이면 → data-modeling

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/api-design.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
