---
proposal: docs/proposals/2026-07-27-muster-portability-and-doc-refresh.md
---

# Hunt record — muster-portability-and-doc-refresh

## after-proposal — stance 0: bypassable-gate

Verdict: FINDING — `t_role_files_carry_no_absolute_home_path` (test_gates.py:255) is the repo's declared "no personal path in role files" guard, but it only rejects literal `/Users/` or `/home/` substrings and requires `path` fields to start with `$`; it does not inspect what a `$HOME`-prefixed default actually expands to, so `roles/qa.json`'s `QA_WORKSPACE` default `$HOME/workspace/10_WORK/tokenmaxxxer/qa-workspace` — the exact personal directory-naming convention the proposal is written to remove — passes the gate clean today, and would continue to pass with any other person's convention substituted in its place.
Kind: silent-failure
Seed: docs/proposals/2026-07-27-muster-portability-and-doc-refresh.md (roles/qa.json QA_WORKSPACE default), test_gates.py:255 t_role_files_carry_no_absolute_home_path

### Reproduce
cd /home/jwjung/tokenmaxxxer/muster
python3 -c "
import json
raw = open('roles/qa.json').read()
spec = json.loads(raw)
assert '/Users/' not in raw and '/home/' not in raw
assert spec['env']['QA_WORKSPACE'].startswith('\$')
print('GATE PASSES despite personal path:', spec['env']['QA_WORKSPACE'])
"

### Observed
GATE PASSES despite personal path: $HOME/workspace/10_WORK/tokenmaxxxer/qa-workspace

### Expected
A gate meant to keep "one person's directory-naming convention" out of tracked role files (per the proposal's own grounding section) should fail on this value, since `$HOME` expands to a per-person home directory that then has this specific person's `workspace/10_WORK/tokenmaxxxer/qa-workspace` layout hardcoded after it — the same class of defect the gate exists to catch, just placed after the `$VAR` instead of before it.
