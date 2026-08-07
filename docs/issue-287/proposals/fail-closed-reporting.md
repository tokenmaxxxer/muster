---
status: proposed
files:
  - gates/closure_sweep.py
  - gates/flows.py
  - spawn.py
  - gates/ci.py
  - on-the-record/hooks/deliverable-guard.sh
  - docs/specs/flows-schema.md
  - test_flows.py
  - test_spawn.py
  - gates/test_closure_sweep.py
  - tests/run-orchestrate-tests.sh
---

## Request

Every reporting surface in this repo currently collapses "I could not
check" into "checked, and it's clean": `closure_sweep` exits 0 and prints
"위반 없음" when `gh` fails for every subject; `flows`'s JSON payload
renders an empty board on a `gh` outage with no error field; a corrupt
ledger line is dropped with no count; `deliverable-guard.sh` allows a
write through on an unparseable stdin payload despite claiming to fail
closed; and two escalation-comment posts (`closure_sweep.post_sweep_comments`,
`spawn._post_crash_comment`) never check whether the post itself
succeeded. Fix each surface so a failed lookup produces a distinct, named
"could not check" outcome instead of an empty/clean-looking result.

## Constraints

- Never change the *direction* of an existing fail-closed decision (e.g.
  `_phase_from_approval` must still classify an unconfirmed PR as phase1,
  `approve_scope` must still refuse when it lacks a comment) — only make
  the *reason* distinguishable in the reported message/payload.
- No new dependency, no schema-breaking rename: `flows --json` gets new
  optional fields, not removed/renamed existing ones. Keep the change
  additive; if `docs/specs/flows-schema.md` §4 turns out to require a
  `schema_version` bump for a field addition, bump it and note that in
  `## What did not work`.
- `deliverable-guard.sh`'s allowed-path behavior for unrelated files (no
  `src/`/`test/`/`docs/` in payload) must not change — only the
  malformed-payload and `tests/`-segment cases move from ALLOW to DENY.
- Existing tests (`test_flows.py`, `test_spawn.py`, `test_gates.py`,
  `test_approve_scope.py`) must keep passing — they already exercise the
  gh-success paths of every function this proposal touches.

## Rationale

Two shapes were available for signaling "lookup failed" from the `gh`
wrapper functions (`_pr_list_all`, `_issue_list_all`, `_issue_comments`,
`_issue_view`, `_pr_view_state_body`) up to their callers
(`flows_payload`, `find_violations`, `approve_scope`, `_phase_from_approval`):

1. **Raise an exception on `gh` failure**, caught at each call site. This
   was rejected: several of these functions are deliberately network-free
   and dict-in for testability (`closure_sweep.find_violations` accepts a
   pre-fetched `issue_states` dict exactly so tests and `flows_payload`
   can drive it without `gh`; `classify` is a pure function over strings).
   Exceptions would force try/except at every call site, several of which
   are nested two and three calls deep in `flows_payload`, and would
   diverge from the wrapper-returns-a-value convention already used
   throughout this codebase.
2. **Return a distinguishable value** — chosen. Each wrapper returns a
   small tuple or sentinel that says explicitly whether the call
   succeeded, mirroring the precedent already in this codebase:
   `flows._stage_for` returns `(value, derived: bool)` specifically so a
   caller (and the `flows()` text renderer, which already prints `(raw)`
   next to a non-derived stage) can tell "we computed this" from "this is
   a fallback". This proposal reuses that same `(value, ok: bool)` /
   sentinel-object shape for `gh`-call results, so `flows_payload` and
   `find_violations` can propagate "could not check" without exceptions
   and without changing their existing network-free call signatures.

For the ledger (S3), a global "degraded mode" flag was considered instead
of a per-read skipped-count, but rejected — the issue's acceptance
criterion ("skipped ledger lines are counted in the payload") needs a
number attributable to that specific read, not a boolean that would
conflate ledger corruption with an unrelated `gh` failure in the same
`flows_payload` call.

## What will be done

- `gates/closure_sweep.py`: `_issue_view`/`_pr_view_state_body` return
  `(value, ok)` instead of `value | None`; `find_violations` collects a
  list of `{"subject"/"issue", "reason": "gh-issue-view-failed" | ...}`
  skip records alongside `violations` and returns both (or a small result
  object) so callers can tell "checked, 0 violations" from "N subjects
  unchecked". `main()` exits 2 (distinct from the existing 0/1) and prints
  a "종결 일관성 스윕: 확인 불가" message naming the unchecked subjects when
  any skip occurred, even if some subjects did resolve. `post_sweep_comments`
  checks `subprocess.run(...).returncode` and logs/returns which issues'
  comments failed to post (S7).
