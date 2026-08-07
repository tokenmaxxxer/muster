# Current-state survey — issue #289

## Scope

Sandbox-boundary defects reported from three live role sessions: home
dotfiles leaking into every workspace's `git status` (H1), and a
sandbox-denied write masquerading as a git lock (H2).

## H1 — home dotfile overlay

`issue_workspace()` (`spawn.py:2689`) is the single place that creates
every role workspace: a fresh `git clone -q <src> <work>` under
`~/.tokenmaxxxer/work/<repo>-issue-<n>-<role>/` (or `MUSTER_WORK_DIR`).
It already writes one entry to the clone's own
`.git/info/exclude` — the `.muster-cache/` line added right after clone
(`spawn.py:2743-2750`) — for exactly the same reason issue #289 names:
keep an operator/tooling artifact out of `git add`'s reach without
touching the repo's own tracked `.gitignore`. That is the precedent to
extend, not a new mechanism.

No code path currently writes entries for the dotfile set the issue
lists (`.bashrc`, `.bash_profile`, `.gitconfig`, `.gitmodules`,
`.claude/`, `.idea`, `.mcp.json`, `.profile`, `.ripgreprc`, `.vscode`,
`.zprofile`, `.zshrc`). The repo's own `.gitignore` (checked: root of
this repo) and `.git/info/exclude` (checked: this repo's own, not a
role workspace's) cover neither — confirming the issue's claim that "no
workspace `.gitignore` covers them" holds for the mechanism, not just
observed instances.

The overlay itself (why these paths show up as untracked inside a fresh
clone under a sandboxed session, when the same clone from outside the
sandbox does not show them) is a Claude Code Bash-sandbox filesystem
behavior, not something `spawn.py` controls — `protocol.md:4` already
documents this project's stance of accepting the sandbox as given
("Isolation — a sandbox, not a container") rather than reimplementing
it. That leaves the workspace-side exclude as the fix this repo can
make directly, matching the issue's own fallback framing ("if the
overlay is not ours to change — ensure every role workspace carries a
`.gitignore`/`.git/info/exclude`").

`git add -A`/`git add .` as a role-contract prohibition is a rulebook/
role-instruction concern — the text sessions receive at start (the
"role-handoff contract v3" seen in role sessions) is delivered by a
separately-cloned rulebook plugin (`spawn.py:275`, "룰북 clone"), not
authored in this repo. Grepped this repo for the contract's own source
text (`Never push to main`, `role-handoff contract v3`, `s13`) — it
does not live here; only per-issue *records* that quote it do
(e.g. `docs/issue-232/reports/implementation.md`). So the "forbid `git
add -A`" half of H1's fix direction is out of this repo's write set —
it belongs wherever that rulebook is authored. This repo's actionable
fix is the technical backstop (the exclude entries), which holds even
if a session ignores or never sees the contract-level prohibition.

## H2 — denied write masquerading as a git lock

`spawn.py` already has a refusal-classification layer built for exactly
this class of confusion: `_SANDBOX_REFUSAL_PATTERNS` (`spawn.py:1596`),
matched by `_classify_refusal_text()` (`spawn.py:1622`) against
tool-result text, feeding session-log events
(`gate-refusal`/`harness-refusal`/`sandbox-refusal`/
`unclassified-refusal`). Two patterns are registered today:
`Operation not permitted` and `haven't granted it yet`. Neither matches
git's own wording for a sandbox-denied lock-file create — git reports
that as `cannot lock config file .git/config: File exists`, an errno
translation (`EEXIST`) with no "permission"/"granted" vocabulary at
all. So the existing classifier — built for this exact defect class —
silently misses this specific manifestation; it would currently fall
through to `unclassified-refusal` or go unclassified entirely if no
`permission_denials` entry correlates.

This classification path is *post-hoc telemetry* (recorded to the
session's event log for `on-the-record` to read later) — it does not
put anything in front of the role session at the moment it hits the
error. The issue's H2 complaint is about the *in-session* moment: a
session saw the lock message, had no way to tell "sandbox denial" from
"real concurrent lock," and reflexively ran `rm -f
.git/config.lock`. Nothing in `spawn.py` or the rulebook (per the H1
finding above, rulebook text lives outside this repo) currently tells a
session what to do when it sees that message. `protocol.md` documents
the sandbox's filesystem boundary in the abstract (§4) but has no
line about this specific git/sandbox interaction.

Related precedent already in this repo: `allowUnsandboxedCommands =
False` (`spawn.py:536`, `protocol.md` invariant 7) exists specifically
to stop a different reflex — turning off the sandbox when a command
hits its boundary — for the same underlying reason issue #289 names
for H2 ("the same class ... unguarded here because the target is a
file, not the sandbox flag"). No equivalent guard exists for `rm` of a
git lock file today.

## Write-set implications

- `spawn.py` — `issue_workspace()` gains the dotfile exclude entries
  (extends the existing `.muster-cache/` pattern); `_SANDBOX_REFUSAL_PATTERNS`
  gains a pattern for git's lock-masquerade wording, so the existing
  telemetry layer classifies it instead of missing it.
- `test_spawn.py` — coverage for both additions, next to the existing
  `issue_workspace()`/refusal-classification test blocks already
  identified above.
- `protocol.md` — a line under §4 (or a new short subsection) naming
  the git-lock masquerade explicitly, so a session reading the contract
  has a documented "diagnose, don't delete" instruction. This is the
  only lever *inside this repo* that can reach a session's in-the-moment
  behavior, since the actual role-contract text is authored in the
  external rulebook (out of scope, per H1 above).

## Skip conditions

Not applicable — this is a design decision (which layer absorbs each
fix: workspace-creation code vs. documentation vs. an out-of-repo
rulebook), not a pure bugfix, and the spec (the issue) leaves the exact
split open. Scout (product/library research) does not apply — this is
an internal tooling defect in `on-the-record`'s own workspace-creation
and refusal-classification code, not a product-shaped surface with an
external category to benchmark against; skipping scout under the "no
design decision to benchmark externally" reading of the scout
directive.
