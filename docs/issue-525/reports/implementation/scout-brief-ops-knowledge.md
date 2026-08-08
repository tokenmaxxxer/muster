# Scout brief — ops/knowledge family (11 roles)

Mode: parallel Agent-tool fan-out, 1 stage (sweep only; saturation reached).

Must-bes:
- incident-response: SRE Postmortem Template (Google SRE book) — timeline, impact
  statement, root cause, action items with owner.
- capacity-planning: ITIL Capacity Management practice — capacity plan document,
  demand forecast tied to business capacity, threshold monitoring.
- knowledge-management: KCS (Knowledge-Centered Service) — article captured at
  point of resolution (Solve loop), reuse/flag-for-review workflow.
- technical-writing: Diataxis — content classified into one of the four quadrants
  (tutorial/how-to/reference/explanation), each with a distinct required structure.
- issue-retrospective: blameless retrospective format (same SRE lineage, applied to
  non-incident retros) — timeline, impact summary, action-item table
  (item/owner/due-date/status), no-blame language constraint.
- devrel: no single ratified standard confirmed (gap, stated as assumption) —
  closest convergent practice: Keystone DevRel metrics + DevRel-Qualified-Lead
  concept (Mary Thengvall), metrics mapped to product-journey stage.
- customer-support: HDI Support Center Standard + CSAT as the satisfaction metric
  (1-5 scale).
- content-design: GOV.UK Content Design / GDS style guide — content organized
  around user need/user language, mandatory plain-language conventions.
- brand-design: DTCG Design Tokens Format spec — tokens as JSON
  (`application/design-tokens+json`), name/value/type structure.
- localization: Unicode CLDR / UTS #35 (LDML) — locale data per LDML schema,
  date/time/number/currency patterns and translated names per locale.
- ux-engineering: same DTCG token spec as brand-design (deliberate shared lineage —
  token JSON is the machine-consumable artifact this role implements against,
  consumed via reference implementations like Style Dictionary).

Performance axes: point-in-time capture workflow (KCS, blameless retro) vs.
structural classification (Diataxis quadrants, DTCG token types) vs. numeric
threshold (CSAT, capacity forecast) — required_fields type varies per role
accordingly.

Adopt: KCS's capture-at-resolution ordering as a pre-registration-style rule for
knowledge-management (mirrors #515 invariant 1). Skip: inventing a DevRel closed
enum — devrel's `required_fields` stay prose/string pending a stronger primary
source at delivery time.

Segment fit: ops/support/knowledge-lifecycle roles, distinct segment from build —
justifies this being its own family rather than folded into build.

Gap line: brand-design and ux-engineering share one canonical format (DTCG) but
remain two separate roles/specs (different write_scope: brand-design owns token
authoring, ux-engineering owns token consumption) — noted so the delivery batch
doesn't collapse them into one spec.

Sources:
- https://sre.google/sre-book/postmortem-culture/
- https://www.itlibrary.org/
- https://www.thekcsacademy.net/kcs/
- https://diataxis.fr/
- https://www.blameless.com/blog/retrospective-template
- https://docs.blameless.com/hc/en-us/articles/9644205918487-Retrospectives
- https://openviewpartners.com/blog/measuring-the-impact-of-your-developer-relations-team/
- https://developerrelations.com/talks/measuring-progress-in-developer-relations/
- https://www.thinkhdi.com/services/support-center-standard
- https://www.gov.uk/guidance/content-design/writing-for-gov-uk
- https://www.designtokens.org/tr/2025.10/format/
- https://cldr.unicode.org/
- https://www.unicode.org/reports/tr35/
