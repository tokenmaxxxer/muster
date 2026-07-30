# Issue #103 — Phase 1 Proposal: vocabulary-coherence test for wake-routing

Scout: skipped. This is an internal repo-tooling test with no external
product category to benchmark (a coherence check between this repo's
own routing code and its own role rulebooks); the one open design
decision (where the checked-against vocabulary lives) is resolved by
an internal constraint this survey found — `test_gates.py`'s existing
no-network rule — not by field research.

## files: (frozen write set)

- `test_vocab_coherence.py` (new, repo root, alongside `test_gates.py`
  and `test_spawn.py`): the coherence test itself.
- `docs/specs/loop-state-vocab.md` (new): declared `loop_state`/
  `verdict` vocabulary per role, with an explicit `scope-approved`
  human-only allowlist entry. This is the file the test checks
  `wakes.py`/`wake-routing.md`'s consumed literals against.
- `wakes.py`: comment-only — a pointer from the six exact-match
  literal comparisons (and the `scope-approved` gate check) to
  `docs/specs/loop-state-vocab.md` as their source of truth. No
  branch-logic change.

**Explicitly excluded from this write set:** any change to `_rows()`'s
conditions or return values, `roles/*.json` (registration metadata,
confirmed not the authoritative vocab source by this survey),
`test_gates.py`/`test_spawn.py` (untouched, new test is a separate
file), and the nine external role-rulebook repos (out of scope — they
live outside this repo; syncing `loop-state-vocab.md` to them is a
manual maintenance step this proposal names, not code this proposal
writes).

## Request (paraphrased intent)

Two live incidents came from `wakes.py`/`wake-routing.md` consuming a
state/field value that no rulebook actually produces: a free-text
`verdict` (issue #100, now fixed by write-time enum validation) and a
pre-approval gate requiring `scope-proposed` when the product
rulebook's vocabulary terminates at `decided` (controller #93). Build
a test that catches this class of gap at design time: cross-check
every state/field value `wake-routing.md`/`wakes.py` consume against
declared rulebook vocabularies, with an explicit human-only allowlist
for values no role produces by design (e.g. `scope-approved`). A
consumed value with no producer and no exemption fails the test.

## Constraints

- Must run with **no network and no GitHub access**, matching
  `test_gates.py`'s own stated rule ("네트워크·GitHub 없이 도는 것만") —
  the new test joins the same offline suite and must not silently
  require a rulebook clone to pass.
- Zero behavior change to `_rows()`/`wake_coding()` — this is a test
  addition plus a documentation source-of-truth, not a routing-logic
  change.
- The allowlist must be **explicit and named**, not a broad catch-all:
  each exempted value states which value, which consumer, and why it
  has no role-producer (mirrors `wakes.py`'s existing `HUMAN_ONLY`
  dict shape — same discipline, applied to the new test).
- Scope is literal state/field *values* consumed by exact-match
  comparison in `wakes.py` (`verdict`, `loop_state`) — not role names,
  not structural checks (`upstream`, `addressed_to` keys), matching
  the issue's own wording ("every state/field value... consume").

## What will be done (phase 2, after approval)

1. Add `docs/specs/loop-state-vocab.md`: a table of role -> declared
   `loop_state`/`verdict` values, seeded from what this survey already
   read out of the nine role rulebooks — `coding-agent-rulebook`'s
   `docs/specs/handoff-protocol.md` §5 is the only rulebook that
   currently declares a vocabulary at all (`proposed, approved,
   landed`), and it does not literally contain `scope-approved`/
   `scope-proposed`; the other eight rulebooks declare none. The doc
   records this state of the world honestly — including entries
   marked "not yet declared upstream" where a rulebook has no written
   vocabulary — rather than inventing vocabulary the rulebooks
   themselves don't state. A dedicated `## Human-only allowlist`
   section carries `scope-approved` with its producer ("a human, via
   the pre-approval gate — no role") sourced from `wakes.py`'s
   existing `HUMAN_ONLY` entry.
2. Write `test_vocab_coherence.py`:
   - Statically extract the consumed literals from `wakes.py` (the
     six exact-match comparisons plus the `scope-approved` gate
     check) — either by parsing the source with `ast` for the
     `=="..."` literal comparisons against `loop_state`/`verdict`
     lookups, or (if that proves brittle) a maintained explicit list
     colocated in `wakes.py` itself that the test imports directly,
     so the test breaks loudly if a new consumed literal is added to
     `wakes.py` without updating the list.
   - Load `docs/specs/loop-state-vocab.md`'s declared vocab per role
     plus its human-only allowlist.
   - Assert every consumed value is either in its producing role's
     declared set or in the allowlist; a value that is in neither
     fails with a message naming the value, the consuming call site,
     and that it has no producer and no exemption — mirroring
     `wakes.py.report()`'s own principle of never silently dropping
     an unresolvable line.
   - Runs offline: no `spawn.rulebook_dir()`/network calls at test
     time; the vocab doc is the sole input.
3. Add the `wakes.py` comment pointers (step above) — no logic change.
4. Run `python3 test_vocab_coherence.py` (and the existing
   `test_gates.py`) once to confirm the new test passes against
   current repo state and fails when a literal is deliberately
   mismatched (self-check, not a verification pass).

## Out of scope

- Auto-syncing `docs/specs/loop-state-vocab.md` from the live external
  rulebook repos (would reintroduce the network dependency this
  proposal explicitly avoids). Keeping the doc in sync when a
  rulebook's vocabulary changes is a manual step, named here, not
  automated by this change.
- Any change to the nine external role-rulebook repos themselves
  (e.g. adding a declared vocabulary to the eight that don't have
  one) — out of this repo's write set.
- Re-litigating controller #93's `scope-proposed`/`decided` gap or
  issue #100's write-time enum gate — both already addressed
  elsewhere; this test is meant to catch the *next* instance of the
  same class, not resolve those two specifically (though it will
  cover the `scope-approved` edge those incidents both touched).

## How you'll know it worked

- `python3 test_vocab_coherence.py` passes on current `main` after the
  vocab doc is filled in from this survey's findings.
- Temporarily changing one of `wakes.py`'s six literal comparisons
  (or the `scope-approved` check) to a value absent from both the
  vocab doc and the allowlist makes the test fail with a message
  naming that exact value and call site — confirming the test
  actually catches the class of gap issue #103 describes, not just
  that it runs green.
