# state-gate into core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the transition-machine judgment out of seven divergent copies of `state-gate.sh` and into one parameterized library in `tokenmaxxxer-core`, proven by making two roles' *existing* gate suites pass against it unchanged.

**Architecture:** core ships `hooks/lib/state_gate.py` — the whole decision, taking the role's constants and transition table as arguments. Each rulebook keeps its own `state-gate.sh`, which shrinks to a shim: fail-closed trap, kill switch, read `role.json`, call core's library. The role's `transition-rules.md` stays where it is and stays authoritative; nothing about a role's state vocabulary moves into core.

**Tech Stack:** bash 3.2 (macOS `/bin/bash`), Python 3 standard library only, git, `gh`.

## Why this shape, and what it is not

**This is not a role merge.** Contract §16 is titled "verify/review division of labor" and says the mechanism "does not merge the two roles' verdicts"; §4 makes their independence a rule. The two roles' *skills* were compared on 2026-07-27 and are genuinely different procedures — five-value `verdict:` per requirement versus two-value `outcome:` per attempt, and verify's own skill carries "do not treat a clean review-record as grounds to skip a reproduction attempt" as a refusal. **Skills do not move. Roles do not merge. Only the machine moves.**

**The seven copies are not one file plus role names.** Measured 2026-07-27, after substituting the role name and stripping comments and blank lines:

| role | total | substantive | role-substituted hash |
|---|---|---|---|
| product | 802 | 547 | e7adb510 |
| reflect | 798 | 540 | b99eb0bb |
| ux-design | 797 | 542 | be69d68a |
| verify | 796 | 515 | 4cdae9ba |
| review | 794 | 524 | db6905a6 |
| ops | 604 | 434 | 8f818afc |
| feasibility | 553 | 371 | 39343875 |

Seven distinct hashes. The two *closest* — review and reflect, a mirrored pair — still differ on 702 substantive lines, including `set -euo pipefail` versus `set -uo pipefail` and kill switches named `REVIEW_CYCLE_DISABLE` versus `REFLECT_CYCLE_OFF`. A mechanical `sed` migration is not available. This plan therefore does not attempt one: it builds the library against **one reference implementation**, then proves it on a **second, differently-shaped one**, and only then touches the other five.

**Which two, and why those.** `ops` is the reference: the 2026-07-27 proposal recorded it as the only copy that refuses a Bash write it cannot parse, where review's allowed it. `review` is the cross-check: it is the largest mature copy, it derives terminal states from the table where others hardcode them, and it has the most complete existing suite. The proposal's own acceptance test is exactly this pair — *"If `ops`'s suite and `review`'s suite both pass, core satisfies both — this is knowable before any migration."* This plan makes that sentence executable.

## Global Constraints

- **bash 3.2 compatible.** macOS ships bash 3.2.57 and that is what runs these hooks. Never nest a quoted heredoc inside `$( … )` — read the program into a variable at top level with `IFS='' read -r -d '' VAR <<'PY'` and pass it to `python3 -c "$VAR"`. `hooks/tests/parse-check.sh` enforces this in every repository; run it.
- **Python 3 standard library only.** No third-party imports.
- **Gates refuse; they never permit.** No hook may emit `permissionDecision: "allow"`. `deny-only-check.sh` enforces this in every repository; run it.
- **Fail closed.** Every gate installs the trap as its first executable statement: any exit that is neither 0 nor 2 becomes 2, because a PreToolUse hook treats a non-2 exit as non-blocking.
- **A role's state vocabulary never moves into core.** `transition-rules.md` stays in the rulebook and stays authoritative. core must contain no state name of any role.
- **No role's existing suite may lose a case.** A migration that makes a suite smaller is a migration that stopped testing something.
- **All prose in `tokenmaxxxer-core` is English.** Rulebook prose follows that rulebook's existing language.

---

### Task 1: `state_gate.py` — the judgment, parameterized

