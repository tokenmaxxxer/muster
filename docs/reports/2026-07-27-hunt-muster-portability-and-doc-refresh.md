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

## before-landing — stance 0: bypassable-gate

Verdict: FINDING — t_role_files_carry_no_absolute_home_path only rejects the literal marker "workspace/10_WORK" inside $HOME/~ prefixed env defaults, so any other personal-directory-convention value planted in a role file's env passes the guard silently.
Kind: silent-failure
Seed: test_gates.py t_role_files_carry_no_absolute_home_path strengthened to reject $HOME-/~-prefixed personal-convention defaults (diff vs main ccc322e), roles/qa.json env/allowWrite block removed.

### Reproduce
```
cd /home/jwjung/tokenmaxxxer/muster
cp roles/qa.json /tmp/qa.json.bak
python3 -c "
import json
d = json.load(open('roles/qa.json'))
d['env'] = {'QA_WORKSPACE': '\$HOME/Documents/jiwon-personal-qa-scratch'}
json.dump(d, open('roles/qa.json','w'), indent=2)
"
python3 -m pytest test_gates.py -k role_files -q -o python_functions="t_*"
cp /tmp/qa.json.bak roles/qa.json   # restore
```

### Observed
```
1 passed, 28 deselected in 0.02s
```
The guard passes even though `$HOME/Documents/jiwon-personal-qa-scratch` is exactly the kind of personal-directory-convention default the strengthened test's own docstring says it now catches ("`workspace/10_WORK` 같은 개인 디렉터리 관례를 그 뒤에 박아 넣으면 ... 이 가드를 통과해 왔다").

### Expected
The test should reject any `$HOME`/`~`-prefixed env default that embeds a personal path segment (e.g. a username, a personal scratch directory), not just the one literal string `workspace/10_WORK` that happened to be in the removed qa.json. As written, the "fix" only covers the exact string it was built to catch and gives false confidence that the general class of personal-path leaks is now guarded against.
