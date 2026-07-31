#!/usr/bin/env bash
# SessionStart: architecture's role directive — how this role fills the core
# lifecycle. Kill switch: export ARCHITECTURE_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ARCHITECTURE_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "architecture" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[architecture] Role directive (on top of core's protocol):

YOU DECIDE: 컴포넌트 경계·의존 방향

USE_WHEN: 새 모듈 경계나 기존 경계 변경이 걸릴 때

PRODUCES (required record fields): ADR (context/decision/consequences), boundary diagram

WRITE_SCOPE: ["docs/issue-<n>/decisions/**"]

HAND-OFF: 인터페이스 형태 세부는 → api-design; 성능 예산이 걸리면 → performance-engineering

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/architecture.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
