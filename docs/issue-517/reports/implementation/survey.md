# Survey — issue-517: aggregate record_lint + record scaffolder

## Where record checks live today

Record-authoring rules are split across two layers, neither of which
gives an author a single aggregated pre-check:

1. **`gates/gates.py`** (CI-side, diff-scan against a whole PR): the
   real rule implementations — `record_enums`, `record_refusal_reasoned`,
   `record_wellformed_in`/`record_wellformed`, `record_no_tool_residue_in`,
   `record_derived_counts_in`, `record_fulfils_diff`, `record_checked_claims`,
   `reach_check`, `sibling_mention_check` all live in `gates/gates.py`.
   `gates/ci.py` already accumulates several of these into one `bad` list
   (chained `bad += gates.record_enums(...)`-style calls) — so *CI*
   already reports several violations per run, but only after a PR is
   opened.
2. **`on-the-record/hooks/record-claim-guard.sh`** (PreToolUse, write-time):
   a hand-written Python mirror of a subset of `gates.py`'s checks (issue
   #310, #331, #333, #330 — unverifiable-reason, checked-claim reason,
   bare-count claims, orphaned path references), scoped to
   `docs/issue-*/reports/**` writes. Its own docstring says plainly it is
   "a write-time approximation, not a byte-identical port" of `gates.py`'s
   CI checks — it only sees one write's fragment, not the full file, so
   it cannot check whole-file-shape rules such as `loop_state` presence,
   required headings, or frontmatter completeness.

No `record_lint`, `record-fields-gate.sh`, `record-shape-gate.sh`,
`survey-order-gate.sh`, or `proposal-shape-gate.sh` file exists anywhere
in the repo outside two unrelated per-role skeleton generators under
`docs/issue-170/_assets/rulebook-skeleton` and
`docs/issue-167/_assets/rulebook-skeleton` — a different subsystem that
scaffolds *other* plugins' rulebooks, not this repo's own record checks
(confirmed via a repo-wide filename search). The session-start directives
naming those gate scripts describe a target state this issue is asked to
build toward, not code already present in this repo.

**Consequence matching the issue's observed pain**: whole-file rules
(`loop_state` presence/enum, required headings, frontmatter shape) are
enforced only in CI, after a PR is opened — an author gets no write-time
signal for them today and discovers them only via a failed CI run, or
via repeated after-the-fact review comments each naming one more missing
thing. `record-claim-guard.sh`'s checks are the only write-time signal
that exists, and they cover only a claim-shape slice, not the full rule
set gates.py already implements.

## Existing single-source-of-truth precedent

`gates/gates.py` functions already take a `(dir, cfg)`-shaped signature
and return the complete violation list for that one check (no
first-failure abort inside a single function) — each does
`bad.append(...)`/`bad += ...` and returns the full list. `gates/ci.py`
already composes several via list concatenation. This is the aggregation
pattern to reuse, not invent: `record_lint` should be a thin CLI wrapper
that calls the existing `gates.py` check functions against a full record
file on disk (not a diff fragment) plus the checks
`record-claim-guard.sh` currently duplicates as inline Python, unioning
all resulting violation lists in one pass.

## Role definitions as the schema source

`roles/<role>.json` already declares `record_fields.loop_state` (an enum
plus a terminal state) per role — `gates/gates.py` cross-checks this
declaration against a `# CLAIM-CHECK: enum-subset` marker comment near
`record_enums`. A scaffolder generating a role/issue-appropriate skeleton
has a real, existing per-role schema to read from — `record_fields` in
`roles/<role>.json` — rather than needing a new schema file.
`record_wellformed`/`record_wellformed_in` in `gates/gates.py` is the
existing check for "loop_state/verdict readable at all," a natural model
for what "required section present" should look like for the
scaffolder's placeholder-vs-gate contract.

## Deployment shape

Hooks run via `${CLAUDE_PLUGIN_ROOT}/hooks/*.sh` (registered in
`on-the-record/hooks/hooks.json`), each a bash wrapper invoking inline
Python or a `python3 -m gates.<module>` call. `gates/claims.py`'s own CLI
entry point (its module docstring documents `python3 -m gates.claims .`)
is the existing pattern for "a gates/ module directly runnable against a
repo root" — `record_lint` should follow the same `python3 -m
gates.record_lint <dir>` shape so a PreToolUse hook and a plain CLI
invocation (issue requirement 3: "run `record_lint` before writing the
record") call the identical code path, and `gates/ci.py` can also switch
its existing chained `bad += gates.record_enums(...)`-style calls to call
the same aggregator instead of hand-listing checks.

## Alternatives visible from this state

- **Keep checks scattered, just document "run these commands before
  writing"**: rejected in Rationale — doesn't satisfy requirement 1's
  "single command... single source of truth," and a fixture-driven pytest
  asserting one invocation reports every violation cannot be satisfied by
  several separate commands.
- **Rewrite `record-claim-guard.sh`'s checks from scratch inside
  `record_lint` instead of reusing `gates.py`**: rejected — `gates.py`
  already owns more check functions than `record-claim-guard.sh` mirrors
  (`record_enums`, `record_refusal_reasoned`, `record_no_tool_residue_in`,
  `sibling_mention_check`, `reach_check` are not mirrored at all today);
  duplicating logic a second time recreates exactly the "duplicated rule
  logic" drift risk issue requirement 1's "no drift" clause names.
