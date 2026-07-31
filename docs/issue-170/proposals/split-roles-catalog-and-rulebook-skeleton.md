# Proposal — role split ③ : 26 new roles/*.json + rulebook skeletons (issue-170)

files (phase 2 write set): 26 new `roles/*.json` files (list in §1); `spawn.py` (`ROLES` tuple — kept unchanged, decision in §2); `test_gates.py` (no change, per §2); no `.claude-plugin/marketplace.json` in this repo (none exists at repo root). Skeleton output for the 26 rulebook repos lands as files under `docs/issue-170/_assets/rulebook-skeleton/<role>/**` in this repo (a template a human pushes per repo, §4), not as a push to any external repo. `docs/issue-170/reports/implementation.md` (phase-2 record, gated on Approve).

## Request (paraphrased, secrets stripped)
Execute step 3 (final) of the already-merged issue-160 role taxonomy: stand up `roles/*.json` for the 26 round-3-promoted domain roles (market-analysis, ux-engineering, api-design, architecture, security-threat-model, legal-compliance, data-modeling, performance-engineering, accessibility, secure-coding, ml-engineering, data-engineering, technical-writing, finance-unit-economics, pricing, sales, marketing, growth-analytics, customer-support, partnerships-bd, pr-communications, risk-management, brand-design, content-design, localization, devrel), produce a rulebook skeleton per role for a human to push into 26 new GitHub repos, and list the 26 repo-creation+seed commands as a human execution list. Same pattern as issue-167 (②). Given output scale, phase-2 delivery may split into 2-3 PRs if the proposal states each PR's scope.

## Constraints
- Proposal only in this PR — no `roles/*.json` file lands here; phase 2 opens only after human Approve per contract v3 s19.
- `gh repo create` (26 repos) and pushing the rulebook skeleton to them is outside this session's authority — deliverable is a command list for a human, per issue-162/issue-167 precedent.
- Re-deriving `decides`/`use_when`/`produces`/hand-off content is out of scope — already settled and merged in issue-160's role-taxonomy.md (the "26 promoted roles (round 3)" table, role-taxonomy.md:51-80); this proposal only carries it into the new artifact shapes and resolves the few `write_scope` placeholders canon left open.
- Full old/new-name grep + main-baseline pytest comparison must be attached to the phase-2 record per issue-162's stated lesson (carried forward by issue-167, restated in the issue text itself).

## What will be done

### 1. `roles/*.json` — 26 new files, canon values verbatim

Each file follows the existing 17 roles' schema exactly (`marketplace`/`repo`/`path`/`sandbox`/`decides`/`use_when`/`produces`/`write_scope`/`record_fields`, confirmed against `roles/capacity-planning.json`), `decides`/`use_when`/`produces`/hand-off values taken verbatim from role-taxonomy.md's "26 promoted roles (round 3)" table (role-taxonomy.md:51-80) — not reproduced row-by-row here since the canon table is the source of truth and this proposal makes no edit to it; only the `write_scope` resolution below is new decision content:

| role | write_scope (resolved) | rationale |
|---|---|---|
| `market-analysis`, `security-threat-model`, `legal-compliance`, `performance-engineering`, `accessibility`, `secure-coding`, `ml-engineering`, `data-engineering`, `finance-unit-economics`, `pricing`, `sales`, `marketing`, `growth-analytics`, `customer-support`, `partnerships-bd`, `pr-communications`, `risk-management`, `content-design`, `localization` | `[]` | canon's own value; no ambiguity |
| `architecture` | `["docs/issue-<n>/decisions/**"]` | canon's explicit concrete value |
| `data-modeling` | `["src/**"]` (migrations) | canon's explicit concrete value, narrowed from "`src/**` migrations" prose to the path glob `roles/*.json`'s schema expects |
| `technical-writing` | `["docs/**"]` | canon's explicit concrete value ("외부공개 한정" is a use_when qualifier, not a narrower path — no narrower glob exists in this repo to express "external-facing only") |
| `devrel` | `["docs/**"]` | same reasoning as `technical-writing` |
| `ux-engineering` | `[]` | canon leaves this "design-system source paths (TBD at execution)" — this repo has no design-system source tree today, so there is no concrete path to grant; kept empty (safest default, matches how `write_scope: []` already means "no filesystem write authority" for every report-only role) rather than inventing a path that doesn't exist. Flagged as a follow-up for whichever future issue actually adds a design-system source tree. |
| `api-design` | `[]` | same reasoning — canon's "interface/schema paths (TBD at execution)" has no concrete target in this repo yet |
| `brand-design` | `[]` | canon's "design-system source paths" carries no TBD marker but is equally unresolvable against this repo's current tree; same resolution as `ux-engineering` for consistency (both point at the same not-yet-existing design-system source) |

