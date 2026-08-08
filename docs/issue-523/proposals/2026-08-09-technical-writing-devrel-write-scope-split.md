---
status: proposed
files:
  - roles/technical-writing.json
  - roles/devrel.json
---

## Request

Follow-up C of #515: `roles/technical-writing.json` and `roles/devrel.json`
both declare `write_scope: ["docs/**"]` — an identical set. The only
distinguishing text lives in Korean prose (`decides`, `use_when`), which no
mechanical check reads. If both roles are spawned on one issue, their write
claims are indistinguishable at the `write_scope`/`files:` layer. Issue #523
asks to differentiate the two globs so each role's declared surface matches
what it actually decides — external-public docs authoring vs
external-developer adoption surfaces — encoded in the JSON itself, not
prose. No role merge or removal.

## Constraints

- Differentiate only; no role merge, removal, or rename.
- The distinction must be grounded in each role's existing methodology
  fields (`decides`/`use_when`/`produces`), not invented from scratch.
- Must satisfy both acceptance checks named in issue #523: the two
  `write_scope` sets must differ (`set(a) != set(b)`) and both be non-empty,
  and `scripts/check-write-set-conflicts.sh` must report no
  technical-writing/devrel overlap.
- Stay inside the doctrine-ladder docs layout as much as the existing
  precedent allows; `roles/knowledge-management.json`'s `docs/patterns/**`
  is the one pre-existing exception to the six-standing-bucket rule, and is
  out of this issue's scope to fix.

## Rationale

**Chosen approach**: give each role its own dedicated subdirectory under
`docs/`, following the precedent already set by `roles/architecture.json`
(`docs/issue-<n>/decisions/**`), `roles/incident-response.json`
(`docs/issue-<n>/postmortems/**`), and `roles/knowledge-management.json`
(`docs/patterns/**`) — every other role that writes docs already narrows to
a role-specific subtree instead of claiming all of `docs/**`.
`technical-writing` and `devrel` are the only two roles still claiming the
full tree, which is the actual root cause of the collision, not just a
missing tag.

**Alternative considered and rejected**: keep both roles on `docs/**` and
resolve the collision procedurally instead — e.g. rely on
`has_resolution_record()` in `check-write-set-conflicts.sh` (a written
resolution record permanently marks an overlap "RESOLVED" rather than
"CONFLICT"). Rejected because that mechanism is designed for two
*different issues'* proposals overlapping by circumstance and resolving it
once per pair; it does not fix the *roles' own contract* — every future
issue that spawns both roles together would regenerate the same
`write_scope` intersection and need a fresh resolution record. Issue #523
explicitly asks to fix this in the JSON contract, not defer it to a
per-issue procedural workaround.

**Alternative considered and rejected**: fetch each role's external
rulebook (`tokenmaxxxer/technical-writing-rulebook`,
`tokenmaxxxer/devrel-rulebook`) for a methodology-grounded split narrower
than "authoring vs adoption." Rejected for this phase: those marketplace
repos are not checked out in this sandbox and are outside the sandbox's
allowed network hosts, so a live methodology read isn't available; each
role's `decides`/`produces` fields (survey.md) already state the
distinguishing qualifier issue #523 names — "structuring what a reader
needs to know" vs "can a developer adopt this surface" — which is enough
to ground a disjoint split without inventing new methodology.

## What will be done

Phase 2 (after approval) narrows both roles' `write_scope`:

- `roles/technical-writing.json`: `write_scope` becomes
  `["docs/guides/**", "docs/issue-<n>/guides/**"]` — general external-public
  documentation surfaces (outlines, drafts, target-reader notes), matching
  its `decides` field.
- `roles/devrel.json`: `write_scope` becomes
  `["docs/devrel/**", "docs/issue-<n>/devrel/**"]` — developer-adoption
  surfaces (onboarding docs, sample-code framing notes, adoption-friction
  lists), matching its `decides` field.

The two sets are disjoint by construction (`guides` vs `devrel`
subdirectories), both remain non-empty, and both stay nested under `docs/`.

## Out of scope

- Fixing `roles/knowledge-management.json`'s pre-existing
  `docs/patterns/**` doctrine-ladder exception.
- Any change to the 34 roles with empty `write_scope`.
- Merging, removing, or renaming either role.
- Migrating any existing files currently under `docs/**` into the new
  `docs/guides/**` / `docs/devrel/**` subdirectories — no such files exist
  yet from either role (survey confirmed no prior technical-writing/devrel
  output on disk to migrate).

## How you'll know it worked

- `python3 -c "import json;a=json.load(open('roles/technical-writing.json'))['write_scope'];b=json.load(open('roles/devrel.json'))['write_scope'];assert set(a)!=set(b) and a and b"` exits 0.
- `bash scripts/check-write-set-conflicts.sh` reports no
  technical-writing/devrel overlap.
