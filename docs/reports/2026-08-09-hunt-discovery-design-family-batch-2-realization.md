---
proposal: docs/issue-524/proposals/2026-08-09-discovery-design-family-batch-2-realization.md
---

# Hunt record — discovery-design-family-batch-2-realization

## after-proposal, stance 0, tier default

Verdict: FINDING — gates/role_spec_shape.py checks only presence/type/non-emptiness, so a spec.json with placeholder content (`"enum": ["TODO"]`, `"source_standard": "bogus-role"`, `"rule": "TODO"`) passes with exit 0, meaning batch-2 spec files can satisfy the gate while being substantively empty/bypassing intent.
Kind: silent-failure
Seed: docs/issue-524/proposals/2026-08-09-discovery-design-family-batch-2-realization.md (plans batch-2 roles/specs/*.spec.json validated only by gates/role_spec_shape.py + a new gates/test_role_spec_shape_batch2.py, following the 782a81d batch-1 pattern)
cap_seconds: 120
tier: default
diff_stat_lines: proposal-only (no code diff; survey.md + scout-brief.md + proposal markdown)
started_at: 2026-08-09T02:00:19+09:00
ended_at: 2026-08-09T02:03:30+09:00

### Reproduce
```
python3 - <<'PY'
import json
spec = {
    "role": "bogus-role",
    "source_standard": "bogus-role",
    "required_fields": [{"name": "a", "type": "enum", "enum": ["TODO"], "required": True}],
    "reference_resolution": {"rule": "TODO", "checked_by": "TODO"},
    "recomputation": {"rule": "TODO", "checked_by": "TODO"},
    "write_scope": [],
    "report_only": True,
    "loop_state": {"progress": [], "terminal": ["TODO"], "refusal": [], "error": []},
    "use_when": {"board_condition": "TODO"},
}
open("/tmp/bogus.spec.json", "w").write(json.dumps(spec))
PY
python3 gates/role_spec_shape.py /tmp/bogus.spec.json; echo "exit=$?"
```

### Observed
The command prints nothing to stderr and exits 0 (pass). `role_spec_shape.py`'s `check()` never inspects the *content* of `enum` values, `source_standard`, `rule`/`checked_by` strings, or `board_condition` — only that they exist, are the right JSON type, and (for enum) are a non-empty list. A `["TODO"]` enum or a `source_standard` equal to the role's own name (no real external citation) is structurally indistinguishable from a correctly-authored spec.

### Expected
A gate meant to realize discovery/design-family role specs "following the exact pattern of batch-1" should be understood as only a shape gate, not a content gate — so if the batch-2 proposal or the associated PR review relies on `role_spec_shape.py` passing as evidence that the new spec files' enums/citations/rules are real and non-placeholder, that reliance is misplaced. Any batch-2 spec author (or future batch) can pass the gate with placeholder/bogus field values, and nothing in the gate or its test file would catch it.
