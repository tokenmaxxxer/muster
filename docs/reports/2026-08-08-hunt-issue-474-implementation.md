---
proposal: docs/issue-474/proposals/2026-08-08-batch-d-provenance-and-recurrence-gates.md
---

# Hunt record — issue-474-implementation

## before-landing — stance 2: silent-empty on malformed input lets violations through

Verdict: FINDING — `check_accumulation_claim` (gates/accumulation.py, #424) returns `[]` (no violations) whenever the `work` path is not a git repository (or the git subprocess calls otherwise fail), even if the tree plainly contains a shape-1/shape-5 accumulation pattern — a fail-open on tool-call failure rather than fail-closed.
Kind: silent-failure
Seed: gates/accumulation.py (new in this batch, #424); diff touches gates/acceptance_gate.py, gates/accumulation.py, gates/ci.py, gates/gates.py, gates/repo_scope.py, spawn.py, plus tests (23 files, 1326+/341- per git diff --cached --stat origin/main)
cap_seconds: 180
tier: size:large (>200 lines / >5 files)
diff_stat_lines: 1326 insertions, 341 deletions across 23 files
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:10:00Z

### Reproduce
```
mkdir -p /tmp/scratch-nogit/roles
printf '{"a": 1}\n' > /tmp/scratch-nogit/roles/foo.json
python3 - <<'PY'
import sys
sys.path.insert(0, "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-474-implementation")
from pathlib import Path
from gates.accumulation import check_accumulation_claim
print(check_accumulation_claim(Path("/tmp/scratch-nogit"), "no accumulation section"))
PY
```

### Observed
`[]` — no violation reported, even though `roles/foo.json` matches shape 5 (`roles/*.json`) and the proposal body has no `## Accumulation` line. The function's own two `git` subprocess calls (`git diff --name-only HEAD` / `--cached`) both fail (non-zero return, not a git repo), so `changed` starts empty; the code's stated fallback for "empty diff" (`git ls-files`) *also* fails silently for the same reason, leaving `changed == []` and both shape-detectors trivially False. The docstring only advertises the fallback for the "committed, no working-tree diff" case — it does not distinguish "git succeeded and reports no changes" from "git failed to answer at all," and both collapse to the same silent `[]`.

### Expected
A failed `git` invocation (non-zero returncode, or `work` not being a git repository at all) should be treated as an inability to determine `changed`, and the gate should either raise/fail closed (produce a violation flagging that accumulation-shape detection could not run) rather than silently reporting no violations — consistent with the repo's own stated principle elsewhere in this same diff (gates/ci.py line ~489: "파싱 실패는 통과가 아니라 차단 사유다" — parse failure is a reason to block, not to pass).
