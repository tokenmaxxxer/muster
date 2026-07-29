# Issue #87 — Phase 1 proposal: fix `_muster_resolve` fallback naming

files:
- `on-the-record/hooks/directive.sh`
- `on-the-record/hooks/self-update.sh`

(No other files in the write set — the phase-1 survey's repo-wide grep for
`_muster_resolve`, `TOKENMAXXXER_MUSTER`, `tokenmaxxxer/muster`, and
`.claude/tokenmaxxxer/muster` found no other live code referencing the old
naming; remaining hits are dated docs/reports that must stay as historical
record. See `docs/issue-87/reports/coding/survey.md`.)

## Request

Issue #83's rebrand sweep froze hook edits to the `mk=` marketplace-path
line, leaving the self-clone fallback in both hooks pointing at the old
`tokenmaxxxer/muster` slug. It only works today via GitHub's rename
redirect and has already produced a stale-named checkout on at least one
machine. Fix the fallback in both hooks: point the clone URL at
`tokenmaxxxer/on-the-record`, rename the fallback path to
`$HOME/.claude/tokenmaxxxer/on-the-record`, rename the `_muster_resolve`
function/variable and update comments accordingly, and handle an existing
old-path checkout so it isn't silently orphaned.

## Constraints

- Scope is limited to the fallback branch of `_muster_resolve` (the
  self-clone path) and its naming — the dev-override, plugin-root-ancestor,
  and marketplace-clone branches (the `mk=` line already fixed by #83) are
  unaffected and must not be touched beyond variable renames that flow
  through from the function rename.
- No behavior change outside what the issue asks: resolution order, the 4
  other resolution branches, and the calling code around `_muster_resolve`
  (error messaging aside from the muster->on-the-record text) stay as-is.
- Migration must be decided and documented, not left implicit — the issue
  offers three explicit options: prefer the new path, fall back to the old
  one if present, or move it.
- Historical docs/reports under `docs/` that mention "muster" are out of
  scope — they are dated records, not live naming to rebrand.
- Work-in-English policy: code, comments, commit message, and PR in
  English throughout.
- Phase 1 only: no code changes in this delivery. Phase 2 (actual hook
  edits) waits for approver Approve per contract v3 s19.

## What will be done (phase 2 preview — not executed in this delivery)

In both `on-the-record/hooks/directive.sh` and
`on-the-record/hooks/self-update.sh`:

1. Rename `_muster_resolve` -> `_checkout_resolve` (or equivalent
   non-muster name) and rename the `MUSTER` result variable -> `CHECKOUT`
   (or equivalent), updating every call site and every downstream use
   (`directive.sh:37,38,50,57-58`; `self-update.sh:31-32`).
2. Update the self-clone fallback's target variable
   (`own=$HOME/.claude/tokenmaxxxer/muster` at `directive.sh:30`,
   `self-update.sh:24`) to `$HOME/.claude/tokenmaxxxer/on-the-record`.
3. Update the clone URL
   (`https://github.com/tokenmaxxxer/muster.git` at `directive.sh:33`,
   `self-update.sh:27`, and the error-message copy at `directive.sh:42`)
   to `https://github.com/tokenmaxxxer/on-the-record.git`.
4. Update comments referring to "the muster checkout" / "muster" as the
   checkout name (`directive.sh:14-17,40,50`; `self-update.sh:8-11`) to
   refer to the on-the-record checkout instead.
5. **Migration for an existing old-path checkout**, per the issue's own
   options ("prefer the new path, fall back to the old one if present, or
   move it"): before doing a fresh `git clone` into the new path, probe
   the old path (`$HOME/.claude/tokenmaxxxer/muster`) for a `spawn.py` and
   use it if the new path doesn't already have one — i.e. *prefer the new
   path, fall back to the old one if present*. This mirrors the existing
   resolution order's own pattern (each branch is itself a "prefer X, else
   try Y" probe) and avoids re-cloning (network cost, and losing any local
   `git pull`-ed state) when a working old-path checkout already exists.
   No file-move / deletion of the old checkout is performed — moving or
   deleting a directory outside the hook's own responsibility carries more
   risk (partial state, permissions, concurrent hook runs) than leaving it
   in place and simply not preferring it once the new path is populated.

## Out of scope

- Any change to the dev-override, plugin-root-ancestor, or
  marketplace-clone resolution branches beyond variable renames that flow
  from the function rename.
- Rewriting historical `docs/` reports/proposals that mention "muster" —
  they are dated records of past work, not live naming.
- Renaming any test-fixture or unrelated "muster" string outside these two
  hook scripts (the survey's grep found none, so this is moot for issue
  #87, but stated for clarity per the issue-83 precedent of not touching
  unrelated fixture strings).
- Actually performing the file edits — this delivery is phase 1
  (survey + proposal) only.

## How success will be known

- The frozen write set stays exactly the two hook files listed above.
- After phase 2: `grep -rn muster on-the-record/hooks/` returns no hits.
- `grep -rn 'tokenmaxxxer/on-the-record' on-the-record/hooks/` shows the
  clone URL and fallback path in both hooks.
- `_muster_resolve`/`MUSTER` no longer appear as identifiers anywhere in
  the two hooks; the renamed function/variable are used consistently at
  every call site.
- The self-clone fallback, when the new path is absent but a working old
  path checkout exists, resolves to the old path without attempting a
  redundant clone (verifiable by reading the updated function logic;
  covered by any existing/added hook tests in phase 2).
- No behavior change to the other three resolution branches (dev override,
  plugin-root ancestors, marketplace clone).
