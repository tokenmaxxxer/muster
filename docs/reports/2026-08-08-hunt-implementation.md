---
proposal: docs/issue-476/proposals/implementation.md
---

# Hunt record — implementation

## after-proposal — stance 0: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — proposal's own literal scope choice for wiring reexecution_gate into blocking_causes (`{"reason": ..., "scope": {"gates/"}}`, step 3) makes a failed reexecution verdict invisible to `classify()` for any PR whose changed files do not start with `gates/` — i.e. exactly the normal case, since the PR being re-executed is a role's implementation/record PR, not a gates/ change.
Kind: design-error
Seed: docs/issue-476/proposals/implementation.md (H1 item 3: "Wire reexecution_gate's verdict into landing_readiness.py's blocking_causes construction ... a fail/error verdict ... becomes one {"reason": ..., "scope": {"gates/"}}-shaped (or PR-specific scope, decided at implementation time...) entry")
cap_seconds: 120
tier: default
diff_stat_lines: N/A (proposal doc, ~150 lines)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:02:00Z

### Reproduce
Using the existing `classify()` machinery the proposal explicitly says it will reuse unchanged (`gates/landing_readiness.py`), with the scope shape the proposal names literally for the reexecution_gate wiring:

```python
import sys
sys.path.insert(0, "gates")
from landing_readiness import classify

causes = [{"reason": "reexecution_gate: command exited 1", "scope": {"gates/"}}]
pr_files = frozenset(["src/feature.py", "roles/records/476-implementation.md"])
result = classify("OPEN", "pass", True, True, pr_files, tuple(causes))
print(result)
```

