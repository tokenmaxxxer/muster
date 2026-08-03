---
subject: issue-235
role: execution-observation
observed_role: implementation
observed_pr: 237
code_under_review: 611c0c0
loop_state: phase-2-complete
closed_checks:
  - name: regression-discrimination-static-derivation
    code_sha: 611c0c0
  - name: denials-gate-property-trace
    code_sha: 611c0c0
  - name: coverage-delta-sweep
    code_sha: 611c0c0
  - name: dedup-masking-trace
    code_sha: 611c0c0
  - name: prescription-coverage-map
    code_sha: 611c0c0
---

# Execution-observation record — issue #235, PR #237 (`implementation` role)

Phase 2, opened by the issue-level comment whose entire body is `APPROVE
issue-235/execution-observation`, author `jjongkwann` (MEMBER, listed in
`docs/specs/approvers.md:2`), posted 2026-08-03T06:49:29Z
(https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5163202429)
— single-account mode per role-handoff contract v3 s19, this branch's PR
being #239 authored by the same account. Nothing above this line is a
verdict; the Independence statement below precedes all verdict language
in this document.

## Independence

This role did not author, edit, or execute the observed artifact — not in
this session and not on this branch. PR #237's three commits (`bf5f71f`,
`611c0c0`, `e7a13db`) are the `implementation` role's; nothing under
`spawn.py`, `test_spawn.py`,
`docs/issue-235/proposals/refusal-classifier-corroboration.md`, or
`docs/issue-235/reports/implementation*` was written or edited by this
session, in either phase. No test suite was run, `spawn.py` was never
invoked, and no part of the observed role's task was re-executed: the
admissible evidence is the commits' diff text, the pre-change blobs those
diffs landed on, the observed role's own record, the issue and its
comments, the PR metadata, and externally-owned files read directly.
Every code citation below addresses a blob through its SHA — no
working-tree path is cited as evidence of what the observed role did.
Findings return only through this record on this role's own PR; this role
files no issue and proposes no fix.

## What was done

Rendered the three verdict levels declared in
`docs/issue-235/proposals/execution-observation-plan.md:19-36` — outcome,
trajectory, step — against exactly the evidence that plan named, and ran
the five checks it fixed at
`docs/issue-235/proposals/execution-observation-plan.md:118-157`. The
invoking prompt's three judgment items are each answered by a named
check: (a) the four regression cases' pre-change failure →
`regression-discrimination-static-derivation`; (b) the
`permission_denials` gate's two-way guarantee →
`denials-gate-property-trace`; (c) the gap versus the local four-point
prescription, specifically the session-end-fallback wholesale-suppression
input and the per-layer-once dedup masking input → `coverage-delta-sweep`
+ `dedup-masking-trace` + `prescription-coverage-map`. Four findings are
recorded below in the blameless four-part shape. Nothing was fixed.

## Why

The upstream basis is issue #235's `## 실행 계획` step 2
(`execution-observation`) and the invoking prompt for this session, which
fixes the three judgment items above and the disposition: judge, do not
fix. This record is the sole phase-2 artifact for that step. The
observed role's own claims — in particular
`e7a13db:docs/issue-235/reports/implementation.md:151-161`, which reports
all four regression cases failing pre-fix — are checked here by
independent derivation on the blobs rather than relayed, because relaying
would make this verdict a restatement of the claim it exists to test
(`docs/issue-235/proposals/execution-observation-plan.md:95-99`).

## What was read this session

- `gh issue view 235` (body in full: 배경, 결함 1·2, 요구사항 1-5, 참고,
  실행 계획) and all three issue comments via
  `gh api repos/tokenmaxxxer/on-the-record/issues/235/comments`.
- `git show 611c0c0 -- spawn.py` and `git show 611c0c0 -- test_spawn.py`
  — the full phase-2 diff, including its commit message.
