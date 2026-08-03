---
subject: issue-235
role: implementation
phase: 1
---

# Build proposal — issue-235

files:
- `spawn.py`
- `test_spawn.py`

## Request

Issue #235 asks for two precision fixes to `watch`'s tool-refusal
classifier landed by issue #232/PR #233 (`70f867f`), both identified by
`docs/issue-232/reports/execution-observation.md`'s independent Finding 1
and Finding 2 (that record is issue #235's own cited authoritative
evidence, `## 참고`) and corroborated separately by a local sandbox
adversarial-verification experiment that rejected the same code twice on
the same attack angle: (1) `_classify_refusal_text` classifies any
`is_error: true` tool_result text by unanchored substring search without
ever checking the harness's own `permission_denials` record, so `is_error`
(a "this tool call failed" signal) gets treated as if it were "this was a
refusal" on its own — a session with zero denials can still emit a
`gate-refusal`, and a layer-2 harness denial that quotes a command
containing the gate-hook marker string gets mislabeled as layer 1, which
is the exact mislabel direction issue #232 was filed to end; (2)
`_GATE_HOOK_RE` is not anchored to the start of the tool_result text, so it
cannot distinguish a hook error the harness itself placed at the message's
start from the same marker text quoted/embedded inside an unrelated
message; (3) `detail.gate` prefers `gate_deny`'s first whitespace token
over the hook path stem, but that token's documented signature
(`gate-lib.sh:75`, `gate_deny <role-or-gate-name> <message>`) does not
guarantee it names the gate — a real `record-fields-gate` denial observed
in execution-observation's own session put a role name
(`execution-observation`) in that token while the hook path stem correctly
read `record-fields-gate`.

## Constraints

- No new instrumentation — issue #235 constraint 5 explicitly carries
  forward issue #232's requirement 3 ("이 이슈가 세운 제약 유지 — 새 계측
  금지"): the fix reads only text already present in the session's
  stream-json lines (`tool_result` text and the terminal `result` line's
  `permission_denials`), adding no new log line, CLI flag, or hook output.
