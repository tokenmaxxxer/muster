---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request

#286 (paraphrased): the orchestrator reconstructs a session's state entirely
from `spawn.py`'s `.events.jsonl` / `.events.offset` / `runs/active.json` /
`runs/workspaces.json`, and today that reconstruction lies in ten distinct,
independently-reproduced ways — a lost cursor replays old events, a torn
line wedges the watcher or misclassifies a finished session as crashed, a
`progressed` verdict survives on a stale closed PR, a dropped `pr-opened`
leaves no trace, refusals arrive only after the session has already ended
and get deduped by content instead of by incident, a truncation fallback
destroys its own payload, the cursor file is unlocked, and roster keys
collide across repos with the same issue number.

## Constraints

- Per #310: every acceptance line must be an executable test against a real
  function, not a docstring, comment, or memory note.
- Per #363: the proposal states, per defect, what generated it and whether
  the fix removes that generator or only patches the reported instance —
  done below in "Rationale" and per-item in "What will be done."
- Per #358: `runs/` is gitignored and absent from this clone (confirmed:
  `.gitignore:1` lists `runs/`, `ls runs` fails in this workspace) — every
  file/line citation in the survey and here comes from reading `spawn.py`
  itself, never from a `runs/*.json` file, none of which exist to read.
- No overlap with #390 (CI/merge-time re-verification), #358 (survey
  honesty about a session's own clone), #325/#374 (spawn *coverage*, not
  event correctness) — confirmed in the survey's "Boundary with named
  sibling issues" section.
- E11 (2026-08-07 comment: vanished log reported as stall) is already
  substantially fixed in the `watch` path (`_await_bounded` now reports
  "cannot observe" instead of "stall" when the log file is gone) — this
  proposal does not re-touch that path. It leaves the `_auto_respawn_check`
  path as surveyed: `session_end_verdict` currently falls through to
  `"in-progress"`, not `"stalled"`, when `log_path` doesn't exist, so no
  reproduction of E11's watchdog-side variant exists yet to fix against.

## Rationale

Considered fixing E1/E2/E3/E9 by wrapping every call site in more
try/except instead of hardening the two shared primitives
(`_read_offset`/`_write_offset`) and the one shared parse loop
(`_await_bounded`/`session_end_verdict`) — rejected. Defensive code at every
call site is exactly how a torn-line assumption keeps recurring: the
generator is "nothing in this codebase treats a killed session's last write
as first-class," and that only gets removed by hardening the primitives
everything else calls through, not by patching each caller. This mirrors
`_roster_locked()`'s existing precedent (spawn.py:1426) — the repo already
locks `active.json` centrally rather than at each read/write site; the
proposal extends the same pattern to `.events.offset`.

