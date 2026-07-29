# Issue #87 — Phase 1 survey: `_muster_resolve` fallback fix

## Issue summary

Issue #83's rebrand sweep froze hook edits to the `mk=` line (marketplace
path), leaving the `_muster_resolve` fallback in
`on-the-record/hooks/directive.sh` and `on-the-record/hooks/self-update.sh`
still pointing at the old `tokenmaxxxer/muster` slug. It currently works
only via GitHub's rename redirect from `tokenmaxxxer/muster` to
`tokenmaxxxer/on-the-record`, which breaks if a new repo ever takes the old
name, and it has already produced a stale-named checkout on at least one
machine (`$HOME/.claude/tokenmaxxxer/muster`).

## Current fallback logic

Both hooks carry an identical `_muster_resolve` function (only the calling
code around it differs). Lines quoted from
`on-the-record/hooks/directive.sh`:

```
14  # Resolve the muster checkout (spawn.py lives at the repo root, OUTSIDE the
15  # plugin subtree — a cache install copies only orchestrate/, so the old
16  # plugin-root/../.. guess pointed at nothing there). Order: dev override,
17  # plugin-root ancestors, the marketplace clone, else self-clone.
18  _muster_resolve() {
19    if [ -n "${TOKENMAXXXER_MUSTER:-}" ] && [ -f "${TOKENMAXXXER_MUSTER}/spawn.py" ]; then
20      printf '%s' "${TOKENMAXXXER_MUSTER}"; return 0
21    fi
22    d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
23    probe="$d"
24    for _ in 1 2 3 4; do
25      probe="$(dirname "$probe")"
26      if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
27    done
28    mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
29    if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
30    own="$HOME/.claude/tokenmaxxxer/muster"
31    if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
32    mkdir -p "$(dirname "$own")" 2>/dev/null
33    git clone -q https://github.com/tokenmaxxxer/muster.git "$own" 2>/dev/null
34    if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
35    return 1
36  }
37  MUSTER="$(_muster_resolve || true)"
```

`on-the-record/hooks/self-update.sh` has the same function verbatim at
lines 8-30, called at line 31 (`MUSTER="$(_muster_resolve || true)"`) and
used at line 32 (`git -C "$MUSTER" pull -q --ff-only`).

Resolution order in both hooks (unaffected by this issue, kept as-is):
1. `TOKENMAXXXER_MUSTER` env override (dev override).
2. Walk up from the hook's own location looking for `spawn.py` (plugin-root
   ancestors) — up to 4 levels (`directive.sh:22-27`, `self-update.sh:16-21`).
3. `$HOME/.claude/plugins/marketplaces/tokenmaxxxer` (the marketplace clone;
   this path was already fixed by issue #83 — `mk=` line, `directive.sh:28`,
   `self-update.sh:22`).
4. Self-clone fallback — this is the part issue #87 targets:
   `own="$HOME/.claude/tokenmaxxxer/muster"` (`directive.sh:30`,
   `self-update.sh:24`), cloned from
   `https://github.com/tokenmaxxxer/muster.git` (`directive.sh:33`,
   `self-update.sh:27`).

## Current clone URL and fallback path (the two things to change)

- Clone URL: `https://github.com/tokenmaxxxer/muster.git`
  — appears at `directive.sh:33`, `self-update.sh:27`, and again in the
  user-facing error message at `directive.sh:42` (`git clone
  https://github.com/tokenmaxxxer/muster.git
  ~/.claude/tokenmaxxxer/muster`).
- Fallback path: `$HOME/.claude/tokenmaxxxer/muster`
  — appears at `directive.sh:30` (`own=`) and again in the same error
  message at `directive.sh:42`; and at `self-update.sh:24` (`own=`).

Both must become `tokenmaxxxer/on-the-record` (clone URL) and
`$HOME/.claude/tokenmaxxxer/on-the-record` (fallback path) per the issue
body.