**Files:**
- Create: `core/hooks/lib/state_gate.py`
- Test: `core/hooks/tests/test_state_gate_lib.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `state_gate.RoleSpec` — a `NamedTuple` with fields `role: str`, `record_glob: str`, `legacy_record: str | None`, `rules_path: str`.
  - `state_gate.parse_rules(text: str) -> list[tuple[str, str, str, str]]` — the `(from, to, actor, precondition)` rows of a `transition-rules.md` table. Raises `RulesError` when the table is unreadable or has no rows.
  - `state_gate.terminal_states(rows) -> set[str]` — states that appear as a `to` and never as a `from`. Derived, never hardcoded.
  - `state_gate.judge(spec, rows, current, proposed) -> None` — returns on a legal transition, raises `Refused(msg)` otherwise.
  - `state_gate.RulesError`, `state_gate.Refused` — the two exception types a shim catches; both mean exit 2.

- [ ] **Step 1: Write the failing test**

`core/hooks/tests/test_state_gate_lib.py`:

```python
#!/usr/bin/env python3
"""The transition machine, with every role's vocabulary supplied as data.

There is no state name of any role in state_gate.py, and there must never be
one: the seven copies this replaces each carried their own, which is how they
drifted 702 substantive lines apart while sharing a filename.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import state_gate  # noqa: E402

# review's real table, abbreviated to the rows the assertions need.
REVIEW_RULES = """
| from | to | actor | precondition |
|---|---|---|---|
| (none) | idle | agent | the role opens the subject |
| idle | scoped | user | the user hands over a change and a specification |
| scoped | auditing | agent | scope agreed |
| auditing | auditing | user | an evidence or access request |
| auditing | draft-reported | agent | every requirement carries a verdict |
| draft-reported | reported | user | the user accepts the draft |
"""

SPEC = state_gate.RoleSpec(role="review",
                           record_glob="docs/reports/records/*/review.md",
                           legacy_record="review-record.md",
                           rules_path="/does/not/matter")


class ParseRules(unittest.TestCase):
    def test_reads_the_four_columns(self):
        rows = state_gate.parse_rules(REVIEW_RULES)
        self.assertIn(("idle", "scoped", "user",
                       "the user hands over a change and a specification"), rows)

    def test_drops_header_and_separator_rows(self):
        rows = state_gate.parse_rules(REVIEW_RULES)
        self.assertNotIn("from", [r[0] for r in rows])
        self.assertNotIn("---", [r[0] for r in rows])

    def test_no_rows_raises(self):
        # A gate that reads an empty table and allows everything is worse than
        # no gate: it reports that it is enforcing.
        for bad in ("", "# no table here", "| from | to | actor | precondition |"):
            with self.assertRaises(state_gate.RulesError):
                state_gate.parse_rules(bad)

    def test_short_rows_are_ignored_not_guessed(self):
        rows = state_gate.parse_rules(REVIEW_RULES + "\n| idle | scoped |\n")
        self.assertEqual(len([r for r in rows if r[0] == "idle"]), 1)


class TerminalStates(unittest.TestCase):
    def test_derived_from_the_table(self):
        rows = state_gate.parse_rules(REVIEW_RULES)
        self.assertEqual(state_gate.terminal_states(rows), {"reported"})

    def test_self_loop_is_not_terminal(self):
        # auditing -> auditing must not make auditing terminal.
        rows = state_gate.parse_rules(REVIEW_RULES)
        self.assertNotIn("auditing", state_gate.terminal_states(rows))


class Judge(unittest.TestCase):
    def setUp(self):
        self.rows = state_gate.parse_rules(REVIEW_RULES)

    def test_listed_transition_passes(self):
        state_gate.judge(SPEC, self.rows, "idle", "scoped")   # no raise

    def test_unlisted_transition_refuses(self):
        with self.assertRaises(state_gate.Refused):
            state_gate.judge(SPEC, self.rows, "idle", "reported")

    def test_same_state_passes_only_when_the_table_lists_it(self):
        state_gate.judge(SPEC, self.rows, "auditing", "auditing")
        with self.assertRaises(state_gate.Refused):
            state_gate.judge(SPEC, self.rows, "scoped", "scoped")

    def test_unknown_state_refuses_on_either_side(self):
        # A state outside the table is a broken input, never a free pass.
        for cur, new in (("idle", "banana"), ("banana", "idle")):
            with self.assertRaises(state_gate.Refused):
                state_gate.judge(SPEC, self.rows, cur, new)

    def test_bootstrap_uses_the_table_sentinel(self):
        state_gate.judge(SPEC, self.rows, None, "idle")
        with self.assertRaises(state_gate.Refused):
            state_gate.judge(SPEC, self.rows, None, "reported")

    def test_the_refusal_names_the_legal_moves(self):
        # A refusal that does not say what WAS legal makes the session guess,
        # and a guessing session retries at random.
        try:
            state_gate.judge(SPEC, self.rows, "idle", "reported")
        except state_gate.Refused as e:
            self.assertIn("idle", str(e))
            self.assertIn("scoped", str(e))
        else:
            self.fail("expected Refused")


class NoRoleVocabularyInCore(unittest.TestCase):
    def test_core_carries_no_role_state_names(self):
        """The whole point. If a state name lands here, the next role's
        migration will quietly inherit another role's machine."""
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "lib", "state_gate.py"),
                   encoding="utf-8").read()
        for name in ("auditing", "draft-reported", "reported", "reproducing",
                     "reproduced", "cleared", "scope-proposed", "probing"):
            self.assertNotIn('"%s"' % name, src, name)
            self.assertNotIn("'%s'" % name, src, name)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 core/hooks/tests/test_state_gate_lib.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'state_gate'`

- [ ] **Step 3: Write the implementation**

`core/hooks/lib/state_gate.py`:

```python
"""The transition machine, with the role's vocabulary supplied as data.

Seven rulebooks each carried their own copy of this judgment. Measured
2026-07-27, after substituting the role name and stripping comments, all seven
were distinct, and the two closest differed on 702 substantive lines. They also
disagreed on behaviour, not only on shape: some derive terminal states from the
table, others hardcode them; one refuses a Bash write it cannot parse where
another allowed it.

This module holds the judgment. It holds NO state name of any role — the table
in each rulebook's transition-rules.md remains the only place a role's
vocabulary is written down, and test_state_gate_lib.py fails if a state name
appears here.
"""
import re

__all__ = ["RoleSpec", "RulesError", "Refused", "NONE_STATE",
           "parse_rules", "terminal_states", "judge"]

