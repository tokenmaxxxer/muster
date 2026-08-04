---
kind: survey
subject: issue-227
date: 2026-08-04
phase: 1
---

# Current-state survey — execution-observation of issue #227 step 2

## Scope under observation (named, not "recent work")

- **Role observed**: `implementation`, on branch `issue-227/implementation`.
- **Session observed**: the phase-1→phase-2 run that produced PR **#254**
  (`https://github.com/tokenmaxxxer/on-the-record/pull/254`), title
  "issue-227: conditional-approval relay recipe + warn policy", author
  `jjongkwann`, base `main`, state MERGED at `2026-08-04T02:03:57Z`, merge
  commit `a4eca54`.
- **Issue**: #227 — "조건부 승인 릴레이 규칙 미명문화", execution plan step 1
  (implementation, the observed step) and step 2 (execution-observation, this
  role's step).
- **Observer**: this role, `execution-observation`, branch
  `issue-227/execution-observation`. This role did not author, and has not
  edited, any file in PR #254 or on branch `issue-227/implementation`.

## What was read this session (evidence inventory)

Read directly in this session — nothing below is secondhand:

1. `gh issue view 227` — issue body (배경 / 요구사항 3항 / 제약 2항 / 실행
   계획 2 steps) and `gh issue view 227 --comments` — all three comments.
2. `gh pr view 254 --json ...` — PR metadata: `state=MERGED`,
   `mergedAt=2026-08-04T02:03:57Z`, `mergeCommit=a4eca54`,
   `headRefName=issue-227/implementation`, `reviews=[]` (empty — no PR review
   object of any state exists on #254), and the four commit objects with their
   full messages.
3. Commit SHAs on PR #254, read as commit objects:
   - `75f32f0f2a91bfbb7a0d86a90492740e7a50e2d1` — phase 1 (survey, scout,
     proposal).
   - `681f61e450efcfda9d9d52595c33a00110631ce6` — phase 1 rework (empirical
     gate run + non-canonical-form policy).
   - `144b413a1a2f4eff6458cf4bdc114622ddffdd4c` — phase 2 content. Full diff
     read (`git show 144b413`): 3 files, +140/-0.
   - `6fee354d8f31a953b7658ac23a4cfb3ce6bd9b2c` — phase 2 record, +291.
4. The observed role's own record: `docs/issue-227/reports/implementation.md`
   (291 lines, read in full).
5. The approved proposal: `docs/issue-227/proposals/implementation.md` (205
   lines, read in full).
6. Contract text: `protocol.md:217-246` (§5 Approval — a GitHub act) and
   `protocol.md:255-257` (invariant 4). Token occurrences located by grep
   across `protocol.md`, `README.md`, `docs/handbooks/operations.md`,
   `on-the-record/commands/run.md`.
7. `docs/specs/approvers.md` — two logins: `JiwonJung94`, `jjongkwann`.
8. Live relay comments and their metadata on issues #224, #245, #246 (and
   #227 itself), via `gh issue view <n> --comments` and
   `gh issue view <n> --json comments --template ...`.

Not read as evidence, deliberately: `gates/flows.py`, `spawn.py`, and any
other `src/`-side file. Under this role's directive, current source state is
not evidence of what the observed session did; the admissible artifacts are
its diff, its commits, and its record.

## Current state — what PR #254 actually landed

`144b413` (+140, 3 files, no deletions):

| File | Δ | Content landed |
| --- | --- | --- |
| `on-the-record/commands/run.md` | +14 | Step 6: **조건부 승인** bullet (two issue comments in order — (a) token-only `gh issue comment` with body exactly `APPROVE issue-<n>/<역할>`, (b) separate feedback comment referencing (a)) and **비정규 형태(warn)** bullet (near-miss = body contains literal `APPROVE` but is not whole-body-identical; post exactly one reply pointing at the recipe, keep waiting, never treat as approval, never repeat). Both close with the issue-#224 cross-reference. |
| `docs/handbooks/operations.md` | +18 | Same recipe and warn policy in English, appended to the canonical-approval-location section (after the existing `gh issue comment` canon at `operations.md:313`). |
| `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md` | +108 (new) | Decision + companion warn policy; "Why (adopted)" citing `docs/decisions/2026-07-29-permanently-closed-alternatives.md`; empirical run results for `gates/flows.py::_pr_approved()` (→ `False`) and `spawn.py::approve_scope()` (→ `SystemExit`) against the verbatim rsb #20/#23 bodies plus a token-only control (→ `True` / `rc=0`) and a synthetic prose-before-token variant (→ `False`); two rejected alternatives; warn-vs-abort-vs-log-only tradeoff table; "Related, not superseded: issue #224". |

`6fee354` (+291): `docs/issue-227/reports/implementation.md` — the observed
role's phase-2 record. Frontmatter `kind: coding-record`, `loop_state:
landed`, `code_under_review` as a three-file list, six `ref:`-keyed
`closed_checks`. Sections present: Why / What was done / What will be done
(from proposal) / What did not work / Doc-placement ladder / Hunt (stance
composition-regression, 3 findings all dispositioned non-blocking, 5 clean
checks) / Verification run / Open findings / Next steps / Open-finding
resolution path.

## Current state — the approval event on the observed PR

- `gh pr view 254 --json reviews` → `[]`. No PR review Approve exists.
- Issue-level approval comment:
  `https://github.com/tokenmaxxxer/on-the-record/issues/227#issuecomment-5166285829`,
  `2026-08-03T12:26:37Z`, author `jjongkwann` (listed in
  `docs/specs/approvers.md`), body rendered by `gh issue view 227 --comments`
  as the single line `APPROVE issue-227/implementation`.
- PR #254 author is also `jjongkwann` → single-account mode, which
  `protocol.md:239-246` names as the path where the issue comment is the only
  approval channel.
- The observed record claims exactly this basis at
  `docs/issue-227/reports/implementation.md:23-29`, including the same
  timestamp `2026-08-03T12:26:37Z`.

## Current state — the three documents' relationship to the contract text

Canon locations for the token, located by grep this session:

- `protocol.md:219-222` — approval is an `APPROVED` PR review **or** a comment
  that is exactly `APPROVE issue-<n>/<role>` from an `approvers.md` login.
- `protocol.md:239-246` — the canonical location is the **issue comment**;
  PR-review Approve is the two-account hardened alternative; and: *"Location
  drift here already caused one missed approval (issue-126); do not
  reintroduce a second signal location without updating all three together."*
- `README.md:41`, `README.md:64` — same token, same issue-comment canon.
- `docs/handbooks/operations.md:125` (Korean section), `:313` (English
  section) — the `gh issue comment` canon; the new recipe landed at `:318-334`.
- `on-the-record/commands/run.md:210` — 제안 승인 bullet; the new bullets
  landed immediately after.

Open (not judged here — phase 2 material): PR #254 wrote the recipe into two
of those surfaces (`run.md`, `operations.md`) plus a new decision doc, and did
not touch `protocol.md` or `README.md`. Whether `protocol.md:245-246`'s "all
three together" clause reaches a same-location recipe (as opposed to a *new
signal location*, which the recipe does not introduce) is a question this
survey records and leaves open.

## Current state — live relays on issues #224 / #245 / #246 (raw specimens)

Read this session; bodies as rendered by `gh issue view <n> --comments`,
timestamps and URLs from `gh issue view <n> --json comments`.

| Issue | Comment | Time (UTC) | Body shape |
| --- | --- | --- | --- |
| #227 | `#issuecomment-5163763980` | 2026-08-03T07:59:58Z | Prose only ("실물 사례 환류 …" + 추가 요구 (a)(b)). No `APPROVE` token. |
| #227 | `#issuecomment-5166285829` | 2026-08-03T12:26:37Z | Token only: `APPROVE issue-227/implementation`. |
| #227 | `#issuecomment-5173758897` | 2026-08-04T02:04:17Z | Prose only (재오픈 note for step 2). |
| #224 | `#issuecomment-5166077886` | 2026-08-03T12:05:12Z | Token only: `APPROVE issue-224/implementation`. |
| #224 | `#issuecomment-5173757435` | 2026-08-04T02:04:03Z | Token only: `APPROVE issue-224/execution-observation`. |
| #245 | `#issuecomment-5166253167` | 2026-08-03T12:23:10Z | Token only: `APPROVE issue-245/implementation`. |
| #246 | `#issuecomment-5165949228` | 2026-08-03T11:52:01Z | Prose only (범위 확장 3항: 요구 추가 / 해석 추인 / dedup 키 규칙). No token. |
| #246 | `#issuecomment-5166140486` | 2026-08-03T12:11:26Z | Token only: `APPROVE issue-246/implementation`. |

Raw facts recorded, judgment deferred to phase 2:

- Every token-bearing comment in the sample is token-only — zero mixed
  token+prose specimens in this repo's #224/#245/#246/#227 sample.
- Where feedback and approval both occur on the same issue (#227, #246), they
  are in **separate comments**, but the observed order is feedback-then-token
  (#227: 07:59:58 → 12:26:37; #246: 11:52:01 → 12:11:26), whereas the landed
  recipe specifies token-first (comment A) then feedback (comment B).
- All eight specimens except `#224#issuecomment-5173757435`
  (2026-08-04T02:04:03Z) predate `144b413`'s commit time
  (2026-08-04T01:29:51Z), so they are prior practice, not downstream
  conformance to it.

## Write surfaces for this role, and their unknowns

This role's only write surfaces are `docs/issue-227/reports/execution-observation/`
(phase 1) and `docs/issue-227/reports/execution-observation.md` (phase 2).
Unknowns this survey could not close, which the scout pass is aimed at:

1. **What a strong independent execution audit of a documentation/policy
   change checks** — this observation's deliverable class. Thin: this repo has
   prior execution-observation records (issues #232, #235, #228) but no stated
   checklist for a docs-only subject.
2. **How cross-document consistency of a single canonical rule is normally
   verified** — the recipe now exists in three places (`run.md`,
   `operations.md`, decision doc) while two adjacent canon surfaces
   (`protocol.md`, `README.md`) were not touched. Unknown what the field
   treats as the must-be here.
3. **How the field states a finding in an audit that must not edit the
   audited artifact** — this role returns findings only in its own record, so
   the finding shape (impact / timeline / root cause / action item) carries
   all the weight.
4. **Whether "documented policy with no implementing code" is an accepted
   outcome class** — the proposal's Out-of-scope defers the warn policy's
   detection code to an out-of-tree plugin; the observed record's finding 2
   raises the same actor-ambiguity point.
