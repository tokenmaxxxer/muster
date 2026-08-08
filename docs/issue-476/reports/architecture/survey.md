# Survey — issue #476, architecture phase-1 current-state check

Scope: locate the actual integration points on the deployed plugin surface (hooks / `spawn.py` /
`gates/` / `run.md`) that H1 (mechanized independent re-execution) and H2 (refusal at equal
structural cost) from `docs/issue-476/proposals/discovery.md` must attach to. Checked by reading
the files directly, not inferred.

## Gate suite (`gates/`)

- `gates/gates.py` (943 lines) — the gate registry/runner other gate modules plug into.
- `gates/acceptance_gate.py` (100 lines) — field-presence check on discovery-doc style records
  (confirms discovery survey's own claim: checks a doc *contains* required elements, does not
  execute anything).
- `gates/test_boundary.py` (267 lines) — write-scope/boundary enforcement per role.
- `gates/landing_readiness.py` — merge-readiness aggregator; a natural attachment point for a new
  required check, since it already aggregates pass/fail across the existing gate suite before a
  PR is considered landable.
- `gates/skip_gate.py`, `gates/closure_sweep.py`, `gates/issue_bundling.py`,
  `gates/pr_reference.py`, `gates/spawn_coverage.py`, `gates/risk_report.py`, `gates/ci.py` —
  existing gates; none execute re-derived evidence, confirmed by absence of any subprocess/git
  worktree call in a grep across `gates/*.py` (only `test_*.py` files invoke subprocesses, and
  those test the gates themselves, not role records).

## Spawn/session layer (`spawn.py`, 3709 lines)

- `ROLES` tuple at `spawn.py:777` — closed vocabulary of role names (`product-discovery`,
  `interaction-design`, `technical-feasibility`, ...) — confirms the survey's observation that
  this repo already has a habit of closed-vocabulary fields rather than free text.
- `_classify_refusal_text` (`spawn.py:1769`) and `_flush_unverified` (`spawn.py:1838`) — existing
  refusal-classification machinery, harness-level ("did the tool call get blocked"), not
  content-level ("is the claimed positive result real"). Confirms discovery survey's finding:
  orthogonal to this issue's failure mode.
- `REPO_CONFIG` (`spawn.py:853`) enumerates `.claude/settings.json` / `.claude/settings.local.json`
  / `.claude/hooks` as the hook surface `on-the-record` reads from both ends without inspecting
  the middle (comment at `spawn.py:862`) — i.e. hooks are additive, not something the harness
  audits for content, which matters for the re-execution gate's own trust boundary (see proposal:
  the gate script must not itself be role-writable).
- Plugin-packaging code (`spawn.py:2506-2514`) shows the actual deployed shape a hook takes:
  a `hooks/hooks.json` with `UserPromptSubmit` / `PreToolUse` matchers — this is the literal
  attachment shape H1's trigger must use if implemented as a hook rather than a `gates/` script.

## `run.md` (420 lines, `on-the-record/commands/run.md`)

- Line 115 area enumerates the closed stage/flow vocabulary
  (`product-discovery`/`architecture`/`implementation`/`verification`/`merge`/`close`) that a
  role's `loop_state` must be drawn from — this is the exact mechanism H2 should extend (append a
  `refused` / `not-needed` state to the existing closed vocabulary) rather than invent a parallel
  field or gate shape.

## Gap, stated against this surface specifically (not re-litigating discovery's JTBD)

No existing gate or hook in `gates/` or `spawn.py` performs a **subprocess execution** step at
all — every existing gate is a text/structure check over a record file. This confirms discovery's
survey finding at the code level relevant to architecture: H1 needs a genuinely new capability
(gate-owned subprocess execution in an isolated checkout), not an extension of an existing
pattern; H2 needs no new capability, only a vocabulary extension to a pattern (`loop_state` closed
enum, `ROLES` closed tuple) already used three times in this codebase.
