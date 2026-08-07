# Survey — issue #358

## The three cited cases, confirmed against corrected records

- **#318/#320** — the original survey read only `on-the-record/hooks/hooks.json`
  (declares `SessionStart`, `UserPromptSubmit`, `PreToolUse` — 3 events) and the
  open #298 issue text, then generalized their union into "no hook in this repo
  fires on conversational text delivered to the user." Confirmed by reading the
  corrected survey on `origin/issue-318/implementation`
  (`docs/issue-318/reports/implementation/survey.md`, "Root cause" section):
  the claim was never checked against the primary source (Claude Code's hooks
  reference) that actually answers the question. A `Stop` hook exists,
  receives `last_assistant_message`, and can block — hooks.json not declaring
  it is a fact about this plugin's *configuration*, not about the platform's
  *capability*.
- **#324** — the original survey treated `spec.md` as the primary write-set
  signal. Confirmed via `git show origin/issue-324/implementation:docs/issue-324/reports/implementation/survey.md`
  ("Correction" note): repo-wide measurement on 2026-08-07 found 0 of 87
  `docs/issue-*/` trees contain a `spec.md`, and no writer for one exists in
  `spawn.py` or `commands/*.md` — `gates/gates.py:writeset()`'s `spec.md` read
  is dead code for the current flow. The absence claim needed here runs the
  other way from #318/#320: `spec.md` really is absent, but the original
  survey treated an untested read (`writeset()` calls it) as proof the file
  gets produced, rather than checking file existence directly.
- **#341/#327** — `runs/ledger.jsonl` and a file the record called
  `runs/roster.json` were cited as not existing. Confirmed in this checkout:
  `.gitignore:1` lists `runs/`, so nothing under `runs/` is ever present in a
  role session's clone regardless of what exists on the operator's machine —
  genuinely unavailable to this checkout, not proven absent from the system.
  The actual constant is `ROSTER = ROOT / "runs" / "active.json"`
  (`spawn.py:1393`), not `runs/roster.json` — confirmed by
  `grep -n "runs/roster\|runs/ledger\|runs/active" spawn.py`, which finds only
  `runs/active.json` (`spawn.py:1393` docstring) and `runs/ledger.jsonl`
  (`spawn.py:2101` docstring, `on-the-record/commands/run.md:340`). The
  filename error compounds the absence error: the record was wrong about both
  *whether* the thing exists and *what it is called*.

## Where "does not exist" gets written today

Searched for any existing convention governing survey absence claims:

- `on-the-record/commands/run.md` (354 lines, orchestrator-facing) — has no
  section addressing how role sessions write surveys; it governs the
  orchestrator's own PR-description and mission-board steps only (`grep -n
  "survey"` on this file: no output).
- `docs/specs/` (`approvers.md`, `flows-schema.md`) — neither addresses survey
  content or absence-claim evidence.
- `docs/decisions/` (`2026-07-29-headless-cli-measured-facts.md`,
  `2026-07-29-permanently-closed-alternatives.md`) — the first is the closest
  existing precedent in spirit (measured facts over assumed ones) but does not
  address the specific gitignored-clone or platform-capability failure modes.
- `gates/gates.py` — every `check()` function (`record_wellformed`,
  `record_no_tool_residue`, `record_fulfils_diff`, etc., `gates/gates.py:534`)
  operates on the committed diff and record frontmatter. None reads survey
  *prose content* for absence-claim shape; there is no established mechanical
  pattern in this repo for checking what a survey document *says*, only for
  what a record's frontmatter/diff structurally contains.

Conclusion: this repo has no existing convention or mechanical check for
survey absence claims. #358 is not correcting a broken rule — it is proposing
a first one.

## The precedent this issue is the survey-layer instance of

#287 ("can't check" reported as "checked clean") establishes the same
distinction one layer down, at the gates: a failed `gh` lookup must produce a
distinct, named "could not check" outcome, never an empty result that reads as
a clean one. #358 is the same shape applied to prose: a role session that
cannot see `runs/` (gitignored) or does not know Claude Code's hook surface
(never asked the primary source) must not write "does not exist" — it must
write "not visible from this clone" or "not verified against the primary
source," distinctly from a genuine, verified absence like `spec.md`'s.

## Mechanical-enforceability constraint (per #310, checked honestly per #358's own Acceptance)

A survey is prose. Whether a given English/Korean sentence is an
*unfounded* absence claim is a natural-language judgment call — the same
class of check #341's survey already refused to attempt for orchestrator
constraint claims ("classifying ... is a natural-language judgment call,
which is exactly the kind of check gates.py's own docstring says a mechanical
gate must refuse to attempt"). A gate that must guess whether "X does not
exist" was backed by a real search cannot reliably tell a diligent absence
claim from a careless one — attempting that classification would itself be
an unfounded-absence-claim generator.

What **is** mechanically checkable, without guessing at meaning:
1. **Syntactic evidence-adjacency**: whether a sentence matching an
   absence-claim pattern (a fixed phrase list: "does not exist", "is absent",
   "was not found", "존재하지 않는다", "없다" adjacent to a path-like token)
   is accompanied, in the same paragraph, by a citable search description —
   a command (`grep`/`git show`/`find`), a file path, or a cited source URL.
   This does not verify the search was *sufficient*, only that *a* search is
   named — the same "named, checkable source rather than an inference" bar
   #318's corrected survey held itself to.
2. **Two known-wrong facts as regression fixtures**: this issue's own two
   corrected facts (`runs/active.json`, not `runs/roster.json`; a `Stop` hook
   exists and is documented at the cited URL) can be pinned as permanent
   regression assertions — cheap, exact, and already fully verified above.

What is **not** mechanically checkable: whether a search was *adequate*
(a role session could cite a trivial grep and still miss the real answer),
and whether a claim about platform capability (as opposed to repository
content) was checked against the right primary source at all — recognizing
"this is a platform-capability question, not a repository-content question"
is itself a judgment call with no syntactic signal to key on.

## Sibling-issue boundary

- **#287** — same distinction, at the gates/reporting layer (`gh` failures,
  ledger corruption). #358 is prose/survey layer; it does not touch
  `closure_sweep.py`, `flows.py`, or `deliverable-guard.sh`.
- **#310** — governs the acceptance bar (executable artifact, not prose) for
  every issue in this run, #358 included; not re-litigated here.
- **#318/#320, #324, #341/#327** — already corrected on their own branches;
  #358 does not reopen or re-fix those, it addresses the survey-writing habit
  that produced all three.
- **#298** (orchestrator ungated) — distinct actor (orchestrator prose vs.
  role-session survey prose) and distinct surface; not folded in here.

## Expected write set

- `gates/absence_claims.py` (new) — the syntactic evidence-adjacency checker
  described above, plus the two pinned regression facts.
- `test_absence_claims.py` (new) — executable regression test.
- A short addition to `on-the-record/commands/run.md` or a new
  `docs/specs/survey-conventions.md` naming the "cannot see" vs. "does not
  exist" distinction and the search-evidence requirement for role sessions
  writing surveys (exact location decided in the proposal's Rationale).
- `docs/issue-358/reports/implementation.md` — phase-2 record, written only
  after approval.
