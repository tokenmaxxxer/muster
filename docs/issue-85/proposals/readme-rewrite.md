files: README.md, README.ko.md

## Request

Issue #85 asks for `README.md` / `README.ko.md` to open by selling the
plugin through the user problems it solves, not by describing its
mechanism. A first-time visitor should see *why* they'd want
on-the-record before *how* it works. Concretely: lead with five named
"walls" a plain AI-coding user hits —

1. Vibe coding drifts (long chat session, context rot, forgotten
   requirements, an unowned codebase).
2. Quality is a coin flip (nothing gates unverified work before it lands).
3. You repeat yourself every session (working rules re-taught each time).
4. Nothing is handover-able (requirements/decisions live only in chat logs).
5. Parallel agents collide (no isolation, no merge discipline).

— then answer with the one-line brand statement: "Other AI works off the
record. Yours works on the record." (every piece of work becomes an
official git record: requirements as issues, work as PRs, decisions as
recorded approvals, rules as versioned rulebooks — trustworthy,
handover-able, sellable-grade output).

After that hook, the existing accurate content (how it works: roles spawned
per issue, two-phase proposal→delivery PRs, approval gates, wake/board;
install instructions) becomes supporting detail, reused rather than
rewritten from scratch. Both languages must carry the same message —
README.ko.md is currently missing sections README.md has (see survey), so
achieving parity is part of this request, not an optional nicety.

## Constraints

- Frozen write set for the rewrite phase: `README.md`, `README.ko.md` only.
  No other file changes.
- Preserve all currently-accurate technical detail (install commands, roles
  table, isolation/sandbox explanation, gates, traps, open items) — reposition
  as supporting detail, do not delete or invent new mechanism claims.
- Keep exact install commands as documented: `claude plugin marketplace add
  tokenmaxxxer/on-the-record`, `claude plugin install on-the-record@tokenmaxxxer`
  (and the `/plugin marketplace add` / `/plugin install` slash-command form
  already present).
- README.ko.md must be a genuine Korean rewrite carrying the same
  structure and message as README.md — not a literal translation artifact,
  but also not free to diverge in content coverage (fix the existing parity
  gaps: missing "Getting started" section, missing "Package-registry
  access" / "Web access" / "Default-open posture" subsections under the
  traps section).
- Do not touch protocol.md, roles/*, spawn.py, or any code — this is a
  documentation-only phase.
- This proposal covers phase 2 planning only; no README edits happen until
  this proposal is approved.

## What will be done

Both README.md and README.ko.md will be restructured to this skeleton
(section order is the deliverable; exact wording is drafted at build time):

1. **Title + language cross-link** (unchanged).
2. **Hook — five problems, above the fold.** A short lead naming the five
   walls (vibe-coding drift, quality coin-flip, re-taught rules, no
   handover, parallel-agent collisions) in plain, concrete language grounded
   in what a solo AI-coding user actually experiences.
3. **The on-the-record answer.** The "off the record vs on the record"
   one-liner, followed by a short paragraph on what "on the record" means
   mechanically at a glance (issues = requirements, PRs = work, recorded
   approvals = decisions, versioned rulebooks = rules) and why that produces
   trustworthy / handover-able / sellable-grade output. Benefits to weave in
   here or immediately after: role experts get clean context per task; the
   process asset lives in git so a better model is leveraged immediately
   without re-teaching it anything; the user stays the sole approver (CEO
   position, nothing merges without them); self-contained — one plugin
   installs the whole system.
4. **How it works (supporting detail, reusing existing accurate content).**
   Roles spawned per issue (session-scoped isolation, the "power outlet with
   a concierge" framing kept as the mechanism metaphor), two-phase
   proposal→delivery PRs (`loop_state: proposed,approved,landed`), approval
   gates (human-only at proposed→approved), the wake/board loop. This
   reuses the current "Why this exists," "Roles," and loop-mechanics content
   almost verbatim, just moved below the fold and re-framed as "here is how
   the promise above is actually implemented."
5. **Install / usage (supporting detail).** Getting-started steps (`gh auth
   login`, plugin marketplace add/install, per-target-repo setup with
   `docs/specs/approvers.md`), the roles table, "Using it" command
   reference, session-end ledger behavior, where a run stops on purpose.
   Kept close to current content; README.ko.md gains the missing
   "Getting started" section to reach parity with README.md.
6. **Deep supporting material (unchanged position, low-priority-for-the-
   fold).** Isolation/sandbox comparison, three traps + package-registry /
   web-access / default-open posture subsections (added to README.ko.md for
   parity), gates, self-check, and the "Open" section.

Both files will carry the same section order and the same claims; the
Korean file will be drafted as an independent, idiomatic rewrite of each
section rather than a sentence-by-sentence translation, matching the
project's existing style of "same message, not same words" between EN/KO
(as already true for the parts of the files that do have KO coverage today).

## Out of scope

- Any change to protocol.md, roles/*.json, spawn.py, gates/, or other code.
- Adding new features or mechanism claims not already documented elsewhere
  in the repo.
- Reworking the roles table, command reference, or sandbox/isolation
  technical content beyond repositioning them under the new structure.
- Localization of any file other than README.ko.md.

## How we'll know it worked

- Both README.md and README.ko.md open (first screen, above any install
  command) with the five named problems and the off-the-record/on-the-record
  answer, before any mechanism explanation.
- Every currently-accurate technical claim (install commands, roles table,
  loop mechanics, isolation table, traps, gates, self-check, open items)
  still appears somewhere in the rewritten file — nothing is silently
  dropped.
- README.ko.md reaches structural parity with README.md (no section present
  in one language and silently missing from the other), while remaining an
  independent rewrite rather than a literal translation.
- A fresh reader of either file can state, from the first screen alone, why
  they'd want on-the-record — without needing to reach "## Why this exists"
  or later sections.