`marketplace`/`repo`/`path` follow the round-6 naming convention already used by all 17 existing files (`tokenmaxxxer-<role>` / `tokenmaxxxer/<role>-rulebook` / `$TOKENMAXXXER_RULEBOOKS/<role>-rulebook`), `sandbox` copies the uniform block every existing role file carries. `record_fields.loop_state`: the 3 roles with non-empty `write_scope` (`architecture`, `data-modeling`, `technical-writing`, `devrel` — 4, not 3; corrected count) get the 4-state lifecycle (`scope-proposed`, `scope-approved`, `in-progress`, `landed`) matching `implementation.json`'s pattern; the 22 report-only roles get the single-state `["landed"]`, matching `capacity-planning.json`'s confirmed pattern.

### 2. `spawn.py` `ROLES` tuple — NOT extended (issue-167 precedent carried forward)

Issue-167 already decided this exact question for the 8 round-4 roles: `ROLES` (spawn.py:646-651) is board *display order* for the original 9-role sequential lifecycle chain, not "all known roles" — and left it unextended. The 26 roles in this issue are domain roles even further from that lifecycle shape (`pricing`, `sales`, `brand-design`, `localization`, etc. have no natural position in a product→ship sequence). The same reasoning applies with more force: **`ROLES` stays at 17; `test_gates.py:216`'s `len(spawn.ROLES) == 17` needs no change.**

`board()`'s known gap (it renders only `ROLES`-listed roles' status, so none of the 8 round-4 roles or these 26 show on a subject's board summary today) remains unfixed here, same as issue-167 left it — a `board()` generic-iteration change is a separate design decision belonging to whichever issue first needs to *display* one of these roles' status, not a bulk-catalog-creation issue.

If phase-2 review disagrees, this is a one-line change (`test_gates.py:216`'s constant moves in lockstep) — open question for the Approve step, not pre-decided.

### 3. Phase-2 delivery split — 3 PRs by domain cluster

Given ~260 skeleton files + 26 `roles/*.json` files, phase-2 delivery splits into 3 PRs on this same branch/issue, each independently reviewable and each carrying its own full-repo grep + pytest comparison in its slice of the record:

- **PR A — engineering-adjacent (10 roles):** `ux-engineering`, `api-design`, `architecture`, `security-threat-model`, `data-modeling`, `performance-engineering`, `accessibility`, `secure-coding`, `ml-engineering`, `data-engineering`.
- **PR B — business/GTM (11 roles):** `market-analysis`, `finance-unit-economics`, `pricing`, `sales`, `marketing`, `growth-analytics`, `customer-support`, `partnerships-bd`, `pr-communications`, `risk-management`, `legal-compliance`.
- **PR C — content/comms/docs (5 roles):** `technical-writing`, `brand-design`, `content-design`, `localization`, `devrel`.

Each PR adds only its cluster's `roles/*.json` files and skeleton subtrees; none touches `spawn.py`/`test_gates.py` (§2's decision means no shared-file edit to sequence across the 3 PRs, so they carry no ordering dependency and can land in any order or in parallel).

### 4. Rulebook skeleton — 26 templates, adapted from issue-167's own landed skeleton

Same 7-file-per-role shape issue-167 already established and landed (`docs/issue-167/_assets/rulebook-skeleton/<role>/**`), used here as the in-repo exemplar instead of re-reading an external checkout:

```
<role>/.claude-plugin/marketplace.json
<role>/.claude-plugin/plugin.json
<role>/README.md
<role>/docs/specs/approvers.md
<role>/agents/warrant-hunter.md
<role>/hooks/hooks.json
<role>/hooks/directive.sh
<role>/hooks/record-fields-gate.sh
<role>/hooks/trailer-gate.sh
<role>/hooks/handbook-trigger-gate.sh
```

As with issue-167, `record-fields-gate.sh` is the one file individually derived per role — each of the 26 gates checks its own `produces` required-field list from role-taxonomy.md's table (e.g. `market-analysis`'s gate checks for a five-forces-summary section, a competitor-list section, and a JTBD-landscape-verdict section) rather than copying any other role's field set. Everything else is templated with the role name substituted, same mechanical pattern issue-167 used.

### 5. GitHub repo creation + skeleton push — human command list

Per issue-162/issue-167 precedent, out of this session's write authority. Recommended order: land the 3 phase-2 PRs first (`roles/*.json` resolves generically the moment its file exists, regardless of whether the target GitHub repo exists) — repos can be created any time after. Commands for a human with org create rights, one per repo:

