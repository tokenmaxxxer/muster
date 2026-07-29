# Issue #80 — Phase 1 Proposal (coding)

files:
- `orchestrate/hooks/directive.sh`
- `orchestrate/commands/run.md`
- No file under any `core/` path will be touched (no such path exists in this repo; the sibling `tokenmaxxxer-core` repo is a separate repository entirely out of this proposal's write set).

## Request

Follow up on `docs/issue-76/reports/reflect.md` §1a/§1b (backlog item 1): add missing `(contract v3 sNN)` citations at the two zero-cite approval-string restatement sites, and reduce `orchestrate/hooks/directive.sh`'s informing-hook approval-rule prose to a bare section pointer (no restated rule prose), per issue #80's chosen approach (pointer-only, not build-time generation).

## Constraints

- Do not weaken, remove, or contradict any enforcing-hook behavior — `approval-gate.sh`/`board-gate.sh` (core repo) are unaffected; this proposal only touches muster's two informing surfaces.
- Do not restate contract prose anywhere it isn't already gated by an enforcing hook — the whole point (per the core#18 incident) is that citation-plus-restated-prose still drifts, so 1b removes the restated prose rather than just adding a cite next to it.
- `run.md:185-187`'s exact `gh pr comment ... "APPROVE issue-<n>/<역할>"` command text must stay verbatim (it's an operational instruction the orchestrator runs, not free-standing rule prose) — only the missing citation is added there, no reduction.
- `directive.sh:73`'s bullet is different in kind: it is prose describing the rule (in a hook whose sole job is to inject *steering text*, not to run commands), so it is the pointer-only reduction target per 1b.
- Do not touch `core/` files from this repo; if `core/hooks/directive.sh` (tokenmaxxxer-core) needs the same treatment, that is a separate core-repo issue, not filed here.
- Both files stay in their current language (run.md is Korean prose; directive.sh's heredoc is English) — no bulk translation.

## What will be done

### Site 1 — `orchestrate/hooks/directive.sh` (1a citation, folded into 1b's pointer-only rewrite)

Current (lines 71-79):

```
- Explain returning PRs (phase 1 proposal vs phase 2 delivery), then
  relay the user's decisions per conversation: feedback -> gh pr comment;
  approval -> a comment that is EXACTLY "APPROVE issue-<n>/<role>";
  acceptance -> gh pr merge --delete-branch (a merged role branch is
  always deleted); refusal -> gh pr close. When the user confirms the
  issue's round is DONE, relay gh issue close <n> and run spawn.py clean
  — merge, issue close, branch deletion, workspace cleanup end an
  issue's life. Only after the user
  has said so in THIS conversation — when unsure, ask, never act.
```

Proposed replacement (pointer-only — drops the restated rule prose, keeps only what a fresh orchestrator session needs to know it must go read the authoritative source before acting):

```
- Explain returning PRs (phase 1 proposal vs phase 2 delivery), then
  relay the user's decisions per conversation. The exact relay actions
  (feedback/approval/acceptance/refusal comment forms, issue-close, and
  spawn.py clean) are specified in /orchestrate:run step 6 (contract v3
  s19) — read it there before relaying; do not improvise or restate the
  wording here. Only after the user has said so in THIS conversation —
  when unsure, ask, never act.
```

This satisfies 1a (the approval string is no longer restated at all here, so there is nothing to cite-and-drift) and 1b (no rule prose remains — just a pointer to run.md's step 6 plus the section number).

### Site 2 — `orchestrate/commands/run.md:185-187` (1a citation only, prose stays — this is the authoritative detail site, not an informing hook)

Current:

```
   - 제안 승인 → 기본(1계정)에서는 자기 PR 에 리뷰 Approve 가 불가하므로,
     정확히 이 문자열의 코멘트를 단다: `gh pr comment <n> --body "APPROVE issue-<n>/<역할>"`
     (approval-gate 가 이 정확한 문자열만 승인으로 인정한다. 에이전트 계정을
     분리한 하드닝 구성에서는 `gh pr review <n> --approve` 도 된다)
```

Proposed (add citation only, no wording removed since this is where directive.sh's pointer sends readers):

```
   - 제안 승인 → 기본(1계정)에서는 자기 PR 에 리뷰 Approve 가 불가하므로,
     정확히 이 문자열의 코멘트를 단다: `gh pr comment <n> --body "APPROVE issue-<n>/<역할>"`
     (approval-gate 가 이 정확한 문자열만 승인으로 인정한다. 에이전트 계정을
     분리한 하드닝 구성에서는 `gh pr review <n> --approve` 도 된다) (contract v3 s19)
```

`run.md:11`'s existing generic `(contract v3)` cite is left as-is (out of scope — it is a section-level framing statement, not a rule restatement; sharpening it to a section number is not part of this proposal's frozen write set beyond the two named sites).

## Out of scope

- Editing any `core/` file (e.g. `core/hooks/directive.sh` in the `tokenmaxxxer-core` repo) is out of scope for this proposal — that repo is not part of muster's write set and is not touched.
- Filing a core-repo issue for `core/hooks/directive.sh`'s analogous drift risk is out of scope for this proposal; per issue #80's body, phase 1 only needs to note that it should happen separately if the reduction is judged necessary there too (it is — `core/hooks/directive.sh:82-93` is exactly the file that caused the core#18 incident per reflect.md §1). The user/orchestrator should file that as its own core-repo issue outside this flow.
- Consolidating `run.md`'s other accreted obligations (reflect.md §2) — separate backlog item, not this issue.
- Sharpening `run.md:11`'s generic `(contract v3)` cite to a section number, or mirroring contract v3 text locally under `docs/specs/` (reflect.md §1c) — separate, undecided backlog items.

## How we'll know it worked

- `grep -n 'APPROVE issue-<n>' orchestrate/hooks/directive.sh` no longer matches (the string is no longer restated there).
- `orchestrate/hooks/directive.sh`'s relay bullet contains `(contract v3 s19)` and points to `/orchestrate:run` step 6, with no restated approval/acceptance/refusal command forms.
- `orchestrate/commands/run.md:185-187` (or its shifted line numbers after edit) contains `(contract v3 s19)` immediately after the existing approval-comment instruction, with the instruction text otherwise unchanged.
- No `core/` path in this repo is touched (`git diff --stat` shows only the two named files).
- A human reviewer confirms via `gh pr diff` that no approval-rule prose exists in muster outside `run.md`'s step 6 and the contract itself, per issue #80's acceptance criteria.
