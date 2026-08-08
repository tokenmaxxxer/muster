---
code_under_review: HEAD
loop_state: phase-2-complete
---

# issue-457 phase 2 — implementation record

Subject: issue-457. Approved scope (operator, 2026-08-08): port the 16
category-2 gate checks per the architecture proposal
`docs/issue-457/proposals/2026-08-08-gate-porting-order.md`, 5 groups in
order; justify-only rows go into a shipped unenforced-clause list per the
parity-manifest Acceptance.

## What was done

- Group A+B (port), one hook, `on-the-record/hooks/record-claim-guard.sh`
  (`PreToolUse`, `Write|Edit|MultiEdit` on `docs/issue-*/reports/**`):
  write-time mirrors of `gates.py`'s record-claim-integrity checks —
  #310 (`unverifiable:` needs a reason), #331 (`checked:`/`result:
  unverifiable` needs a reason), #333 (bare "N of M"/"N items" counts need
  a code fence or `derived: ...`), #330 (backtick-quoted relative path
  references must resolve on disk). #332 is the umbrella generator issue;
  satisfied by porting its three named children plus #331.
- Group C (port), `on-the-record/hooks/role-test-claim-guard.sh` (`Stop`,
  role sessions only): #334 mirror (pasted pytest output with SKIPPED
  lines but a clean-pass claim in the prose with no skip mention), #435
  mirror (a hand-typed pass count in the reply that doesn't match the
  pasted pytest summary's actual count).
- Group D+E+#396 (justify), `on-the-record/unenforced-clauses.md`,
  shipped under `on-the-record/` so a consumer reads it zero-install:
  justification rows for #312, #369, #383, #388, #325, #407 (GitHub-board
  state unreachable from a local session), #319, #322 (non-blocking
  advisory tools, not gates), and #396 (no implementation exists anywhere
  to port — deferred, flagged for whichever role opens its own follow-up).
- Wired both new hooks into `on-the-record/hooks/hooks.json`; added both
  as rows to `docs/specs/enforcement-boundary.md` (verdict `contract`) so
  `gates/test_boundary.py`'s existing derivation-completeness check keeps
  passing; regenerated `docs/specs/reconciled-index.md` after the
  `run.md` edit (spec_index.py --update).
- Added a reference line in `on-the-record/commands/run.md` pointing the
  orchestrator at `${CLAUDE_PLUGIN_ROOT}/unenforced-clauses.md`.
- Added the parity-manifest test `t_gate_porting_rows_are_ported_or_
  justified` to `gates/test_boundary.py`: for each of the 16 issue
  numbers, asserts either an `#<n>` mention inside `on-the-record/hooks/
  *.sh` or a justification row in `on-the-record/unenforced-clauses.md`.

## Why

Approved architecture proposal names 5 groups, in order, and requires every
one of the 16 audited rows to end as ported or justified, per the #444
audit's category-2 list and #452's shipped-unenforced-clause shape.

## Open findings

None.

## resolved_findings

- warrant-hunt finding (docs/reports/2026-08-08-hunt-gate-porting-order.md,
  before-landing, stance 0): `record-claim-guard.sh`'s #333 bare-count
  noun allowlist (`items?|works?|checks?|cases?`) omitted "tests", so a
  claim phrased "38 tests passing" evaded the check while "38 items
  passing" was caught. Fixed by adding `tests?` to the noun list; added
  `t_bare_test_count_claim_is_denied` to
  `on-the-record/hooks/test_record_claim_guard.py`, code_under_review:
  HEAD.

## Next steps

None for this delivery. Follow-ups the proposal itself named as belonging
to other roles/issues: #396's own design (whichever role opens that
follow-up), and Group D's "local-subset worth mirroring" question the
proposal flagged for implementation to confirm against the operator — not
pursued here since the proposal explicitly left that decision open rather
than approved, and no such subset was requested for this delivery.

## Open finding resolution path

N/A — no open findings.

## What did not work

- First cut of `role-test-claim-guard.sh`'s skip-vs-clean-pass check
  scanned the whole message for the word "skip", which false-negatived
  every case because the pasted pytest output itself always contains the
  literal string "SKIPPED" — the check never fired. Fixed by stripping
  fenced code blocks before checking the prose for a skip acknowledgment.
- Same first cut's hand-typed-count regex used `\b...\b` word boundaries
  around Korean text; Python's `\b` treats Hangul as a word character, so
  `통과했습니다` (no boundary between `통과` and `했`) never matched.
  Dropped the trailing `\b`.
- `record-claim-guard.sh`'s derived-count regex used a hand-invented
  `_DERIVED_TAG`/`_COUNT_NOUN` shape that didn't match `gates.py`'s actual
  regexes (`_COUNT_NOUN` word list, `` `derived:\s*\S.*?` `` requiring a
  backtick-quoted tag) — a first test (`25 of 107 items ... (derived:
  ...)`) failed because my invented format didn't match either the ported
  code's own pattern or the fix I'd made. Reread `gates/gates.py:409-441`
  and copied its exact regexes instead of re-deriving them from memory.

## closed_checks

- record-claim-guard.sh check: `on-the-record/hooks/test_record_claim_guard.py` — 11 of 11 passed (`python3 -m pytest on-the-record/hooks/test_record_claim_guard.py -q`), code_under_review: HEAD.
- role-test-claim-guard.sh check: `on-the-record/hooks/test_role_test_claim_guard.py` — 7 of 7 passed (`python3 -m pytest on-the-record/hooks/test_role_test_claim_guard.py -q`), code_under_review: HEAD.
- parity-manifest check: `gates/test_boundary.py` — 4 of 4 passed (`python3 -m pytest gates/test_boundary.py -q`), code_under_review: HEAD.
- full suite check: `python3 -m pytest -q` — 561 of 562 passed; the one failure (`test_gates.py::t_rulebook_version_is_recorded`) is a pre-existing dirty-working-tree assertion unrelated to this delivery's content (asserts the rulebook checkout is clean; fails whenever there are uncommitted changes in this repo, by design) — resolves once this work is committed.