```
gh repo create tokenmaxxxer/market-analysis-rulebook --public
gh repo create tokenmaxxxer/ux-engineering-rulebook --public
gh repo create tokenmaxxxer/api-design-rulebook --public
gh repo create tokenmaxxxer/architecture-rulebook --public
gh repo create tokenmaxxxer/security-threat-model-rulebook --public
gh repo create tokenmaxxxer/legal-compliance-rulebook --public
gh repo create tokenmaxxxer/data-modeling-rulebook --public
gh repo create tokenmaxxxer/performance-engineering-rulebook --public
gh repo create tokenmaxxxer/accessibility-rulebook --public
gh repo create tokenmaxxxer/secure-coding-rulebook --public
gh repo create tokenmaxxxer/ml-engineering-rulebook --public
gh repo create tokenmaxxxer/data-engineering-rulebook --public
gh repo create tokenmaxxxer/technical-writing-rulebook --public
gh repo create tokenmaxxxer/finance-unit-economics-rulebook --public
gh repo create tokenmaxxxer/pricing-rulebook --public
gh repo create tokenmaxxxer/sales-rulebook --public
gh repo create tokenmaxxxer/marketing-rulebook --public
gh repo create tokenmaxxxer/growth-analytics-rulebook --public
gh repo create tokenmaxxxer/customer-support-rulebook --public
gh repo create tokenmaxxxer/partnerships-bd-rulebook --public
gh repo create tokenmaxxxer/pr-communications-rulebook --public
gh repo create tokenmaxxxer/risk-management-rulebook --public
gh repo create tokenmaxxxer/brand-design-rulebook --public
gh repo create tokenmaxxxer/content-design-rulebook --public
gh repo create tokenmaxxxer/localization-rulebook --public
gh repo create tokenmaxxxer/devrel-rulebook --public
```

Then, per repo, push the corresponding skeleton subtree from `docs/issue-170/_assets/rulebook-skeleton/<role>/` as that repo's first commit (clone the new empty repo, copy the subtree in as its root, `git add -A && git commit -m "seed <role> rulebook skeleton" && git push`) — 26 independent operations, no cross-repo ordering constraint. Visibility and `approvers.md` allowlist seeding are the human operator's choice, same as issue-167 left them.

## Side-effect analysis — use_when orchestration-decidability and flow conflicts

All 26 `use_when` values are condition-shaped, not trigger-shaped, same as every prior taxonomy round — none names a mechanized orchestration signal, unchanged from issue-160's own side-effect section. No `write_scope` overlap found among the 26 or against the existing 17: the only non-empty scopes (`architecture` → `docs/issue-<n>/decisions/**`, `data-modeling`/`technical-writing`/`devrel` → `src/**`/`docs/**`) are disjoint from `implementation`'s `src/**`,`test/**` and `refactoring-legacy`/`test-authoring`'s scopes in the sense that role-taxonomy.md's boundary-case deep dive already covers (`architecture` decides *whether* a boundary exists, distinct from `implementation`'s code diff; `data-modeling`'s `src/**` migrations are schema-only, not general implementation — this distinction is canon's, not re-derived here). `technical-writing`/`devrel` both scope to `docs/**` but are use_when-disjoint (외부공개 문서 vs. 외부 개발자 온보딩) — a real soft overlap already named in canon's own hand-off row (`technical-writing`'s hand-off → `devrel` for developer-onboarding-shaped docs), not a new conflict this issue introduces.

## Out of scope
- `gh repo create`/rulebook-repo push execution itself — human-run per §5.
- Widening `spawn.py`'s `board()`/`status()` to iterate `roles/*.json` generically — same known gap issue-167 flagged, still unresolved, still belongs to a future issue.
- Re-deriving `decides`/`use_when`/`produces`/`write_scope`/hand-off content — settled and merged in issue-160, except the `write_scope` placeholder resolutions in §1 (new decision content, scoped narrowly to those 3 roles).

## How you'll know it worked
- `python3 spawn.py <new-role-name> ...` resolves the role file for each of the 26 (fails later only on missing rulebook repo, expected until §5's human steps run).
- `pytest test_vocab_coherence_roles.py test_gates.py` passes unchanged (`ROLES` length assertion untouched per §2's decision) — run against main baseline and attached to the phase-2 record per issue-162's lesson.
- `grep -rn "market-analysis\|ux-engineering\|api-design\|architecture\|security-threat-model\|legal-compliance\|data-modeling\|performance-engineering\|accessibility\|secure-coding\|ml-engineering\|data-engineering\|technical-writing\|finance-unit-economics\|pricing\|sales\|marketing\|growth-analytics\|customer-support\|partnerships-bd\|pr-communications\|risk-management\|brand-design\|content-design\|localization\|devrel" roles/*.json` returns exactly the 26 new files with canon-matching content, cross-checked against role-taxonomy.md's table — attached full grep output per issue-162's lesson.
- Each of the 26 `docs/issue-170/_assets/rulebook-skeleton/<role>/hooks/record-fields-gate.sh` references that role's own record path and its own `produces` field names, not another role's.
