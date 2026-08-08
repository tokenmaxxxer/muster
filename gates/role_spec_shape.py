#!/usr/bin/env python3
"""role-spec shape checker (issue #521, realizing the #515 template).

Hand-rolled, no `jsonschema` dependency (proposal constraint: `jsonschema`
is not declared in this repo's own manifest and isn't used elsewhere in
`gates/`; adding it as a real dependency would need a manifest entry +
handbook note for a shape check simple enough to hand-roll, same style as
`gates/spec_index.py`).

Checks a role's `roles/specs/<name>.spec.json` against the shape
`docs/specs/role-spec-template.schema.json` documents: required top-level
keys present, `required_fields[].type` in the closed set, `enum` non-empty
when `type: enum`, `loop_state` carries exactly the 4 buckets each as a
list, `use_when.board_condition` present as a string.

  python3 gates/role_spec_shape.py roles/specs/<name>.spec.json
  exit 0 pass / 1 fail (prints reasons to stderr)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

_TOP_REQUIRED = (
    "role", "source_standard", "required_fields", "reference_resolution",
    "recomputation", "write_scope", "loop_state", "use_when",
)
_FIELD_TYPES = {"string", "enum", "ref", "ref[]"}
_LOOP_BUCKETS = {"progress", "terminal", "refusal", "error"}


def check(spec: dict) -> list[str]:
    """Reasons the spec fails the shape check. Empty list means pass."""
    bad = []
    if not isinstance(spec, dict):
        return ["spec is not a JSON object"]

    for k in _TOP_REQUIRED:
        if k not in spec:
            bad.append(f"missing top-level key: {k}")
    if bad:
        return bad

    rf = spec["required_fields"]
    if not isinstance(rf, list) or not rf:
        bad.append("required_fields must be a non-empty array")
    else:
        for i, f in enumerate(rf):
            if not isinstance(f, dict):
                bad.append(f"required_fields[{i}] is not an object")
                continue
            for k in ("name", "type", "required"):
                if k not in f:
                    bad.append(f"required_fields[{i}] missing key: {k}")
            t = f.get("type")
            if t is not None and t not in _FIELD_TYPES:
                bad.append(f"required_fields[{i}].type '{t}' not in {sorted(_FIELD_TYPES)}")
            if t == "enum":
                enum_vals = f.get("enum")
                if not isinstance(enum_vals, list) or not enum_vals:
                    bad.append(f"required_fields[{i}] type=enum but enum is missing/empty")

    for section in ("reference_resolution", "recomputation"):
        s = spec.get(section)
        if not isinstance(s, dict) or "rule" not in s or "checked_by" not in s:
            bad.append(f"{section} must be an object with 'rule' and 'checked_by'")

    ws = spec.get("write_scope")
    if not isinstance(ws, list):
        bad.append("write_scope must be an array")
    elif not ws and not spec.get("report_only"):
        bad.append("write_scope is empty but report_only is not true")

    ls = spec.get("loop_state")
    if not isinstance(ls, dict) or set(ls.keys()) != _LOOP_BUCKETS:
        bad.append(f"loop_state must have exactly the keys {sorted(_LOOP_BUCKETS)}")
    else:
        for bucket, vals in ls.items():
            if not isinstance(vals, list):
                bad.append(f"loop_state.{bucket} must be an array")
        if not ls.get("terminal"):
            bad.append("loop_state.terminal must be non-empty")

    uw = spec.get("use_when")
    if not isinstance(uw, dict) or not isinstance(uw.get("board_condition"), str) or not uw.get("board_condition"):
        bad.append("use_when.board_condition must be a non-empty string")

    return bad


_VERIFICATION_FAMILY_ROLES = (
    "execution-observation", "conformance-review", "defect-verification",
    "security-threat-model", "accessibility", "secure-coding",
)


def record_path_role(rel_path: str) -> str | None:
    """When rel_path is one of the 6 batch-1 roles' own record file
    (docs/issue-<n>/reports/<role>.md), return the role name; else None.
    Used by role-spec-reference-guard.sh to scope the reference-resolution
    check to exactly the roles whose spec.json declares it (issue-521
    requirement 1's reference_resolution.rule)."""
    import posixpath
    n = posixpath.normpath(rel_path.replace("\\", "/"))
    m = None
    import re
    m = re.match(r"^(?:.*/)?docs/issue-[^/]+/reports/([^/]+)\.md$", n)
    if not m:
        return None
    role = m.group(1)
    return role if role in _VERIFICATION_FAMILY_ROLES else None


def reference_resolution_check(content: str, repo_root) -> list[str]:
    """Every backtick-quoted relative path referenced in a batch-1 role's
    record content must resolve to a real path in the working tree — the
    reference_resolution.rule every roles/specs/*.spec.json declares
    ('ref'/'ref[]' fields must resolve to an existing repo path, commit
    sha, or line-anchored citation; issue-515 invariant 2). Delegates to
    record_lint's orphaned-path check, the same logic record-claim-guard.sh
    already applies to docs/issue-*/reports/** generally — this function
    exists so role-spec-reference-guard.sh can invoke it standalone
    (its own hook entry, scoped to just the 6 verification-family roles)
    without importing gates/record_lint.py from the shell wrapper."""
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).parent))
    import record_lint
    return record_lint.orphaned_path_reference_check(_Path(repo_root), content)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: role_spec_shape.py <spec.json> [<spec.json> ...]", file=sys.stderr)
        return 1
    ok = True
    for path in argv:
        try:
            spec = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"{path}: unreadable/invalid JSON: {e}", file=sys.stderr)
            ok = False
            continue
        bad = check(spec)
        if bad:
            ok = False
            for reason in bad:
                print(f"{path}: {reason}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
