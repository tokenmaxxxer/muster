# Proposal — role split ② : 8 new roles/*.json + rulebook skeletons (issue-167)

files (phase 2 write set): `roles/user-discovery.json`, `roles/requirements-engineering.json`, `roles/refactoring-legacy.json`, `roles/test-authoring.json`, `roles/observability.json`, `roles/incident-response.json`, `roles/capacity-planning.json`, `roles/knowledge-management.json` (8 new files, no existing file touched); `spawn.py` (`ROLES` tuple — decision below); `test_gates.py` (the `len(spawn.ROLES)` assertion, only if `ROLES` changes); no `.claude-plugin/marketplace.json` in this repo (none exists at repo root — each rulebook lives in its own repo, out of this repo's write scope). Skeleton output for the 8 rulebook repos lands as files under `docs/issue-167/_assets/rulebook-skeleton/<role>/**` in *this* repo (a template a human pushes per repo — see §2), not as a push to any external repo.

## Request (paraphrased, secrets stripped)
Execute step 2 of the already-merged issue-160 role taxonomy: stand up `roles/*.json` for the 8 round-4-promoted roles that split off `product-discovery`/`implementation`/`release-engineering`/`issue-retrospective`, produce a rulebook skeleton (directive/hooks/README/approvers procedure) per role for a human to push into 8 new GitHub repos, enumerate what should migrate out of the split-origin roles' rulebooks (as a list for those repos' own future issues, not executed here), and analyze whether each role's `use_when` is orchestration-decidable.

## Constraints
- Proposal only in this PR — no `roles/*.json` file, no `spawn.py`, no `test_gates.py` edit lands here; phase 2 opens only after human Approve per contract v3 s19.
- `gh repo create` (8 repos) and pushing the rulebook skeleton to them is outside this session's authority — deliverable is a command list for a human, exactly as issue-162's precedent treated the 9 GitHub repo renames.
- Re-deriving `decides`/`use_when`/`produces`/`write_scope`/hand-off content is out of scope — already settled and merged in issue-160's proposal; this proposal only carries it into the new artifact shapes.
- Split-origin rulebook edits (the 4 source roles) are explicitly out of scope per the issue's own text — each migration item below is a **pointer for a future issue against that rulebook repo**, not a change made here.

## What will be done

### 1. `roles/*.json` — 8 new files, canon values verbatim

Each file follows the existing 9 roles' schema exactly (`marketplace`/`repo`/`path`/`sandbox`/`decides`/`use_when`/`produces`/`write_scope`/`record_fields`), values taken verbatim from `docs/issue-160/proposals/role-taxonomy.md`'s "8 promoted roles (round 4)" table:

| role | decides | use_when | produces (required fields) | write_scope | hand-off |
|---|---|---|---|---|---|
| `user-discovery` | 이 문제가 실제 사용자의 고통인가 | 가설 검증을 위해 사용자 인터뷰가 필요할 때 | interview script, per-interview evidence log, pain-confirmed\|not-confirmed verdict | `[]` | 검증된 가설을 스펙화하면 → `requirements-engineering` |
| `requirements-engineering` | 요구사항이 검증가능·일관·추적 가능하게 명세되었는가 | product 가설이 확정되어 정식 스펙으로 전환할 때 | structured requirements doc, traceability matrix, ambiguity list resolved | `[]` | 화면/플로우 설계는 → `interaction-design` |
| `refactoring-legacy` | 기존 코드의 관찰 가능한 동작을 바꾸지 않고 안전하게 재구조화할 수 있는가 | 레거시/기존 코드에 손을 대야 할 때 | refactoring plan, characterization tests, before/after behavior-equivalence note | `["src/**","test/**"]` | 신규 기능 구현이 섞이면 그 부분은 → `implementation` |
| `test-authoring` | 테스트 코드 자체가 격리성·fixture 전략 면에서 좋은 설계인가 | 신규/기존 테스트 스위트를 설계·리뷰할 때 | suite architecture note, fixture strategy, smell list (Meszaros catalog refs) | `["test/**"]` | 실제 실행 결과 관찰은 → `execution-observation` |
| `observability` | 프로덕션 내부 상태에 대해 사전에 정의하지 않은 질문도 던질 수 있는가 | 신규 서비스/경로에 계측이 필요할 때 | telemetry/instrumentation design, cardinality budget, dashboard/query examples | `[]` | 장애가 실제로 발생하면 → `incident-response` |
| `incident-response` | 장애 후 무엇을 배웠고 재발을 무엇으로 막을 것인가 | 장애 종결 직후 | timeline, blameless postmortem, action items w/ owner+deadline | `["docs/issue-<n>/postmortems/**"]` | 용량 부족이 원인이면 → `capacity-planning`; 계측 부재가 원인이면 → `observability` |
| `capacity-planning` | 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가 | 용량 예측/증설 시점 결정이 걸릴 때 | capacity forecast, expansion trigger thresholds, cost note | `[]` | 성능 자체의 병목 원인 분석은 → `performance-engineering` |
| `knowledge-management` | 개별 이슈의 교훈이 조직 차원에서 재사용 가능한 형태로 축적·색인되는가 | 여러 이슈의 회고가 쌓여 지식 큐레이션이 필요할 때 | curated pattern-library entry, cross-issue index, supersession note (if replacing an older pattern) | `["docs/patterns/**"]` | 단일 이슈 회고 자체는 → `issue-retrospective` |

