#!/usr/bin/env bash
# SessionStart: technical-writing's role directive — how this role fills the core
# lifecycle. Kill switch: export TECHNICAL_WRITING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${TECHNICAL_WRITING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "technical-writing" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[technical-writing] Role directive (on top of core's protocol):

YOU DECIDE: 독자가 알아야 할 것을 어떻게 구조화할지

USE_WHEN: 외부 공개 문서가 필요할 때

PRODUCES (required record fields): doc outline, draft, target-reader note

WRITE_SCOPE: ["docs/**"] (외부공개 한정 — external-facing docs only)

HAND-OFF: 개발자 대상 온보딩이면 → devrel

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/technical-writing.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
