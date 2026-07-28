#!/usr/bin/env bash
# SessionStart: refresh the installed checkout. Nothing else does — the
# measured trap: `claude plugin update` reads only the version string and
# reports "already latest" forever. Quiet; offline failure is fine.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 0; fi' EXIT
set -uo pipefail
case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
MUSTER="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
git -C "$MUSTER" pull -q --ff-only 2>/dev/null || true
trap - EXIT
exit 0
