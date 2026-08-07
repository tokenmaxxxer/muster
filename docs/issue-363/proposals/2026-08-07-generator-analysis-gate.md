---
kind: proposal
date: 2026-08-07
subject: issue-363
role: implementation
---

files: gates/gates.py, gates/ci.py, test_gates.py, on-the-record/hooks/generator-guard.sh,
on-the-record/hooks/hooks.json, on-the-record/hooks/test_generator_guard.sh

## Request

Nothing in this repo requires a proposal to say what produced the defect it fixes, so a proposal
that only handles the symptom passes every check that exists today (#363). The issue names a
trap in advance: a required `## Generator` heading whose presence is checked but content never
read is itself a symptom fix for the symptom-fix problem. It also forecloses one dodge: the
`Stop` hook makes the orchestrator's own conversational output inspectable (#298), so the
question of whether this binds the orchestrator's chat proposals — not just role proposals —
cannot be answered "not mechanically reachable."

## Constraints

- No new dependency, no new env var, no schema/migration.
- `gates/gates.py` and `gates/ci.py` are under `PROTECTED_ROOT_DIRS`
  (`gates.py:26`) — this PR's diff will trip `is_protected()` and route to mandatory human
  review regardless of this check's own content. Expected, not worked around.
- Must not change the return shape or call signature of any existing function in
  `gates/gates.py`'s `ALL` registry — only add one new entry.
- The `Stop`-hook half must not fire inside role sessions (`CLAUDE_ROLE` set), mirroring
  `deliverable-guard.sh`'s existing convention (`deliverable-guard.sh:17`) — this issue's
  instance was the orchestrator's own chat output, not a role's.
- Per #310/#330: acceptance is discharged by an executable artifact that actually runs, and the
  record must state what the change reaches. Both checks below are new machinery this PR adds
  and runs once against representative fixtures — not a retroactive audit of history.

## Rationale

**Considered: a `## Generator` heading whose only requirement is non-empty content (the trap the
issue names verbatim) — rejected.** Any non-empty sentence satisfies "non-empty," including
`generator: not analyzed` restated in prose. That is exactly the symptom-fix-for-a-symptom-fix
the issue warns against building. Rejected in favor of a **structured, self-declared claim**
(`generator: fixed|deferred`, plus a required issue reference when `deferred`) — the same shape
`record_fulfils_diff` already uses for `fulfils:` lines (`gates.py:411-461`): not free prose, a
machine-parseable claim that at least has a checkable *shape*, even though — like `fulfils:` —
it cannot verify the claim's *truth*.

**Considered: verifying the linked issue number actually exists via `gh issue view` (network
call) inside `gates.py` — rejected for `gates.py` itself, accepted only at the `ci.py` PR-context
layer.** `gates.py`'s functions are called by the router without a network guarantee (its own
module docstring: "spec 없이 성립하는 검사만"; `record_fulfils_diff` and siblings do no network
I/O). Existing precedent for network calls at gate time lives in `ci.py` (`_pr_title`,
`_pr_head_ref`, both `subprocess`-calling `gh`). So the regex-shape check (`#\d+` present) lives
in `gates.py` for both callers; an *existence* check of the referenced issue via `gh issue view`
is added only in `ci.py`'s PR-context path, matching where similar network-dependent checks
already live. This still cannot verify the linked issue is *about* the same generator — stated
as the honest ceiling below, not silently dropped.

**Considered: skipping the orchestrator-chat half entirely, citing "conversation isn't a
deliverable file" — rejected.** The issue explicitly pre-empts this: #298 already establishes
the `Stop` hook makes conversational output inspectable, so "not mechanically reachable" is
unavailable as an answer for the orchestrator half specifically. A weaker, explicitly-labeled
heuristic is chosen instead of silence.

## What will be done

