#!/usr/bin/env bash
# SessionStart: brand-design's role directive — how this role fills the core
# lifecycle. Kill switch: export BRAND_DESIGN_CYCLE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${BRAND_DESIGN_CYCLE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ "${CLAUDE_ROLE:-}" = "brand-design" ] || { trap - EXIT; exit 0; }

cat <<'DIRECTIVE'
[brand-design] Role directive (on top of core's protocol):

YOU DECIDE: 브랜드 정체성이 시각적으로 일관되는가

USE_WHEN: 브랜드 자산 신설/변경이 걸릴 때

PRODUCES (required record fields): brand guide entry, asset spec, consistency check vs existing guide

WRITE_SCOPE: design-system source paths (TBD at execution)

HAND-OFF: 토큰 시스템화 구현은 → ux-engineering

BOUNDARY CASE: if the work in front of you drifts outside `decides` above,
stop and hand off per the arrow — do not silently absorb another role's
scope. Record the hand-off point in this role's record before opening the
next role's session.

RECORD: docs/issue-<n>/reports/brand-design.md, phase-gated per contract v3 s19
(phase-1 homes only pre-Approve; this record is phase-2 output).
DIRECTIVE
