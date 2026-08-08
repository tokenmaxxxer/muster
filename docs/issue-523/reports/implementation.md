---
code_under_review:
  - roles/technical-writing.json
  - roles/devrel.json
loop_state: landed
---

# Implementation record — issue-523

## What was done

Differentiated `roles/technical-writing.json` and `roles/devrel.json`
`write_scope` per the approved proposal
(`docs/issue-523/proposals/2026-08-09-technical-writing-devrel-write-scope-split.md`):

- `roles/technical-writing.json`: `write_scope` changed from `["docs/**"]`
  to `["docs/guides/**", "docs/issue-<n>/guides/**"]`.
- `roles/devrel.json`: `write_scope` changed from `["docs/**"]` to
  `["docs/devrel/**", "docs/issue-<n>/devrel/**"]`.

The two sets are disjoint by construction and both remain non-empty.

## Why

Basis: `docs/issue-523/proposals/2026-08-09-technical-writing-devrel-write-scope-split.md`
(approved via issue comment `APPROVE issue-523/implementation` by
JiwonJung94, an account listed in `docs/specs/approvers.md`; single-account
mode, since the phase-1 PR and this branch share the same author account).
Every other docs-writing role already narrows to a role-specific subtree
(`architecture`, `incident-response`, `knowledge-management`);
technical-writing and devrel were the only two still claiming the full
`docs/**` tree, which is the actual root cause of the collision the issue
names.

## Acceptance clauses vs commits

- check 1 (`python3 -c "...assert set(a)!=set(b) and a and b"`): PASSES —
  confirmed by running it against the committed `roles/*.json` files after
  this change (exit 0).
- check 2 (`bash scripts/check-write-set-conflicts.sh`): the script errors
  (`pairs_file: 바인딩 해제한 변수` / unbound variable) independent of this
  change and, per the after-proposal hunt finding already on record
  (`docs/reports/2026-08-09-hunt-issue-523-technical-writing-devrel-write-scope-split.md`),
  never reads `roles/*.json` or `write_scope` at all — it compares proposal
  `files:` frontmatter across issues with open PRs, an unrelated mechanism.
  It cannot detect or confirm the technical-writing/devrel write_scope
  split either way. Fixing that script is outside this issue's frozen
  write set (`roles/technical-writing.json`, `roles/devrel.json` only) and
  is not attempted here; the gap was already flagged pre-build by the
  after-proposal hunt and stands as known follow-up work, not a regression
  introduced by this change.
- provenance: executed-unit — both `roles/*.json` edits and check 1 were
  run directly in this session (see commands above), not delegated.

## Rationale for deviations

The proposal's "How you'll know it worked" names `bash
scripts/check-write-set-conflicts.sh` as acceptance check 2. That script
errors (`pairs_file: 바인딩 해제한 변수`) and, per the after-proposal hunt
finding already on record, never inspects `roles/*.json`/`write_scope` at
all — it is the wrong tool for this collision, pre-existing and unrelated
to this change. `roles/technical-writing.json` and `roles/devrel.json` are
the only files in the frozen write set; fixing or rewiring
`check-write-set-conflicts.sh` is outside it. No alternative script swap
was made — the deviation is reporting check 2 as unable to confirm or deny
the split, rather than silently claiming it passed.

## What did not work

None.

## Open findings

- The pre-existing after-proposal hunt finding (check 2's script being
  unwired from `roles/*.json`) remains open as a follow-up outside this
  issue's frozen write set; no resolution attempted here per
  scope-exceeded rule.
- Before-landing hunt (stance 1: bypass the gate just touched) found:
  `gates/gates.py`'s `role_scope()`/`_always_writable()` uses
  `fnmatch.fnmatch`, whose `*` also matches `/`, so the always-writable
  `proposals/**` and `reports/<role>/**` carve-outs let any role — not
  just technical-writing/devrel — write into a path with an extra nested
  directory segment (e.g. the other role's declared directory name)
  inserted before `proposals/`, defeating this diff's disjoint
  `write_scope` split (and every other role's write_scope) at the
  enforcement layer. Full reproduction: `docs/reports/2026-08-09-hunt-issue-523-technical-writing-devrel-write-scope-split.md`
  (`before-landing — stance 1`). `gates/gates.py` is outside this issue's
  frozen write set (`roles/technical-writing.json`, `roles/devrel.json`
  only) — not fixed here per scope-exceeded rule; flagged for a follow-up
  issue.
closed_checks:
  - check: "python3 -c \"...assert set(a)!=set(b) and a and b\""
    code_sha: f8e9741c79ec1a7165fab64eb2f4ca980a134094
    result: PASS (exit 0)
