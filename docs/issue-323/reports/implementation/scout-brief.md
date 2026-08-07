# Scout brief — issue #323

Mode: batched-sequential (two local skill reads, not parallel web fan-out — the
strongest prior art for this exact problem shape is already installed in this
environment as `agent-coordination` and `merge-gates`; sweeping the open web
for "AI agent merge conflict methodology" would return weaker, less
repo-specific material than what is already on disk). Stages used: 1.

## Field surveyed

- `agent-coordination` skill — file-based claims/conflicts/resolutions bus,
  heartbeat liveness, cheapest-to-revert yield rule, self-merge protocol.
  Source: `~/.claude/skills/agent-coordination/SKILL.md`.
- `merge-gates` skill — four-property gate shape test (binary,
  machine-evaluable, fail-closed, combined-state), fail-open audit,
  explicit refusal of risk-tiering by prediction. Source:
  `~/.claude/skills/merge-gates/SKILL.md`.

## Must-bes the field converges on

- A conflict is detected from **declared write sets**, not discovered by
  editing the same file blind. (agent-coordination Step 1/Step 0)
- Detection state is **committed, not in-memory** — an agent/session that
  doesn't persist its claim doesn't exist to others. (agent-coordination,
  "the repo is the bus")
- A gate must be binary, machine-evaluable, and fail-closed — a prose
  policy is not a gate. (merge-gates Step 2)
- Never gate by *predicting* which change is risky — only by verifying a
  concrete precondition (overlap exists / does not). (merge-gates Step 6)

## Performance axes

- **Liveness detection** (agent-coordination): heartbeat staleness decides
  whether a blocked party may resolve unilaterally.
- **Yield cost heuristic** (agent-coordination): cheapest-to-revert, not
  seniority or importance.
- **Fail-open auditing** (merge-gates): every gate states its failure
  direction explicitly.

## Adopt / skip

- **Adopt**: write-set-overlap detection as the trigger, and requiring
  every detected overlap to resolve into a written record before either
  side proceeds.
- **Skip**: self-merge and live heartbeat files. This repo's landing model
  is PR + human Approve (contract v3 s19), not agent self-merge — heartbeat
  liveness has no home here since sessions are short-lived and don't loop
  waiting on each other in real time. The PR's open/closed state is this
  repo's liveness signal, not a heartbeat file.

## Gap line

This repo already has the raw input a write-set-overlap check needs (every
phase-1 proposal freezes a `files:` list) and already has PR-based landing
with human gating (satisfies merge-gates' "human review is not a gate to
be automated" boundary). What's missing, mechanically: (1) nothing reads
open proposals' `files:` lists and diffs them against each other, (2)
nothing fails when it finds an overlap, (3) no recorded-resolution
location exists. These three gaps are the entire build.

## Sources

- `~/.claude/skills/agent-coordination/SKILL.md`
- `~/.claude/skills/merge-gates/SKILL.md`
- `docs/specs/` (this repo, listing confirms absence of existing coverage)
- GitHub issue #324 (sibling, dependency direction confirmed via `gh issue view 324`)
- GitHub issue #298 (orchestrator-enforcement caution, `gh issue view 298`)
