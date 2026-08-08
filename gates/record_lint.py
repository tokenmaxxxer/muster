"""issue-517 — aggregate, single-pass record lint.

Authoring a role record today costs one model turn per gate refusal:
`record_enums`/`record_wellformed`/... in `gates.py` and the four checks
mirrored inline in `on-the-record/hooks/record-claim-guard.sh` each
report only their own first failure, and there is no single command an
author can run before writing to see every violation at once (a
7-refusal loop was observed on issue-512 phase 2).

`lint_record(path)` is a thin aggregator: it calls the existing
`gates.py` check functions (unchanged — this module adds no new rule
logic for anything they already cover) plus four checks lifted here
from `record-claim-guard.sh`'s inline regexes, and unions every
violation into one list. `record-claim-guard.sh` and `gates/ci.py` call
back into this module's functions instead of carrying their own copies,
so each rule's logic lives in exactly one place.

  python3 -m gates.record_lint <record-path>
  python3 -m gates.record_lint            # scans the whole repo
"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates

RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md

# Re-exported, not reimplemented: `gates/ci.py` and `record-claim-guard.sh`
# call these names on this module instead of holding their own copies —
# single source of truth means the same function object, not a mirror.
record_enums = gates.record_enums
record_wellformed_in = gates.record_wellformed_in
record_no_tool_residue_in = gates.record_no_tool_residue_in
record_checked_claims = gates.record_checked_claims


def _repo_root(start: Path) -> Path:
    """Walk up from `start` to the nearest `.git` — the target repo's
    root, not this plugin's own checkout (`gates.ON_THE_RECORD_ROOT`)."""
    p = start.resolve()
    if p.is_file():
        p = p.parent
    for cand in (p, *p.parents):
        if (cand / ".git").exists():
            return cand
    return start.resolve() if start.is_dir() else start.resolve().parent


# ---------------------------------------------------------------------------
# Checks lifted from record-claim-guard.sh's inline mirror (issue #457 Group
# A/B) — the hook used to carry these as a write-time-fragment approximation.
# Here they run against a record's full text, the shape issue #517 requires.
# ---------------------------------------------------------------------------

_UNVERIFIABLE_LINE = re.compile(r"(?im)^\s*[-*]?\s*unverifiable\s*:\s*(.*)$")
_CHECKED_CLAIM_LINE = re.compile(
    r"^\s*[-*]\s*.+—\s*checked:\s*(\S+)\s*—\s*"
    r"result:\s*(pass|fail|unverifiable)(?::\s*(.+))?\s*$")
_COUNT_RATIO = re.compile(r"\d+\s*(?:of|/)\s*\d+")
_COUNT_NOUN = re.compile(
    r"\d+\s+(?:detection\s+)?(?:items?|works?|checks?|cases?|tests?)\b")
_CLAIM_DERIVED_TAG = re.compile(r"`derived:\s*\S.*?`")
_PATH_REF = re.compile(
    r"`((?:src|test|tests|docs|gates|on-the-record)/[^`\s]+)`")


def unverifiable_reason_check(text: str) -> list[str]:
    """#310/#331 mirror: an `unverifiable:` escape line needs a reason."""
    bad = []
    for m in _UNVERIFIABLE_LINE.finditer(text):
        if not m.group(1).strip():
            bad.append(
                "`unverifiable:` 줄에 이유가 없다 (issue #310) — "
                "`unverifiable: <이유>` 형태로 왜 기계 검사가 불가능한지 "
                "적어야 한다.")
    return bad


def checked_claim_reason_check(text: str) -> list[str]:
    """#331 mirror: an Acceptance-verification `unverifiable` result needs
    a reason."""
    bad = []
    for ln in text.splitlines():
        cm = _CHECKED_CLAIM_LINE.match(ln)
        if not cm:
            continue
        result, reason = cm.group(2), cm.group(3)
        if result == "unverifiable" and not (reason and reason.strip()):
            bad.append(
                "Acceptance verification 의 `unverifiable` 항목에 이유가 "
                f"없다 (issue #331): {ln.strip()!r}")
    return bad


