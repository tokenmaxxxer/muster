---
kind: verify-record
loop_state: cleared-with-open-findings
code_under_review: "7f30bf0fbee9b606481646297eec7408b14bdf2f"
what-was-done: "Phase-2 execution per approved docs/issue-38/proposals/verify.md: independently re-ran the 4-item attempt list against a fresh origin/main worktree checkout (0dce2e7, confirmed byte-identical to the proposal's cited 7f30bf0f on every file this issue touches) -- 4b's file-instead-of-directory repro, GOPROXY/CARGO_HOME wiring re-derivation by direct code read, full test_spawn.py rerun, and a 4d scope-out currency check on _spawn_one()."
why: "Approved verify.md proposal committed to independent reproduction, not citation of qa's or the phase-1 survey's conclusions, per contract v3 s19/s20; PR #49 carries the issue-level 'APPROVE issue-38/verify' comment from JiwonJung94 (listed in docs/specs/approvers.md), counted as a valid phase-2 approval under the s19 single-account-mode amendment (tokenmaxxxer-core PR #15)."
upstream-basis: "docs/issue-38/proposals/verify.md (approved phase-1 plan), docs/issue-38/reports/verify/survey.md (this role's own phase-1 survey), docs/issue-38/reports/coding.md and docs/issue-38/reports/qa.md (read only, not cited as basis for verdicts below), issue #38, issue #46."
next-steps: "Issue #46 (os.path.exists vs os.path.isdir at spawn.py:364) remains the sole open item, already tracked and confirmed still open/unfixed at this execution's sha -- no verify-side filing or fixing authority, resolution belongs to a future coding pass on issue #46. 4d's live nested-spawn gap remains BLOCKED, not something this or any verify session inside the same sandboxing scheme can close without a deliberately budgeted follow-up."
open_findings:
  - finding: "4b (re-confirmed by direct, independent reproduction, not cited from qa or the phase-1 survey): a PACKAGE_CACHE_DIRS env var (e.g. GOMODCACHE) pointing at a regular file, not a directory, passes spawn.py:364's os.path.exists check, gets mounted into sandbox.filesystem.allowRead, and go_proxy_layer() then builds a broken file://<file>/cache/download GOPROXY source. Reproduced against a fresh origin/main worktree at 0dce2e7 (spawn.py:364 unchanged, still os.path.exists not os.path.isdir)."
    resolution_path: "Tracked by issue #46 (open, confirmed live via gh issue view 46 at execution time). No silent fix landed on main since qa's original filing; source at spawn.py:364 is byte-identical to what qa and the phase-1 survey both inspected. Correctly scoped out of docs/issue-38/proposals/coding.md's frozen write set. Filing/fixing outside verify role scope."
closed_checks:
  - check: "4b repro: GOMODCACHE pointing at a file produces a broken file:// GOPROXY source"
    code_sha: "0dce2e7e3078339110b5cbec3637bc7c5ed359b7"
  - check: "issue #46 open, tracks 4b, no silent fix on main"
    code_sha: "0dce2e7e3078339110b5cbec3637bc7c5ed359b7"
  - check: "PACKAGE_CACHE_DIRS cargo entry is (None, \"~/.cargo/registry\"), matching coding.md's documented CARGO_HOME correction"
    code_sha: "0dce2e7e3078339110b5cbec3637bc7c5ed359b7"
  - check: "go_proxy_layer() call site (spawn.py ~1595) is gated inside `if issue is not None:`"
    code_sha: "0dce2e7e3078339110b5cbec3637bc7c5ed359b7"
  - check: "role_settings()'s registry-merge and cache-mount blocks are both gated on sb0.get(\"enabled\"); all 9 roles/*.json have sandbox.enabled: true"
    code_sha: "0dce2e7e3078339110b5cbec3637bc7c5ed359b7"
  - check: "test_spawn.py full suite passes, no regression"
    code_sha: "0dce2e7e3078339110b5cbec3637bc7c5ed359b7"
  - check: "_spawn_one()'s composed subprocess invocation / .muster-cache env block unchanged from what qa's 4d already inspected -- BLOCKED scope-out still correct"
    code_sha: "0dce2e7e3078339110b5cbec3637bc7c5ed359b7"
---

# Issue #38 — verify phase-2 verdict record

## What was done

Executed the 4-item attempt list from the approved
`docs/issue-38/proposals/verify.md`, against a fresh `git worktree`
checkout of `origin/main` (`0dce2e7e3078339110b5cbec3637bc7c5ed359b7`,
confirmed byte-identical to the proposal's cited `7f30bf0fbee9b606481646297eec7408b14bdf2f`
on every file this issue touches — `git diff 7f30bf0f..origin/main --
spawn.py test_spawn.py roles/ README.md` returns empty). All reproduction
below is my own execution, not a restatement of qa's, coding's, or the
phase-1 survey's conclusions.

## Basis

