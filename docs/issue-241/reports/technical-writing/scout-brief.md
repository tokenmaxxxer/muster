---
status: final
---

# Scout brief — issue-241 README overhaul

Mode: parallel WebSearch (2 angles, 1 round). Wall-clock well under budget; stopped
at judge point 1 — the two angles converged and matched the issue's own ask, so no
deepening round was needed.

## Must-bes (category: OSS project README)
- Quickstart (copy-paste install/run commands) within the first screenful.
- "What is this / why" stated early, in plain language, before deep technical detail.
- Keep the README itself focused; push complete/operational documentation to linked
  docs rather than inlining everything.

## Performance axes competitors visibly compete on
- Essay-as-README depth: some projects (e.g. Day8/re-frame) run a full philosophy
  essay as the README's spine, not just a short blurb — proves the pattern the issue
  asks for is not unusual, it's a known strong form.
- Explicit "philosophy"/"why" section as a named, separate block from install/usage
  (create-go-app/cli, Gofiber/fiber, Express-style templates).
- Brevity discipline: one strong opposing signal — "keep it concise; ain't nobody
  got time for your manifesto" — the risk with essay-led READMEs is bloat if the
  quickstart isn't hoisted clearly above the essay.

## Adopt / skip
- Adopt: essay-as-spine pattern (precedent: re-frame) — matches issue's structure
  exactly (quickstart top, essay body, docs links at tail).
- Adopt: quickstart-before-essay ordering to defuse the "manifesto bloat" risk found
  in the counter-signal above.
- Skip: badges/table-of-contents scaffolding — not asked for, would compete with the
  essay's own voice.

## Segment fit
This is a dev-tool README for a multi-agent orchestration harness; the closest peers
in the sweep (re-frame, fiber, express) are also framework/tool READMEs, not app
READMEs — good fit, no swap needed.

## Gap line
Current README.md/README.ko.md already have a "why" section (Five walls / "다른 AI는
기록에 안 남고 일한다") but it precedes the quickstart and is a bullet-pitch, not an
essay — the issue's ask is exactly to swap that pitch for the fuller essay and move
the quickstart above it. Operational content (Requirements, Windows/WSL rationale,
repo layout, account model, config) has no docs/ home yet — it's a genuine gap that
must be filled, not merely relocated to an existing doc.

Sources:
- https://github.com/banesullivan/README
- https://www.thegooddocsproject.dev/template/readme
- https://github.com/matiassingers/awesome-readme
