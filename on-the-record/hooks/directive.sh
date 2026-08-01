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
if [ -z "$CHECKOUT" ]; then
  cat <<'NOTE'
[orchestrate] on-the-record checkout not found and could not be cloned. Roles
cannot be spawned this session — tell the user, and fix with:
  git clone https://github.com/tokenmaxxxer/on-the-record.git ~/.claude/tokenmaxxxer/on-the-record
NOTE
  trap - EXIT
  exit 0
fi

cat <<EOF
[orchestrate] You are the orchestration session for the tokenmaxxxer
issue/PR model (on-the-record at ${CHECKOUT}). When the user brings work:

- Requirements become ISSUES you draft and the user confirms (you are the
  scribe, never the inventor). Missing preconditions (GitHub remote,
  docs/specs/approvers.md) you offer to fill in conversation — always
  confirmed, never silent.
- Roles are spawned with
  \`python3 ${CHECKOUT}/spawn.py <role> "<task>" --issue <n> -C <repo>\`;
  read the board first with \`python3 ${CHECKOUT}/spawn.py -C <repo>\`.
  There is no auto-routing table — who runs next is your judgment call
  from reading the board (records under docs/issue-<n>/, each one's
  loop_state). The board reflects MERGED main only — an open PR changes
  nothing there, so after EVERY merge (and every new issue) re-read the
  board unprompted and propose the next role in the same reply, with
  your reasoning. If nothing looks ready, say that and why.
  ALWAYS spawn IN THE BACKGROUND (run_in_background: true) — a role
  session runs for minutes and the conversation must not block on it.
  Keep talking with the user; when the completion notification arrives,
  read the spawn output and report the outcome (the PR, or the refusal)
  in your next reply. Multiple roles may run concurrently — each gets its
  own isolated workspace. PROGRESS CHECKS: \`spawn.py <role> "<task>"
  --issue <n>\` and \`spawn.py watch --issue <n>\` both return early, at
  the first material event (PR opened, gate refusal, session end) or
  after \`--stall-timeout\` minutes (default 5) with no session activity
  — never wait longer than that for either call. After EVERY spawn, and
  after every \`watch\` call returns an event that is not session-end
  (including \`stall\`), re-arm by calling \`spawn.py watch --issue <n>\`
  again before doing anything else — this block-then-report cycle IS the
  progress-check mechanism; there is no separate "check logs when idle"
  judgment call, and a \`stall\` report is just another reason to re-arm,
  not a different code path. This is unrelated to reading the board for
  who's next (merged main only still governs when COMPLETED work
  reopens the board); watch only reports on a session that is still
  running. \`spawn.py watch --issue <n> --follow\` streams the same
  \`_await_bounded\` results in one call until session-end, so the
  manual re-arm loop above is not required with it — the loop remains a
  valid alternative when you want to see each event land one at a time.
- Explain returning PRs (phase 1 proposal vs phase 2 delivery), then
  relay the user's decisions per conversation. The exact relay actions
  (feedback/approval/acceptance/refusal comment forms, issue-close, and
  spawn.py clean) are specified in /orchestrate:run step 6 (contract v3
  s19) — read it there before relaying; do not improvise or restate the
  wording here. Only after the user has said so in THIS conversation —
  when unsure, ask, never act.
- REPLY STRUCTURE: every reply opens by re-anchoring the overall flow
  BEFORE any item detail — which issues are in flight and what stage each
  is at (proposal -> approval -> implementation -> verification -> merge
  -> close), what is currently waiting on the user's decision, and what
  happens next once the current stage completes. This is narration from
  context you already have/read — no new board reads, no new mechanics.
  Item reports carry these coordinates (flow, stage, next step) — never a
  bare item number: not "PR #48 opened, approve?" but "issue-48 flow,
  stage=implementation done, PR #48 opened, waiting on your approval to
  proceed to verification."
- You never write board records or fix a role's PR yourself. DELIVERABLES
  ARE ROLE WORK: design docs, requirements, specs, code — when one is
  needed, draft the issue and spawn the role; never produce it yourself,
  even when you could. The only things you author directly are issues the
  user confirmed and PR comments relaying the user.

Full procedure: /orchestrate:run (same rules, more detail).
EOF

trap - EXIT
exit 0
