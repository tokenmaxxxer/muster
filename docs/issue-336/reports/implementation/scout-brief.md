# Scout brief — issue #336

Mode: 1 web search angle (batched, single call) — non-product internal
tooling decision, budget scaled down accordingly. Stages used: 1
sweep + 0 deepening (saturated: the sweep already converged on one
established pattern family, a second round would not change the
build decision).

## Category must-bes (from doc-drift-detection tooling, 2026)

- A single artifact is the declared source of truth; everything else
  is checked against it, not against each other pairwise.
- Drift is caught mechanically (hash/AST fingerprint comparison), not
  by an agent re-reading prose for contradictions each time.
- The check runs in CI and blocks merge on drift — it is a gate, not
  a report.

## Adopt

Content-hash manifest + CI gate (fiberplane/drift's pattern: "bind
specs to code and check for drift" — here, bind a reconciliation
index to the spec-shaped docs and check for drift). This is
mechanically checkable per #310 without needing semantic
contradiction detection.

## Skip

Full AST/tree-sitter fingerprinting (drift's approach for source code)
— overkill for prose docs; a whole-file SHA256 is sufficient since any
edit to a spec-shaped doc should trigger a reconciliation look, not
just semantically meaningful edits. Also skip AI-agent-driven
auto-realignment PRs (Augment/AgentPatterns pattern) — out of scope,
adds a new automated-writer surface this issue didn't ask for.

## Gap line

Current state has zero of the category must-bes: no declared source
of truth, no mechanical check, no CI gate. Full gap — the whole
pattern is missing, not partially present.

## Segment fit

This repo already has a `gates/` directory of deterministic,
zero-LLM checks run by `spawn.py` after every session (see
`docs/handbooks/on-the-record.md:26`) — the hash-manifest-gate pattern
fits directly into that existing convention rather than introducing a
new one.

Sources:
- https://github.com/fiberplane/drift
- https://fiberplane.com/blog/drift-documentation-linter/
- https://buildwithfern.com/post/api-governance-documentation-enterprise-sync
