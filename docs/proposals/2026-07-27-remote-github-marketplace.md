---
status: landed
files:
  - .claude-plugin/marketplace.json
  - README.md
  - README.ko.md
  - protocol.md
  - protocol.ko.md
---

## Intent

A consumer machine should be able to point at one place — `tokenmaxxxer/muster`
on GitHub — and get every role rulebook plugin from remote HEAD, without
cloning any of the nine rulebook repos by hand. Today `muster`'s own
`.claude-plugin/marketplace.json` lists exactly one plugin, `orchestrate`, with
a local relative `source: "./orchestrate"`. It does not mention any rulebook
plugin (`coding-cycle`, `qa-cycle`, `product-cycle`, …) at all — those are only
reachable by role-by-role fetch inside `spawn.py`, one role at a time, on first
spawn.

The end state: `claude plugin marketplace add tokenmaxxxer/muster` followed by
`claude plugin install <plugin>@tokenmaxxxer-muster` for any of the role
plugin sets resolves that plugin from its own GitHub repo (`{"source": "github",
"repo": "tokenmaxxxer/<repo>"}`) — the same one-marketplace, GitHub-source
pattern each rulebook already uses for itself, just aggregated in `muster` so
a consumer registers one marketplace instead of ten. Per the measured
behavior already documented in `README.md:86-95`, GitHub-sourced plugin
caches stay pinned at their installed version (`0.1.0`) — `claude plugin
update` does **not** refresh them; refreshing a GitHub-sourced rulebook goes
through `spawn.py update <role>` (or a reinstall). This new marketplace
listing is for **install-time resolution from remote**, not for keeping
installed plugins current via `claude plugin update`.

## Interface finding

Inspected the current source format and the spawn-time coupling to determine
whether this is purely a docs/marketplace-listing change or whether it also
touches how role sessions locate rulebook content at runtime.

- `muster/.claude-plugin/marketplace.json` (as it stands) lists only
  `orchestrate`, sourced `"./orchestrate"` (local relative path within this
  repo). No rulebook plugin appears in it.
- Every rulebook repo already has its own marketplace listing its own plugin
  set with local relative `source` paths (e.g.
  `coding-agent-rulebook/.claude-plugin/marketplace.json` lists `freelunch`,
  `terse`, `blueprint`, `no-mock`, `scout`, `no-footgun`, `doctrine`,
  `warrant`, `dispatch`, `coding-agent-env`, all `source: "./<name>"`). These
  are unaffected by this proposal — they stay local-relative for their own
  standalone/dev-clone use.
- `spawn.py`'s `rulebook_source()` (lines 66-77) already resolves each role's
  rulebook from GitHub when no matching local checkout exists: `_path(spec)` is
  tried first (an env-var-expanded local path, e.g.
  `$TOKENMAXXXER_RULEBOOKS/coding-agent-rulebook`; unresolved `$VAR` reduces to
  `""` and is treated as absent), and only if that directory's
  `.claude-plugin/marketplace.json` does not exist does it fall back to
  `{"source": "github", "repo": spec["repo"]}` from the role file (e.g.
  `roles/coding.json`: `"repo": "tokenmaxxxer/coding-agent-rulebook"`).
  `ensure_rulebook()` (lines 100-138) then warms that marketplace via a
  throwaway `--settings` file and `claude -p`, retried once, so a github-source
  role is fetched into `~/.claude/plugins/marketplaces/<name>` without any
  local clone ever existing. `README.md` (lines 66-95) documents this same
  path explicitly: "The rulebooks are **not** cloned by hand: each role file
  names its repo, and the first spawn of a role fetches that rulebook's
  marketplace [from GitHub]." `TOKENMAXXXER_RULEBOOKS` is documented as an
  **optional** dev override for working on a rulebook's own source locally,
  not a spawn-time requirement.

Conclusion: **`spawn.py` role-spawning already does not require local
rulebook clones today** — it is self-sufficient via each role file's `repo`
field, independent of `muster`'s own marketplace.json and independent of
whatever a consumer has separately `claude plugin install`-ed. This proposal's
job is narrower than "make spawning work remotely" (it already does): it is to
make `muster`'s **marketplace listing** — the thing `claude plugin install`
resolves against — also enumerate all nine rulebook plugin sets with GitHub
sources, so a consumer who wants to `claude plugin install <role>-cycle`
directly (browse/install/update via the plugin UI/CLI, outside of
`spawn.py`) can do it from one marketplace add instead of adding all ten repos
individually. It does not change how `spawn.py` itself locates rulebook
content at runtime.

## Constraints

> `muster`'s marketplace lists every role rulebook's plugins with a GitHub
> `source` (`{"source": "github", "repo": "tokenmaxxxer/<rulebook-repo>"}`),
> alongside the existing local `orchestrate` entry. Each rulebook repo's own
> marketplace.json is left untouched — it keeps local-relative sourcing for
> its own standalone/dev-clone use; this is a second, aggregating listing in
> `muster`, not a replacement. `spawn.py`'s role-resolution logic
> (`rulebook_source`, `rulebook_dir`, `ensure_rulebook`, `roles/*.json`) is
> unchanged — it already resolves each role's rulebook from GitHub via its own
> `repo` field when no local checkout exists, so nothing here needs to touch
> that code path to make remote installs work. The private-repo case is a
> consumer-side prerequisite (git/gh auth against `github.com/tokenmaxxxer/*`),
> not something this proposal can automate or work around.

