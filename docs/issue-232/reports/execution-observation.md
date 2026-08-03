---
subject: issue-232
role: execution-observation
observed_role: implementation
observed_pr: 233
code_under_review: a670098
loop_state: phase-2-complete
closed_checks:
  - name: fixture-discrimination-static-derivation
    code_sha: a670098
  - name: pattern-provenance-trace
    code_sha: a670098
  - name: dedup-contract-trace
    code_sha: a670098
  - name: watch-cycle-invariance
    code_sha: a670098
---

# Execution-observation record — issue #232, PR #233 (`implementation` role)

Phase 2, opened by the issue-level comment whose entire body is `APPROVE
issue-232/execution-observation`, author `jjongkwann` (MEMBER, listed in
`docs/specs/approvers.md`), posted 2026-08-03T04:58:51Z
(https://github.com/tokenmaxxxer/on-the-record/issues/232#issuecomment-5162467587)
— single-account mode per role-handoff contract v3 s19, this branch's PR
being #234 authored by the same account.

## Independence

This role did not author, edit, or execute the observed artifact — not in
this session and not on this branch. PR #233's three commits (`2dc6ba6`,
`a670098`, `af92fce`) are the `implementation` role's; nothing under
`spawn.py`, `test_spawn.py`, `docs/issue-232/proposals/implementation.md`,
`docs/issue-232/reports/implementation*`, or
`docs/issue-232/decisions/event-layer-taxonomy.md` was written or edited by
this session. No test suite was run, no `spawn.py` invoked, and no part of
the observed role's task was re-executed: the admissible evidence is the
commits' diff text, the pre-change blobs those diffs landed on, the observed
role's own record, the issue and its comments, and externally-owned files
read directly. Findings return only through this record on this role's own
PR; this role files no issue and proposes no fix.

## What was done

Rendered the three verdict levels declared in
`docs/issue-232/proposals/execution-observation-plan.md:34-113` — outcome,
trajectory, step — against the evidence that plan named, plus the four
judgment items (a)-(d) the invoking prompt fixed. Three findings are
recorded below in the blameless four-part shape. Nothing was fixed.

## Why

The upstream basis is issue #232's `## 실행 계획` step 2 and the invoking
prompt for this session, which names the four judgment items — (a) fixture
strength against the pre-change code, (b) pattern provenance including the
gate marker quoted inside another layer's message body, (c) the dedup
contract, (d) `watch` cycle invariance — and instructs that the observed
role's own claims be checked rather than relayed, and that nothing be
fixed. This record is the sole phase-2 artifact for that step.

## What was read this session

- `gh issue view 232` (body), `gh api .../issues/232/comments` — 요구사항 1-4,
  the two 제약, and all three comments with author, association, timestamp,
  and URL.
- `gh pr view 233` (body), `gh pr view 233 --json commits,mergedAt,mergeCommit,files,reviews`
  — merged 2026-08-03T04:48:59Z as `70f867f`, `reviews: []`, six-file change
  set.
- `git show a670098 -- spawn.py`, `git show a670098 -- test_spawn.py` — the
  phase-2 delivery diff in full.
- `git show 2dc6ba6 --stat`, `git show a670098 --stat`, `git show af92fce --stat`,
  `git log --format='%H %aI %s'` — write sets and authored timestamps.
- `git show 2dc6ba6:spawn.py` at `2580-2625` (the pre-change per-line loop)
  and `1665-1755` (`_await_bounded`, `_watch`) — the baseline the delivery
  landed on.
- `git show 2dc6ba6:test_spawn.py` at `1180-1265` — `EventReporting._run`,
  the harness the new fixtures are driven through, and the pre-change
  `test_real_denial_still_reported`.
- `docs/issue-232/reports/implementation.md` (171 lines),
  `docs/issue-232/proposals/implementation.md` (169 lines),
  `docs/issue-232/decisions/event-layer-taxonomy.md` (78 lines), and
  `git show 2dc6ba6:docs/issue-232/reports/implementation/survey.md` at
  `1-30` and `86-150`.
