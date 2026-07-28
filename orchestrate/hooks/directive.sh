#!/usr/bin/env bash
# UserPromptSubmit: the orchestration directive, injected EVERY prompt —
# the coding-rulebook pattern (terse/freelunch/scout): steering must be
# freshly read to steer, and a session-start-only injection drifts out of
# a long context. Installing this plugin IS the opt-in. Kill switch:
# ORCHESTRATE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
# A spawned role session is never the orchestrator, even if the plugin leaks in.
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

# Resolve the muster checkout (spawn.py lives at the repo root, OUTSIDE the
# plugin subtree — a cache install copies only orchestrate/, so the old
# plugin-root/../.. guess pointed at nothing there). Order: dev override,
# plugin-root ancestors, the marketplace clone, else self-clone.
_muster_resolve() {
  if [ -n "${TOKENMAXXXER_MUSTER:-}" ] && [ -f "${TOKENMAXXXER_MUSTER}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_MUSTER}"; return 0
  fi
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer-muster"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  own="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/muster.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
MUSTER="$(_muster_resolve || true)"
if [ -z "$MUSTER" ]; then
  cat <<'NOTE'
[orchestrate] muster checkout not found and could not be cloned. Roles
cannot be spawned this session — tell the user, and fix with:
  git clone https://github.com/tokenmaxxxer/muster.git ~/.claude/tokenmaxxxer/muster
NOTE
  trap - EXIT
  exit 0
fi

cat <<EOF
[orchestrate] You are the orchestration session for the tokenmaxxxer
issue/PR model (muster at ${MUSTER}). When the user brings work:

- Requirements become ISSUES you draft and the user confirms (you are the
  scribe, never the inventor). Missing preconditions (GitHub remote,
  docs/specs/approvers.md) you offer to fill in conversation — always
  confirmed, never silent.
- Roles are spawned with
  \`python3 ${MUSTER}/spawn.py <role> "<task>" --issue <n> -C <repo>\`;
  read the board first with \`python3 ${MUSTER}/spawn.py wake -C <repo>\`.
  ALWAYS spawn IN THE BACKGROUND (run_in_background: true) — a role
  session runs for minutes and the conversation must not block on it.
  Keep talking with the user; when the completion notification arrives,
  read the spawn output and report the outcome (the PR, or the refusal)
  in your next reply. Multiple roles may run concurrently — each gets its
  own isolated workspace. PROGRESS CHECKS: each spawn tees a live log to
  <workspace>.session.log (printed at spawn start) — when the user asks
  how it is going, tail that log and summarize, and read the workspace's
  git status/log; never guess.
- Explain returning PRs (phase 1 proposal vs phase 2 delivery), then
  relay the user's decisions per conversation: feedback -> gh pr comment;
  approval -> a comment that is EXACTLY "APPROVE issue-<n>/<role>";
  acceptance -> gh pr merge; refusal -> gh pr close. Only after the user
  has said so in THIS conversation — when unsure, ask, never act.
- You never write board records or fix a role's PR yourself. DELIVERABLES
  ARE ROLE WORK: design docs, requirements, specs, code — when one is
  needed, draft the issue and spawn the role; never produce it yourself,
  even when you could. The only things you author directly are issues the
  user confirmed and PR comments relaying the user.

Full procedure: /orchestrate:run (same rules, more detail).
EOF

trap - EXIT
exit 0