## What will be done

- Extend `.claude-plugin/marketplace.json`'s `plugins` array with one entry
  per plugin found in each rulebook's own `marketplace.json`, each pointed at
  the matching repo under the `tokenmaxxxer` GitHub org via
  `{"source": "github", "repo": "tokenmaxxxer/<repo>"}`:
  - `tokenmaxxxer/coding-agent-rulebook`: `freelunch`, `terse`, `blueprint`,
    `no-mock`, `scout`, `no-footgun`, `doctrine`, `warrant`, `dispatch`,
    `coding-agent-env`
  - `tokenmaxxxer/qa-agent-rulebook`: `intake`, `testrun`, `bugreport`,
    `stats`, `regress`, `qa-cycle`, `signoff`, `qa-agent-env`
  - `tokenmaxxxer/product-agent-rulebook`: `product-cycle`, `product-agent-env`
  - `tokenmaxxxer/feasibility-agent-rulebook`: `feasibility-cycle`,
    `feasibility-agent-env`
  - `tokenmaxxxer/ops-agent-rulebook`: `ops-cycle`, `ops-agent-env`
  - `tokenmaxxxer/reflect-agent-rulebook`: `reflect-cycle`, `reflect-agent-env`
  - `tokenmaxxxer/review-agent-rulebook`: `review-cycle`, `review-agent-env`
  - `tokenmaxxxer/ux-design-rulebook`: `ux-design-cycle`,
    `ux-design-agent-env`
  - `tokenmaxxxer/verify-agent-rulebook`: `verify-cycle`, `verify-agent-env`
  - existing `orchestrate` entry (local `"./orchestrate"`) is kept as-is.
- Each new entry carries the plugin's `name` and `description` copied from its
  source rulebook's own `marketplace.json` (not re-derived), plus
  `"source": {"source": "github", "repo": "tokenmaxxxer/<repo>"}`.
- Update `README.md` / `README.ko.md` install sections to state: setup is
  `claude plugin marketplace add tokenmaxxxer/muster` followed by
  `claude plugin install <plugin>@tokenmaxxxer-muster` for whichever plugins a
  consumer wants directly installed; that this marketplace listing resolves
  the **install**, not ongoing updates — per the measured behavior already
  documented in `README.md:86-95`, GitHub-sourced plugin caches stay pinned
  at their installed version and `claude plugin update` does not refresh
  them, so refreshing goes through `spawn.py update <role>` (or a
  reinstall); and that this install path is a separate, optional path from
  `spawn.py`'s own per-role fetch (which needs no marketplace add at all — it
  warms its own marketplace registration on first spawn).
- Update `protocol.md` / `protocol.ko.md`'s install/marketplace section
  (`protocol.md` lines ~105-134) to note the same: `muster`'s marketplace now
  also lists the rulebook plugin sets by GitHub source, for consumers who want
  `claude plugin install` to resolve them directly rather than going through
  `spawn.py`'s automatic per-role fetch.
- State explicitly in the docs (this is a documentation fact, not a code
  change): **local clones via `TOKENMAXXXER_RULEBOOKS` are not required** for
  either `spawn.py` role-spawning (already GitHub-fallback by design, per the
  interface finding above) or for `claude plugin install` against `muster`'s
  marketplace after this change. `TOKENMAXXXER_RULEBOOKS` remains available
  purely as an opt-in local-dev override for working on a rulebook's own
  source without round-tripping through GitHub.

## Out of scope

- Changing any rulebook repo's own `.claude-plugin/marketplace.json` — each
  stays local-relative-sourced for its own standalone/dev-clone use.
- Making any of the nine rulebook repos public.
- The bootstrap script (or any change to how `TOKENMAXXXER_RULEBOOKS` itself
  is set).
- Any change to `spawn.py`, `roles/*.json`, or the role-resolution functions
  named above — they already resolve rulebooks from GitHub when no local
  checkout is present, and this proposal does not touch that code path.

## Success

On a machine that has run only `claude plugin marketplace add
tokenmaxxxer/muster` (no local clone of any rulebook repo, `git`/`gh` auth
already configured against the `tokenmaxxxer` org), `claude plugin install
<plugin>@tokenmaxxxer-muster` succeeds for every plugin newly listed in
`.claude-plugin/marketplace.json`, each resolving from its own GitHub repo.
`README.md`, `README.ko.md`, `protocol.md`, and `protocol.ko.md` describe this
install path accurately, including the explicit statement that local rulebook
clones are not required for it, and that refreshing an installed GitHub-sourced
plugin goes through `spawn.py update <role>` (or a reinstall) — none of these
docs claims `claude plugin update` refreshes GitHub-sourced plugin caches from
remote HEAD.
