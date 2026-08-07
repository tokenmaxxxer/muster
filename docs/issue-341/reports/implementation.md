---
code_under_review:
  - test_gates.py
  - docs/issue-341/reports/implementation.md
loop_state: phase-2-complete
---

# Issue #341 — Phase 2 record (implementation)

## What was done

1. Added `t_spawn_has_no_concurrency_limit()` to `test_gates.py` — a
   regression test that reads `spawn.py`'s source and asserts it
   contains no concurrency-limiting construct (`Semaphore`, `Lock(`,
   `Queue`, or a `MAX_CONCURRENT`-shaped constant) anywhere. This pins
   the falsifiable fact the incident turned on: `spawn.py` imposes no
   limit on simultaneous session spawns.

2. This record, stating the mechanical-enforceability verdict for the
   general claim in #341.

## Mechanical-enforceability verdict (issue's own escape hatch)

The issue's general rule — "every orchestrator-stated constraint names
its enforcer" — is **not mechanically enforceable today**, for the
reason the survey and proposal already traced and this record
confirms by having actually looked, again, at commit time:

- Orchestrator conversational turns (the "슬롯 대기" prose from the
  incident) are not a git-tracked artifact. `gates/gates.py` is
  diff-based (`git diff --name-status` against `origin/main...HEAD`,
  fail-closed when unreadable) — it has nothing to diff when the
  claim in question was never committed anywhere.
- The Mission Board is recomputed fresh every render, never stored.
  The GitHub issue body's Execution Plan block has no field for ad hoc
  capacity claims. `runs/ledger.jsonl` is a spawn/exit accounting log,
  not a claims log — **and it does not exist in this checkout**: I ran
  `find . -iname 'ledger.jsonl'` and `git log --all --diff-filter=A --
  '**/ledger.jsonl'` from the repo root and both returned nothing.
  `runs/` itself is listed in `.gitignore` (confirmed:
  `grep -n '^runs' .gitignore` → `runs/`), so absence in this clone is
  expected regardless of whether any live instance has ever created
  one — this is a fact about `.gitignore`, not a fact about whether the
  mechanism could exist.
- A keyword/regex gate scanning orchestrator output was considered and
  rejected in phase 1 (see the proposal's Rationale) because there is
  no committed artifact to scan, and per `gates/gates.py`'s own stated
  design principle ("불확실하면 막는다") a gate that must guess at
  natural-language intent is disqualified by the project's own
  gate-design doctrine, not merely inconvenient to build.

Closing this gap for real would require making orchestrator
constraint-claims a committed, structured artifact first (sketched,
not built, in the proposal's second rejected alternative), and then
something that *forces* every constraint-shaped utterance through that
channel — an open design question about the orchestrator/board
protocol itself, out of this issue's write set per the approved
proposal. Left to the user as a follow-on issue; not decided here.

## #330 reach-beyond-acceptance note

The regression test's actual guarantee is narrower than #341's title:
it guards `spawn.py` against ever silently *acquiring* the exact
invented constraint from this incident (a real concurrency limiter
landing with no accompanying decision record). It does **not** guard
against the orchestrator *saying* something false about a limit in
chat — that claim-checking gap is exactly the part this record's
verdict above states is unenforced, not solved. A reader should not
conclude from the test passing that #341's general problem is closed.

## What did not work

None — no dead ends this phase; the approach matched the phase-1
proposal exactly (grep-based assertion against `spawn.py`'s source,
no committed claims artifact existed to build against, confirmed
again above).

## Acceptance run

```
$ python3 test_gates.py
  ok  t_slug_is_directory_name
  ...
  ok  t_spawn_has_no_concurrency_limit
  ...
  ok  t_rename_bypass
Traceback (most recent call last):
  ...
OSError: [Errno 30] Read-only file system: '/home/jwjung/.tokenmaxxxer/trusted-repo-config.json'
```

58 tests pass, including `t_spawn_has_no_concurrency_limit` (isolated run
also confirmed green: `python3 -c "import test_gates;
test_gates.t_spawn_has_no_concurrency_limit()"` → `ok`). The suite then
hits `t_repo_local_claude_config_stops_the_spawn`, which fails in this
sandbox because it writes to `~/.tokenmaxxxer/trusted-repo-config.json`
and this sandbox's `$HOME` is read-only outside the allowed write paths
— a sandbox-filesystem limitation, not a regression from this change:
confirmed by `git stash`-ing this change and re-running the unmodified
suite, which fails at the exact same test with the identical
`OSError`. This is the real, unresolved result — reported as-is per
#334, not silently treated as a pass.

## Doctrine ladder

- No env var, dependency, migration, or public-signature change in
  this phase — nothing to place on the handbook/decisions/reports
  ladder beyond this record itself.

## Hunt

No hunter dispatch this phase-2 turn: the warrant-directive's hunter
protocol is a separate proposal-track mechanism (`docs/proposals/`,
`.warrant-hunt.count`) that this issue does not use — #341 runs under
role-handoff contract v3's phase-1/phase-2 PR gate instead, which has
its own dispatch point (end of phase 1, already run per the
system-reminder's cadence note) and no equivalent before-landing slot
defined for this contract. Recorded per contract's "record a section
even when nothing is found."

## Open findings

None.

## Next steps

None — #341's write set (per the approved phase-1 proposal) is fully
delivered: the regression test and this record. The unenforceable
general-claim gap and the ledger-flag design question are explicitly
left to the user as separate follow-on issues, not tracked as
outstanding work in this record.
