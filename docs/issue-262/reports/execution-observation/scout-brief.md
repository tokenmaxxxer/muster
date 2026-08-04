---
kind: scout-brief
subject: issue-262
role: execution-observation
date: 2026-08-04
phase: 1
---

# Scout brief — what a strong observation of a *gate-code* change checks

Deliverable class scouted: **an independent audit record of an executed change
to an enforcement control** (the changed code *is* a gate). Angles were aimed
at the four unknowns the survey left open (Q1 control-vs-outcome, Q2
declared-vs-actual deviation, Q3 scope-widening, Q4 recurrence).

**Segment fit**: closest field match is internal-control/change-management
auditing plus least-privilege access review plus blameless post-incident
review — all three judge an executed change against evidence, which is this
role's exact shape.

**Category must-bes (what strong exemplars assume)**

1. Separate a *design* deficiency from an *operating* deficiency: a control
   that executes exactly as written but still fails to meet its objective is a
   design deficiency, and remediation aims at redesign, not at execution
   discipline (Pathlock, Drata, Linford).
2. Distinguish an isolated exception from a control deficiency — recurrence is
   the discriminator, not severity (Secureframe).
3. Every deviation from an approved change plan is itself an audit exception
   unless it carries a named owner, reason, and expiry; undocumented deviation
   is the archetypal change-management finding (SOC2Auditors, Cloudaware).
4. Privilege changes are judged on the *delta of newly granted access*, and
   broad wildcards are called out explicitly rather than accepted because
   something nearby was already broad (AWS SEC03-BP02, IAM wildcard
   masterclass, OWASP Authorization cheat sheet).
5. A repeat event triggers a postmortem regardless of severity and is treated
   as systemic; action items split into *mitigative* (this instance) and
   *preventative* (the class) (incident.io, SRE School).

**Performance axes the field competes on**: (a) design-vs-operating attribution
per finding; (b) delta-based (not absolute) privilege judgment; (c) recurrence
detection across sibling changes.

**GAP LINE** — must-bes 2, 3 and 5's blameless four-part shape are already met
by this role's directive and by this repo's prior records
(`docs/issue-227/reports/execution-observation.md`,
`docs/issue-224/reports/execution-observation.md`). **Must-bes 1, 4, and the
mitigative/preventative split in 5 are the gap**: no prior observation record
here has separated "the gate passed" from "the gate's objective was met"
(survey F6–F8 is exactly that case), none has judged a widened matcher by its
newly-granted delta (survey F10), and none has had a confirmed recurrence to
classify (survey F9, issue #266).

**Adopt**: (i) design-vs-operating attribution on the auto-close finding, so
the action item points at the right surface; (ii) delta-based privilege check
on the widened glob — enumerate what the post-fix literal permits that the
pre-fix literal did not; (iii) mitigative/preventative split in the action item.

**Skip**: control-maturity scoring, sample-based testing of other changes, and
any remediation *implementation* — this role judges one executed change and
never edits the observed surface; grading the repo's control maturity would be
re-scoping, not observing.

**Pass shape**: 2 stages (1 sweep of 4 angles + 1 judge point), **parallel**
mode — four concurrent `WebSearch` calls in a single turn. Stopped at
saturation: another round would not change any check in the plan.

Sources:
- https://pathlock.com/blog/internal-controls/control-deficiencies/
- https://drata.com/blog/control-deficiencies
- https://linfordco.com/blog/audit-deficiency-analysis/
- https://secureframe.com/blog/auditing-isolated-exception-vs-control-deficiency
- https://soc2auditors.org/insights/soc-2-change-management-controls/
- https://cloudaware.com/blog/devsecops-change-management/
- https://docs.aws.amazon.com/wellarchitected/latest/framework/sec_permissions_least_privileges.html
- https://medium.com/@sthallapelly/iam-policy-crafting-masterclass-preventing-privilege-escalation-and-wildcard-misuse-9a37fb0c8974
- https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- https://incident.io/blog/sre-incident-postmortem-best-practices
- https://sreschool.com/blog/blameless-postmortem/
