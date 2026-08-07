---
proposal: docs/issue-379/proposals/2026-08-07-choice-framing-guard.md
---

# Hunt record — choice-framing-guard

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the proposal's write set puts new files under gates/ (gates/open_work.py, gates/test_open_work.py), but gates/gates.py — the merge-time machine gate, itself unlisted and itself living under the protected root — hard-blocks any diff touching the gates/ directory via PROTECTED_ROOT_DIRS, independent of what spec.md declares as the allowed write-set. The proposal never lists a path (gates/gates.py edit, escalation record, or PROTECTED_ROOT_DIRS carve-out) to get past this block, so as written the build cannot land through the normal gate path.
Kind: design-error
Seed: docs/issue-379/proposals/2026-08-07-choice-framing-guard.md write set: gates/open_work.py (new), gates/test_open_work.py (new), on-the-record/hooks/choice-framing-guard.sh (new), on-the-record/hooks/hooks.json (edit), docs/decisions/2026-08-07-choice-framing-scope.md (new)
cap_seconds: 120
tier: size:21-200
diff_stat_lines: 21-200 (proposal is docs-only at hunt time)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:05:00Z

### Reproduce
```
python3 -c "
import sys; sys.path.insert(0,'.')
from gates.gates import is_protected
print(is_protected('gates/open_work.py'))
print(is_protected('gates/test_open_work.py'))
"
```

### Observed
```
True
True
```
`gates/gates.py`'s `writeset()` does:
```python
bad = [f"보호 경로 변경: {f}" for f in files if is_protected(f)]
...
if not allowed: return bad + ["spec 에 write-set 선언이 없다 (fail closed)"]
bad += [f"write-set 이탈: {f} ..." for f in files if not any(fnmatch.fnmatch(f, a) for a in allowed)]
return bad
```
`PROTECTED_ROOT_DIRS = {"roles", "gates", "agents", "images", "profiles"}` (gates/gates.py:30) and `is_protected()` (gates/gates.py:59-66) checks `parts[0] in PROTECTED_ROOT_DIRS` — this check runs regardless of whether the path is also declared in spec.md's write-set, so declaring `gates/open_work.py` as an allowed write in the proposal's spec does not suffice: `writeset()` still returns a non-empty `bad` list ("보호 경로 변경: gates/open_work.py") purely because the top-level directory is "gates". This is a self-referential trap: gates/ is protected precisely because "파이프라인이 자기 규칙을 다시 쓸 수 없어야 한다" (the pipeline must not be able to rewrite its own rules), and open_work.py is new pipeline logic being added under that same protected root.

### Expected
The proposal's write set should either avoid placing new files under gates/ (e.g. put open_work.py elsewhere), or should list an explicit path/step for clearing the PROTECTED_ROOT_DIRS block (e.g. a documented escalation/human sign-off artifact, or an edit to gates/gates.py's PROTECTED_ROOT_DIRS/is_protected exception list) — none of which currently appears in the frozen write set.
