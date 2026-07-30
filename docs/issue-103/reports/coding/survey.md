# Issue #103 — current-state survey

## Write set (projected)

- `test_vocab_coherence.py` (new): the coherence test. Standalone file,
  same style as `test_gates.py` (`t_*` functions, `python3
  test_vocab_coherence.py` runner, **no network** per that file's own
  header rule).
- `docs/specs/loop-state-vocab.md` (new): this repo's own record of
  each role's declared `loop_state`/`verdict` vocabulary and its
  producer, plus the human-only allowlist. The test reads this file
  as its source of truth rather than reaching over the network into
  the nine external rulebook repos at test time (see gap below).
- `wakes.py`: comment-only, pointing the consumed-literal call sites
  at the new vocab doc as their source of truth — no branch-logic
  change.
- `docs/specs/wake-routing.md`: none required if the new vocab doc is
  additive, but may need a one-line cross-reference in "Board
  vocabulary this doc uses" — kept a possible-not-certain item for
  phase 2, not frozen into files: below.

## What's already there

- `wakes.py._rows()` consumes exactly six state-value literals by
  exact string compare:
  - `roles["feasibility"]["verdict"] == "go"`
  - `roles["qa"]["loop_state"] == "handed-off"`
  - `roles["ux-design"]["loop_state"] == "reviewed"`
  - `roles["verify"]["loop_state"] == "cleared"`
  - `roles["review"]["loop_state"] == "reported"`
  - `roles["coding"]["loop_state"] == "landed"`
  - `state == "scope-approved"` inside `wake_coding()` (the
    pre-approval gate, `_rows()` line ~267)
  - `roles["coding"]["loop_state"]` in general (existence check, not
    a value compare)
- `docs/specs/wake-routing.md` restates the same values in prose
  (`scope-proposed`, `scope-approved`, `landed` as examples) and
  already carries a `HUMAN_ONLY` dict in `wakes.py` that documents
  `scope-approved`'s producer as "a human reading `scope-proposed`
  and approving it — no role can self-approve." This is the existing
  human-only exemption pattern issue #103 asks the new test to make
  explicit and enforced, not something to invent from scratch.
- `roles/<role>.json` (9 files, this repo) do **not** declare
  `loop_state` vocab formally. Their `produces` field is free-text
  and only loosely echoes some values (`ux-design.json` mentions
  "reviewed" parenthetically; `feasibility.json` mentions
  `go|no-go|conditional` for `verdict`). None of `handed-off`,
  `cleared`, `reported`, `landed`, `scope-approved` appear anywhere
  in `roles/*.json`. These files are role *registration* metadata
  (marketplace, sandbox, one-line decides/produces), not the
  authoritative state-machine spec — confirmed by reading all nine.
- The authoritative `loop_state` vocabulary per role lives in each
  role's own external rulebook repo, resolved via
  `roles/<role>.json`'s `path`/`repo` fields through
  `spawn.rulebook_dir()`/`rulebook_checkout()`. Confirmed by reading
  `coding-agent-rulebook`'s `docs/specs/handoff-protocol.md` §5: it
  declares `build-proposal`/`coding-record` `loop_state` vocabulary
  as **`proposed, approved, landed`** — which does not literally
  contain `scope-approved` or `scope-proposed`, the strings
  `wakes.py`/`wake-routing.md` actually consume. This is a live
  instance of exactly the class of gap issue #103 describes (parallel
  to controller #93's `scope-proposed`/`decided` case), found by this
  survey, not invented for the proposal.
- Of the other eight role rulebooks
  (`qa/verify/review/ux-design/feasibility/product/ops/reflect
  -agent-rulebook` under `~/tokenmaxxxer/`, resolved locally in this
  environment via `roles/*.json`'s `path`), none of their
  `docs/specs/` trees declare a `loop_state` vocabulary at all (only
  `coding-agent-rulebook` does, confirmed by
  `grep -rl loop_state */docs/specs` across all nine checkouts). So
  today there is no single declared vocabulary to check `handed-off`,
  `cleared`, `reported` against, even in principle — the producers
  are undocumented, not just uncross-checked.
- `roles/<role>.json`'s `path` resolves through `$TOKENMAXXXER_RULEBOOKS`,
  which is unset in this sandbox and will be unset in most CI/agent
  environments. `spawn.rulebook_dir()` falls back to a registry lookup
  or a local clone under `runs/rulebooks/` — both are either
  environment-local state or a network fetch. `test_gates.py`'s own
  header states its suite runs "네트워크·GitHub 없이" (no network, no
  GitHub) — a coherence test that reaches into nine external repos
  (cloning over the network when no local checkout exists) would
  break that invariant for the whole test run it joins.

## Unknowns / gaps this proposal must close

- **Where the checked-against vocabulary lives.** Two options surveyed:
  (a) the test reads live rulebook checkouts via
  `spawn.rulebook_dir()`, skipping/reporting-unverifiable for any role
  whose rulebook isn't locally present (no clone); or (b) this repo
  commits its own `docs/specs/loop-state-vocab.md` as the declared
  source of truth per role, kept in sync by whoever changes a
  rulebook's vocabulary or `wakes.py`'s consumed literals. (b) keeps
  the test network-free (matches `test_gates.py`'s existing rule) and
  gives the allowlist (`scope-approved`, human-only) one place to
  live next to the vocab it's an exemption from; its cost is a second
  place that can drift from the rulebooks themselves. The proposal
  below picks (b) for network-freedom and states the drift risk as an
  explicit, accepted limitation — not a silent gap.
- Whether `scope-approved` is the *only* human-only value to allowlist,
  or whether `_front()`'s fallback roles (`product`, `feasibility`) and
  the two `HUMAN_ONLY` edges (`finding 해소 후 재검증`,
  `라운드 종료 가치 게이트`) also need explicit vocabulary entries even
  though they don't compare a literal `loop_state`/`verdict` string.
  Proposal scopes the test to literal state/field *values* only, per
  issue text ("every state/field value... consume"), and leaves role
  names / structural checks out.
