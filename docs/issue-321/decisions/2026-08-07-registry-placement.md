# Requirements registry placement: docs/specs/, not docs/issue-321/

The registry file itself (`docs/specs/requirements.md`) lives under
`docs/specs/`, not under `docs/issue-321/reports/` or
`docs/issue-321/proposals/`.

Alternative considered and rejected: keep the registry inside
`docs/issue-321/reports/implementation/` alongside this issue's own
record. Rejected because the registry is system design that spans every
issue past and future — it should change only when the registry's own
design changes (a new field, a new status value), not on every unrelated
issue's cadence. Per role-handoff contract v3, `docs/specs/` is exactly
where system design that outlives a single issue belongs; a per-issue
`docs/issue-<n>/` tree is scoped to that issue's own lifecycle and would
make the registry look like it belongs to #321 rather than to the whole
board.

The gate function (`gates.requirement_registry`) and its wiring in
`gates/ci.py` are ordinary code, not documents, so this decision does not
apply to them — they follow the existing `gates/` layout used by every
other record gate (`record_enums`, `record_fulfils_diff`, etc.).
