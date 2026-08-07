# Survey — issue-301 (B2: push-rejection must not report as silent-failure)

Skip condition: neither applies (this is not a pure bugfix with a single obvious
fix location, and the issue itself asks for a new distinguishable outcome
category — a naming/shape decision). Scouting skipped anyway: this is an
internal event-taxonomy fix scoped entirely to this repo's own
`spawn.py`/`gates/ci.py`; there is no external product category to benchmark
against (it is not product-shaped surface). Recorded per scout-directive.

## Write surfaces

- `spawn.py`
  - `ensure_pushed()` (spawn.py:2795-2846): pushes commits and opens the PR
    from the host side. On `git push` failure it currently only
    `print(...)`s the truncated stderr to the orchestrator's own stderr and
    returns `None` — the caller (`_spawn_one`) never learns push failed vs
    succeeded vs was a no-op (nothing to push).
  - `classify()` (spawn.py:1268-1291): produces `"silent-failure"` whenever
    `rc==0`, no board delta, nothing blocked, no permission denials — this is
    exactly the bucket a push-rejected session falls into today, since board
    delta is computed from the **local** working tree (`board_snapshot`),
    which already reflects the (locally committed, remote-rejected) content.
  - `_spawn_one()` call site (spawn.py:3290-3294): calls `ensure_pushed(cwd,
    issue, role)` for side effect only, discards any return value. Right
    after, it only checks `uncommitted` (from `git status --porcelain`,
    spawn.py:3281-3283) to upgrade `silent-failure` -> `uncommitted-work`.
    `uncommitted` catches a dirty working tree, not a clean tree that is
    **ahead of origin** — the issue-290 case (committed, clean tree, push
    rejected) is invisible to this check.
  - `_release_worktree`/`clean` (the `--clean` path, spawn.py:2499-2508)
    already has the exact detection primitive needed:
    `git log --branches --not --remotes --oneline` to count commits ahead of
    every remote-tracking branch, printed as `미push 커밋 N건`. This runs only
    at `spawn.py --clean` time, never at session end — confirmed via grep,
    it has exactly one call site.
  - `ledger_write()` call (spawn.py:3323-3335): persists `outcome` (a bare
    string) and no `reason`/`detail` field at all — there is no existing slot
    in the record schema for "why", only "what".
  - `_append_event(events_path, "session-end", outcome)` (spawn.py:3374): the
    terminal event on the workspace's own `events.jsonl`. `_append_event`'s
    signature (grep confirms 3 call sites, all `(path, type, payload)`) takes
    a `payload` positional that is currently always the bare outcome string.

- `gates/ci.py`: also references `silent-failure`/`ensure_pushed`-adjacent
  vocabulary (grep hit) — read to confirm it is a *consumer* of `outcome`
  strings (gate-report generation), not a producer; no diff expected inside
  this file for a first cut, but the write set below includes it in case the
  new outcome string needs a case there too.

## Existing outcome taxonomy (classify + fail_closed_downgrade)

`progressed`, `waiting-on-human`, `refused`, `silent-failure` (classify);
`uncommitted-work`, `progressed-dirty-tree`, `failed-no-commit`
(fail_closed_downgrade escalations at spawn.py:3293-3321). All are plain
strings threaded through `ledger_write`'s `outcome` field and the
`session-end` event's payload — there is no separate `reason:` channel
anywhere in this pipeline; every existing distinction is carried by
inventing a new outcome *label*, not by attaching detail to an existing one.
This sets the precedent the fix should follow: a new label
(`push-rejected` or similar) plus, additionally, a `reason` string threaded
alongside it — the issue explicitly asks for the remote's message to reach
the event and the record, not just a differently-named bucket.

## Test coverage

`grep -rn "ensure_pushed\|classify(" test/` shows unit tests exist for
`classify()` in isolation (pure function, easy to test) but none exercise
`ensure_pushed()` against a real/fake remote — it shells out to `git push`
and `gh pr create` directly. Any test added for the new push-rejection path
needs a fake remote (a second local bare repo) or a monkeypatched
`subprocess.run`/`_run_net`, matching the pattern already used elsewhere in
`test/` for `git`-shelling functions (confirmed by grep for
`monkeypatch.*subprocess` in test/).

## Alternatives visible from this survey

1. Return a structured result from `ensure_pushed` (status + reason) and let
   `_spawn_one` fold it into `outcome`/`ledger`/`event` — keeps `ensure_pushed`
   as the single source of truth for what happened on the host push path.
2. Leave `ensure_pushed` returning `None` (side-effect only, as today) and
   have `_spawn_one` re-derive "ahead of origin" itself via the same
   `git log --branches --not --remotes` primitive `--clean` already uses,
   independently of whether `ensure_pushed` was even called successfully —
   cheaper to write, but duplicates detection logic and cannot carry the
   remote's rejection *message* (only "ahead: yes/no"), which the issue
   explicitly asks for ("carry the remote's message into the event and the
   record").

Alternative 2 is real (the `--clean` code already proves the primitive
works standalone) but loses the rejection reason text — decided in the
proposal.
