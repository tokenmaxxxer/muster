# Defect-verification record — issue #445

`code_under_review:` `0fa8a2c621e536bcfbd27876ae53b8e122f756ba`
loop_state: reported
Attempt list source: `docs/issue-445/proposals/2026-08-08-spawn-path-silent-failure-hunt.md`
(approved by `APPROVE issue-445/defect-verification`, single-account mode,
`JiwonJung94`, on issue #445).
Repro scripts: `test/test_silent_failure_repros.py` (4 passed).

## What was done

Ran all 4 attempts from the approved proposal's attempt list against
`code_under_review` above, each as a runnable repro in
`test/test_silent_failure_repros.py` (not code-reading-only, per issue
#445's #416 acceptance clause). 2 reproduced (filed as findings addressed
to coding, below); 2 did not (the claimed gap already had a mitigation in
code or in the codebase's own documentation). No new attempts were added
beyond the approved list — proposal scope is frozen post-approval.

## Open findings

2 open, both `addressed_to: coding`, both `severity: advisory` (see the
finding blocks below): (1) `issue_workspace()`'s credential-exclude write
can fail silently with the guard unenforced and unreported; (2)
`_watch(follow=True)` has no bound when the roster entry never appears.

## Next steps

Both findings await coding's resolution (or a filed follow-up issue per
the splitting rules — this role reproduces and files, it does not fix).
No further attempts are open on this issue; if either finding is disputed
by coding, this record is re-examined and the severity band adjusted
in-place, never dropped.

## Open-finding resolution path

Each open finding is `addressed_to: coding` with `severity: advisory` —
downstream loops that depend on coding's output are not blocked pending
resolution; the finding travels as context alongside coding's next pass
on `spawn.py`. Resolution closes when coding either patches the guarded
paths (exclude-write reporting; a bound on the `--follow` loop) or
records a disagreement with the severity/verdict here, which this role
then re-examines per the finding-record skill's dispute path.

---
attempt: proposal item 1 — issue_workspace() `except OSError: pass` around the
  `.git/info/exclude` credential-leak guard write (spawn.py:2964-2983)
outcome: reproduced
evidence: test/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning
  — with `.git/info/exclude` writes forced to raise `OSError(13,
  "Permission denied")`, `issue_workspace()` returns a live workspace
  (no `sys.exit`, no raised exception) whose `.git/info/exclude` contains
  none of the guard's entries (`.mcp.json`, `.gitconfig`, etc. absent),
  and neither stdout nor stderr mentions "exclude" anywhere in the run.
steps: monkeypatched `Path.open` to raise OSError only for
  `.git/info/exclude` opened in append mode; drove `spawn.issue_workspace()`
  end-to-end against a local origin/src pair (no network); captured
  stdout/stderr and read back the resulting workspace's exclude file.
expected: either the exclude write succeeds, or its failure is surfaced to
  the caller/operator in some form (return value, log line, warning).
actual: the write silently fails and `issue_workspace()` returns
  successfully with the credential-leak guard from issue #289 H1
  unenforced and no signal that it didn't take.
---

---
requirement: issue_workspace()'s `.git/info/exclude` write for the issue
  #289 H1 credential-leak guard must not fail silently — a session running
  in a workspace whose exclude guard silently didn't take is exposed to the
  exact credential-in-git-add-A leak the guard exists to prevent, with
  nobody told the guard is absent.
verdict: Incorrect
evidence: spawn.py:2964-2983 (`try: ... except OSError: pass`);
  test/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning
spawn_vs_built: the exclude write is guarded against exactly the failure
  mode this attempt forces (a filesystem-level OSError), but the guard's
  own writer has no equivalent protection — its failure is absorbed with
  no propagation, no log, no follow-up check before the workspace is
  handed to a session that may `git add -A`.
rationale: reproduced with evidence; the failure mode is a silent
  reinstatement of a previously-fixed credential-leak path (#289 H1),
  conditioned on the exclude write failing (rare, needs a specific
  filesystem state) — real impact but requiring that plus a follow-on
  `git add -A` to materialize, which is Chromium-scale Medium ("limited
  info exposure, harmless-alone-but-combinable").
addressed_to: coding
severity: advisory
---

---
attempt: proposal item 2 — `_watch(follow=True)` loop has no bound when the
  roster entry stays absent (spawn.py:2199-2235)
outcome: reproduced
evidence: test/test_silent_failure_repros.py::test_attempt_2_follow_loop_unbounded_on_absent_roster_entry
  — 5 simulated stall cycles with `_roster_load()` returning `{}`
  throughout (no roster entry ever appears): `terminal_hits == 0` across
  all 5 — neither the session-end branch nor the dead-`wrapper_pid` branch
  ever fires, because both require data (`events.jsonl` progress, a
  present roster entry) that never arrives. `_await_bounded()`'s own
  `stall_timeout_min` bound returns each cycle (so each individual call is
  bounded, and each stall does print a diagnostic to stderr), but the
  outer `while True:` in `_watch(follow=True)` has no counter or bound of
  its own on how many such cycles it will run before giving up.
steps: registered a workspace-index entry with events/log paths but no
  roster entry (`_roster_load` monkeypatched to `{}`, simulating a spawn
  that crashed before `roster_register()`); drove 5 iterations of the same
  before/after-offset + session-end-scan + dead-pid check the real
  `_watch(follow=True)` loop performs, and counted how many reached a
  terminal branch.
expected: either a diagnostic distinguishing "still waiting on an entry
  that may never appear" from ordinary polling, or a bound (retry cap,
  overall timeout) after which the loop gives up and returns non-zero.
actual: the loop has periodic per-cycle stall messages (not silent at the
  cycle level) but no bound across cycles — a workspace-index entry with
  no matching roster entry (a spawn that crashed before registering) makes
  `spawn.py watch --follow` re-poll forever with no terminal state ever
  reachable.
---

---
requirement: `_watch(follow=True)` must eventually terminate (or clearly
  signal indefinite-wait) when the roster entry it needs to detect a crash
  never appears.
verdict: Incorrect
evidence: spawn.py:2199-2235 (`while True:` with no cycle counter or
  outer bound); test/test_silent_failure_repros.py::test_attempt_2_follow_loop_unbounded_on_absent_roster_entry
rationale: reproduced with evidence; the failure mode is a hang, not data
  loss or a security exposure, and each cycle does print a stall
  diagnostic to stderr (so it is not fully silent) — the gap is only the
  missing outer bound. Chromium-scale Low/Medium: availability annoyance,
  no privilege or data impact, operator can Ctrl-C and re-run non-`--follow`.
addressed_to: coding
severity: advisory
---

---
attempt: proposal item 3 — `require_doctor()` re-probe under version drift
  is a live paid session with no confirmation (spawn.py:2405-2431)
outcome: not-reproduced
evidence: test/test_silent_failure_repros.py::test_attempt_3_doctor_reprobe_prints_pre_charge_notice
  — driving `require_doctor(version=None)` with a version mismatch
  (stored `runs/doctor-ok` = "1.0.0", `_claude_version()` mocked to
  "2.0.0") confirms `doctor()` is invoked, and confirms a stderr notice
  is printed *before* that invocation: `"[doctor] CLI 2.0.0 는 아직 실측
  전이다 — 훅 발화 프로브를 먼저 돌린다 (실 세션 1회, 소액 과금)"` —
  containing both "실 세션 1회" (one real session) and "소액 과금" (small
  charge).
steps: monkeypatched `spawn.doctor` to a stub and `spawn._claude_version`
  to return a version differing from a pre-seeded `runs/doctor-ok`; called
  `require_doctor(version=None)` (the auto-detect path — the explicit-
  version path, e.g. for tests, instead halts and tells the caller to run
  `spawn.py doctor` manually rather than probing); captured stderr.
expected (per attempt's claim): a silent live-billed probe indistinguishable
  from a routine spawn, no pre-charge notice.
actual: a distinguishable stderr notice naming the cost and the fact a
  real session is about to launch is printed immediately before the
  probe.
---

---
attempt: proposal item 4 — `gates/issue_bundling.py`'s workflow may be
  advisory-only / silently decorative enforcement
outcome: not-reproduced
evidence: test/test_silent_failure_repros.py::test_attempt_4_bundling_gate_is_documented_comment_only
  — `.github/workflows/issue-bundling-gate.yml`'s header comment states
  plainly: GitHub Actions cannot block issue creation itself (only PR
  merges); posting an issue comment is "이 이슈 생성 자체를 막을 수 없다
  ... issues:opened 이벤트에 대해 가능한 가장 가까운 집행 지점" (the
  closest enforcement point available for that event); and that branch-
  protection required-check registration "해당 없다" (does not apply)
  because there is no PR to block at that trigger.
steps: read `.github/workflows/issue-bundling-gate.yml` in full and
  `gates/issue_bundling.py`'s module docstring; checked whether the
  comment-only behavior observed on issue #445 itself is undocumented
  (a hidden gap) or stated as the intentional, GitHub-Actions-imposed
  scope of this specific trigger.
expected (per attempt's claim): comment-only enforcement rendering as a
  "gate" while silently being advisory in effect, undocumented.
actual: the comment-only behavior is explicitly documented in the
  workflow's own header as the maximum enforcement GitHub Actions permits
  for an `issues: opened` trigger — not a silent gap, a stated design
  boundary specific to this trigger (the same repo's PR-time gates, e.g.
  `plan-aware-closes-gate.yml`, do block merges — out of this issue's
  scope per the proposal).
---

## Summary

4 attempts, all from the approved proposal's attempt list, all with
recorded outcomes:

- 2 `reproduced` (proposal items 1, 2) — both filed as findings addressed
  to coding, both `severity: advisory` per the deterministic Chromium-band
  lookup (neither reaches Critical/High: item 1 needs a rare filesystem
  failure plus a follow-on `git add -A` to matter; item 2 is an
  availability hang with a recoverable operator path, not data loss or a
  privilege/data exposure on its own).
- 2 `not-reproduced` (proposal items 3, 4) — both attempts' claimed gap
  turned out to already have a mitigation in the code (item 3: an explicit
  pre-charge stderr notice) or the codebase's own documentation (item 4:
  the workflow states its comment-only scope is a GitHub Actions
  constraint, not an oversight).

No attempt was `blocked: needs-repro-access` — all four were reproducible
from the current tree with no external runtime dependency.
