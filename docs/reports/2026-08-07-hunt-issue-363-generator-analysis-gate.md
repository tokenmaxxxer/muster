---
proposal: docs/issue-363/proposals/2026-08-07-generator-analysis-gate.md
---

# Hunt record — issue-363-generator-analysis-gate

## after-proposal — stance 1: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — the proposal's own regex `generator:\s*(fixed|deferred)` is unanchored substring matching, so a sentence that explicitly negates or merely mentions the claim (e.g. while explaining that the author is NOT ready to declare `fixed`) still satisfies the check
Kind: design-error
Seed: docs/issue-363/proposals/2026-08-07-generator-analysis-gate.md, section "What will be done" item 1: "Requires, within that section, a line matching `generator:\s*(fixed|deferred)`."
cap_seconds: 180
tier: default
diff_stat_lines: 246
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:05:00Z

### Reproduce
Not yet implemented (phase 1, design only — no `proposal_generator_section` function exists
anywhere in the repo, confirmed via `grep -rn "proposal_generator_section" .`). Reproduced the
exact regex the proposal specifies against a `## Generator` section whose prose explicitly
disclaims real analysis:

```python
import re
pat = re.compile(r'generator:\s*(fixed|deferred)')
text = """## Generator

We have not finished analysis yet. It would be dishonest to write generator: fixed right now,
so we are explicitly punting on real analysis, but the regex this gate uses cannot tell that
apart from a genuine claim -- it only checks substring shape.
"""
m = pat.search(text)
print('match:', m)
```

### Observed
```
match: <re.Match object; span=(80, 96), match='generator: fixed'>
```
The regex matches and would pass the gate, even though the surrounding sentence is an explicit
admission that no real fix/analysis exists.

### Expected
The proposal's own Rationale section rejects the "non-empty content" trap specifically because
"any non-empty sentence satisfies non-empty ... exactly the symptom-fix-for-a-symptom-fix the
issue warns against." The chosen replacement (`generator:\s*(fixed|deferred)`) is claimed to be
a "structured, self-declared claim" with "a checkable shape" instead — but as specified
(unanchored `re.search`/`re.match` over the section text, no requirement that the match sit at
the start of its own line or outside a negating clause), it is defeated by the exact same class
of prose-padding the trap-heading design was rejected for: the string `generator: fixed` need
only appear anywhere in the section's text, including inside a sentence that says the opposite.
A one-line fix (anchor to `^generator:\s*(fixed|deferred)\s*$` per line, e.g. via
`re.MULTILINE`) would close this, but the proposal as written does not specify that anchoring.
