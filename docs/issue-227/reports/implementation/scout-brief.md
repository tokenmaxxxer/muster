---
kind: scout-brief
subject: issue-227
date: 2026-08-03
---

# Scout brief — conditional-approval relay

Non-product surface: an internal governance/contract-text fix (approval-token
relay recipe), not a user-facing product. No category exemplar applies;
scouted the deliverable's own kind — mature bot/CI approval-signal
conventions — for how they keep "approved" unambiguous when conditional
feedback rides along.

## Must-bes (Kano)

- Approval must be an atomic, structurally separate signal from free-text
  rationale — never inferred from prose. GitHub's PR Review API keeps
  `state`/`event` (APPROVE/REQUEST_CHANGES/COMMENT) as a field distinct from
  the review `body`; the platform never parses body text for approval
  meaning. [Source: docs.github.com/en/rest/pulls/reviews]
- Conditional/blocking context gets its own separate channel, not a
  qualifier bolted onto the approval token. Kubernetes' Prow bot keeps
  `/approve` and `/lgtm` as separate commands, and uses a distinct `/hold`
  command (not a variant of `/approve`) when a PR looks good but must not
  merge yet — explicitly to avoid conflating "looks good" with
  "unconditionally ready." [Source: kubernetes.dev/blog/2022/12/12/prow-and-tide-for-kubernetes-contributors]

## Performance axes

- Parseability (string/state equality, zero ambiguity) vs. expressiveness
  (can the same utterance carry rationale) vs. round-trips (one comment vs.
  two). Both exemplars above choose parseability + a second channel over a
  single expressive-but-ambiguous one.

## Adopt / skip

- Adopt: split the approval signal from the conditional text into two
  distinct comments — mirrors both exemplars' separation and needs no new
  syntax.
- Skip: generalizing the string matcher (e.g. first-line-only match) to
  tolerate a single mixed comment. This project's own
  `docs/decisions/2026-07-29-permanently-closed-alternatives.md` already
  closed the entire "parse natural language for approval intent" class
  after three measured leaks — any matcher generalization reopens that
  surface, not a new one.

## Gap line

Current state already has a *structured* channel that mirrors the GitHub
exemplar exactly — `gates/flows.py`'s second `_pr_approved()` detection path
(a PR review Approve from a distinct approvers.md login) — but it only
exists for the hardened multi-account setup. The single-account default (PR
author = approver, and GitHub blocks self-review-approval) has no structured
channel at all, forcing the free-text issue-comment token — exactly where
issue #227's ambiguity originates. What's missing is a documented recipe for
carrying conditional feedback through that one remaining channel without
corrupting the token match.

## Segment fit

Two-person internal tool, not a mass product — the bar is "as disciplined as
Prow/GitHub's separation," not replicating their UI or labels.

## Method

1 sweep stage, 2 genuinely parallel `WebSearch` calls in one turn, 1 judge
point — the two hits agreed and directly answered the open design question
(separate-channel vs. smarter-parser), so deepening was not run (saturation
reached; no build decision would change with another round).

Sources:
- https://docs.github.com/en/rest/pulls/reviews
- https://www.kubernetes.dev/blog/2022/12/12/prow-and-tide-for-kubernetes-contributors/
