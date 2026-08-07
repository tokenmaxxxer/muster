# Survey — issue #415

## Base verified against (#390)

`git rev-parse HEAD` = `05f266c` (main, `issue-415/implementation` branch,
clean). `python3 -m pytest -q --ignore=gates`: 396 passed, 1 pre-existing
failure (`test_spec_index.py::t_baseline_repo_passes`, a stale-hash drift in
`docs/specs/reconciled-index.md` unrelated to this issue — confirmed present
before any edit in this session). `gates/` itself was not collected, per
#398's still-open module-name collision (confirmed: `gates/` still has no
`__init__.py` and `spec_index.py`/`gates.py` still import as top-level
modules — `find gates -name "__init__.py"` returns nothing).

## The instance, as documented (not independently reproducible against the sibling repos)

The issue cites `thaki-agent-security-controller` issue-234 concluding eight
editing surfaces absent while `thaki-agent-security-console` had implemented
them the same day under its own issue-135. Those two repositories are not
checked out anywhere in this environment and are not reachable from this
session (searched: no `~/work/thaki-*` directories exist, confirmed via
`find ~ -maxdepth 3 -iname 'thaki-*' 2>/dev/null` returning nothing; no
network host for them is in this sandbox's allowlist). The instance is taken
as reported in the issue text, not re-run — this survey does not claim to
have reproduced the original incident, only the *shape* of it (below).

## Shape reproduction, done locally

Built two throwaway directories in the scratchpad (not committed anywhere)
to reproduce the mechanism, not the specific incident:
- repo A: `README.md` only, no reference to "capability_x".
- repo B: `capability.py` defining `capability_x()`.

`grep -rl "capability_x" repoA` returns nothing (confirmed, empty output);
`grep -rl "capability_x" repoB` finds `capability.py` (confirmed). A role
whose clone is repo A — mirroring `spawn.py`'s one-clone-per-role model,
confirmed below — has no mechanical way to know repo B, or the capability
it implements, exists; grepping its own clone exhaustively and reporting
"capability_x not found" is indistinguishable, from inside that clone, from
"capability_x does not exist anywhere." This is the shape of the #415
instance. It is a throwaway demonstration, not a kept artifact — the kept,
executable regression lives in `test_repo_scope_gate.py` per the proposal
(fixtures assert the checker flags an unscoped capability-absence sentence
the same way this grep-only reproduction would have been flagged had the
convention existed).

## Current state: spawn.py's isolation model

`spawn.py`'s own docstring (`spawn.py:1-15`) states the write-isolation
rationale for one-clone-per-role explicitly but says nothing about read
access to other repositories — confirmed via `grep -n "sibling\|other repo\|cross-repo" spawn.py`
(no matches). `spawn.py` takes a single working directory (`-C`) and one
role; there is no flag or code path that attaches a second repository,
read-only or otherwise (`grep -n "^def \|add_argument" spawn.py | grep -i repo`
finds only the one `-C` target-directory argument). This confirms the
issue's technical premise: a role's clone is genuinely the only repository
state it can read, mechanically, not just as a matter of discipline.

## #358's mechanism and why it does not reach this issue

`docs/issue-358/proposals/implementation.md` (status: `proposed`, not yet
approved — confirmed via its frontmatter and the absence of
`docs/issue-358/reports/implementation.md` on `main`) proposes
`gates/absence_claims.py`: a syntactic checker that flags absence-claim
phrases ("does not exist", "존재하지 않는다", etc.) lacking an adjacent
evidence marker (a file path, a `grep`/`git show`/`find` command, or a URL).
That checker, once it lands, would catch a bare unevidenced "X does not
exist" — but it would **not** catch a *well-evidenced, single-repo* claim
like "grepped `security-controller` for the editing surfaces, found none" —
that sentence already carries an evidence marker (the grep) and #358's
checker has no notion of repo scope to flag it as incomplete. This is
exactly the boundary the issue text draws itself ("#358's fix does not
reach it") — confirmed by reading #358's own `check()` design, which takes
`text: str` with no repository-identity or multi-repo concept anywhere in
its signature or `KNOWN_CORRECTIONS` list.

## Which questions are cross-repo by nature (issue's question 3)

Surveyed the issue text's own examples plus this repo's existing role
vocabulary (`spawn.py` role names: build/verify/review/qa/coding/etc.,
confirmed via `grep -n "^ROLES\|role ==" spawn.py`) for a syntactic signal
that separates the two classes the issue names:
- "Does capability X exist" / "Is contract Y implemented" — the issue's own
  phrasing, and the shape of both #358's cited cases and the #415 instance,
  is a claim about a *capability or contract*, not about a specific file.
- "Does function Z exist in this file" — scoped to a named, already-open
  file; answerable from the one clone in hand.
The distinguishing signal available syntactically: whether the absence
claim's subject is a named capability/feature/contract noun phrase with no
accompanying file path in the same sentence, versus a claim anchored to a
specific path already read. This is the same "evidence-adjacency, not
adequacy" ceiling #358 already established (`survey.md`'s
"Mechanical-enforceability constraint") — confirmed by re-reading that
section, which explicitly refuses semantic judgment of whether a search was
*sufficient*.

## Boundary (per the issue's own three cross-references, confirmed)

- **#358**: same-repo unevidenced absence claims. Necessary precondition —
  a claim with no evidence marker at all is a strict subset of an
  under-scoped claim — but not sufficient, confirmed above.
- **#376**: `docs/issue-376/reports/implementation/survey.md` exists,
  proposal `docs/issue-376/proposals/2026-08-07-capability-reachability-gates.md`
  — reading its title, it is about capability that exists *and* cannot be
  found *within one reach* (a discoverability problem inside a repo the
  role already has). Different from #415's shape (capability exists
  entirely *outside* the repo the role can see) per the issue's own
  boundary section.
