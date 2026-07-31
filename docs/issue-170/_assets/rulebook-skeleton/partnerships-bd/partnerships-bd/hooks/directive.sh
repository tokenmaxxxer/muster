#!/usr/bin/env bash
# SessionStart: partnerships-bd's role directive — how this role fills the core
# lifecycle. Kill switch: export PARTNERSHIPS_BD_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${PARTNERSHIPS_BD_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "partnerships-bd" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[partnerships-bd] Role directive (on top of core's protocol):

YOU DECIDE: 파트너십이 구조적으로 성립하는가

USE_WHEN: 제휴/BD 딜 구조가 걸릴 때

PRODUCES (required record fields): deal structure verdict, term sheet outline

WRITE_SCOPE: []

HAND-OFF: 법적 계약 검토는 → legal-compliance

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/partnerships-bd.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
