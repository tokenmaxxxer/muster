# Issue #100 — Phase 1 Proposal (coding)

files:
- `roles/feasibility.json` (add machine-readable enum declaration for `verdict`)
- `roles/coding.json`, `roles/qa.json`, `roles/review.json`, `roles/verify.json`,
  `roles/ux-design.json`, `roles/product.json`, `roles/ops.json`,
  `roles/reflect.json` (add machine-readable enum declaration for
  `loop_state`, each role's own value set)
- `gates/gates.py` (new `record_enums` check function + registration in `ALL`)
- `test_gates.py` (tests for the new check)
- No file under `tokenmaxxxer-core` (the repo that owns `board-gate.sh`) is
  touched — that repo is out of this write set entirely.

## Request (paraphrased)

A feasibility record was committed with `verdict: "go (조건부 → ...)"` — free
text in what is supposed to be a closed enum field
(`go|no-go|conditional`). Nothing rejected it at write time; the only
consumer, `wakes.py:277`, does an exact-match on `"go"` and silently did
not match, so the failure surfaced only much later as "coding never woke
up." Add validation of machine-judged record fields against the role's
declared enum **at write time**, so an out-of-enum value is an immediate,
loud refusal (deny the write, say why) instead of a silent downstream
routing no-op.

## Constraints

- Fail-closed, consistent with this repo's existing gate direction
  (`gates/gates.py`'s own docstring: 불확실하면 막는다). An unparseable
  enum declaration or an unreadable role file blocks the write; it never
  silently passes.
- The enum source of truth is `roles/<role>.json` — not a value hardcoded
  in the gate itself — because the whole point is that a role's declared
  contract (not tribal knowledge in `wakes.py`'s comparisons) is what gets
  enforced. `wakes.py`'s existing string comparisons (`"go"`,
  `"scope-approved"`, `"handed-off"`, `"reviewed"`, `"cleared"`,
  `"reported"`, `"landed"`) are the values that seed each role's declared
  set — this proposal does not invent new vocabulary, it makes existing
  vocabulary machine-readable.
- Only fields that are actually machine-judged today are in scope:
  `verdict` (feasibility) and `loop_state` (all roles, per
  `docs/specs/wake-routing.md`'s state-marker convention). Per-requirement
  or per-attempt classifications that live in prose inside a record body
  (review's `Present|Surface|Absent|Incorrect|Unverifiable`, verify's
  `reproduced|not-reproduced`) are NOT frontmatter fields and are out of
  scope for this proposal (see Out of scope).
- `roles/*.json` and `gates/gates.py` are both under
  `gates.py`'s own `PROTECTED_ROOT_DIRS`. A PR touching them is expected to
  be flagged by the existing CI/router protected-path check and escalate
  to human review rather than merge silently — this is intended
  (파이프라인이 자기 규칙을 다시 쓸 수 없어야 한다), not a bug to route
  around.
- This proposal only extends `gates/gates.py` (owned by this repo). It
  does not touch `board-gate.sh` (owned by `tokenmaxxxer-core`, a separate
  repository) — that would need its own issue in that repo if a
  PreToolUse-time (not CI-time) enforcement point in role sessions is
  wanted later (see Out of scope).
- Backward compatibility: existing records already committed to `main`
  with values that would now be out-of-enum are not retroactively touched;
  the gate only checks the changed-files diff at write/CI time, same as
  `writeset`/`deps` do today.

## What will be done

### 1. Declare enums in `roles/<role>.json`

Add a new top-level key, `record_fields`, mapping frontmatter field name
to its closed value set, e.g.:

```json
{
  ...
  "record_fields": {
    "verdict": ["go", "no-go", "conditional"]
  }
}
```

`roles/feasibility.json` gets `verdict`. Every role file gets `loop_state`
with its own set, read off of `wakes.py`'s existing comparisons and
`docs/specs/wake-routing.md`'s state-marker convention (e.g. coding:
`["scope-proposed", "scope-approved", "in-progress", "landed"]`, qa:
`["handed-off", ...]`, ux-design: `["reviewed", ...]`, verify:
`["cleared", ...]`, review: `["reported", ...]` — exact per-role sets are
enumerated from `docs/specs/wake-routing.md` and `wakes.py` during
implementation, not guessed here). A role file with no `record_fields` key
means no enum fields to check for that role (not "check nothing" —
`loop_state` is a de facto convention across all roles per
`docs/specs/wake-routing.md`, so every role file gets at least that key).

### 2. `gates/gates.py`: new `record_enums` check

```python
def record_enums(d: Path, cfg: dict) -> list[str]:
    """Changed docs/issue-<n>/reports/<role>.md frontmatter fields must be
    in that role's roles/<role>.json record_fields enum, if declared."""
```

- Reuses `changed_files()` (already fail-closed on diff failure) to find
  changed paths matching `docs/issue-*/reports/<role>.md` (top-level
  role record only — matches `spawn.py`'s `ROLES` set and `wakes.py`'s
  `_rec()` path shape; per-subrole files under `reports/<role>/*.md`, e.g.
  survey files, carry no frontmatter contract and are not in scope).
- For each match, reads the role name from the filename, loads
  `roles/<role>.json` from the **repo root being checked** (`d / "work" /
  "roles" / f"{role}.json"` in router mode, matching `writeset`'s existing
  `d / "work"` convention) — if the role file is missing or unparseable,
  that is a block ("역할 정의를 읽을 수 없어 enum 을 검사할 수 없다"), not
  a pass.
- Parses the changed record's frontmatter with the same shallow `---`
  parser `spawn.py.frontmatter()` uses (duplicated here in
  `gates.py`, matching how `gates.py` already stands apart from
  `spawn.py`/`wakes.py` as the router/CI's own dependency-free module —
  no new cross-import).
- For every `record_fields` key present in the record's frontmatter, if
  its value is not in the declared set: block with
  `f"레코드 enum 위반: {path} 의 {field}={value!r} — roles/{role}.json 이 선언한 값 ({allowed}) 이 아니다"`.
- A record with no matching `record_fields` key in frontmatter is not
  blocked (the field simply wasn't written — free-text fields the role
  hasn't declared as enum stay unchecked, matching the issue's ask: only
  machine-judged declared fields are validated).

### 3. Register in `ALL` and add to CI

Add `"record_enums": record_enums` to `gates.py`'s `ALL` dict so router
callers can opt in via `check(["record_enums"], ...)`, and add the same
check (repo-root form, no `d / "work"` prefix) to `gates/ci.py::check()`
so a human-authored PR onto `main` is checked too — mirroring how
`gates/ci.py` already re-runs `deps` in repo-root form because
`gates.deps` assumes the router's `d / "work"` layout.

### 4. Tests (`test_gates.py`)

- A record with an out-of-enum `verdict` is blocked with a message naming
  the field, the value, and the allowed set.
- A record with an in-enum `verdict` passes.
- A record whose role has no `record_fields` declared passes (nothing to
  check).
- A record referencing a role whose `roles/<role>.json` is missing/corrupt
  is blocked (fail-closed), not passed.
- A record with a `loop_state` value outside its role's declared set is
  blocked the same way `verdict` is.

## Out of scope

- Extending `board-gate.sh` in `tokenmaxxxer-core` for a PreToolUse-time
  (inside a live role session, before the file even reaches disk) version
  of this same check. That repo is a separate repository this issue's
  write set does not include; if a session-time (not CI-time) version is
  wanted, it needs its own issue filed against `tokenmaxxxer-core`. This
  proposal's `gates/gates.py` extension gives the CI/router-time
  enforcement the issue asks for ("write-time... immediate, loud
  refusal") without needing that separate repo change.
- Validating per-requirement/per-attempt inline classifications that live
  in record body prose rather than frontmatter (review's
  `Present|Surface|Absent|Incorrect|Unverifiable`, verify's
  `reproduced|not-reproduced`) — these are not single frontmatter fields
  and would need a different (body-parsing) mechanism; not this issue's
  reported failure mode.
- Retroactively fixing or flagging already-merged records with
  out-of-enum values on `main`.
- Changing `wakes.py`'s own comparison logic — it stays exact-match; this
  proposal prevents the mismatch from being writable in the first place,
  it doesn't make the reader more lenient.

## How we'll know it worked

- `roles/feasibility.json` and every other `roles/*.json` file contains a
  `record_fields` key naming its enum(s) as JSON arrays.
- `gates/gates.py::ALL` contains `"record_enums"`, and `gates/ci.py::check`
  calls it.
- `python3 -m pytest test_gates.py` (or the repo's existing test runner)
  passes, including the new out-of-enum / missing-role-file /
  no-declared-field / in-enum cases.
- Manually reproducing the issue's trigger — writing
  `docs/issue-<n>/reports/feasibility.md` with `verdict: "go (조건부 →
  ...)"` — causes the gate to block with a message naming the field, the
  bad value, and the allowed set, instead of silently landing.
- `PROTECTED_ROOT_DIRS`-triggered escalation on this PR itself (touching
  `roles/` and `gates/`) is expected and not treated as a defect.
