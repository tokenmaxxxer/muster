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

## before-landing — stance 1: assume this change and another plugin's rule cancel each other

Verdict: NO FINDING
Seed: ledger/decisions.py, ledger/test_decisions.py (new files, ~230 lines) — before-landing dispatch for the decision-mining proposal
cap_seconds: 120
tier: default
diff_stat_lines: ~230
started_at: 2026-08-07T14:20:38+09:00
ended_at: 2026-08-07T14:26:00+09:00

Checked whether decisions.py's exit-1 behavior or normalization is cancelled by, or cancels, any other gate/hook reading the same reports files.
- No gate anywhere invokes ledger's decisions module or references it (grep across repo for "decisions.py" returns only the two new files). Not wired into CI, pre-commit, or .claude/hooks (empty). No consumer expects exit 0 from it.
- No gate forces a "What did not work / None." boilerplate for the sections scanned. gates/gates.py checks (record_wellformed, record_enums, record_fulfils_diff) only touch frontmatter/tool-residue, not section bodies; all roles/*.json record_fields are frontmatter enum fields (verdict, loop_state), not section-content mandates. The only record-fields-gate.sh found is inert template content under an unrelated rulebook-skeleton asset tree, unwired.
No reproducible cancellation/composition pair: there is no second party currently reading or gating on these files' content.