## All occurrences of "muster" naming in the two hook scripts

Beyond the URL/path literals above, `directive.sh` and `self-update.sh`
each contain:

- Function name `_muster_resolve` (`directive.sh:18`, `self-update.sh:12`)
  and its 1 call site each (`directive.sh:37`, `self-update.sh:31`).
- Variable name `MUSTER` — the resolved-path variable
  (`directive.sh:37`, used again at `directive.sh:38,50,57-58`;
  `self-update.sh:31`, used again at `self-update.sh:32`).
- Comment header calling it "the muster checkout" (`directive.sh:14`,
  `self-update.sh:8`), and the general comment prose referring to "muster"
  as the checkout name in the resolution-order sentence
  (`directive.sh:14-17`, `self-update.sh:8-11`).
- `directive.sh` additionally prints "muster" in two user-facing strings:
  - The not-found note text: `[orchestrate] muster checkout not found and
    could not be cloned...` (`directive.sh:40`).
  - The orchestration directive body: `(muster at ${MUSTER})`
    (`directive.sh:50`).

`self-update.sh` has no other user-facing "muster" text (it runs quietly;
see its header comment at lines 2-4).

## Occurrences outside the two hook scripts (found via repo-wide grep)

Grepped for `_muster_resolve`, `TOKENMAXXXER_MUSTER`, `tokenmaxxxer/muster`,
and `.claude/tokenmaxxxer/muster` across the whole repo (excluding
`.git/`). Every other hit is historical documentation/reports, not live
code, and is **out of the write set** for this issue:

- `docs/issue-83/proposals/coding.md`
- `docs/issue-83/reports/coding.md`
- `docs/issue-83/reports/coding/survey.md`
- `docs/issue-40/reports/coding.md`
- `docs/issue-31/reports/qa.md`
- `docs/reports/2026-07-27-hunt-muster-portability-and-doc-refresh.md`
- `docs/reports/2026-07-27-hunt-remote-github-marketplace.md`
- `docs/proposals/2026-07-27-remote-github-marketplace.md`

These are dated records of past phase-1/phase-2 work and must not be
rewritten (rewriting history docs would falsify the record); they are
listed here only because the survey scope said "even if out of the write
set." A broader grep for the bare word `muster` (not just the specific
fallback identifiers) turns up nothing else beyond this list plus the two
hook scripts themselves — no other source file, config, or plugin manifest
references the old fallback naming.

## What an existing old-path checkout looks like, and what migration must handle

Per the issue's own description, this is not hypothetical: "[the current
fallback] has already materialized a stale-named checkout locally," i.e. on
at least one machine there is a real, already-cloned, already-`git pull`-ed
directory at `$HOME/.claude/tokenmaxxxer/muster` containing a working copy
of the `on-the-record` repo content (checked out under the old name because
`git clone` was pointed at the (redirected) old slug). It has:
- A `spawn.py` at its root (that's what `_muster_resolve` probes for).
- A `.git` directory whose `origin` remote is whatever URL was live at
  clone time (`https://github.com/tokenmaxxxer/muster.git`, which GitHub
  currently redirects to `tokenmaxxxer/on-the-record` transparently for
  fetch/pull, but not for `git clone`'s local-path naming).
- Possibly local uncommitted state is not expected here (self-update.sh
  only does `git pull -q --ff-only`), so the checkout should be safe to
  treat as disposable/replaceable, but the migration approach must not
  silently lose it without being decidable by the resolution order.

The issue body says migration must be decided and documented as one of:
"prefer the new path, fall back to the old one if present, or move it."
This survey does not pick one — that choice belongs in the phase-1
proposal (`## What will be done`) and must come from the issue body's own
language, not be invented here.

## Frozen write set (proposed, confirmed in proposal doc)

- `on-the-record/hooks/directive.sh`
- `on-the-record/hooks/self-update.sh`

No other source file needs to change; the grep above found no other code
occurrences.
