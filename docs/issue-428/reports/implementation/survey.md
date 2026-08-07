# Survey — issue-428

## Scope surveyed

`spawn.py` (single-file orchestrator, 3548 lines): workspace reuse
(`issue_workspace`), branch checkout (`checkout_issue_branch`), fetch
(`_fetch_or_halt`), push/PR relay (`ensure_pushed`), and outcome recording
(`ledger_write` + the `outcome ==` print block around spawn.py:3450-3541).

## Fault 1 — mechanism, reproduced

`issue_workspace()` (spawn.py:2798) reuses the existing work directory on
respawn ("재스폰이면 기존 작업 디렉토리를 fetch 로 재사용한다") and only
calls `_fetch_or_halt`, i.e. plain `git fetch -q origin` (spawn.py:2789),
never `git branch -d`/`-D` on anything.

`checkout_issue_branch()` (spawn.py:2907) then does, in order:
1. if a **local** branch `issue-<n>/<role>` exists → `git checkout` it
   (spawn.py:2918-2919) — no check of whether it is already fully merged.
2. elif `origin/<branch>` exists → track it.
3. else → branch fresh from base.

A round that ends with `gh pr merge --delete-branch` removes the **remote**
branch only. The reused workspace's **local** branch is never touched by
that merge — it is a separate ref that git does not delete as a side
effect of anything happening on GitHub. On respawn, branch (1) fires: the
stale local branch is checked out as-is, and because its content is now
fully contained in main (it was merged), it has zero commits ahead of
base. If the new session makes no further commits (or the push step also
finds nothing to push), `ensure_pushed`'s `gh pr create --head <branch>`
is called against a branch with no diff from base — which is exactly
GitHub's own rejection text observed in the incident: "No commits between
main and issue-<n>/implementation".

Reproduced directly (not reasoned about) with real git, no spawn.py
mocking — clone → branch → commit → push → merge into base → delete
remote branch → re-fetch the **same, reused** clone:

```
$ git fetch -q origin              # respawn's only network call, no --prune
$ git branch -a
  issue-999/implementation
* trunk
  remotes/origin/trunk
$ git rev-parse --verify -q issue-999/implementation
1b8deb72ebda70d4777e24defd37d21fd4832c45
YES-STALE-LOCAL-BRANCH
$ git rev-list --count trunk..issue-999/implementation
0
```

The local branch survives `--delete-branch` untouched, and its ahead-count
against base is 0 — the exact precondition the incident's error text
requires. `origin/issue-999/implementation` was in fact auto-pruned by
this git version's plain fetch (a modern-git side effect, not something
`checkout_issue_branch` relies on) — so the culprit is **not** a stale
remote-tracking ref, it is the stale **local** branch and
`checkout_issue_branch`'s unconditional trust of "local branch exists" as
"resume this work" without checking it is already fully absorbed into
base.

This settles the incident text's own hedge ("narrows it but does not
settle it"): the branch that "exists ... with no commits ahead of main"
is the checked-out **local** branch, reused verbatim from a previous
finished round, not a surviving remote ref.

## Fault 2 — where outcome recording stops

`ledger_write()` (spawn.py:2177) appends to `runs/ledger.jsonl`, which is
gitignored ("측정 데이터는 소스가 아니다") — local-host-only, per-machine
data. The `outcome == "refused"` / `outcome == "silent-failure"` branches
(spawn.py:3512-3519) only `print(..., file=sys.stderr)` — visible solely
to whoever is tailing that specific session's log at that moment. Nothing
else consumes either the ledger line or the stderr print. There is no
code path from a bad outcome to anything durable and visible without a
human proactively choosing to go look (a log tail, or `runs/ledger.jsonl`
on that exact host).

Per #424's precedent (`record-fields-gate`, `closes-gate`, `board-gate`):
those don't advise, they mechanically block. The equivalent here is not a
CI gate (nothing merges when a session merely reports a bad outcome —
there is nothing to block), but a **push**, not a **pull**: the outcome
has to travel to a surface the operator already looks at without being
told to look. GitHub issues are that surface in this project (`board` =
what's on GitHub, per spawn.py's own comments elsewhere and
role-handoff contract v3). No existing code posts anything to the issue
on a bad outcome — `ensure_pushed()`'s own PR-create failure
(`pr-create-failed`) already carries the exact rejection reason in
`push_result["reason"]`, and that reason currently only reaches
`ledger_write` and stderr.

## Fault 3 (scope item 3) — commit recoverability

`issue_workspace()` never deletes a workspace itself, so a session's local
commits already survive its own failure to open a PR — they sit in the
reused work directory (`~/.tokenmaxxxer/work/<repo>-issue-<n>-<role>`)
until the next respawn's `checkout_issue_branch` (fault 1's own reuse
path) either continues them or — per fault 1 above — silently discards
them by checking out a stale, already-merged branch instead. So faults 1
and 3 are coupled: fixing fault 1's reuse check is also what keeps
unpushed commits from a failed round reachable on the next respawn,
rather than being masked by a stale merged branch tip.

## Write set (frozen for the proposal)

- `spawn.py` — `_fetch_or_halt` (prune), `checkout_issue_branch` (stale
  local branch detection), the outcome block ~3512-3519 (issue-comment
  wiring for `silent-failure`/`refused`).
- `test_spawn_fault_428.py` (new) — reproduces fault 1 against the real
  `checkout_issue_branch`/`issue_workspace` functions (not the shell
  reproduction above, which was scouting evidence) and exercises the
  outcome-surfacing wiring with a stubbed `gh`.
- `docs/issue-428/proposals/*.md`, `docs/issue-428/reports/implementation.md`,
  `docs/issue-428/reports/implementation/survey.md` — this survey and its
  proposal/record.

## Alternatives considered while surveying

- **Prune-only fix** (just add `--prune` to fetch): rejected as
  insufficient — the reproduction above shows the actual stale ref is the
  **local** branch, which `--prune` (a remote-tracking-ref operation)
  never touches. It would leave the reported failure fully reproducible.
- **Always re-clone on respawn** (drop workspace reuse entirely): rejected
  — `issue_workspace`'s own comment records why reuse exists (an
  in-progress uncommitted session's work must survive a respawn); dropping
  it would resurface the exact loss scope item 3 asks to avoid, for the
  much more common case of a respawn that isn't post-merge at all.
- **Advisory-only outcome surfacing** (a runbook line telling the
  orchestrator to check the ledger after every spawn): rejected per the
  issue's own text and #424's precedent — a rule the orchestrator should
  follow is exactly the shape that already failed five times.