- `.../tokenmaxxxer-core/core/hooks/lib/gate-lib.sh:70-84` — `gate_deny`'s
  documented signature and literal output, read directly this session.
- `docs/specs/approvers.md`.

## Verdict 1 — outcome

**Met, with one requirement met only in form and one new defect of the same
class as the filed one.** The issue's central defect — every tool refusal
labeled `gate-refusal` — is fixed for the inputs the issue cites.

- **요구사항 1 (three-way layer split): met.** `a670098`'s `spawn.py` hunk
  `@@ -2559,7 +2617,11 @@` emits four distinct type strings selected by
  `_classify_refusal_text` (same commit, hunk `@@ -1482,6 +1482,64 @@`):
  `gate-refusal`, `harness-refusal`, `sandbox-refusal`, and
  `unclassified-refusal`; the taxonomy is recorded at
  `docs/issue-232/decisions/event-layer-taxonomy.md:15-30`. The label itself,
  not a nested field, now carries the layer — which is what the issue's
  measured incident required.
- **요구사항 2 (which gate, plus reason): met in form, defective in
  identity.** `_classify_refusal_text`'s layer-1 return in `a670098`'s
  `spawn.py` replaces the baseline's `str(denials)[:200]`
  (`2dc6ba6:spawn.py:2607`) with `{"gate": ..., "reason": ...}`, so gate
  identity and reason do reach the event. But the extraction prefers
  `_GATE_DENY_RE`'s `(\S+):\s*refused\s*—` token over the hook-path stem,
  and `gate_deny`'s first parameter is documented as `<role-or-gate-name>`
  (`gate-lib.sh:75`, read directly this session) — so for a gate that passes
  the role name the event reports the role, not the gate. See finding 2.
- **요구사항 3 (reuse existing log evidence, no new instrumentation): met.**
  `git show a670098 --stat` shows `spawn.py`, `test_spawn.py`, and one
  decision record only; the new branch is an `elif` over the `obj` the loop
  already `json.loads`-ed (`2dc6ba6:spawn.py:2599`), adding no log line, CLI
  flag, or hook. The evidence-sufficiency check that licenses this is the
  observed role's own survey, §"Where the classification evidence actually
  lives (requirement 3)" and §"Preserved-log check"
  (`2dc6ba6:docs/issue-232/reports/implementation/survey.md:89-150`), which
  searched for preserved session logs, found none on the machine, and
  concluded the issue's own cited strings suffice.
- **요구사항 4 (per-layer regression fixtures): met.** `a670098`'s
  `test_spawn.py` adds one fixture case per layer, built verbatim from the
  issue's cited strings, plus an `is_error` guard case and an
  `unclassified-refusal` case; their discriminating power against the
  pre-change code is derived independently in (a) below.
- **제약 1 (`watch` block-then-report cycle untouched): honored** — see (d).
- **제약 2 (layer-2/3 policy out of scope): honored.** `git show a670098 --stat`
  writes nothing that changes when the harness or the sandbox refuses; the
  change is confined to how a refusal is labeled in `.events.jsonl`.

Against that, the delivered classifier opens a path on which a refusal from
layer 2 — or no refusal at all — is reported as `gate-refusal` with a gate
name attached (finding 1, evidence in (b)). That is the same wrong-label
class the issue exists to end, narrower in reach than the pre-change bug but
newly capable of firing where the pre-change code emitted nothing.

## Verdict 2 — trajectory

**Sound.** Every gate contract v3 s19 imposes on the phase-1 → phase-2 path
is satisfied by the artifacts, in the required order.

- **Phase 1 preceded any code.** `git show 2dc6ba6 --stat` is exactly
  `docs/issue-232/proposals/implementation.md` (+169) and
  `docs/issue-232/reports/implementation/survey.md` (+196), 365 insertions,
  zero lines of code, authored 2026-08-03T12:34:36+09:00.