- `gates/flows.py`: `_pr_list_all`/`_issue_list_all` return `(list, ok)`;
  `flows_payload` adds a top-level `"errors": {"pr_list": bool, "issue_list": bool}`-shaped
  field (present, empty/false when nothing failed) instead of silently
  keeping `decision_queue`/`flows`/hygiene empty. `_ledger_read` returns
  `(entries, skipped_count)`; `flows_payload` puts `skipped_count` into the
  existing `unattributed`-style aggregate as `ledger_skipped`. `flows()`
  text renderer prints the error/skip fields when non-empty/non-zero.
- `spawn.py`: `_issue_comments` returns `(list, ok)`;
  `approve_scope` distinguishes, in its exit message, "no matching APPROVE
  comment found" (call succeeded, list is empty/non-matching) from "이슈/PR
  코멘트를 읽지 못했다" (call failed) — call sites updated to unpack the new
  tuple. `_post_crash_comment` checks its `gh api` call's returncode and
  prints/logs to stderr when the escalation post itself fails, so a lost
  escalation isn't silent (S7).
- `gates/ci.py`: `_phase_from_approval` unpacks the new `_issue_comments`
  tuple; behavior (fail-closed to phase1 on failure) is unchanged — this
  is a call-site update only, no direction change, per Constraints.
- `on-the-record/hooks/deliverable-guard.sh`: the
  Python heredoc's `except ValueError: sys.exit(0)` becomes `deny(...)`
  (exit 2); non-dict payload and missing/empty `file_path` become `deny(...)`
  too. Bash prefilter case pattern and the Python regex both add a
  `tests/` alternative alongside `test/`.
- `docs/specs/flows-schema.md`: document the new `errors` object and
  `ledger_skipped` field under §1/§2.4.
- Tests: extend `test_flows.py` (gh-failure simulation for
  `_pr_list_all`/`_issue_list_all`/`_ledger_read`, asserting the payload
  reports unknown rather than empty), `test_spawn.py` (`_issue_comments`
  failure path, `approve_scope` message distinction), new
  `gates/test_closure_sweep.py` (gh-failure simulation asserting non-zero
  exit and "확인 불가" wording, not "위반 없음"), and add cases to
  `tests/run-orchestrate-tests.sh` for `deliverable-guard.sh` (empty
  stdin, non-JSON stdin, non-dict JSON, missing `file_path`, a `tests/`-segment
  path) asserting deny (exit 2) in every case.

## Out of scope

- Any change to which conditions count as a *violation* in
  `closure_sweep.classify` — only how lookup failures are reported.
  Alerting/notification changes beyond the existing issue-comment
  mechanism (e.g. paging, Slack).
- Retrying failed `gh` calls or adding backoff — this proposal only makes
  failure visible, not less frequent.
- Changing `flows --json`'s `schema_version` unless the additive-field
  rule in `docs/specs/flows-schema.md` §4 turns out to require it (will be
  logged in `## What did not work` if so).
- Any other gate or hook not named in S1-S7 of the issue.

## How you'll know it worked

- `closure_sweep` run against a repo with `gh` forced to fail (e.g. bad
  `GH_TOKEN`/mocked `subprocess.run`) exits non-zero with a message that
  says it could not check, distinct from both its 0 ("위반 없음") and 1
  ("위반 발견") outcomes today.
- `flows --json` under the same forced failure carries a non-empty
  `errors` object instead of empty `decision_queue`/`flows` arrays with no
  indication anything went wrong.
- A corrupted `runs/ledger.jsonl` line is reflected as a nonzero count in
  the payload, not silently dropped.
- `deliverable-guard.sh` denies (exit 2) on empty stdin, non-JSON stdin, a
  non-dict JSON payload, and a payload missing `file_path`; it also denies
  a write under a `tests/...` path the same way it already denies
  `test/...`.
- `approve_scope`'s failure message differs between "no APPROVE comment
  exists" and "could not read comments from gh".
- All of the above are covered by the new/extended tests listed above,
  runnable without live network access (gh calls simulated/mocked), and
  the full existing test suite (`test_flows.py`, `test_spawn.py`,
  `test_gates.py`, `test_approve_scope.py`) still passes.
