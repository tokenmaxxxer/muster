loop_state: phase-2 complete

# QA phase-2 execution report — issue #38 (package-registry access)

Branch: `issue-38/qa`. Upstream basis: this record executes the plan at
`docs/issue-38/proposals/qa.md` (committed at
`746165121f2b75e489cd3279362e7e001e49b71f`, "docs(issue-38): phase-1 QA
survey and proposal for package-registry access") against the
implementation shipped in `spawn.py` on this same branch — the
`role_settings()`/`go_proxy_layer()`/`_spawn_one()` package-registry-access
code from PR #39 ("feat(issue-38): hybrid package-registry access for role
sandboxes", commit `8bda829`), already merged to `main` and present here.

## What was done

Ran the full `test_spawn.py` suite, then executed (not just read) every
probe in the QA plan: the AC1 `--dry-run` invocation for role `coding`
against a fresh git repo, an AC2 README-vs-code drift check, and five edge
cases (empty cache dir, file-instead-of-dir env var, allowedDomains
merge/dedup, real-sandbox cache read, and the non-`--issue` ad-hoc spawn
path) — each via a throwaway Python harness calling directly into
`spawn.py`'s functions where no CLI flag exposed the path. One edge case
(4b) reproduced a confirmed defect (filed below as `UNFILED`); one (4d)
was judged infeasible to execute live within this session and is marked
`BLOCKED` with the reasoning recorded in place. All commands and raw
output are pasted below (truncated only where noted).

## Next steps / open-finding resolution path

- The `UNFILED` bug in §4b (`os.path.exists` vs `os.path.isdir` at
  `spawn.py:364`) needs human triage/filing as a tracked issue before any
  fix lands — this QA session does not file issues or patch code.
- §4d remains unverified at the "does the external sandbox runtime
  actually honor the `allowRead` mount at execution time" layer; if that
  guarantee needs closing, it requires a deliberately-scoped follow-up
  session with an accepted budget for one real nested `claude -p` spawn
  (not attempted here — see reasoning in §4d).
- No other open items; AC1/AC2 and edge cases 4a/4c/4e are closed PASS.

## Time breakdown

| Step | What | ~time |
|---|---|---|
| 1 | Full `test_spawn.py` run | 3 min |
| 2 | AC1 dry-run probe (fresh git repo, `--dry-run`) | 5 min |
| 3 | AC2 README/spawn.py drift check | 6 min |
| 4a | Empty-but-existing cache dir probe | 4 min |
| 4b | Env var pointing at a file probe | 6 min |
| 4c | allowedDomains merge/dedup probe (fake ROOT) | 8 min |
| 4d | Composed sandbox command inspection / real-spawn feasibility | 7 min |
| 4e | Non-`--issue` (ad-hoc) spawn path probe | 8 min |
| 5 | Report writeup | 6 min |

Total: ~53 min (over the ~40 min timebox; edge cases 4c/4d/4e required
building small harnesses since none of them are exposed as a bare CLI flag).

---

## 1. Full test suite — PASS

Command:
```
python3 -m pytest test_spawn.py -v
```
Output (tail):
```
collected 40 items
...
test_spawn.py::PackageRegistryAccess::test_absent_cache_dir_is_skipped_without_error PASSED
test_spawn.py::PackageRegistryAccess::test_go_proxy_layer_none_when_cache_not_mounted PASSED
test_spawn.py::PackageRegistryAccess::test_go_proxy_layer_prefers_mounted_host_cache PASSED
test_spawn.py::PackageRegistryAccess::test_present_cache_dir_added_to_allow_read PASSED
test_spawn.py::PackageRegistryAccess::test_registry_hosts_merged_into_allowed_domains PASSED
...
============================== 40 passed in 0.25s ==============================
```
**Verdict: PASS.** 40/40 passed, 0 failures, 0 skips. No regressions
anywhere else in the suite (`RepoConfigRefusal`, `SpawnCmd`,
`DryRunModelReflection`, `BoardSnapshot`, `SessionResult`, `Classify`,
`Ledger`, `OwnershipReport`, `RequireDoctor`, `Drive` all green).

---

## 2. AC1 — fresh workspace gets cache-or-registry access — PASS

Set up a throwaway fresh git repo (no board, no prior state) and invoked
the real CLI entrypoint for role `coding` with `--dry-run` (bypasses the
board requirement per `main()`:
`require_board(a.cwd, a.no_contract or a.dry_run)`).

Command:
```
git init -q /tmp/.../qa38work/repo
python3 /home/jwjung/.tokenmaxxxer/work/muster-issue-38-qa/spawn.py coding "test task" \
  -C /tmp/.../qa38work/repo --dry-run
```
Output:
```json
{
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": [
        "api.anthropic.com", "*.github.com", "github.com",
        "registry.npmjs.org", "pypi.org", "files.pythonhosted.org",
        "proxy.golang.org", "sum.golang.org", "crates.io",
        "static.crates.io", "repo.maven.apache.org"
      ]
    },
    "filesystem": {
      "allowRead": ["/home/jwjung/.npm"]
    },
    "allowUnsandboxedCommands": false
  },
  ...
  "model": "sonnet"
}
--model sonnet
```
The 8 `PACKAGE_REGISTRY_HOSTS` are merged into `allowedDomains` alongside
the role's pre-existing entries, and `/home/jwjung/.npm` (this host's real
npm cache — the only `PACKAGE_CACHE_DIRS` candidate that exists on this
box) is mounted read-only into `allowRead`.