- `git show 611c0c0:spawn.py` (regions 1486-1545 and 2615-2710) and
  `git show bf5f71f:spawn.py` (regions 1488-1545 and 2618-2695) — the
  post-change and pre-change blobs, line numbers re-derived this session.
- `git show 611c0c0:test_spawn.py` lines 1185-1230 (`EventReporting._run`)
  and the four added cases as they appear in the diff.
- `e7a13db:docs/issue-235/reports/implementation.md` — the observed
  role's own record, in full.
- `bf5f71f:docs/issue-235/proposals/refusal-classifier-corroboration.md`
  (Request, Constraints, Rationale, What will be done 1-4) and
  `bf5f71f:docs/issue-235/reports/implementation/survey.md:9-15` (Scout
  skip record).
- `git show --stat` for `bf5f71f`, `611c0c0`, `e7a13db`; author dates for
  all three.
- `gh pr view 237 --json ...` (author, reviews, mergedAt, mergeCommit,
  headRefName) and its body; `gh pr list --state all`.
- `docs/specs/approvers.md`; `d2ae7c0:docs/issue-232/reports/execution-observation.md`
  (head) as the prior record of this role for the same classifier.
- `git grep -n -I -E "153.?(fixture|개)|unconditional.*fallback|무조건.*폴백" d187559 -- docs`
  — no match, re-verified this session.

## Verdict 1 — outcome: the PR landed what issue #235 asked, with two residual shapes it did not close

**요구사항 1 (corroborate against `permission_denials`) — met.**
`611c0c0:spawn.py:2629` adds `pending_refusals: dict = {}`; the
`type == "user"` branch no longer emits, it buffers
(`611c0c0:spawn.py:2700-2701`, `if key not in pending_refusals:
pending_refusals[key] = (ev_type, detail)`, with no `_append_event` call
anywhere in that branch); emission moved into the terminal-`result`
branch under `if issue is not None and denials:`
(`611c0c0:spawn.py:2672`, flush loop `:2675-2679`). The requirement's own
wording allows "corroborate … 하거나, 동등한 안전장치를 둘 것", and this
is a corroboration. It is **session-scoped**: `611c0c0:spawn.py:2672`
tests only the truthiness of `denials`, and no line in `:2669-2688` maps
an entry of `denials` to a key in `pending_refusals`, so one genuine
denial licenses every buffered candidate. The observed role names the
same limit itself at
`e7a13db:docs/issue-235/reports/implementation.md:116-129` and correctly
ties closing it to issue #235's own constraint 5 (no new instrumentation).

**요구사항 2 (anchor `_GATE_HOOK_RE`) — met.**
`611c0c0:spawn.py:1491` is
`re.compile(r"^PreToolUse:\S+ hook error: \[([^\]]*)\]")` against
`bf5f71f:spawn.py:1491`'s unanchored form; the call site is unchanged
`.search(text)` at `611c0c0:spawn.py:1527`, and no `re.MULTILINE` flag is
present, so `^` binds to text index 0 only. The requirement's "앵커만으로
부족하면 … 보강" clause is answered by 요구사항 1's gate.

**요구사항 3 (`detail.gate` prefers the hook stem) — met.**
`611c0c0:spawn.py:1529` computes `gate = Path(hook_m.group(1)).stem`
unconditionally before `deny_m` is even evaluated (`:1530`), and the deny
token now only chooses where the reason text starts (`:1531-1532`) —
against `bf5f71f:spawn.py:1528-1533`, where `deny_m.group(1)` won and the
stem was the fallback.

**요구사항 4 (four regression cases failing pre-change) — met, derived
independently.** All four cases exist at
`611c0c0:test_spawn.py:1342-1415` and each is statically forced to
diverge on `bf5f71f:spawn.py`; the per-case derivation is Verdict 3(a).

