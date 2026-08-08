#!/usr/bin/env python3
"""issue #524 (follow-up D of #515, batch-2) — validate the 4 discovery/design-family
roles/specs/*.spec.json against the #515 realization template shape
(docs/specs/role-spec-template.schema.json, checked by gates/role_spec_shape.py).
Mirrors gates/test_role_spec_shape.py's structure with its own BATCH2_ROLES tuple
(proposal constraint: don't edit the batch-1 test file, keep each batch's own test
intent legible).

  python3 -m pytest gates/ -q -k "spec"
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import role_spec_shape

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "roles" / "specs"

BATCH2_ROLES = (
    "product-discovery",
    "user-discovery",
    "requirements-engineering",
    "interaction-design",
)


def test_batch2_spec_files_exist():
    for role in BATCH2_ROLES:
        assert (SPECS_DIR / f"{role}.spec.json").is_file(), f"missing spec: {role}"


def test_batch2_specs_pass_shape_check():
    bad = []
    for role in BATCH2_ROLES:
        path = SPECS_DIR / f"{role}.spec.json"
        spec = json.loads(path.read_text(encoding="utf-8"))
        reasons = role_spec_shape.check(spec)
        if reasons:
            bad.append(f"{path}: {reasons}")
    assert not bad, "\n".join(bad)


def test_batch2_specs_role_field_matches_filename():
    for role in BATCH2_ROLES:
        path = SPECS_DIR / f"{role}.spec.json"
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert spec.get("role") == role, f"{path}: role field {spec.get('role')!r} != {role!r}"
