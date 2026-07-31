#!/usr/bin/env bash
# SessionStart: test-authoring's role directive — how this role fills the core
# lifecycle. Kill switch: export TEST_AUTHORING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${TEST_AUTHORING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "test-authoring" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[test-authoring] Role directive (on top of core's protocol):

YOU DECIDE: 테스트 코드 자체가 격리성·fixture 전략 면에서 좋은 설계인가

USE_WHEN: 신규/기존 테스트 스위트를 설계·리뷰할 때

PRODUCES (required record fields): suite architecture note, fixture strategy, smell list (Meszaros catalog refs)

WRITE_SCOPE: ['test/**']

HAND-OFF: 실제 실행 결과 관찰은 → execution-observation

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/test-authoring.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
