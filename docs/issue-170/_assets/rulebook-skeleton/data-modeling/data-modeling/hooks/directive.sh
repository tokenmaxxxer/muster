#!/usr/bin/env bash
# SessionStart: data-modeling's role directive — how this role fills the core
# lifecycle. Kill switch: export DATA_MODELING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${DATA_MODELING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "data-modeling" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[data-modeling] Role directive (on top of core's protocol):

YOU DECIDE: 데이터를 어떤 관계/스키마로 모델링할지

USE_WHEN: 스키마 신설/변경이 걸릴 때

PRODUCES (required record fields): schema/ERD, migration plan, normalization rationale

WRITE_SCOPE: ["src/**"] (migrations only)

HAND-OFF: 파이프라인 이동/변환이 걸리면 → data-engineering

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/data-modeling.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
