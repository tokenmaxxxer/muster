#!/usr/bin/env bash
# SessionStart: knowledge-management's role directive — how this role fills the core
# lifecycle. Kill switch: export KNOWLEDGE_MANAGEMENT_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${KNOWLEDGE_MANAGEMENT_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "knowledge-management" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[knowledge-management] Role directive (on top of core's protocol):

YOU DECIDE: 개별 이슈의 교훈이 조직 차원에서 재사용 가능한 형태로 축적·색인되는가

USE_WHEN: 여러 이슈의 회고가 쌓여 지식 큐레이션이 필요할 때

PRODUCES (required record fields): curated pattern-library entry, cross-issue index, supersession note (if replacing an older pattern)

WRITE_SCOPE: ['docs/patterns/**']

HAND-OFF: 단일 이슈 회고 자체는 → issue-retrospective

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/knowledge-management.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
