---
name: scout-brief
description: >
  ITIL/FMEA/CVSS sweep for issue #511's multi-axis impact classification
  spec — one round, mode: parallel (3 WebSearch angles in one turn).
---

# Scout brief — issue #511

Stages used: 1 sweep + judgment, no deepening round (saturation reached —
all three methodologies are standardized/textbook and a second round would
not change which parts to adopt or reject). Mode: parallel (3 `WebSearch`
calls in one message) + 1 follow-up search for the review-routing failure
signal required by issue requirement 6.

## Must-bes (what the strong references assume)
- ITIL: a standard change is pre-authorized only because its **scope,
  prerequisites, and approval model are documented in advance**; a change
  outside that documented envelope reverts to normal-change (individual
  authorization). Re-authorization is required whenever the standard
  procedure itself changes.
- FMEA (AIAG-VDA handbook): every S/O/D grade is an **anchored,
  machine-legible description**, not a number picked by feel; severity and
  occurrence are scored independently — they are never averaged into each
  other.
- CVSS v4: dropped the ambiguous "Scope" metric in favor of explicit
  Vulnerable-System vs. Subsequent-System impact, and resolves the full
  metric vector via **worst-case equivalency sets**, not a weighted sum —
  the score for a vector is the ceiling of what's reachable, not an
  average across metrics.

## Performance axes (where the field visibly competes)
- **Anchoring precision** — CVSS's early free-text severity choices vs.
  v4's/AIAG-VDA's fully enumerated per-grade criteria (fewer disputes,
  directly machine-checkable).
- **Composition rule** — FMEA's classic RPN (S times O times D) is
  explicitly superseded by AIAG-VDA's Action-Priority table because a low
  score on one axis was masking a catastrophic score on another; CVSS v4's
  worst-case MacroVector approach converges on the same lesson from a
  different field.
- **Escalation default on unknown input** — ITIL standard change: anything
  outside the pre-documented envelope is not silently treated as standard,
  it reverts to normal (human) change.

## Adopt / skip
- **Adopt**: ITIL's pre-documented-envelope-with-automatic-reversion shape
  for standing decisions (req. 4); AIAG-VDA's per-grade anchored-criteria
  table shape for the axis scales (req. 2); CVSS v4's worst-case
  (non-averaging) resolution rule for combining axes (req. 3).
- **Skip**: classic FMEA RPN multiplication (superseded even inside FMEA's
  own lineage, for the exact failure this issue is trying to avoid);
  CVSS's single composite score as the *output* shape (issue explicitly
  wants per-axis grades surfaced, not one collapsed number, so routing
  logic can inspect which axis fired).

## Gap line (current state vs. field must-bes)
`gates/risk_report.py` today has one boolean-ish axis (low/high), sourced
only from protected-path membership and a single size threshold — no
blast-radius/reversibility/propagation decomposition, no anchored
per-grade table, and no worst-axis-dominance rule (there is only one axis
to dominate). It already has the fail-closed default ITIL/AIAG-VDA both
assume (unparseable write-set becomes high), so that must-be is already
met and does not need re-deriving in the proposal.

## Review-routing failure signal (issue req. 6)
A systematic roadmap on modern code review reports that historically risky
and later-defective files receive less rigorous review than clean files —
the inverse of what a risk-routing signal is supposed to produce once
reviewers start trusting the low/high label as a substitute for reading
the diff. This is the named failure mode requirement 6 asks the proposal
to guard against: classification must reallocate attention, never exempt
review depth.

## Stages / mode
One sweep stage (parallel), no deepening stage, one supplemental
single-angle search for the failure-signal citation. Judge point: all
three angles' top hits converged on the same three lessons above
(anchored criteria, worst-case composition, documented-envelope
reversion) — no exemplar mismatch, no further round needed.

Sources:
```
https://www.spoclearn.com/blog/itil-4-definition-of-standard-change/
https://itsm.tools/change-enablement/
https://fmearatings.com/aiag-vda-fmea-tables
https://quasist.com/fmea/severity-in-fmea/
https://quasist.com/fmea/detection-in-fmea/
https://blog.qualys.com/product-tech/2023/11/02/cvss-v4-is-now-live-and-what-do-you-need-to-know
https://www.malwarebytes.com/blog/news/2025/11/how-cvss-v4-0-works-characterizing-and-scoring-vulnerabilities
https://arxiv.org/pdf/2405.18216 (A Roadmap on Modern Code Review: Challenges and Opportunities)
```