Approved via the issue-level comment "APPROVE issue-38/verify" from
GitHub user `JiwonJung94`, who is listed in `docs/specs/approvers.md` —
per an amendment to contract v3 s19 (tokenmaxxxer-core PR #15, merged), in
single-account mode this comment counts as a valid phase-2 approval (a PR
review Approve is not required in this mode). PR #49 carries this
branch's work.

## Attempts

---

### attempt: 1 — re-run qa's 4b repro (env var pointing at a file, not a
directory) directly against `main` HEAD, independent of qa's own working
copy and of the phase-1 survey's prior run

outcome: reproduced

evidence:
Ran against the `origin/main` worktree checkout, calling directly into
that checkout's `spawn.py`:

```python
import os, tempfile
d = tempfile.mkdtemp()
filepath = os.path.join(d, "notadir_gomodcache")
open(filepath, "w").write("not a directory\n")
os.environ["GOMODCACHE"] = filepath
import spawn
out = spawn.role_settings("coding")
print("allowRead:", out["sandbox"]["filesystem"]["allowRead"])
print("go_proxy_layer:", spawn.go_proxy_layer(out))
```
Output:
```
allowRead: ['/tmp/claude-1000/tmpbw5o2vwe/notadir_gomodcache', '/home/jwjung/.npm']
go_proxy_layer: file:///tmp/claude-1000/tmpbw5o2vwe/notadir_gomodcache/cache/download,https://proxy.golang.org,direct
```
The plain file at `GOMODCACHE` is accepted into `allowRead` and used to
build a broken `file://<file>/cache/download` GOPROXY source — same shape
qa originally filed and the phase-1 survey re-derived. `spawn.py:364` on
this checkout is still `os.path.exists(cache_path)` (not `os.path.isdir`),
confirming the defect is unpatched at current `main` tip and that
tracking issue #46 (`gh issue view 46`, `state: OPEN`, body matches this
exact repro) remains open and accurate — not stale, not silently
abandoned.

finding:
  requirement: "role_settings()/go_proxy_layer() must not silently accept
    a non-directory path from a PACKAGE_CACHE_DIRS env var (spawn.py:364)"
  verdict: Incorrect
  evidence: "see reproduction above; spawn.py:364 uses os.path.exists,
    accepting regular files"
  rationale: "os.path.exists returns True for files as well as
    directories, so a misconfigured cache env var pointing at a file is
    mounted into allowRead and fed into a nonsensical GOPROXY file://
    source (<file>/cache/download can never exist); go build/test then
    either errors probing that source or silently falls through to
    https://proxy.golang.org, masking the misconfiguration rather than
    surfacing it — the same silent-failure shape this codebase otherwise
    designs against"
  spec_vs_built: "spec (implicit, from the cache-dir mounting design in
    docs/issue-38/proposals/coding.md): only real cache directories should
    be mounted read-only. Built: os.path.exists accepts any existing path,
    directory or file, with no isdir check."
  addressed_to: coding
  severity: advisory
  severity_rationale: "Chromium-scale Medium — limited-scope
    misconfiguration-masking bug, no code execution, no privilege
    escalation, no cross-boundary data access; only reachable by
    controlling the host-side env var that spawn.py itself reads (not
    attacker-controlled input), and its worst concrete effect is a build
    failure or a silent no-op fallback to the public Go proxy. Correctly
    triaged and tracked as issue #46, explicitly scoped out of
    docs/issue-38/proposals/coding.md's frozen write set rather than left
    unfiled. Not a new defect beyond what qa already found and got filed
    — recorded here as `reproduced` per this skill's rule (independent
    reproduction, not a restatement), but does not add new severity
    information beyond what issue #46 already carries."

---

### attempt: 2 — confirm go_proxy_layer()/CARGO_HOME wiring by reading
`main`'s `spawn.py` directly, checking coding.md's `resolved_findings` and
`closed_checks` against current code rather than the PR description

outcome: not-reproduced

evidence:
Read `spawn.py` on the `origin/main` worktree checkout.

`PACKAGE_CACHE_DIRS` (lines 57-63):
```
PACKAGE_CACHE_DIRS = [
    ("GOMODCACHE", "~/go/pkg/mod"),
    ("NPM_CONFIG_CACHE", "~/.npm"),
    ("PIP_CACHE_DIR", "~/.cache/pip"),
    (None, "~/.cargo/registry"),
    ("MAVEN_REPO", "~/.m2/repository"),
]
```
matches coding.md's claim exactly: `CARGO_HOME` is not probed directly
(the documented correction — `CARGO_HOME` points at `~/.cargo`, parent of
`registry/`, not the cache itself); the cargo entry always probes the
fixed default `~/.cargo/registry` with `env_var=None`.

`go_proxy_layer()` (lines 66-83) builds
`file://<GOMODCACHE>/cache/download,https://proxy.golang.org,direct` only
when the host GOMODCACHE candidate is present in
`sandbox.filesystem.allowRead`, matching coding.md's `resolved_findings`
description and the two dedicated tests
(`test_go_proxy_layer_prefers_mounted_host_cache`,
`test_go_proxy_layer_none_when_cache_not_mounted`).

