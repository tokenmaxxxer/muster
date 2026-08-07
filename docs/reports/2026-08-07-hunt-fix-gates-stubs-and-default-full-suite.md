---
proposal: docs/issue-435/proposals/2026-08-07-fix-gates-stubs-and-default-full-suite.md
---

# Hunt record — fix-gates-stubs-and-default-full-suite

## before-landing — stance 2: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — assert_stub_return_shape only checks the outer container type, never the parameterized inner element types, so a stub that returns the right container with wrong inner shapes passes silently.
Kind: silent-failure
Seed: shape_contracts.py::assert_stub_return_shape; gates/test_closes_gate_ci.py::t_issue_comments_stub_shape_contract_catches_old_pre_287_shape
cap_seconds: 120
tier: default
diff_stat_lines: ~150
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:10:00Z

### Reproduce
```
python3 -c "
import shape_contracts as sc

def real() -> tuple[list[dict], bool]:
    return ([], True)

def bad_stub(*a, **k):
    return (5, 'not-a-bool')  # right outer container, wrong inner shape

sc.assert_stub_return_shape(bad_stub, real)
print('PASSED (no error) -- silent divergence')
"
```

### Observed
```
PASSED (no error) -- silent divergence
```
No AssertionError raised even though the stub's inner element types (int instead of list[dict], str instead of bool) don't match the real function's declared `tuple[list[dict], bool]` annotation at all.

### Expected
`assert_stub_return_shape` is documented as checking a stub's return value "against the real function's `-> ...` return annotation" and exists specifically to catch stubs whose return shape has drifted from production (the #287 list-vs-tuple case it was built to close). Because `origin = typing.get_origin(ann) or ann` discards the annotation's type arguments (`get_origin(tuple[list[dict], bool])` returns bare `tuple`, dropping `list[dict]` and `bool`), any stub returning a same-arity tuple/list of arbitrary element types passes. This is the same category of drift the function was written to catch, just one level deeper — a stub could return `(None, None)`, `({}, {})`, or any garbage 2-tuple and this "shape contract" would still say the stub matches production.
