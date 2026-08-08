proposal: docs/issue-522/proposals/2026-08-09-loop-state-keys.md

## after-proposal

docs-only, no after-proposal dispatch — both touched paths
(`docs/issue-522/proposals/2026-08-09-loop-state-keys.md`,
`docs/issue-522/reports/implementation/survey.md`) are under `docs/`.
Phase 1 stops here (proposal only); no before-landing transition in this
session either, per the same docs-only fast path.

## before-landing -- stance 0: assume the gate just touched is bypassable -- find the bypass

Verdict: NO FINDING
Seed: roles/issue-retrospective.json, roles/release-engineering.json -- 8-line diff adding record_fields.loop_state vocab lists (previously empty record_fields: {})
cap_seconds: 60
tier: default
diff_stat_lines: 8
started_at: 2026-08-09T01:27:48+09:00
ended_at: 2026-08-09T01:29:38+09:00

Traced enforcement path: gates/gates.py:record_enums (registered in ALL at gates.py:1203) is a
generic role-agnostic check -- for any changed report record file matching the pattern
`^docs/issue-[^/]+/reports/([^/]+)\.md$`, it loads `roles/<role>.json` by the captured
filename and rejects any `loop_state` frontmatter value not in the declared
`record_fields.loop_state` list (fail-closed if the role file is unreadable or if the
origin/main diff can't be resolved). It is not restricted to `roles/implementation.json`
despite the `# CLAIM-CHECK: enum-subset roles/implementation.json:...` comment above it (that
comment documents one example claim, not the code's scope) -- the role lookup is generic by
filename, so it applies uniformly to `issue-retrospective` and `release-engineering` the moment
their JSON declares a non-empty `loop_state` list, exactly like it now does. Reproduced directly
against this checkout with a synthetic repo (origin/main tracking ref set up, then a commit
adding a release-engineering report record with `loop_state: made-up-value`):

    RESULT ["record enum violation: <sandbox-path>/release-engineering.md loop_state='made-up-value'
    -- roles/release-engineering.json declared values (['idle', 'readiness', 'rollout', 'steady',
    'incident']) do not include it"]

i.e. the gate correctly rejects the out-of-vocabulary value using the live
`roles/release-engineering.json` in this repo. Before this diff, `record_fields: {}` meant
`declared` was an empty dict and the loop over `declared.items()` at gates.py:340 was a no-op --
so the list was genuinely decorative for these two roles. After this diff it is not: no value,
path, or role-name variant tested slipped past `record_enums` for either role. Did not find a
separate wiring gap (e.g. a hook or CI step that runs `ALL` gates but excludes `record_enums`,
or excludes these two roles specifically) within the time budget.
