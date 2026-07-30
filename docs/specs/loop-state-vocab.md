# loop_state / verdict vocabulary consumed by wakes.py

This doc is the declared vocabulary that `test_vocab_coherence.py`
checks `wakes.py`'s exact-match literal comparisons against. It exists
because `roles/*.json` do NOT declare `loop_state`/`verdict` vocab
(confirmed by the issue #103 phase-1 survey), and the one external
rulebook that does declare any vocabulary at all —
`coding-agent-rulebook`'s `docs/specs/handoff-protocol.md` §5
(`proposed, approved, landed`) — lives outside this repo and is not
reachable offline. Per the approved proposal
(`docs/issue-103/proposals/coding.md`), this repo treats this file
itself as the sole authoritative, offline-checkable declaration of
which `loop_state`/`verdict` values each role is understood to
produce, for the values `wakes.py` actually consumes by exact-match
comparison.

Keep this file in sync with `wakes.py`'s literal comparisons — adding
a new consumed value there without a corresponding entry here (or an
allowlist entry) is exactly the class of gap `test_vocab_coherence.py`
is built to catch.

## Declared vocab per role

### feasibility

- `verdict: go` — consumed at `wakes.py` (`roles.get("feasibility", {}).get("verdict") == "go"`, wake_coding's feasibility branch, ~line 277).

### qa

- `loop_state: handed-off` — consumed at `wakes.py` (`roles.get("qa", {}).get("loop_state") == "handed-off"`, wake_coding's qa branch, ~line 279).

### ux-design

- `loop_state: reviewed` — consumed at `wakes.py` (`roles.get("ux-design", {}).get("loop_state") == "reviewed"`, ~line 293).

### verify

- `loop_state: cleared` — consumed at `wakes.py` (`roles.get("verify", {}).get("loop_state") == "cleared"`, ~line 306).

### review

- `loop_state: reported` — consumed at `wakes.py` (`roles.get("review", {}).get("loop_state") == "reported"`, ~line 310).

### coding

- `loop_state: landed` — consumed at `wakes.py` (`roles.get("coding", {}).get("loop_state") == "landed"`, ~line 325).

## Human-only allowlist

- `scope-approved` — consumed at `wakes.py`'s pre-approval gate inside
  `wake_coding()` (`state == "scope-approved"`, ~line 266-267, the
  "사전 승인 게이트" comment block). No role produces this value — a
  human, via the pre-approval gate, is the only path to it. No role
  approves its own or another's scope-approved; this mirrors
  `wakes.py`'s existing `HUMAN_ONLY` dict entry ("사전 승인 게이트")
  which names the same gate as human-only by design, not by omission.