- `watch` cadence/interval unchanged — `_await_bounded`'s
  block-until-first-new-event-line-or-stall cycle (`spawn.py:1670-1713`,
  per issue-232's own proposal and unchanged since) is not touched; this
  fix only changes what gets classified and written to an existing event
  shape, not when `watch` returns.
- No arbitrary expansion of the pattern set — issue #235 constraint 5
  carries forward "패턴은 실물 샘플 기반(임의 확장 금지)": no new
  harness/sandbox phrase, and no change to which strings `_GATE_HOOK_RE`/
  `_GATE_DENY_RE`/`_HARNESS_REFUSAL_PATTERNS`/`_SANDBOX_REFUSAL_PATTERNS`
  match — only (a) anchoring the existing gate-hook pattern to text start,
  and (b) which of two already-extracted values (hook stem vs. deny token)
  is preferred for `detail.gate`.

## Rationale

**Chosen approach (per the issue's own prescribed fix, which leaves no
open design decision — see Scout skip record in
`docs/issue-235/reports/implementation/survey.md`):** corroborate the
per-line `is_error` classification against the terminal `result` line's
`permission_denials` before emitting a layer-1/2/3 verdict; anchor
`_GATE_HOOK_RE` to the start of the tool_result text; swap which of the
two already-extracted gate-identity sources is preferred, keeping the
deny-token as reason text only. This is a correctness fix to logic that
already exists, not new logic — every fact base it needs
(`permission_denials`, the hook path stem, the deny token) is already
being read at the sites in question (`spawn.py:1525-1533`, `2666`); the
fix reorders/re-gates existing reads rather than adding new evidence
sources.

**Alternative 1 — keep unanchored substring search, but narrow it by
expanding/tightening the pattern set instead of adding corroboration
(e.g. require the marker plus a following gate-name-shaped token
in one combined regex).** Rejected: issue #235 constraint 5 explicitly
forbids expanding the pattern set ("패턴은... 임의 확장 금지"), and any
regex-only tightening still cannot distinguish a real harness-placed hook
error from the same literal marker string quoted inside a *different*
layer's message — the quoted text is byte-identical to a real occurrence,
so no amount of local pattern refinement recovers the missing signal;
only checking against the harness's own out-of-band `permission_denials`
record (evidence the classifier isn't already using) can, which is why
the issue asks for corroboration rather than a smarter regex.

**Alternative 2 — add new instrumentation, e.g. have gate hooks emit a
structured marker (a `hookSpecificOutput`-style field) so the classifier
never has to pattern-match free text at all.** Rejected: issue #235
constraint 5 explicitly forbids new instrumentation ("새 계측 금지"),
mirroring issue #232's own requirement 3 and its proposal's Alternative 2
rejection (`docs/issue-232/proposals/implementation.md:82-94`) for the
same reason — it would mean coordinating changes across
`tokenmaxxxer-core` and/or Claude Code itself, both outside this project's
control, for information a corroboration-only fix can already recover
from evidence the session log already carries.

**Alternative 3 — resolve Finding 2 by dropping the deny-token source
entirely instead of merely re-ranking it.** Rejected: the issue's
requirement 3 keeps the deny-token as the reason text's source
("`gate_deny` 토큰은 사유 텍스트로만 쓸 것"), and the current code already
extracts a reason string from whichever branch fires (`spawn.py:1530,
1533`); dropping the token source outright would either lose reason-text
information execution-observation's own Finding 2 evidence never asked to
lose, or require inventing a new reason-text derivation — a larger change
than the issue's stated fix and not something either finding's evidence
supports.

## What will be done

1. **Corroborate `_classify_refusal_text`'s substring match against
   `permission_denials` before emitting a layer verdict.** Today, the
   `obj.get("type") == "user"` branch (`spawn.py:2676-2690`) calls
   `_classify_refusal_text(text)` on any `block.get("is_error")` tool_result
   text with no reference to `denials`, which is read only inside the
   separate `obj.get("type") == "result"` branch (`spawn.py:2664-2675`) and
   never shared with the classification decision. Phase 2 will make the
   per-line classification consult the session's `permission_denials`
   signal (read from the terminal `result` line, which per Claude Code's
   `--output-format json` behavior always follows the per-line stream) so a
   substring match with no corroborating denial does not produce a layer-1/
   2/3 verdict on its own — closing execution-observation Finding 1's
   zero-denials and quoted-marker misfire paths
   (`docs/issue-232/reports/execution-observation.md:264-279, 339-378`).
2. **Anchor `_GATE_HOOK_RE` to the start of the text.** Today
   (`spawn.py:1491`) the pattern
   `r"PreToolUse:\S+ hook error: \[([^\]]*)\]"` has no start anchor and is
   applied with `.search()` (`spawn.py:1525`), matching anywhere in the
   tool_result text. Phase 2 will anchor it to the start of the text (per
   issue requirement 2's "시작 위치에 앵커"), the minimum condition to
   distinguish a hook error the harness itself placed at the message's
   start from the marker quoted/embedded inside an unrelated message.
3. **Prefer the hook path stem over `gate_deny`'s first token for
   `detail.gate`.** Today (`spawn.py:1526-1533`) `_GATE_DENY_RE`'s token is
   tried first and the hook-path stem (`Path(hook_m.group(1)).stem`,
   already extracted at `spawn.py:1532`) is used only as fallback. Phase 2
   will invert the preference — the hook path stem becomes the source of
   `detail.gate` unconditionally when `_GATE_HOOK_RE` matches, and the
   `gate_deny` token (when present) is used only to build the reason text,
   per issue requirement 3 and execution-observation Finding 2's
   `record-fields-gate` counterexample
   (`docs/issue-232/reports/execution-observation.md:380-417`).
4. **Add the four regression cases the issue names (`## 요구사항 4`), each
   shown to fail against pre-change `main`:**
   - (i) a layer-2 message that quotes the gate-hook marker (e.g. a
     harness "requires approval" denial whose quoted command text contains
     the literal string `PreToolUse:Bash hook error: [.../some-gate.sh]`),
     asserting the event classifies as `harness-refusal`, not
     `gate-refusal`;
   - (ii) a session with an empty `permission_denials` on the terminal
     `result` line whose failed tool_result output nonetheless contains the
     gate-hook marker text, asserting no `gate-refusal` (or any refusal)
     event fires;
   - (iii) a synthetic case combining a spurious marker match with a real,
     distinct denial in the same session, asserting the real denial is
     still reported (not suppressed by the spurious match populating
     `refusals_seen` first) and the spurious one is not;
   - (iv) the real `record-fields-gate` denial text from
     execution-observation Finding 2 (`PreToolUse:Write hook error:
     [.../record-fields-gate.sh]: execution-observation: refused —
     record is missing required section(s): …`), asserting
     `detail.gate == "record-fields-gate"`, not `"execution-observation"`.

   All four will be run against the current pre-change classifier
   (this branch's `spawn.py` as of this PR, equivalent to `main`) in
   phase 2 to confirm each fails there before the fix lands, per the
   issue's requirement 4 and the role-handoff contract's evidence
   standard.

## Out of scope

- All phase-2 code changes to `spawn.py` and `test_spawn.py` — this
  phase-1 PR adds only this proposal and the accompanying survey
  (`docs/issue-235/reports/implementation/survey.md`); no line of
  `spawn.py` or `test_spawn.py` is touched by this PR.
- The four regression tests themselves — named and specified above, not
  written, in this phase.
- The implementation record (`docs/issue-235/reports/implementation.md`)
  — written only after phase-2 code lands, per the role-handoff contract.
- Harness-permission and sandbox layer *policy* — unaffected; this fix
  only changes which layer a refusal is correctly attributed to, never
  what the harness or sandbox allows or denies.
- Any change to `.events.jsonl`'s event type names or `detail` dict shape
  — both are unchanged; only which event fires (or doesn't) and what value
  `detail.gate` holds change.

Per this repo's role-handoff contract, phase 2 (the actual code and test
changes above) opens only after a human approver listed in
`docs/specs/approvers.md` posts a GitHub PR "Approve" review on this PR,
or — in single-account mode — an issue comment on #235 whose entire body
is exactly `APPROVE issue-235/implementation`.

## How you'll know it worked

- The four regression cases from "What will be done" item 4 are
  demonstrated failing against pre-change code and passing after the fix
  lands, in phase 2.
- Execution-observation's Finding 1 and Finding 2 misclassification paths
  no longer fire spuriously: a zero-`permission_denials` session with
  gate-marker-shaped failure text produces no `gate-refusal`; a layer-2
  denial that quotes the gate-hook marker classifies as `harness-refusal`;
  a `record-fields-gate` denial's `detail.gate` resolves to
  `"record-fields-gate"`, not a role name.
- All existing `EventReporting` cases in `test_spawn.py` (`test_spawn.py:
  1183` onward) — including `test_gate_hook_denial_is_gate_refusal_with_
  gate_name`, `test_harness_permission_denial_is_not_labeled_gate_refusal`,
  `test_sandbox_denial_is_not_labeled_gate_refusal`,
  `test_denials_with_no_correlating_tool_result_are_unclassified`, and
  `test_non_error_tool_result_matching_refusal_text_fires_nothing` — stay
  green, confirming the fix is a narrowing/correction and not a regression
  of issue-232's own three-layer split or issue-129's `is_error` structural
  guard.