### Observed
```
('READY', None)
```
A PR whose role record contains an unreproduced/false claim, and for which `reexecution_gate` produced a `fail` verdict, is classified READY — the blocking cause never fires because `pr_files` (the PR's own record/source changes) don't match the `gates/` scope prefix. `classify()`'s scope semantics (any(f.startswith(tuple(scope)) for f in pr_files)) require the *offending PR itself* to touch `gates/` for the cause to apply to it — but the whole point of H1 is to catch false claims in ordinary role PRs that touch application code and records, not gates/.

### Expected
A `fail`/`error` reexecution verdict for a specific PR's claim should block that PR regardless of which files it touched — the proposal itself flags this as unresolved ("or PR-specific scope, decided at implementation time to match the existing scope semantics") but ships the literal `{"gates/"}` example as the illustrative wiring, and the existing `scope` mechanism has no PR-identity concept (only file-path prefixes) to express "this cause applies to PR #N specifically" without a hack such as adding every one of that PR's own file paths as scope entries (workable, but not what's specified, and not exercised by any test the proposal names).

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — `gates/ci.py:_phase2_record_evidence()` (and its sibling `gates/closure_sweep.py:classify()`'s `has_record_evidence` path) treat any non-empty `loop_state` as "closing intent" evidence that waives the phase-2 "Closes #issue" requirement — a rule that predates this diff and was written when the enum's non-"landed" values (`scope-proposed`/`scope-approved`/`in-progress`) all meant "still ongoing." This diff adds `refused`/`not-needed`/`cannot-verify` to the same enum, values whose entire purpose (per gates.py's new `record_refusal_reasoned()`) is to declare that work was explicitly NOT delivered. Because `_phase2_record_evidence` deliberately ignores the *value* of `loop_state` (only checks non-empty, per issue #284's design comment "loop_state 의 값은 보지 않는다"), a merged phase-2 PR whose record says `loop_state: refused` now silently satisfies the "must close the issue" CI check and the closure-sweep evidence check — the refusal-declaring record cancels the very enforcement that #284 built specifically to make sure delivery was real. Nobody updated `_phase2_record_evidence`/`closure_sweep.classify` to exclude the new refusal states when this diff added them.
Kind: composition
Seed: git diff origin/main...HEAD (gates/gates.py record_refusal_reasoned + roles/*.json loop_state enum additions) vs gates/ci.py:_phase2_record_evidence and gates/closure_sweep.py has_record_evidence, both pre-existing and unmodified by this diff
cap_seconds: 180
tier: size:large
diff_stat_lines: 1198 insertions across 17 files
started_at: 2026-08-08T10:21:50Z
ended_at: 2026-08-08T10:33:00Z

### Reproduce
```
python3 -c "
import sys; sys.path.insert(0, 'gates')
import gates
text = '''---
loop_state: refused
reason: could not verify claim
---
body
'''
fm = gates.record_frontmatter(text)
print(bool(fm.get('loop_state','').strip()))
"
```
(run from repo root; `gates/ci.py:_phase2_record_evidence` performs exactly this `bool(fm.get("loop_state","").strip())` check on line 282, and its result gates whether the "Closes #issue" CI requirement in `gates/ci.py` around line 414 is waived; `gates/closure_sweep.py:classify()` uses the same boolean, sourced identically, to decide whether a merged-PR-with-open-issue counts as a violation.)

### Observed
`True` — a record whose `loop_state` explicitly declares the work was refused (never delivered) is treated identically to a record declaring `loop_state: landed`, satisfying both the CI closes-check waiver and the closure-sweep delivery-evidence check.

### Expected
A refusal state (`refused`/`not-needed`/`cannot-verify`) should not count as "closing intent" evidence — if anything it should mean the opposite (no delivery occurred, the issue should stay open, closing the PR without `Closes #issue` should still be flagged). `_phase2_record_evidence` and `closure_sweep`'s `has_record_evidence` computation need to special-case (or exclude) the new refusal states, the same way `_terminal_loop_state()` was updated elsewhere in this diff to keep `landed` last in the enum.

## after-proposal — stance 0: assume the gate just touched (gates/claim_scan.py, per the proposal below) is bypassable — find the bypass.

Verdict: FINDING — the proposal's own `--base` design silently falls back to permissive whole-repo `git ls-files` targets whenever the diff command errors (bad ref, shallow clone, wrong merge-base), reopening case0 (the exact bug `--base` exists to close) with no error signal.
Kind: design-error
Seed: docs/issue-490/proposals/implementation.md ("What will be done" #1: "`_repo_targets(repo, base=None)`: when `base` is given, source targets from `git diff --name-only <base>...HEAD` (falling back to the existing whole-repo `git ls-files` behavior if the diff command itself errors, e.g. unknown ref — fail toward the current behavior, never toward zero targets/spurious false-rejects).")
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (survey.md + proposal.md)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:05:00Z

### Reproduce
```
git diff --name-only nonexistent-ref...HEAD
```
run inside this repo (or any repo where `--base` is given a ref that doesn't resolve — a typo, a stale branch name, or a shallow clone that lacks the base commit, which is common in CI checkouts).

### Observed
```
fatal: 애매한 인자 'nonexistent-ref...HEAD': 알 수 없는 리비전 또는 작업 폴더에 없는 경로.
경로와 리비전을 구분하려면 다음과 같이 '--'를 사용하십시오:
'git <명령> [<리비전>...] -- [<파일>...]'
```
i.e. the diff subprocess exits non-zero. Per the proposal text, `_repo_targets()` is designed to catch exactly this and fall back to whole-repo `git ls-files` — the same target set case0 exploited (a fabricated claim citing any real-but-unrelated tracked file passes with 0 findings). No warning, no distinct exit code, nothing that would let a caller (or the human reading `claim_scan`'s output) know diff-scoping silently failed and the check reverted to its known-bypassable mode. Since the proposal explicitly rules out a caller (CI shallow clone, wrong base spec, refname typo) surfacing this, `--base` is a bypass whenever the ref it's given doesn't resolve — attacker-controlled or not, any mundane CI misconfiguration reopens case0 with the gate reporting success.

### Expected
When `--base` is supplied but the diff command fails, `_repo_targets()`/`main()` should not silently degrade to the pre-fix permissive whole-repo set — it should either hard-fail loudly (distinct from a clean pass) or at minimum print/log that diff-scoping was requested but not honored, so a case0-shaped fabrication under a broken `--base` doesn't pass with 0 findings and no indication the intended check never ran.
