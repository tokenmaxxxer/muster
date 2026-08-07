---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - protocol.md
  - protocol.ko.md
---

# Close the sandbox-boundary leaks from issue #289

## Request

Two sandbox-boundary defects observed across three live role sessions.
H1: home dotfiles (`.bashrc`, `.gitconfig`, `.mcp.json`, `.claude/`, and
others) show up as untracked in every role workspace's `git status`,
invisible from outside the sandbox — a plain `git add -A` would commit
the operator's `.mcp.json`/`.gitconfig` into a public repo, and no
workspace exclude file covers them today. H2: a sandbox-denied write
surfaces as git's `cannot lock config file .git/config: File exists`,
indistinguishable from real lock contention; one session reflexively
ran `rm -f .git/config.lock`, a move that corrupts `.git/config` against
a genuine concurrent lock, and left two sessions without upstream
tracking.

## Constraints

- The sandbox filesystem overlay that causes H1 is a Claude Code
  Bash-sandbox behavior, not something `spawn.py` implements or can
  turn off (`protocol.md` §4 already commits this project to accepting
  the sandbox as given). The fix has to be workspace-side, not
  overlay-side.
- The role-contract text sessions receive at start (forbidding `git add
  -A`, per the issue's own fix direction) is authored in a separately
  cloned rulebook plugin (`spawn.py:275`), not in this repo — this
  proposal cannot edit that text; the write set stays limited to what
  `on-the-record` itself controls.
- `issue_workspace()` already has one precedent for exactly this shape
  of fix: the `.muster-cache/` line it appends to the fresh clone's
  `.git/info/exclude` (`spawn.py:2743-2750`). Any H1 fix should extend
  that mechanism, not invent a second one.
- `_SANDBOX_REFUSAL_PATTERNS`/`_classify_refusal_text()`
  (`spawn.py:1596-1622`) is the existing post-hoc classifier for
  sandbox-vs-real refusals; it is telemetry (feeds session-log events
  for `on-the-record` to read later), not something a role session sees
  live. Any H2 fix through this path only closes the *telemetry* gap,
  not the *in-session* one.
- `allowUnsandboxedCommands = False` (`spawn.py:536`) is the existing
  guard against the sibling reflex ("sandbox denial → turn off the
  sandbox"); no code change should touch that switch, only add an
  analogous safeguard for the lock-file reflex.

## Rationale

**H1 — workspace-side `.git/info/exclude` entries vs. a shared repo-root
`.gitignore` template.** Considered shipping a `.gitignore` fragment or
template file that role rulebooks would be told to drop into target
repos. Rejected: it would depend on every target repo's rulebook
adopting it, is not `on-the-record`'s repo to edit, and does not help
existing repos that never re-run rulebook seeding. `.git/info/exclude`
is local to the workspace clone `issue_workspace()` already creates and
owns — the same reasoning issue #289 itself gives for accepting a
workspace-side exclude when "the overlay is not ours to change." It
also matches the `.muster-cache/` precedent already in the same
function, so the fix is one more line in an existing pattern instead of
a new one.

**H1 — no `git add -A`/`git add .` prohibition in this PR.** Considered
adding that prohibition somewhere in this repo (e.g. `protocol.md`).
Rejected: `protocol.md` documents the on-the-record/role boundary
contract, but the literal git-idiom instruction sessions act on at
commit time is the separately-cloned rulebook's role contract text
(confirmed in the survey: that text is not present anywhere in this
repo). Writing the prohibition into `protocol.md` would not reach a
session, since sessions are not shown `protocol.md` — they are shown
the rulebook's contract. Flagging this split explicitly here so it is
not silently dropped: the rulebook-side half of H1 is out of scope for
this repo and needs its own issue against wherever that rulebook is
authored.

**H2 — extend the existing classifier vs. build a new in-session
check.** Considered writing a Bash-tool wrapper or PreToolUse hook in
this repo that intercepts `git` commands and rewrites the lock error
live. Rejected for this pass: `on-the-record` does not own the role
session's tool-call path the way it owns workspace creation — hooks
that run inside a role session come from the target repo's own gate
scripts (per the survey: PreToolUse gates are per-target-repo rulebook
assets, e.g. `docs/issue-170/_assets/rulebook-skeleton/*/hooks/`), not
from `on-the-record`'s own code. Building a live interceptor here would
mean reaching into a surface this repo doesn't control, mirroring the
H1 rulebook-boundary problem. The two levers `on-the-record` does
control are: (a) the post-hoc classifier, extended so this exact wording
is recognized instead of falling through to `unclassified-refusal`,
which at minimum makes the failure legible in the session log
`on-the-record` reads afterward; and (b) `protocol.md`, which — unlike
the role rulebook contract — *is* authored in this repo and *is* the
document that states this project's sandbox-boundary stance (§4
already covers the general case). Adding the concrete git-lock
masquerade there, next to the existing `allowUnsandboxedCommands`
invariant, gives the next reader (human or session) a documented
"diagnose, don't delete" answer in the one place in this repo that
already carries that class of rule, even though it cannot force a
live session to read it.

## What will be done

- `spawn.py::issue_workspace()` — after the existing `.muster-cache/`
  exclude write, add entries for the dotfile set named in the issue
  (`.bashrc`, `.bash_profile`, `.gitconfig`, `.gitmodules`, `.claude/`,
  `.idea/`, `.mcp.json`, `.profile`, `.ripgreprc`, `.vscode/`,
  `.zprofile`, `.zshrc`) to the same `.git/info/exclude` file, reusing
  the existing dedupe-by-substring check pattern.
- `spawn.py::_SANDBOX_REFUSAL_PATTERNS` — add a pattern matching git's
  lock-masquerade wording (`cannot lock config file .*: File exists`,
  scoped to the `.git/config`-style message so it does not swallow
  unrelated "File exists" errors) so `_classify_refusal_text()` tags it
  `sandbox-refusal` instead of missing it.
- `protocol.md` / `protocol.ko.md` §4 — one short addition documenting:
  git reporting `cannot lock config file ...: File exists` inside the
  sandbox is usually a denied create surfacing as `EEXIST`, not a real
  lock; a session should check for the file from outside the sandbox
  (or via `on-the-record`) before removing anything, and never `rm` a
  `*.lock` file as a first response.
- `test_spawn.py` — one test asserting the dotfile set lands in
  `.git/info/exclude` after `issue_workspace()` runs (alongside the
  existing `.muster-cache/` coverage identified in the survey), and one
  test asserting `_classify_refusal_text()` returns `sandbox-refusal`
  for the git lock-masquerade wording.

## Out of scope

- Changing or disabling the Claude Code sandbox's filesystem overlay
  itself — not `on-the-record`'s to change (per Constraints).
- Prohibiting `git add -A`/`git add .` in the role contract text — lives
  in the separately-cloned rulebook, outside this repo's write set;
  flagged above as a gap needing its own issue against that rulebook.
- A live, in-session interceptor that rewrites or explains the git lock
  error at the moment it happens — would require hooking a surface
  (role-session tool calls) that this repo does not own; the rulebook's
  own PreToolUse hooks are the right layer for that, not `spawn.py`.
- Any change to `allowUnsandboxedCommands` or other sandbox switches in
  `role_settings()` — this proposal only adds a sibling safeguard for
  the lock-file reflex, it does not touch the existing one.

## How you'll know it worked

- `test_spawn.py` passes, including the two new tests: dotfile exclude
  entries present after `issue_workspace()`, and the lock-masquerade
  message classified as `sandbox-refusal`.
- Manual check: a fresh `issue_workspace()` clone's
  `.git/info/exclude` lists all twelve dotfile paths from the issue,
  so `git status`/`git add -A` in that workspace does not surface or
  stage them.
- `protocol.md` and `protocol.ko.md` both carry the new git-lock note
  under §4, in sync with each other (matching this repo's existing
  practice of keeping the two files parallel).