- **Survey preceded and fed the proposal.** The proposal's Alternative-2
  rejection rests on the survey's requirement-3 finding and cites it
  (`docs/issue-232/proposals/implementation.md:82-94` against
  `2dc6ba6:docs/issue-232/reports/implementation/survey.md:89-150`); the
  proposal's `_await_bounded` constraint (`:39-41`) restates the survey's
  reading of the same span. The dependence runs survey → proposal in
  content, not merely in file order.
- **Scout skip record present and valid.**
  `2dc6ba6:docs/issue-232/reports/implementation/survey.md:9-23` declares
  "Skipped — pure bugfix" with its one-line reason (a labeling-correctness
  bug in the repo's own instrumentation, with policy explicitly out of
  scope), which is one of the two skip conditions the scout directive
  allows.
- **Approval is real, and delivery followed it.** The issue comment whose
  entire body is `APPROVE issue-232/implementation` was posted by
  `jjongkwann` (MEMBER) at 2026-08-03T03:54:44Z
  (https://github.com/tokenmaxxxer/on-the-record/issues/232#issuecomment-5162113858);
  `docs/specs/approvers.md` lists that account; PR #233's author is the same
  account, so single-account mode's issue-comment path applies and
  `gh pr view 233 --json reviews` returning `[]` is consistent rather than a
  gap. The phase-2 delivery commit `a670098` is authored
  2026-08-03T13:11:50+09:00 (04:11:50Z), ~17 minutes after the approval —
  after, not before.
- **Delivered write set matches the approved proposal.** The proposal's
  `files:` list (`docs/issue-232/proposals/implementation.md:9-12`) is
  `spawn.py`, `test_spawn.py`,
  `docs/issue-232/decisions/event-layer-taxonomy.md`; `git show a670098 --stat`
  is those three files and nothing else, with `af92fce` adding only the
  role's own required record (`git show af92fce --stat`). No silent addition,
  no silent omission.
- One blemish, non-structural: PR #233's title still reads "issue-232:
  phase 1 — layer-classify watch's tool-refusal events" while the PR carries
  `a670098` and `af92fce` (`gh pr view 233`, title and commits) — finding 3.

## Verdict 3 — step

### (a) Do the layer fixtures actually fail against the pre-change code? — yes

Method: static derivation over `2dc6ba6:spawn.py` and `a670098`'s
`test_spawn.py` diff. The baseline's only refusal-emitting branch is
`2dc6ba6:spawn.py:2602-2607` — `type == "result"` with non-empty
`permission_denials` appends exactly one `gate-refusal` whose `detail` is
`str(denials)[:200]` — and that loop has no `type == "user"` branch at all
(the adjacent `elif` at `2dc6ba6:spawn.py:2608` handles `assistant` only).
Feeding each case's fixture lines (read from `a670098`'s `test_spawn.py`
diff) through that branch:

| case | baseline emits | case's assertions | result on `2dc6ba6` |
| --- | --- | --- | --- |
| `test_denials_with_no_correlating_tool_result_are_unclassified` | one `gate-refusal` | `unclassified-refusal` present, `gate-refusal` absent | fails both |
| `test_gate_hook_denial_is_gate_refusal_with_gate_name` | one `gate-refusal`, `detail` a `str` | `len == 1`, then `detail["gate"] == "board-gate"` | first passes; second raises `TypeError` on subscripting a `str` |
| `test_harness_permission_denial_is_not_labeled_gate_refusal` (5 subTests) | one `gate-refusal` | `harness-refusal` present, `gate-refusal` absent | fails all five |
| `test_sandbox_denial_is_not_labeled_gate_refusal` (2 subTests) | one `gate-refusal` | `sandbox-refusal` present, `gate-refusal` absent | fails both |
| `test_non_error_tool_result_matching_refusal_text_fires_nothing` | nothing (no `result` line in the fixture) | no refusal event of any type | passes |
| `ProgressEvents::test_refusal_parsing_still_works_alongside_progress` | one `progress`, one `gate-refusal` | `unclassified-refusal` count `== 1` | fails |

