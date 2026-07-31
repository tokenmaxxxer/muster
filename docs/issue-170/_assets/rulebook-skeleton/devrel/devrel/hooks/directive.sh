#!/usr/bin/env bash
# SessionStart: devrel's role directive — how this role fills the core
# lifecycle. Kill switch: export DEVREL_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${DEVREL_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "devrel" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[devrel] Role directive (on top of core's protocol):

YOU DECIDE: 외부 개발자가 이 표면을 채택할 수 있는가

USE_WHEN: 외부 개발자 대상 API/SDK가 걸릴 때

PRODUCES (required record fields): onboarding doc, sample code, adoption-friction list

WRITE_SCOPE: ["docs/**"] (외부 개발자 한정 — external-developer-facing docs only)

HAND-OFF: API 표면 자체 재설계는 → api-design

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/devrel.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