def bare_count_claim_check(text: str) -> list[str]:
    """#333 mirror: a bare "N of M"/"N items" count needs `derived:` or a
    code-fence reproduction — fences are excluded."""
    bad = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for pat in (_COUNT_RATIO, _COUNT_NOUN):
            for cm in pat.finditer(line):
                tail = line[cm.end():]
                if _CLAIM_DERIVED_TAG.match(tail.lstrip()):
                    continue
                bad.append(
                    "레코드에 근거 없는 개수 주장 (issue #333): "
                    f"{line.strip()!r} — 숫자가 코드펜스 재현이나 "
                    "`derived: ...` 인용 없이 그냥 타이핑되어 있다.")
                break
    return bad


def orphaned_path_reference_check(root: Path, text: str) -> list[str]:
    """#330 mirror: a backtick-quoted relative path that resolves nowhere
    in the working tree."""
    bad = []
    for m in _PATH_REF.finditer(text):
        ref = m.group(1)
        if any(ch in ref for ch in ("*", "?", "<", ">")):
            continue
        if not (root / ref).exists():
            bad.append(
                "레코드가 존재하지 않는 경로를 참조한다 (issue #330): "
                f"`{ref}` — 리치(reach)가 끊긴 참조다.")
    return bad


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def lint_record(path: Path) -> list[str]:
    """Run every record rule against one record file's full text and
    return the complete violation list — no first-failure abort.

    Delegates to `gates.py`'s existing diff-scoped check functions (they
    already accept a repo root and internally scan `changed_files()`,
    which covers uncommitted worktree edits — the common authoring case
    of a record just written/scaffolded), filtered down to violations
    naming this specific file, plus the four full-text checks above.
    """
    path = Path(path).resolve()
    root = _repo_root(path)
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.name
    text = path.read_text(encoding="utf-8-sig", errors="replace") if path.exists() else ""

    bad: list[str] = []
    if not RECORD_PATH.match(rel):
        bad.append(
            f"레코드 경로 형태가 아니다: {rel} — "
            "docs/issue-<n>/reports/<role>.md 형태여야 한다.")
        return bad
    if not path.exists():
        bad.append(f"레코드 파일이 없다: {rel}")
        return bad

    diff_scoped = []
    try:
        diff_scoped += gates.record_enums(root, {})
        diff_scoped += gates.record_refusal_reasoned(root, {})
        diff_scoped += gates.record_wellformed_in(root)
        diff_scoped += gates.record_no_tool_residue_in(root)
        diff_scoped += gates.record_derived_counts_in(root)
        diff_scoped += gates.record_checked_claims(root, {})
        diff_scoped += gates.reach_check(root, text)
        diff_scoped += gates.sibling_mention_check(root, text)
    except RuntimeError as e:
        bad.append(str(e))
    # These functions report against every changed record, not just this
    # one — keep only violations that name this file.
    bad += [b for b in diff_scoped if rel in b]

    bad += unverifiable_reason_check(text)
    bad += checked_claim_reason_check(text)
    bad += bare_count_claim_check(text)
    bad += orphaned_path_reference_check(root, text)
    return bad


def find_records(root: Path) -> list[Path]:
    """All `docs/issue-*/reports/*.md` record files tracked or present
    under `root` — used by the whole-repo scan mode."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            full = Path(dirpath) / fn
            rel = full.relative_to(root).as_posix()
            if RECORD_PATH.match(rel):
                out.append(full)
    return out


def main(argv: list[str]) -> int:
    target = Path(argv[0]) if argv else Path(".")
    if target.is_dir():
        records = find_records(target)
        if not records:
            print("record_lint: no records found under "
                  f"{target.resolve()} — 검사할 레코드가 없다.")
            return 0
        exit_code = 0
        for rec in sorted(records):
            violations = lint_record(rec)
            if violations:
                exit_code = 1
                print(f"== {rec} ==")
                for v in violations:
                    print(f"- {v}")
        return exit_code

    violations = lint_record(target)
    if not violations:
        print(f"record_lint: {target} — 위반 없음.")
        return 0
    for v in violations:
        print(f"- {v}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
