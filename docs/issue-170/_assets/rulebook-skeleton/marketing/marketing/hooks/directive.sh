#!/usr/bin/env bash
# SessionStart: marketing's role directive — how this role fills the core
# lifecycle. Kill switch: export MARKETING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${MARKETING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "marketing" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[marketing] Role directive (on top of core's protocol):

YOU DECIDE: 어떤 메시지로 어떤 채널에 도달할지

USE_WHEN: 캠페인/포지셔닝이 걸릴 때

PRODUCES (required record fields): messaging doc, channel plan, target segment

WRITE_SCOPE: []

HAND-OFF: 퍼널 성과 해석은 → growth-analytics

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/marketing.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
