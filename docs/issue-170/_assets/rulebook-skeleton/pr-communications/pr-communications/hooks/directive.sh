#!/usr/bin/env bash
# SessionStart: pr-communications's role directive — how this role fills the core
# lifecycle. Kill switch: export PR_COMMUNICATIONS_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${PR_COMMUNICATIONS_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "pr-communications" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[pr-communications] Role directive (on top of core's protocol):

YOU DECIDE: 메시지가 외부에 어떻게 읽힐지

USE_WHEN: 외부 커뮤니케이션이 걸릴 때

PRODUCES (required record fields): communications plan, key message, risk/Q&A prep

WRITE_SCOPE: []

HAND-OFF: 캠페인 성격 메시지는 → marketing

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/pr-communications.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
