---
proposal: docs/issue-476/proposals/architecture.md
---

# Hunt record — architecture

## after-proposal — stance 0: assume the gate just designed is bypassable — find the bypass

Verdict: FINDING — the H1 trigger/execution design binds the gate's pass verdict only to the exit code of whatever command is cited next to the claim, with no check that the command actually exercises the claim it's attached to, so a trivially-true cited command (e.g. `echo ok` / `true` / `exit 0`) satisfies both the "adjacent machine-runnable command" hard-fail-avoidance rule (§1) and the re-execution ground-truth check (§3), letting a session write "tests pass" backed by a no-op command and pass the gate without any real verification.
Kind: design-error
Seed: docs/issue-476/proposals/architecture.md (commit c8cc09a)
cap_seconds: 60
tier: default
diff_stat_lines: ~205 (3 files, docs-only)
started_at: 2026-08-08T18:57:03+09:00
ended_at: 2026-08-08T18:58:30+09:00

### Reproduce
Read §1 ("Trigger") and §3 ("Execution and ground truth") of the Decision section. §1 says a
claim-language hit is a hard fail *only if* there is no "adjacent machine-runnable command (a
fenced code block or an explicit `Repro:`/`Verify:` line within N lines of the match)". §3 says
the gate's ground truth is "the subprocess's own exit code ... where the record cites specific
expected output, a diff against that" — but citing expected output is optional ("where the record
cites"), not required. Nothing in the design requires the cited command to actually correspond to
or exercise the thing being claimed. Construct the adversarial record:

```
Tests pass — verified.

Repro:
\`\`\`
true
\`\`\`
```

Walking through the design: claim_scan.py's regex matches "verified"/"pass" (word-boundary,
case-insensitive) → satisfied. An adjacent fenced code block exists within N lines → the
hard-fail-on-no-command branch does not fire. reexecution_gate.py runs `true` in the SHA-pinned
worktree → exit code 0, no cited expected output to diff against → ground truth is "pass".
`.reexecution/<issue>-<role>.json` records exit 0. `landing_readiness.py` sees no
`reexecution_gate` failure and aggregates green.

### Observed
Per the design as written, the gate produces a `pass` verdict for a record whose claim is
completely unverified by its own cited command — the mechanism only proves "a command called
`true` returned 0", not that the tests described in prose actually ran or passed.

### Expected
The gaming-resistance argument for H1 (provisioning) explicitly claims "the honest-work path" is
the only way to pass — "a session would have to make the actual committed code pass the actual
cited command". That claim is false as designed: the session only has to cite *some* command that
exits 0, with no requirement that the command's semantics match the claim text, and no default
requirement that expected output be specified/diffed. The design needs either (a) mandatory
expected-output binding (not "where the record cites"), or (b) some claim-to-command semantic
correspondence check, to close this. As written, the regex-plus-exit-code contract is satisfiable
by a no-op.
