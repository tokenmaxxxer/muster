# Current-state survey — README.md / README.ko.md (issue #85)

## What each README currently leads with

**README.md**: opens with the name, a one-line pointer to the Korean version,
then immediately describes the mechanism — "Musters a role — brings up one
sandboxed session with only that role's rulebook..." — followed by the
"not a dispatcher, a power outlet with a concierge" framing, then a directory
listing (`protocol.md`, `roles/`, `spawn.py`, ...). The first user-facing
benefit does not appear until deep into "## Why this exists" (session-scoped
plugin isolation) — itself a mechanism explanation, not a problem statement.

**README.ko.md**: same shape. Opens with "역할을 소집한다 — ..." (mechanism),
"배차 기사가 아니라 콘센트다" (same concierge/outlet metaphor), directory
listing, then "## 왜 필요한가" (why this exists) — again a mechanism
rationale (session-scoped plugin isolation), not a user problem statement.

Both READMEs are mechanism-first: they explain *how* on-the-record works
before explaining *why* a reader should care. There is no "off the record vs
on the record" framing anywhere in either file today, and none of the five
user problems named in the issue (vibe-coding drift, quality coin-flip,
repeating rules every session, nothing handover-able, parallel-agent
collisions) are named explicitly as problems — they are implicit in later
mechanism sections at best.

## Structural outline (current)

Both files share this skeleton (English section names, Korean mirrors each):

1. Title + language cross-link
2. One-line mechanism description ("musters a role...")
3. "Not a dispatcher, a power outlet with a concierge" metaphor + contract
   description (who talks to whom, which account does what)
4. Repo/file tree with one-line annotations (`protocol.md`, `roles/`,
   `spawn.py`, `on-the-record/`, `wakes.py`, `gates/`, `ledger/`; README.md
   also lists `bench/`-adjacent content inline in EN vs KO has `bench/` too)
5. "## Getting started" (EN only — README.ko.md does not have this section
   at all, a content parity gap between the two languages already) — setup
   steps: `gh auth login`, plugin marketplace add/install, doctor probe,
   optional agent identity, `MUSTER_ROLE_MODEL`, rulebook auto-fetch, and
   per-target-repo setup (`docs/specs/approvers.md`, branch protection)
6. "## Why this exists" (EN) / "## 왜 필요한가" (KO) — session-scoping
   rationale
7. "## Roles" — table of the nine roles and what each decides
8. "## Using it" (EN) / "## 쓰기" (KO) — Installing, board opt-in
   precondition, the loop (`wake`, `spawn.py <role>`), from-a-conversation
   usage, every command, session-end ledger behavior, where a run stops on
   purpose
9. "## Isolation — a sandbox, not a container" — comparison table vs
   containers
10. "## Three traps, each one measured" (EN) / "## 실측으로 확인한 함정 셋"
    (KO) — plus EN-only subsections "Package-registry access (issue #38)",
    "Web access (issues #58, #65)", "Default-open posture (issue #72)" that
    do not exist in the KO file — another parity gap
11. "## Gates" — deterministic post-session checks
12. "## Self-check" — `python3 test_gates.py`
13. "## Open" (EN) / "## 미해결" (KO) — known gaps/limitations

Note: README.md and README.ko.md have already drifted apart structurally —
README.ko.md is shorter, missing the "Getting started" section and the three
EN-only subsections under "Three traps" (package-registry, web access,
default-open posture). Any rewrite must treat "same message in both
languages" as a real fix, not just a stylistic goal — the two files are not
at parity today even before layering in the benefit-first requirement.

## Where they diverge from the issue's benefit-first requirement

- Neither file leads with a user problem. The issue names five specific
  "walls" (vibe-coding drift, quality coin-flip, re-teaching rules every
  session, nothing handover-able, parallel-agent collisions on git) that a
  first-time visitor should see before any mechanism detail. None of these
  five are named as such in either README today.
- Neither file has the "off the record vs on the record" brand line or
  framing. The closest existing material is the "power outlet with a
  concierge" / "not a dispatcher" metaphor, which describes control flow
  (who talks to the user, who spawns what) rather than the trust/record
  argument the issue wants foregrounded.
- The "why this exists" content that does appear (session-scoped plugin
  isolation preventing settings.json bleed across roles) is a real, accurate
  benefit but it is narrow (one specific technical justification) and
  buried under "## Why this exists", well past the fold — not connected to
  the five broader problems named in the issue.
- Structure guidance in the issue explicitly wants: problems → the
  on-the-record answer (above the fold) → how it works (roles, two-phase
  proposal→delivery PRs, approval gates, wake/board) as supporting detail →
  install. The current files invert this: mechanism/install first,
  rationale ("why this exists") buried mid-document, and no problem framing
  at all.

## Content that is accurate and must be preserved as supporting detail

This content is correct today and should survive the rewrite, repositioned
as supporting detail beneath the new benefit-first opening rather than
deleted or rewritten from scratch:

- **How it works**: the role-muster mechanism (one sandboxed session per
  role, rulebook + tokenmaxxxer-core plugins only), the "power outlet with a
  concierge" contract description (orchestration session talks to the user,
  drafts issues, spawns role sessions, relays approvals; role sessions run
  under the agent account and return everything by PR), and "each role owns
  its state; on-the-record only reads it."
- **Repo/file tree** annotations (`protocol.md`, `roles/`, `spawn.py`,
  `on-the-record/`, `wakes.py`, `gates/`, `ledger/`).
- **Install instructions**: `claude plugin marketplace add
  tokenmaxxxer/on-the-record` + `claude plugin install
  on-the-record@tokenmaxxxer` (or the `/plugin` slash-command equivalents),
  no-clone-needed explanation, doctor probe on first spawn after a CLI
  update.
- **Getting started / per-machine and per-target-repo setup**: `gh auth
  login`, optional agent identity (`MUSTER_AGENT_GH_TOKEN`), optional
  `MUSTER_ROLE_MODEL` / `role_model.txt` precedence, rulebook auto-fetch
  under `on-the-record/runs/rulebooks/`, target-repo prerequisites
  (`docs/specs/approvers.md`, branch protection).
- **Roles table**: the nine roles (product, feasibility, coding, review, qa,
  ux-design, verify, reflect, ops) and what each decides — this is the
  concrete evidence for "role experts with clean context per task."
- **Using it**: installing, board opt-in precondition, the loop
  (`spawn.py <role>`, `wake`), from-a-conversation usage, every command
  reference, session-end ledger/ outcome naming, where a run stops on
  purpose (proposed→approved gate, first-read-of-upstream-artifact gate).
- **Isolation section**: sandbox-vs-container comparison table — supports
  the "self-contained, one plugin, whole system" and safety claims.
- **Three traps / package-registry / web access / default-open posture**:
  measured engineering detail, valuable as deep supporting material but not
  above-the-fold material.
- **Gates, self-check, and Open sections**: accurate, low-priority-for-the-
  fold content that should stay near the end.

## Frozen write set for phase 2

- `README.md`
- `README.ko.md`

No other files are in scope for the rewrite phase.