- **#396**: `docs/issue-396/proposals/2026-08-07-consumer-reach-boundary.md`
  — fixes made here not reaching consumer projects; the issue's own text
  calls this "adjacent... opposite sides" of the same visibility boundary,
  not the same question.
- **#298**: orchestrator-side hook/enforcement infrastructure. The issue's
  question 4 ("how the orchestrator... is involved") points here — the
  orchestrator is the one actor that does see across repos in this system's
  current shape (it dispatches `spawn.py` for each repo). Building
  orchestrator-side cross-repo answering is #298's declared territory per
  #358's own proposal (`"the same class of infrastructure #298 already
  owns"`) — confirmed by re-reading #298's still-open state
  (`gh issue view 298` — open, no PR merged referencing it in
  `git log --grep`).

## Write set implied by the above

- `gates/repo_scope.py` — new, standalone syntactic checker (mirrors
  #358's `gates/absence_claims.py` shape but does not depend on it landing
  first, since #358 is unapproved). Exposes a function that flags a
  capability/contract-shaped absence claim lacking a scope statement
  ("as of `<sha>` in `<repo>`" or equivalent), independent of whether the
  claim is otherwise evidenced.
- `test_repo_scope_gate.py` — the shape reproduction (two-repo fixture) as
  pinned regression cases, plus positive/negative string fixtures for the
  capability-vs-file-scoped distinction.
- `docs/specs/survey-conventions.md` — does not yet exist (confirmed:
  `ls docs/specs/` has no such file); #358 proposes creating it. This
  proposal adds a section to the same target path rather than inventing a
  second conventions doc, on the assumption #358 lands first or in
  parallel; if #358 has not landed by the time #415 reaches phase 2, the
  section is written into a standalone file instead (recorded as a
  deviation if it happens).
- `docs/issue-415/reports/implementation.md` — phase-2 record.

## Skip-condition check (scout directive)

Scouting for "category best-in-class" does not apply cleanly — this is
infrastructure internal to one project's role-isolation model, not a
product surface with external exemplars to benchmark against. The nearest
prior art is #358 itself (surveyed in full above) and the issue's own
citations (#376, #396, #298), all internal. No external web sweep was run;
recording this as the skip reason per scout-directive's mandatory skip
record: **skip condition = spec (issue text) leaves the only open design
question as "which of four listed sub-decisions to build now", which this
survey narrows using the issue's own boundary section rather than external
category research.**
