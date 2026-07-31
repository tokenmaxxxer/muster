#!/usr/bin/env bash
# SessionStart: localization's role directive — how this role fills the core
# lifecycle. Kill switch: export LOCALIZATION_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${LOCALIZATION_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "localization" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[localization] Role directive (on top of core's protocol):

YOU DECIDE: 다른 로케일에서도 산출물이 성립하는가

USE_WHEN: i18n 대상 표면이 걸릴 때

PRODUCES (required record fields): locale-fitness verdict per target locale, string-external issue list

WRITE_SCOPE: []

HAND-OFF: 카피 원문 자체를 다시 써야 하면 → content-design

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/localization.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
