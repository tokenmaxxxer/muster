# Issue #105 — Phase 1 Proposal (coding)

files:
- `gates/gates.py` (two new check functions: `record_wellformed` and
  `record_no_tool_residue` + registration in `ALL`)
- `gates/ci.py` (wire both checks into the CI-time `check()` call, same
  place `record_enums`/`deps`/`writeset` are wired)
- `test_gates.py` (tests for both new checks)
- No `roles/*.json` changes — these checks are structural (every record),
  not per-role enum declarations.

## Request (paraphrased)

Two silent routing killers observed on live boards, neither caught by the
enum gate from #100: (1) a record committed without a well-formed
`----`-delimited frontmatter block, so `loop_state` parses to nothing and
a wake branch silently dies while the record sits merged on `main`; (2) a
record with leaked tool-tag residue (e.g. `</content>`) after the body,
left over from an agent's tool-call transcript bleeding into the file.
Add write-time gate checks that refuse both, fail-closed and loud,
consistent with this repo's existing gate direction.

## Constraints

- Fail-closed, same principle `gates/gates.py`'s docstring already states
  ("불확실하면 막는다") and `record_enums` (#100) already applies to
  missing role files: an unparseable structure is refused, never treated
  as "nothing to check."
- Frontmatter well-formedness is a **presence/shape** check, distinct
  from #100's `record_enums` (which checks *values inside* an already-
  parsed frontmatter dict). It must fire even when zero `record_fields`
  are declared for a role, and it must fire on the exact failure the
  current shallow parser silently swallows: missing leading `---`, or a
  block missing its closing `---` (i.e. `text.split("---", 2)` yielding
  fewer than 3 parts).
