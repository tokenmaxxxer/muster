---
status: proposed
files:
  - roles/specs/execution-observation.spec.json
  - roles/specs/conformance-review.spec.json
  - roles/specs/defect-verification.spec.json
  - roles/specs/security-threat-model.spec.json
  - roles/specs/accessibility.spec.json
  - roles/specs/secure-coding.spec.json
  - roles/execution-observation.json
  - roles/conformance-review.json
  - roles/defect-verification.json
  - roles/security-threat-model.json
  - roles/accessibility.json
  - roles/secure-coding.json
  - docs/specs/role-spec-template.schema.json
  - gates/role_spec_shape.py
  - gates/test_role_spec_shape.py
  - on-the-record/hooks/role-spec-reference-guard.sh
  - on-the-record/hooks/hooks.json
  - docs/issue-521/reports/implementation.md
---

## Request

Issue #521 (follow-up A of #515): realize the 6 verification-family role specs
(execution-observation, conformance-review, defect-verification, security-threat-model, accessibility,
secure-coding) against the #515 realization template — required-field lists, closed enums, reference-resolution
rules, recomputation rules, real `write_scope`, multi-bucket `loop_state`, board-decidable `use_when` — each
grounded in the discipline's canonical artifact form (EARL, IV&V/RTM, ISO 29119-3/Bugmon, STRIDE/Threat Dragon,
WCAG-EM/EARL/ACT, OWASP ASVS), with enforcement wired as target-repo hooks, not CI.

## Constraints

- Minimal-required-fields-first — expand a role's field list only where the survey/scout found evidence a field
  is needed, never speculatively.
- No new dependency: `jsonschema` is installed in this dev environment but not declared in the repo's own
  manifest and not used elsewhere in `gates/` — the validation test must not silently rely on it being present
  in every plugin-installed target repo.
- Enforcement mechanism is a hook (`on-the-record/hooks/*.sh` + `gates/*.py`), anchored to the target project
  root via the existing hook-wiring convention (`on-the-record/hooks/hooks.json`) — never a GitHub Actions
  workflow.
- `docs/issue-521/reports/implementation.md` is phase-2 output (per this session's role-handoff contract) —
  listed in the write set for completeness of the frozen scope, not written this turn.
- Every enum value must be lifted from a cited standard (this proposal's scout-brief), never invented.

## Rationale

**One shared JSON Schema file (`docs/specs/role-spec-template.schema.json`) validated by a hand-rolled
Python checker, vs. six independent ad hoc per-role schemas.** Rejected the six-ad-hoc-schemas alternative:
the #515 template defines one required shape (required_fields/closed enums/reference_resolution/recomputation/
write_scope/loop_state/use_when) that all six roles share structurally — only the *content* of `required_fields`
and its enums differs per role. Six independent schemas would duplicate the shape-check logic six times and let
the six copies drift out of sync with each other (the exact failure #515's survey found in the flat, ungoverned
`roles/*.json` files this issue is fixing). One shared schema keeps the shape check in one place; each role's
`.spec.json` supplies its own `required_fields` content against that one shape.

**Hand-rolled Python validator, vs. depending on the `jsonschema` PyPI package.** Rejected `jsonschema`: it
happens to be installed in this dev container but is not declared as a project dependency anywhere in this
repo, and this plugin's own constraint (no new dependency without a manifest entry + handbook note, per the
no-footgun/operational-surface commit rule) means adding it as a real dependency would require touching
`requirements.txt`/`pyproject.toml` plus a handbook doc — real cost for a shape check simple enough to hand-roll
(required keys present, type tags in a closed set, enum values are non-empty lists) in the same
dependency-free style `gates/spec_index.py` already uses for a structurally similar problem (checking a
document against a declared shape).

**ACT's 5-value outcome enum for `accessibility`, vs. reusing EARL's 4-value `result` enum verbatim.** Rejected
reusing EARL's enum unchanged: the scout-brief addendum confirms ACT Rules Format defines its own outcome
vocabulary (`inapplicable|passed|failed|cantTell|untested`) — a superset adding `untested`, and the W3C spec
frames ACT-EARL compatibility as expressibility, not identity. Since issue-521 names WCAG-EM/EARL/ACT together
for this specific role, the ACT-specific superset is the more precise fit than dropping down to EARL's plain
4-value enum.

