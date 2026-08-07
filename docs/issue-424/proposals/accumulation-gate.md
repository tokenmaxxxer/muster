# Proposal: wire symptom-handling shut, per instance — not a root/symptom judgment gate

Status: phase-1 (research + proposal only). Awaiting Approve per contract v3 s19 before any
code lands.

## Context (superseded scope — read this before the decision below)

This proposal was rewritten twice by operator correction, both on 2026-08-07:

1. First correction withdrew the original body's "honest ceiling" — duplicate-call-shape counts,
   signature-drift counts, growing-constant counts — as the deliverable. Those are counted because
   they're easy to count, and counting them silently swapped the real question ("did this change
   solve the problem structurally") for a different, cheaper one. Duplication-count and
   root-cause-ness correlate weakly and not even in a guaranteed direction.
2. Second correction withdrew both remaining branches of the first correction's three-way fork —
   (1) require the author to state which layer they addressed, (2) stand up a separate judge role
   to rule root-vs-symptom. Both terminate in one more piece of prose whose truth the operator must
   still weigh; that is the shape already refused today in #319 (approval fatigue), #371 (degree-of-
   completion prose), #411 (unchecked rule masquerading as an enforced one). An author's "I solved
   it structurally" and a reviewer's "yes they did" carry identical unverifiability.

**What survives, and is now the entire scope of this proposal**: build by removing the option, not
by judging the choice. The single question this proposal answers, per named instance: *is there
wiring that makes symptom-handling structurally unreachable at that point, and if so where does it
hang.* Not "is there duplication," not "did the author try hard enough" — whether the path to the
symptom-shaped state can be physically closed. `record-fields-gate` does not advise a record state
its basis, it refuses to commit a record missing the field; `closes-gate` does not advise closing
the issue, it refuses to merge a delivery that doesn't; `board-gate` does not advise staying inside
your own issue tree, it refuses the write. This proposal looks for that same shape at each of the
five named instances, and states plainly where it isn't there.

No re-scouting was run for this revision: the operator's second correction names the exact
in-repo precedent to follow (`record-fields-gate`/`closes-gate`/`board-gate`), so the steering
question is internal-precedent-fit, not field-survey — the prior scout-brief.md (external
fitness-function tooling: jscpd, ArchUnit) answered a question this revision no longer asks and is
superseded, not deleted, as the phase-1 record of what was tried first.

## Decision

Per instance, below. Each verdict is graded against one test: **would this wiring make the
symptom-shaped change fail to merge, with no one having to read prose and decide whether to
believe it?** If yes, the wiring is specified concretely enough to build in phase 2. If no, the
instance is recorded as unreachable per #310 — not papered over with "the author should be
careful" or "review should judge," both withdrawn by the operator's second correction.

### Instance 1 — `gates/ci.py`'s second, malformed `gh api` call shape (#388)

**Reachable. Wiring: a single `gh`-invocation chokepoint + a gate that refuses any other one.**

Today `gates/ci.py` has 6 independent call sites (`ci.py:59,79,104,122,204,256`), each with its own
inline `import subprocess` + `subprocess.run(...)`. Nothing stops a 7th ad hoc shape — the comment
at `ci.py:188` telling the next author to reuse the existing shape is exactly the kind of advisory
prose this issue now refuses to rely on.

The fix that removes the option: collapse all `gh` invocation into one function (e.g.
`_gh(*args) -> subprocess.CompletedProcess`) that every call site in `gates/` must go through, then
add a mechanical CI check — AST-scan every `gates/*.py` file for a `subprocess.run`/`check_*` call
whose first-arg list contains the literal `"gh"`, outside the one file/line defining `_gh`. Any
match fails the gate. This is not "duplication is high, please reduce it" — it is that a second
shape for invoking `gh` **cannot be committed at all**, symptom-patch or not, because there is
exactly one legal call site and the gate enforces that geometrically (same shape as `board-gate`
refusing a write outside the declared path).

Where it hangs: a new check function inside `gates/ci.py` or `gates/gates.py` (co-located with
`duplicate_test_basenames`, the one existing dedup check), run on every PR touching `gates/`.

### Instance 2 — `_phase2_record_evidence` cross-file signature drift (#369 risk on #383)

