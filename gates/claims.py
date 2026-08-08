"""issue-377 — stale self-description claim checker.

A stale-but-confident description (comment, docstring, role JSON,
workflow comment) is worse than no description: it ends an inquiry an
absence would have continued. This reuses `record_fulfils_diff`'s shape
(#155): an author states a checkable claim explicitly via a marker
comment, and this module evaluates it mechanically — no NLP inference
over free text, which would launder unverified inference through a tool
that looks authoritative (the exact failure this issue reports).

Marker: `# CLAIM-CHECK: <kind> <args>` anywhere in a tracked file.
Two kinds only:

- `enum-subset <json-path>:<dotted-key> <glob>:<frontmatter-key>` —
  every value found for `<frontmatter-key>` in the frontmatter of files
  matching `<glob>` must appear in the JSON array at `<json-path>`'s
  `<dotted-key>` (dot-separated nested-dict path).
- `producer-exists <filename>` — at least one file named `<filename>`
  must exist anywhere in the repo tree.

A `CLAIM-CHECK` line with an unrecognized kind or malformed args is
itself a failure — fail closed, never silently skipped.

  python3 -m gates.claims .
"""
from __future__ import annotations
import glob as globmod
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates

_CLAIM_LINE = re.compile(r"#\s*CLAIM-CHECK:\s*(\S+)\s+(.*)$")


def _tracked_claim_lines(repo: Path) -> list[tuple[str, int, str]]:
    """(path, lineno, rest-of-marker) for every `# CLAIM-CHECK:` line in a
    tracked file. `git grep` fails on an empty repo/no matches (exit 1) —
    that is "no markers", not an error.

    Scoped to code/config files (`.py`/`.sh`/`.yml`/`.yaml`) — `.md` docs
    that merely *describe* the marker syntax in prose (this module's own
    docstring, proposals) are not markers and must not be evaluated as
    ones. `gates/claims.py`/`gates/test_claims.py` are excluded too: they
    are this checker's own source and test fixtures, which necessarily
    contain the marker string as text/regex source/example data, not as
    live claims about *their own* staleness."""
    p = subprocess.run(
        ["git", "-C", str(repo), "grep", "-n", "CLAIM-CHECK:", "--",
         "*.py", "*.sh", "*.yml", "*.yaml",
         ":!gates/claims.py", ":!gates/test_claims.py"],
        capture_output=True, text=True)
    if p.returncode not in (0, 1):
        raise RuntimeError(f"git grep 실패: {p.stderr.strip()}")
    out = []
    for line in p.stdout.splitlines():
        m = re.match(r"^([^:]+):(\d+):(.*)$", line)
        if not m:
            continue
        path, lineno, text = m.group(1), int(m.group(2)), m.group(3)
        cm = _CLAIM_LINE.search(text)
        if not cm:
            continue
        out.append((path, lineno, f"{cm.group(1)} {cm.group(2)}".strip()))
    return out


def _nested_get(obj, dotted_key: str):
    cur = obj
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def _check_enum_subset(repo: Path, args: str) -> str | None:
    m = re.match(r"^(\S+):(\S+)\s+(\S+):(\S+)$", args)
    if not m:
        return f"파싱 불가: 'enum-subset {args}' 는 '<json-path>:<key> <glob>:<frontmatter-key>' 형식이 아니다"
    json_path, key, glob_pat, fm_key = m.groups()
    jf = repo / json_path
    if not jf.is_file():
        return f"claim 대상 파일이 없다: {json_path}"
    try:
        data = json.loads(jf.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return f"{json_path} 파싱 실패: {e}"
    allowed, ok = _nested_get(data, key)
    if not ok or not isinstance(allowed, list):
        return f"{json_path} 에 '{key}' 경로의 배열이 없다"
    allowed_set = set(allowed)

    unmatched = []
    for f in sorted(repo.glob(glob_pat)):
        if not f.is_file():
            continue
        fm = gates.record_frontmatter(
            f.read_text(encoding="utf-8-sig", errors="replace"))
        if fm_key not in fm:
            continue
        value = fm[fm_key]
        if value not in allowed_set:
            unmatched.append(f"{f.relative_to(repo)}:{fm_key}={value!r}")
    if unmatched:
        return (f"enum-subset 위반: {json_path}:{key} = {sorted(allowed_set)} "
                f"에 없는 값 — {', '.join(unmatched)}")
    return None


def _check_producer_exists(repo: Path, args: str) -> str | None:
    filename = args.strip()
    if not filename or "/" in filename or " " in filename:
        return f"파싱 불가: 'producer-exists {args}' 는 파일명 하나가 아니다"
    excluded = gates._excluded_tree_dirs(repo)
    matches = []
    for dirpath, dirnames, filenames in os.walk(repo):
        gates._prune_excluded(dirnames, excluded)
        if filename in filenames:
            matches.append(Path(dirpath) / filename)
    if not matches:
        return f"producer-exists 위반: '{filename}' 이름의 파일이 트리 어디에도 없다"
    return None


def check_claims(repo: Path) -> list[str]:
    bad = []
    for path, lineno, rest in _tracked_claim_lines(repo):
        loc = f"{path}:{lineno}"
        kind, _, args = rest.partition(" ")
        if kind == "enum-subset":
            msg = _check_enum_subset(repo, args)
        elif kind == "producer-exists":
            msg = _check_producer_exists(repo, args)
        else:
            msg = f"알 수 없는 claim 종류 {kind!r} (enum-subset/producer-exists 만 허용, fail closed)"
        if msg:
            bad.append(f"{loc} — {msg}")
    return bad


def check(d: Path, cfg: dict) -> list[str]:
    return check_claims(d)


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    findings = check_claims(target)
    for f in findings:
        print(f)
    print(f"{len(findings)} claim failure(s)")
    sys.exit(1 if findings else 0)
