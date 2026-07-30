"""Regression guard: roles/*.json must not carry routing/wake prose.

The #120 sweep deleted the wake-routing mechanism (wakes.py,
docs/specs/wake-routing.md) but never checked roles/*.json content; #140
found residue there. This test asserts no role's decides/use_when/produces
string names routing/wake vocabulary going forward.
"""
import glob
import json
import os
import re

ROLES_DIR = os.path.join(os.path.dirname(__file__), "roles")
FIELDS = ("decides", "use_when", "produces")
ROUTING_VOCAB = re.compile(r"깨운|wakes\b|wake\b|라우팅", re.IGNORECASE)


def test_roles_have_no_routing_vocab():
    offenders = []
    for path in sorted(glob.glob(os.path.join(ROLES_DIR, "*.json"))):
        with open(path, encoding="utf-8") as fh:
            role = json.load(fh)
        for field in FIELDS:
            value = role.get(field)
            if isinstance(value, str) and ROUTING_VOCAB.search(value):
                offenders.append(f"{os.path.basename(path)}:{field} = {value!r}")
    assert not offenders, "routing/wake vocabulary found in roles/*.json:\n" + "\n".join(offenders)
