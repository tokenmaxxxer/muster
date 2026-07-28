#!/usr/bin/env bash
# SessionStart: the orchestration directive. Installing this plugin IS the
# opt-in — every session it is enabled in becomes a conversational
# orchestrator for the issue/PR model. Informing only; role-session
# enforcement lives in core's gates. Kill switch: ORCHESTRATE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
# A spawned role session is never the orchestrator, even if the plugin leaks in.
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

MUSTER="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"

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
- Explain returning PRs (phase 1 proposal vs phase 2 delivery), then
  relay the user's decisions per conversation: feedback -> gh pr comment;
  approval -> a comment that is EXACTLY "APPROVE issue-<n>/<role>";
  acceptance -> gh pr merge; refusal -> gh pr close. Only after the user
  has said so in THIS conversation — when unsure, ask, never act.
- You never write board records or fix a role's PR yourself.

Full procedure: /orchestrate:run (same rules, more detail).
EOF

trap - EXIT
exit 0
