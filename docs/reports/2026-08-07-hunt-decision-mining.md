---
proposal: docs/issue-322/proposals/2026-08-07-decision-mining.md
---

# Hunt record — decision-mining

## after-proposal — stance 0: assume the gate/mechanism just proposed is bypassable — find the bypass.

Verdict: NO FINDING
Seed: docs-only commit 2c27d14 adding docs/issue-322/proposals/2026-08-07-decision-mining.md, docs/issue-322/reports/implementation/survey.md, docs/issue-322/reports/implementation/scout-brief.md
cap_seconds: 60
tier: default
diff_stat_lines: ~100 (docs only)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:03:00Z

Notes: The proposal's confirmation step ("a docs/decisions/*.md file whose frontmatter or body cites the pattern's normalized key" discharges the recurrence) is plausibly gameable — nothing in the described mechanism distinguishes an operator-authored decisions/*.md entry from any agent trivially writing one containing the key text to silence the check. This is a real design concern worth flagging to the operator before build, but ledger/decisions.py does not exist yet (confirmed absent from ledger/), so there is no command to run and no observed wrong output to report. Per the reproduction requirement, this is reasoning about what might break, not a finding — recording NO FINDING.
