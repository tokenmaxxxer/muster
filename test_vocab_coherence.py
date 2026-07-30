#!/usr/bin/env python3
"""vocabulary-coherence test for wake-routing (issue #103).

Cross-checks every state/field value `wakes.py` consumes by exact-match
comparison against `docs/specs/loop-state-vocab.md`'s declared vocab.
A consumed value with no producer and no exemption fails the test.

No network, no GitHub access, no spawn.rulebook_dir() — the vocab doc
is the sole input.

  python3 test_vocab_coherence.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VOCAB_DOC = ROOT / "docs" / "specs" / "loop-state-vocab.md"

# Explicit list of (role, field, value, wakes.py call-site line) tuples
# consumed by exact-match comparison in wakes.py. MUST be kept in sync
# with wakes.py's literal comparisons by hand — if a new consumed
# literal is added to wakes.py without updating this list, this test
# will not catch it (it will only catch mismatches between what's
# listed here and what's declared in the vocab doc).
CONSUMED = [
    ("feasibility", "verdict", "go", 289),
    ("qa", "loop_state", "handed-off", 292),
    ("ux-design", "loop_state", "reviewed", 307),
    ("verify", "loop_state", "cleared", 321),
    ("review", "loop_state", "reported", 326),
    ("coding", "loop_state", "landed", 342),
]

# The human-only value: consumed at wakes.py's pre-approval gate, not
# produced by any role's declared vocab.
HUMAN_ONLY_VALUE = ("scope-approved", 275)


def _parse_vocab_doc(text: str):
    """Return (declared: {role: {values}}, allowlist: {value})."""
    declared = {}
    allowlist = set()

    role_section_re = re.compile(r"^### (\S+)\s*$", re.M)
    sections = list(role_section_re.finditer(text))
    for i, m in enumerate(sections):
        role = m.group(1)
        start = m.end()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        body = text[start:end]
        for bullet in re.findall(r"`([a-zA-Z_-]+):\s*([^`]+)`", body):
            field, value = bullet
            declared.setdefault(role, set()).add((field.strip(), value.strip()))

    allow_start = text.find("## Human-only allowlist")
    if allow_start != -1:
        allow_body = text[allow_start:]
        for bullet in re.findall(r"`([^`]+)`", allow_body):
            allowlist.add(bullet.strip())

    return declared, allowlist


def t_vocab_doc_exists():
    assert VOCAB_DOC.exists(), f"missing {VOCAB_DOC}"


def t_all_consumed_values_are_declared_or_allowlisted():
    text = VOCAB_DOC.read_text()
    declared, allowlist = _parse_vocab_doc(text)

    for role, field, value, line in CONSUMED:
        role_decls = declared.get(role, set())
        ok = (field, value) in role_decls
        assert ok, (
            f"wakes.py line {line}: roles.get({role!r}, {{}}).get({field!r}) "
            f"== {value!r} — value {value!r} for role {role!r} has no "
            f"producer declared in {VOCAB_DOC} and no exemption in the "
            f"human-only allowlist."
        )


def t_scope_approved_is_in_human_only_allowlist():
    text = VOCAB_DOC.read_text()
    _, allowlist = _parse_vocab_doc(text)
    value, line = HUMAN_ONLY_VALUE
    assert value in allowlist, (
        f"wakes.py line {line}: pre-approval gate checks state == {value!r} "
        f"— value {value!r} has no producer (no role reaches it) and is "
        f"not present in {VOCAB_DOC}'s human-only allowlist."
    )


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
