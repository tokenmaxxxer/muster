# Scout brief — what strong "judgment record about someone else's execution" looks like

Deliverable class scouted: not a product — an **execution-judgment record**
(audit/observation report over a landed change). Angles were aimed at the
survey's gaps: proof quality of the two new tests (gap 3), scope deviation
handling (gap 1), citation durability (gap 5), finding shape (gap 4).

Mode: **parallel tool calls in one turn** (4 concurrent `WebSearch` angles),
**1 stage** — sweep only. Judge point 2 hit saturation immediately: all four
decision-relevant answers came back from the sweep, so no deepening round ran
(elapsed well under the 3-minute budget).

## Category must-bes (what strong records of this class assume)

- **Regression proof = fail-without-fix.** A bug-fix test counts as proof only
  when it is shown to fail on the unpatched version and pass on the patched one;
  effectiveness is otherwise validated by mutation-style perturbation, i.e. a
  non-vacuity demonstration. A test that would pass either way is not evidence.
- **Evidence bound to an immutable reference.** Audit workpapers are the record
  of "evidence obtained, procedures performed, conclusions reached", and
  defensibility comes from an immutable trail — provenance that still resolves
  later, not a pointer that drifts.
- **A deviation needs affected scope + evidence reviewed + conclusion.** "No
  product impact" with no rationale is explicitly the weak form; the defensible
  form names what scope was affected, what evidence was looked at, and what the
  quality conclusion is.
- **Timeline is timestamped fact, no interpretation.** Postmortem practice: the
  timeline is a chronological list of events with timestamps and sources, with
  causal claims kept out of it; action items carry specific work and an owner.

## Performance axes this class competes on

1. **Traceability density** — share of verdict-bearing claims with a resolving
   reference. 2. **Non-vacuity of the proofs cited** — does the cited evidence
   discriminate the two states it claims to separate. 3. **Separation of fact
   from judgment** — timeline/inventory kept clean of verdicts.

## Adopt / skip

- **Adopt**: sha-pinned citations for every verdict (`file:line @ sha`, or a
  `git show <sha>:path` fact) — this is the immutable-reference must-be applied
  to a git repo, and it directly answers survey gap 5.
- **Adopt**: judge each new test by the fail-without-fix standard, from the
  artifact's own recorded red evidence — never by re-running it (the role's
  prohibition and the standard agree here: the observed role's own red run is
  the workpaper).
- **Skip**: full postmortem ceremony per finding. The role directive already
  scales it to four parts (impact/timeline/root cause/action item); adding
  contributing-factors/lessons-learned sections would bloat a single finding.

## Gap line

Current state already meets: timestamped timeline (survey has it), fact/judgment
separation (phase gating enforces it). Missing until phase 2: sha-pinned
citations on verdicts, and an explicit fail-without-fix judgment for each of the
two new tests plus a deviation-defensibility read of the one unlanded write-set
item.

Sources:
- https://rotteveel.ca/masp/security-testing/regression-testing
- https://en.wikipedia.org/wiki/Audit_working_papers
- https://trackerproducts.com/best-practices-for-documenting-audit-evidence-in-compliance-tools/
- https://www.automotivequal.com/deviation-management-a-practical-step-by-step-guide/
- https://theartofcto.com/guides/incident-postmortem-template-blameless-post-incident-review-guide
