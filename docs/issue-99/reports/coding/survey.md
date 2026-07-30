# Issue #99 — current-state survey

## Write set (projected)

- `docs/specs/wake-routing.md`: add one section defining the
  conditional -> go resolution path. No existing section covers it;
  the doc's "Human-only edges" section is the closest precedent
  (findings-resolved re-verify is also "a human triggers this").
- `wakes.py`: comment-only, if the new doc section needs a pointer
  next to the exact-match `go` check at the coding wake-branch
  (`roles.get("feasibility", {}).get("verdict") == "go"`). No branch
  logic changes — the exact-match refusal of non-"go" strings is
  already correct behavior per the issue; the gap is that nothing
  defines how a record legally becomes "go" after a condition is
  settled.
- `test_gates.py`: none needed unless the doc gets a structural
  equivalence check; issue #99 does not ask for one and this is a doc-
  only spec addition, not a new routing edge for `_rows()` to encode
  (the resolution is a human act that produces a new commit with
  `verdict: go`, which the existing exact-match check already wakes
  on — no new machine-judged row).

## What's already there

- `roles/feasibility.json` declares `verdict: go|no-go|conditional`
  but no code path or doc currently says what happens to
  `conditional`.
- `wakes.py` (coding's first wake-branch) does an exact string
  compare `verdict == "go"` — confirmed correct-as-is by the issue
  (it "correctly refused" the free-text variant). This survey found
  no other place verdict strings are compared or parsed.
- `docs/specs/wake-routing.md` (added by #95) documents the routing
  table but has no section on record-field resolution/normalization —
  it documents *when* a role wakes, not *how a verdict value changes*.
- The closest existing precedent for "a human act moves a stuck
  record forward" is the **findings-resolved re-verify** human-only
  edge already in the doc: "the role that raised a blocking finding
  wakes again once it is addressed. Only a human triggers this
  re-verify." Issue #99's requirement (who re-raises, on what
  evidence, condition text lives in body not verdict field) is
  structurally the same shape: a human-gated field transition,
  documented as a named edge, not a mechanically-judged row.
- `docs/specs/approvers.md` lists which GitHub accounts count as
  human approvers — the natural "on what evidence" anchor (a PR
  Approve or an APPROVE comment from an approvers.md account is
  already this repo's sole definition of a human decision), so the
  new edge can point at the same evidence source rather than invent a
  new one.

## Unknowns / gaps this proposal must close

- Who edits the feasibility record to flip `verdict: conditional` to
  `verdict: go`: feasibility itself (re-raising after being pointed at
  the settled condition) vs. anyone. Issue text says "who re-raises the
  verdict" — implies a role acts, not an automated rewrite.
- What "evidence" is: issue text says "once its condition is settled
  by a human decision (e.g. on the proposal PR)" — the evidence is a
  human decision already expressed through this repo's existing
  approval mechanics (PR Approve / APPROVE comment per
  `docs/specs/approvers.md`), not a new decision channel.
- Where condition narrative lives: issue says "in the record body,
  never in the verdict field" — the field must stay exactly one of
  `go|no-go|conditional` (matching `roles/feasibility.json`'s enum),
  never a compound string like the observed
  `"go (조건부 → confirmed by human on PR)"`.

## Scout skip record

Scouting skipped: this is an internal protocol-spec fix (a routing/
verdict-resolution rule for this repo's own board machinery), not a
product-shaped surface with an external best-in-class category to
compare against. The applicable prior art is this repo's own existing
human-only edge (findings-resolved re-verify) and its approvers.md
evidence model, both already surveyed above — no external field to
sweep.
