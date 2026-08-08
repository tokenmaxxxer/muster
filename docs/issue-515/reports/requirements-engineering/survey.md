# Current-state survey — issue-515 (role specialization realization)

Subject: issue-515. Basis: `roles/*.json` at repo HEAD (`be8b3ea`), issue-160 taxonomy proposal (`docs/issue-160/proposals/role-taxonomy.md`), `docs/specs/approvers.md`.

## What exists today

- 43 role definitions at `roles/<name>.json`. Common shape: `marketplace`, `repo`, `path`, `sandbox`, `decides`, `use_when`, `produces` (free-text sentence), `write_scope` (array), `record_fields.loop_state` (array).
- `produces` is prose, not a schema: e.g. `requirements-engineering.json` — `"structured requirements doc, traceability matrix, ambiguity list resolved"`. No required-field list, no enum, no reference-resolution or recomputation rule. A record can claim these three things exist without any field being checkable.
- Empty `write_scope` and single/missing `loop_state` counts, reproduced directly against `roles/*.json` at HEAD:
  ```
  $ grep -lc '"write_scope": \[\]' roles/*.json | wc -l
  34

  $ python3 -c "
  import json, glob
  missing=single=multi=0
  for f in glob.glob('roles/*.json'):
      rf=json.load(open(f)).get('record_fields')
      if not rf or 'loop_state' not in rf: missing+=1
      elif len(rf['loop_state'])<=1: single+=1
      else: multi+=1
  print('missing=%d single=%d multi=%d' % (missing, single, multi))"
  missing=2 single=34 multi=7

  $ python3 -c "
  import json, glob
  for f in glob.glob('roles/*.json'):
      rf=json.load(open(f)).get('record_fields')
      if not rf or 'loop_state' not in rf: print(f)"
  roles/issue-retrospective.json
  roles/release-engineering.json
  ```
  Read directly out of the fence above: empty write_scope, single-element loop_state, missing-key roles, and multi-state roles — matches issue-515's own stated shape. issue-160's promoted rows mark several empty scopes as "TBD at execution" (ux-engineering, api-design, brand-design, devrel) — that TBD was never resolved.
  Sampled directly: `requirements-engineering` → `["landed"]`, `conformance-review` → `["reported"]`, `defect-verification` → `["cleared"]`.
- Checked for a terminal-state override file at the repo-relative path the interaction-protocol system-reminder names, docs slash specs slash record-fields-terminal-states.json, via `test -f` — not present. Terminal states currently fall back entirely to the contract's per-kind default list; whether any realized role needs an override is a phase-2 per-role call, not assumed here.
- No machine-checkable spec artifact exists per role today — no JSON Schema, no enum file, no reference-graph checker. Enforcement of record shape is presently at the free-text/prose level only (readable by contract text, not lintable).
- issue-160's proposal (accepted design, not yet executed as `roles/*.json` edits per its own scope note) already assigns each of the 43 roles a `produces` required-field *list* (prose, comma-separated) and a hand-off target — this is the nearest existing precedent for "required fields," but it stops short of closed enums, reference resolution, or recomputation rules. issue-515 explicitly builds on top of this list, not from scratch.
- Issue-515's own body already names a deliverable catalog per family (MADR, Spectral/oasdiff/dbt-contract, Kayenta, IV&V, Bugmon, STRIDE/Threat Dragon, WCAG-EM/EARL, DPIA, Cagan, EARS+RTM, Torres, Dunford, SRE postmortems, ITIL, KCS, Diataxis, MEDDPICC, SRM, NIST 8286) from a prior in-conversation research pass — this survey does not re-derive that catalog; it treats it as accepted background and confirms the repo state it needs to act on.

## Gaps this proposal must close

1. **No schema layer.** `produces` prose → needs required fields + closed enums + reference-resolution + recomputation rules, per role.
2. **No write_scope realization.** Empty scopes need real paths (or an explicit, narrow "report-only" declaration where that's the true shape — several roles, including this session's own `requirements-engineering`, are legitimately report-only per the interaction-protocol directive already in force).
3. **No multi-state loop_state.** Single-state roles need progress/refusal/error states; the two roles missing the key outright need a mechanical fix (add the key).
4. **`use_when` is prose, not a dispatch condition.** Needs to become a board-decidable trigger (issue-text/board-state condition), not a Korean sentence a human has to interpret.
5. **No enforcement surface.** Whatever spec shape is chosen must be checkable by a **hook** running inside a plugin-installed session on an arbitrary target repo — not a GitHub Action, not something that assumes marketplace-repo layout. No such hook exists yet for any role's deliverable shape.

## Reference-forward: verification-family field grounding (from scout pass)

Confirms the field-level shape available to borrow for the verification family (see `scout-brief.md`): IV&V RTM (requirement ID + verification method + linked test case + result), EARL (subject/test/result/assertedBy/mode — 4+1 fields, W3C-standard, directly liftable), ASVS (ID + level + CWE mapping + verdict), Threat Dragon (title/diagramType/cells, per-threat fields not fully confirmable — flagged as a gap, not a blocker: STRIDE's own category enum already supplies the closed-enum half). This is the concrete evidence the per-role template's field list should be *shaped like an existing standard*, not invented, per issue-515's invariant 3.