**Reachable. Wiring: static call-site verification in CI, not a self-report and not a documented
dependency list.**

`_phase2_record_evidence` (`gates/ci.py:223`) has two call sites today — `gates/ci.py:377` and
`gates/closure_sweep.py:113` — and nothing in the tree records that `closure_sweep.py` depends on
this signature. Writing that dependency down (a comment, a docstring, a manifest entry) is prose
again — it can rot the moment a caller is added and nobody updates it, and the issue names exactly
this failure mode.

The fix that removes the option: add a type-checker (e.g. `mypy --strict` scoped to `gates/`) to
the CI gate set, with `_phase2_record_evidence` fully annotated. A signature change that leaves any
call site's argument count/types mismatched fails the type-check step, unconditionally, before
merge — not because someone remembered to grep for callers, but because the checker resolves every
call site in the tree by construction. This also forecloses the symptom-patch version of this
failure (silently widening the signature to `*args, **kwargs` to avoid breaking callers) if the
lint config additionally bans `**kwargs`/`*args` on this function — a mismatched call becomes
unrepresentable, not merely flagged.

Where it hangs: a new CI step (`mypy` invocation) in the same harness `gates/gates.py`/`gates/ci.py`
already run from; scope to `gates/` first since that is where the named instance lives, not a
repo-wide type-check migration (out of scope here).

### Instance 3 — `PACKAGE_REGISTRY_HOSTS`/`github.com` growing constant (#406, precedent #303)

**Not reachable. No wiring found; recording why, per #310.**

The symptom here is not "a list has an item appended" — a list gaining an item is sometimes the
entire correct fix. The symptom is *solving the specific case by enumeration instead of the general
rule the enumeration is standing in for* (e.g., "is this a package registry host" solved by a
member-list instead of, say, a suffix/pattern rule or a delegated-trust check). Whether the general
rule exists and covers the case is a question about the domain the constant encodes, not about the
tree's shape. There is no AST/git-log-derivable predicate for "this list item should have been a
rule" — building one collapses back into the withdrawn growing-constant *count*, which the first
operator correction already rejected as a weak, undirected proxy.

