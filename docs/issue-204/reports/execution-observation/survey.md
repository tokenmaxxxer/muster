# Survey — issue #204: execution-observation of PR #211 (`implementation` role, phase 2)

## Scope

Observed: role `implementation`, subject `issue-204`. Sessions landed as PR #208
(`implementation` phase 1 — survey + proposal, merge commit `0ba20c5`, sole commit
`eda5bd2`, merged 2026-08-02T11:34:02Z) and PR #211 (`implementation` phase 2 — code
+ record, merge commit `cfeb3c5`, merged 2026-08-02T12:57:10Z). Code commit under
observation: `dd65451f07f8980e1ddd969eb8a6c45a42c6ae6f` (`conftest.py` + 3 fixture
JSON files, 18 insertions, confirmed via `git show dd65451 --stat`). Record commit:
`0ab22b4b4734562adffef1a912cf9f956f98abef` (`docs/issue-204/reports/implementation.md`
+ hunt report, 277 insertions, confirmed via `git show 0ab22b4 --stat`).

## Scope skip record (scout-directive)

Scouting is skipped. Skip condition: the spec — this role's own directive (the
three-level outcome/trajectory/step verdict format, the citation-adjacency rule, the
blameless four-part finding shape, the record path) plus this session's own task
instruction, which already enumerates the four judgment items phase 2 must check
(요구 1 network-blocked 0-fail reconfirmation, 요구 2 open-network no-regression
citation, `setdefault` non-clobber, hunt open-finding disposition) — leaves no design
decision open for this proposal to make. This is a mechanical evidence-gathering task
against an already-fixed spec (issue #204's own requirements + the observed role's
own record), not a product/design choice to scout industry practice for. No
`scout-brief.md` is written.

## What was read this session

- `gh issue view 204` (full body: 배경, 요구사항 1-3, 방향 a/b/c, 참고, 범위 밖, 실행
  계획 2-step checklist) and `gh issue view 204 --json comments` — exactly one
  comment, `APPROVE issue-204/implementation`, author `jjongkwann`, association
  MEMBER, 2026-08-02T12:11:58Z,
  https://github.com/tokenmaxxxer/on-the-record/issues/204#issuecomment-5157765047.
  No `APPROVE issue-204/execution-observation` comment exists.
- `gh pr list --search "204" --state all` — PR #208 (phase 1, MERGED) and PR #211
  (phase 2, MERGED), both head branch `issue-204/implementation`.
- `gh pr view 211` (summary, verification bullets, hunt-disposition paragraph) and
  `gh pr diff 211` (full diff: `conftest.py` new, 15 lines; three fixture JSON files;
  `docs/issue-204/reports/implementation.md` new, 218 lines;
  `docs/reports/2026-08-02-hunt-issue-204-rulebook-checkout-test-fixture.md` new, 59
  lines).
- `docs/issue-204/proposals/rulebook-checkout-test-fixture.md` (on `main`, approved
  phase-1 proposal, full) — frozen `files:` write set (`conftest.py` + 3 fixture
  JSONs), Constraints (non-clobber via `setdefault`, `spawn.py` untouched), Rationale
  with three named-and-rejected alternatives (per-test monkeypatch, `network` marker
  + skip, per-class env injection), and a "How you'll know it worked" section that
  explicitly states this session's own sandbox cannot reach real GitHub either and
  defers requirement 2's real open-network confirmation to "phase 2
  execution-observation" (i.e., this role, this issue's step 2).
- `docs/issue-204/reports/implementation/survey.md` (on `main`, phase-1 survey, full)
  — full-inventory triage of all 18 network-blocked failures (16 assigned to
  candidate (a), 2 already out-of-scope per issue #201), the git-hook-copy-denial
  reproduction methodology used as this repo's stand-in for "network-blocked," and a
  spike measurement of `152 passed in 12.74s` using an out-of-tree fixture built
  before any repo file was written.
- `docs/issue-204/reports/implementation.md` (on `main`, phase-2 record, full) —
  frontmatter `code_under_review: dd65451`, `loop_state: landed`, 5
  `closed_checks` entries; §검증 transcripts: `152 passed in 18.01s` (both env vars
  fully unset), a `python3 -c` non-clobber assert (ambient values preserved through
  `import conftest`), `152 passed in 14.15s` (ambient override left in place, re-run);
  a note that a bare `pytest -q` (no file args) shows 9 unrelated pre-existing
  failures reproducing identically with `conftest.py` present or removed; and a
  "Hunt" + "Open findings" section carrying the hunt's FINDING forward with an
  explicit rationale for not widening the write set.
- `docs/reports/2026-08-02-hunt-issue-204-rulebook-checkout-test-fixture.md` (on
  `main`, full) — one stance (composition regression), verdict FINDING: the repo's
  own documented non-pytest entry points (`python3 test_gates.py` per README.md,
  `python3 -m unittest test_spawn.py` per an issue-31 QA survey) never import
  `conftest.py`, so `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` stay unset on those
  paths and `rulebook_source`/`rulebook_checkout`/`core_root` fall through to the real
  network path. Two repro scripts (A: no conftest import, B: conftest imported first)
  with observed output for each, matching the claim.
- `conftest.py` (current working tree, 15 lines) — `os.environ.setdefault(...)` calls
  for both env vars, `_FIXTURES = Path(__file__).parent / "tests" / "fixtures" /
  "rulebooks"`; content matches the `dd65451` diff exactly.
- `git show dd65451 --stat`, `git show 0ab22b4 --stat`, `git show cfeb3c5 --stat` —
  confirms commit boundaries, file lists, and that `cfeb3c5` is PR #211's actual merge
  commit (6 files, 295 insertions, matching the sum of `dd65451` + `0ab22b4`).
- `gh pr view 211 --json ...commits` — `dd65451` authored 2026-08-02T12:34:09Z,
  `0ab22b4` authored 12:37:01Z, PR #211 merged 12:57:10Z — all after the
  `APPROVE issue-204/implementation` comment (12:11:58Z).
- `docs/specs/approvers.md` — approver accounts `JiwonJung94`, `jjongkwann`.
- `gh pr list --state all --search "head:issue-204/execution-observation"` — empty.
  Confirms no PR yet exists for this role's branch on this issue, i.e. this role's
  own phase 1 has not previously run.
- `gh pr view 207 --json ...reviews,comments` and `gh issue view 197 --comments` (read
  for procedural precedent only) — issue #197 shows the identical two-step pattern
  this role's directive requires: PR #207 (`execution-observation` phase 1, survey +
  proposal, no verdict language) merged with zero reviews/comments on the PR itself,
  then a separate GitHub issue comment `APPROVE issue-197/execution-observation`
  posted by `jjongkwann`, then PR #209 opened for phase 2. This confirms the
  issue-level `APPROVE issue-<n>/execution-observation` string is this repo's actual,
  previously-exercised mechanism for opening this exact role's phase 2 — not a
  formality that gets skipped when the requester is a human giving instructions
  directly in a chat session.

