---
proposal: docs/proposals/2026-08-08-multi-axis-impact-classification.md
---

# Hunt record — multi-axis-impact-classification

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — scan_open_proposals()/batch_blocked() trust each proposal file's `status: proposed` frontmatter, but nothing updates that field when the proposal's implementation actually merges, so the target repo's own history has ~40 already-landed proposals still reading `status: proposed`, permanently tripping the batch-merge deny.
Kind: silent-failure
Seed: gates/risk_report.py (scan_open_proposals, batch_blocked, classify_axes), on-the-record/hooks/impact-guard.sh
cap_seconds: 180
tier: default (diff >200 lines / >5 files touched vs origin/main)
diff_stat_lines: (per dispatcher, default tier)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:20:00Z

### Reproduce
```
git log --oneline --all | grep -i "286/implementation"
# -> merge commit for the issue-286 implementation branch exists (already merged, PR #404)

head -5 docs/issue-286/proposals/2026-08-07-fix-event-cursor-integrity.md
# -> status: proposed   (still says "proposed" despite the merge above)

python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, "gates")
import risk_report
root = Path(".")
proposals = risk_report.scan_open_proposals(root)
print("open proposals found:", len(proposals))
blocked = risk_report.batch_blocked(proposals, root)
print("blocked count:", len(blocked))
print(blocked[0]["path"], blocked[0]["axes"]["reversibility"])
PY
```

### Observed
`scan_open_proposals()` returns 82 "open" proposals and `batch_blocked()` flags 40 of them at `reversibility=4` (AXIS_MAX), including the fix-event-cursor-integrity proposal whose implementation was merged long before this commit. Nothing in the repo (no gate, no merge-time hook, no test) flips a proposal's `status:` field from `proposed` to `landed`/`merged` when its PR lands, so `scan_open_proposals()` — and therefore `impact-guard.sh` — keeps treating dozens of long-closed proposals as currently open and high-reversibility. Since `batch_blocked` is non-empty essentially always in this repo's actual history, `on-the-record/hooks/impact-guard.sh` denies *every* batch of 2+ gh pr merge invocations unconditionally, not just when a genuinely open high-reversibility proposal exists — the guard's precondition ("this proposal is still open right now") is state the rule assumes but nothing in the codebase maintains.

### Expected
`batch_blocked()`/`scan_open_proposals()` should only ever surface proposals that are actually still open (unmerged), or the classifier and hook should treat `status: proposed` as authoritative only if something (a gate, CI check, or the merge flow itself) is responsible for flipping it on landing — otherwise the axis is graded off frontmatter nobody maintains, and the block fires independent of the real batch actual risk.
