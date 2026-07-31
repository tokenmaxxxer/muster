#!/usr/bin/env bash
# SessionStart: customer-support's role directive — how this role fills the core
# lifecycle. Kill switch: export CUSTOMER_SUPPORT_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${CUSTOMER_SUPPORT_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "customer-support" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[customer-support] Role directive (on top of core's protocol):

YOU DECIDE: 문의를 어떤 우선순위/SLA로 처리할지

USE_WHEN: CS 플로우/SLA 설계가 걸릴 때

PRODUCES (required record fields): support playbook, SLA table, escalation path

WRITE_SCOPE: []

HAND-OFF: 반복 문의가 제품 결함이면 → product-discovery

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/customer-support.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
