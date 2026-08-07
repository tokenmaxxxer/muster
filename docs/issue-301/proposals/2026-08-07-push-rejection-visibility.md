---
status: proposed
files:
  - spawn.py
  - test/test_spawn.py
---

## Request

B2 half of #301 only (B1, the missing `workflow` OAuth scope, is out of
repo scope and explicitly excluded by the issue). A session that committed
real work but whose host-side push was rejected by the remote must not be
reported as `silent-failure` — that label is reserved for "nothing happened
and no one knows why." A push rejection is a *distinct, named, loud*
outcome that carries the remote's rejection message into both the
`session-end` event and the ledger record, and it must be distinguishable
from (a) a session with unpushed commits sitting locally for some other
reason, and (b) a session that genuinely produced nothing.

## Constraints

- No credential/scope work (B1) — out of scope per the issue text.
- Must not touch the `--clean` detection path's existing behavior
  (spawn.py:2499-2508) beyond reusing its detection primitive; that path is
  unrelated to the session-end pipeline and already correct.
- Existing outcome strings (`progressed`, `refused`, `silent-failure`,
  `uncommitted-work`, `progressed-dirty-tree`, `failed-no-commit`) keep
  their current meaning — this only adds a new label plus a new `reason`
  field, it does not rename or repurpose an existing one.

## Rationale

Two ways to get "distinguishable": (1) make `ensure_pushed` return a
structured result (status + reason string) that `_spawn_one` folds into the
outcome/ledger/event, or (2) leave `ensure_pushed` a side-effecting `None`
function and have `_spawn_one` independently re-derive "commits ahead of
origin" via the same `git log --branches --not --remotes` primitive the
`--clean` path already uses (survey alternative 2).

