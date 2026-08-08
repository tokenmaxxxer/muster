# Scout brief — issue-466

This repo (`on-the-record`) is an internal dev-tool, not a consumer
product — its own prior architecture is the field to scout, per the
issue-466 task framing. Two questions: how do existing hooks under
`on-the-record/hooks/` structure themselves and their tests, and how does
existing anomaly-detection code elsewhere in `spawn.py` already work, so
the two new mechanisms extend established patterns rather than inventing
new ones.

## Existing hook pattern (`on-the-record/hooks/`)

All shipped hooks (`directive.sh`, `stop-gate.sh`, `contract-guard.sh`,
`deliverable-guard.sh`, `pr-preflight.sh`, `record-claim-guard.sh`,
`role-test-claim-guard.sh`, `spec-index-preflight.sh`,
`self-update.sh`) share one shape, read directly from `stop-gate.sh` and
`directive.sh` in full:

- `trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT`
  at the top — fail-closed: any unexpected non-0/2 exit becomes a 2
  (block), never silently passes.
- `case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac`
  — the one global kill switch, checked first, before any other work.
- `[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }` on hooks meant
  for the orchestrator only (`directive.sh`, `stop-gate.sh`) — a spawned
  role session is never the orchestrator even if the plugin leaks in.
  (Not universal — `pr-preflight.sh`/`contract-guard.sh` are `PreToolUse`
  hooks meant to fire inside role sessions too, so they skip this gate;
  the #374/#466 Stop hook belongs with the `CLAUDE_ROLE`-gated group
  since it is orchestrator-only, same as `directive.sh`/`stop-gate.sh`.)
- Payload read from stdin, JSON logic done in an embedded `python3 -c`
  block for anything beyond string matching (`stop-gate.sh`'s
  `STOP_PAYLOAD` env var + heredoc `CHECK` script is the exact template
  the #374 proposal already committed to reusing).
- Output shape: `{"hookSpecificOutput": {"hookEventName": "Stop",
  "additionalContext": "..."}}` for non-blocking, `exit 2` (or a JSON
  `decision: "block"` per the #374 proposal's tier-2) for blocking.
- `directive.sh`'s `_checkout_resolve()` — a 4-step probe order
  (`TOKENMAXXXER_CHECKOUT` env override → walk up from the hook's own
  path looking for `spawn.py` → marketplace clone path → self-clone
  fallback) — is the one already-established way any hook reaches
  `spawn.py` to run a command against it. The #374 proposal explicitly
  commits to reusing this order rather than reimplementing it. Confirmed
  present, unchanged, still the only such resolver in the directory.
- Tests: one `test_*.py` per hook script, at the same directory level
  (`on-the-record/hooks/test_pr_preflight.py`,
  `test_contract_guard.py`, `test_record_claim_guard.py`,
  `test_role_test_claim_guard.py`, `test_spec_index_preflight.py`) —
  fixture/subprocess-driven (invoke the shell script as a subprocess with
  a crafted stdin payload and env, assert stdout/exit code), not unit
  tests against extracted Python functions. `test_decision_queue_stopgate.py`
  should follow this exact convention: same directory, same
  subprocess-driven shape, one file per hook.

This confirms the #374 proposal's own design decisions (Stop-hook event
choice, `directive.sh`-derived checkout resolution, `ORCHESTRATE_OFF`/
`CLAUDE_ROLE` gates, embedded-python check body) are not novel — they are
the established pattern every other hook in the directory already
follows. Phase-2 has no open design question here beyond translating the
already-fully-specified #374 proposal into the #466-named file paths.

## Existing anomaly-detection pattern (`spawn.py`)

`roster_watchdog()` (`spawn.py:1635`) is the standing "check something and
say so loudly, do not silently continue" pattern in this codebase:
report-only ("아무 것도 고치거나 죽이지 않는다"), runs on the
orchestrator's own repeating tick (not a hook), non-zero exit on anomaly
(`spawn.py:1651-1654`), and calls `_auto_respawn_check()`
(`spawn.py:2001`) which classifies an entry as `crashed`/`stalled`/
`normal`/`in-progress` and only escalates to `_respawn_or_cap()`
(`spawn.py:1938`) for the `crashed` case — an explicit state-classify
step before any respawn action, never a bare "branch exists → reuse it"
assumption. This is the same shape the #428 fix needs to add to
`checkout_issue_branch()`: classify the branch's state (merged-into-base
vs genuinely ahead) before deciding to reuse or discard it, rather than
"local ref exists" being sufficient by itself — `checkout_issue_branch()`
today is the one place in the respawn path that skips this classify step
that `roster_watchdog()`'s own respawn path already performs one level up
(session liveness, not branch content). `WATCHDOG_SILENCE_MIN = 90`
(`spawn.py:1545`) is the numeric precedent for "how long is too long
before something quiet becomes loud" that #374's own two-tier ages (1h
below it, 4h above the incident's observed 4.7h) were calibrated against
— already argued in the #374 proposal's Rationale, re-confirmed by direct
read of `spawn.py:1545`.

## Skip-condition judgment

No full architecture sweep beyond the above was run for either sub-item,
for a stated reason each:

- **#374**: skip condition met. The full mechanism, rationale (including
  both rejected alternatives), and test plan already exist, fully
  written, in the approved-shape #374 proposal
  (`docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md`,
  frontmatter `status: proposed`) — issue #466 itself says this proposal
  "only described" the hook and asks for delivery, not redesign. This
  survey's job was to confirm nothing in the codebase has moved since
  that proposal was written (confirmed: `hooks.json`'s `Stop` array,
  `directive.sh`'s resolver, and `WATCHDOG_SILENCE_MIN` are all
  unchanged) and to name where the new acceptance-mandated file paths
  diverge (test file name/location) from that proposal's original plan.
- **#428**: skip condition met for the same reason, one layer deeper —
  `docs/issue-428/reports/implementation/survey.md` already contains a
  from-scratch mechanism survey with a real-git reproduction (not
  reasoning-only) and a fully specified fix
  (`docs/issue-428/proposals/2026-08-07-respawn-after-merge-and-silent-outcome.md`).
  This survey's job was to confirm that proposal's fix was never actually
  applied to `spawn.py` (confirmed: no `rev-list`/merged check exists in
  `checkout_issue_branch()` today, `test_spawn_fault_428.py` does not
  exist) and to check the two repro shapes #466 names against it
  (issue-441 matches directly and is independently documented live in
  `docs/issue-441/reports/execution-observation.md`; issue-58 does not
  match anything in this repo's own docs — flagged in survey.md rather
  than silently substituted).
