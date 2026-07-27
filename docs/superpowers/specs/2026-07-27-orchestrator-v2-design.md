---
kind: design
date: 2026-07-27
status: proposed
subject: orchestrator-v2
---

# muster as a Claude Code orchestrator — architecture review and v2 design

A four-lens architecture review (enforcement, human gates, coordination,
native-feature fit) ran against the current implementation, the contract, two
representative rulebooks, and the official Claude Code documentation, with
every load-bearing claim settled by experiment on this machine (claude CLI
2.1.220, keychain auth). Verdict, unanimous across all four lenses:
**sound-with-changes**. The session-per-role CLI foundation is right and every
alternative fails on enforcement grounds. Specific mechanisms change, several
defects must be fixed before the core migration, and the platform now covers
real chunks of muster's hand-built machinery.

## 1. The foundation holds — and why each alternative dies

Rulebook enforcement *is* plugin hooks firing in-session. Whatever spawns
roles must load each role's plugins, with hooks, in an isolated session, under
the sandbox, using keychain auth. Measured against that bar:

| alternative | fails because |
|---|---|
| Agent SDK driver | does not auto-enforce plugin hooks (documented parity gap: the `plugins` option loads skills/agents/commands/MCP, not hook enforcement); no sandbox option — isolation is delegated to external tooling |
| one session + native subagents per role | plugin scoping is session-level; a subagent cannot carry a different plugin set |
| agent teams | experimental, opt-in env var; no per-teammate plugin scoping; no session resumption |
| `--bare` isolation | never reads OAuth/keychain — requires ANTHROPIC_API_KEY, same disease that disqualified CLAUDE_CONFIG_DIR |
| MCP board server | rejected permanently (§4 below) |

Two claims from research were **refuted by experiment** and must not steer
design: (1) "parent plugin hooks don't apply to subagent tool calls" — false;
a `.*`-matcher PreToolUse hook logged the subagent's inner Bash call with
agent attribution, so hunter subagents stay gated; (2) "--allowed-tools ''
disables tools" — false; that flag is a permission allowlist. `--tools ""` is
the documented disable-all spelling.

One caveat keeps the foundation honest: headless hook firing is **measured,
not documented**. The hooks reference never states that hooks fire in `-p`
mode. The CLI auto-updates; a platform regression would remove every gate
while sessions keep exiting 0. Hence the canary (change M6).

## 2. Facts verified by experiment (claude 2.1.220, 2026-07-27)

1. `--plugin-dir` loads a plugin's hooks fully in headless: UserPromptSubmit
   (including for the initial `-p` prompt) and PreToolUse both fired from a
   probe plugin loaded by path. No marketplace, no install, no cache.
2. `--input-format stream-json` keeps one headless session open across
   injected user turns; UserPromptSubmit fired once per injected turn
   (`--output-format stream-json` additionally requires `--verbose`).
3. `claude -p --resume <full-uuid>` preserves conversation context; plugin
   hooks fire again only when `--plugin-dir`/`--settings` are re-passed
   (docs: those flags are not restored on resume).
4. Plugin hooks fire for subagent tool calls (same session id, agent-attributed).
5. **Headless default permissions silently deny Write.** No file was created;
   the session looked successful from the outside; the denial is visible only
   in `--output-format json`'s `permission_denials` — which spawn.py never
   reads. This is a live muster defect: roles can write only through
   sandboxed Bash today, and it is the best explanation of the measured
   "exits 0 having done nothing" sessions.
6. `--permission-mode acceptEdits` fixes 5 — and a PreToolUse exit-2 gate
   still blocks the Write under acceptEdits. Permission mode removes the
   nobody-to-answer prompts; gates remain the deny plane. Sandboxed Bash is
   auto-allowed; unsandboxed fallback is already forced off.
7. `--output-format json` returns session_id, total_cost_usd, usage,
   num_turns, permission_denials, is_error, terminal_reason, modelUsage.
8. Verified present on 2.1.220: `--json-schema`, `--tools`, `--session-id`,
   `--fork-session`, `--no-session-persistence`, `--include-hook-events`,
   `--worktree`, `--max-turns`, `--append-system-prompt[-file]`.

## 3. Defects found (fix before the core migration)

**D1 — the orchestrator can mint a human-consent token.** A muster-spawned
session's UserPromptSubmit carries orchestrator-authored text (the stdin task
arrives verbatim as the prompt — measured). A spawn task of exactly
`APPROVE <kind> <subject>` would mint an `actor: user` token with no human
involved. mint.sh's only guard is TOKENMAXXXER_UNATTENDED — which nothing in
muster sets. Three of four judges flagged this independently.