Alternative (2) is rejected: it can tell you commits are unpushed, but it
cannot tell you *why* — it has no access to the `git push` stderr, so it
cannot carry "refusing to allow an OAuth App to create or update workflow
... without `workflow` scope" into the event, which is exactly what the
issue asks for ("carry the remote's message into the event and the
record"). Re-deriving ahead-count independently of `ensure_pushed` also
duplicates a check `ensure_pushed` already performs internally
(`git rev-list --count origin/<br>..<br>`) for no benefit.

Chosen: (1). `ensure_pushed` becomes the single source of truth for what
happened on the host push path, since it already has the push stderr in
hand; it returns a small structured result instead of `None`, and
`_spawn_one` reads it to decide the outcome label.

## What will be done

- `ensure_pushed()` returns a dict `{"status": ..., "reason": <str|None>}`
  instead of `None`. Statuses, derived from its existing branches:
  - `"nothing-to-push"` — branch has no local commits ahead of origin (the
    `unborn` / `n in ("", "0")` false branch today — currently silent
    no-op).
  - `"pushed"` — push succeeded (covers today's success print).
  - `"push-rejected"` — `git push` returned nonzero; `reason` is the
    existing truncated `r.stderr.strip()[:200]` already computed at
    spawn.py:2821, now returned instead of only printed.
  - `"pr-create-failed"` — push succeeded (or was a no-op with an existing
    open PR check) but `gh pr create` failed; `reason` is the existing
    `c.stderr.strip()[:200]` from spawn.py:2846, now returned too.
  - `"pr-opened"` / `"pr-already-open"` — the two existing success
    sub-branches at spawn.py:2842-2844 / 2831, distinguished for record
    completeness though not required by the acceptance criteria.
  All existing `print(..., file=sys.stderr)` calls in `ensure_pushed` stay
  (no change to what a human tailing the log sees) — the function gains a
  return value, it does not lose its existing side effects.

- `_spawn_one()` (spawn.py:3290) captures the return: `push_result =
  ensure_pushed(cwd, issue, role)`. After the existing `uncommitted` /
  `outcome = classify(...)` computation (spawn.py:3292-3294), add one more
  branch, checked before the existing `silent-failure` ->
  `uncommitted-work` upgrade so the two never collide (a session can have
  either a dirty tree or unpushed-but-rejected commits, and if a session
  somehow has both, dirty-tree/`uncommitted-work` — the more locally-visible
  problem — wins, matching the existing precedence: uncommitted check is
  already first in source order):
  ```python
  if outcome == "silent-failure" and uncommitted:
      outcome = "uncommitted-work"
  elif outcome == "silent-failure" and push_result and push_result["status"] == "push-rejected":
      outcome = "push-rejected"
  ```
  A push rejection with a **dirty** tree still reports `uncommitted-work`
  first — the tree not being clean is the more actionable/blocking fact for
  a respawn to pick up, and this mirrors the existing ordering rationale
  already in the `classify()` docstring (the repo's stated principle that
  "검사 불가와 이상 없음은 정반대 처분을 받아야 한다" — a rejection reason
  known is not the same as nothing known, so it must not collapse into
  either category silently).

- `reason` threading:
  - `ledger_write()`'s dict (spawn.py:3323) gains a `"push_reason":
    push_result.get("reason") if push_result else None` field (present,
    possibly `None`, on every record — not conditionally omitted, so a
    reader of the ledger schema does not have to guess whether the key's
    absence means "no push attempted" or "old record predates the field").
  - `_append_event(events_path, "session-end", outcome)` (spawn.py:3374)
    changes to `_append_event(events_path, "session-end", {"outcome":
    outcome, "reason": push_result.get("reason") if push_result else None}
    if isinstance(outcome, str) else outcome)` — concretely: the payload
    becomes a dict carrying both fields when a reason exists, matching how
    the issue asks for the event itself (not only the record) to name the
    rejection reason. Existing consumers of `session-end` events that read
    `ev.get("type")` only (confirmed by grep: `session_end_verdict` and the
    watch-loop code at spawn.py:1329/2035/2045 all check only `type`, never
    inspect `payload`'s shape) are unaffected by payload becoming a dict
    instead of a bare string.
  - A stderr print mirroring the existing `silent-failure`/`refused`
    messages (spawn.py:3349-3356) is added for `push-rejected`:
    `f"[{role}] 호스트 push 가 거부됐다 — 커밋은 로컬에 있다: {reason}"` so a
    human tailing the log sees the same loud, named signal the ledger and
    event now carry.

- Tests (`test/test_spawn.py`): three new/updated cases exercising the
  three outcomes the issue's acceptance criteria name explicitly —
  1. a fake remote that rejects `git push` (a second local bare repo with a
     pre-push hook that exits nonzero, or a monkeypatched `_run_net` /
     `subprocess.run` matching the existing test pattern for git-shelling
     functions) -> asserts `ensure_pushed` returns
     `{"status": "push-rejected", "reason": <non-empty>}` and that
     `_spawn_one`'s resulting outcome is `"push-rejected"`, distinct from
     `"silent-failure"`.
  2. a workspace with local commits ahead of a remote that accepts the push
     with no error (or push skipped entirely) but where `uncommitted-work`
     does not apply (clean tree) — confirms this is not conflated with
     case 1.
  3. a workspace with no board delta, no uncommitted changes, and no
     commits ahead of origin at all (`ensure_pushed` returns
     `{"status": "nothing-to-push", "reason": None}`) -> outcome stays
     `"silent-failure"`, unchanged from today.

## Out of scope

- B1 (the missing `workflow` OAuth scope) — explicitly excluded by the
  issue; no credential/token change in this repo.
- Landing the stranded `issue-290/implementation` commits — that is a
  separate act (the issue's third acceptance line, "the stranded work
  lands") for a human/on-the-record operator with host push access, not a
  code change this proposal produces.
- `gates/ci.py` — survey found it only consumes outcome strings for gate
  reporting; no diff identified there for this change. If phase-2 execution
  finds an actual touch point, that is a scope-exceeded stop, reported per
  contract, not a silent widen.
- Renaming or restructuring any existing outcome label.

## How you'll know it worked

Three scripted/tested scenarios, each producing a distinguishable
event + ledger outcome, matching the issue's acceptance criteria:
1. **Push rejected by remote**: `session-end` event payload is
   `{"outcome": "push-rejected", "reason": "<remote's message>"}`,
   ledger row has `outcome: "push-rejected"` and a non-null
   `push_reason`.
2. **Unpushed commits at session end for another reason** (e.g. push
   simply not attempted because `ensure_pushed` itself errored before
   reaching `git push`, or is skipped because `issue is None`) does not
   collapse into the same label — remains distinguishable via `outcome`
   staying `silent-failure`/other existing labels plus `push_reason: None`,
   never silently reported as `push-rejected` when no rejection actually
   happened.
3. **Session that produced nothing**: `outcome` stays `"silent-failure"`,
   `push_reason: None`, unchanged from current behavior — proving the fix
   is additive, not a reclassification of the existing bucket.
All three demonstrated via the new `test/test_spawn.py` cases (unit-level,
run in phase 2) plus one recorded terminal transcript per scenario in the
phase-2 implementation record, per the effect-verification requirement
carried over from #298.
