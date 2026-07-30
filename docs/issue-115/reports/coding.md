---
loop_state: landed
upstream:
  - path: docs/issue-115/proposals/coding.md
    sha: 199f61b
---

# Issue #115 — Phase 2 record (coding)

code_under_review: spawn.py, wakes.py, docs/specs/wake-routing.md,
docs/specs/loop-state-vocab.md, test_approve_scope.py (this branch,
phase-2 commit)

## Why

Humans were hand-editing `loop_state: scope-approved` into front records
because the interface for expressing scope approval was never built —
orchestrators filled the gap (observed on controller #89/#91), violating
the records-are-written-by-roles principle and producing `scope-approved`
values with no declared writer. Per the approved proposal
(`docs/issue-115/proposals/coding.md`, PR #117 merged): move the human's
part to a standard s19 exact-string comment, and give `spawn.py` a command
that verifies that comment and writes the promotion commit — no hand-edit
by human or orchestrator, ever.

## What was done

1. `spawn.py` — new `approve-scope --issue <n> [-C <repo>]` subcommand
   (`approve_scope`, dispatched in `main()` next to the existing `approve`
   stub). It resolves the subject's front record via `wakes._front` (local
   import inside the function, the same pattern the `wake` dispatch already
   uses to sidestep the `spawn`↔`wakes` circular import), reads
   `docs/specs/approvers.md` (`_approvers`), fetches issue-level comments
   for the subject issue and — if a PR whose head branch is
   `issue-<n>/<front-role>` exists — that PR's comments too
   (`_issue_comments`, `_pr_for_branch`, `_repo_slug`, all `gh` shell-outs),
   and accepts only an exact-string `APPROVE issue-<n>/scope` body from a
   login in the allowlist. No match: exits non-zero naming what's missing
   (no matching comment vs. commenter not in `approvers.md`). Match: rewrites
   the front record's `loop_state:` line to `scope-approved` in place and
   writes the commit itself (`git add` + `git commit`, message names the
   approving login) — no push; pushing `main` is left to the human/
   orchestrator, matching this repo's general no-auto-push posture and
   because the issue asked only for the commit to be tool-written. Idempotent
   on an already-`scope-approved` record (returns 0, no second commit); a
   record not currently `scope-proposed` is refused with the state named.
2. `wakes.py:47-56` (`HUMAN_ONLY["사전 승인 게이트"]`) reworded: the
   decision (a human's `APPROVE issue-<n>/scope` comment) stays human-only;
   the mechanics (allowlist check + commit) are named as `spawn.py
   approve-scope`'s job.
3. `docs/specs/wake-routing.md`'s "First-build approval guard" section
   reworded the same way, naming `spawn.py approve-scope --issue <n>`
   explicitly and stating no hand-edit is ever required or accepted.
4. `docs/specs/loop-state-vocab.md`'s `## Human-only allowlist` entry for
   `scope-approved` extended to name `spawn.py approve-scope` as the sole
   writer and state it is a tool-written value, not a role's record output —
   the exemption stays scoped to this one name and does not weaken
   `record_enums`'s write-time check on role-produced fields. (Survey found
   `roles/coding.json`'s `record_fields.loop_state` enum already lists
   `scope-approved` since #103/#109 — the enum gap itself was already
   closed; requirement 3 here was naming the writer, not opening a new
   enum slot.)
5. `test_approve_scope.py` (repo root, matching the existing `test_*.py`
   convention — no `test/` subdir observed anywhere in this repo) — 5
   `unittest` cases, GitHub calls monkeypatched (no network): matching
   approver writes `scope-approved` and commits; non-approver login
   rejected; non-matching comment text rejected; already-approved is
   idempotent; wrong starting `loop_state` rejected.

## Verification run (this session, once)

- `python3 test_approve_scope.py -v` — 5/5 pass.
- `python3 test_vocab_coherence.py` — 3/3 pass (confirms the reworded
  `scope-approved` allowlist entry still parses).
- `python3 test_spawn.py` — 83/83 pass (no regression on the existing
  `spawn.py` surface).
- `python3 test_gates.py` — one pre-existing failure
  (`t_repo_local_claude_config_stops_the_spawn`, `OSError: Read-only file
  system: .../trusted-repo-config.json`), unrelated to this change — it's a
  sandbox filesystem-permission artifact, out of this write set.

## closed_checks

- check: approve-scope comment→allowlist→commit path (5 cases: matching
  approver, non-approver, non-matching text, idempotent re-run, wrong
  starting state) — code_sha: this branch's phase-2 commit; verified by
  `test_approve_scope.py`.

## What did not work

- Nothing needed reverting. One design tradeoff worth flagging: `gh api
  .../comments` is called without `--paginate` — multi-page concatenation
  under `--paginate` produces an invalid single JSON document without
  further `-q '.[]'` handling, and approval threads are short, so a single
  page is the honest choice rather than adding untested pagination logic.

## Hunt

Warrant-hunter dispatched at phase-2 completion (stance: silent-failure —
does `approve-scope` ever report success without having actually written
the promotion, or refuse silently with exit 0?).

## Open findings

None open. No blocking finding has been addressed to this record.