**Scope the hook-writing to one shared reference-resolution guard this pass, vs. a bespoke enforcement hook per
role.** Rejected six bespoke hooks: five of the six roles' `reference_resolution.rule` reduces to the same
check ("every `ref`/`ref[]` field value resolves to an existing repo path, commit sha, or line-anchored
citation") — the exact shape `record-claim-guard.sh` already partially enforces for record claims generally.
One shared `role-spec-reference-guard.sh` + `gates/role_spec_shape.py` function covers all six; `recomputation`
enforcement (role-specific verdict-derivation logic) is intentionally left as a stated TBD in each spec's
`recomputation.checked_by` field for a follow-up pass, per the "minimal-required-fields-first, expand only on
evidence" constraint — issue-521's acceptance clauses test schema validity and field shape, not live
recomputation enforcement, so building six bespoke recomputation checkers now would be scope beyond what the
issue's own acceptance bar asks for.

## What will be done

1. Author `docs/specs/role-spec-template.schema.json` — the shared shape every `roles/specs/<name>.spec.json`
   must match: `required_fields[]` (each `{name, type, enum?, required}`), `reference_resolution{rule,
   checked_by}`, `recomputation{rule, checked_by}`, `write_scope[]` (or `report_only: true`), `loop_state`
   (`{progress[], terminal[], refusal[], error[]}`), `use_when{board_condition}`, `source_standard` (free text
   naming the grounding standard(s), per #515's Threat Dragon open-finding resolution note).
2. Author the 6 `roles/specs/<name>.spec.json` files, each instantiating that shape with the fields the
   scout-brief confirmed:
   - `execution-observation`: EARL 1.0 (`subject`, `test`, `result` enum `passed|failed|cantTell|inapplicable|
     untested`, `assertedBy`, `mode`).
   - `conformance-review`: EARL 1.0, same base, `assertedBy` pinned to the reviewing role's own identity.
   - `defect-verification`: `reproduced|not-reproduced` verdict + `repro_steps` (string, no closed vocabulary
     exists per 29119-3/Bugmon), `evidence` (ref[]), `severity`/`status` (29119-3-derived).
   - `security-threat-model`: STRIDE 6-category `type` enum, `severity`, `status`, `mitigation`, `title`,
     `description` — all confirmed live from the Threat Dragon model schema.
   - `accessibility`: WCAG-EM procedure fields (scope/sample/criterion) + ACT's 5-value `result` enum, `test`
     bound to a WCAG success-criterion ID.
   - `secure-coding`: OWASP ASVS `requirement_id`, `level` enum `L1|L2|L3` (cumulative), `cwe` (ref), `verdict`.
3. Update each `roles/<name>.json`: real `write_scope` per role (report-only roles get `write_scope: []` +
   `report_only: true`, matching each role's existing `record_fields`-only footprint — none of the 6 currently
   write source/doc files outside their own record); `loop_state` expanded to the 4-bucket
   `{progress, terminal, refusal, error}` shape (terminal = the role's existing single value; progress/refusal/
   error populated from that role's `use_when`/`produces` prose, e.g. `defect-verification` gets a `blocked`
   refusal state matching its own `produces` field's `blocking|advisory finding`); `use_when` rewritten as a
   `board_condition` predicate string (e.g. execution-observation: `"artifact landed AND no execution-
   observation record exists for this commit sha"`).
4. Author `gates/role_spec_shape.py` (hand-rolled validator: required keys present, `type` in the closed set
   `string|enum|ref|ref[]`, enums non-empty when `type: enum`, `loop_state` has exactly the 4 buckets each as a
   list) and `gates/test_role_spec_shape.py` (pytest, matches `-k "spec"`, loads and validates all 6
   `roles/specs/*.spec.json` files — satisfies acceptance clause 1).
5. Author `on-the-record/hooks/role-spec-reference-guard.sh` (invokes a `gates/role_spec_shape.py` function
   that checks any `ref`/`ref[]`-typed field value in a role's *record output* resolves to a real repo path/
   commit sha) and wire it into `on-the-record/hooks/hooks.json` under the existing `PreToolUse`/`Bash` matcher
   group, alongside `record-claim-guard.sh`.
6. Verify acceptance clauses locally before opening the PR: `python3 -m pytest gates/ -q -k "spec"` exits 0;
   the per-role `write_scope`/`loop_state` python check exits 0 for all 6; `grep -c "use_when" roles/specs/*.spec.json` equals 6.

## Accumulation

`gates/role_spec_shape.py` is the one shared shape checker for all 6 `roles/specs/*.spec.json` files (and any
future role's spec) — a 7th, 8th, ... role spec adds a data file, not a code change to the checker. The 6
`roles/<name>.json` field edits (`write_scope`/`loop_state`/`use_when`) are structurally identical one-line-shape
edits repeated across 6 files today; if a future batch (#515 follow-up Issues B-E) repeats this same edit shape
across the remaining ~33 roles, that repetition should promote to a shared migration script under `gates/`
(e.g. a `--update` mode on `role_spec_shape.py` or a sibling script) rather than continuing as N hand-edited
JSON files — this batch (6 roles) stays hand-edited since 6 is below where a migration script pays for itself.

## Out of scope

- Batch-2+ roles (discovery/design, build, ops/knowledge, commercial/risk families) — #515's follow-up Issues
  B-E, not this issue.
- Bespoke `recomputation.checked_by` enforcement hooks per role (stated as a TBD in each spec's
  `recomputation.checked_by` field, with the reason above) — this pass ships the *rule* text (how the verdict
  is derived) and the shared reference-resolution enforcement; per-role recomputation enforcement is a
  follow-up once evidence from real usage shows which roles actually need it (minimal-required-fields-first
  constraint).
- Rewriting `record-claim-guard.sh` or any other existing hook — `role-spec-reference-guard.sh` is new and
  additive, not a modification of existing enforcement logic.
- Filing the follow-up issues B-E named in #515 — this role never files issues (interaction protocol).

## How you'll know it worked

- `python3 -m pytest gates/ -q -k "spec"` exits 0, including `gates/test_role_spec_shape.py` loading and
  validating all 6 `roles/specs/*.spec.json` files against `docs/specs/role-spec-template.schema.json`'s shape.
- For each of the 6 roles: `python3 -c "import json;d=json.load(open('roles/<name>.json'));assert
  d['write_scope'] is not None and len(d['record_fields']['loop_state'])>=3"` — note: acceptance clause 2's
  literal `len(...)>=3` reads against the *old* flat-array `loop_state` shape; once `loop_state` becomes the
  4-bucket object per the #515 template, this check is satisfied by `len(d['record_fields']['loop_state'])`
  counting the object's 4 keys (`progress/terminal/refusal/error`), which is `>=3` — this is flagged explicitly
  here since it is a place the acceptance clause's literal Python and the template's intended shape could be
  read two ways; resolved in favor of the object-with->=3-keys reading, consistent with the #515 template.
  **Warrant-hunter finding (docs/reports/2026-08-09-hunt-verification-family-batch-1-realization.md,
  after-proposal, stance 0):** `len(dict)` on the 4-bucket object is always 4 regardless of whether
  `progress`/`refusal`/`error` are ever populated — the check as literally stated can never fail, even for a
  role that leaves those three buckets empty. Phase 2 must not ship the check in this literal form: it will
  additionally assert each of the 4 keys is present (`set(d['record_fields']['loop_state']) ==
  {'progress','terminal','refusal','error'}`) rather than relying on `len(...)>=3` alone, so a dropped or
  unpopulated bucket is still visible to review even though it wouldn't fail this particular acceptance
  predicate.
- `grep -c "use_when" roles/specs/*.spec.json` equals 6 (one `use_when` object per spec file), and each
  `use_when.board_condition` is a predicate over board/issue state, not prose — reviewed at PR review as the
  stated human check (acceptance clause 3's own provenance note).
- `on-the-record/hooks/hooks.json`'s new entry passes the existing `gates/test_hooks_parity.py` parity check
  (new hook registered consistently, no drift between the hand-written list and `spawn.py`'s actual output).
