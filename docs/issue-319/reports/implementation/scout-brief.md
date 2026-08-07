Subject: issue-319 — scout brief

Mode: 1 stage, single WebSearch call (batched-sequential fallback — Agent-tool
parallel fan-out was not warranted for one narrow angle: "how do comparable
systems reduce approval-decision volume without removing the human act").
Stopped after judge point 1 — the hits converged tightly (Meta RADAR, GitLab
CODEOWNERS docs, Dependabot auto-merge, an auto-approvability blog) on the
same three must-bes below; a second round would not change a build decision.

## Category must-bes (what strong systems assume)

- Risk is not just "which path" — size/blast-radius matters too. A safe
  50-file refactor and a 3-line change to a critical path get different
  review requirements under real risk-based routing; path-only classification
  (which is what `gates/gates.py:is_protected` currently gives us) is one
  input, not the whole signal.
- The safe-to-batch/auto-handle class is an explicit, narrow allowlist
  (docs, tests, disabled-flag code, mechanical renames, CI config tweaks),
  never an implicit "everything not on the protected list."
- Auto-merge precedent (Dependabot) is scoped to one narrow, well-understood
  PR shape (dependency version bump), not a general risk score threshold —
  the safe pattern narrows the class first, then automates within it.
- When a required-reviewer rule (CODEOWNERS-equivalent) applies, risk
  classification does not bypass it — it only changes presentation/urgency,
  never removes the required act.

## Performance axes strong systems compete on

1. Classification signal quality (path + size + change-shape, not path alone).
2. Whether automation ever *removes* a required human act, vs. only changes
   how/when it's presented (the safe systems never do the former for a
   required-reviewer class).

## Adopt / skip

- Adopt: narrow, explicit low-stake allowlist + size threshold, reused from
  `gates/gates.py:is_protected` plus a line/file-count check, as the risk
  signal. Present classification alongside the approval request rather than
  silently auto-approving.
- Skip: any threshold-scored auto-approval that grants approval without a
  human GitHub act for a class contract v3 §8 reserves to a human — this
  repo already tried and withdrew that move (2026-07-26, protocol.md:230-234)
  for a different reserved judgment point; same rule applies here by
  extension.

## Gap line

This repo already has the path-protection half of the signal
(`gates/gates.py:is_protected`). It has no size/change-shape signal, no
narrow allowlist, and no batched presentation — those are the gaps this
issue's build should close.

Sources:
- [Automating Low-Risk Code Review at Meta: RADAR, Risk](https://arxiv.org/pdf/2605.30208)
- [What Is Approvability? AI Auto-Approve Pull Requests | Macroscope](https://macroscope.com/content/what-is-approvability-auto-approve-safe-pull-requests)
- [Agentic codeowners / anyblockers](https://anyblockers.com/posts/agentic-codeowners)
