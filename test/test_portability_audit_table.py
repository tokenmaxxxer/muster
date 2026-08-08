import re
from pathlib import Path

REPORT_PATH = Path(__file__).resolve().parent.parent / "docs" / "issue-444" / "reports" / "conformance-review.md"

# Closed issues numbered #310-#441 in tokenmaxxxer/on-the-record, captured via
# `gh issue list --state closed --json number` (2026-08-08). Many numbers in
# this range belong to PRs, not issues, so the in-scope set is this explicit
# list rather than the full numeric range.
IN_SCOPE_ISSUES = [
    310, 312, 313, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329,
    330, 331, 332, 333, 334, 335, 336, 341, 358, 360, 362, 363, 367, 369, 371,
    373, 374, 376, 377, 379, 383, 384, 388, 390, 391, 392, 396, 398, 406, 407,
    411, 412, 414, 415, 416, 419, 424, 427, 428, 432, 435, 441,
]

CATEGORY_ALIASES = {
    "repo-local": "Repo-local",
    "prose-only": "Prose-only",
    "deployed surface": "Deployed surface",
}


def _load_table_rows():
    text = REPORT_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Issue") and "Category" in line:
            header_idx = i
            break
    assert header_idx is not None, "classification table header not found"

    rows = []
    for line in lines[header_idx + 2 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 5:
            continue
        issue_cell, title, category, evidence, followup = cells[0], cells[1], cells[2], cells[3], cells[4]
        m = re.match(r"#(\d+)", issue_cell)
        if not m:
            continue
        issue_num = int(m.group(1))
        rows.append(
            {
                "issue": issue_num,
                "title": title,
                "category": category,
                "evidence": evidence,
                "followup": followup,
            }
        )
    return rows


def test_report_file_exists():
    assert REPORT_PATH.exists(), f"missing {REPORT_PATH}"


def test_one_row_per_in_scope_closed_issue():
    rows = _load_table_rows()
    seen = [r["issue"] for r in rows]

    in_scope_seen = [n for n in seen if n in IN_SCOPE_ISSUES]
    counts = {}
    for n in in_scope_seen:
        counts[n] = counts.get(n, 0) + 1

    duplicates = {n: c for n, c in counts.items() if c > 1}
    assert not duplicates, f"issues appearing more than once: {duplicates}"

    missing = sorted(set(IN_SCOPE_ISSUES) - set(in_scope_seen))
    assert not missing, f"in-scope issues missing a row: {missing}"


def test_every_row_has_a_file_path_citation():
    rows = _load_table_rows()
    path_pattern = re.compile(r"`[^`]*\.[A-Za-z0-9_]+`|`[^`]*/[^`]*`")
    for r in rows:
        assert path_pattern.search(r["evidence"]), (
            f"issue #{r['issue']} evidence lacks a file-path citation: {r['evidence']!r}"
        )


def test_repo_local_and_prose_only_rows_have_nonempty_followup():
    rows = _load_table_rows()
    for r in rows:
        category = r["category"].replace("*", "").strip().lower()
        if category in ("repo-local", "prose-only"):
            followup = r["followup"].strip()
            assert followup and followup.lower() not in ("none", "n/a", "-"), (
                f"issue #{r['issue']} ({r['category']}) has an empty/placeholder follow-up: {followup!r}"
            )