**Verdict: PASS.** Fresh workspace gets both the cache mount (when present)
and the registry allowlist fallback, exactly as specced.

---

## 3. AC2 — documented, matches current spawn.py — PASS (minor doc nit)

`README.md:334-368` has a dedicated section:

```
### Package-registry access (issue #38)

A fresh sandboxed workspace has no package cache, so `go build`/`npm
install`/`pip install`/etc. hit the network boundary on the very first
dependency fetch. `role_settings()` addresses this two ways:

1. **Read-only host cache mount (default path).** ... an
   issue-scoped spawn also layers a `file://<host GOMODCACHE>/cache/download`
   source in front of `GOPROXY` ... npm/pip/cargo/Maven cache directories
   are still added to `allowRead` when present, but those tools' own cache
   env vars (`npm_config_cache`, `PIP_CACHE_DIR`, ...) are unconditionally
   redirected to the empty workspace `.muster-cache/` ...
2. **Registry allowlist (fallback for cache misses).** `PACKAGE_REGISTRY_HOSTS`
   ... is merged into every sandboxed role's `sandbox.network.allowedDomains` ...

**Trade-off, explicit:** the cache mount is read-only and low-risk ...
The registry allowlist is higher but bounded risk ...
```

Cross-checked against current `spawn.py`:
- `role_settings()` lines 344-368 do exactly what's described (registry
  merge gated on `sandbox.enabled`; cache-dir mount gated the same way,
  `os.path.exists` only, silent skip if absent).
- `go_proxy_layer()` (line 66) matches "only actively consulted... for
  Go" — it only fires when `GOMODCACHE` is already in `allowRead`.
- `_spawn_one()` lines 1580-1597 confirm "issue-scoped spawn also
  layers..." — the `.muster-cache` write-redirection and the
  `go_proxy_layer()` call are both inside `if issue is not None:`, so the
  doc's qualifier is accurate, not aspirational (see §4e below, confirmed
  by execution).

**Drift found (cosmetic only):** the doc writes the npm env var in
lowercase, `npm_config_cache`, which does match the code (`_spawn_one` sets
lowercase `"npm_config_cache"` at line 1592 for the workspace redirection —
note this is a *different* var than `NPM_CONFIG_CACHE`, the uppercase one
`PACKAGE_CACHE_DIRS` reads for the read-only mount at line 59). This is a
real naming asymmetry in the code itself (mount-detection reads
`NPM_CONFIG_CACHE`, redirection writes `npm_config_cache`), not a doc bug —
the doc happens to name the correct (lowercase, write-side) var in that
sentence. No functional drift found otherwise.

**Verdict: PASS.**

---

## 4a. Edge case — empty-but-existing cache dir — PASS

```python
os.environ["NPM_CONFIG_CACHE"] = ".../qa38work/emptycache"  # mkdir'd, 0 files
import spawn
out = spawn.role_settings("coding")
print(out["sandbox"]["filesystem"]["allowRead"])
```
Output:
```
allowRead: ['/tmp/.../qa38work/emptycache']
```
**Verdict: PASS.** `role_settings()` only checks `os.path.exists`
(spawn.py:364), not emptiness — an empty dir is mounted exactly like a
populated one, which is correct (a fresh cache should get read-only access
too; there's simply nothing useful in it yet).

---

## 4b. Edge case — env var pointing at a file, not a directory — UNFILED bug found

```python
open(".../qa38work/notadir_gomodcache", "w").write("not a directory\n")
os.environ["GOMODCACHE"] = ".../qa38work/notadir_gomodcache"
import spawn
out = spawn.role_settings("coding")
print("allowRead:", out["sandbox"]["filesystem"]["allowRead"])
print("go_proxy_layer:", spawn.go_proxy_layer(out))
```
Output:
```
allowRead: ['/tmp/.../qa38work/notadir_gomodcache', '/home/jwjung/.npm']
go_proxy_layer: file:///tmp/.../qa38work/notadir_gomodcache/cache/download,https://proxy.golang.org,direct
```
No error, no warning — the file path is silently accepted as if it were a
valid cache directory, added to `allowRead`, and `go_proxy_layer()` builds
a `file://<path>/cache/download` GOPROXY source pointing *inside* a regular
file (a nonsensical filesystem path — `<file>/cache/download` cannot
exist).

