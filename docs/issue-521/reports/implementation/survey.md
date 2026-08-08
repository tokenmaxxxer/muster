# Current-state survey — issue-521 (batch-1 verification-family spec realization)

Subject: issue-521, phase 1. Scope: the write set this proposal will actually touch, surveyed before drafting.

## Write surfaces found

### 1. `roles/<name>.json` — 6 files, all TBD-shaped today

Read directly (`roles/execution-observation.json`, `roles/conformance-review.json`,
`roles/defect-verification.json`, `roles/security-threat-model.json`, `roles/accessibility.json`,
`roles/secure-coding.json`). Every one of the 6 shares the same gap pattern the #515 survey already found
system-wide:

- `write_scope: []` with no `report_only: true` tag — an unresolved TBD per the #515 template, not yet a
  decision.
- `record_fields.loop_state` is a **flat single-element array** (`["handed-off"]`, `["reported"]`,
  `["cleared"]`, `["landed"]` x3) — not the `{progress, terminal, refusal, error}` four-bucket shape the
  realization template requires.
- `use_when` is Korean prose ("실행 가능한 산출물이 랜딩됐을 때...") — not a board-decidable predicate.
- `produces` is a free-text sentence — not a `required_fields` array with typed/enum fields.
- No `roles/specs/<name>.spec.json` sibling exists for any of the six roles.

### 2. `roles/specs/` — does not exist yet

`ls roles/specs` fails (no such directory). This proposal's write set creates it fresh with 6 new
`<name>.spec.json` files, per the #515 template's `roles/specs/<name>.spec.json` path convention.

### 3. `gates/` — no spec-shape validation test exists yet

`gates/spec_index.py` exists but is unrelated (spec-*document* drift detection via SHA256, for
`docs/specs/reconciled-index.md` — a different "spec" than a role's deliverable spec). No file in `gates/`
currently loads `roles/specs/*.spec.json` against a template schema, and no `-k "spec"`-matching pytest exists
for this purpose (confirmed: `find gates -iname "*spec*test*"` returns only `spec_index.py`'s own
`test_spec_index.py`-shaped sibling is absent — the acceptance clause's `pytest -k "spec"` selector currently
matches only `spec_index`-related tests, none of which validate role specs). Issue-521's acceptance clause 1
therefore requires a **new** gate/test file — a genuinely new write surface, not an edit to an existing one.

### 4. Hook wiring — `on-the-record/hooks/`

`on-the-record/hooks/hooks.json` wires `PreToolUse`/`Stop` hooks (`record-claim-guard.sh`,
`contract-guard.sh`, `spec-index-preflight.sh`, etc.), each a shell script calling into a `gates/*.py` module.
The realization template's `reference_resolution.checked_by` and `recomputation.checked_by` fields must each
name a real hook file — issue-521 requirement 3 states enforcement fires via hooks in plugin-installed
sessions, anchored to the target project root, never GitHub Actions. No hook currently checks a verification-
family record's reference-resolution or recomputation rules; this is new surface, matching the #515 proposal's
own deferral of hook-writing to follow-up Issue A (this issue).

### 5. `docs/issue-515/reports/requirements-engineering.md` and its `scout-brief.md` — read-only precedent

The approved #515 record already defines the realization template (produces-spec fields, closed enums,
reference-resolution rules, recomputation rules, write_scope, loop_state states, use_when dispatch signal) and
sketches all 6 batch-1 specs at the field level, each traced to a named standard. This proposal instantiates
that template; it does not redesign it. #515's `scout-brief.md` already carries sourced findings for EARL 1.0,
STRIDE/Threat Dragon (partially — see open finding below), OWASP ASVS, Bugmon, and IV&V/DO-178C traceability.
It does **not** cover WCAG-EM/ACT (accessibility) or ISO/IEC/IEEE 29119-3 (defect-verification) at the field
level — both named explicitly in issue-521's requirement 2 — so this phase-1 pass ran one supplementary
research round (see scout-brief addendum in the proposal) to close those two gaps and to resolve #515's open
finding on Threat Dragon's per-threat field list (previously unconfirmed from a live schema fetch).

## Unknowns the survey leaves for the proposal to decide

- Exact JSON Schema shape for the template itself (a `docs/specs/`-level schema file the pytest validates
  against) — not yet decided; the proposal's Rationale section picks between "one shared schema file" vs.
  "six independent ad hoc schemas."
- Whether `reference_resolution.checked_by` / `recomputation.checked_by` hooks are written now (new `.sh` +
  `gates/*.py` pair) or named as a follow-up — issue-521 requirement 3 requires enforcement to exist, but the
  acceptance clauses only test schema validity, `write_scope`/`loop_state` shape, and `use_when` count; the
  proposal decides how much hook-writing lands in this phase-2 vs. what stays a stated TBD with reason.

## Skip-condition check (scout directive)

Neither skip condition applies — the spec fields, closed enums, and loop_state buckets are all design
decisions with more than one plausible shape (e.g. one shared schema file vs. per-role schemas; how deep
hook enforcement goes this pass). Scouting runs; see the proposal's scout-brief addendum.
