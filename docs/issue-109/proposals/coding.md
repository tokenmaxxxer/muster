# Issue #109 — Phase 1 Proposal (coding)

files:
- `gates/gates.py` (`record_enums`: resolve `roles/<role>.json` from the
  on-the-record checkout, not the checked work repo; add an on-the-record
  `ROOT`-equivalent constant)
- `test_gates.py` (update `_record_repo`/`record_enums` fixtures and tests
  for the new resolution; add cases for "board has no `roles/`" and
  "on-the-record checkout's own `roles/<role>.json` missing")
- No other file. `gates/ci.py` calls `gates.record_enums(repo, {})`
  unchanged — the fix is entirely inside what `record_enums` treats as
  its role-file root, not in the call signature.

## Request (paraphrased intent)

`record_enums` (#100) resolves `roles/<role>.json` relative to the repo
being checked (the "work repo" / board). Role definitions only ever live
in the `on-the-record` repo itself, so on every board that is not
`on-the-record`, the gate finds no `roles/` directory and blocks with
"역할 정의를 읽을 수 없어 enum 을 검사할 수 없다" on records that are
otherwise fine — observed twice (feasibility-agent-rulebook issue-26
phase 2, product-agent-rulebook issue-29 phase 2). Fix: resolve role
definitions from the on-the-record checkout the session runs under —
the same self-location resolution `spawn.py` already uses for its own
`roles/<role>.json` reads (`spawn.py:32`, `ROOT = Path(__file__)
.resolve().parent`) — so a board with no `roles/` of its own is never a
violation. Decide and document what happens when the on-the-record
checkout itself lacks the role file (fail-closed, still a block, but
worded as an on-the-record install problem, not a board problem).

## Constraints

- Fail-closed stays fail-closed: an unreadable/missing role file still
  blocks (`gates.py`'s own stated principle: "불확실하면 막는다" —
  "검사할 수 없다" is a block, never a silent pass). This proposal
  changes *where* the file is looked for, never the pass/block default
  on failure to read it.
- `gates/gates.py` stays import-independent from `spawn.py` (existing
  docstring-stated design: dependency-free, deterministic, 0-LLM). The
  fix computes its own on-the-record root via `Path(__file__)`
  (mirroring `spawn.ROOT`'s pattern, not importing it), matching how
  `record_frontmatter` already duplicates `spawn.frontmatter()` for the
  same reason.
- `gates/ci.py::check(repo)`'s call site
  (`gates.record_enums(repo, {})`) is unchanged — `repo` continues to be
  used for `changed_files()`/the diff (still correct: the *record being
  written* lives in the work repo) and stops being used for the
  `roles/` lookup (the *role definition* lives in on-the-record). No
  signature change, no caller-visible change.
- Absence of `roles/` in the work repo is explicitly not an error
  condition after this fix and must never appear in a block message —
  the work repo is simply never consulted for role files anymore.
- The one case that must keep failing closed, loudly and distinctly: the
  on-the-record checkout that `gates.py` itself is running from is
  missing `roles/<role>.json` (a broken/stale on-the-record install, not
  a board's normal state). The block message for this case names the
  on-the-record-relative path that was actually checked, so a human
  reading it can tell "your board is fine, the on-the-record checkout
  gates.py ran from is broken" apart from "you wrote an out-of-enum
  value."

## What will be done

### 1. `gates/gates.py`: on-the-record root constant

Add, near the top of the module (alongside the existing module-level
constants like `PROTECTED_ROOT_DIRS`):

```python
# gates.py는 자신이 놓인 on-the-record 체크아웃을 이 파일의 위치로
# 찾는다 — spawn.py의 ROOT와 같은 자기위치 해석. 검사 대상 레포(work
# repo)의 경로와는 무관하다: roles/ 는 on-the-record 자산이지 보드
# 자산이 아니다.
ON_THE_RECORD_ROOT = Path(__file__).resolve().parent.parent
```

(`gates/gates.py` lives in `gates/`, so `.parent.parent` is the
on-the-record repo root — the same depth `spawn.py`'s own `ROOT =
Path(__file__).resolve().parent` reaches, since `spawn.py` lives at the
repo root directly.)

### 2. `record_enums`: switch the role-file root

Change `role_file = root / "roles" / f"{role}.json"` to
`role_file = ON_THE_RECORD_ROOT / "roles" / f"{role}.json"`. The work
repo's `root` (still computed from `d`/`d / "work"` for router-mode
compatibility) continues to be used only for `changed_files(root)` and
`record_file = root / f` — the diff and the record being validated stay
work-repo-relative; only the enum's source of truth moves.

Block-message wording keeps distinguishing what's missing from where:

```python
bad.append(f"역할 정의를 읽을 수 없어 enum 을 검사할 수 없다: "
           f"{role_file} (on-the-record 체크아웃: {ON_THE_RECORD_ROOT}) ({e})")
```

so a human sees the on-the-record path, not a board path, and cannot
mistake this for "board is missing roles/" (which is never checked and
never blocks).

### 3. Tests (`test_gates.py`)

- Update `_record_repo` (`test_gates.py:592-605`): stop writing
  `roles/<role>.json` into the fabricated work repo; instead write it
  under a fabricated on-the-record checkout and monkeypatch/parametrize
  `gates.ON_THE_RECORD_ROOT` (or construct `gates.py` under test with
  that root) to point at it — matching how `test_gates.py` already
  exercises `spawn.ROOT`-relative fixtures elsewhere in the file
  (e.g. `spawn.ROOT / "roles" / "_probe.json"` at line 301).
- New: a work repo with **no `roles/` directory at all** and a valid
  on-the-record `roles/<role>.json` — record with an in-enum value
  passes, no block, no "역할 정의를 읽을 수 없어" message anywhere in
  the result (this is the issue's core repro: board without `roles/`
  must never warn).
- New: a work repo with no `roles/`, on-the-record checkout also missing
  the specific `roles/<role>.json` — blocks, and the message contains
  the on-the-record-relative path checked (not a work-repo path).
- Existing `t_record_enums_out_of_enum_blocks`,
  `t_record_enums_in_enum_passes`,
  `t_record_enums_undeclared_field_passes`,
  `t_record_enums_missing_role_file_blocks`,
  `t_record_enums_loop_state_out_of_set_blocks` keep their assertions
  (fail-closed defaults, enum checking behavior) but move their
  `roles/<role>.json` fixture write to the on-the-record-checkout
  location instead of the work-repo location.

## Out of scope

- Any change to `spawn.py`'s own role resolution (`ROOT`) — it already
  does this correctly; this proposal only brings `gates.py` in line with
  it.
- Any change to `board-gate.sh` (owned by the separate
  `tokenmaxxxer-core` repo) or to router-mode (`gates.check`/`ALL`)
  call sites beyond what `record_enums`'s internals do — `gates/ci.py`'s
  call site is untouched (see Constraints).
- Retroactively re-checking already-merged records that were previously
  (incorrectly) blocked or passed under the old resolution.
- Making `record_enums` configurable to point at a different
  on-the-record checkout than the one `gates.py` itself runs from — the
  issue asks for "the on-the-record checkout the session runs under,"
  which self-location (`Path(__file__)`) already gives for free; no
  override mechanism is being requested or added.

## How we'll know it worked

- `gates.ON_THE_RECORD_ROOT` exists and is computed via `Path(__file__)`,
  independent of any work-repo argument.
- `record_enums` no longer reads `roles/` from the checked repo's `root`
  at all.
- `python3 -m pytest test_gates.py` passes, including the new
  "board has no roles/, on-the-record does — passes, no warning" and
  "on-the-record checkout itself missing the role file — blocks with an
  on-the-record-relative path in the message" cases.
- Manually reproducing the issue's trigger — running `gates/ci.py`
  against a checked-out board repo (e.g. `feasibility-agent-rulebook` or
  `product-agent-rulebook`) that has no `roles/` directory, with a valid
  `docs/issue-<n>/reports/<role>.md` record — no longer prints "역할
  정의를 읽을 수 없어 enum 을 검사할 수 없다".
