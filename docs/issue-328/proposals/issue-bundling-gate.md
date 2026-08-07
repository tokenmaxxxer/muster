---
status: proposed
files:
  - gates/issue_bundling.py
  - test_issue_bundling.py
  - .github/workflows/issue-bundling-gate.yml
  - docs/issue-328/reports/implementation.md
---

## Request

On-the-record (the LLM that files issues) repeatedly bundles several
unrelated problems into one issue, which blocks parallel work, blocks
partial acceptance, and forces one role to hold context for unrelated
mechanisms. Per issue #310, prose promising not to bundle does not
discharge this — the fix must be an executable artifact that fails when
bundling regresses.

## Constraints

- Issue content is authored as prose by an LLM (`on-the-record/commands/run.md`);
  there is no code call site that constructs an issue title/body to patch
  directly (confirmed by survey — `spawn.py` only comments on existing
  issues). The check must therefore be a **post-hoc mechanical gate**
  against title/body text, not a change to how issues get written.
- Must follow the existing gate shape (`gates/pr_reference.py`): a pure
  `check_*(text) -> list[str]` function, network-free and unit-testable,
  with a thin CLI wrapper that fetches live text via `gh issue view`.
- Must fail closed on uncertainty per `gates/gates.py`'s stated
  philosophy ("불확실하면 막는다") — an issue the checker cannot classify
  is not silently passed.
- Per #310: any of the issue's three named tells that this pass cannot
  mechanically check must be stated as unchecked in the record, not
  silently dropped or implied as covered.
- Per #330: this gate only judges an issue's own title/body text; it does
  not and cannot verify that a *role* boundary was respected (issues
  don't declare structured role-assignment data today), and it does not
  retroactively re-check issues already filed before the gate existed.

## Rationale

**Chosen: a CI gate on `issues: opened` that checks title conjunctions +
acceptance-item path spread, considered against two rejected alternatives.**

Considered patching `on-the-record/commands/run.md`'s issue-filing
instructions with a stronger prose rule ("never bundle unrelated
problems"). Rejected: this is exactly the class of fix issue #310 rules
out — a promise about future LLM behavior is not an executable artifact
and cannot fail on regression; the operator's own filed complaint is that
prose instructions already exist informally and are not holding.

Considered a full semantic check (an LLM call that reads the issue and
judges "are these unrelated?") run as a CI step. Rejected: it reintroduces
exactly the non-determinism `gates/gates.py`'s own docstring rejects
("리뷰 에이전트의 판단력에 기대지 않고 막을 수 있는 것만 여기서 막는다") —
an LLM-judged gate can be inconsistent run-to-run on the same input, is
not reproducible in a unit test without mocking the model, and costs a
model call on every issue filed. A regex/structural check on title
conjunctions and acceptance-item path spread is deterministic, testable
with literal strings (as `test_gates.py` already does for
`pr_reference.check_body`), and directly matches two of the three tells
the issue itself names as mechanical.

## What will be done

- `gates/issue_bundling.py`: new module, modeled on `gates/pr_reference.py`.
  - `check_title(title: str) -> list[str]`: flags a coordinating
    conjunction joining two distinct clauses outside of any quoted or
    backtick span — `" and "` (English) and `" 및 "` / `" 그리고 "`
    (Korean), anchored so a normal descriptive title ("check permissions
    and validate input" as a single mechanism) is not the target; the
    check is conjunction-presence, matching the issue's own stated tell
    literally, not an attempt at deeper semantic parsing.
  - `check_body(body: str) -> list[str]`: parses an `## Acceptance`
    section (same section-heading convention already used across this
    repo's own issues, including #328 itself), collects inline
    backtick-quoted path-shaped tokens from each top-level bullet under
    it, and flags when two or more bullets reference path roots with no
    common top-level directory (e.g. `spawn.py` and `on-the-record/hooks/x.py`
    in separate acceptance items) — mirroring the path-segment comparison
    style already used in `gates/gates.py`'s `PROTECTED_DIRS` handling.
  - Both functions return `[]` on no signal; CLI `__main__` fetches
    `gh issue view <n> --json title,body` and exits 1 if either list is
    non-empty, printing the violations.
  - A docstring note (not a runtime check) states plainly that the
    "different roles" tell is intentionally unchecked here, matching
    survey finding (3) and #310's requirement that an unchecked rule say
    so.
- `test_issue_bundling.py`: unit tests against literal strings, no
  network — bundled-title positive/negative cases, acceptance-path-spread
  positive/negative cases, and a same-directory-multiple-files negative
  case (to confirm the check doesn't false-positive on a normal
  multi-file single-mechanism change, e.g. this very issue's own write
  set).
- `.github/workflows/issue-bundling-gate.yml`: triggers on
  `issues: [opened]`, checkout `main` only (same trust-boundary reasoning
  as `plan-aware-closes-gate.yml` — the issue's own text must not be able
  to disable the gate that judges it), runs
  `python3 gates/issue_bundling.py "$ISSUE_NUMBER"`, exits non-zero on a
  bundling signal. Since GitHub Actions cannot block issue creation
  itself (only PR merges), the job posts its failure as a comment on the
  issue (`gh issue comment`) naming the specific violation — this is the
  closest enforcement point available for issue-open events; branch
  protection registration is not applicable here since there is no PR to
  gate.
- `docs/issue-328/reports/implementation.md`: phase-2 record per the
  role-handoff contract's record-shape requirements.

## Out of scope

- Retroactively scanning or flagging issues filed before this gate
  exists.
- The "different roles" tell — no structured role-assignment data exists
  in issue text to check against; recorded as an intentionally unchecked
  signal, not silently implied as covered.
- Auto-splitting a bundled issue into multiple issues — the gate only
  detects and reports; splitting stays a human/LLM authoring decision.
- Changing `on-the-record/commands/run.md`'s issue-filing instructions —
  the gate is the enforcement mechanism; prose guidance is optional
  follow-on, not required by this issue's acceptance.
- The sibling "issue-sizing" problem (issue named as filed alongside
  #328) — different fault per the issue's own text ("a single-mechanism
  issue can still be far too large"), different fix, not addressed here.

## How you'll know it worked

`python3 test_issue_bundling.py` exits 0, covering: a title with " and "/
" 및 " is flagged; a normal title is not; two acceptance bullets
referencing unrelated top-level paths (e.g. `spawn.py` vs.
`on-the-record/hooks/foo.py`) are flagged; acceptance bullets referencing
paths under a shared top-level root (e.g. this issue's own `gates/*.py`
and `test_issue_bundling.py`) are not flagged. This is the executable
artifact that fails when the regression (a bundled issue passing
unflagged, or a legitimate multi-file single-mechanism issue getting
falsely flagged) reoccurs, per #310.