Each file's `marketplace`/`repo`/`path` follow the round-6 naming convention already ratified in issue-160 (`tokenmaxxxer-<role>` / `tokenmaxxxer/<role>-rulebook` / `$TOKENMAXXXER_RULEBOOKS/<role>-rulebook`), `sandbox` copies the uniform block every existing role file carries (`enabled: true`, `allowedDomains: [api.anthropic.com, *.github.com, github.com]`), and `record_fields.loop_state` uses the same 4-state generation lifecycle `implementation.json` carries (`scope-proposed`, `scope-approved`, `in-progress`, `landed`) for the 3 roles with non-empty `write_scope` (`refactoring-legacy`, `test-authoring`, `incident-response`); the 5 report-only roles get the single-state `["landed"]`, matching how existing report-only roles (e.g. `defect-verification.json`'s pattern) mark completion without an in-progress build phase — confirmed at execution time against the actual existing 9 files rather than assumed here, since not all 9 were read this session.

### 2. `spawn.py` `ROLES` tuple — NOT extended

`ROLES` (spawn.py:646-648) is the **board display order** for `status()`/`board()`, iterated to find `docs/issue-<n>/reports/<role>.md` per subject — it exists to render the original 9-role lifecycle chain (product-discovery → … → release-engineering) as one flow. The 8 new roles are not steps in that chain; they are orthogonal domain roles that may or may not appear on a given subject. Adding them to `ROLES` would misrepresent them as sequential lifecycle stages, which issue-160's own taxonomy explicitly rejects (the whole point of the round-3/4 promotion was moving off lifecycle-stage splitting).

**Decision: `ROLES` stays at 9; `test_gates.py:216`'s `len(spawn.ROLES) == 9` needs no change.** The issue text says "spawn.py ROLES 갱신과 테스트 갱신 포함" — read here as conditional instruction ("include the ROLES update *if the design calls for one*"), not a mandate to extend the tuple regardless of fit; `board()`'s docstring (spawn.py:964-966) already states it renders "subject (issue-<n>) -> role -> frontmatter" generically over `ROLES`, so a non-lifecycle role appearing in a subject's `reports/` simply does not show on the board's summary line today — a real gap, but a `board()` behavior change (iterate `roles/*.json` generically instead of the fixed tuple) is a separate design decision belonging to whichever issue first needs to *display* one of these 8 roles' status, not a rename-shaped edit this issue should force through. Flagged here as a known follow-up, not fixed in this PR.