**Verdict: FAIL (edge case exposes a real defect).**

### UNFILED(defect confirmed by reproduction, awaiting human triage)

**Title:** `role_settings()`/`go_proxy_layer()` don't validate that a
package-cache env var points at a directory — a file path is silently
accepted and turned into a broken GOPROXY source.

**Repro steps:**
1. `touch $SOMEPATH` where `$SOMEPATH` is a plain file.
2. `export GOMODCACHE=$SOMEPATH` (or any of the other `PACKAGE_CACHE_DIRS`
   vars — same code path, same bug).
3. Run `spawn.role_settings("coding")` (or `spawn.py <role> ... --dry-run`).

**Expected:** either skip the path (same as "doesn't exist" — currently
handled correctly for that case), or fail loudly, since a file can't
usefully be mounted read-only as a directory nor used as a
`file://.../cache/download` GOPROXY source.

**Actual:** `os.path.exists(cache_path)` (spawn.py:364) returns `True` for
regular files too, so the file path is added to `allowRead` unconditionally.
`go_proxy_layer()` (spawn.py:78-83) then does
`host_path in allow_read` → true → builds
`file://<file-path>/cache/download,...` — a GOPROXY entry whose first
source is an unreachable path. Downstream effect on a real spawn: `go
build`/`go test` would either error probing that bogus GOPROXY source or
silently fall through to the next source (`https://proxy.golang.org`),
masking the misconfiguration rather than surfacing it — same
silent-failure shape the rest of this codebase explicitly designs against
(see `require_no_repo_config`'s docstring philosophy: "정지, 명시적
opt-out... 사고가 아니라 결정이 되게").

**Environment:** this repo at commit `746165121f2b75e489cd3279362e7e001e49b71f`
on `issue-38/qa`, Python 3.10.12, Linux 6.8.0-110-generic.

**Evidence:** full command + output pasted above in §4b.

**Fix suggestion (for triage, not applied by this QA session):** change the
`os.path.exists(cache_path)` check at spawn.py:364 to
`os.path.isdir(cache_path)`.

---

## 4c. Edge case — allowedDomains merge/dedup — PASS

Built a fake `ROOT`/`roles/probe.json` (monkeypatched `spawn.ROOT`,
`spawn.KNOWN`, `spawn.USER_SETTINGS` in-process; nothing in the real repo
touched) declaring pre-existing domains including a duplicate of a
registry host:

```python
role_spec["sandbox"]["network"]["allowedDomains"] = [
    "my-extra-domain.example.com", "registry.npmjs.org", "pypi.org"
]
out = spawn.role_settings("probe")
```
Output:
```
input pre-existing: ['my-extra-domain.example.com', 'registry.npmjs.org', 'pypi.org']
merged domains: ['my-extra-domain.example.com', 'registry.npmjs.org', 'pypi.org',
                  'files.pythonhosted.org', 'proxy.golang.org', 'sum.golang.org',
                  'crates.io', 'static.crates.io', 'repo.maven.apache.org']
dup count for registry.npmjs.org: 1
extra domain preserved: True
no dup entries overall: True
```
**Verdict: PASS.** The existing extra domain (`my-extra-domain.example.com`)
is preserved, the pre-existing duplicate (`registry.npmjs.org`) is not
duplicated, and every registry host not already present is appended
exactly once.

---

## 4d. Edge case — real sandboxed session reads from mounted cache — BLOCKED(infeasible within this QA session)

Inspected the composed spawn command by monkeypatching `subprocess.Popen`
inside a real call to `spawn._spawn_one(work, "coding", "probe again",
unattended=True, issue=None)` (intercepting only invocations of the
`claude` binary itself; all other subprocess calls — git clone of the
rulebook, etc. — ran for real) to capture the actual argv without letting
the child process run:

```
CMD: ['claude', '-p', '--settings', '/tmp/claude-1000/tmp6dep6svl.json',
      '--permission-mode', 'acceptEdits', '--output-format', 'stream-json',
      '--verbose', '--plugin-dir', '.../rulebooks/tokenmaxxxer-coding/coding',
      ... (7 more --plugin-dir), '--model', 'sonnet']
```
The `--settings` file is the same merged JSON shown in §2 (it's written by
`json.dump(s, f)` immediately before `spawn_cmd()` is called, and
`role_settings()` output is what appears there), then unlinked by
`_spawn_one`'s `finally` block once the (fake) session exits.

Attempting an actual **real** sandboxed session (letting `claude` itself
run, inside its own declared sandbox, reading a file from the mounted
cache path) was not carried out: this QA session is itself a
`claude`-spawned role session running under this same `spawn.py`
machinery, and recursively spawning another live `claude -p` session from
inside it would (a) consume a second, uncontrolled session's worth of
tokens/credits for no additional signal beyond what §2's settings JSON and
this composed argv already establish, (b) require the real `claude` binary
to itself run a nested sandbox inside this already-sandboxed environment
(unclear whether that nests cleanly, and not something to discover by
trial in a shared repo), and (c) is outside this session's Bash sandbox
network allowlist regardless of what the child sandbox declares.

**What this leaves unverified:** whether the sandbox runtime that actually
executes `--settings`'s `allowRead` entry truly permits a file read from
that path at runtime (as opposed to `role_settings()` merely producing the
correct *declaration*). That is a property of the external `claude`
sandbox enforcement, not of `spawn.py`'s Python logic, and is outside what
this repo's own test suite or QA harness can exercise without a live
session.

**Verdict: BLOCKED(real `claude` sandbox session not run — nested-spawn cost/feasibility judged out of scope for this QA pass; composed command and settings content otherwise verified above).**

---

## 4e. Edge case — non-`--issue` (ad-hoc) spawn path — PASS (confirms doc, no cache/proxy layering)

Called `spawn._spawn_one()` directly with `issue=None` against a throwaway
git repo (board marker stubbed in), with `subprocess.Popen` monkeypatched to
intercept only the `claude` invocation (git/gh calls ran for real) so the
composed `env` passed to the child could be captured without actually
starting a session:

```python
rc = spawn._spawn_one(work, "coding", "adhoc probe task", unattended=True, issue=None)
extra_env = {k: v for k, v in captured["env"].items() if k in
             ("GOCACHE","GOMODCACHE","GOENV","GOPATH","XDG_CACHE_HOME",
              "npm_config_cache","PIP_CACHE_DIR","GOPROXY")}
```
Ambient environment checked first (this QA session's own shell — itself a
muster-spawned session — already carries these from its own `--issue`
spawn):
```
$ python3 -c "import os; print({k:os.environ.get(k) for k in [...]})"
{'GOMODCACHE': '/home/.../muster-issue-38-qa/.muster-cache/gomod',
 'GOCACHE': '/home/.../muster-issue-38-qa/.muster-cache/go-build',
 ... (GOENV, GOPATH, XDG_CACHE_HOME, npm_config_cache, PIP_CACHE_DIR similarly under .muster-cache/)
 'GOPROXY': None}
```
Output of the `issue=None` probe — captured child `env` for the *new*
ad-hoc spawn:
```
cache/proxy env vars present in extra_env for issue=None spawn:
{'npm_config_cache': '/home/.../muster-issue-38-qa/.muster-cache/npm',
 'PIP_CACHE_DIR': '/home/.../muster-issue-38-qa/.muster-cache/pip',
 'GOMODCACHE': '/home/.../muster-issue-38-qa/.muster-cache/gomod',
 'XDG_CACHE_HOME': '/home/.../muster-issue-38-qa/.muster-cache/xdg',
 'GOENV': '/home/.../muster-issue-38-qa/.muster-cache/goenv',
 'GOCACHE': '/home/.../muster-issue-38-qa/.muster-cache/go-build',
 'GOPATH': '/home/.../muster-issue-38-qa/.muster-cache/gopath'}
```
These values are **byte-identical to the pre-existing ambient
environment** — i.e. `_spawn_one(issue=None)` did not add or modify any of
them; they simply passed through from `{**os.environ, **extra_env}`
because `extra_env` was never populated for this path. Crucially,
`GOPROXY` is absent in both the ambient environment and the captured child
env: `go_proxy_layer()` was never called for the ad-hoc path (its call
site at spawn.py:1595 is inside the same `if issue is not None:` block).

**Verdict: PASS (behaves as documented).** Confirmed by execution: the
`.muster-cache` workspace-redirection layer and the `GOPROXY`
host-cache-first layering are both **exclusively** applied on the
`--issue` spawn path (`_spawn_one`, lines 1580-1597). A non-`--issue`
(ad-hoc) spawn gets the `role_settings()`-level benefits from §2/§4a (the
read-only `allowRead` mount and the `PACKAGE_REGISTRY_HOSTS` network
allowlist — those are unconditional on `sandbox.enabled`, not on `issue`),
but **not** the write-cache workspace redirection nor the Go
proxy-layering optimization. This matches README.md's wording ("an
**issue-scoped** spawn also layers...") — not a drift, but worth flagging
explicitly since it means ad-hoc/adhoc-mode Go builds get zero benefit from
a warm host GOMODCACHE beyond the read-only mount itself (no `GOPROXY`
entry to actually make Go consult it) — functionally the ad-hoc path relies
entirely on the registry allowlist fallback for Go, same as any other
uncached ecosystem.

---

## Summary of verdicts

| Item | Verdict |
|---|---|
| Full test suite | **PASS** (40/40) |
| AC1 (fresh workspace cache-or-registry) | **PASS** |
| AC2 (documented, matches code) | **PASS** (cosmetic nit: no functional drift) |
| 4a empty-but-existing cache dir | **PASS** |
| 4b env var → file, not dir | **FAIL** → `UNFILED` bug filed above |
| 4c allowedDomains merge/dedup | **PASS** |
| 4d real sandbox file-read via mounted cache | **BLOCKED**(nested live-session spawn out of scope for this QA pass) |
| 4e non-`--issue` ad-hoc spawn path | **PASS** (confirms no GOPROXY/`.muster-cache` layering off the issue path, as documented) |

## UNFILED bugs

1. **UNFILED(defect confirmed by reproduction, awaiting human triage)** —
   `role_settings()`/`go_proxy_layer()` accept a file path (not a
   directory) for any `PACKAGE_CACHE_DIRS` env var without validation,
   silently mounting it into `allowRead` and building a broken
   `file://<file>/cache/download` GOPROXY source. See §4b for full repro,
   expected/actual, and suggested fix (`os.path.isdir` instead of
   `os.path.exists` at spawn.py:364).

loop_state: phase-2 complete