1. **`gates/gates.py`**: add `proposal_generator_section(d, cfg)`, modeled on
   `record_fulfils_diff`'s shape (fail-closed on anything unparseable, not "nothing to check"):
   - Scans changed files under `docs/issue-*/proposals/**` (reusing `changed_files()` /
     `_changed_records`-style filtering, generalized off `RECORD_PATH` to a sibling
     `PROPOSAL_PATH` regex).
   - Requires a `## Generator` heading. Missing heading → blocking message.
   - Requires, within that section, a **whole line** matching
     `^\s*generator:\s*(fixed|deferred)\s*$` (anchored per-line via `re.MULTILINE`, not a bare
     `re.search` substring match) — an after-proposal warrant hunt on this proposal (stance:
     bypass-the-gate) reproduced that an unanchored version matches the string `generator:
     fixed` anywhere in the section's prose, including inside a sentence that explicitly denies
     it ("It would be dishonest to write generator: fixed right now"). Anchoring to a standalone
     line closes that specific bypass; it does not make the claim harder to lie about on its own
     line, which is already conceded in "How you'll know it worked" below. Missing or
     unparseable → blocking message (fail closed, not "no claim to check" — mirrors
     `record_fulfils_diff`'s handling of an unparseable `fulfils:` line, `gates.py:454-460`).
   - When `deferred`, requires an issue reference matching `#\d+` elsewhere in the same section.
     Missing → blocking message naming exactly what's missing.
   - Register as `"proposal_generator_section"` in `ALL` (`gates.py:530`).
2. **`gates/ci.py`**: add `bad += gates.proposal_generator_section(repo, {})` to the same
   non-`--closes-only` check chain that already runs `record_enums` /
   `record_wellformed_in` / etc. (`ci.py:275-278`). Add a second, PR-context-only step (guarded
   the same way `_pr_title` is, only when `--pr` is given): for every `deferred` proposal
   changed in the PR, call `gh issue view <n>` for its referenced issue and block if the
   referenced issue does not exist (catches a fabricated/typo'd number — the one thing that is
   objectively checkable about a `deferred` claim without judging its content).
3. **`test_gates.py`**: unit tests calling `proposal_generator_section` directly (matching the
   existing per-function test style) — missing heading, empty section, missing `generator:`
   line, `deferred` with no `#N` reference, and the two passing shapes (`fixed`, `deferred` with
   a reference) all covered as separate cases.
4. **`on-the-record/hooks/generator-guard.sh`** (new `Stop` hook): reads the transcript path from
   the `Stop` payload, extracts the final assistant turn's text, and — only when `CLAUDE_ROLE` is
   unset (orchestrator session, mirroring `deliverable-guard.sh:17`) — fires a heuristic: if the
   reply contains 2+ enumerated items shaped like offered options (numbered list or repeated
   leading `-`/`*` bullets each starting a short clause) AND the substring "generator" (case
   -insensitive, either language's spelling as used in this repo's directives) appears nowhere in
   the reply, print a warning to stderr and exit 2 (block, matching `deliverable-guard.sh`'s
   deny pattern) — otherwise exit 0. Fail-open on any payload it can't parse (unlike the file
   gates): a `Stop` hook guessing at transcript shape from outside Claude Code's own hook docs
   must not brick every orchestrator turn on a schema mismatch it can't yet verify; this is
   recorded as a named limitation, not hidden.
5. **`on-the-record/hooks/hooks.json`**: register `generator-guard.sh` under `Stop`.
6. **`on-the-record/hooks/test_generator_guard.sh`**: fixture-driven test invoking the hook
   script directly with representative Stop-payload JSON (enumerated options + no "generator"
   mention → exit 2; enumerated options + "generator" mentioned → exit 0; ordinary prose → exit
   0; malformed payload → exit 0), run once and its actual output shown in the phase-2 record.

## Out of scope

- Verifying that a `fixed` claim is true, or that a `deferred` claim's linked issue is actually
  about the same generator — no mechanical check in this repo can do this; named explicitly as
  what the check does not catch, not silently dropped (per the issue's own instruction not to
  present a presence check as if it verified the analysis).
- Rewriting `proposal-shape-gate.sh` / the seven-section proposal-shape-directive — that lives in
  the `implementation-rulebook` plugin, a different repo this role has no write access to
  (see survey). If that plugin should also require `## Generator`, that is a separate proposal
  against that repo, named here so it isn't silently dropped.
- Making the `Stop` heuristic robust against rephrasing that avoids the enumerated-options shape,
  or against a reply that mentions "generator" without real analysis — both are named limitations
  of the chosen heuristic (see Rationale), not follow-up work bundled into this PR.
- Backfilling `## Generator` sections onto proposals that already merged (#297→#313, #140→#147,
  the six `closes-gate` PRs) — this gate is prospective; retrofitting history is not part of
  "does the generator still exist" for *this* fix's own generator (the check's absence), and
  bundling it would silently widen scope past what #363 asks.
- `docs/specs/write_scope.md` overrides for `gates/**` / `on-the-record/**` under the
  `implementation` role's default `write_scope` (`src/**`, `test/**`) — a pre-existing mismatch
  between the generic role write-scope and this repo's own root-level layout, unrelated to this
  issue, and currently inert since CI only runs `--closes-only` (`role_scope` isn't part of the
  required check today per `ci.py`'s docstring). Named so it isn't mistaken for silently fixed.

## How you'll know it worked

- `python3 -m pytest test_gates.py -k proposal_generator_section -v` passes, covering all six
  cases in item 3 above, output shown in the phase-2 record.
- `bash on-the-record/hooks/test_generator_guard.sh` passes, output shown in the phase-2 record.
- Manually re-running `gates/gates.py`'s new check against this very proposal file (which
  declares its own `## Generator` section below, `generator: fixed`) returns no blocking message
  — the check demonstrably reads the file it's shipped alongside, run once in phase 2.
- The phase-2 record states plainly, in prose, the two things this gate does not catch (claim
  truth for `fixed`; relatedness for `deferred`'s linked issue) and that the `Stop`-hook half is
  a keyword heuristic, not a semantic check — so the record itself cannot be mistaken for a claim
  that the analysis is verified.

## Generator

generator: fixed

The generator this issue names is a **structural absence**: no code path in this repo ever reads
a proposal's or an orchestrator reply's content for whether it names what produced the defect.
This proposal removes that absence by adding the only two write surfaces that can check it — the
general-purpose PR gate (`gates/gates.py` + `gates/ci.py`, which already runs against every
board-repo PR) and a new orchestrator-side `Stop` hook — rather than handling one more instance
of a symptom-only proposal by hand. It does not remove the softer generator behind it (that a
structured claim can still be filled in dishonestly, i.e. "generator: fixed" with no real fix) —
that residual is named explicitly in "How you'll know it worked" and "Out of scope" rather than
left implicit, per the issue's own instruction to say what the honest ceiling does not catch.
