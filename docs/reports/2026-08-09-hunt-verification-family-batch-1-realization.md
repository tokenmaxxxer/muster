---
proposal: docs/issue-521/proposals/2026-08-09-verification-family-batch-1-realization.md
---

# Hunt record — verification-family-batch-1-realization

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — acceptance clause 2's `len(d['record_fields']['loop_state'])>=3` check is vacuous once loop_state becomes the proposed 4-bucket object, so it can never fail regardless of content
Kind: design-error
Seed: docs/issue-521/proposals/2026-08-09-verification-family-batch-1-realization.md (acceptance section "How you'll know it worked", second bullet), plus survey.md / scout-brief.md context for the #515 4-bucket loop_state template
cap_seconds: 60
tier: default
diff_stat_lines: 3 new files (survey.md, scout-brief.md, proposal), proposal itself ~90 lines
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:01:00Z

### Reproduce
Acceptance clause 2 as literally stated in the proposal:
```python
python3 -c "import json;d=json.load(open('roles/<name>.json'));assert d['write_scope'] is not None and len(d['record_fields']['loop_state'])>=3"
```
The proposal itself commits `loop_state` to the fixed 4-key shape `{progress, terminal, refusal, error}` (item 3 of "What will be done", and `docs/specs/role-spec-template.schema.json`'s declared shape in item 1). Evaluate the `len(...)>=3` predicate against that fixed-shape object, with every bucket left empty (i.e. no progress/refusal/error states actually populated for a role):
```
d = {'progress': [], 'terminal': [], 'refusal': [], 'error': []}
len(d) >= 3   # -> True, because a dict's len() counts its 4 keys, not the items inside any bucket
```
This is true even if the role's implementer forgets to populate `progress`/`refusal`/`error` at all (leaving them as empty lists) — `len(dict)` is 4 regardless, and even a malformed 3-key object (one bucket dropped entirely) still passes `>=3`.

### Observed
The stated acceptance check for "loop_state expanded to the 4-bucket shape" cannot distinguish a correctly populated loop_state (all 4 buckets carrying real states) from a degenerate one (buckets present but empty, or one bucket missing) — `len()` on the *object* only ever measures its key count, not whether any bucket actually contains a value. The proposal's own acceptance-check note (in "How you'll know it worked") already flags that the literal `len(...)>=3` was written for the *old flat-array* loop_state shape and resolves the ambiguity by re-reading it against the new object's key count — but that re-reading is exactly what makes the check vacuous: once `loop_state` is the fixed 4-key object mandated by the shared schema, `len(...)>=3` is unconditionally true for every conforming role file, populated or not. It looks like an enforcement check but cannot fail.

### Expected
An acceptance check for "loop_state was correctly expanded with real progress/refusal/error states per role" needs to inspect the *contents* of each bucket (e.g. `all(len(v) > 0 for v in d['record_fields']['loop_state'].values())`, or specifically checking that `progress`/`refusal`/`error` are non-empty for the roles the "What will be done" section says should get them), not the key-count of the wrapping object. As written, a role could ship with `loop_state: {progress: [], terminal: ['done'], refusal: [], error: []}` — silently failing to carry the refusal/progress states item 3 promises — and the stated acceptance check would still report success.
