# Proposal: `gates/accumulation_gate.py` — a narrow, mechanical accumulation check

Status: phase-1 (research + proposal only). Awaiting Approve per contract v3 s19 before any
code lands.

## Context

Issue #424: no gate, record, or acceptance criterion in this system asks what the codebase
becomes after ten more changes of a given shape — only whether one change does what its issue
asked. The issue names four *reachable* patterns and asks (1) what a delivery must state about
the shape it leaves behind, (2) which of those are derivable rather than self-reported, (3) where
the check belongs, (4) what the operator sees. It explicitly rejects prose-only discharge (#310)
and demands an executable artifact, graded against five concrete 2026-08-07 instances.

## Decision

Add one new gate, `gates/accumulation_gate.py` (+ `gates/test_accumulation_gate.py`, following the
existing `gates/*.py` + `gates/test_*.py` pairing already used by `duplicate_test_basenames`),
wired into the same CI harness as the other gates (`gates/gates.py`) so it runs on every PR that
touches `gates/` or Python source — never as a periodic sweep.

The gate checks exactly the four reachable patterns named in the issue's own "honest statement of
the ceiling," and no more:

1. **Duplicate invocation shapes.** Parse Python source for `subprocess.run` / `subprocess.check_*`
   call sites whose first positional arg is a list literal; normalize by (executable, first
   subcommand token); flag when ≥2 call sites in the same file share that normalized shape without
   going through a common helper function. Directly reproduces instance 1 (`gates/ci.py`'s 6
   ungrouped `gh` call sites).
2. **Call-site signature drift.** For a function whose call sites span more than one file (found via
   AST + import resolution, scoped to the repo tree — no cross-repo resolution), diff the
   call-site arg count/order against the current `def`. Fails when a caller's positional-arg count
   no longer matches. Directly reproduces the risk instance 2 describes (`_phase2_record_evidence`
   consumed from both `ci.py` and `closure_sweep.py`); it did not fire historically because the
   signature never actually drifted, so it is a regression guard, not a retroactive catch.
3. **Constant/list growth.** For any module-level list/tuple/set literal assignment, walk
   `git log -p` on that file for the last N (default 5) commits that touched the literal's name;
   flag when the literal grew (item count increased) in every one of the last N such commits. This
   is the shape #303 and the `PACKAGE_REGISTRY_HOSTS`/`github.com` (#406) precedent describe.
4. **Two mechanisms answering the same question.** Explicitly **not attempted**. Detecting that two
   functions/modules encode the same concept ("what counts as delivered") is a semantic judgment,
   not a derivable one — the issue's own ceiling statement excludes this, and any keyword/name
   heuristic here would produce exactly the false-positive noise the scout brief's field survey
   warns against (jscpd/ArchUnit both scope down for this reason). Left to review judgment.

The 43-file `roles/*.json` instance (design question: does a per-role declaration belong in N
files or one?) is also **not attempted** as a mechanical check — it is a placement judgment, not
a derivable pattern, and is explicitly the kind of thing the issue says is unreachable in general.

## Scope-item answers

1. **What a delivery must state**: nothing new is *asserted* by the author — see item 2. The gate
   computes, the author states nothing.
2. **Derivable vs. self-report**: all three implemented checks (duplicate shapes, signature drift,
   list growth) are 100% derivable from the tree + git history; none is a self-report, matching
   #333's rejection of self-reported compliance.
3. **Placement — argued, not defaulted**: per-change CI gate, not a periodic sweep. A periodic
   sweep over accumulated state produces a report nobody is individually on the hook to act on —
   exactly the "noise" failure mode the issue names, and the field survey (scout-brief.md)
   confirms every comparable tool (jscpd, ArchUnit, fitness functions generally) converges on
   running unattended at every-commit cadence with a blocking exit code, not as a report. It also
   is not owned by the delivering role as a self-check — the gate is derivable and adversarial by
   construction (an author under deadline pressure has no incentive to self-flag duplication), so
   it belongs where `duplicate_test_basenames` already lives: the shared CI gate harness everyone's
   PR must pass, independent of which role authored the change.
4. **What the operator sees**: gate failure output names the file:line pair(s) or the growing
   literal directly in CI — the same surface as every other `gates/*.py` failure today. No new UI.

## Honest coverage count

Against the five 2026-08-07 instances named in the issue:

| # | Instance | Caught by this gate? |
|---|---|---|
| 1 | `gates/ci.py` duplicate `gh api` call shapes | **Yes** — check 1 |
| 2 | `_phase2_record_evidence` cross-file signature drift risk | **Yes**, as a regression guard — check 2 |
| 3 | `PACKAGE_REGISTRY_HOSTS`/`github.com`-shaped growing constant | **Yes** — check 3 |
| 4 | A second notion of "delivered" (#383) | **No** — semantic, explicitly out of reachable scope |
| 5 | 43 identical one-line edits to `roles/*.json` | **No** — placement judgment, explicitly out of reachable scope |

**3 of 5.** This is stated as the ceiling, not rounded up: this gate catches shape-level
duplication and drift; it does not and cannot tell whether a structure is *appropriate*, per the
issue's own honesty requirement. A "maintainability" heading whose presence is checked but content
never read is exactly what this proposal avoids by only adding checks with a concrete pass/fail
computation — no new self-report or heading is introduced.

## C4 (container-boundary sketch)

```
[PR author]
    | pushes commit
    v
[CI pipeline] --runs--> [gates/gates.py registry]
                              |-- existing gates (acceptance_gate, ci, closure_sweep, ...)
                              `-- gates/accumulation_gate.py  (NEW)
                                     reads: changed files (diff), git log -p (bounded, N=5)
                                     writes: nothing (stdout pass/fail only, no new state file)
                                     boundary: repo tree + local git history only — no network,
                                     no cross-repo resolution, no persistent store.
```

No new component boundary is introduced beyond one more module inside the existing `gates/`
container; no new external dependency, no new data store, no new service boundary.

## Alternatives considered

- **General AST clone detector (jscpd-style)** across the whole repo — rejected: scout brief notes
  the field itself treats broad clone detection as noisy/false-positive-prone; this repo's actual
  instances are narrow enough that named checks outperform a general detector, and a general
  detector risks becoming the unread heading #310 warns about.
  - **Periodic sweep report** — rejected per scope-item-3 reasoning above (noise, no owner).
- **Self-report field in the delivery record** ("state what you left behind") — rejected: #333
  already rejects self-report as a compliance mechanism.

## Consequences

- New CI gate adds Python-AST-parsing cost to every relevant PR; kept cheap by scoping to changed
  files only (diff-scoped), following the speed axis the scout brief flags as the field's binding
  constraint at every-commit cadence.
- Instances 4 and 5 remain uncaught and stay judgment calls for review — this proposal does not
  claim otherwise.
- `gates/` currently does not collect under `python3 -m pytest -q --ignore=gates` from repo root
  (#398); the new gate's own tests will only run via `gates/`'s existing test invocation path, same
  as all other `gates/test_*.py` today — this proposal does not fix #398, which is out of scope.

## What did not work

(none yet — phase-1 only; this section grows during phase-2 build if approved.)