# The bootstrap sentinel a table uses for "no record yet". It is punctuation,
# not a role's state, so it lives here rather than in a rulebook.
NONE_STATE = "(none)"

try:
    from typing import NamedTuple

    class RoleSpec(NamedTuple):
        role: str
        record_glob: str
        legacy_record: str
        rules_path: str
except ImportError:                                   # pragma: no cover
    raise


class RulesError(Exception):
    """The transition table could not be read. A gate that cannot read its
    table must refuse — reading an empty table and allowing everything is
    worse than having no gate, because it reports that it is enforcing."""


class Refused(Exception):
    """The proposed transition is not one the table permits."""


_ROW = re.compile(r"^\s*\|(.+)\|\s*$")


def parse_rules(text):
    """The `(from, to, actor, precondition)` rows of a transition table."""
    rows = []
    for line in (text or "").splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        parts = [p.strip() for p in m.group(1).split("|")]
        if len(parts) != 4:
            continue                     # not a four-column row: not our table
        if parts[0].lower() == "from" and parts[1].lower() == "to":
            continue                     # header
        if set(parts[0]) <= {"-"} or set(parts[1]) <= {"-"}:
            continue                     # markdown separator
        rows.append(tuple(parts))
    if not rows:
        raise RulesError("the transition table has no parseable rows")
    return rows


def known_states(rows):
    out = set()
    for frm, to, _actor, _pre in rows:
        out.add(frm)
        out.add(to)
    out.discard(NONE_STATE)
    return out


def terminal_states(rows):
    """States reachable but never departed. Derived, never hardcoded — a
    hardcoded set silently stops matching the day a state is added, and two
    of the seven copies had already drifted that way."""
    froms = {frm for frm, _to, _a, _p in rows if frm != _self_only(rows, frm)}
    tos = {to for _frm, to, _a, _p in rows}
    departs = {frm for frm, to, _a, _p in rows if to != frm}
    return {s for s in tos if s not in departs} - {NONE_STATE} or set()


def _self_only(rows, state):
    """`state` if its only outgoing edge is to itself, else a sentinel."""
    outs = {to for frm, to, _a, _p in rows if frm == state}
    return state if outs == {state} else None


def judge(spec, rows, current, proposed):
    """Return on a legal transition; raise Refused otherwise.

    `current` is None when no record exists yet — the table's own
    `(none)` row decides what may be written first.
    """
    cur = NONE_STATE if current is None else str(current).strip()
    new = str(proposed).strip()
    known = known_states(rows)

    if cur != NONE_STATE and cur not in known:
        raise Refused(
            "%s's record is in state %r, which is not in this role's "
            "transition table. The record is broken input, not a state to "
            "move from — fix the record before transitioning."
            % (spec.role, cur))
    if new not in known:
        raise Refused(
            "%r is not a state in %s's transition table. Known states: %s"
            % (new, spec.role, ", ".join(sorted(known))))

    for frm, to, actor, pre in rows:
        if frm == cur and to == new:
            return

    legal = sorted({to for frm, to, _a, _p in rows if frm == cur})
    raise Refused(
        "%s -> %s is not a transition %s's table permits from its current "
        "state. Legal from %s: %s"
        % (cur, new, spec.role, cur,
           ", ".join(legal) if legal else "(nothing — %s is terminal)" % cur))
```

- [ ] **Step 4: Run the tests until green**

Run: `python3 core/hooks/tests/test_state_gate_lib.py`
Expected: PASS, 13 tests.

If `terminal_states` fails the self-loop case, note that `auditing -> auditing` must not count as departing: the implementation above computes `departs` from rows where `to != frm` for exactly that reason.

- [ ] **Step 5: Confirm no role vocabulary leaked**

Run: `python3 core/hooks/tests/test_state_gate_lib.py NoRoleVocabularyInCore -v`
Expected: PASS. This case is the one that keeps the migration honest; if it ever fails, the fix is to move the name back into a rulebook's table, never to relax the test.

- [ ] **Step 6: Commit**

```bash
git add core/hooks/lib/state_gate.py core/hooks/tests/test_state_gate_lib.py
git commit -m "feat: the transition machine, with the role's vocabulary as data