Considered leaving E6 (refusals batched at session end) exactly as
designed, since :3242-3248's comment documents that provisional emission
was deliberately rejected by issue #235 to avoid a false-positive layer
label — rejected as a "leave it" answer, but the *fix* keeps that
constraint rather than reopening it: emit a new, distinctly-typed
provisional event (`refusal-candidate`) the instant a candidate is
detected mid-stream, and keep the existing confirmed
(`gate-refusal`/`harness-refusal`/`sandbox-refusal`/`unverified-refusal`)
event as the correlated truth once the terminal `result` line lands. This
gives a live watcher gate friction in real time (E6's acceptance line)
without asserting a confirmed layer label before `permission_denials`
confirms it — the exact distinction #235 was protecting.

Considered fixing E4 by changing `classify()` itself to require a commit
before `progressed` — rejected: `classify()`'s own docstring states it is
report-only ("판정하지 않는다 — 이름만 붙인다") and `fail_closed_downgrade()`
already exists as the separate git-aware verification stage precisely so
`classify()` stays untouched. E4's actual defect is one call:
`_pr_for_branch`'s `--state all` should not be treated as evidence the
*current* work was delivered — only an **open** PR on the branch, or a
**closed-merged** PR whose merge commit is an ancestor of the current HEAD,
counts as "already delivered." A closed-unmerged PR (abandoned attempt)
must not suppress `failed-no-commit`.

## What will be done

1. **E1 — `_read_offset` fails closed to file end, not 0** (spawn.py:1973).
   On `OSError`/`ValueError`, return `_event_count(events_path)` (already
   exists, :1980) instead of `0`, so a lost/corrupt offset resumes at the
   *tail* of the log — never replays history — for both the standalone
   `watch` path and any caller. Removes the generator: every offset-read
   site goes through this one function.
2. **E2 — `_await_bounded` skips a torn line, counts it, and advances past
   it** (spawn.py:2039). Wrap `json.loads(lines[seen])` in try/except
   `ValueError`; on failure, `_write_offset(offset_path, seen + 1)` (advance
   past the poisoned line so it is never retried), append a new
   `torn-line` event with a running count in its detail, and continue the
   loop instead of raising. Removes the generator for the *watch* cursor:
   the read-parse-advance path becomes single-function and torn-line-safe.
3. **E3 — `session_end_verdict` reports uncertainty instead of `crashed`
   when the terminal region contains a torn line** (spawn.py:1339). Count
   dropped/malformed lines seen after the last `session-start` index
   (currently silently `continue`d, :1360-1364); if any were dropped *and*
   no `session-end` was found, return a new verdict `"undetermined"`
   (documented in the same three-way-becomes-four-way docstring) instead of
   falling through to the `alive_fn`/mtime branch — a torn last line is
   evidence the process was writing something, not evidence it is
   crashed-and-safe-to-respawn. `_auto_respawn_check` treats `"undetermined"`
   the same as `"stalled"` today (report-only, no auto-respawn, one-time
   issue comment) — reusing `_post_stall_comment`'s marker pattern with a
   distinct message. This patches the specific instance (malformed
   `session-end` line) rather than removing torn-line risk everywhere in
   this function, since the rest of the parse loop already degrades safely
   (a torn *non-terminal* line just loses one event, which does not change
   the verdict).
4. **E4 — `already_delivered` requires an open PR, or a merged PR whose
   merge is an ancestor of HEAD** (spawn.py:3415-3420). Replace the bare
   `_pr_for_branch(...) is not None` check with a call to a new
   `_pr_delivered_for_branch(root, branch, head)` that runs
   `gh pr list --head <branch> --state all --json number,state,mergeCommit`
   and returns `True` only if the top result is `state == "OPEN"`, or
   `state == "MERGED"` and `git merge-base --is-ancestor <mergeCommit> HEAD`
   succeeds. A closed-unmerged PR (or a merged PR whose commit isn't in the
   current history — a stale phase-1-only merge on a since-reset branch)
   no longer suppresses `failed-no-commit`. Removes the generator: the one
   `already_delivered` computation is the only place `progressed` gets
   git-verified.
5. **E5 — a dropped `pr-opened` is reported, not silent** (spawn.py:3274-3293).
   When `_pr_for_branch` returns `None` for a candidate URL (transient `gh`
   failure or no PR found yet) and no *later* candidate line in the same
   session ever resolves to a match, append a `pr-open-unconfirmed` event
   at end-of-stream (alongside the existing `_flush_unverified`/
   `_flush_correlated_refusals` end-of-stream flush point) naming the
   candidate URL(s) seen and unresolved. This does not retry `gh` — it
   makes the drop an observable fact instead of nothing.
6. **E6 — provisional refusal events land in real time** (spawn.py:3325-3340).
   The instant a candidate is classified in the `user`/`tool_result` branch
   (:3332-3335), append a `refusal-candidate` event immediately (in
   addition to, not instead of, buffering into `pending_refusals` for
   later correlation) — same `key`/`detail` shape as the confirmed event
   types, distinctly typed so a consumer can tell "something looked like a
   refusal" (live) from "confirmed by permission_denials" (end of session).
   Keeps #235's confirmed/correlated distinction; adds the live signal E6
   asks for as a second, honestly-labeled event stream.
7. **E7 — repeat refusals are counted, not dropped after the first**
   (spawn.py:3336). Change `pending_refusals` from `dict[key -> single
   tuple]` to `dict[key -> list[tuple]]`, appending each occurrence instead
   of skipping when the key repeats. `_flush_correlated_refusals` and
   `_flush_unverified` iterate every buffered occurrence per key (bounded
   by however many `permission_denials` with that `tool_name` actually
   exist, same `remaining` Counter logic, just walking a list instead of a
   single value) — a second same-gate/same-reason denial in one session now
   produces a second event instead of vanishing.
8. **E8 — `unclassified-refusal` carries valid, parseable JSON**
   (spawn.py:1734). Replace `str(denials)[:200]` with
   `json.dumps(denials)[:2000]` guarded by `try/except (TypeError,
   ValueError): str(denials)[:200]` as a last-resort fallback only for
   non-JSON-serializable content — normal `denials` (a list of dicts from
   `permission_denials`) now round-trips through `json.loads` instead of
   being an unparseable Python repr fragment. Raised the cap to 2000 since
   this event exists specifically to preserve the payload a human/consumer
   needs to diagnose an unattributed denial.
9. **E9 — `_write_offset` is lock-protected like `ROSTER`**
   (spawn.py:2001). Add a `_offset_locked(offset_path)` contextmanager
   mirroring `_roster_locked()`'s flock-based pattern (:1426-1429,
   `.lock`-suffixed sibling file), and call `_write_offset` only inside it
   from `_await_bounded`. Removes the generator: the one write site is now
   the only site, and it is serialized.
