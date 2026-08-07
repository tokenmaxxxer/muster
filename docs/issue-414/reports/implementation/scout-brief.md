# Scout brief: #414

Mode: batched-sequential fallback (single session, no parallel subagent
dispatch available for this read-only grep/Read sweep — stated per
scout-directive's fallback-disclosure requirement). Stages used: 1
(sweep only; saturation reached immediately — five sibling docs already
converge on the same mechanism, a second round would not change the
build decision).

Angle run: by-precedent — grep the repo's own prior art for Stop-hook /
`last_assistant_message` design, since this is internal tooling with no
external product category to benchmark against (non-product infra
work; the comparable "field" is this codebase's own family of
Stop-hook proposals).

## Findings

- Must-be (from #411, merged precedent): fail-closed `trap`, `CLAUDE_ROLE`
  pass-through, cheap prefilter before any Python, `additionalContext`
  not `block` for a heuristic that can't prove substance.
  Source: docs/issue-411/proposals/2026-08-07-stop-hook-structural-check.md
- Must-be (from #320, #379): a Stop hook can read `last_assistant_message`
  and *can* `block`, but every sibling proposal that considered blocking
  on a soft/heuristic signal rejected it — disruption disproportionate
  to what a regex/substring check can prove.
  Source: docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md,
  docs/issue-379/proposals/2026-08-07-choice-framing-guard.md
- Gap line: what the field (sibling proposals) already covers — same-turn
  structural presence checks (issue ref, change clause, risk clause;
  #411) and same-turn framing checks (#320, #379). What none of them
  cover, and what #414 specifically needs: **cross-turn** state — a
  check that persists what was stated in turn N and verifies turn N+1
  against it. No sibling proposal builds this; it is new surface for
  #414, not reuse.
- Pattern to adopt: marker-file-per-session persistence (simplest
  cross-turn mechanism available to a stateless bash hook — no daemon,
  no DB, matches "no new dependency" constraint).
- Pattern to deliberately skip: judgment-based detection (distinguishing
  "explains effect" vs "enumerates", per #320/#373's already-recorded
  false-positive risk) — same reasoning applies to #414: detecting
  *that* an intention was stated is checkable by phrase-matching;
  detecting *whether* the follow-through genuinely satisfies it is not,
  and is left explicitly unenforced per #310 (matches #411's decision
  precedent of naming what's covered vs open rather than overclaiming).

Sources:
- docs/issue-411/proposals/2026-08-07-stop-hook-structural-check.md
- docs/issue-411/reports/implementation/survey.md
- docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md
- docs/issue-379/proposals/2026-08-07-choice-framing-guard.md
- docs/issue-374/reports/implementation/survey.md
