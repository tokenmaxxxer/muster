# Issue #105 — Current-State Survey (coding)

## Scout: skipped

Skip condition: internal control-plane gate with no external product
analog; the issue text and #100's precedent already fix the mechanism
(extend `gates/gates.py`'s existing fail-closed checks). Only
implementation detail is open. Current-state survey (this repo's own
gate code) is the deciding input, same as #100.

## What exists today

- `spawn.py:777` `frontmatter(p)` and `gates/gates.py`'s
  `record_frontmatter(text)` (added on branch `issue-100/coding`,
  commit `26a8a18`, **not yet merged to `main`**) are both shallow `---`
  parsers with the same shape: if `text` doesn't start with `"---"`, or
  `text.split("---", 2)` yields fewer than 3 parts, the function returns
  `{}` — an **empty dict**, indistinguishable from "well-formed record
  with no frontmatter fields set." Nothing downstream can tell
  "malformed/missing frontmatter" apart from "valid record, empty
  frontmatter."
- `gates/gates.py`'s `record_enums` (same commit) only checks fields it
  finds *inside* the parsed frontmatter dict against each role's declared
  enum. If parsing produced `{}` because the block was unparseable, there
  is nothing to iterate — `record_enums` returns no violations. A record
  committed with broken/missing `----` delimiters passes this gate
  silently. This reproduces exactly the issue's first failure mode
  ("committed without ----wrapped frontmatter -> loop_state
  unparseable -> wake branch silently dead, still on `main`").
- `wakes.py` (per #100's survey) reads records via `spawn.frontmatter()`
  and does exact-match comparisons on `loop_state`/`verdict` — a record
  whose frontmatter never parsed simply yields `{}`, so every comparison
  silently misses. No error, no log line naming the record.
- Nothing in `gates/gates.py` or `spawn.py` inspects the record **body**
  (post-frontmatter content) at all today. There is no tool-tag-residue
  concept anywhere in the codebase — issue #105's second failure mode
  (`</content>` leaked at EOF) has no existing detector.
- `gates/gates.py`'s registration point is `ALL = {"writeset": writeset,
  "deps": deps, "record_enums": record_enums}` (on `issue-100/coding`,
  not yet on `main`) at the bottom of the file, plus a matching call in
  `gates/ci.py`. Both #100 checks are keyed off `changed_files()` (fails
  closed on diff failure) and iterate `RECORD_PATH =
  re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")` — the same
  record-path shape this issue's new checks must match.
- `gates/gates.py`'s own module docstring states the fail-closed
  direction this issue must follow: "게이트가 막으면 재시도가 아니라
  에스컬레이션이다" / "불확실하면 막는다" — unparseable is a block, not a
  pass, same principle #100 already applied to missing role files.
- Dependency note for phase 2: `issue-100/coding`'s `record_enums` +
  `record_frontmatter` are the natural home for this issue's frontmatter
  check (same file, same helper), but that branch is not yet merged to
  `main` (only its phase-1 docs merged via PR #102; the code commit
  `26a8a18` sits unmerged on the branch). This issue's write set does not
  depend on `record_enums` existing — the new checks are independent
  functions in `gates/gates.py`, addable to `ALL` regardless of merge
  order — but phase 2 should re-check whether `issue-100/coding` has
  landed by then and share `RECORD_PATH`/parsing helpers instead of
  redefining them if so.

## The gap

Two write-time holes, both silent-pass today:

1. A record whose frontmatter block is missing, missing its second
   `---` delimiter, or otherwise fails the shallow parse yields `{}`
   from every existing parser — structurally indistinguishable from
   "no frontmatter fields declared." No gate flags this; the record
   commits, and `loop_state`/`verdict` reads downstream silently miss.
2. A record body is never inspected for tool-output residue (leaked
   closing/opening tags like `</content>`, `<result>`, or similar) left
   over from an agent's own tool-call transcript bleeding into the
   record file. No detector exists.

Both need a write-time, fail-closed, loud-refusal check in
`gates/gates.py`, consistent with #100's direction — but neither can
reuse `record_enums`'s "field not present -> skip" logic, since the
whole point here is treating *absence of a parseable structure* itself
as the violation, not a per-field enum mismatch.
