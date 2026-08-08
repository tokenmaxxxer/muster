---
proposal: docs/issue-474/proposals/2026-08-08-batch-d-provenance-and-recurrence-gates.md
---

# Hunt record — issue-474-batch-d-proposal

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — Batch D's "adopt #415's design verbatim" claim silently relocates a file #415's own proposal names at repo root.
Kind: design-error
Seed: docs/issue-474/proposals/2026-08-08-batch-d-provenance-and-recurrence-gates.md (commit 2e68905)
cap_seconds: 60
tier: default
diff_stat_lines: 1 file added (proposal doc, ~215 lines)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:02:00Z

### Reproduce
```
grep -n "test_repo_scope_gate" \
  docs/issue-415/proposals/implementation.md \
  docs/issue-474/proposals/2026-08-08-batch-d-provenance-and-recurrence-gates.md
```

### Observed
The #415 proposal's frontmatter `files:` lists `test_repo_scope_gate.py` at repo root, and
its item 2 / acceptance section says `pytest test_repo_scope_gate.py` (no `gates/` prefix).
Batch D's frontmatter `files:` and "## What will be done" item 1 instead name
`gates/test_repo_scope_gate.py`, while Batch D's Constraints section asserts "this proposal
does not redesign them; it adopts each design verbatim ... per the ADR's hand-off
instruction." No section-shape or write-set-self-consistency gate would catch this, since
Batch D's own write-set matches its own body text (`gates/test_repo_scope_gate.py` appears
consistently in both) — the divergence is only visible by cross-referencing the *cited
source document*, which no mechanical shape/order gate does.

### Expected
A "verbatim adoption" claim should either place the file exactly where the adopted proposal
places it, or the Rationale/Constraints section should explicitly name and justify the
relocation (e.g. "unlike #415's own proposal, this batch's test file moves under gates/
because..."). As written, a reader trusting the word "verbatim" gets a materially different
write-set than #415 actually specifies, with no signal that the divergence occurred.