Five of six do not pass against the pre-change code, one passes — matching
the observed role's claim at `docs/issue-232/reports/implementation.md:140-151`
without adopting it: the derivation above is this role's evidence, that run
is theirs. The fixtures are therefore genuine regression guards, not tests
written to pass either way. Two precision corrections to that claim, neither
changing the conclusion: the layer-1 case does not fail by assertion — its
first assertion passes on the baseline and it stops on a `TypeError`, an
error rather than a failure, because the baseline's `detail` is a string;
and `record:149-150`'s "All 5 failures show the old code emitting
`gate-refusal` for harness/sandbox/correlation-miss inputs" omits that the
layer-1 case's discriminator is the `detail` shape, not the type string. The
one passing case is the issue-129 `is_error` guard, which the record itself
labels as passing on both sides (`record:146-149`) — declared, not
concealed. The fixtures drive real `_spawn_one` through
`EventReporting._run` (`2dc6ba6:test_spawn.py:1186-1231`, which mocks the
workspace and spawns `cat` over the fixture text), so they exercise the
production loop rather than a stub.

Limit: this is a derivation from diff text and the baseline blob. Re-running
the observed role's tests is prohibited for this role, so this establishes
what that code must do on those inputs, not an observed execution.

### (b) Do the patterns rest only on the issue's real samples? — provenance yes; application no

**Provenance is clean.** Every pattern in `a670098`'s `spawn.py` traces to a
sample cited in issue #232's §배경, and every cited sample is covered:
`Permission to use \S+ has been denied` ← "Permission to use Bash has been
denied"; `requires approval` ← both "…The following part requires approval:
…" and "This command requires approval"; `cannot be statically analyzed` ←
"Contains shell syntax (string) that cannot be statically analyzed";
`simple_expansion` ← "Contains simple_expansion"; `Operation not permitted`
← "mkdir: /tmp/…: Operation not permitted"; `haven't granted it yet` ←
"Claude requested permissions to write to …, but you haven't granted it
yet"; `_GATE_HOOK_RE` ← "PreToolUse:Bash hook error: [.../board-gate.sh]".
No pattern exists without a sample and no sample lacks a pattern. The one
regex covering two samples (`requires approval`) is the literal common
substring of those two samples — a narrowing to the shared token, not an
extension past the evidence. The `refused —` half of `_GATE_DENY_RE` is not
from the issue: it comes from `gate-lib.sh:78`
(`echo "${1:-gate}: refused — $2" >&2`, read directly this session), a
project-owned source that the delivered code's own comment names.

**The quoted-marker case, which the invoking prompt asks about, is not
handled.** `_classify_refusal_text` (`a670098`, `spawn.py`) runs
`_GATE_HOOK_RE.search(text)` first and returns on a hit before either later
pattern tuple is consulted, and its input is the whole text of any
`tool_result` carrying `is_error: true`. The issue's own layer-2 sample
shape embeds arbitrary quoted command text — "This Bash command contains
multiple operations. The following part requires approval: …" — and that
embedding was directly observed in this session: a `Bash` call of this
session was denied with `This Bash command contains multiple operations. The
following part requires approval: head -80 && echo "=== COMMITS ===" && gh
pr view 233 --json commits …`, the harness quoting the command verbatim into
its own denial message. A layer-2 denial of any command containing the
literal marker `PreToolUse:<tool> hook error: [<path>]` therefore classifies
as `gate-refusal` with a gate name attached — a layer-2 refusal reported as
layer-1, which is the exact mislabel direction issue #232 was filed to end.
This is not remote for this repo: that marker string now lives verbatim in
`a670098`'s own layer-1 fixture in `test_spawn.py` and in
`docs/issue-232/decisions/event-layer-taxonomy.md:19-20`, files role
sessions routinely read and grep.

