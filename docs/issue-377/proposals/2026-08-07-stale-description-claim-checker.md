---
status: proposed
files:
  - gates/claims.py
  - gates/test_claims.py
  - gates/gates.py
  - gates/ci.py
  - roles/implementation.json
  - .github/workflows/plan-aware-closes-gate.yml
---

## Request

Operator observation, filed 2026-08-07: the system's self-descriptions
(comments, docstrings, role JSON, workflow comments) go stale unchecked,
and a stale-but-confident description is worse than no description — it
ends an inquiry an absence would have continued. Sibling to #376
(capability that exists and can't be found); this issue is the opposite
sign — description that persists after the described thing changed.
Four named instances from 2026-08-07 must be run against whatever is
built, with the catch count stated honestly.

## Constraints

- Per #310: prose does not discharge this; the fix must be an artifact
  that runs, not a written rule about keeping descriptions accurate
  (that would be the exact failure the issue reports, self-applied).
- Only the checkable half of a mixed claim gets a mechanical check; the
  intent half stays prose, per the issue's own instruction.
- Check `record_fulfils_diff` / #330 / #333 for overlap before building
  a new mechanism (done in survey.md) — none cover this surface; the
  *shape* of `record_fulfils_diff` (opt-in marker → paired mechanical
  check) is reused, not duplicated.
- State the catch count against the four named instances honestly, even
  if partial.

## Rationale

**Considered:** a general-purpose "docstring linter" that tries to parse
arbitrary prose and infer a checkable claim automatically (e.g. NLP-ish
pattern matching over comments). **Rejected:** this is exactly the kind
of thing that produces false confidence — a linter that *thinks* it
understood a claim from free text and checks the wrong thing is worse
than no linter, because it launders unverified inference through a tool
that looks authoritative (the issue's own complaint, one level down).
An opt-in marker (author states the checkable claim explicitly, in a
small fixed vocabulary) trades automatic coverage for correctness: every
check that exists is provably checking what the author meant, at the
cost of not catching claims nobody annotated. Chose the marker approach
because `record_fulfils_diff` already validated it as a shape in this
repo and it fails honestly (silence, not wrong answers) on unmarked
prose.

**Considered:** wiring the new checker into `gates/ci.py`'s required CI
path immediately, same commit. **Rejected:** the write-set for this
proposal already touches `.github/workflows/plan-aware-closes-gate.yml`
for a comment split (see below); adding this check to the *required*
branch-protection status check is a second, separable decision (does a
false-negative on a stale claim, or a checker bug, block merges
repo-wide?) that deserves its own review, not a rider on the first
delivery. The new gate function ships and is unit-tested and runnable
standalone (`python3 gates/claims.py`), so it is real and can be
promoted to required-check status in a follow-up once it has run clean
for a cycle.

## What will be done

1. **`gates/claims.py`** — new module, `record_fulfils_diff`'s shape:
   - Marker comment `# CLAIM-CHECK: <kind> <args>` anywhere in a tracked
     file. Two kinds only (no speculative third kind):
     - `enum-subset <json-path>:<key> <glob>:<frontmatter-key>` — every
       value found for `<frontmatter-key>` in the frontmatter of files
       matching `<glob>` must appear in the JSON array at `<json-path>`
       (dotted key) `[<key>]`. Reuses `gates.record_frontmatter`.
     - `producer-exists <filename>` — at least one file named
       `<filename>` must exist anywhere in the repo tree (falsifies
       "this artifact is produced/consumed" claims when nothing ever
       writes or has ever written one).
   - `check_claims(repo: Path) -> list[str]`: finds all `CLAIM-CHECK`
     lines via `git grep`, evaluates each, returns one message per
     failed claim naming the file:line and what was expected vs. found.
     A `CLAIM-CHECK` line with an unrecognized kind or malformed args is
     itself a failure (fail closed, matching `record_fulfils_diff`'s own
     stated principle for its `fulfils:` line) — never silently skipped.
   - Registered in `gates.ALL` alongside `record_fulfils_diff` so it is
     callable the same way; NOT added to `gates/ci.py`'s required path
     in this delivery (see Rationale) — runnable via
     `python3 -m gates.claims .` or `python3 -c "import gates.claims as
     c, gates; print(c.check_claims(Path('.')))"` for now.
2. **`gates/test_claims.py`** — unit tests for both check kinds
   (pass/fail cases), plus one test that runs `check_claims()` against
   this repo's actual tree and asserts it catches the #3 and #4
   instances once they're annotated (step 3) — this is the "run it
   against the four instances" requirement, executable rather than
   asserted in prose.
3. **Annotate the two cleanly checkable instances:**
   - `roles/implementation.json` gets no code change to the enum itself
     (out of scope — fixing #147's drifted vocabulary is #147's job, not
     this issue's); instead `gates/gates.py` (near `record_frontmatter`
     or a new small section) gets a `# CLAIM-CHECK: enum-subset
     roles/implementation.json:loop_state docs/issue-*/reports/
     *.md:loop_state` marker, so the *drift itself* is now mechanically
     caught going forward, without this proposal taking on fixing #147.
   - `gates/gates.py::writeset()` docstring gets a
     `# CLAIM-CHECK: producer-exists spec.md` marker next to the
     spec.md-based claim, making its currently-false premise fail
     loudly instead of reading as present-tense truth.
4. **`.github/workflows/plan-aware-closes-gate.yml`** comment split: the
   mixed claim on the checkout-pinning comment is rewritten to state
   only what is still true today — "checkout stays pinned to `main`
   because this workflow never checks out the PR's own code" (the
   checkable-and-still-true half, left as prose since it is about *this
   workflow step*, already enforced by the `ref: main` line right below
   it) — and drops the now-false "PR의 파일 diff를 전혀 보지 않는다"
   clause, replacing it with a one-line note that `closes_only` mode
   does read one local file (`_phase2_record_evidence`, #284) but never
   the PR's own diff. This is a comment edit, not a new claim marker —
   the trust-boundary reasoning is intent, not a checkable property (per
   Constraints), so it stays prose, corrected rather than machine-bound.

## Out of scope

- Fixing #147's enum drift itself (only detecting future drift of the
  same shape).
- "Fixing" the `roster_watchdog` docstring (#325's job — prose cannot
  discharge it, and no mechanism this proposal builds can verify a
  polling discipline that doesn't exist yet).
- Wiring `gates/claims.py` into the required CI status check (follow-up
  decision, not this delivery — see Rationale).
- A general/automatic claim-extraction linter (rejected in Rationale).
- #330's reach-check mechanism itself (not touched; confirmed no
  current overlap to coordinate against, since #330 has not landed an
  artifact yet).

## How you'll know it worked

- `python3 -m pytest gates/test_claims.py` passes.
- Running `check_claims()` against this repo's tree after step 3's
  markers land reports exactly 2 failures (the #3 enum drift and the #4
  spec.md producer-exists claim) before any fix, and 0 after `roles/
  implementation.json`'s enum is corrected or `spec.md` is produced —
  proving the check is live, not decorative.
- Stated catch count against the four named instances: **2 of 4**
  (#3 enum drift, #4 spec.md claim) mechanically caught and enforced
  going forward; **1 of 4** (#1, the workflow comment) corrected by
  hand this delivery because its checkable half is a code-shape claim
  not covered by either marker kind, with its non-checkable half left
  as corrected prose per the issue's own instruction; **1 of 4** (#2,
  `roster_watchdog`) explicitly and permanently out of this mechanism's
  reach, per the issue's own ruling that a promise cannot be fixed by
  checking prose.
