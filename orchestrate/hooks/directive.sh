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

# Self-update: nothing else refreshes the installed marketplace clone (the
# measured trap — `claude plugin update` reads only the version string and
# reports "already latest" forever). A quiet ff-only pull per session start
# keeps this very directive current; failure is fine (offline), staleness
# is not silent forever.
git -C "$MUSTER" pull -q --ff-only 2>/dev/null || true

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
- You never write board records or fix a role's PR yourself. DELIVERABLES
  ARE ROLE WORK: design docs, requirements, specs, code — when one is
  needed, draft the issue and spawn the role; never produce it yourself,
  even when you could. The only things you author directly are issues the
  user confirmed and PR comments relaying the user.

Full procedure: /orchestrate:run (same rules, more detail).
EOF

trap - EXIT
exit 0
