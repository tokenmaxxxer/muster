---
proposal: docs/proposals/2026-08-07-cli-truth-vs-action.md
---

# Hunt record — cli-truth-vs-action

## after-proposal — stance 1: find a path the frozen write set (spawn.py, test_spawn.py) cannot carry, or a plain design error in the just-landed diff

Verdict: FINDING — the new origin-mismatch guard in `issue_workspace()` compares an origin normalized under the *current* process's `MUSTER_KEEP_SSH` setting against a work-dir origin that was normalized (and baked into the clone) under whatever `MUSTER_KEEP_SSH` setting was in effect when that work dir was first created; if the env var differs between the two spawns, the guard fires a false "origin 불일치" exit even though both refer to the same repo.
Kind: design-error
Seed: git diff HEAD -- spawn.py (fix 5, `issue_workspace()` reuse-branch origin check, ~lines 2727-2743 and 2745-2760)
cap_seconds: 120
tier: default
diff_stat_lines: (six fixes landed in spawn.py + pinning tests in test_spawn.py; full diff not separately measured here)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:02:00Z

### Reproduce
`issue_workspace(cwd, issue, role)` computes `origin` from `cwd`'s remote and, unless `MUSTER_KEEP_SSH` is truthy, rewrites `git@github.com:org/repo.git` / `ssh://git@github.com/org/repo.git` to `https://github.com/org/repo.git` (spawn.py ~line 2734):

```python
m = re.match(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$", origin)
if m:
    origin = "https://github.com/%s.git" % m.group(1)
```

This *rewritten* `origin` is what the work clone's `origin` remote is actually set to when the workspace is first created. Later, on reuse, the guard re-derives `origin` fresh from `cwd` under the *current* env and compares it against `work_origin` read from the existing clone (spawn.py ~line 2745-2751):

```python
def _norm(u):
    return re.sub(r"\.git$", "", u.rstrip("/"))
if _norm(work_origin) != _norm(origin):
    sys.exit(f"작업 경로에 다른 레포가 있다 (origin 불일치): ...")
```

Minimal reproduction of the comparison logic in isolation (both sides literally taken from spawn.py):

```python
python3 - <<'PYEOF'
import re
def normalize_origin(origin, keep_ssh):
    if keep_ssh:
        return origin
    m = re.match(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$", origin)
    return "https://github.com/%s.git" % m.group(1) if m else origin
def norm(u):
    return re.sub(r"\.git$", "", u.rstrip("/"))

raw_origin = "git@github.com:someorg/somerepo.git"
# spawn 1 (MUSTER_KEEP_SSH unset): work clone's origin remote gets set to this
work_origin = normalize_origin(raw_origin, keep_ssh=False)
# spawn 2, same cwd/repo, but MUSTER_KEEP_SSH=1 now set (e.g. operator flips it
# per the docstring's own suggested use case: "회사 정책이 ssh 원격만 허용하면
# MUSTER_KEEP_SSH=1 로 끈다")
origin_run2 = normalize_origin(raw_origin, keep_ssh=True)
print("work_origin:", work_origin)
print("origin_run2:", origin_run2)
print("mismatch:", norm(work_origin) != norm(origin_run2))
PYEOF
```

### Observed
```
work_origin: https://github.com/someorg/somerepo.git
origin_run2: git@github.com:someorg/somerepo.git
mismatch: True
```
The guard would `sys.exit()` on the second spawn, refusing to reuse (and fetch into) a workspace that is in fact the correct, previously-created workspace for the same repo/issue/role — solely because `MUSTER_KEEP_SSH` differs between the two invocations. This is exactly the scenario the surrounding comment names as legitimate ("회사 정책이 ssh 원격만 허용하면 MUSTER_KEEP_SSH=1 로 끈다"): the env var is documented as something an operator toggles, but the reuse guard treats any such toggle as "다른 레포" (a different repo) rather than the same repo under a different transport normalization.

### Expected
The origin-identity check should compare a form that is invariant to `MUSTER_KEEP_SSH`/transport (e.g. normalize both sides to the same canonical `org/repo` form regardless of ssh vs https, independent of which setting was active when the clone was created), so that toggling the env var between spawns of the same issue/role does not falsely trip the "다른 레포" guard.