Call site (lines 1580-1597, inside `_spawn_one`):
```
        if issue is not None:
            ...
            proxy = go_proxy_layer(s)
            if proxy:
                extra_env["GOPROXY"] = proxy
```
confirms `go_proxy_layer()` fires only for `--issue` spawns, matching both
coding's and qa's description of the ad-hoc-path gap (qa.md §4e).

`role_settings()`'s two additive blocks (lines 344-367) are each guarded
by `if sb0.get("enabled"):` inside `if sb0 := s.get("sandbox", {}):` —
confirmed by direct read, both blocks, matching the phase-1 survey's item
4 "additive-only, `sandbox.enabled`-gated" claim. All 9 `roles/*.json`
files on this checkout have `sandbox.enabled: true`
(`grep -A1 '"enabled"' roles/*.json`), so — as the phase-1 survey already
noted — there is still no role on `main` to exercise the disabled branch
against; this remains an assertion about code structure, not something
exercisable via a real role file today. Not a defect; not filed.

Claims hold as recorded in coding.md; no discrepancy found between the PR
description and the actual checked-out code.

---

### attempt: 3 — run `test_spawn.py` against `main`'s checked-out files
to confirm no regression since qa's 40/42-pass runs

outcome: not-reproduced

evidence:
```
$ cd <origin/main worktree> && python3 -m pytest test_spawn.py -q
..........................................                               [100%]
42 passed in 0.25s
```
42 passed, 0 failed, 0 skipped — matches the phase-1 survey's count
exactly (qa's own run showed 40 passed at the pre-merge sha `8bda829`; the
2-test difference is other issues' tests merged into `main` since, per the
proposal's own note that "test count may differ from qa's snapshot since
other issues have merged since" — not a regression in this issue's
`PackageRegistryAccess` suite, which is present and green in the verbose
tail). No new failures, no new skips, no regression.

---

### attempt: 4 — check whether 4d's scope-out is still the correct call
by reading `_spawn_one()`'s sandbox invocation on `main` for anything that
would make a live nested-spawn verification newly feasible or necessary

outcome: not-reproduced

evidence:
Read `_spawn_one()` (same region inspected in attempt 2, lines ~1560-1600)
on the `origin/main` worktree checkout. The composed `claude -p` subprocess
invocation, the `--settings` JSON write/unlink lifecycle, and the
`.muster-cache` env redirection block are structurally unchanged from what
qa.md §4d already inspected (same `subprocess.Popen(...)` call shape, same
`finally`-block settings-file cleanup, same env var set). No new code path
was added between qa's inspection sha and this issue's frozen write set
that would make a live nested `claude -p` spawn newly feasible (still
requires spawning a second, uncontrolled live session from inside this
already-sandboxed one) or newly necessary (nothing changed about what a
nested spawn would additionally verify beyond the settings-JSON content
and composed argv, both already captured by qa without running the child).
The cost/feasibility argument does not change with code content that
itself did not change in this region — per the proposal's own instruction,
citing qa's `BLOCKED` reasoning here rather than re-deriving a nested spawn
attempt. `4d` remains `BLOCKED`(infeasible within this session, same
reasoning as qa.md §4d): the property being asked about (does the external
`claude` sandbox runtime actually honor the `allowRead` declaration at
execution time) is a property of the sandbox runtime, not of `spawn.py`'s
Python logic, and stays outside what this repo's test suite or this
verify session can exercise without a live nested session — not filed as
open because a `BLOCKED` scope-out is not a defect.

---

## Verdict

**cleared** (with one open, non-blocking finding) — no unresolved
*blocking* finding.

Rationale: 4 attempts run, all independently re-derived against a fresh
`origin/main` checkout at the tip current when this record was written
(`0dce2e7e3078339110b5cbec3637bc7c5ed359b7`, confirmed byte-identical to
the proposal's cited `7f30bf0f` on every file this issue touches). One
`reproduced` outcome (attempt 1) carries an inline finding, but it is not
new: it independently confirms the exact defect qa already found, filed,
and got triaged as issue #46 (open, correctly out of this PR's frozen
write set per `docs/issue-38/proposals/coding.md`), and its severity band
(Chromium-scale Medium — limited-scope misconfiguration-masking, no code
execution or privilege boundary crossed) is `advisory`, not `blocking`.
Attempts 2-4 all `not-reproduced`: the GOPROXY/CARGO_HOME wiring, gating,
and test-suite claims all hold under direct re-derivation against current
code (not restated from any other role's record), and attempt 4's
`BLOCKED` scope-out for a live nested-spawn check is confirmed still the
correct call — nothing in `_spawn_one()` changed to make it newly
feasible or newly necessary. No new defect surfaced beyond what qa already
tracked. AC1/AC2 from the issue (fresh workspace gets cache-or-registry
access; mechanism documented with its trade-off) are supported by the
code read in attempts 1-2 and by qa.md's own executed AC1/AC2 passes,
which this session did not need to re-run since the proposal scoped this
verify pass to 4b/wiring/suite/4d, not a full AC re-walk.
