# Issue #100 — Current-State Survey (coding)

## Scout: skipped

Skip condition: the issue text already prescribes the mechanism direction
("PreToolUse gate or board-gate extension, consistent with the existing
fail-closed gate direction"), leaving only where-to-place and
how-to-declare-the-enum as implementation detail, not an open product
design. This is an internal control-plane gate with no external product
analog to scout against; the current-state survey below (reading this
repo's existing gates) is the deciding input instead.

## What exists today

- `roles/<role>.json` declares each role's `produces` field as **free
  prose**, e.g. `roles/feasibility.json`: `"produces": "4프로브 결과,
  verdict go|no-go|conditional, 측정 설계"`. The enum `go|no-go|conditional`
  lives inside a human-readable sentence — nothing parses it.
- `wakes.py:277` reads the written record's frontmatter (`spawn.frontmatter`,
  a shallow `---`-block parser) and does an **exact string match**:
  `roles.get("feasibility", {}).get("verdict") == "go"`. Any other spelling
  (`"go (조건부 ...)"`, `"Go"`, `"conditional-go"`) is fail-closed at the
  wake router in the sense that it silently does not match "go" —
  correct per its own doc comment, but it means the record's author gets
  no signal that their value was ever out of enum. The failure surfaces
  only downstream as "coding never woke up."
- `loop_state` is the same shape of problem, already exercised across more
  roles: `wakes.py` exact-matches `"scope-approved"`, `"handed-off"`,
  `"reviewed"`, `"cleared"`, `"reported"`, `"landed"` (lines 266, 279, 293,
  306, 310, 325). None of these values is declared anywhere machine-
  readable either — they are conventions living only in
  `docs/specs/wake-routing.md` prose and in `wakes.py`'s own comparisons.
- `gates/gates.py` is this repo's existing **fail-closed, deterministic,
  0-LLM gate** direction (its own module docstring: "게이트가 막으면
  재시도가 아니라 에스컬레이션이다"). It currently checks two things at
  spawn/CI time: protected-path writes (`writeset`) and unverifiable new
  dependencies (`deps`) — both keyed off a work-tree diff against
  `origin/main`. It has no concept of record/frontmatter content today.
  `gates/ci.py` is the CI-time entry point (spec-less subset of the same
  checks); `gates.check`/`ALL` is the router-time entry point (used with a
  `spec.md` write-set).
- `on-the-record/hooks/deliverable-guard.sh` + `hooks.json` is this repo's
  existing **PreToolUse (Write|Edit|MultiEdit|NotebookEdit)** hook,
  matcher-scoped, reading the tool-call JSON off stdin, inspecting
  `tool_input.file_path`, and denying (`exit 2`, message to stderr) when a
  condition holds — same shape the issue's "PreToolUse gate" option means.
  It is deny-only and fails closed on any non-0/2 exit (`trap ... EXIT`).
- A second, same-shaped hook, `board-gate.sh` (referenced live in this very
  session — e.g. "writing docs/issue-85/ requires branch issue-85/coding"),
  lives in the **separate** `tokenmaxxxer-core` repo, not in this
  (`on-the-record`) repo. It enforces subject/branch alignment on writes
  under `docs/issue-<n>/`. It is the issue's "board-gate extension" option,
  but it is out of this repo's write set — extending it is a
  `tokenmaxxxer-core` change, not an `on-the-record` change.
- `PROTECTED_ROOT_DIRS = {"roles", "gates", ...}` in `gates/gates.py`
  means any PR touching `roles/*.json` or `gates/gates.py` is flagged by
  `is_protected()` and blocked at CI/router time pending human attention
  ("파이프라인이 자기 규칙을 다시 쓸 수 없어야 한다"). This proposal's
  write set necessarily touches both — expected to escalate, not merge
  silently; noted here so phase 2 isn't surprised by it.

## The gap

Nothing in this repo validates a written record's machine-judged fields
(`verdict`, `loop_state`) against the role's declared enum at write time.
The only enum declaration that exists is prose inside `produces`, which no
code reads. The fix has to do two things: (1) make each role's enum
machine-readable, (2) check a record write against it before the write
lands, loud-refusing (not routing-no-op) on mismatch — matching this
repo's own "불확실하면 막는다" gate direction.
