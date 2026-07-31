# Implementation record — issue-170, PR A (engineering-adjacent cluster)

## Scope of this PR

Per the approved proposal (`docs/issue-170/proposals/split-roles-catalog-and-rulebook-skeleton.md` §3), phase-2 delivery splits into 3 PRs by domain cluster. This PR is **PR A — engineering-adjacent (10 roles)**: `ux-engineering`, `api-design`, `architecture`, `security-threat-model`, `data-modeling`, `performance-engineering`, `accessibility`, `secure-coding`, `ml-engineering`, `data-engineering`. PR B (business/GTM, 11 roles) and PR C (content/comms/docs, 5 roles) land as separate PRs on this same branch/issue.

## What was done

- 10 new `roles/*.json` files, one per PR-A role, schema-identical to the existing 17 (`marketplace`/`repo`/`path`/`sandbox`/`decides`/`use_when`/`produces`/`write_scope`/`record_fields.loop_state`). `decides`/`use_when`/`produces`/hand-off values taken verbatim from `docs/issue-160/proposals/role-taxonomy.md`'s "26 promoted roles (round 3)" table. `write_scope` resolved per proposal §1: `[]` for 8 of the 10 roles (report-only), `["docs/issue-<n>/decisions/**"]` for `architecture`, `["src/**"]` for `data-modeling`. `record_fields.loop_state` is the 4-state lifecycle for `architecture`/`data-modeling` (non-empty write_scope) and the single-state `["landed"]` for the other 8.
- 10 rulebook skeleton subtrees under `docs/issue-170/_assets/rulebook-skeleton/<role>/**`, 10 files each (100 files total), same shape issue-167 landed: `.claude-plugin/marketplace.json`, `README.md`, `docs/specs/approvers.md` at the skeleton root; `<role>/.claude-plugin/plugin.json`, `<role>/hooks/{hooks.json,directive.sh,record-fields-gate.sh,trailer-gate.sh,handbook-trigger-gate.sh}`, `<role>/agents/warrant-hunter.md` nested under the role's own subdirectory (mirrors the real rulebook repo's root). `record-fields-gate.sh` carries each role's own `produces`-derived required-field slugs (e.g. `security-threat-model`: `stride-table`, `mitigation-list`, `residual-risk-note`), not copied from any other role.
- `spawn.py`'s `ROLES` tuple and `test_gates.py:216`'s `len(spawn.ROLES) == 17` assertion: **not touched**, per proposal §2 (issue-167 precedent carried forward — `ROLES` is board display order for the original 9-role sequential lifecycle chain, not a full role registry).

## Upstream basis

`docs/issue-160/proposals/role-taxonomy.md`'s "26 promoted roles (round 3)" table (lines 51-80), carrying `decides`/`use_when`/`produces`/`write_scope`/hand-off verbatim, and the approved `docs/issue-170/proposals/split-roles-catalog-and-rulebook-skeleton.md`.

## What did not work

Nothing failed; delivery matched the proposal on the first pass. One process note: `Workflow` (multi-agent orchestration tool) declined with "Review dynamic workflow before running" in this headless session — degraded to single-batch `Agent`-tool dispatch of all 10 role-writer workers per the freelunch directive's stated fallback order, which completed successfully.

## Closed checks — full grep + main-baseline pytest comparison

