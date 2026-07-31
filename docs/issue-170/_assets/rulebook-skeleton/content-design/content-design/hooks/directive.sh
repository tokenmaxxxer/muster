#!/usr/bin/env bash
# SessionStart: content-design's role directive — how this role fills the core
# lifecycle. Kill switch: export CONTENT_DESIGN_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${CONTENT_DESIGN_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "content-design" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[content-design] Role directive (on top of core's protocol):

YOU DECIDE: 문구가 사용자의 실제 결정을 돕는가

USE_WHEN: 플로우에 새 카피/마이크로카피가 걸릴 때

PRODUCES (required record fields): copy draft, rationale per string, A/B alternative (if applicable)

WRITE_SCOPE: []

HAND-OFF: 화면/플로우 구조 자체가 바뀌어야 하면 → interaction-design

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/content-design.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