This is the same ceiling the issue's own withdrawn section named for pattern 4: unreachable in
general. Recorded as unreachable, not as "flag when a list grows N times running" (that gate would
be presence-only — it fires on correct list growth exactly as often as on symptom-shaped growth,
which is the non-discharge #310 names) and not as "author/reviewer should judge" (withdrawn).

### Instance 4 — a second notion of "delivered" that almost forked (#383)

**Not reachable. No wiring found; recording why, per #310.**

Detecting that two functions/modules answer the same semantic question ("what counts as delivered")
requires understanding what each means, not just their shape. #383's author avoided the fork by
convention and said so in prose — nothing structural stopped it, and nothing structural could have:
there is no syntactic signal distinguishing "a second, competing definition of delivered" from "a
legitimately different concept that happens to also return a bool." This is exactly the issue
body's own honest-ceiling statement for this pattern, and the operator's corrections did not reopen
it — they narrowed what counts as an acceptable *answer* to "unreachable," not the reachability
itself. Recorded as unreachable.

### Instance 5 — 43 identical one-line edits to `roles/*.json`

**Reachable, but only via a design change to where the value lives — not via detecting the edit
pattern.**

Counting "the same one-line diff appeared in 43 files" is the withdrawn proxy-metric shape again —
identical repeated diffs are sometimes exactly correct (a genuinely per-role, independently-owned
value that happens to be changing the same way this time). What removes the *option* to keep
storing a shared value once-per-role is moving that value to one location the per-role files
inherit from or are generated from, then gating on the *result*: a CI check that fails if a
`roles/*.json` file redefines a key that the (to-be-created) shared-defaults source already
declares, forcing the value out of N files and into 1. That is buildable in the `record-fields-gate`
shape — refuse the commit that recreates the duplicate, not judge whether duplicating it was a good
idea this time.

This is conditional, not unconditionally reachable today: it requires first deciding (a design
question, out of this proposal's scope) which `roles/*.json` fields are meant to be shared defaults
vs. genuinely per-role. Recorded as **reachable pending that design decision** — the enforcement
gate is mechanical once the shared-vs-per-role boundary is drawn, but this proposal does not draw
that boundary itself, since doing so requires reading what each of the 43 fields actually encodes,
which is domain work belonging to the role that owns `roles/*.json`'s schema, not to this gate
proposal.

## Coverage count

Per the issue's own acceptance criterion (five instances, catching means *judging the delivery as
symptom-only*, not *finding duplication*):

| # | Instance | Structurally-unreachable wiring found? |
|---|---|---|
| 1 | `gates/ci.py` second `gh api` call shape | **Yes** — single chokepoint + AST gate |
| 2 | `_phase2_record_evidence` signature drift | **Yes** — mypy in CI, no `*args`/`**kwargs` escape |
| 3 | `PACKAGE_REGISTRY_HOSTS`-shaped growing constant | **No** — recorded unreachable, per #310 |
| 4 | Second "delivered" definition (#383) | **No** — recorded unreachable, per #310 |
| 5 | 43-file `roles/*.json` edit | **Reachable pending an out-of-scope design decision** |

**2 of 5 unconditionally reachable, 1 conditional, 2 recorded as not reachable.** This is stated as
the count, not rounded toward 5: instances 3 and 4 both require judging whether a given code shape
is the *right* generalization, and the operator's own corrections withdrew every mechanism this
proposal could have used to make that judgment on someone's behalf, human or agent. Where no wiring
exists, this proposal states that plainly rather than substituting "author should state" or
"reviewer should judge" — both withdrawn — or a presence-only heading nobody reads (#310, #363's
trap).

## C4 (container-boundary sketch)

```
[PR author]
    | pushes commit touching gates/
    v
[CI pipeline] --runs--> [gates/gates.py registry]
        |-- existing gates (acceptance_gate, ci, closure_sweep, duplicate_test_basenames, ...)
        |-- gates/ci.py: single `_gh()` chokepoint + AST check refusing any other `gh` call site
        `-- mypy --strict (scoped: gates/) — refuses any call-site/def signature mismatch,
              unconditionally, before merge
```

No new external dependency beyond `mypy` (already a common, zero-network, offline static
analyzer); no new data store; no new service boundary. Instance 5's conditional gate is not
included in this boundary sketch — it depends on a `roles/*.json` schema design decision this
proposal does not make.

## Alternatives considered

- **A root-vs-symptom judgment gate** (author self-report, or a separate judging role) — this is
  the operator's second correction's rejected branch, restated for completeness: both terminate in
  prose a human must decide whether to believe, which #319/#371/#411 already establish this
  repository refuses.
- **Counting duplication/drift/growth as a proxy for structural-ness** — the operator's first
  correction's rejected branch: weak, undirected correlation between the count and whether the root
  was actually addressed.
- **A general semantic-clone detector for instance 4** — rejected: no syntactic signal distinguishes
  a harmful second "delivered" definition from a legitimately distinct concept; building one risks
  exactly the unread-heading failure #310/#363 warn about.

## Consequences

- Instances 1 and 2 get concrete, mergeable gates in phase 2 if approved: a `gates/ci.py`
  chokepoint refactor + AST check, and a `mypy --strict` CI step scoped to `gates/`.
- Instance 5's gate is blocked on a design decision this proposal explicitly does not make; phase 2
  should either draw that boundary (as a separate, scoped sub-decision) or defer instance 5 and
  land 1+2 alone — argued in phase 2, not decided here.
- Instances 3 and 4 remain outside this system's reach; the operator is, and stays, the only
  detector for those two, same as the issue's own honest-ceiling statement already conceded before
  either correction landed.
- `gates/` does not collect under `python3 -m pytest -q --ignore=gates` from repo root (#398,
  confirmed again this session) — the new `mypy` step and the AST check's own tests would run only
  via `gates/`'s existing separate test-invocation path, same as every other `gates/test_*.py`
  today. This proposal does not fix #398.

## What did not work

- The original phase-1 draft (duplicate-call-shape count, signature-drift count, growing-constant
  count, all with a numeric coverage table) was written before either operator correction and is
  fully superseded by this revision — kept as git history, not repeated here since the withdrawal
  reason is the substance of this proposal, not an aside.
