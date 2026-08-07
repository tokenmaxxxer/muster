# Survey — issue #376 (capability that exists and cannot be found)

## Scope of this survey

Confirmed each of the four named instances against the current tree
(2026-08-07), and checked which existing mechanisms (`record_fulfils_diff`,
#330's "reach check", #333's derived-numbers, #363's generator framing)
already cover this ground.

## Instance confirmation

**1. `decision_queue`** — `gates/flows.py:257-325` builds it with
`opened_at`/`age_hours`/`awaiting`; fully spec'd at
`docs/specs/flows-schema.md:36-59`; tested (`test_spawn.py:3620-3660+`).
`grep -rn decision_queue` outside `gates/flows.py`, its tests, and
`docs/specs/flows-schema.md` returns nothing — no orchestrator contract,
role JSON, or CLAUDE.md references it. Confirmed: documented, tested,
spec'd, zero declared consumer.

**2. `Stop` hook** — `on-the-record/hooks/hooks.json:1-26` (the only
production hooks.json) declares exactly three events: `SessionStart`,
`UserPromptSubmit`, `PreToolUse`. No `Stop` entry. No other file in the
repo (outside unrelated third-party rulebook-skeleton assets under
`docs/issue-167/_assets/`, `docs/issue-170/_assets/`) mentions `Stop` or
`last_assistant_message`. This is a platform capability (Claude Code's
hook system) that has no footprint in this repo at all — it cannot be
found by reading this repo's own files, because there is nothing here to
find. #318/#320 read `hooks.json`'s 3 configured events and correctly
reported that fact; the issue is that "3 events configured" was reported
as "3 events exist," conflating repo configuration with platform
capability.

**3. `gates/gates.py::writeset()`** (`gates.py:171-190`) — reads
`spec.md` (line 183); confirmed zero `spec.md` files exist anywhere under
`docs/issue-*/`. Distinct defect from #4: `writeset` is registered in the
`ALL` dict (`gates.py:527-531`) but **never called anywhere in
`gates/ci.py::check()`** — not gated by `closes_only`, just absent from
the call graph entirely (`grep -n "writeset(" gates/ci.py` → no hits).

**4. `gates/record_enums`** (`gates.py:296-335`) — wired at
`gates/ci.py:354`, but that line sits after the `if closes_only: return
bad` short-circuit at `ci.py:346`. The only CI workflow
(`.github/workflows/plan-aware-closes-gate.yml:49`) always invokes
`gates/ci.py ... --closes-only`. So `record_enums` (and
`record_wellformed_in`, `record_no_tool_residue_in`,
`record_fulfils_diff`, `role_scope`, dep checks — everything after line
346) never runs in real CI; only in local/manual invocation or
`test_gates.py`. Confirmed drift: `roles/implementation.json:20`
declares `loop_state` enum `[scope-proposed, scope-approved, in-progress,
landed]`; actual values across `docs/issue-*/reports/implementation.md`
are `complete, delivered, done, landed, phase-2-complete, progressed` —
only `landed` overlaps.

Instances #3 and #4 are the same *family* of defect (a registered gate
that cannot fire under the real CI trigger) but different *mechanisms*:
#3 is total non-invocation; #4 is invocation gated behind a flag CI
always sets. A single "is this registered gate reachable from the actual
CI entry point" check catches both.

## Existing mechanisms checked for overlap

**`record_fulfils_diff`** (`gates.py:408-459`, wired `ci.py:357` — itself
dead in real CI per the #4 finding above). Binds a prose claim
(`fulfils: delete|create|move <path>`) to a git-diff fact (file
status D/A/R/C). Opt-in per record line. This is a real precedent for
"bind a claim to a mechanical check," but the claim shape is narrow
(file-path operations against a diff) and does not generalize to "is
field X consumed anywhere" or "is function Y reachable from CI" — those
need a different ground truth (static call-graph / grep over the source
tree, not a git diff). Does not extend to cover #376 as-is.

**#330 "reach check"** — not a mechanism, a prose convention. No gate
function exists; `#330` appears only as a citation asking authors to
write a "## What reaches" section by hand in implementation records
(e.g. `docs/issue-360/reports/implementation.md:53`). Nothing enforces
its presence or correctness. #330 is itself open/unimplemented. Since
it depends on the human author noticing what a change reaches, it has
the identical failure mode as #318/#320's manual hooks.json read: it
finds what the writer thought to look for, not what is mechanically
derivable. Not usable as a dependency for this issue's mechanism.

**#333 "derived-numbers"** — no implementation exists anywhere in the
tree (`docs/issue-333/` does not exist; zero code hits). Open,
unimplemented. Nothing to build on.

**#363 "generator"** — a defect-analysis convention (not code): a
record should state whether a fix removes the generator of a defect
class or only patches named instances (worked example:
`docs/issue-360/reports/implementation.md:71-90`). Directly informs this
proposal's design choice below (target the generator: "registered gate
not reachable from the real CI entry point," not just `writeset`/
`record_enums` by name).

## What is and is not derivable from the repo

- **Derivable**: whether a function registered in `gates.ALL` is ever
  called by `gates/ci.py::check()`, and whether that call site is
  reachable when `closes_only=True` (the only mode the real CI workflow
  ever passes). Static source inspection, no maintained list. Catches
  #3, #4.
- **Derivable**: whether a field name documented in a `docs/specs/*.md`
  schema table (e.g. `decision_queue`'s `opened_at`, `age_hours`, ...)
  appears anywhere outside its own implementation, tests, and the spec
  table itself — i.e., whether anything outside the producer claims to
  consume it. Names are extracted from the spec table at check time, not
  hand-maintained. Catches #1.
- **Not derivable from this repo**: whether a named platform capability
  (e.g. Claude Code's `Stop` hook event) exists at all — that is a fact
  about the platform, not this tree. No grep over this repo can confirm
  or deny it. Per the issue's own §"What needs deciding" item 1, this
  needs "a different answer path — say what it is rather than leaving it
  implicit," not a gate. This is the one instance (#2) this proposal
  cannot mechanically cover; it is addressed by a single stated fact in
  a spec doc, explicitly labeled as unchecked.

## Write set implied by the above

- `gates/gates.py` — two new gate functions.
- `gates/ci.py` — wire the CI-reachability gate unconditionally (before
  the `closes_only` short-circuit — the whole point is that it must
  survive that gate).
- `test_gates.py` — unit tests for both new gates, including a
  regression test reproducing the `writeset`/`record_enums` dead-gate
  shape.
- `docs/specs/flows-schema.md` — no change to the schema itself; the new
  gate reads it, doesn't alter it.
- `docs/specs/platform-capabilities.md` (new) — the one stated,
  explicitly-unchecked fact for instance #2.
- `docs/issue-376/reports/implementation/survey.md` (this file),
  `docs/issue-376/proposals/*.md` — this session's own phase-1 output.
