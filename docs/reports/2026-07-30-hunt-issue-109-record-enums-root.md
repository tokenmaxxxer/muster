---
proposal: docs/proposals/2026-07-30-issue-109-record-enums-root.md
---

# Hunt record — issue-109-record-enums-root

## after-proposal — stance 1: ON_THE_RECORD_ROOT resolution for record_enums

Verdict: NO FINDING
Seed: gates/gates.py (ON_THE_RECORD_ROOT = Path(__file__).resolve().parent.parent, used in
record_enums for roles/<role>.json instead of `root`), test_gates.py (_record_repo fixture,
ON_THE_RECORD_ROOT monkeypatching).

Traced the deployment model: spawn.py already resolves `roles/<role>.json` via
`ROOT = Path(__file__).resolve().parent` (its own checkout, spawn.py:32,328,470,533,1600,1792) —
never from the work repo being spawned into. gates.py's ON_THE_RECORD_ROOT mirrors that exact
pattern one directory up (gates/gates.py -> parent.parent = same checkout root), so the two
role-resolution call sites (spawn.py and gates.py) are now consistent instead of split (one
reading its own checkout, the other reading the work repo).

Checked the plugin/marketplace deployment split (.claude-plugin/marketplace.json publishes only
`./on-the-record` — commands/hooks, not gates.py/spawn.py/roles/) and on-the-record/hooks/
directive.sh's _checkout_resolve(), which independently locates the real spawn.py-owning checkout
(dev override, ancestor probe, marketplace clone, self-clone fallback) before ever invoking
spawn.py — so gates.py, when reached via `sys.path.insert(0, ROOT/"gates"); import gates` from
spawn.py, always lives inside that same resolved checkout. Path(__file__).resolve() also
correctly follows symlinks, so an invocation via a symlinked entry point still resolves
ON_THE_RECORD_ROOT to the real checkout's roles/ dir.

Confirmed fail-closed behaviour is preserved: role_file missing/unreadable still appends to `bad`
(gates.py:279-283) rather than passing silently, and `python3 test_gates.py` runs all
`t_record_enums_*` cases green (unrelated failure later in the run is a sandboxed-filesystem
write in an unrelated spawn.py test, not this change).

Considered but could not reproduce as a defect: a work repo shipping its own
`roles/<role>.json` to locally override enum values would now be silently ignored (validated
against the global on-the-record definition instead). No such override mechanism exists anywhere
in the codebase — spawn.py never reads roles/ from a work repo either — so there is nothing this
regresses; it is the intended single-source-of-truth design, not a composition regression.
