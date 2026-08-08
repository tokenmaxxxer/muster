#!/usr/bin/env bash
# SessionStart: refresh the installed checkout. Nothing else does — the
# measured trap: `claude plugin update` reads only the version string and
# reports "already latest" forever. Quiet; offline failure is fine.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 0; fi' EXIT
set -uo pipefail
case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
# Resolve the on-the-record checkout (spawn.py lives at the repo root,
# OUTSIDE the plugin subtree — a cache install copies only orchestrate/, so
# the old plugin-root/../.. guess pointed at nothing there). Order: dev
# override, plugin-root ancestors, the marketplace clone, else self-clone
# (preferring an existing new-path checkout, falling back to a still-present
# old-path checkout before re-cloning).
_checkout_resolve() {
  if [ -n "${TOKENMAXXXER_CHECKOUT:-}" ] && [ -f "${TOKENMAXXXER_CHECKOUT}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_CHECKOUT}"; return 0
  fi
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  own="$HOME/.claude/tokenmaxxxer/on-the-record"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  old="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$old/spawn.py" ]; then printf '%s' "$old"; return 0; fi
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] && git -C "$CHECKOUT" pull -q --ff-only 2>/dev/null || true
# #412: a self-clone (or any pre-existing checkout) can be shallow — a
# shallow checkout silently breaks history-dependent checks (log/blame
# ranges truncate at the shallow boundary). Detect it and attempt to
# unshallow; record the outcome either way so a still-shallow checkout is
# at least visible, not silent.
if [ -n "$CHECKOUT" ]; then
  marker="$CHECKOUT/.shallow-check"
  if [ "$(git -C "$CHECKOUT" rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]; then
    if git -C "$CHECKOUT" fetch -q --unshallow 2>/dev/null; then
      printf 'shallow=true unshallow=ok\n' > "$marker" 2>/dev/null || true
    else
      printf 'shallow=true unshallow=failed\n' > "$marker" 2>/dev/null || true
    fi
  else
    printf 'shallow=false\n' > "$marker" 2>/dev/null || true
  fi
fi
trap - EXIT
exit 0
