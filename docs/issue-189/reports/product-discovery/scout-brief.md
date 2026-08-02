# Scout brief — issue #189: execution plan in the issue body

Mode: parallel fan-out (3 concurrent WebSearch calls), 1 sweep stage, no deepening round —
stopped at judge point 1 (saturation): the two decision-relevant hits already converge on
the same shape the survey needed to check, and a second round would not change the
recommendation. Elapsed: ~32s, well under the 3-stage/3min budget actually used.

## Must-bes (Kano) — what the strong hits assume

- A pre-declared step/parallel-group sequence is visible **before any execution starts**,
  not gated on a merge/deploy artifact (GitHub Actions: the job DAG renders from the YAML
  the moment it exists). This is the same shape requirement 4 needs.
- A step that needs a human check **pauses visibly** (status "Waiting") rather than
  silently blocking or auto-advancing — matches requirement 3's no-auto-progress rule.
- Checkbox-style plan items are a first-class, load-bearing GitHub primitive (issue
  tasklists), not a hack — but GitHub's own *auto-tracking* of those checkboxes only
  fires when a checkbox item is a link to another tracked issue, not for arbitrary
  inline text.

## Performance axes (where exemplars visibly compete)

1. **How early the plan becomes visible** — GitHub Actions wins outright (pre-run); Jira/Linear
   backlog visibility is default-on but frequently misconfigured/hidden by board filters.
2. **Whether the human gate is legible as "waiting," not just absent** — GitHub Actions'
   environment-reviewer gate names this explicitly; issue checkboxes have no such state of
   their own (a step's box just stays unchecked either way).
3. **Whether the checklist auto-syncs with real work items or is manually maintained** —
   GitHub tasklists auto-check only when checkbox items are actual sub-issue links; plain-text
   checkbox items (e.g. `- [ ] step 1 product-discovery`, not a `#123` link) never auto-sync and
   must be hand-edited.

## Adopt / skip

- **Adopt**: declare the full step + parallel-group DAG up front, before any step runs
  (GitHub Actions pattern) — this repo's proposed plan block already does this.
- **Adopt**: treat "awaiting human" as a distinct, explicitly reported state per step (not
  merely "not yet checked") — carries into the acceptance criteria below.
- **Skip**: GitHub's native tasklist-block → sub-issue auto-tracking. It was deprecated in
  favor of sub-issues (Apr 2025), and even before that only auto-checked issue-linked items —
  this repo's steps are role branches under **one** issue, not separate linked issues, so the
  native mechanism doesn't fit this repo's issue-to-branch model. Confirms hand-parsing plain
  checkbox text (the issue's proposed direction) is the right-shaped primitive here, not a
  shortcut around a better-fitting native feature.

## Segment fit

This is an internal dev-orchestration tool for a single operator pair (user + orchestrator),
not a multi-team PM tool — so Jira/Linear's board-visibility-configuration failure modes
(hidden by swimlane/filter settings) are a weak signal here: this repo has no board filters to
misconfigure. GitHub Actions' single-pipeline-per-run shape is the closer analogue.

## Gap line

Current state already meets: parallel-group declaration and step ordering as prose (matches
the "declare the DAG up front" must-be, once requirement 1 is written). Currently missing: a
visible "awaiting human" state distinct from "not started" (flows[] has no such field today —
see survey), and the pre-merge visibility a plan needs (the requirement-4 gap the survey and
proposal address).

Sources:
- [about tasklists — GitHub Docs](https://docs.github.com/en/enterprise-server@3.14/get-started/writing-on-github/working-with-advanced-formatting/about-tasklists)
- [GitHub Issues & Projects – February 18th update](https://github.blog/changelog/2025-02-18-github-issues-projects-february-18th-update/)
- [Tasklist Feedback (private beta retirement) — community discussion #39106](https://github.com/orgs/community/discussions/39106)
- [Deployments and environments — GitHub Docs](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Deploying with GitHub Actions (required reviewers, "Waiting" status) — GitHub Docs](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments)
- [Editing an issue (edit history) — GitHub Docs](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/editing-an-issue)
- [How to get GitHub edit history via API — community discussion #33551](https://github.com/orgs/community/discussions/33551)
