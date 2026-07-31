#!/usr/bin/env bash
# SessionStart: refactoring-legacy's role directive — how this role fills the core
# lifecycle. Kill switch: export REFACTORING_LEGACY_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${REFACTORING_LEGACY_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "refactoring-legacy" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[refactoring-legacy] Role directive (on top of core's protocol):

YOU DECIDE: 기존 코드의 관찰 가능한 동작을 바꾸지 않고 안전하게 재구조화할 수 있는가

USE_WHEN: 레거시/기존 코드에 손을 대야 할 때

PRODUCES (required record fields): refactoring plan, characterization tests, before/after behavior-equivalence note

WRITE_SCOPE: ['src/**', 'test/**']

HAND-OFF: 신규 기능 구현이 섞이면 그 부분은 → implementation

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/refactoring-legacy.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