**D2 — token forgery by writes.** (a) warrant's path-ownership-gate denies a
foreign-record write only when the tail has no `/` or ends in `.md` —
`records/<subject>/tokens/<kind>.token` passes both tests, so the coding role
can Write a forged approval token (verified against the gate source). qa's
gate already denies everything not qa-owned; that shape must become the
kernel rule. (b) `/orchestrate:run` pre-approves `Bash(cp:*)` in the user's
interactive session, which carries **zero** rulebook gates (rulebooks are
deliberately globally disabled) — a pre-approved cp can plant a forged token
file silently.

**D3 — silent Write denial in every role session** (fact 5). Operational, not
security: the failure mode is roles silently unable to work.

**D4 — judge tokens are dead on arrival.** consent.consume() hard-refuses
`actor != "user"`, while the pending judge.py plan mints `actor: judge`. The
two halves of the unattended design, as currently written, cannot compose.

**D5 — wake evaluation violates contract §6.** The qa row fires whenever any
commit ever touched src|tests (no consumption tracking), coding re-wakes
forever on a persistent `verdict: go`, review on persistent
`loop_state: landed`. A driver loop built on this would spin; even the manual
report shows stale wakes.

**D6 — repo-config refusal has gaps.** REPO_CONFIG omits `.claude/agents/`
(project agent files honor hooks/permissionMode frontmatter per the
sub-agents doc) and `.mcp.json` (repo-authored process execution) — the same
class as the measured repo-committed-hook sandbox escape.

**D7 — the update-dance disease ships in core.** Rulebooks stay "already
latest" at 0.1.0 because `claude plugin update` compares the version string.
Docs: for git-distributed plugins **without** a `version` field, the commit
SHA is the version and every commit is an update. core/plugin.json carries
`"version": "0.1.0"` today — about to reproduce the measured pitfall in the
repo built to cure duplication.

**D8 — ledger reads the v1 board.** collect.py reads root `review-record.md`,
a location spawn.py itself lists as legacy; on every v2 repo the ledger
reports "no review cycles ever".

## 4. Decisions pinned (alternatives rejected with reasons)

**Die-and-respawn stays the only gate-crossing mechanism.** A human gate is
not a paused conversation; it is a durable board-state transition awaiting an
out-of-band single-use token that survives session death by construction. The
board is the sanctioned context carrier (write-then-stop); a role that cannot
resume from board state reveals a board-content defect, not a lifecycle one.
Fresh sessions also preserve protocol invariant 6 (idempotent retries) and
§12's once-per-role-entry first-read semantics.

**stream-json keep-alive is rejected as an approval channel.** Every injected
"user turn" is authored by whichever process holds stdin. In `/orchestrate:run`
flows that holder is downstream of a model. Mechanically indistinguishable
from the human's own turn, it dissolves the exact trust premise the challenge
line exists to enforce. (Verified to *work*; rejected on trust, not
capability.)

**`--resume` is not adopted for role sessions now.** If ever: only after JSON
capture exists (needs session_id), only with settings/plugin flags re-passed
(documented as not restored — a bare resume would re-attach the user's global
plugins, regressing the measured merge pitfall), only from the same project
directory, and only with the token already minted out-of-band. Recorded here
so it is not relitigated.

**The MCP board server is rejected permanently.** MCP tool use is voluntary —
a session holding Write/Edit/Bash bypasses any board server, so the PreToolUse
deny plane must exist regardless; the server would add a component and remove
none. Role identity would rest on a caller-supplied claim (every session loads
the same MCP set — no per-role MCP scoping), where the hook plane gets
identity by construction from per-session plugin scoping. And the contract's
git-native properties (§12 staleness via `git log`, drift by content hash,
commit-level audit) would be lost or reimplemented.

**The driver is deterministic muster code, not a model and not the cloud.**
Not the orchestrate plugin (an LLM must not be the scheduler); not
cron/Routines (Anthropic-cloud execution cannot reach keychain auth or the
local Seatbelt sandbox).

**The attended approval channel is mechanical, and relays are forbidden.**
Two first-class paths only: (a) the human types the challenge line in their
own interactive session with core enabled — a genuine UserPromptSubmit, one
hop, no model in between; (b) `spawn.py approve <kind> <subject>`, which
requires stdin `isatty()` — Claude's Bash tool has no TTY, so the command
fails closed when a model invokes it. The orchestrator's job is to *print*
the exact line, never to relay it.

**The judge moves out of the hook and into muster's loop.** Same module, same
fail-closed verdict discipline (APPROVE/REFUSE/HOLD), different call site:
the session stops at the gate; muster classifies "waiting-on-human-gate"; in
unattended mode muster runs the judge between sessions with muster-synthesized
settings (global plugins force-disabled), mints `actor: judge`, respawns.
This removes the in-hook claude subprocess and with it the hook-timeout
fail-open path and reentrancy; CORE_OFF=1-for-the-judge is replaced by real
settings isolation muster already owns.

## 5. Changes