- Tool-tag-residue detection targets **leaked tool-transcript markup**,
  not arbitrary angle brackets a record may legitimately contain (code
  fences quoting HTML/XML, prose describing a tag by name). Scope: a line
  that is *only* an XML-ish tag (`</?[A-Za-z][\w-]*>`, optionally with
  simple attributes) sitting outside a fenced code block (` ``` `),
  anywhere in the record body — not just EOF, since a leaked tag could
  appear mid-body from a truncated/interleaved tool response, and the
  issue's own EOF example is one instance of the pattern, not the whole
  scope. Fenced code blocks are exempted because a record legitimately
  quoting `</content>` inside a ```` ``` ```` block (e.g. explaining this
  very gate) is not residue.
- Both checks key off the same `docs/issue-<n>/reports/<role>.md` path
  shape #100 already matches (`RECORD_PATH` in `gates/gates.py`), and off
  the same fail-closed `changed_files()` helper — no new diff mechanism.
- This proposal does not depend on `record_enums` / `record_frontmatter`
  (from #100, commit `26a8a18`) being merged to `main` first — per the
  survey, that commit sits unmerged on `issue-100/coding`. The new checks
  are independent functions addable to `gates/gates.py`'s `ALL` dict
  regardless of merge order. If `record_enums` has landed by phase 2,
  `record_wellformed` should share/call its `record_frontmatter` helper
  rather than redefining a third shallow parser; if not, phase 2 adds its
  own local shallow-split check scoped to presence, not values.
- No `roles/*.json` change and no `PROTECTED_ROOT_DIRS` interaction beyond
  what already applies to `gates/gates.py` itself (already protected;
  expected to escalate to human review on this PR, not a defect).
- Backward compatibility: only the changed-files diff is checked (same as
  every existing check) — already-merged malformed records on `main` are
  not retroactively flagged.

## What will be done

### 1. `gates/gates.py`: `record_wellformed` check

```python
def record_wellformed(d: Path, cfg: dict) -> list[str]:
    """변경된 docs/issue-<n>/reports/<role>.md 가 well-formed `---`
    frontmatter 블록을 가졌는지 검사한다. 파싱 실패는 '검사할 필드 없음'이
    아니라 차단 사유다."""
```

- Reuses `changed_files()` + `RECORD_PATH` (matching #100's shape) to
  find changed top-level role records.
- For each match: read the file; block if it does not start with `---`,
  or if splitting on `---` (max 2 splits) yields fewer than 3 parts (no
  closing delimiter found) — the exact condition the existing shallow
  parsers currently swallow into `{}`.
- Message names the file and the specific defect ("frontmatter 시작
  구분자(`---`) 없음" vs "닫는 구분자 없음"), e.g.:
  `f"레코드 frontmatter 파싱 불가: {path} — {reason}. loop_state/verdict 를
  읽을 수 없어 wake 라우팅이 조용히 죽는다."`

### 2. `gates/gates.py`: `record_no_tool_residue` check

```python
def record_no_tool_residue(d: Path, cfg: dict) -> list[str]:
    """레코드 본문에 툴 호출 트랜스크립트가 새어들어온 흔적(고립된 XML 태그
    한 줄)이 있는지 검사한다. 코드펜스 안은 제외한다."""
```

- Same `changed_files()` + `RECORD_PATH` scope.
- Walk the file body (after the frontmatter block, or the whole file if
  frontmatter didn't parse — a malformed record can carry both defects,
  and `record_wellformed` already blocks that case independently, but
  residue-scanning should not skip a file just because frontmatter also
  failed), tracking fenced-code-block state (toggle on lines starting
  with ` ``` `).
- Outside a fence, a line matching `^\s*</?[A-Za-z][\w-]*\s*/?>\s*$`
  (whole line is one tag, optional self-closing) is residue. Block with
  the file, line number, and the matched tag text.
- Message: `f"레코드에 툴 태그 잔여물: {path}:{lineno} — {tag!r}. 에이전트
  툴 출력이 레코드 본문에 새어들어왔다."`

### 3. Register both, wire into CI

- `ALL["record_wellformed"] = record_wellformed`,
  `ALL["record_no_tool_residue"] = record_no_tool_residue` in
  `gates/gates.py`.
- Add both names to whatever check-list `gates/ci.py::check()` already
  passes for CI-time enforcement (same place `deps`/`writeset`/
  `record_enums` are listed, repo-root form).

### 4. Tests (`test_gates.py`)

- A record missing the opening `---` is blocked, message names the file.
- A record with an opening `---` but no closing `---` is blocked.
- A well-formed record with valid frontmatter passes `record_wellformed`.
- A record with a bare `</content>` line in the body is blocked by
  `record_no_tool_residue`, message names file + line + tag.
- The same tag text appearing inside a ```` ``` ```` fence does not block.
- A record with no tag-shaped lines passes.
- A record with both defects (malformed frontmatter AND leaked tag) is
  blocked by both checks independently (neither masks the other).

## Out of scope

- Retroactively scanning/fixing already-merged records on `main`.
- Any change to `roles/*.json`, `spawn.py`, or `wakes.py` — this proposal
  is a write-time refusal upstream of those readers, not a change to how
  they read.
- A PreToutTool-time (inside a live role session) version of this check
  in `tokenmaxxxer-core`'s `board-gate.sh` — that is a separate repo, same
  boundary #100 already drew; this proposal covers CI/router-time
  enforcement in `on-the-record` only.
- Enumerating every conceivable leaked-tag name (`</content>`,
  `<result>`, `<system-reminder>`, etc.) as a hardcoded list — the
  generic "isolated XML-tag-shaped line outside a code fence" pattern is
  chosen specifically so it doesn't need updating every time a new tool
  tag shape appears.
- Merging or depending on `issue-100/coding`'s unmerged `record_enums`
  commit; phase 2 reconciles with it if it has landed by then, but does
  not block on it landing first.

## How we'll know it worked

- `gates/gates.py::ALL` contains `record_wellformed` and
  `record_no_tool_residue`; `gates/ci.py::check` calls both.
- `python3 -m pytest test_gates.py` passes, including all new cases
  listed above.
- Manually reproducing both trigger cases from the issue — a record
  missing its `---` block, and a record with a trailing `</content>`
  line — causes the gate to block with a message naming the file (and,
  for residue, the line) instead of silently landing.
- `PROTECTED_ROOT_DIRS`-triggered escalation on this PR (touching
  `gates/`) is expected, not a defect.
