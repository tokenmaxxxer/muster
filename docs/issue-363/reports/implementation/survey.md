SKIP CONDITION: neither skip clause applies. This is not a pure bugfix (no single defective
line is named) and the spec leaves real design decisions open — issue #363 poses three
unresolved questions ("Where a proposal states its generator analysis", "Whether an
instance-only fix can be approved without a linked issue", "Whether this binds the
orchestrator's conversational proposals too") and explicitly warns that the obvious answer
(a presence-only `## Generator` heading check) is itself a symptom fix. Scout's field-research
protocol therefore does not have a product/library exemplar to sweep for — the "field" here is
this repo's own gate machinery and its existing self-referential mechanisms (`fulfils:`,
`record_enums`, `record_fulfils_diff`) — so scouting is done as a read of that prior art
in-repo, not a web sweep (see gaps below).

## Current state (verified by reading, not just the issue text)

- No mechanism in this repo checks a proposal document's **content** at all. `gates/gates.py`'s
  `ALL` registry (`gates.py:530`) exposes only `writeset`, `deps`, `record_enums`,
  `record_wellformed`, `record_no_tool_residue`, `record_fulfils_diff` — every one of these
  targets `docs/issue-<n>/reports/<role>.md` (`RECORD_PATH`, `gates.py:43`), the phase-2
  *record*, never `docs/issue-<n>/proposals/**`. Proposal files are only ever referenced as a
  **write-scope path** (`_always_writable`, `gates.py:474`: `"docs/issue-*/proposals/**"`) —
  something a role is *allowed* to write, with zero content requirement. This confirms the
  issue's claim precisely: "Acceptance criteria are not currently required to mention the
  generator at all" — literally true; there is no code path that reads a proposal's prose.
- The `proposal-shape-directive` / `proposal-shape-gate.sh` referenced in this session's own
  system reminders (seven required sections, `## Rationale` naming a rejected alternative) is
  **not part of this repo**. It is a PreToolUse hook shipped by a different plugin (the
  `coding`/`implementation` rulebook plugin, `$TOKENMAXXXER_RULEBOOKS/implementation-rulebook`,
  per `roles/implementation.json:3`), which this checkout does not contain and this role has no
  write access to (`write_scope: ["src/**", "test/**"]`, `roles/implementation.json:8`, plus
  `_always_writable`'s record/proposal-path carve-out — neither covers a *rulebook plugin's own
  hook scripts*). So a "## Generator" requirement enforced only at that layer would live outside
  this issue's reachable write set. `gates/gates.py` + `gates/ci.py`, by contrast, are this
  repo's own general-purpose CI gate, already invoked against arbitrary board-repo PRs
  (`gates/ci.py`'s `check()` call chain, `ci.py:270-278`) via `--pr`/`--issue`/`--autodetect`,
  and already the place where a *record's* self-declared claim gets cross-checked against
  something objective (`record_fulfils_diff`, `gates.py:411-461`: a `fulfils: delete|create|move
  <path>` line is verified against the actual commit diff, not just required to be present). This
  is the load-bearing precedent for this issue's own trap warning: a presence check is
  worthless, a **claim cross-checked against something the author cannot fully control** is not.
- `gates/gates.py:26` (`PROTECTED_ROOT_DIRS = {"roles", "gates", "agents", "images",
  "profiles"}`) — `gates/` itself is a protected root dir. Any change to `gates/gates.py` or
  `gates/ci.py` trips `is_protected()` (`gates.py:59-69`), which — per `is_protected`'s callers
  — routes to mandatory human review rather than mechanical approval. This is expected and
  correct for changing enforcement machinery, not a defect to route around; noted as a
  constraint for the proposal.
- `on-the-record/hooks/hooks.json` currently wires exactly three hook events for the
  orchestrator session: `SessionStart` (self-update), `UserPromptSubmit` (`directive.sh`,
  injects the standing directives visible in this very session's system reminders), and
  `PreToolUse` on `Write|Edit|MultiEdit|NotebookEdit` (`deliverable-guard.sh`, denies the
  orchestrator writing into a target repo's `src/`/`test/`/`docs/`). **There is no `Stop` hook
  registered anywhere in this repo.** Issue #363 references "the Stop hook" as something #298
  already established makes "the orchestrator's own conversational output inspectable" — that
  claim is about the *general Claude Code hook surface* (any session, including the
  orchestrator's, can register a `Stop` hook that receives the session transcript), not about
  something already wired here. Confirmed by reading `.claude-plugin`-adjacent hook wiring
  across the repo (`grep -rln "Stop\b"` over `*.py`/`*.json`/`*.md` outside `docs/issue-*`
  returns nothing) — the capability exists at the harness level; this repo has simply never used
  it. So "not mechanically reachable" genuinely is unavailable as an excuse (the plumbing point
  stands), but "already built" is equally false — a `Stop` hook here would be new machinery, not
  a rewire of existing machinery.
- `docs/issue-282/proposals/` (`plan.md`) and `docs/issue-155/proposals/`
  (`2026-07-31-coding-fulfils-marker-gate.md`) are the two most recent proposals in this repo
  that both (a) touched `gates/gates.py` + `gates/ci.py` and (b) shipped a paired
  `test_gates.py` change — read as the shape template for this issue's own proposal (frontmatter
  style, `files:` line, six-section body, `## How you'll know it worked` naming a runnable
  `pytest -k` invocation).
- `test_gates.py` exists at repo root (`test_gates.py`, 1 file) and already has direct-call unit
  tests per gate function (not through the CLI) — the pattern this issue's new check's tests
  will follow.

## Gap this proposal must close

The honest ceiling, read against `record_fulfils_diff`'s precedent: a mechanical gate can check
that a proposal's `## Generator` section (a) exists, (b) is non-empty, (c) contains a
machine-parseable `generator: fixed|deferred` declaration, and (d) when `deferred`, contains an
issue-number reference (`#\d+`) alongside it — the same shape `fulfils:` uses (a self-declared,
structured claim, not free prose). What it categorically cannot check, and must say so: whether
the named generator is *actually* the generator, whether a `fixed` claim is true, or whether a
`deferred` claim's linked issue is actually about the same generator rather than an unrelated
number typed in to satisfy the regex. That is `record_fulfils_diff`'s own ceiling too — it
verifies the claim against the diff shape, never against whether the *reasoning* behind the
claim is sound.

For the orchestrator's conversational half (issue's decision point 3): no prior art in this repo
to lean on — this would be new `Stop`-hook machinery. The honest ceiling there is weaker still:
a `Stop` hook receives the transcript, but distinguishing "an offer of symptom-only options" from
ordinary prose is a genuine language-understanding task no regex performs reliably. A keyword
heuristic (fire only when the reply enumerates 2+ items shaped like a choice, e.g. numbered or
bulleted options, and the word "generator" appears nowhere in the reply) catches the exact shape
that triggered this issue (a "wait, or spend a session rewriting bodies" two-option message) but
is trivially defeated by rephrasing as flowing prose, or satisfied by dropping the word
"generator" into an otherwise-unanalyzed reply. This must be stated plainly in the proposal
rather than presented as if it verifies the analysis — which is exactly the trap the issue names.
