#!/usr/bin/env bash
# SessionStart: user-discovery's role directive — how this role fills the core
# lifecycle. Kill switch: export USER_DISCOVERY_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${USER_DISCOVERY_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "user-discovery" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[user-discovery] Role directive (on top of core's protocol):

YOU DECIDE: 이 문제가 실제 사용자의 고통인가

USE_WHEN: 가설 검증을 위해 사용자 인터뷰가 필요할 때

PRODUCES (required record fields): interview script, per-interview evidence log, pain-confirmed|not-confirmed verdict

WRITE_SCOPE: [] (report-only role — no code/doc write outside the record itself)

HAND-OFF: 검증된 가설을 스펙화하면 → requirements-engineering

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/user-discovery.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
