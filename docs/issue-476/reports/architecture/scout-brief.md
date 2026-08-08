# Scout — issue #476, architecture phase-1

**Skip record.** External category scouting (independent-verification literature, re-execution-
as-ground-truth patterns, refusal-cost-parity) was already run exhaustively in phase-1
product-discovery (`docs/issue-476/reports/product-discovery/scout-brief.md`) and is cited
directly in the discovery proposal's H1/H2 gaming-resistance arguments. The decision left open at
this stage is not "which category of mechanism" (settled: H1 primary, H2 secondary, pre-registered
and timestamped) but "where on this specific plugin's file layout does the mechanism attach" —
answered by reading `spawn.py`/`gates/`/`run.md` directly (see `../architecture/survey.md`), which
is a current-state-survey question, not a field-scouting question. Re-running the discovery scout
sweep here would duplicate it against the same sources for no new decision. Skip condition applied:
"the spec literally leaves no design decision open" for the *category* axis specifically — the
*integration* axis is answered by the survey, not by scouting.