**요구사항 5 (constraints from #232 preserved) — met.**
`_HARNESS_REFUSAL_PATTERNS` and `_SANDBOX_REFUSAL_PATTERNS` are
byte-identical between `bf5f71f:spawn.py:1493-1502` and
`611c0c0:spawn.py:1493-1502`, and `_GATE_DENY_RE` is identical at
`:1492` in both — no pattern was added or widened. `git show 611c0c0 --
spawn.py` contains exactly three hunks (the regex line,
`_classify_refusal_text`, the two refusal branches of `_spawn_one`); no
new log line, CLI flag, or hook output appears, and nothing in
`_await_bounded` or the `watch` cadence is touched.

## Verdict 2 — trajectory: sound, with one recorded deviation at the PR-body level

**Phase 1 confined itself to the two phase-1 homes.** `bf5f71f`
(authored 2026-08-03 14:46:02 +0900 = 05:46:02Z) changed exactly two
paths — `docs/issue-235/proposals/refusal-classifier-corroboration.md`
(+214) and `docs/issue-235/reports/implementation/survey.md` (+257) — and
no code file, per `git show --stat bf5f71f`.

**Approval was real, human, and correctly-shaped.** The issue comment
whose entire body is `APPROVE issue-235/implementation` was posted by
`jjongkwann` (MEMBER, listed at `docs/specs/approvers.md:2`) at
2026-08-03T05:52:52Z
(https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162801451).
PR #237's `reviews` array is empty and its author is `jjongkwann`
(`gh pr view 237 --json author,reviews`), so single-account mode applies
and the issue-comment path is the correct one under contract v3 s19.

**Phase 2 began after approval.** `611c0c0` is authored 2026-08-03
15:03:13 +0900 = 06:03:13Z, ten minutes after the approval comment;
`e7a13db` (the record) 06:12:37Z; PR #237 merged 06:15:33Z as `d187559`.
The ordering approval → code → record → merge holds.

**Scouting was skipped with a recorded reason, as the directive
requires.** `bf5f71f:docs/issue-235/reports/implementation/survey.md:9-15`
carries a `## Scout skip record` naming the pure-bugfix condition and the
prescribing record (`docs/issue-232/reports/execution-observation.md`
Findings 1·2) — one of the two admissible skip conditions, recorded rather
than silently taken.

**Deviation.** PR #237's body carries `Closes #235`
(`gh pr view 237 --json body`, line 31), so merging it auto-closed the
issue while its own `## 실행 계획` step 2 (`execution-observation`) was
unrun — the human recorded this at 06:16:21Z
(https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162962921)
and attributed the missed guard to a phase-1-created workspace being
checked by a stale pre-merge gate (#221), not to a judgment the role made.
Carried as Finding 4 below rather than as an outcome failure, because the
delivered work itself is unaffected.

## Verdict 3 — step: which artifact, if any, is deficient

### (a) Do the four regression cases fail against the pre-change blob? — yes, all four

Derived from `611c0c0:test_spawn.py` against `bf5f71f:spawn.py`, one case
at a time. Shared harness: `EventReporting._run`
(`611c0c0:test_spawn.py:1187-1230`) calls `spawn._spawn_one(..., "execution-observation",
task, unattended=True, issue=7)` at `:1223`, so `issue is not None` holds
on every path, and each fixture streams its `tool_result` line **before**
the terminal `result` line.

- **(i)** `611c0c0:test_spawn.py:1342-1359`. The marker sits mid-text,
  after `"...requires approval: "` (`:1348-1351`). On the pre-change blob
  `_GATE_HOOK_RE.search(text)` (`bf5f71f:spawn.py:1525`) matches anyway;
  `deny_m` matches `some-gate: refused —` so `gate = "some-gate"`
  (`:1529`); the function returns `gate-refusal` at `:1534`, making the
  `requires approval` harness pattern at `:1535-1537` unreachable, and
  `bf5f71f:spawn.py:2690` appends it. Both asserts diverge:
  `assertTrue(harness-refusal)` (`611c0c0:test_spawn.py:1358`) and
  `assertFalse(gate-refusal)` (`:1359`).
- **(ii)** `611c0c0:test_spawn.py:1361-1377`. Text begins with the
  marker and `permission_denials` is `[]` (`:1371`). The pre-change
  `type == "user"` branch appends `gate-refusal` at
  `bf5f71f:spawn.py:2690` without ever reading `denials` — the two
  branches are `elif` siblings on `obj.get("type")`
  (`bf5f71f:spawn.py:2664`, `:2676`). The assert that no refusal event of
  any of the four types exists (`611c0c0:test_spawn.py:1374-1377`)
  diverges.
- **(iii)** `611c0c0:test_spawn.py:1379-1396`. The spurious text names
  `some-other-gate`, the real denial on the terminal line names tool
  `Write` (`:1385-1392`). Pre-change, the spurious text classifies and
  populates `refusals_seen` at `bf5f71f:spawn.py:2689`, which falsifies
  `not refusals_seen` at `:2667`, so no `unclassified-refusal` is
  appended. Both asserts diverge (`611c0c0:test_spawn.py:1395,1396`).
- **(iv)** `611c0c0:test_spawn.py:1398-1415`. `_GATE_DENY_RE` matches
  `execution-observation: refused —`, so `gate = "execution-observation"`
  at `bf5f71f:spawn.py:1529` and the stem branch at `:1532` is not taken.
  The assert `detail["gate"] == "record-fields-gate"`
  (`611c0c0:test_spawn.py:1415`) diverges.

One paired assertion does **not** discriminate:
`611c0c0:test_spawn.py:1414` (`assertEqual(len(refusals), 1)`) holds on
`bf5f71f:spawn.py` too — the single user line appends exactly one event
(`:2690`) and the result branch is then blocked by `not refusals_seen`
(`:2667`). Only `:1415` separates the blobs for case (iv). No other
assertion among the four was found to hold on the pre-change blob, so the
observed role's claim at
`e7a13db:docs/issue-235/reports/implementation.md:151-161` is confirmed
by independent derivation, not merely relayed.

### (b) Does the `permission_denials` gate carry both directions? — P1 yes, in general; P2 only for layer 1

**P1 — a zero-denials session emits nothing: holds structurally.**
`611c0c0:spawn.py:2671` reduces any empty/absent/falsy value to `[]` via
`.get("permission_denials") or []`, so `:2672` is false; `pending_refusals`
is read nowhere but inside that guard (`:2675`), and the
`unclassified-refusal` fallback (`:2680-2688`) is **nested inside** the
same guard. The emitted set is therefore empty for any number and kind of
buffered candidates — this is a property of the control flow, not of the
one fixture at `611c0c0:test_spawn.py:1361-1377`.

**P2 — a spurious match must not suppress a genuine fallback: holds only
for the gate layer.** `611c0c0:spawn.py:2680` gates the fallback on
`if not refusals_seen:`, and `refusals_seen` is populated at `:2678` by
the flush loop in the same pass — so **whenever any buffered candidate
flushes, the fallback does not fire**, structurally the same suppression
as pre-change `denials and not refusals_seen` (`bf5f71f:spawn.py:2667`).
What the `^` anchor at `611c0c0:spawn.py:1491` removed is the *layer-1*
route into that state. `_HARNESS_REFUSAL_PATTERNS`
(`611c0c0:spawn.py:1493-1498`) and `_SANDBOX_REFUSAL_PATTERNS`
(`:1499-1502`) are still applied with unanchored `.search()` at `:1534`
and `:1537`, so the compounding remains reachable one layer over — see
Finding 1. The fixture that is supposed to pin this property,
`611c0c0:test_spawn.py:1379-1396`, does not exercise it post-change: its
spurious text matches no harness or sandbox pattern either, so
`_classify_refusal_text` returns `None` (`611c0c0:spawn.py:1540`) and no
candidate is ever buffered. The test passes for the anchor, not for the
suppression property.

### (c) What is missing relative to the local four-point prescription?

`prescription-coverage-map` ran as the second branch the plan anticipated
(`docs/issue-235/proposals/execution-observation-plan.md:150-157`). No
admissible in-repo source carries a four-point prescription of the shape
"anchor / keep the fallback unconditional / dedup safety / 153-fixture
corpus": `git grep -n -I -E "153.?(fixture|개)|unconditional.*fallback|무조건.*폴백" d187559 -- docs`
returns nothing, and the only in-repo text describing the local
adversarial experiment is
`bf5f71f:docs/issue-235/proposals/refusal-classifier-corroboration.md:19-38`,
whose enumeration is **three** points. Those three map cleanly onto the
delivery: point 1 → `611c0c0:spawn.py:2629` + `:2669-2701`; point 2 →
`:1491`; point 3 → `:1529`. The other three labels are therefore not used
here as a citable external standard; their substance is answered from the
blobs instead, per the plan, and both inputs the invoking prompt named do
exist:

- **Session-end fallback suppressed wholesale.** Because both the flush
  and the fallback are nested under `611c0c0:spawn.py:2672`, three input
  shapes make post-change reporting narrower than
  `bf5f71f:spawn.py:2690`: **S1** the terminal `result` line never
  arrives (crash/kill/truncation) — the loop ends at EOF and
  `pending_refusals` dies with the frame, while `session-end` is still
  written at `611c0c0:spawn.py:2824`; **S2** the terminal line arrives
  but `permission_denials` is absent or falsy-non-list, collapsed to `[]`
  by `or []` at `:2671`; **S3** the terminal line is malformed JSON,
  skipped by the `except ValueError: continue` at `:2665-2666`. S1 is the
  shape the observed role names itself
  (`e7a13db:docs/issue-235/reports/implementation.md:94-115`, Hunt
  finding 1, left open for a follow-up issue); S2 and S3 are not named in
  that record — see Finding 2. S2 is *intended* behaviour when the
  session genuinely had no denial (it is what case (ii) asserts); it
  becomes a loss only when a denial did occur and the harness reported it
  without a well-formed list, and nothing in `:2671-2672` distinguishes
  those two situations. Note also that no `isinstance` check guards
  `denials`: a truthy non-list (e.g. a string) passes `:2672` and drives
  the whole flush, with `str(denials)[:200]` at `:2688` absorbing any
  type.
- **Per-layer once-only dedup masking a genuine event.** The key space is
  `("gate", stem)` (`611c0c0:spawn.py:1533`), `("harness",)` (`:1536`),
  `("sandbox",)` (`:1539`) — layer-wide for layers 2 and 3 — and the
  buffer write is first-wins (`:2700`). Two `is_error` texts in one
  session that key the same layer collapse to one emission carrying the
  **first** text's detail; if the first is spurious, the genuine one's
  detail is discarded at `:2700` before the flush ever runs. See
  Finding 3. This granularity is carried over unchanged from
  `bf5f71f:spawn.py:2624,2687-2689`, not introduced by `611c0c0`.

**Not a coverage delta:** a genuine gate denial whose marker is not at
index 0 fails `^` at `611c0c0:spawn.py:1491`, and if no layer-2/3 pattern
matches, `_classify_refusal_text` returns `None` (`:1540`) — at flush,
`denials` is non-empty and `refusals_seen` empty, so `:2680-2688` emits
`unclassified-refusal`. The event is downgraded, not lost. No shape was
found in which `bf5f71f:spawn.py` emits nothing and `611c0c0:spawn.py`
emits something.

**Step-level conclusion:** no artifact of PR #237 is deficient against
what issue #235 asked. The deficiencies below are (1) one fixture that
does not pin the property its requirement names, (2)(3) two residual
input classes the observed record does not name, and (4) one PR-body
deviation — none of which reverse the outcome verdict.

## Open findings

### Finding 1 — case (iii)'s fixture pins the anchor, not the non-suppression property it is named for

- **Impact.** 요구사항 4(iii) exists to lock the compounding failure mode
  (a fake match consuming the `unclassified-refusal` fallback owed to a
  genuine denial). `611c0c0:test_spawn.py:1379-1396` cannot lock it: under
  the anchored pattern its spurious text classifies to `None`
  (`611c0c0:spawn.py:1540`), so nothing is buffered and the fallback path
  is reached trivially. The mode itself survives one layer over — an
  `is_error` text that merely quotes `requires approval` (for instance the
  very text at `611c0c0:test_spawn.py:1348-1351`) buffers a `("harness",)`
  candidate at `:2700`; if the session's genuine denial fails to classify,
  the flush at `:2679` emits that candidate, `refusals_seen` becomes
  non-empty, and the fallback at `:2680` does not fire. The genuine
  denial then gets a wrong-layer label and no fallback — the two failure
  modes issue #235's 결함 1 describes as "합성된다", still composed.
- **Timeline.** Named as a required case in issue #235 요구사항 4(iii);
  restated in the proposal at
  `bf5f71f:docs/issue-235/proposals/refusal-classifier-corroboration.md:156-159`;
  delivered as a fixture at `611c0c0:test_spawn.py:1379-1396`; reported
  as passing at `e7a13db:docs/issue-235/reports/implementation.md:151-161`.
- **Root cause.** The fixture reuses a gate-marker text for the spurious
  side, so the anchor added in the same commit (`611c0c0:spawn.py:1491`)
  removes the input before it can reach the state the case is about. The
  fix's two mechanisms — anchoring and the denials gate — overlap on this
  one input, and only the cheaper one is exercised.
- **Action item (for the human to judge).** A companion case whose
  spurious text matches an unanchored layer-2/3 pattern rather than the
  gate marker would pin the property. Blocked at the source, not just at
  the fixture: closing the behaviour needs either per-candidate
  correlation or an anchored layer-2/3 form, both of which touch issue
  #235's constraint 5 boundary. This role does not fix and files no
  issue.

### Finding 2 — the record names one of three inputs that lose reporting relative to pre-change

- **Impact.** `e7a13db:docs/issue-235/reports/implementation.md:94-115`
  documents S1 (crash before the terminal `result` line) and flags it for
  a follow-up issue. S2 (terminal line present, `permission_denials`
  absent/falsy/non-list) and S3 (terminal line malformed JSON) produce
  the identical outcome through `611c0c0:spawn.py:2671` and `:2665-2666`
  respectively, and are not named anywhere in that record, so a reader
  taking "Open findings" as the delivery's full residual set
  under-estimates the class by two shapes.
- **Timeline.** Introduced by `611c0c0` moving emission from
  `bf5f71f:spawn.py:2690` into the guarded flush at
  `611c0c0:spawn.py:2672-2688`; recorded partially at `e7a13db`.
- **Root cause.** The record reasons about the *stream ending early*
  case, which the adversarial hunt surfaced, but not about the terminal
  line arriving in an unexpected shape — `611c0c0:spawn.py:2671`'s
  `or []` and the absent `isinstance` check make three distinct
  harness-side anomalies indistinguishable from "no denial happened".
- **Action item (for the human to judge).** If the follow-up issue Hunt
  finding 1 proposes is filed, S2/S3 belong in its scope statement, and
  the `isinstance` question on `denials` at `611c0c0:spawn.py:2671-2672`
  belongs with them. This role files no issue.

### Finding 3 — a spurious candidate can mask a genuine same-layer event, and no fixture or record entry covers it

- **Impact.** `611c0c0:spawn.py:2700` is first-write-wins over a key space
  that is layer-wide for layers 2 and 3 (`:1536`, `:1539`) and
  stem-scoped for layer 1 (`:1533`). Two `is_error` texts keying the same
  layer in one session yield exactly one event, carrying the earlier
  text's detail; the later one is discarded before the flush. When the
  earlier is textually coincidental and the later is the real denial, the
  emitted event describes the wrong thing while the layer count still
  reads "one refusal seen". `Path(hook_m.group(1)).stem` at `:1529`
  additionally discards the directory, so two hook scripts sharing a
  filename stem collapse to one key.
- **Timeline.** Key space and first-wins ordering carried from
  `a670098` through `bf5f71f:spawn.py:2624,2687-2689`; restated in the new
  shape at `611c0c0:spawn.py:2623,2676-2678,2700`. The observed record's
  Hunt finding 2 (`e7a13db:docs/issue-235/reports/implementation.md:116-129`)
  names the adjacent shape — two candidates both firing — but not the one
  where one masks the other.
- **Root cause.** Not a regression: `611c0c0` moved the dedup check from
  emit-time to buffer-time without changing its granularity, so the
  masking property was inherited rather than introduced. It surfaces here
  because 요구사항 1's "동등한 안전장치" invites the question and no check
  in the delivery answers it.
- **Action item (for the human to judge).** Whether per-layer once-only
  dedup is still the intended contract now that emission is deferred —
  the "보고 한 번, 거부마다 아님" intent recorded at
  `611c0c0:spawn.py:2619-2622` predates buffering. This role does not fix.

### Finding 4 — PR #237's body closed the issue with the plan's step 2 unrun

- **Impact.** `Closes #235` in PR #237's body (`gh pr view 237 --json
  body`, line 31) auto-closed issue #235 on merge (`d187559`,
  2026-08-03T06:15:33Z) while its `## 실행 계획` step 2
  (`execution-observation`) had not run — the human reopened it 48
  seconds later and recorded it as the 8th occurrence
  (https://github.com/tokenmaxxxer/on-the-record/issues/235#issuecomment-5162962921).
- **Timeline.** Body authored with the PR during phase 1/2 of the
  observed role; merge 06:15:33Z; reopen comment 06:16:21Z.
- **Root cause.** Per the human's own note, the plan-aware gate that
  would have caught this had landed on `main`, but the observed session's
  workspace was created in phase 1 and reused, so the pre-merge check ran
  against a stale copy — the failure mode issue #221 describes. The
  role's judgment is not the proximate cause.
- **Action item (for the human to judge).** Already tracked: the reopen
  comment states the issue stays open until the plan is exhausted, and
  #221 covers the reused-workspace staleness. Recorded here only so this
  observation's trajectory verdict accounts for it. This role files no
  issue.

## What this record does not establish

- That the four regression cases pass on `611c0c0` — this role may not
  run the suite. The claim at
  `e7a13db:docs/issue-235/reports/implementation.md:145-161` (170 passed)
  is reported, not verified; what is verified here is the pre-change
  divergence of each case, derived from the two blobs.
- That the shapes in Findings 1-3 have ever occurred in a live session.
  They are derived from the control flow of `611c0c0:spawn.py`; no
  observed sample is cited for any of them, and Finding 3's colliding-stem
  variant in particular is structural only.
- That S1-S3 exhaust the coverage delta. They are the shapes reachable
  through `611c0c0:spawn.py:2665-2672`; the sweep found no fourth, which
  is not the same as proving none exists.
- Anything about issue #232 / PR #233 beyond context. `a670098` is the
  baseline this fix landed on, read as context, not re-reviewed.

## Next steps

None for this role. The record is the deliverable; the human judges the
four findings on this PR and files whatever issues they warrant —
Findings 1 and 2 both point at the same follow-up the observed role
already proposed at
`e7a13db:docs/issue-235/reports/implementation.md:163-171`, and would be
naturally scoped into it.

## Open-finding resolution path

All four findings are reported for human judgment on PR #239 and require
no action by this role. None blocks the acceptance of PR #237, which is
already merged (`d187559`); none is a fix this role is permitted to make.
Findings 1-3 resolve, if the human so decides, inside the follow-up issue
Hunt finding 1 already nominates; Finding 4 is already tracked by the
reopen comment and issue #221.
