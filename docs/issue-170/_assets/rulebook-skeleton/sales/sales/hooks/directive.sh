#!/usr/bin/env bash
# SessionStart: sales's role directive — how this role fills the core
# lifecycle. Kill switch: export SALES_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${SALES_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "sales" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[sales] Role directive (on top of core's protocol):

YOU DECIDE: 리드/기회를 어떻게 진행시킬지

USE_WHEN: 영업 프로세스 설계가 걸릴 때

PRODUCES (required record fields): sales playbook, stage definitions, qualification criteria

WRITE_SCOPE: []

HAND-OFF: 메시지/포지셔닝 자체는 → marketing

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/sales.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
