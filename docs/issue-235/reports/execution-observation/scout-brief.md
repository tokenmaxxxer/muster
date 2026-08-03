---
subject: issue-235
role: execution-observation
phase: 1
---

# Scout brief — what strong audits of this change class check

Deliverable class: an independent audit of a **stream-log classifier
precision fix** (regex anchoring + cross-signal corroboration gate +
buffer-then-flush emission). Scouted the audit practice for that class,
not the product. Mode: **parallel** (4 concurrent WebSearch angles in one
turn), **2 stages total** (sweep + one judge point; saturation reached —
another round would not change a planned check). Angles were aimed at the
survey's unknowns 1-5, not at the issue text.

## Category must-bes (what strong audits of this class assume)

- **Test discrimination is derived, not asserted.** A suite can pass while
  the patch violates the intended semantics; strengthened suites lowered
  top repair agents' resolved rates by 4.2-9.0%, i.e. passing tests were
  exploiting suite weakness [arxiv 2604.01518]. The audit unit is the
  surviving-vs-killed distinction: a change that leaves assertions passing
  means the assertion that should have caught it didn't [circleci].
- **Precision tuning is audited for its false-negative cost.** Over-tuning
  for precision increases false negatives; correlation gating and
  dedup/suppression can silence real events, so the tuning's effect must be
  monitored for what it stopped reporting [cymulate, data443, n-able].
- **Deferring emission to a commit point is an at-most-once choice.**
  Committing/flushing only at the end means a crash before that point loses
  the buffered records outright; EOF handling that still flushes buffered
  data is the standard counter-shape [streamkap, nodejs streams].
- **Forged structural markers in untrusted log text are a real class.**
  Attacker-controlled fields carrying forged structural markers can
  override real signatures [OWASP Log Injection, wallarm]. Anchor tokens
  are an established log-parsing device [USPTO 12093162].

## Performance axes this class competes on

1. discrimination strength per regression case (does each case *force* a
   divergence on the pre-change blob); 2. false-negative delta (what the
   gate stopped reporting relative to before); 3. failure-mode honesty
   (is the at-most-once trade named and owned, or silent).

## Adopt / skip

- **Adopt**: per-case static discrimination derivation on the two blobs
  (the killed/surviving frame, applied by reading rather than running —
  re-execution is prohibited for this role).
- **Adopt**: an explicit coverage-delta sweep — enumerate input shapes
  where pre-change emits and post-change does not, and where dedup collapses
  two real events into one.
- **Skip**: running a mutation tool or any test. The measurement
  instrument here is the two blobs' text; tool-running is re-execution.

## Gap line

Current state already meets: forged-marker awareness (issue #235 req 2
names anchoring) and named regression cases (req 4). Missing from the
current state: any *coverage-delta* check (must-be 2) — issue #235's five
요구사항 contain no false-negative-regression criterion; and the
at-most-once trade (must-be 3) is named only inside the observed role's own
Hunt finding 1, with no independent check. Those two gaps are what the
proposal's checks target.

**Assumption, not a finding**: that anchoring a marker regex to text start
is specifically a documented *security* mitigation for quoted-marker
forgery. The sweep found anchor tokens as a parsing device and forged
markers as an attack class, but no source tying the two; treated as an
assumption throughout.

Sources:
- https://arxiv.org/html/2604.01518
- https://circleci.com/blog/what-is-mutation-testing/
- https://en.wikipedia.org/wiki/Mutation_testing
- https://cymulate.com/cybersecurity-glossary/siem-correlation-rules/
- https://data443.com/blog/reducing-siem-false-positives-risk-scoring-thresholds-and-real-costs/
- https://www.n-able.com/blog/reduce-false-positives-ai-threat-detection
- https://streamkap.com/resources-and-guides/exactly-once-vs-at-least-once
- https://nodejs.org/api/stream.html
- https://owasp.org/www-community/attacks/Log_Injection
- https://www.wallarm.com/what/log-forging-attack
- https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12093162
