---
subject: issue-235
role: implementation
phase: 1
---

# Current-state survey — issue-235

## Scout skip record

Skipped — pure bugfix. Issue #235 is a precision correction to the layer
classifier `spawn.py` already carries (landed by issue #232/PR #233,
`70f867f`), directly prescribed by a prior independent observation record
(`docs/issue-232/reports/execution-observation.md`, Finding 1 and Finding
2). The issue body's own `## 요구사항` names the exact fix behavior for
each of the two findings — corroborate `is_error` matches against the
harness's own `permission_denials`, anchor `_GATE_HOOK_RE` to the start of
the text, prefer the hook path stem over `gate_deny`'s first token for
`detail.gate` — and enumerates the four regression cases verbatim. There is
no external product category to benchmark this against and no open
design choice: the shape of the fix is fixed by two already-published
findings from a report this repo already treats as authoritative evidence
(the issue's own `## 참고` cites it as such), and the issue's constraint 5
explicitly forbids the two things that would otherwise be design
decisions — new instrumentation and pattern-set expansion. This mirrors
the identical skip call issue-232's own phase-1 survey made for the
identical reason (`docs/issue-232/reports/implementation/survey.md`
§Scout skip record) and the issue-129 precedent it in turn cites.

## Warrant-hunter

The role-handoff contract calls for dispatching a "warrant-hunter" agent
at the end of phase 1. This harness's available agent types are `claude`,
`Explore`, `freelunch:freelunch-worker`, `general-purpose`, `Plan`,
`statusline-setup` — no `warrant-hunter` type exists. Skipped for that
reason; no hunt result is fabricated or implied below.

## Where the classifier lives

Single file: `spawn.py`. The three pieces of logic issue #235 targets are
all inside or immediately around `_classify_refusal_text`
(`spawn.py:1520-1541`), called from the per-stdout-line loop in
`_spawn_one` (`spawn.py:2676-2690`).

```python
# spawn.py:1491-1492
_GATE_HOOK_RE = re.compile(r"PreToolUse:\S+ hook error: \[([^\]]*)\]")
_GATE_DENY_RE = re.compile(r"(\S+):\s*refused\s*—")
```

```python
# spawn.py:1520-1541
def _classify_refusal_text(text: str):
    hook_m = _GATE_HOOK_RE.search(text)
    if hook_m:
        deny_m = _GATE_DENY_RE.search(text)
        if deny_m:
            gate = deny_m.group(1)
            reason = text[deny_m.end():].strip()[:300]
        else:
            gate = Path(hook_m.group(1)).stem
            reason = text.strip()[:300]
        return ("gate-refusal", ("gate", gate), {"gate": gate, "reason": reason})
    for pat in _HARNESS_REFUSAL_PATTERNS:
        if pat.search(text):
            return ("harness-refusal", ("harness",), text.strip()[:300])
    for pat in _SANDBOX_REFUSAL_PATTERNS:
        if pat.search(text):
            return ("sandbox-refusal", ("sandbox",), text.strip()[:300])
    return None
```

```python
# spawn.py:2664-2690 (the two relevant branches of _spawn_one's per-line loop)
if obj.get("type") == "result":
    result = obj
    denials = result.get("permission_denials") or []
    if issue is not None and denials and not refusals_seen:
        refusals_seen.add(("unclassified",))
        _append_event(events_path, "unclassified-refusal",
                     str(denials)[:200])
elif issue is not None and obj.get("type") == "user":
    for block in (obj.get("message") or {}).get("content") or []:
        if not isinstance(block, dict) or block.get("type") != "tool_result":
            continue
        if not block.get("is_error"):
            continue
        text = _tool_result_text(block.get("content"))
        classified = _classify_refusal_text(text)
        if classified is None:
            continue
        ev_type, key, detail = classified
        if key in refusals_seen:
            continue
        refusals_seen.add(key)
        _append_event(events_path, ev_type, detail)
```

## Point 1 — `_classify_refusal_text` fires on `is_error` alone, uncorroborated with `permission_denials`

`obj.get("type") == "user"` (`spawn.py:2676`) is a wholly separate branch
from `obj.get("type") == "result"` (`spawn.py:2664`), and the two never
share state going *into* the classification decision — `denials` is read
only inside the `"result"` branch (`spawn.py:2666`) and is not passed to,
or consulted by, `_classify_refusal_text` or its caller. The only gate on
the `"user"` branch is `block.get("is_error")` (`spawn.py:2680`): "was this
one tool call's result an error," not "did the harness record a
permission denial for this session." Those are different predicates —
`is_error: true` covers every failed tool call (a bad path, a syntax
error, a network timeout), while `permission_denials` is the harness's own
authoritative record of what was actually denied.

This is exactly execution-observation's Finding 1
(`docs/issue-232/reports/execution-observation.md:339-378`), which traces
the same code (pre-#235) and states the root cause identically: "`is_error:
true` is a weaker predicate than the constraint assumed: it marks any
failed tool call, whose content is arbitrary stdout/stderr, not only a
refusal... Nothing ties a classification to the `permission_denials` list
the harness itself reports." The finding's concrete evidence: (a) a
session with zero `permission_denials` whose failed tool call happens to
print gate-marker-shaped text produces a `gate-refusal` event that the
pre-issue-232 code could never have produced (`execution-observation.md:
264-272`); (b) a real layer-2 harness denial that quotes a command
verbatim — the harness's own "The following part requires approval: …"
shape — will classify as `gate-refusal` if the quoted command happens to
contain the literal marker `PreToolUse:<tool> hook error: [<path>]`, and
that marker string is not rare: it lives verbatim in this repo's own
`test_spawn.py` fixture (`test_spawn.py:1269-1271`) and in
`docs/issue-232/decisions/event-layer-taxonomy.md:19-20`, files role
sessions routinely `grep` (`execution-observation.md:244-262`); (c) a
spurious match populates `refusals_seen` (`spawn.py:2687-2689`), which
suppresses the terminal-result fallback (`spawn.py:2667`,
`not refusals_seen`) for a genuine denial in the same session, compositing
the two failure modes (`execution-observation.md:303-311`).

## Point 2 — `_GATE_HOOK_RE` is not anchored to the start of the text

`_GATE_HOOK_RE.search(text)` (`spawn.py:1525`) is a plain `.search()` over
the entire tool_result text with no `^` anchor and no `re.match`/position
constraint (`spawn.py:1491`: `re.compile(r"PreToolUse:\S+ hook error:
\[([^\]]*)\]")`, no anchor characters). `.search()` finds the pattern
anywhere in the string, so a real hook-wrapped error that the harness
places at the start of the message and a quoted/embedded occurrence of the
same marker text deep inside an unrelated message (e.g. inside a harness
denial that echoes a command containing that literal string, per Point 1
above) are indistinguishable to this regex — both match. The issue's own
requirement 2 names anchoring to the start of the text as the "minimum
condition" to tell them apart
(`gh issue view 235`: "`_GATE_HOOK_RE` 를 tool_result 텍스트의 시작
위치에 앵커할 것(인용된 마커와 하네스가 감싼 실제 훅 오류를 구분하는
최소 조건)"), and execution-observation's Finding 1 action item proposes
the identical fix ("anchor `_GATE_HOOK_RE` to the start of the
`tool_result` text instead of searching anywhere within it",
`execution-observation.md:374-378`). This is a distinct fix from Point 1's
corroboration: even with corroboration, an unanchored regex still risks
misreading which layer produced a *correlated* denial's tool_result text if
a hook-error-shaped substring is quoted inside it; anchoring narrows what
counts as "the harness's own hook-wrapped error" to only text the harness
itself places at the message's start.

## Point 3 — `detail.gate` prefers `gate_deny`'s first token over the hook path stem

`spawn.py:1526-1533`: when `_GATE_HOOK_RE` matches, the code tries
`_GATE_DENY_RE.search(text)` (`spawn.py:1527`, pattern
`r"(\S+):\s*refused\s*—"`) *first*, and only falls back to
`Path(hook_m.group(1)).stem` (`spawn.py:1532`) when that second regex does
not match — i.e. the deny-token source is preferred, the hook-path stem is
the fallback. `gate_deny`'s documented signature is `gate_deny
<role-or-gate-name> <message>` (external file, this project's
`tokenmaxxxer-core` plugin dependency,
`core/hooks/lib/gate-lib.sh:75`, read directly this session at
`/Users/jk/.tokenmaxxxer/work/tokenmaxxxer-core-issue-94-execution-observation/core/hooks/lib/gate-lib.sh:75,77-79`:
`gate_deny() { echo "${1:-gate}: refused — $2" >&2; exit 2; }`) — the
first argument is explicitly documented as *either* a role name or a gate
name, never guaranteed to be the gate.

Execution-observation's Finding 2 supplies a real counterexample observed
in that session's own tool stream
(`execution-observation.md:380-417`): a `record-fields-gate.sh` denial
whose text is `PreToolUse:Write hook error:
[.../record-fields-gate.sh]: execution-observation: refused — record is
missing required section(s): …`. Against that text, `_GATE_HOOK_RE` yields
the correct stem `record-fields-gate`, while `_GATE_DENY_RE` yields
`execution-observation` — a *role* name, not the gate — and the current
code (`spawn.py:1528-1529`) prefers the wrong one. The same finding notes
a second real sample, a `board-gate.sh` denial, where the deny-token
*does* happen to equal the gate name — so the preferred source is right
for some gates and silently wrong for others, while the discarded
fallback source (the hook path stem) is right in both observed cases. The
issue's requirement 3 states the fix directly: `detail.gate` should prefer
the hook path stem, and the `gate_deny` token should be used only as
reason text (`gh issue view 235`: "`detail.gate` 는 훅 경로 stem 을
우선하고, `gate_deny` 토큰은 사유 텍스트로만 쓸 것").

## Existing test/regression coverage

`test_spawn.py`'s `EventReporting` class (`test_spawn.py:1183-1231` for
the harness, cases from `test_spawn.py:1233` onward) covers the
issue-232-era shape of this classifier but not the three paths above:

- `test_gate_hook_denial_is_gate_refusal_with_gate_name`
  (`test_spawn.py:1264-1281`) uses a single-layer, single-source fixture —
  hook marker plus `board-gate: refused —` in one `tool_result`, paired
  with a non-empty `permission_denials` on the terminal `result` line —
  where `_GATE_DENY_RE`'s token and the hook stem happen to agree
  (`board-gate` both ways). It does not exercise a case where they
  disagree (Point 3), nor a zero-`permission_denials` session (Point 1),
  nor a quoted-marker-inside-another-layer's-message case (Points 1+2).
- `test_denials_with_no_correlating_tool_result_are_unclassified`
  (`test_spawn.py:1253-1262`) covers the reverse direction — denials
  present, no correlating tool_result text — not the direction issue #235
  is about (tool_result text present, no corroborating denials).
- `test_harness_permission_denial_is_not_labeled_gate_refusal`
  (`test_spawn.py:1283-1305`) includes the harness's literal
  "requires approval"/quoted-command sample
  (`test_spawn.py:1290-1291`, `"This Bash command contains multiple
  operations. The following part requires approval: git show
  <sha>:<path>"`) but that quoted command does not itself contain the
  literal gate-hook marker string, so this fixture does not exercise the
  Finding-1 quoted-marker collision — every one of its five subTests still
  runs with a non-empty `permission_denials` on the paired `result` line
  (`test_spawn.py:1300-1301`), so it does not probe the corroboration gap
  either.
- `test_non_error_tool_result_matching_refusal_text_fires_nothing`
  (`test_spawn.py:1325-1340`) is the `is_error` structural guard from
  issue-129, re-verified for the layer classifier; it does not touch
  `permission_denials` correlation at all (no `result` line is fed in that
  case; `is_error: False` short-circuits before `_classify_refusal_text`
  is reached).

No existing case: (i) feeds a layer-2-shaped message that quotes the
literal gate-hook marker; (ii) feeds a `tool_result` with the marker
alongside a `result` line whose `permission_denials` is empty; (iii)
composes a spurious match with a real, distinct denial in the same
session; (iv) uses the real `record-fields-gate` denial text from
execution-observation's Finding 2 to assert `detail.gate` resolves to the
stem rather than the role-name token. All four are the issue's own
`## 요구사항 4` list and are the four regression cases the proposal names.

## Write set implied (frozen for phase 2, not touched this phase)

- `spawn.py` — `_GATE_HOOK_RE` (`spawn.py:1491`, add start anchor),
  `_classify_refusal_text` (`spawn.py:1520-1541`, prefer hook stem over
  deny token for `gate`), and the per-line loop's `"user"` branch
  (`spawn.py:2676-2690`, corroborate against the terminal `result` line's
  `permission_denials` before emitting a layer verdict).
- `test_spawn.py` — four new regression cases in `EventReporting`
  (`test_spawn.py:1183` onward), per issue requirement 4, each
  demonstrated to fail against pre-change `main` in phase 2.

No decision-record file is implied: unlike issue-232 (which introduced a
new wire-format shape — new event type strings and a new `detail` dict
shape, meriting `docs/issue-232/decisions/event-layer-taxonomy.md`), issue
#235 changes only the *correctness* of an existing classification (which
event fires, and what value `detail.gate` holds) without adding, removing,
or reshaping any event type or `detail` key — no wire-format decision is
newly made. No `.env`, dependency, or schema/migration surface is touched.
