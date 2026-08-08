---
name: survey
description: >
  Current-state survey for issue #511 — what risk_report.py, the approval
  path, and the enforcement-boundary doctrine already provide, and what
  requirements 1-8 actually need added.
---

# Current-state survey — issue #511

## Follow-up chain
Issue #319 shipped `gates/risk_report.py` (binary low/high classifier,
`test_risk_report.py`) plus `on-the-record/hooks/stop-gate.sh` and
`decision-queue-stopgate.sh` — all non-blocking: they change what a human
sees, never what a human must do. Issue #319's own record deferred the
structural direction (multi-axis classification, standing decisions) to a
"contract v3 s19 amendment" that #511 states was never filed. This survey
confirms that: no file in this repo defines section-numbered "contract v3"
text (`grep -rn "s19"` outside prose references and one commented sentinel
string in `spawn.py`/`directive.sh` returns nothing) — the contract lives
as role-directive text injected at session start by the plugin's hooks,
not as a versioned document in this repo. There is no existing s19 body to
amend; the amendment has to introduce the section, not patch one.

## `gates/risk_report.py` today
- `classify(paths, added_lines, removed_lines) -> "low"|"high"`: single
  axis. `high` iff write-set is empty (fail-closed), any path is
  `gates.is_protected`, or total changed lines exceed `SIZE_THRESHOLD = 30`.
- `scan_open_proposals(root)` walks `docs/proposals/*.md` and
  `docs/issue-*/proposals/*.md` with `status: proposed`, parses each
  proposal's YAML-ish `files:` block, and diff-stats each listed file
  against `gates.BASE` (`origin/main`, overridable via `GATE_BASE`).
  **This already takes `root: Path` as a parameter and never assumes it is
  running inside this repo** — it is already target-repo-portable in
  shape, which matters directly for requirement 7.
- `report()` renders a two-column-risk Markdown table, high-risk rows
  first. Purely advisory: nothing reads its output to block anything.
- Docstring is explicit that `classify()` returning `"low"` never
  substitutes for the GitHub approval act — the file already states the
  scope-limit principle requirement 6 asks for; #511 needs it enforced,
  not re-asserted.

## Approval path this must wire into
Phase 2 opens on exactly two paths (role-handoff contract, s19 area per
the injected directive): a PR review Approve from a distinct
`docs/specs/approvers.md` account, or — single-account mode — an issue
comment whose entire body is the literal string
`APPROVE issue-<n>/<role>` from a listed account (`spawn.py` around line
1141 implements the exact-string check). `docs/specs/approvers.md`
currently lists two accounts. Nothing today distinguishes "any approver,
any time" from "this proposal's impact requires an approver who isn't the
proposal's own reviewer-of-convenience" — there is no batching concept and
no impact-gated approval-route split at all; requirement 5 (block
batch-approval for high-impact) has no hook to attach to yet.

## Target-repo enforcement pattern already established
`on-the-record/hooks/decision-queue-stopgate.sh`'s `_checkout_resolve()`
is the repo's working pattern for "run inside an arbitrary target repo,
locate the on-the-record checkout separately from the working tree":
checks `$TOKENMAXXXER_CHECKOUT`, then walks parent directories from the
hook's own path for `spawn.py`, then falls back to known marketplace/
plugin install locations, cloning as a last resort. `docs/specs/
enforcement-boundary.md` records, per mechanism, whether it reaches a
consumer session zero-install (`contract`) or is repo-local to this repo
only. `risk_report.py` is currently classified `n/a (infrastructure)` in
that table — "non-blocking classifier feeding gates.py's review surface,
not itself a clause." Turning it blocking (requirement 5) moves it into
`contract` territory and this classification/table need updating in the
same delivery that ships the behavior, per `gates/test_boundary.py`'s
completeness check (a new/changed blocking mechanism with no boundary row
fails the build).

## Structural axes requirement 1 asks for vs. what exists
None of blast radius (DEPENDS-ON edges / write_scope overlap / READing
role count), reversibility (path-class ordering), or propagation
(rulebook/role fan-out count) exist anywhere in `gates/` today —
`risk_report.py`'s only structural signal is protected-path membership
and line count (requirement 1's "existing signals" bucket). DEPENDS-ON
edges and write_scope are referenced by `gates.py`/`ci.py` for a different
purpose (write-scope conflict detection between concurrent proposals, see
`docs/specs/parallel-conflict-methodology.md`) — that machinery computes
overlap already and is the natural source for the blast-radius axis
rather than a new parser.

## Gap this proposal must close
1. Axis 1 (blast radius): reuse `parallel-conflict-methodology`'s
   write_scope overlap computation instead of re-deriving it.
2. Axis 2 (reversibility): new — a path-class ordering table, structurally
   simple (checked against the existing `PROTECTED_DIRS`/
   `PROTECTED_ROOT_DIRS`/`PROTECTED_ROOT_FILES` constants in `gates.py`,
   which already encode part of this ordering implicitly).
3. Axis 3 (propagation): new — count of distinct rulebooks/roles a
   changed path is documented as governing; no existing computation to
   reuse.
4. Axis 4 (existing signals): already computed by `risk_report.py`
   verbatim (protected paths, changed-line count) — carry forward as-is.
5. Dominant-axis composition: new; today's single-axis classifier has
   nothing to dominate over.
6. Standing decisions / ITIL standard change: wholly new; no pre-approved
   change-type registry exists anywhere in the repo.
7. Blocking wiring into approval flow: requires a new zero-install
   `PreToolUse` hook (matching the `contract-guard.sh`/`pr-preflight.sh`
   shape already used for the two other `gh pr` interception points) —
   `risk_report.py` alone cannot block anything; it is a library today,
   called by nothing at merge/approval time.
8. Target-repo portability (requirement 7): the classifier itself already
   takes `root: Path`; the new blocking hook needs the same
   `_checkout_resolve()`-style split between "where on-the-record's own
   code lives" and "which target repo it is classifying" that
   `decision-queue-stopgate.sh` already demonstrates.