Main baseline commit at time of this record: `757466d` (origin/main, `Merge pull request #173 from tokenmaxxxer/issue-172/implementation`); this branch is based on `a4c499a` (issue-170 phase-1 proposal, merged to main as PR #171 at `7253506`).

```
$ python3 -m pytest test_vocab_coherence_roles.py test_gates.py -q
1 passed in 0.07s
```

`ROLES` length assertion (`test_gates.py:216`) passes unchanged, confirming §2's decision held.

```
$ grep -rn "market-analysis\|ux-engineering\|api-design\|architecture\|security-threat-model\|legal-compliance\|data-modeling\|performance-engineering\|accessibility\|secure-coding\|ml-engineering\|data-engineering\|technical-writing\|finance-unit-economics\|pricing\|sales\|marketing\|growth-analytics\|customer-support\|partnerships-bd\|pr-communications\|risk-management\|brand-design\|content-design\|localization\|devrel" roles/*.json
roles/architecture.json:2:  "marketplace": "tokenmaxxxer-architecture",
roles/architecture.json:3:  "repo": "tokenmaxxxer/architecture-rulebook",
roles/architecture.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/architecture-rulebook",
roles/performance-engineering.json:2:  "marketplace": "tokenmaxxxer-performance-engineering",
roles/performance-engineering.json:3:  "repo": "tokenmaxxxer/performance-engineering-rulebook",
roles/performance-engineering.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/performance-engineering-rulebook",
roles/data-engineering.json:2:  "marketplace": "tokenmaxxxer-data-engineering",
roles/data-engineering.json:3:  "repo": "tokenmaxxxer/data-engineering-rulebook",
roles/data-engineering.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/data-engineering-rulebook",
roles/ml-engineering.json:2:  "marketplace": "tokenmaxxxer-ml-engineering",
roles/ml-engineering.json:3:  "repo": "tokenmaxxxer/ml-engineering-rulebook",
roles/ml-engineering.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/ml-engineering-rulebook",
roles/data-modeling.json:2:  "marketplace": "tokenmaxxxer-data-modeling",
roles/data-modeling.json:3:  "repo": "tokenmaxxxer/data-modeling-rulebook",
roles/data-modeling.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/data-modeling-rulebook",
roles/ux-engineering.json:2:  "marketplace": "tokenmaxxxer-ux-engineering",
roles/ux-engineering.json:3:  "repo": "tokenmaxxxer/ux-engineering-rulebook",
roles/ux-engineering.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/ux-engineering-rulebook",
roles/accessibility.json:2:  "marketplace": "tokenmaxxxer-accessibility",
roles/accessibility.json:3:  "repo": "tokenmaxxxer/accessibility-rulebook",
roles/accessibility.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/accessibility-rulebook",
roles/api-design.json:2:  "marketplace": "tokenmaxxxer-api-design",
roles/api-design.json:3:  "repo": "tokenmaxxxer/api-design-rulebook",
roles/api-design.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/api-design-rulebook",
roles/security-threat-model.json:2:  "marketplace": "tokenmaxxxer-security-threat-model",
roles/security-threat-model.json:3:  "repo": "tokenmaxxxer/security-threat-model-rulebook",
roles/security-threat-model.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/security-threat-model-rulebook",
roles/secure-coding.json:2:  "marketplace": "tokenmaxxxer-secure-coding",
roles/secure-coding.json:3:  "repo": "tokenmaxxxer/secure-coding-rulebook",
roles/secure-coding.json:4:  "path": "$TOKENMAXXXER_RULEBOOKS/secure-coding-rulebook",
roles/test-authoring.json:17:  "produces": "suite architecture note, fixture strategy, smell list (Meszaros catalog refs)",
```

Matches exactly the 10 PR-A files (plus one incidental substring hit inside `test-authoring.json`'s unrelated `produces` prose, expected and harmless — "architecture" appears as a common noun there, not a role reference).

## Open findings / follow-ups (carried from proposal, not re-opened here)

- `board()`'s known gap (renders only `ROLES`-listed roles) remains unfixed — belongs to whichever future issue first needs to display one of these roles' status.
- `ux-engineering`/`api-design`/`brand-design`'s design-system source-path `write_scope` resolution (kept `[]`, no such tree exists in this repo yet) is a follow-up for whichever future issue adds one.
- GitHub repo creation (10 of the 26 `gh repo create ...-rulebook` commands) and rulebook-skeleton push are human-run, out of this session's write authority — proposal §5 lists the full 26-repo command set; only this PR's 10 roles' skeletons are ready to push once their repos exist.
