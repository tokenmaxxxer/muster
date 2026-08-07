Subject: issue-322 — scout brief (1 sweep stage, parallel WebSearch x2, budget: well under 3min/5 stages, stopped at judge point 1 — saturated)

## Category
Not product-shaped; nearest comparable deliverable class: tools that convert recurring human-review feedback into checkable rules.

## Must-bes the field assumes
- Detection is over *recurring* text, not single instances — a rule is proposed only once the same correction fires more than once (the field's examples cite a concrete repeat threshold, e.g. "written on 12 PRs in 3 months").
- The mined artifact is a *draft* a human still turns into an enforceable check (lint rule / CI rule) — mining never self-installs as an enforced gate. This matches the issue's own "a mined pattern is a proposal to them, never a fact" constraint almost exactly.
- The loop closes into CI/PR-bot enforcement *after* human codification — mining alone (no downstream enforcement path) is treated as incomplete in every source found.

## Performance axes strong tools compete on
1. Precision of "recurring" (avoiding false patterns from superficially similar but substantively different corrections).
2. How cheaply a detected pattern converts to a runnable check (autofix/lint draft vs. a report a human must still hand-translate).
3. Traceability back to the source instances (a rule with no linked evidence is not trusted).

## Adopt / skip
- Adopt: draft-then-confirm shape — the mining step never installs a rule; it proposes a candidate with cited evidence (source PR/issue/session), and only the operator's own confirmation (e.g. a follow-up issue or ADR they approve) turns it into an enforced check. Mirrors this repo's existing APPROVE-string mechanism for phase-2 authorization — reuse that pattern rather than inventing a new confirmation channel.
- Skip: full LLM-fine-tuning / large paired-dataset approaches (Meta's 64k review-comment-pairs) — disproportionate to this repo's scale (one operator, dozens of issues) and outside what a phase-1-scoped proposal should commit to.

## Segment fit
This repo already has an analogous ledger (`ledger/collect.py`) that reads a structured record and computes objective, non-LLM metrics from git history. The mining tool for #322 is the same shape one layer up: read operator-authored text across issues/PRs instead of role verdict files, count recurrence, surface candidates — no LLM step required to satisfy the "recurring" detection axis mechanically (repeated normalized substrings/keywords is enough for a first mechanical pass).

## Gap line
Current state already meets: an evidence source exists and is git-durable (issue comments, PR reviews, `## What did not work` sections); an established human-confirmation channel exists (the APPROVE-string / PR-review protocol) that a mined-rule-confirmation step can reuse without inventing new ceremony.
Missing: any aggregation across that evidence; any recurrence count; any candidate-surfacing artifact; any check that fails when a correction repeats without a candidate having been surfaced.

## Mode used
Stage 1 sweep: 2 parallel WebSearch calls (angle: lint-rule-from-recurring-comment industry practice; angle: ADR/decision-log pattern-detection tooling). Judge point 1: results converged on the same shape (recurring → draft → human confirms → enforce) from independent angles — saturated, stopped after 1 stage.

Sources:
- https://factory.ai/news/using-linters-to-direct-agents
- https://medium.com/agoda-engineering/how-to-make-linting-rules-work-from-enforcement-to-education-be7071d2fcf0
- https://arxiv.org/pdf/2507.13499
- https://adr.github.io/adr-tooling/
- https://github.com/adr/ad-guidance-tool