If phase-2 human review disagrees and wants `ROLES` widened now, that is a one-line change (`test_gates.py:216`'s constant moves in lockstep) — noted as an open question for the Approve step rather than pre-decided.

### 3. Rulebook skeleton — 8 templates, adapted (not cloned) from the `implementation-rulebook` exemplar

Read directly from the local checkout `~/tokenmaxxxer/rulebooks/implementation-rulebook` (round-5-renamed `coding-agent-rulebook`), the shape a rulebook repo takes:

```
<repo-root>/.claude-plugin/marketplace.json     # this repo's own plugin registration
<repo-root>/README.md
<repo-root>/docs/specs/approvers.md             # (or: the approve procedure, see below)
<role>/.claude-plugin/plugin.json               # name/description/author
<role>/hooks/hooks.json                         # SessionStart + PreToolUse wiring
<role>/hooks/directive.sh                        # SessionStart: role directive (facets)
<role>/hooks/record-fields-gate.sh              # PreToolUse: this role's record required-field check
<role>/hooks/trailer-gate.sh                    # PreToolUse(Bash): commit Subject: issue-<n> trailer
<role>/hooks/handbook-trigger-gate.sh           # PreToolUse(Bash): s21 handbook-sync gate
<role>/hooks/<role>-progress-gate.sh            # PreToolUse(Bash): blocking-finding gate (if applicable)
<role>/agents/warrant-hunter.md                 # rotating-stance hunt agent
```

Per the issue's explicit instruction, this is **not** a name-substitution copy — the one file whose content must be individually derived per role is `record-fields-gate.sh`: `implementation`'s copy hardcodes `implementation`'s own required sections (`what-was-done`/`why`/`upstream-basis`/`loop_state`/`open-findings`, `record-fields-gate.sh:166-183`) against `docs/issue-<n>/reports/implementation.md`. Each of the 8 new roles' `record-fields-gate.sh` is adapted to (a) match its own record path (`docs/issue-<n>/reports/<role>.md`) and (b) require its own `produces` field list from the table above (e.g. `test-authoring`'s gate checks for a suite-architecture-note section, a fixture-strategy section, and a smell-list section, in place of `implementation`'s generic what-was-done/why/upstream-basis/open-findings set) — this is the "record-fields는 이 역할의 produces 필수 필드로" instruction from the issue, applied per role.

The generated skeleton (8 role directories, each with the 7 files above, `record-fields-gate.sh` content individualized per role's `produces`, everything else templated with the role name substituted) lands at `docs/issue-167/_assets/rulebook-skeleton/<role>/**` in *this* repo at phase 2 — a human then copies each role's subtree as the seed commit of its new GitHub repo (§5), rather than this session pushing to 8 repos it has no authority to create.

### 4. Migration items — split-origin rulebooks (enumerated, not executed)

Per the issue's boundary instruction, prose that should move *out of* the 4 split-origin roles' rulebooks and *into* the corresponding new role, listed for each origin repo's own future issue (this PR makes no edit to any of the 4):

- **`product-discovery-rulebook`** (was the un-split `product`): any directive prose instructing interview-script writing or per-interview evidence-log discipline moves to `user-discovery-rulebook`; any prose instructing traceability-matrix or ambiguity-resolution discipline moves to `requirements-engineering-rulebook`.
- **`implementation-rulebook`** (was `coding`): any directive prose about behavior-preserving restructuring of pre-existing code (as distinct from net-new implementation) moves to `refactoring-legacy-rulebook`; any prose about test-suite fixture-strategy or isolation-smell review (as distinct from writing code that happens to include tests) moves to `test-authoring-rulebook`.
- **`release-engineering-rulebook`** (was `ops`): any directive prose about instrumentation/telemetry design for a new service path moves to `observability-rulebook`; any prose about post-incident blameless writeup discipline moves to `incident-response-rulebook`; any prose about demand forecasting or expansion-trigger thresholds moves to `capacity-planning-rulebook`.
- **`issue-retrospective-rulebook`** (was `reflect`): any directive prose about cross-issue pattern curation or a reusable pattern library (as distinct from a single issue's own timeline/lessons) moves to `knowledge-management-rulebook`.

Each bullet is a scan target for the named repo's next issue, not a claim that such prose currently exists there — unread in this session (those 4 repos' current rulebook content was not fetched; only `implementation-rulebook`'s current shape was read, as the skeleton exemplar). The executing issue against each origin repo should grep its `directive.sh` for the moved-out `decides` language before assuming a match.

### 5. GitHub repo creation + skeleton push — human command list (outside role-session authority)

Per issue-162's precedent (`gh repo rename` for 9 existing repos was likewise a human list, never executed by that role session), repo *creation* is further outside a role session's write-scope than a rename. Recommended order: land this PR's `roles/*.json` first (phase 2, once approved) — `spawn.py` resolves a role generically the moment its JSON exists, regardless of whether the target GitHub repo exists yet, so `roles/*.json` can merge before the repos do without breaking anything already-running. Commands for a human with org create rights (one per repo, run after this PR lands):

```
gh repo create tokenmaxxxer/user-discovery-rulebook --public
gh repo create tokenmaxxxer/requirements-engineering-rulebook --public
gh repo create tokenmaxxxer/refactoring-legacy-rulebook --public
gh repo create tokenmaxxxer/test-authoring-rulebook --public
gh repo create tokenmaxxxer/observability-rulebook --public
gh repo create tokenmaxxxer/incident-response-rulebook --public
gh repo create tokenmaxxxer/capacity-planning-rulebook --public
gh repo create tokenmaxxxer/knowledge-management-rulebook --public
```

Then, per repo, push the corresponding skeleton subtree from `docs/issue-167/_assets/rulebook-skeleton/<role>/` as that repo's first commit (clone the new empty repo, copy the subtree in as its root, `git add -A && git commit -m "seed <role> rulebook skeleton" && git push`) — 8 independent operations, no cross-repo ordering constraint, each safe to run any time after the corresponding empty repo exists. Visibility (`--public` vs `--private`) and any branch-protection/`docs/specs/approvers.md` seed content (who the first approver is) are choices for the human running the command, not pre-decided here — the skeleton ships `approvers.md`'s *procedure* (how it's read, per `spawn.py:_approvers`) but not a populated allowlist, matching how the existing 9 repos leave that to the operator.

## Side-effect analysis — use_when orchestration-decidability and flow conflicts

All 8 `use_when` values above are **condition-shaped, not trigger-shaped**: none names a mechanized orchestration signal (no webhook, no label, no queue depth) — each describes a state a human or an already-running role must recognize and act on by manually opening `issue-<n>/<role>` (same as all 43 taxonomy roles; `use_when` was never meant to be machine-evaluated, per issue-160's side-effect section, which this proposal's survey confirms is unchanged). Two roles carry a soft ordering dependency worth naming explicitly since they sit downstream of an existing role in the same chain:

- `requirements-engineering`'s `use_when` ("product 가설이 확정되어") presumes `product-discovery` ran first on the same subject — no code enforces this ordering (any role can open on any subject at any time per contract v3), so a `requirements-engineering` session opened without a prior `product-discovery` record is not blocked, just under-informed; this is the same non-enforcement already true of every hand-off arrow in the taxonomy table, not a new conflict this issue introduces.
- `incident-response`'s `use_when` ("장애 종결 직후") and `release-engineering`'s existing hand-off arrow ("배포 후 장애면 → incident-response") together mean a `release-engineering` role's own record is the expected trigger source for opening `incident-response` — again advisory, not mechanized; no orchestration code changes as a result.

No conflict found with the existing 9-role lifecycle flow: none of the 8 new roles' `write_scope` overlaps another role's declared `write_scope` except `refactoring-legacy`/`test-authoring` both touching `src/**`/`test/**` alongside `implementation` — already covered by issue-160's boundary-case deep dive (`implementation` ↔ `refactoring-legacy` ↔ `test-authoring`, role-taxonomy.md:99-103), re-derived nowhere in this proposal.

## Out of scope
- `gh repo create`/rulebook-repo push execution itself — human-run per §5.
- Editing any of the 4 split-origin roles' rulebooks — enumerated as migration pointers (§4) for those repos' own future issues, never executed here.
- Widening `spawn.py`'s `board()`/`status()` to iterate `roles/*.json` generically instead of the fixed `ROLES` tuple — flagged in §2 as a real gap, left for the issue that first needs to display one of these 8 roles' status.
- Re-deriving `decides`/`use_when`/`produces`/`write_scope`/hand-off content — already settled and merged in issue-160.

## How you'll know it worked
- `python3 spawn.py <new-role-name> ...` resolves the role file (fails later only on missing rulebook repo, a separate, expected failure until §5's human steps run).
- `pytest test_vocab_coherence_roles.py test_gates.py` passes unchanged (`ROLES` length assertion untouched per §2's decision).
- `grep -rn "user-discovery\|requirements-engineering\|refactoring-legacy\|test-authoring\|observability\|incident-response\|capacity-planning\|knowledge-management" roles/*.json` returns exactly the 8 new files with canon-matching content, cross-checked against `docs/issue-160/proposals/role-taxonomy.md`'s table.
- `docs/issue-167/_assets/rulebook-skeleton/<role>/hooks/record-fields-gate.sh` for each of the 8 roles references that role's own record path and its own `produces` field names, not `implementation`'s.
