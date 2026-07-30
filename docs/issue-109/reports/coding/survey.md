# Issue #109 — Current-State Survey (coding)

## Scout: skipped

Skip condition: this is a bugfix to an existing internal gate's path
resolution — the issue text already prescribes the mechanism direction
("resolve roles/<role>.json from the on-the-record checkout the session
runs under, same resolution the spawn machinery already performs"),
leaving only where to change the resolution and how to phrase the
fail-closed message as implementation detail, not an open design
question. No external product analog applies to an internal CI gate.

## What exists today

- `gates/gates.py::record_enums(d, cfg)` (added by #100) resolves the
  role file as `root / "roles" / f"{role}.json"`, where `root = d / "work"
  if (d / "work").exists() else d` — i.e. **relative to the repo being
  checked** (`gates/gates.py:265,272`).
- `gates/ci.py::check(repo)` calls `gates.record_enums(repo, {})` with
  `repo` = the checked-out **work repo** (`gates/ci.py:24,28`; CLI:
  `python3 gates/ci.py [<repo 경로>]`, default `.`). On any board that is
  not the `on-the-record` repo itself, `repo / "roles"` does not exist,
  so every changed `docs/issue-<n>/reports/<role>.md` triggers the
  "역할 정의를 읽을 수 없어 enum 을 검사할 수 없다" block —
  observed twice (feasibility-agent-rulebook issue-26 phase 2,
  product-agent-rulebook issue-29 phase 2), per the issue.
- `spawn.py` already solves an equivalent problem for its own
  `roles/<role>.json` reads: `ROOT = Path(__file__).resolve().parent`
  (`spawn.py:32`) — the on-the-record checkout is located by **where
  `spawn.py` itself lives on disk**, never by the work repo's path. Every
  `roles/<role>.json` read in `spawn.py` (`role_settings`, `update`,
  `spawn`, the role-list glob, etc.) goes through `ROOT`, so it resolves
  correctly regardless of which repo the session is working on. This is
  "the same resolution the spawn machinery already performs" the issue
  points at.
- `gates/gates.py` has no `ROOT`-equivalent constant today — `record_enums`
  is the only function in the module that needs to locate `roles/`, and it
  was written taking the checked repo's own root as the source (correct
  for `writeset`/`deps`, which inspect the *work repo's* diff and deps —
  but `roles/` is never part of the work repo's own tree; it is
  `on-the-record`'s own protected asset, per
  `gates/gates.py:30`'s `PROTECTED_ROOT_DIRS = {"roles", ...}` comment:
  "역할 정의와 배선. 루트의 것만" — "root's own [roles], only").
- Test fixture `test_gates.py::_record_repo` (`test_gates.py:592-605`)
  currently creates `roles/<role>.json` **inside the fabricated work
  repo** to make the existing tests pass — this fixture itself encodes
  the bug's premise (that `record_enums` reads roles/ from the work repo)
  and needs to change shape once the fix lands: role files come from the
  on-the-record checkout under test (`gates.py`'s own repo, i.e.
  `Path(__file__).resolve().parent.parent / "roles"`), not from the
  fabricated work-repo fixture.
- `gates/gates.py` is dependency-free by design (its own module docstring
  distinguishes it from `spawn.py`/`wakes.py`: "게이트가 막으면 재시도가
  아니라 에스컬레이션이다" — deterministic, 0-LLM, no cross-import). It
  does not import `spawn.py` today (`record_frontmatter` is a duplicate of
  `spawn.frontmatter()` for exactly this reason, per its own docstring at
  `gates/gates.py:243-245`). A fix should keep that independence — i.e.
  compute a `ROOT`-equivalent locally in `gates.py` via `Path(__file__)`,
  not import `spawn.ROOT`.

## The gap

`record_enums` conflates two different roots that #100 never
distinguished: the **work repo** (whose diff is being checked — correct
source for `writeset`/`deps`) and the **on-the-record checkout** (whose
`roles/` directory is the actual source of truth for role definitions —
correct source for `record_enums`, always, on every board). Because
`record_enums` currently uses the work-repo root for both, any board
that is not `on-the-record` itself gets a spurious "can't read role
definition" block on a record write that has nothing wrong with it.

The issue additionally asks that this now be a considered, documented
choice on the one case that still legitimately fails closed: the
on-the-record checkout the gate itself is running from lacking the role
file (a broken/stale install, not "board doesn't happen to vendor
roles/"). That distinction is not currently expressed anywhere — today's
single error path conflates "board has no roles/ (expected, not a
violation)" with "on-the-record checkout is broken (a real problem)".