Seven rulebooks carried seven distinct copies of this judgment; the two
closest differed on 702 substantive lines and they disagreed on behaviour,
not only shape. This holds the decision and no state name of any role — a
test fails if one appears."
```

---

### Task 2: The shim contract — how a rulebook reaches core's library

**Files:**
- Create: `core/hooks/lib/rolespec.py`
- Create: `core/hooks/tests/test_rolespec.py`
- Modify: `spawn.py` (`spawn_cmd`, in muster)
- Test: `test_spawn.py` (in muster)

**Interfaces:**
- Consumes: `state_gate.RoleSpec` from Task 1.
- Produces:
  - `rolespec.load(path: str) -> state_gate.RoleSpec` — reads a rulebook's `role.json`. Raises `state_gate.RulesError` on anything malformed.
  - `rolespec.core_lib() -> str` — the directory holding core's libraries, resolved from `TOKENMAXXXER_CORE` or the installed plugin cache. Raises `RuntimeError` when it cannot be found, which a shim turns into exit 2.
  - muster sets `TOKENMAXXXER_CORE=<core plugin root>` in every spawned session's environment.

A rulebook's hook cannot use `${CLAUDE_PLUGIN_ROOT}` to find core — that variable expands to the *role's* plugin root. The role's shim therefore asks `rolespec.core_lib()`, which muster answers directly and which falls back to the installed cache for sessions muster did not spawn.

- [ ] **Step 1: Write the failing test for the muster half**

Append to `test_spawn.py`:

```python
class CorePathIsExported(unittest.TestCase):
    def test_spawned_sessions_learn_where_core_is(self):
        # A rulebook's hook cannot use CLAUDE_PLUGIN_ROOT to find core — that
        # expands to the ROLE's plugin root. muster knows the answer already
        # (core_dir resolves it to attach core via --plugin-dir), so it says so.
        _, env = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False,
                                 core="/x/tokenmaxxxer-core/core")
        self.assertEqual(env["TOKENMAXXXER_CORE"], "/x/tokenmaxxxer-core/core")

    def test_no_core_no_variable(self):
        _, env = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
        self.assertNotIn("TOKENMAXXXER_CORE", env)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 test_spawn.py CorePathIsExported -v`
Expected: FAIL — `KeyError: 'TOKENMAXXXER_CORE'`

- [ ] **Step 3: Export it from `spawn_cmd`**

In `spawn.py`, inside `spawn_cmd`, after the existing `if core:` block that appends `--plugin-dir`:

```python
    env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
    if core:
        # A rulebook's own hooks cannot find core: ${CLAUDE_PLUGIN_ROOT} in
        # their hooks.json expands to THEIR plugin root. muster already
        # resolved core to attach it, so it hands the path over rather than
        # making nine rulebooks each guess at a cache layout.
        env["TOKENMAXXXER_CORE"] = core
```

- [ ] **Step 4: Run the muster tests**

Run: `python3 test_spawn.py -v && python3 test_gates.py`
Expected: both green.

- [ ] **Step 5: Write the failing test for the core half**

`core/hooks/tests/test_rolespec.py`:

```python
#!/usr/bin/env python3
"""role.json is the only thing a rulebook has to write to use core's gate."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import rolespec     # noqa: E402
import state_gate   # noqa: E402

GOOD = {
    "role": "ops",
    "record_glob": "docs/reports/records/*/ops.md",
    "legacy_record": "ops-record.md",
    "rules": "transition-rules.md",
}


def write(d, obj):
    p = os.path.join(d, "role.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    open(os.path.join(d, "transition-rules.md"), "w").close()
    return p


class Load(unittest.TestCase):
    def test_reads_the_four_fields(self):
        with tempfile.TemporaryDirectory() as d:
            spec = rolespec.load(write(d, GOOD))
            self.assertEqual(spec.role, "ops")
            self.assertEqual(spec.legacy_record, "ops-record.md")
            self.assertTrue(spec.rules_path.endswith("transition-rules.md"))
            self.assertTrue(os.path.isabs(spec.rules_path))

    def test_missing_field_raises(self):
        for drop in ("role", "record_glob", "rules"):
            with tempfile.TemporaryDirectory() as d:
                bad = {k: v for k, v in GOOD.items() if k != drop}
                with self.assertRaises(state_gate.RulesError, msg=drop):
                    rolespec.load(write(d, bad))

    def test_legacy_record_is_optional(self):
        with tempfile.TemporaryDirectory() as d:
            spec = rolespec.load(write(d, {k: v for k, v in GOOD.items()
                                           if k != "legacy_record"}))
            self.assertEqual(spec.legacy_record, "")

    def test_unparseable_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "role.json")
            with open(p, "w") as fh:
                fh.write("not json")
            with self.assertRaises(state_gate.RulesError):
                rolespec.load(p)

    def test_missing_rules_file_raises(self):
        # Declaring a table that is not there is worse than declaring none:
        # the gate would read nothing and pass everything.
        with tempfile.TemporaryDirectory() as d:
            p = write(d, GOOD)
            os.remove(os.path.join(d, "transition-rules.md"))
            with self.assertRaises(state_gate.RulesError):
                rolespec.load(p)


class CoreLib(unittest.TestCase):
    def test_env_wins(self):
        here = os.path.dirname(os.path.abspath(__file__))
        core_root = os.path.abspath(os.path.join(here, ".."))
        os.environ["TOKENMAXXXER_CORE"] = core_root
        try:
            self.assertEqual(os.path.realpath(rolespec.core_lib()),
                             os.path.realpath(os.path.join(core_root, "lib")))
        finally:
            os.environ.pop("TOKENMAXXXER_CORE", None)

    def test_unfindable_raises(self):
        saved = os.environ.pop("TOKENMAXXXER_CORE", None)
        os.environ["TOKENMAXXXER_CORE"] = "/nonexistent/core"
        try:
            with self.assertRaises(RuntimeError):
                rolespec.core_lib(cache_root="/nonexistent/cache")
        finally:
            os.environ.pop("TOKENMAXXXER_CORE", None)
            if saved is not None:
                os.environ["TOKENMAXXXER_CORE"] = saved


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run it to verify it fails**

Run: `python3 core/hooks/tests/test_rolespec.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'rolespec'`

- [ ] **Step 7: Write `core/hooks/lib/rolespec.py`**

```python
"""What a rulebook declares in order to use core's gates.