10. **E10 — roster/index keys and files are repo-qualified**
    (spawn.py:2015, :2083, :2086, :2148, :3151, plus `ROSTER`/
    `WORKSPACE_INDEX` path constants at :1423, :1625). Prepend the repo
    slug (`_repo_slug(root)`, already exists at :943) to every
    `f"issue-{issue}/{role}"` key: `f"{slug}/issue-{issue}/{role}"`, falling
    back to the bare key only when `_repo_slug` returns `None` (can't
    determine — matches this repo's existing "unknown fails open to old
    behavior, never silently corrupts" convention, e.g. `_origin_pr_prefix`
    at :1988-1998). This is a key-format change to two JSON files
    (`active.json`, `workspaces.json`) — no migration needed since both are
    derived/rebuilt caches (`_workspace_index_put` always upserts;
    `_roster_locked()`'s callers always load-mutate-save), and both are
    gitignored (`runs/`), so no historical data needs converting.

## Out of scope

- E11's watchdog-path variant — no reproduction exists yet against current
  code (surveyed above); re-scouting this if a concrete repro turns up is a
  separate proposal.
- Redesigning the stream-order dependency itself (Claude Code guaranteeing
  `result` is the last line) — out of this repo's control, unchanged.
- #390/#358/#325/#374 — confirmed no write-set overlap in the survey.
- Any change to `_roster_locked()` itself, `gate_report`, `ownership_report`,
  or the respawn-cap/comment machinery beyond reusing
  `_post_stall_comment`'s marker pattern for the new `"undetermined"`
  verdict (item 3) — those are unrelated to event/cursor integrity.
- Migrating or backfilling any existing `runs/active.json` /
  `runs/workspaces.json` on disk — both are gitignored, machine-local,
  self-healing caches; the key-format change (item 10) takes effect on the
  next write.

## How you'll know it worked

Per #310, each of the following is a committed, network-free
`test_spawn.py` test calling the real function directly (matching this
file's existing style for `classify`/`session_end_verdict`/
`fail_closed_downgrade`):

- E1: `_read_offset` on a missing file and on a file containing
  non-integer text both return `_event_count(events_path)` for a
  multi-line fixture log, not `0`.
- E2: `_await_bounded` (or a unit-level helper extracted from its parse
  step) given a torn (non-JSON) line at index `seen` advances the offset
  past it, appends a `torn-line` event, and does not raise.
- E3: `session_end_verdict` given an events fixture whose last line (a
  would-be `session-end`) is truncated JSON, with `alive_fn` returning
  `False`, returns `"undetermined"`, not `"crashed"`.
- E4: `_pr_delivered_for_branch` returns `False` for a closed-unmerged PR
  fixture and `True` for an open PR fixture and a merged-PR-whose-commit-
  is-an-ancestor fixture, each via a mocked `gh`/`git` subprocess.
- E5: the stream-parsing loop given a candidate PR URL line and a mocked
  `_pr_for_branch` returning `None` throughout appends a
  `pr-open-unconfirmed` event naming the candidate, not nothing.
- E6: given a `user`/`tool_result` refusal-shaped line, a
  `refusal-candidate` event is appended immediately, before any `result`
  line is seen.
- E7: two same-key refusal candidates followed by a `permission_denials`
  list with two matching `tool_name` entries produces two flushed events,
  not one.
- E8: `_flush_correlated_refusals`'s fallback given non-`tool_name`-tagged
  denials appends an `unclassified-refusal` event whose detail
  `json.loads`s back to a list equal (up to the 2000-char cap) to the
  input.
- E9: two sequential `_write_offset` calls under `_offset_locked` do not
  interleave (asserted via a lock-held check inside a monkeypatched
  critical section, mirroring however `_roster_locked` is already tested
  if such a test exists, or a direct flock-contention test otherwise).
- E10: `_workspace_index_put` for two different repo slugs, same issue and
  role, produces two distinct keys in the resulting dict, not one
  overwriting the other.

All ten are executable pytest cases against real `spawn.py` functions —
none discharged by a comment, docstring, or this document's prose alone.
