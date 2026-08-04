files: (frozen write set for phase 2)
- `spawn.py`
- `test_spawn.py`
- `docs/handbooks/operations.md`
- No new dependency, no new env var, no schema/migration.

## Request (paraphrased)

A headless role session that splits work across `Agent`/`Task` subagents and
then narrates "I'll continue once the workers finish" has nothing left in
its own main loop once that turn ends — the process exits, cleanly, not
crashed (`rc=0`, `is_error=False`). This repo already computes the correct
signal for that exact shape (`uncommitted-work`/`failed-no-commit`,
spawn.py:2884-2911) and already prints a manual-resume hint
(spawn.py:2876-2880), but nothing auto-acts on it: the existing capped
auto-respawn machinery (issue #132) is wired only to the `crashed` verdict,
which this incident never produces, because its roster entry is removed
synchronously before any watchdog tick could ever see it as dead-but-
registered (survey.md). The issue's own text asks this proposal to judge how
much of the fix belongs in this repo (spawn.py/watchdog side) versus in
role-prompt/contract text (core side) — see Rationale's scope-split
judgment.

## Constraints

- Reuse the existing bounded-retry-then-escalate machinery from issue #132
  (`RESPAWN_MAX_ATTEMPTS = 2`, `runs/respawn_state.json`, the idempotent
  cap-comment) rather than inventing a second counter/state family.
- Must never bypass the approval gate — an auto-respawn only re-runs the
  *same* issue/role/task a human already authorized once by spawning it the
  first time (same rule issue #132's proposal stated).
- Must not fire on outcomes that reflect a legitimate stop needing a human,
  not a bug: `refused` (a gate correctly blocked the session) and
  `waiting-on-human` — auto-respawning either would just hit the same wall
  again.
- Any new claim/state file reuses the existing `O_CREAT|O_EXCL` claim
  family/naming convention (`.respawn-claim-{ts}` / `.spawn-claim`) so
  `clean`'s existing sibling-file glob catches it with no change to `clean`
  itself (same constraint issue #223 held itself to).
- The role-prompt/contract text change acceptance criterion 1 asks for is
  out of this repo's reach: `tokenmaxxxer-core` and
  `tokenmaxxxer/implementation-rulebook` are not checked out here, and this
  branch's `write_scope` (`roles/implementation.json:18`) has no path into
  either repo (survey.md). This proposal does not attempt it inside this
  repo.

## Rationale

**Primary rejected alternative: extend `session_end_verdict()`'s trichotomy
with a 4th value by inspecting the `session-end` event's own `detail` field
(spawn.py:2951 — already the outcome string) instead of only checking
whether the event exists, then let `roster_watchdog()`/`_auto_respawn_check()`
act on it the same way they already act on `crashed`.** This is a real fork
in the design space, not a strawman: it is the same file, the same
established pattern (issue #132), and is the first place a reader familiar
with this codebase would look. Rejected because `roster_remove()`
(spawn.py:2849) already deletes the roster entry synchronously, in-process,
right after `proc.wait()` returns — for this exact incident (a normal exit,
no crash) there is never a dead-but-registered roster entry for any
subsequent watchdog tick to find, no matter how the trichotomy is extended.
That absence is precisely what makes this incident different from
`crashed`/`stalled` in the first place (survey.md's "why it doesn't reach
this case" section). A same-process trigger, added right where `outcome` is
already finalized (spawn.py:2893-2912), needs no new detection logic at all
— the signal already exists — and has zero propagation delay, which matters
because a one-shot headless invocation may have no watchdog cadence running
afterward at all to eventually notice anything.

**Second alternative considered and rejected: also trigger on bare
`silent-failure` (no uncommitted diff), so every exit-0-nothing-happened
session gets a retry.** Rejected because a genuinely idle "nothing to do
this turn" session (rc=0, no board delta, no uncommitted changes, no
permission denials) is a legitimate, correct outcome — not this issue's bug.
Auto-respawning it would burn the attempt cap on non-incidents and could
loop on a task that is simply already done. Scoping the trigger to outcomes
with affirmative evidence of abandoned-but-attempted work
(`uncommitted-work`, and `failed-no-commit` reached via the downgrade path)
keeps the false-positive rate at the level issue #132 already accepted for
`crashed`.

**Scope-split judgment** (the issue's own explicit ask): this proposal takes
the otr-side path in full — acceptance criteria 2 (auto-recovery) and 3
(documenting the resume path) both land here. It deliberately does not touch
role-prompt/contract text (criterion 1) inside this repo, for the reason
given in Constraints — not because criterion 1 doesn't matter, but because
this repo has no write path to where that text actually lives.

## What will be done

1. `spawn.py`: factor `_auto_respawn_check()`'s core sequence — claim via
   the atomic O_EXCL file, check the attempt cap, replay `.task.txt` through
   `_spawn_one()`, else post the idempotent cap comment (spawn.py:1611-1678)
   — into a helper callable from two sites: the existing watchdog
   `crashed`-path, and a new call added at the end of `_spawn_one()`'s own
   run.
2. `spawn.py`: once `outcome` is finalized (after `fail_closed_downgrade()`,
   spawn.py:2893-2912), when `issue is not None` and `outcome` is in
   `{"uncommitted-work", "failed-no-commit"}`, call the shared respawn
   helper before the bounded child's terminal `session-end` event
   append/exit (spawn.py:2948-2952). Same attempt-cap state
   (`runs/respawn_state.json`) and cap-comment marker family issue #132
   established, with the printed/comment text naming which trigger fired
   (self-triggered-abandoned vs watchdog-observed-crashed) so an operator
   reading it later can tell them apart.
3. `test_spawn.py`: new fixture-driven tests (style matching
   `AutoRespawnClaim`/`FailClosedDowngrade`) covering: fires on
   `uncommitted-work`; fires on `failed-no-commit`; does not fire on
   `refused`/`waiting-on-human`/bare `silent-failure`; respects the existing
   attempt cap and posts the same cap-comment shape on exhaustion; does not
   double-claim when the self-trigger and a concurrently-running watchdog
   tick observe the same abandoned workspace (reuses the existing atomic
   claim's race protection — no new concurrency mechanism).
4. `docs/handbooks/operations.md`: new section documenting (a) what
   `uncommitted-work`/`failed-no-commit`/`silent-failure` mean and how they
   differ from `crashed`/`stalled`, (b) that these abandoned-work outcomes
   now self-trigger a capped auto-respawn the same way `crashed` already
   does, (c) the manual resume command
   (`spawn.py <role> "<task>" --issue <n>`, which resumes the existing
   workspace/branch) for when the cap is already exhausted or a human wants
   to intervene sooner than the cap.
5. This proposal document itself is the recorded scope decision for
   acceptance criterion 1 — no file in this repo changes to address it; a
   human needs to open a separate issue against `tokenmaxxxer-core` and/or
   `tokenmaxxxer/implementation-rulebook` for that half.

## Out of scope

- Any change to role-prompt/directive text (the `freelunch`, `scout`, or any
  other core-injected directive) — lives outside this repo; acceptance
  criterion 1 needs its own issue elsewhere (see Rationale).
- Extending the new auto-trigger to `errored`, `progressed-dirty-tree`, or
  bare `silent-failure` — each is a different failure shape (a real runtime
  error; partial progress already committed with a dirty tree; or
  genuinely nothing to do) than the abandoned-mid-delegation pattern this
  issue describes (see Rationale's second rejected alternative for the
  `silent-failure` case).
- Any change to `roster_watchdog()`/`session_end_verdict()`'s own trichotomy
  logic or its existing `crashed`-triggered path — this proposal adds a
  second, independent trigger site next to it, not a replacement.
- A combined attempt-budget policy across the watchdog-crashed and
  self-triggered-abandoned paths for the same workspace — both paths call
  the same shared helper against the same per-key counter in
  `runs/respawn_state.json`, so this falls out for free; nothing separate to
  design.

## How you'll know it worked

- `python3 -m pytest test_spawn.py -k "SelfTriggeredRespawn or AutoRespawnClaim or FailClosedDowngrade" -v`
  — new tests pass; both pre-existing classes stay green with unchanged
  assertions.
- Manual dry run: reproduce the incident shape (a task that leaves a
  workspace with an uncommitted file and no new commit, `rc=0`, no gate
  refusal) and confirm `_spawn_one()` triggers exactly one respawn attempt
  without waiting for any `spawn.py watchdog` invocation; a second forced
  repeat hits the cap and posts exactly one issue comment; a third repeat
  posts no second comment.
- `docs/handbooks/operations.md` contains a section documenting the
  abandoned-work outcomes, the new auto-respawn behavior, and the manual
  resume command — satisfies acceptance criterion 3.
- Acceptance criterion 1 stays explicitly unchecked in this repo, with this
  proposal recorded as the documented reason, rather than silently dropped
  or faked as done.
