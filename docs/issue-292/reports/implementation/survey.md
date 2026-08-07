# Current-state survey — issue-292

## What the issue actually asks

Three acceptance items:
1. A role session can run a one-shot verification command without a permanent
   refusal, or gets a documented sanctioned alternative the contract points to.
2. The scratch-file-script indirection is either unnecessary or blocked — not
   both available and discouraged.
3. Every harness refusal reaching the event log names what was refused,
   untruncated.

## What this repo can and cannot touch

`.claude/settings.json` (the actual Bash sandbox/permission engine that emits
"Contains command_substitution" / "requires approval") is outside this
session's write access (sandbox denies writes to it), and more fundamentally
it is a Claude Code CLI product feature, not code this repo owns. on-the-record's
own hooks (`on-the-record/hooks/*.sh`) do not add the compound-Bash refusal —
grepped for `command_substitution`/`multiple operations`/`cannot be statically
analyzed` across the repo; the only hits are in `spawn.py` (the refusal
*classifier*, which reads these strings out of session logs after the fact)
and two prior proposal docs (`docs/issue-235`, `docs/issue-246`) about that
same classifier. Confirmed via `grep -rl` over `.json/.py/.sh/.md`, no hits
in `on-the-record/hooks` or `gates/`.

So items 1 and 2 cannot be discharged by changing enforcement code in this
repo — there is none to change. They can only be discharged by protocol
documentation: telling role sessions what a sanctioned one-shot verification
command looks like (single Bash calls, no chaining/substitution — the same
constraint this very session was launched under, per its own HARNESS note),
and stating plainly that the scratch-file-script route is not a sanctioned
workaround.

Item 3 is a real, local code defect: `spawn.py:1729`
(`_flush_correlated_refusals`) truncates the unclassified-refusal fallback to
`str(denials)[:200]`. This is exactly the "truncated mid-`repr()`" defect the
issue and its comment describe, and it is inside this repo's write set.
Contrast: `_classify_refusal_text` (spawn.py:1663-1696) already normalizes and
caps classified detail at 300 chars — that path names a gate/harness/sandbox
label plus reason, so 300 chars of a single message is a deliberate size
bound, not the failure mode the issue describes. The failure mode is
specifically the *unclassified* fallback, which stringifies the whole
`denials` list and hard-truncates it — mid-repr, no gate name, no way to see
what was actually refused.

## Existing related work

- `docs/issue-235/proposals/refusal-classifier-corroboration.md` and
  `docs/issue-246/proposals/refusal-classifier-residual-fixes.md` — prior
  work on the same three-layer refusal classifier in `spawn.py`. Both
  predate this issue's truncation complaint; neither touches the 200-char
  cap at line 1729.
- `protocol.md` §4 documents the Bash sandbox's capabilities
  (`network.allowedDomains`, `filesystem.denyRead/allowWrite`,
  `credentials.envVars`) but says nothing about compound-command refusals or
  a sanctioned verification pattern for headless sessions — that gap is what
  item 1 needs filled.
- No `docs/issue-286` or `docs/issue-331` directory exists in this repo
  (checked `ls docs`); those are cross-repo issue references in #292's body
  and comment, not local docs to update.

## Write set this proposal will actually touch

- `spawn.py` — remove/replace the 200-char truncation in
  `_flush_correlated_refusals`'s `unclassified-refusal` fallback so the full
  denials payload reaches the event log.
- `test_spawn.py` — a regression test asserting the fallback event is not
  truncated.
- `protocol.md` — add a short section stating the sanctioned one-shot
  verification pattern for headless role sessions (single, non-compound Bash
  calls — no `&&`/`;`/`$()`/pipes needing shell parsing beyond what the
  sandbox statically allows) and stating that writing the same command to a
  scratch file and executing the file is not a sanctioned substitute for a
  refused inline command.

## Alternatives considered (for the proposal's Rationale)

- Loosen the harness's own permission rules to allow inline compound Bash —
  not available: that ruleset lives in Claude Code's own sandbox
  configuration, not in a file this repo's write set can reach.
- Block the scratch-file route mechanically (e.g. a PreToolUse hook in
  `on-the-record/hooks/` that refuses `Write` to scratch paths followed by
  `Bash` execution of that path) — considered and rejected for this
  proposal; see the proposal's Rationale section.
