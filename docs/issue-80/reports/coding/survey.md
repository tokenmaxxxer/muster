# Issue #80 — Current-State Survey (phase 1)

Scope: follow-up to `docs/issue-76/reports/reflect.md`, items 1a and 1b (§1a, §1b, backlog item 1).

## 1. Sites requiring citations (1a)

### 1.1 `orchestrate/hooks/directive.sh:73`

Current text (lines 71-79 of the file, the relevant sentence at line 73):

```
71	- Explain returning PRs (phase 1 proposal vs phase 2 delivery), then
72	  relay the user's decisions per conversation: feedback -> gh pr comment;
73	  approval -> a comment that is EXACTLY "APPROVE issue-<n>/<role>";
74	  acceptance -> gh pr merge --delete-branch (a merged role branch is
75	  always deleted); refusal -> gh pr close. When the user confirms the
```

Line 73 restates the exact approval-comment string (`APPROVE issue-<n>/<role>`) with **no contract pointer at all** — not even a bare `(contract v3 sNN)` cite, unlike the enforcing hooks.

### 1.2 `orchestrate/commands/run.md:185-187`

Current text:

```
183	   - 수정 요구 → `gh pr comment` 로 해당 PR 에 남긴다
184	   - 제안 승인 → 기본(1계정)에서는 자기 PR 에 리뷰 Approve 가 불가하므로,
185	     정확히 이 문자열의 코멘트를 단다: `gh pr comment <n> --body "APPROVE issue-<n>/<역할>"`
186	     (approval-gate 가 이 정확한 문자열만 승인으로 인정한다. 에이전트 계정을
187	     분리한 하드닝 구성에서는 `gh pr review <n> --approve` 도 된다)
```

Lines 185-187 restate the exact same approval string plus a description of `approval-gate`'s matching behavior, with no `(contract v3 sNN)` cite. `run.md:11` carries only a generic, section-less cite:

```
11	당신은 조율 세션이다 (contract v3). 역할들은 대상 레포의 이슈에서 깨어나
```

`(contract v3)` with no section number does not point a future renumber-check at anything specific.

## 2. Citation pattern already in use (safe pattern to match)

`core/hooks/board-gate.sh` (in the sibling `tokenmaxxxer-core` repo, invoked here as a plugin hook) already uses the target pattern — confirmed live, by triggering it in this session:

```
board-gate: writing docs/issue-76/ requires branch issue-76/coding (current: issue-80/coding).
Every role output reaches main only through a PR the human merges — never a direct write
from another branch. (contract v3 s10)
```

Pattern: `(contract v3 sNN)` appended after a one-line restatement of the rule's *consequence*, not the rule's full prose. `core/hooks/approval-gate.sh` is reported (per reflect.md §1a) to use the same pattern; it was not independently re-read in this session because it lives in a separate repo (`/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/`), outside this sandbox's read/write scope, and outside muster's own `core/` path (there is no `core/` directory in this repo at all — confirmed: `ls core` → not found).

## 3. Section number for the approval-string rule

`docs/issue-76/reports/reflect.md` (merged, `main`) directly ties the single-account APPROVE-comment rule to **contract v3 s19**:

> "Status: final. Phase 2 opened via single-account APPROVE on PR #79 (contract v3 s19)."

and reflect.md §1b independently confirms `core/hooks/directive.sh:82-93` carried a `(contract v3 s19)` cite next to the same rule before it drifted (the core#18 incident). This is the section both 1a sites (directive.sh:73 and run.md:185-187) should cite: **`contract v3 s19`**.

No local copy of the contract v3 text exists under `docs/specs/` in this repo (only `approvers.md` — confirmed by `ls docs/specs/`); reflect.md §1c already flagged this gap as a separate, undecided item, out of scope here.

## 4. Informing-hook prose to reduce to a pointer (1b)

`orchestrate/hooks/directive.sh` lines 71-84 (the bullet spanning the approval/acceptance/refusal relay rules, and the following "you never write board records" bullet) is the informing-hook prose. Per issue #80's body, item 1b chooses **pointer-only reduction** over build-time generation, specifically for muster's `orchestrate/hooks/directive.sh` (the analogue of the core#18-incident file `core/hooks/directive.sh`). The rule text to reduce is lines 71-79 (the phase-1/phase-2 relay bullet containing the approval string at line 73).

`core/hooks/directive.sh` is a separate file in a separate repo (`tokenmaxxxer-core`), not present under this repo's `core/` path (no such path exists here) and explicitly out of scope for direct editing from muster, per the issue body. If it needs the same reduction, that is a **core-repo issue to be filed separately** — not addressed by this proposal.

## 5. Section number for the "informing hook" pointer target

The rule being pointed to is the same relay procedure at `contract v3 s19` (the approval-comment contract). No separate "informing hook" section number was found — s19 is the substantive rule; the pointer in directive.sh should reference `run.md`'s already-detailed step 6 (which cites its own detail inline) plus `(contract v3 s19)`, rather than duplicate wording.
