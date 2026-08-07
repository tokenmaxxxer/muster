---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - protocol.md
---

## Request

Headless role sessions get permanently refused when they try to run a
one-shot verification command with compound Bash syntax, and route around
the refusal by writing the same command to a scratch file and executing the
file instead — which defeats the rule without adding safety. Separately,
when a refusal cannot be classified into a known layer, the event log
truncates the raw denial payload mid-`repr()`, so an operator cannot see
what was actually refused.

## Constraints

- The actual Bash-sandbox permission engine that emits "Contains
  command_substitution" / "requires approval" is a Claude Code CLI product
  feature, not code in this repo's write set — `.claude/settings.json` is
  outside this session's write access and outside this repo's ownership.
  Any fix here has to work by documenting a sanctioned pattern for role
  sessions, not by editing the enforcement engine itself.
- This session itself is running under exactly the constraint at issue: one
  command per Bash call, no chaining. The sanctioned pattern this proposal
  documents has to be something this session can and does follow, not a
  theoretical prescription.
- `spawn.py`'s refusal classifier already has two prior rounds of fixes
  (issue-235, issue-246) touching the same functions; the truncation fix
  must not regress the dedup/correlation logic those rounds built.

## Rationale

Considered mechanically blocking the scratch-file-script indirection with a
new PreToolUse hook in `on-the-record/hooks/` (deny `Write` to a scratch path
immediately followed by `Bash` execution of that same path). Rejected: it
cannot distinguish a role session using scratch space legitimately (writing
a fixture, a test file, a report draft — sanctioned uses documented all over
this repo, e.g. the scratchpad directory convention) from one using it to
smuggle a refused inline command. A path-and-timing heuristic would either
miss the smuggling case (session writes the file, waits, runs it later) or
false-positive on ordinary scratch use — worse than the status quo. The
issue's own acceptance criterion offers a cleaner second branch: "or is given
a documented sanctioned alternative that the contract points to." Since the
first branch (loosen the harness) is unavailable per the Constraints above,
this proposal takes the second branch — document the sanctioned alternative
(single non-compound commands; `--body-file`-style flags in place of
`$(cat <<EOF)` where the tool supports one) directly in `protocol.md`, and
state plainly that the scratch-file-script route is not a substitute for a
refused inline command. That closes the "both available and discouraged"
gap the issue names, without a heuristic hook that would misfire on
legitimate scratch use.

For the truncation defect, considered leaving the 300-char cap that
`_classify_refusal_text` already applies to classified detail and just
raising the unclassified fallback's cap to match (e.g. 300 instead of 200).
Rejected: the issue's acceptance criterion says "untruncated," not "a bigger
number" — a fixed cap on the *unclassified* fallback is exactly the failure
mode reported (mid-`repr()` truncation hiding what was refused), and unlike
the classified path this fallback has no gate/harness/sandbox label to make
a capped snippet still useful. Removing the cap for this one fallback event
is the direct fix; the classified-path caps (300 chars, already carrying a
label) are untouched.

## What will be done

- `spawn.py`: in `_flush_correlated_refusals`, change
  `_append_event(events_path, "unclassified-refusal", str(denials)[:200])`
  to log the full `str(denials)` with no truncation.
- `test_spawn.py`: add a regression test that constructs a `denials` list
  long enough to have been cut by the old 200-char cap, drives it through
  `_flush_correlated_refusals`, and asserts the resulting event's detail
  contains the full un-truncated content.
- `protocol.md`: add a short subsection (near §4's sandbox description)
  stating the sanctioned one-shot verification pattern for headless role
  sessions — single, non-compound Bash calls; tool-native flags
  (`--body-file`, argument files) in place of shell substitution where the
  refused command has one — and stating explicitly that writing the refused
  command to a scratch file and executing the file is not a sanctioned
  workaround.

## Out of scope

- Any change to `.claude/settings.json`, Claude Code's own sandbox/
  permission engine, or any other file outside the frozen write set above —
  none of it is reachable from this repo.
- Mechanically blocking the scratch-file route via a new hook — rejected
  above; not attempted.
- Retroactively re-labeling past `unclassified-refusal` events already in
  existing event logs — this fixes new events going forward only.
- The 300-char caps in `_classify_refusal_text` for already-classified
  refusals — untouched, out of scope for this issue's truncation complaint.

## How you'll know it worked

- `python3 test_spawn.py` passes, including the new regression test, and
  fails against the pre-fix `spawn.py` (i.e. the test actually exercises the
  truncation).
- Reading `protocol.md` after the change, a role session hitting a compound-
  Bash refusal has a documented sanctioned alternative to follow instead of
  writing to scratch and executing the file.