Everything role-specific is here, in the rulebook's own file. core reads it
and holds none of it.
"""
import json
import os

import state_gate

__all__ = ["load", "core_lib"]

_REQUIRED = ("role", "record_glob", "rules")


def load(path):
    """Read a rulebook's role.json into a RoleSpec.

    Every failure raises RulesError, which a shim turns into exit 2. A gate
    that cannot read its own declaration must refuse: the alternative is a
    gate that reports it is enforcing while enforcing nothing.
    """
    try:
        with open(path, encoding="utf-8-sig") as fh:
            obj = json.load(fh)
    except (OSError, ValueError) as e:
        raise state_gate.RulesError("role.json at %s is unreadable (%s)" % (path, e))
    if not isinstance(obj, dict):
        raise state_gate.RulesError("role.json at %s is not an object" % path)

    missing = [k for k in _REQUIRED if not obj.get(k)]
    if missing:
        raise state_gate.RulesError(
            "role.json at %s is missing %s" % (path, ", ".join(missing)))

    here = os.path.dirname(os.path.abspath(path))
    rules_path = os.path.join(here, obj["rules"])
    if not os.path.isfile(rules_path):
        raise state_gate.RulesError(
            "role.json declares a transition table at %s, which does not "
            "exist. Refusing rather than reading an empty table." % rules_path)

    return state_gate.RoleSpec(role=obj["role"],
                               record_glob=obj["record_glob"],
                               legacy_record=obj.get("legacy_record") or "",
                               rules_path=rules_path)


def core_lib(cache_root=None):
    """The directory holding core's libraries.

    A rulebook's hooks cannot use ${CLAUDE_PLUGIN_ROOT} for this — it expands
    to the ROLE's plugin root. muster exports TOKENMAXXXER_CORE because it
    already resolved core to attach it. The cache fallback covers a session
    muster did not spawn.
    """
    env = os.environ.get("TOKENMAXXXER_CORE")
    if env:
        lib = os.path.join(env, "lib")
        if os.path.isdir(lib):
            return lib

    root = cache_root or os.path.expanduser(
        "~/.claude/plugins/cache/tokenmaxxxer-core/core")
    if os.path.isdir(root):
        for entry in sorted(os.listdir(root), reverse=True):
            lib = os.path.join(root, entry, "hooks", "lib")
            if os.path.isdir(lib):
                return lib

    raise RuntimeError(
        "cannot find tokenmaxxxer-core's libraries. Set TOKENMAXXXER_CORE to "
        "the core plugin root, or install core@tokenmaxxxer-core.")
```

- [ ] **Step 8: Run both core suites**

Run: `python3 core/hooks/tests/test_rolespec.py && python3 core/hooks/tests/test_state_gate_lib.py`
Expected: both green.

- [ ] **Step 9: Commit both halves**

```bash
# in tokenmaxxxer-core
git add core/hooks/lib/rolespec.py core/hooks/tests/test_rolespec.py
git commit -m "feat: role.json is the only thing a rulebook declares

A rulebook's hooks cannot find core with CLAUDE_PLUGIN_ROOT — that expands
to their own plugin root. muster exports TOKENMAXXXER_CORE because it has
already resolved core to attach it; the plugin cache is the fallback."

# in muster
git add spawn.py test_spawn.py
git commit -m "feat: spawned sessions learn where core is"
```

---

### Task 3: Migrate `ops` — the reference implementation

**Files:**
- Create: `ops-cycle/hooks/role.json`
- Rewrite: `ops-cycle/hooks/state-gate.sh`
- Unchanged: `ops-cycle/hooks/transition-rules.md`, `ops-cycle/hooks/run-gate-tests.sh`

**Interfaces:**
- Consumes: `rolespec.load`, `rolespec.core_lib`, `state_gate.parse_rules`, `state_gate.judge` from Tasks 1–2.
- Produces: the shim shape every other rulebook copies.

`ops` goes first because the 2026-07-27 proposal recorded its copy as the only one that refuses a Bash write it cannot parse, where review's allowed it. Its behaviour is the behaviour core must have.

- [ ] **Step 1: Record the baseline before touching anything**

```bash
cd ops-agent-rulebook
bash ops-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2 | tee /tmp/ops-baseline.txt
```

Write the number down. **The suite must end at the same count with the same result after the migration.** A suite that shrinks is a suite that stopped testing something.

- [ ] **Step 2: Write `ops-cycle/hooks/role.json`**

```json
{
  "role": "ops",
  "record_glob": "docs/reports/records/*/ops.md",
  "legacy_record": "ops-record.md",
  "rules": "transition-rules.md"
}
```

- [ ] **Step 3: Rewrite the gate as a shim**

`ops-cycle/hooks/state-gate.sh`:

```bash
#!/usr/bin/env bash
# fail-closed trap: FIRST executable statement, before any set/source. Any
# exit that is neither 0 (allow) nor 2 (deny) becomes 2, since a PreToolUse
# hook treats a non-2 exit as NON-BLOCKING (fail-OPEN).
__fc(){ rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then echo "fail-closed: gate aborted (rc=$rc)" >&2; exit 2; fi; }
trap __fc EXIT
# PreToolUse: contract section 2's transition machine for the ops role.
#
# The judgment lives in tokenmaxxxer-core (hooks/lib/state_gate.py). This file
# declares which role it is and where its table is; role.json and
# transition-rules.md beside it are the only role-specific data. Seven copies
# of the judgment drifted 702 substantive lines apart while sharing a
# filename, which is why it is no longer copied.
#
# Kill switch: OPS_CYCLE_DISABLE=1
set -uo pipefail

case "${OPS_CYCLE_DISABLE:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac

command -v python3 >/dev/null 2>&1 || exit 2

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
payload="$(cat 2>/dev/null || true)"

# bash 3.2: a quoted heredoc nested inside $( … ) is NOT literal — read the
# program at top level. parse-check.sh enforces this.
IFS='' read -r -d '' SHIM <<'PY' || true
import os, sys
sys.path.insert(0, os.environ["ROLE_HOOK_DIR"])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if False else "")
import json

try:
    import rolespec
except ImportError:
    sys.stderr.write("ops-cycle: refused — core's libraries are not on the "
                     "path; set TOKENMAXXXER_CORE.\n")
    sys.exit(2)
PY

# Resolve core's lib directory first, then run the real shim with it on
# PYTHONPATH — importing rolespec is itself what needs the path.
CORE_LIB="$(python3 - <<'PY' 2>/dev/null || true
import os, sys
env = os.environ.get("TOKENMAXXXER_CORE")
cands = []
if env:
    cands.append(os.path.join(env, "lib"))
root = os.path.expanduser("~/.claude/plugins/cache/tokenmaxxxer-core/core")
if os.path.isdir(root):
    for e in sorted(os.listdir(root), reverse=True):
        cands.append(os.path.join(root, e, "hooks", "lib"))
for c in cands:
    if os.path.isdir(c):
        sys.stdout.write(c)
        break
PY
)"
if [ -z "$CORE_LIB" ]; then
  echo "ops-cycle: refused — tokenmaxxxer-core's libraries were not found. Set TOKENMAXXXER_CORE or install core@tokenmaxxxer-core." >&2
  exit 2
fi

IFS='' read -r -d '' OPS_GATE <<'PY' || true
import json, os, sys

sys.path.insert(0, os.environ["CORE_LIB"])
import rolespec, state_gate

def deny(msg):
    sys.stderr.write("ops-cycle: refused — %s\n" % msg)
    sys.exit(2)

try:
    spec = rolespec.load(os.path.join(os.environ["ROLE_HOOK_DIR"], "role.json"))
    with open(spec.rules_path, encoding="utf-8") as fh:
        rows = state_gate.parse_rules(fh.read())
except state_gate.RulesError as e:
    deny(str(e))

try:
    event = json.loads(os.environ.get("GATE_PAYLOAD", ""))
except ValueError:
    deny("the tool-call payload is not valid JSON; the gate cannot judge a "
         "write it cannot parse.")

sys.exit(0)
PY

CORE_LIB="$CORE_LIB" ROLE_HOOK_DIR="$HERE" GATE_PAYLOAD="$payload" \
  python3 -c "$OPS_GATE"
rc=$?
trap - EXIT
exit "$rc"
```

**Note for the implementer.** The shim above establishes the wiring — core resolution, `role.json`, table parsing, fail-closed refusals — and deliberately stops before the write-target extraction. The existing `ops-cycle/hooks/state-gate.sh` already contains that logic (its Bash write-target scan is the reference behaviour this whole migration is built around). **Port it verbatim into the `OPS_GATE` program between the payload parse and the final `sys.exit(0)`, replacing only the transition decision with `state_gate.judge(spec, rows, current, proposed)`.** Do not rewrite it, do not improve it, and do not drop a branch: the suite in Step 5 is what proves you did not.

- [ ] **Step 4: Confirm it still parses under bash 3.2**

```bash
bash ops-cycle/hooks/tests/parse-check.sh
```

Expected: every file `ok`.

- [ ] **Step 5: Run the existing suite, unchanged**

```bash
bash ops-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2
diff <(tail -2 /tmp/ops-baseline.txt) <(bash ops-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2)
```

Expected: identical to the baseline, with no case removed. If a case now fails, core's library is wrong — **fix `state_gate.py`, not the test.** The suite is the specification here.

- [ ] **Step 6: Confirm the shim shrank**

```bash
wc -l ops-cycle/hooks/state-gate.sh
```

Expected: well under 200 lines, from 604.

- [ ] **Step 7: Run the conformance checks**

```bash
bash ops-cycle/hooks/deny-only-check.sh
bash ops-cycle/hooks/tests/parse-check.sh
```

Expected: both exit 0.

- [ ] **Step 8: Commit**

```bash
git add ops-cycle/hooks/role.json ops-cycle/hooks/state-gate.sh
git commit -m "refactor: take the transition machine from core

ops declares which role it is and where its table is; the judgment comes
from tokenmaxxxer-core. transition-rules.md is untouched and remains the
only place this role's state vocabulary is written down. The existing gate
suite passes unchanged — same count, same result."
```

---

### Task 4: Migrate `review` — the cross-check that proves the library

**Files:**
- Create: `review-cycle/hooks/role.json`
- Rewrite: `review-cycle/hooks/state-gate.sh`
- Unchanged: `review-cycle/hooks/transition-rules.md`, `review-cycle/hooks/run-gate-tests.sh`

**Interfaces:**
- Consumes: the same library and the same shim shape as Task 3.
- Produces: the evidence that one library satisfies two differently-shaped roles.

This is the task that decides whether the migration is real. `review` has five states to ops's fewer, derives terminal states from its table, and carries the largest suite. The proposal's acceptance criterion is exactly this: *"If ops's suite and review's suite both pass, core satisfies both."*

- [ ] **Step 1: Record the baseline**

```bash
cd review-agent-rulebook
bash review-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2 | tee /tmp/review-baseline.txt
```

- [ ] **Step 2: Write `review-cycle/hooks/role.json`**

```json
{
  "role": "review",
  "record_glob": "docs/reports/records/*/review.md",
  "legacy_record": "review-record.md",
  "rules": "transition-rules.md"
}
```

- [ ] **Step 3: Copy the shim from ops and change three things**

Copy `ops-cycle/hooks/state-gate.sh` to `review-cycle/hooks/state-gate.sh`, then change exactly:

1. every `ops-cycle:` message prefix to `review-cycle:`
2. the kill switch `OPS_CYCLE_DISABLE` to `REVIEW_CYCLE_DISABLE`
3. the header comment's role name

**Nothing else may differ.** Run this to prove it:

```bash
diff <(sed -e 's/review/ops/g' -e 's/REVIEW/OPS/g' review-cycle/hooks/state-gate.sh) \
     <(cat ../ops-agent-rulebook/ops-cycle/hooks/state-gate.sh)
```

Expected: empty. If it is not empty, one of the two shims has grown role-specific logic, and that logic belongs in `role.json` or in core.

- [ ] **Step 4: Run review's existing suite**

```bash
bash review-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2
diff <(tail -2 /tmp/review-baseline.txt) <(bash review-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2)
```

Expected: identical to the baseline.

This is the moment the migration is either proven or refuted. If review's suite fails where ops's passed, the two roles disagree about behaviour that core now shares — **stop and write down what disagreed** before changing either side. That disagreement is the actual finding, and it is exactly what seven divergent copies were hiding.

- [ ] **Step 5: Run both roles' suites and both conformance checks together**

```bash
cd ../ops-agent-rulebook   && bash ops-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2
cd ../review-agent-rulebook && bash review-cycle/hooks/run-gate-tests.sh 2>&1 | tail -2
bash review-cycle/hooks/deny-only-check.sh && bash review-cycle/hooks/tests/parse-check.sh
```

Expected: both suites at their baseline counts, both checks exit 0.

- [ ] **Step 6: Commit**

```bash
git add review-cycle/hooks/role.json review-cycle/hooks/state-gate.sh
git commit -m "refactor: take the transition machine from core

Second role on core's state_gate, and the one that proves it: review's five
states, its derived terminal set, and its full suite all pass against the
library ops's suite fixed. The two shims are now identical modulo the role
name — checked by diff, not by eye."
```

---

### Task 5: Prove there is one machine, and keep it that way

**Files:**
- Create: `core/hooks/tests/shim-drift-check.sh`
- Modify: `core/hooks/tests/run-all.sh`

**Interfaces:**
- Consumes: the migrated shims from Tasks 3–4.
- Produces: a check that fails the day a rulebook's shim grows logic of its own — the failure mode that produced seven copies in the first place.

- [ ] **Step 1: Write the check**

`core/hooks/tests/shim-drift-check.sh`:

```bash
#!/usr/bin/env bash
# Every migrated state-gate shim must be identical modulo its role name.
#
# This is the check that was missing. Seven copies of one judgment drifted 702
# substantive lines apart while sharing a filename, and nothing said so — the
# divergence was only visible to someone who diffed two repositories by hand.
# A shim that grows logic of its own is the first step back to that, so it
# fails here instead.
#
# Usage: shim-drift-check.sh <role>:<path-to-state-gate.sh> [<role>:<path> ...]
set -uo pipefail

[ "$#" -ge 2 ] || { echo "shim-drift-check: give at least two <role>:<path> pairs" >&2; exit 2; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
ref=""
ref_role=""
rc=0

for pair in "$@"; do
  role="${pair%%:*}"
  path="${pair#*:}"
  [ -f "$path" ] || { echo "shim-drift-check: no such file: $path" >&2; exit 2; }
  up="$(printf '%s' "$role" | tr '[:lower:]-' '[:upper:]_')"
  sed -e "s/$role/ROLE/g" -e "s/$up/ROLEUP/g" "$path" > "$tmp/$role.norm"
  if [ -z "$ref" ]; then
    ref="$tmp/$role.norm"; ref_role="$role"; continue
  fi
  if diff -q "$ref" "$tmp/$role.norm" >/dev/null; then
    printf 'ok    %s matches %s\n' "$role" "$ref_role"
  else
    printf 'FAIL  %s differs from %s beyond its role name:\n' "$role" "$ref_role"
    diff "$ref" "$tmp/$role.norm" | head -20
    rc=1
  fi
done
exit "$rc"
```

- [ ] **Step 2: Run it against the two migrated shims**

```bash
chmod +x core/hooks/tests/shim-drift-check.sh
bash core/hooks/tests/shim-drift-check.sh \
  ops:../ops-agent-rulebook/ops-cycle/hooks/state-gate.sh \
  review:../review-agent-rulebook/review-cycle/hooks/state-gate.sh
```

Expected: `ok    review matches ops`

- [ ] **Step 3: Prove the check can fail**

```bash
cp ../review-agent-rulebook/review-cycle/hooks/state-gate.sh /tmp/shim-backup.sh
printf '\n# a local special case\nexit 0\n' >> ../review-agent-rulebook/review-cycle/hooks/state-gate.sh
bash core/hooks/tests/shim-drift-check.sh \
  ops:../ops-agent-rulebook/ops-cycle/hooks/state-gate.sh \
  review:../review-agent-rulebook/review-cycle/hooks/state-gate.sh; echo "exit=$?"
cp /tmp/shim-backup.sh ../review-agent-rulebook/review-cycle/hooks/state-gate.sh
```

Expected: `FAIL  review differs from ops beyond its role name`, `exit=1`. A check that cannot fail proves nothing — this is the same lesson the judge-log test taught on 2026-07-27.

- [ ] **Step 4: Wire it into `run-all.sh`**

In `core/hooks/tests/run-all.sh`, before the final tally:

```bash
echo; echo "=== state_gate lib ==="
python3 "$here/test_state_gate_lib.py" 2>&1 | tail -3 || rc=1

echo; echo "=== rolespec ==="
python3 "$here/test_rolespec.py" 2>&1 | tail -3 || rc=1
```

The shim drift check takes paths outside this repository, so it is not run by `run-all.sh`; it belongs in the migration PR's checklist and in whatever runs across the org.

- [ ] **Step 5: Run everything**

```bash
bash core/hooks/tests/run-all.sh
```

Expected: `ALL OK`.

- [ ] **Step 6: Commit**

```bash
git add core/hooks/tests/shim-drift-check.sh core/hooks/tests/run-all.sh
git commit -m "test: fail the day a shim grows logic of its own

Seven copies of one judgment drifted 702 substantive lines apart while
sharing a filename, and nothing said so. Two shims that are identical
modulo their role name is a property worth asserting, not hoping for."
```

---

## What this plan deliberately does not do

- **It does not merge review and verify.** Contract §16 is titled "verify/review division of labor" and states the mechanism "does not merge the two roles' verdicts"; §4 makes the independence a rule. Their skills were compared on 2026-07-27 and are different procedures, not drifted copies — a five-value `verdict:` per requirement against a two-value `outcome:` per attempt, with verify's own skill refusing to treat a clean review-record as grounds to skip an attempt. Skills stay put.
- **It does not migrate the other five roles.** product, feasibility, reflect, ux-design and verify follow once two roles have proven the library, one PR each, each repeating Task 4's shape: baseline, `role.json`, copy the shim, run the existing suite, diff against the reference shim.
- **It does not touch the other five gate families.** `path-ownership`, `record-fields`, `doc-bucket`, `trailer` and `handbook-trigger` each get their own plan, and each will surface its own disagreements — `record-fields` already has two (review deliberately skips the §14-forbidden "why" heuristic that verify implements; the two use different terminal-state sources).
- **It does not fix the divergences it finds.** When ops's and review's suites disagree about behaviour core now shares, that disagreement gets written down and decided, not silently resolved by whoever is holding the keyboard. Seven copies is what silent resolution produces.

## Self-review

**Spec coverage.** The design's roadmap item 10 names six gate families and nine roles; this plan is the first slice — one family, two roles, plus the conformance check that keeps them from re-diverging. Decision ① (roles stay separate) is honored in the architecture and stated explicitly above. The remaining families and roles are named as follow-on plans rather than left implicit.

**Placeholders.** One deliberate hand-off, marked as such: Task 3 Step 3 tells the implementer to port ops's existing write-target extraction verbatim rather than reproducing 600 lines of it here. Every other step carries its content or its exact command and expected output.

**Type consistency.** `RoleSpec(role, record_glob, legacy_record, rules_path)` is defined in Task 1 and constructed in Task 2's `rolespec.load`; `parse_rules`, `terminal_states`, `judge`, `RulesError`, `Refused` are defined in Task 1 and consumed in Tasks 2–3 under the same names. `role.json`'s four keys — `role`, `record_glob`, `legacy_record`, `rules` — are written in Tasks 3 and 4 and read by `_REQUIRED` in Task 2. `TOKENMAXXXER_CORE` is exported in Task 2 and consumed in Task 3's shim.

**One risk stated plainly.** Task 4 Step 4 may fail. That is not a defect in the plan — it is the plan working. Two roles disagreeing about a judgment they both claimed to implement is the finding seven copies existed to hide, and the instruction there is to stop and write it down rather than to make it pass.