**Structurally, the trigger got weaker, not stronger.** The new branch
(`a670098`'s `spawn.py`, the `elif issue is not None and obj.get("type") ==
"user"` block) emits without any reference to `denials` or `result`, whereas
the baseline could emit only when the terminal `result` line carried a
non-empty `permission_denials` (`2dc6ba6:spawn.py:2602-2606`). A session with
zero permission denials whose failed tool call happens to print matching
text now produces a refusal event that the pre-change code could not
produce. The record's claim that both hunt findings "leave behavior no worse
than the pre-fix code for any input"
(`docs/issue-232/reports/implementation.md:158-160`, echoed at `:119-122`) is
over-broad for exactly this input class, and the hunt's genericity finding
scopes itself to harness/sandbox patterns only (`record:114-122`), leaving
`_GATE_HOOK_RE` — the one whose false positive re-creates the filed bug —
outside its examination, while
`docs/issue-232/decisions/event-layer-taxonomy.md:18-20` describes layer 1
as firing "only on a confirmed match". See finding 1.

### (c) Is the "보고 한 번" dedup contract preserved? — yes, as re-stated and approved

From `a670098`'s `spawn.py`: `refusals_seen: set` replaces
`gate_refusal_seen: bool`; the classification branch does `if key in
refusals_seen: continue` and then `refusals_seen.add(key)` before
`_append_event`, so no key can emit twice; the terminal `result` branch is
guarded by `denials and not refusals_seen` and adds `("unclassified",)`
before emitting, so the fallback can neither double with a classified event
nor repeat. The contract as the approved proposal states it — "each distinct
layer (and, for gate refusals, each distinct gate) reports at most once per
session — preserving today's 'report once, not once per denial' behavior"
(`docs/issue-232/proposals/implementation.md:117-122`, identical wording at
`docs/issue-232/decisions/event-layer-taxonomy.md:54-61`) — holds by
construction.

The per-session ceiling does move: from exactly ≤1 event
(`2dc6ba6:spawn.py:2605-2606`) to ≤(one per distinct gate + one harness + one
sandbox), or exactly one `unclassified-refusal` when nothing correlates.
That widening is the intended consequence of 요구사항 1 and was written into
the proposal in `2dc6ba6`, i.e. before the 03:54:44Z approval — approved, not
silent.

Under-reporting direction: the observed role's hunt finding 1
(`docs/issue-232/reports/implementation.md:99-113`) accurately describes a
second, unmatched denial in an already-classified session producing no event,
and correctly notes the pre-change code lost the same information. One
interaction it does not name: a false positive from (b) also populates
`refusals_seen`, so a session where the spurious match fires and a real
denial fails to correlate reports the spurious one and drops the real one.
That is not a dedup-contract violation — it follows from the fallback guard
being session-wide — but it is where the two failure modes compose.

### (d) Is `watch`'s cycle unchanged? — yes

`git show a670098 -- spawn.py` contains exactly two hunks, `@@ -1482,6
+1482,64 @@` and `@@ -2559,7 +2617,11 @@`. `_await_bounded` occupies
`2dc6ba6:spawn.py:1670-1713` and `_watch` `2dc6ba6:spawn.py:1716-1751`;
neither hunk reaches either span. Reading the baseline directly:
`_await_bounded` returns on the first unconsumed `.events.jsonl` line,
prints `f"[watch] {ev['type']}: {ev['detail']}"` (`2dc6ba6:spawn.py:1691`),
and inspects the type only to distinguish `session-end`; `_watch --follow`
re-calls it and stops only when the consumed event's type is `session-end`
(`2dc6ba6:spawn.py:1738-1751`). None of the four new type strings is
`session-end` and consumption is type-agnostic, so block-until-first-material-
event-then-return is the same cycle, and the four strings surface as-is —
matching the claim at
`docs/issue-232/decisions/event-layer-taxonomy.md:63-67`. The dict-shaped
`detail` for `gate-refusal` is likewise not new to that printer: the
pre-change `progress` event already carried a dict
(`2dc6ba6:spawn.py`, the `assistant` branch's `{"kind": "tool_use", ...}`).

One truthful consequence, not a violation of 제약 1: a session that refuses
at two layers now yields two events where it yielded one, so an orchestrator
may need more `watch` calls to drain to `session-end`. The per-call cycle —
what 제약 1 constrains — is unchanged.

## Open findings

### Finding 1 — the layer-1 pattern is matched first, over uncorroborated error text

Artifact: `spawn.py` as delivered in `a670098` (`_classify_refusal_text` and
the `type == "user"` branch); secondarily
`docs/issue-232/reports/implementation.md:153-160` and
`docs/issue-232/decisions/event-layer-taxonomy.md:18-20`, which state the
behavior more strongly than the code supports.

- **Impact.** An orchestrating session can be shown `gate-refusal` with a
  `detail.gate` naming a gate that did not refuse — for a layer-2 denial
  whose message quotes a command containing the marker, or for a failed tool
  call in a session with no refusal at all, since the branch never consults
  `permission_denials` (`a670098`, `spawn.py`) whereas the baseline required
  it (`2dc6ba6:spawn.py:2602-2606`). That is the same class of report issue
  #232 records as having produced a baseless "board-gate keeps
  false-positiving" claim to the user. The spurious key also fills
  `refusals_seen`, suppressing the `unclassified-refusal` fallback for a
  genuine denial in the same session.
- **Timeline.** `2dc6ba6`'s survey identified `is_error: true` as the
  structural check that keeps issue-129's false-positive class closed
  (`2dc6ba6:docs/issue-232/reports/implementation/survey.md:89-150`); the
  proposal froze it as a constraint — "never bare substring matching over
  arbitrary stdout" (`docs/issue-232/proposals/implementation.md:54-58`);
  `a670098` implemented `is_error` gating plus substring matching over that
  result's text; the hunt examined substring genericity for harness and
  sandbox only (`docs/issue-232/reports/implementation.md:114-122`); merged
  2026-08-03T04:48:59Z as `70f867f` with `gh pr view 233 --json reviews`
  returning `[]`.
- **Root cause.** `is_error: true` is a weaker predicate than the constraint
  assumed: it marks any failed tool call, whose content is arbitrary
  stdout/stderr, not only a refusal. The delivered classifier therefore keeps
  the constraint's letter while its intent — no bare substring matching over
  arbitrary stdout — holds only against *successful* echoes, the narrower
  issue-129 case the new guard test covers. Nothing ties a classification to
  the `permission_denials` list the harness itself reports.
- **Action item.** For the human on PR #234: decide whether this warrants an
  issue to corroborate each per-line classification against the terminal
  `permission_denials` before emitting, and/or to anchor `_GATE_HOOK_RE` to
  the start of the `tool_result` text instead of searching anywhere within
  it. This role proposes no fix, edits nothing, and files no issue.

### Finding 2 — `detail.gate` can carry a role name rather than a gate identity

Artifact: `_classify_refusal_text`'s layer-1 branch in `a670098`'s
`spawn.py`, which takes `_GATE_DENY_RE.group(1)` when present and falls back
to the hook-path stem only when it is absent.

- **Impact.** 요구사항 2 asks which gate refused, enumerating "board-gate,
  trailer-gate, gh-guard". For a gate whose `gate_deny` first argument is the
  gate name the event is right — that is the case `a670098`'s layer-1 fixture
  covers. For a gate that passes the role name it is wrong, and the accurate
  identity (the hook script's stem, already extracted as `hook_m.group(1)`)
  is discarded. Observed live this session: this record's own first write was
  refused with `PreToolUse:Write hook error:
  [${CLAUDE_PLUGIN_ROOT}/hooks/record-fields-gate.sh]: execution-observation:
  refused — record is missing required section(s): …`. Against that text
  `_GATE_HOOK_RE` yields the stem `record-fields-gate` (the gate) while
  `_GATE_DENY_RE` yields `execution-observation` (the role), and the
  delivered code prefers the latter.
- **Timeline.** The survey asserted the gate name is "recoverable **twice
  over** … and, redundantly, the `gate_deny` message's own leading `<gate>:`
  token" (`2dc6ba6:docs/issue-232/reports/implementation/survey.md`, §Layer
  1); proposal step 2 named only hook-path extraction
  (`docs/issue-232/proposals/implementation.md:112-116`); `a670098` added the
  deny-token source and made it the preferred one; the counterexample above
  was observed 2026-08-03 in this session.
- **Root cause.** `gate-lib.sh:75` documents the signature as `gate_deny
  <role-or-gate-name> <message>` — the token is explicitly not guaranteed to
  be a gate name. The survey read `gate-lib.sh:77-79` and treated the two
  sources as redundant without reading the signature comment two lines above
  it, and the implementation then ranked the non-guaranteed source first.
- **Action item.** For the human on PR #234: decide whether to file an issue
  preferring the hook-path stem for `detail.gate` (keeping the deny token as
  the reason text). No fix is proposed or made here.

### Finding 3 — PR #233's title says phase 1 while the PR carries the phase-2 commits

Artifact: PR #233's title, "issue-232: phase 1 — layer-classify watch's
tool-refusal events" (`gh pr view 233`), against its commit list containing
`a670098` and `af92fce` (`gh pr view 233 --json commits`).

- **Impact.** Low. The merge-time artifact a reviewer reads first names the
  wrong phase; the body was updated and does say "Phase 2 (this update):
  implementation, approved via issue comment `APPROVE
  issue-232/implementation`", so the mislabel is recoverable in one scroll.
- **Timeline.** PR opened for phase 1 at `2dc6ba6`; phase-2 commits pushed to
  the same PR per contract v3 s19; title never updated; merged
  2026-08-03T04:48:59Z.
- **Root cause.** Contract v3 s19 reuses one PR across both phases and
  nothing in it requires the title to be re-stated when phase 2 lands.
- **Action item.** None required of the observed role. Noted for the human as
  a candidate convention (retitle at phase 2, or title phase-neutrally from
  the start).

## What this record does not establish

- No execution. Item (a) is a static derivation over `a670098`'s diff and the
  `2dc6ba6` baseline blob, not an observed test run; the observed role's own
  run (`docs/issue-232/reports/implementation.md:136-151`) is treated as its
  claim, corroborated but not adopted.
- Findings 1 and 2 are read from artifact text plus refusal messages observed
  in this session's own tool stream. Neither was reproduced by running
  `spawn.py`, which this role is prohibited from doing.
- Issue #232's process state — auto-close on PR #233's merge at 04:49:00Z and
  the human reopen 11 seconds later
  (https://github.com/tokenmaxxxer/on-the-record/issues/232#issuecomment-5162415521),
  and the `## 실행 계획` checklist carrying only `- [ ] step 1  implementation`
  with no step-2 line — is out of this observation's scope; the issue's own
  comment attributes the auto-close to issue #228.

## Next steps

None for this role on issue #232. This record is the deliverable; PR #234
carries it for the human's judgment.

## Open-finding resolution path

Findings 1-3 stay in this record on PR #234 with their evidence. This role
does not fix them, does not touch the observed role's paths, and does not
file an issue: under contract v3 issues are user-authored only, so the human
judges these on PR #234 and files whatever they consider warranted.
