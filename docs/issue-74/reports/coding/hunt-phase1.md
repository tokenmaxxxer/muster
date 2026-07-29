---
subject: issue-74
role: coding
proposal: docs/issue-74/proposals/coding.md
---

# Hunt record — self-check-suite-revival

## after-proposal — stance 1: does anything in wakes.py read the board/proposals through a v3 path shape that a corrected fixture would still not satisfy — a second, undiscovered drift?

Verdict: FINDING — `wakes.py`'s finding-to-coding branch computes `subject` from the wrong path component, so it silently bypasses the section-19 first-build approval gate for every finding addressed to `coding`.

Kind: silent-failure

Seed: the four already-located root causes plus "does anything in wakes.py or gates/ read the board or proposals through a path shape that a v3-corrected fixture would still not satisfy". I walked every `t_wake_*` test with hand-built v3-shaped fixtures (`docs/issue-<n>/reports/<role>.md`, `docs/issue-<n>/proposals/*.md`) to see which currently-passing assertions are vacuous and which would flip once the fixtures are corrected. All of them turned out to compose correctly against production code *except* one path that test_gates.py never exercises at all: a finding whose `addressed_to:` is `coding` (the suite only ever tests `addressed_to: qa`, see test_gates.py:146).

`wakes._rows()` (wakes.py:331-340) has a `role == "coding"` special case specifically so that findings addressed to coding go through `wake_coding()`, which enforces the section-19 "first build needs a scope-approved front record" gate — the comment at wakes.py:333-334 says so explicitly ("SS19 applies to the finding branch too — all four branches are subject to it"). To find the subject the finding belongs to, it does:

```python
subject = Path(f).parent.name
```

where `f` is the finding-bearing record's path, e.g. a `reports/review.md` file three levels under the repo root (from `_findings_to`, wakes.py:194-201, which always returns paths of that shape). `Path(f).parent.name` resolves to the literal string `"reports"`, not the issue directory name one level further up — the subject is one level up, so it should be `Path(f).parent.parent.name`. Since `"reports"` is never a key in the board dict returned by `spawn.board()` (which is keyed by the issue directory name), `if subject in b:` is always false, `wake_coding()` is never called for this branch, and execution falls through to the unconditional `woken.append(Row(role, ...))` on wakes.py:339-340 — the exact same statement used for roles that have no gate at all. The result: a finding addressed to `coding` wakes `coding` unconditionally, regardless of whether the subject's front record is scope-approved, and it never shows up in the `blocked` list either. This is indistinguishable from a correctly-gated wake unless you specifically check whether the gate held.

### Reproduce
Run this from the repo root with a Python interpreter that can import `spawn` and `wakes` (add `.` and `gates/` to `sys.path`). Build, in a scratch git repo, one issue tree whose `reports` directory holds two files: a `feasibility.md` record at `loop_state: probing` (i.e. not yet `scope-approved` — the subject has not entered its first build), and a `review.md` record whose body carries a finding block with `addressed_to: coding` and `severity: blocking`. Commit both, then call `wakes.evaluate(str(root))` and inspect the `woken` and `blocked` lists it returns.

### Observed
`coding` appears directly in the `woken` list (as `('coding', 'finding addressed_to: coding — <path to the review record>')`) and the `blocked` list is empty — even though the subject's only front record (`feasibility`) is at `loop_state: probing`, not `scope-approved`.

### Expected
`coding` should not appear in `woken` at all here — it should appear in `blocked` instead, exactly the way it does when the *feasibility-verdict-go* branch (not the finding branch) hits an un-approved front record: verified in the same session that `wake_coding()` correctly produces a populated `blocked` list and an empty `woken` entry for `coding` in that case. The fix is to walk up one more directory level when recovering `subject` from the finding-bearing record's path at wakes.py:335, matching the shape `_findings_to` actually returns (`<board root>/<issue dir>/reports/<role>.md`). No existing test in test_gates.py would catch this even after the v2->v3 fixture rewrite, because none of them set `addressed_to: coding` — only `addressed_to: qa` is exercised (test_gates.py:139-148).