muster-side (M), core-side (C), rulebook-side (R). Priorities follow the
judges' consensus; every HIGH is security- or correctness-critical.

- **M1 (HIGH, fixes D1)** — spawn.py stamps every spawned session:
  `TOKENMAXXXER_SPAWNED=1` in the session env (process env and settings `env`
  both, defense in depth). Keep `TOKENMAXXXER_UNATTENDED` as the separate
  human-absent flag (opt-in `--unattended`; bench sets it) so attended spawns
  do not break. mint.sh (C1) treats SPAWNED as mint-inert.
- **M2 (HIGH, fixes D3)** — spawn adds `--permission-mode acceptEdits`.
  Gates remain the deny plane (verified under acceptEdits).
- **M3 (HIGH)** — spawn adds `--output-format json`; capture session_id,
  total_cost_usd, usage, num_turns, permission_denials, is_error; print the
  result text for the human; append one JSONL ledger line per spawn (role,
  subject, session_id, cost, turns, rc, gates verdict, rulebook sha, contract
  hash, board delta); classify the outcome: errored / progressed (board
  changed) / waiting-on-human (unchanged + blocked human row) /
  silent-failure (exit 0, nothing changed) — the measured silent-death mode
  becomes loud. Report-only: muster still does not judge or retry.
- **M4 (HIGH, fixes D6)** — REPO_CONFIG += `.claude/agents`, `.mcp.json`.
- **M5 (HIGH, part of D2)** — orchestrate/run.md: drop `Bash(cp:*)` from
  allowed-tools (the one legitimate cp goes through the normal prompt).
- **M6 (HIGH)** — hook-firing canary: a throwaway probe session with logging
  hooks; if UserPromptSubmit/PreToolUse do not fire, spawn halts. Converts the
  architecture's foundational measured-not-documented assumption into a
  monitored invariant. Run it as part of `spawn.py doctor` (new), invoked
  automatically before first spawn per CLI version.
- **M7 (MEDIUM, fixes D5)** — wake-consumption tracking per contract §6:
  muster-side store (never in the target repo) of content hashes per fired
  row; a row re-fires only when its cited state changed. Precondition for M8;
  also fixes today's stale manual report.
- **M8 (MEDIUM)** — `spawn.py drive -C <repo>`: serial while-loop —
  wake-evaluate → dispatch exactly one mechanically-judged row → re-evaluate.
  Stops (to the human) on: empty woken set; dispatched spawn produced no
  board delta; only human/judgment rows remain (product, ops, §15 re-verify,
  §18 round-end, §19 scope approval). Prints the exact challenge line when it
  stops at a human gate.
- **M9 (MEDIUM)** — `spawn.py approve <kind> <subject>`: TTY-guarded
  (`isatty()`) direct mint through core's token format, for headless-
  orchestrated flows. Prints what it minted; refuses without a TTY.
- **M10 (MEDIUM)** — `--plugin-dir` spawning: resolve each plugin dir from
  the rulebook checkout's marketplace.json; pass one `--plugin-dir` per
  plugin (+ core) instead of marketplace install. Deletes warm-up billed
  spawns, install verification, ghost-entry handling, and the
  registry-name-wins hazard; enables SHA-pinned ablations. Keep `--settings`
  (sandbox + global enabledPlugins:false synthesis — still required; --bare
  is not usable). Adopt behind M6's canary. GitHub-only rulebooks: muster
  clones/pulls into its own cache dir and passes that path — one code path.
- **M11 (LOW)** — spawn task composition: wake reason + board digest +
  cited record paths, so sessions start at their inputs.
- **M12 (LOW, fixes D8)** — ledger/collect.py reads the v2 board
  (docs/reports/records/<subject>/review.md), v1 as labeled fallback.
