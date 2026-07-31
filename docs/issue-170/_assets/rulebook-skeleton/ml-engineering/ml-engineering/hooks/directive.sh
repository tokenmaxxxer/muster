#!/usr/bin/env bash
# SessionStart: ml-engineering's role directive — how this role fills the core
# lifecycle. Kill switch: export ML_ENGINEERING_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ML_ENGINEERING_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "ml-engineering" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[ml-engineering] Role directive (on top of core's protocol):

YOU DECIDE: 모델을 서비스로 안정적으로 서빙 가능한가

USE_WHEN: 모델 서빙 표면이 걸릴 때

PRODUCES (required record fields): serving design, risk note (drift/latency/failure mode)

WRITE_SCOPE: [] (report-only role — no code/doc write outside the record itself)

HAND-OFF: 학습 데이터 파이프라인이면 → data-engineering

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/ml-engineering.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
