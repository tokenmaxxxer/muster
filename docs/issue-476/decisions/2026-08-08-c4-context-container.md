# C4 context/container — H1/H2 gate boundary (issue #476)

Companion diagram to [[2026-08-08-h1-h2-mechanism-adr]]. Scope: where the new
components sit relative to the existing role-session / gate-suite boundary
this repo already has (per survey: no gate executes anything today).

## Context

```mermaid
C4Context
  Person(role, "Role session", "Audited AI role producing a docs/issue-<n>/reports/<role>.md record")
  System(gateSuite, "Gate suite (gates/, landing_readiness.py)", "Merge-readiness aggregation the role session cannot write to")
  System_Ext(ci, "CI / PR merge event", "Reports the PR head commit SHA that triggers re-execution")
  Person(approver, "Human approver", "docs/specs/approvers.md account; reads gate verdicts before merge")

  Rel(role, gateSuite, "Stages record + commits (claim text, cited command)")
  Rel(ci, gateSuite, "Triggers gate run, reports head SHA")
  Rel(gateSuite, approver, "Verdict feeds landing_readiness pass/fail")
```

## Container — H1 re-execution path

```mermaid
C4Container
  Container(record, "Role record", "docs/issue-<n>/reports/<role>.md", "Claim text + cited command, authored by the audited session")
  Container(claimScan, "claim_scan.py", "gate step", "Regex-matches claim vocabulary; hard-fails on no-command or no-target-traceable command")
  Container(reexecGate, "reexecution_gate.py", "gate step, session-unwritable", "Creates SHA-pinned worktree, runs cited command, records exit code")
  ContainerDb(worktree, "Pinned worktree", "git worktree @ PR head SHA", "Fresh checkout the role session's own tool calls never touched")
  ContainerDb(verdict, ".reexecution/<issue>-<role>.json", "gate-owned artifact", "exit code, command, timestamp, SHA — session cannot edit")
  Container(landing, "landing_readiness.py", "existing aggregation", "Treats reexecution_gate fail like any other required-gate failure")

  Rel(record, claimScan, "read (diff-staged)")
  Rel(claimScan, reexecGate, "pass-through on claim+command+target found")
  Rel(reexecGate, worktree, "provision, pinned to CI-reported head SHA")
  Rel(reexecGate, verdict, "write (gate-owned, never session-owned)")
  Rel(verdict, landing, "verdict aggregated into merge gate")
```

## Boundary note

The only write edge into `.reexecution/*.json` originates inside
`reexecution_gate.py` itself, run as part of `landing_readiness.py`'s
aggregation — never as a commit the audited role session's own git history
contains. This is the diagrammed form of the incentive-independence argument
in the ADR: the box that produces the verdict and the box that is judged by
it are drawn as separate containers with no shared write path.
