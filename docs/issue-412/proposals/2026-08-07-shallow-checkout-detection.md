---
status: proposed
files:
  - on-the-record/hooks/self-update.sh
  - on-the-record/hooks/test/self-update-shallow.bats
---

## Request
`self-update.sh`'s self-clone fallback can leave the checkout shallow
without telling anyone. A shallow checkout looks identical to a complete
one for every check that doesn't walk history — `git status` is clean,
`HEAD` is correct — but a history query (e.g. "is there a merge commit for
issue-N") silently returns a truncated, wrong answer instead of an error.
In the reported incident this produced 29 false "not merged" results. Fix
so a shallow checkout is either never produced by this hook's recovery
path, or is recorded somewhere the orchestrator will see before trusting
history.

## Constraints
- Must not add a network call on the hot path when the checkout is already
  complete (the hook runs on every SessionStart; it must stay fast and
  silent on the common case per its own header comment).
- Must not change the hook's fail-open behavior — offline failure is
  explicitly fine per the existing `trap`/`exit 0` design; this proposal
  adds detection, not a new hard failure mode.
- Must be testable without a real GitHub clone (network may be unavailable
  in CI/sandboxed runs) — the acceptance test uses a local fixture repo.

## Rationale
Considered making `git clone` itself impossible to produce shallow output
by pinning `--depth 0`-equivalent flags defensively, and stopping there.
Rejected as insufficient: the survey found no `--depth` flag on the
existing `git clone` call, so it's not shallow by construction from this
script's own code — the incident's shallow depth-1 result was not
reproduced by reading this file, meaning the truncation most likely
originates upstream of this clone call (an environment/tool-level shallow
default, or a different recovery path entirely) rather than in it. A
flag-only fix would not catch that class of cause and would leave the
orchestrator with the same blind spot: no evidence, after the fact,
whether the checkout it's about to trust is complete. Detecting and
recording shallowness after clone/pull — regardless of how it happened —
is the approach that actually satisfies the issue's stated acceptance bar
("a check that fails when the checkout is shallow... before a
history-dependent conclusion is about to be drawn"), so it's the one
proposed here, on top of (not instead of) confirming the clone call is
depth-unrestricted.

## What will be done
- After `_checkout_resolve` and the existing `pull -q --ff-only`, add a
  check: `git -C "$CHECKOUT" rev-parse --is-shallow-repository`. When it
  reports `true`, attempt `git -C "$CHECKOUT" fetch -q --unshallow` (bounded
  by the same offline-fail-open trap already in place). Whether the
  unshallow succeeds or not, write a one-line status marker file (e.g.
  `$CHECKOUT/.git/ON_THE_RECORD_SHALLOW` or a path under the checkout the
  orchestrator already reads) recording the shallow state and the outcome
  of the unshallow attempt, so any later history-dependent check can look
  for that marker before trusting `git log`/`rev-list` output — this is the
  "or must record that it did" half of scope item 1, made real rather than
  left to prose.
- Add `on-the-record/hooks/test/self-update-shallow.bats` (or an
  equivalent runnable shell test if bats isn't already the project's test
  harness — confirming that during phase 2) that: creates a local fixture
  git repo with multiple commits, shallow-clones it (`git clone --depth 1`)
  to simulate the incident, points `self-update.sh` at that shallow clone
  via `TOKENMAXXXER_CHECKOUT`, runs the hook, and asserts the marker file
  is written and/or the clone is no longer shallow afterward. This is the
  executable artifact #310 requires — not a description of the fix.
- Record item 2 (why the working directory disappeared) and item 3 (other
  history-dependent checks) as explicit searched-and-not-found entries in
  the phase-2 implementation record, per #358 — both are already surveyed
  in `docs/issue-412/reports/implementation/survey.md` and carry forward
  unchanged unless phase-2 execution turns up something the survey missed.

## Out of scope
- Reproducing or fixing the original "작업 디렉터리를 읽을 수 없습니다"
  working-directory disappearance — that upstream trigger is unexplained
  and not reproducible from this session; item 2 is discharged by the
  search record, not by a fix, unless phase-2 investigation finds the
  cause.
- Retrofitting shallow-detection into other checkout/clone sites outside
  `self-update.sh` — the survey found none in executable code today: if
  one is added later it inherits this obligation, but nothing else exists
  to change now.
- Changing `_checkout_resolve`'s existing path-resolution order or its
  other fallback branches (marketplace clone, old-path checkout) — only
  the final self-clone branch and the post-resolve check are touched.

## How you'll know it worked
- `on-the-record/hooks/test/self-update-shallow.bats` runs against a
  fixture shallow clone and demonstrably fails before the fix and passes
  after it — run, not reasoned about, per #416.
- Running `self-update.sh` against the real self-clone fallback path (or as
  close to it as a sandboxed/offline environment allows) and showing the
  resulting checkout's `git rev-parse --is-shallow-repository` is `false`,
  or that the marker file correctly reports `true` when it can't be fixed.
- The phase-2 record states, per #363, which generator (this hook's clone
  call) was addressed and whether the shallow state was eliminated at the
  source or only detected-and-recorded for this instance.