- **M13 (LOW)** — shared role-file kernel gains
  `sandbox.filesystem.denyWrite: ["$HOME/.claude"]` (hook processes are
  sandbox-exempt, so gates keep working); gate_report gains a
  records-ownership line (flag changed paths under records/<subject>/ the
  spawned role does not own, tokens/** included).

- **C1 (HIGH, fixes D1)** — mint.sh exits on TOKENMAXXXER_SPAWNED alongside
  CORE_OFF/TOKENMAXXXER_UNATTENDED; add the test: challenge line as the -p
  initial prompt with the marker set must NOT mint.
- **C2 (HIGH, fixes D2)** — core ships a deny-only PreToolUse gate refusing
  every role's writes to `records/*/tokens/**` and any `*.token` under
  records/; deny-only-check gains a forgery probe proving all nine roles
  covered.
- **C3 (HIGH, fixes D4)** — consent.consume(tokens_dir, kind,
  allowed_actors=("user",)); gates pass ("user","judge") only under the
  unattended flag, so a stale judge token can never satisfy an attended gate.
  The four §8/§19 human-reserved kinds never include "judge" — encoded in the
  contract, not ad hoc in a gate.
- **C4 (HIGH)** — judge.py corrections: `--tools ""` (not --allowed-tools);
  verdict via `--output-format json --json-schema` (any deviation → False);
  `--max-turns 1`; judge runs with a muster-synthesized settings file
  (global plugins disabled); invoked from muster's loop per §4, not from a
  hook; stdin closed after the prompt.
- **C5 (HIGH, fixes D7)** — publish core without a `version` field; drop the
  field from each rulebook's plugin.json during its migration PR. After one
  verified update cycle, shrink spawn.py's update dance.
- **C6 (MEDIUM)** — the contract canonical ships inside the core plugin;
  a deny-only SessionStart/root-validation check compares the target repo's
  copy by hash and refuses on mismatch. The target-repo copy stays (it is
  the opt-in marker and the in-repo material); the 9 rulebook copies become
  conformance-checked mirrors. Converts the "§19 sync to 10 copies" item
  from manual synchronization into enforced conformance.
- **C7 (MEDIUM)** — a deny-only guard for gate-free sessions: refuse writes
  under docs/reports/records/** when CLAUDE_ROLE is unset (user-scope
  enabled, CORE_OFF-killable). Protects the board from the orchestrator's
  own interactive session, whose only protection today is prose.

- **R1 (migration)** — warrant path-ownership-gate adopts qa's deny-everything-
  not-owned shape (D2a); feasibility migrates after qa/ops or fixes its 9 red
  suite cases first; migration step 6 authors ux-design/reflect domain
  content as skills with auto-trigger descriptions + one shared core skill
  for the handoff protocol; directives shrink to naming human-only
  transitions (retires directive.sh ×13 and qa's directive-drift-check).

## 6. Revised roadmap

**Status, 2026-07-27 (end of day): items 1–9 are landed and merged.** What is
left is item 10, the per-role migration, plus the two decisions in §4 that only
the human can make. Three things were learned by shipping the rest:

- The judge's CLI contract had never been executed; running it found a
  `judge-log.md` test that could not fail (it asserted on constants, and the
  log was accumulating in the shared system temp dir across runs).
- `spawn.py`'s own path had never been run end to end; running it found a
  gate-blocked session being reported as `silent-failure`, which is the
  opposite disposition from a gate doing its job. `refused` is now its own
  outcome.
- The driver, on its first real run, dispatched a `qa` session carrying a
  rulebook commit that predated a security fix merged hours earlier. That
  moved M10 from cleanup to correctness — sessions now load rulebooks by
  path, with no cache in between.

Order matters; each item names what it supersedes in the 2026-07-27 plan.

1. **core Task 3 review completes** (in flight, unchanged).
2. **Consent hardening slice** — C1 + C3 + M1 + M4 + M5 (all small, all
   security). Amends: mint.sh (in review), consent.py API, spawn.py env,
   REPO_CONFIG, run.md. Blocks everything below.
3. **core Task 4 (judge)** — as amended by C4 and §4's call-site decision.
4. **core Task 5 (conformance)** — deny-only-check + C2's forgery probe.
5. **core Task 6 (publish)** — as amended by C5 (no version field).
6. **muster observability slice** — M2 + M3 + M6 (+ M12, M13). Independent
   of 3-5; can land in parallel after 2.
7. **Contract §19 sync** — via C6 (in-core canonical + hash conformance),
   superseding the manual 10-copy sync item.
8. **Wake correctness + driver** — M7 then M8 + M9 + M11. Supersedes the
   README's open "WAKES-ON watcher" item with a concrete, bounded design.
   The judges affirm the README's sequencing: drive one subject end-to-end
   manually before trusting M8.
9. **--plugin-dir spawning (M10)** — after M6 exists; shrinks spawn.py
   substantially; replaces migration step 3's two-marketplace `also:` merge
   (core arrives as one more --plugin-dir instead).
10. **Per-role migration** — as planned, with R1's ordering fix and C2/C5
    applied per repo; review/verify merge stays the one human decision the
    design cannot settle.

What this roadmap deletes outright: the stream-json approval channel (never
planned, now explicitly rejected), the MCP board server (idea permanently
closed), `--bare`/CLAUDE_CONFIG_DIR isolation (re-confirmed dead), and —
once M10 survives a canary cycle — the warm-up spawns, install verification,
ghost-entry detection, and most of the update dance.

## 7. What was measured vs. inferred

Everything in §2 and every D-item: measured on this machine, this CLI
version, cited to file:line or reproduced live during this review. The four
judge verdicts each re-verified their load-bearing citations in-repo before
relying on digests. Known residual inference: `--plugin-dir` has been proven
with a probe plugin, not yet with a full nine-plugin rulebook (M10 is gated
on exactly that canary); headless hook firing remains undocumented upstream
(M6 exists because of it).