## Current-state facts about PR #211, mapped to the four judgment items named in this session's task instruction (read statically; no code re-executed this session)

1. **요구 1 (network-blocked, 0 fail) reconfirmation.** `implementation.md` records
   `TOKENMAXXXER_RULEBOOKS= TOKENMAXXXER_CORE= python3 -m pytest test_spawn.py
   test_gates.py -q` → `152 passed in 18.01s`. `survey.md`'s independently-recorded
   spike (built before any repo file existed, in a throwaway out-of-tree fixture) got
   `152 passed in 12.74s` with the same 152-test total and the same
   `18 failed, 134 passed` pre-fix baseline (`survey.md` §전수조사 vs.
   `implementation.md`'s "`18 failed, 134 passed` → `152 passed`"). This role's
   directive prohibits re-running the observed role's code
   ("PROHIBITED, always: never re-run the observed role's code"), so this session did
   not execute pytest to reconfirm; the two independently-recorded totals agreeing is
   the citation-based check available under that constraint.
2. **요구 2 (open-network no-regression).** `implementation.md` states plainly that
   this sandbox also lacks real GitHub access and substitutes a `setdefault`
   non-clobber proxy (ambient override pre-set to a non-fixture path, survives
   `import conftest`, and the full command still gives `152 passed in 14.15s`). This
   session's task instruction separately cites an "orchestrator" measurement
   ("네트워크 열린 로컬, 동일 명령 152 passed 13초") that does not appear in any file
   read this session — no commit SHA, file:line, or PR/issue comment URL backs it.
3. **요구 3 (`setdefault` non-clobber).** `conftest.py:14-15` (current tree, matches
   `dd65451`) uses `os.environ.setdefault(...)` for both vars, not `os.environ[...] =
   ...`. `implementation.md`'s §검증 2 records a direct `python3 -c` assertion that
   pre-set ambient values survive `import conftest` unchanged.
4. **요구 4 (hunt open-finding disposition).** The hunt record's one FINDING
   (non-pytest entry points bypass `conftest.py`) is carried into
   `implementation.md`'s "Open findings" section with an explicit not-a-regression /
   outside-the-frozen-write-set argument (the approved proposal's own Out-of-scope
   list already named `test_gates.py`'s non-pytest collection as a separate,
   unaddressed redesign) — not silently dropped and not silently fixed outside the
   approved write set.

## Gate check before phase 2 opens

As of this session, issue #204's only comment is `APPROVE issue-204/implementation`
— no `APPROVE issue-204/execution-observation` comment exists
(`gh issue view 204 --json comments`), and no PR exists yet for the
`issue-204/execution-observation` branch
(`gh pr list --state all --search "head:issue-204/execution-observation"` → empty).
Per role-handoff contract v3 s19, and per this repo's own issue-197 precedent for
this exact role (PR #207 phase-1 merged with no verdict language → issue comment
`APPROVE issue-197/execution-observation` → PR #209 opened for phase 2), phase 2 does
not open until one of the two approval paths is satisfied for this role specifically,
from a `docs/specs/approvers.md` account (`JiwonJung94` or `jjongkwann`). This
session's own task instruction, delivered as chat prose rather than a GitHub act, is
not that approval — the interaction protocol states "Never read approval out of
prose." This survey, the accompanying proposal
(`docs/issue-204/proposals/execution-observation-plan.md`), and the PR that carries
them are this session's phase-1 output; phase 2 (the verdict record at
`docs/issue-204/reports/execution-observation.md`) is deferred to a future session
after approval.
