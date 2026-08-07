#!/usr/bin/env bash
# Test for scripts/check-write-set-conflicts.sh.
# Exercises the sourceable functions directly against fixture proposal
# files, bypassing `gh pr list` (no network in tests) by building the
# "<issue>\t<proposal-file>" pairs file check_conflicts() consumes.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_root/scripts/check-write-set-conflicts.sh" --source-only

fail() { echo "FAIL: $1"; exit 1; }

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

# --- Fixture 1: overlapping paths, no resolution record -> expect non-zero,
# offending path in output.
mkdir -p "$work_dir/unresolved/docs/issue-901/proposals" \
         "$work_dir/unresolved/docs/issue-902/proposals"
cat > "$work_dir/unresolved/docs/issue-901/proposals/a.md" <<'EOF'
---
status: proposed
files:
  - src/shared/thing.py
  - docs/issue-901/reports/implementation.md
---
EOF
cat > "$work_dir/unresolved/docs/issue-902/proposals/b.md" <<'EOF'
---
status: proposed
files:
  - src/shared/thing.py
  - docs/issue-902/reports/implementation.md
---
EOF

cd "$work_dir/unresolved"
pairs_file="$(mktemp)"
printf '901\tdocs/issue-901/proposals/a.md\n902\tdocs/issue-902/proposals/b.md\n' > "$pairs_file"

set +e
output="$(check_conflicts "$pairs_file" 2>&1)"
status=$?
set -e
rm -f "$pairs_file"

[ "$status" -ne 0 ] || fail "unresolved overlap: expected non-zero exit, got $status"
echo "$output" | grep -q 'src/shared/thing.py' || fail "unresolved overlap: offending path missing from output ($output)"
echo "PASS: unresolved overlap detected"

# --- Fixture 2: same overlap, but a resolution record present -> expect
# exit 0.
mkdir -p "$work_dir/resolved/docs/issue-903/proposals" \
         "$work_dir/resolved/docs/issue-904/proposals" \
         "$work_dir/resolved/docs/issue-903/reports"
cat > "$work_dir/resolved/docs/issue-903/proposals/a.md" <<'EOF'
---
status: proposed
files:
  - src/shared/other.py
---
EOF
cat > "$work_dir/resolved/docs/issue-904/proposals/b.md" <<'EOF'
---
status: proposed
files:
  - src/shared/other.py
---
EOF
cat > "$work_dir/resolved/docs/issue-903/reports/implementation.md" <<'EOF'
---
loop_state: phase-2-complete
---
## Rationale for deviations
Overlap with issue #904 on src/shared/other.py resolved: this session narrowed its write set.
EOF

cd "$work_dir/resolved"
pairs_file="$(mktemp)"
printf '903\tdocs/issue-903/proposals/a.md\n904\tdocs/issue-904/proposals/b.md\n' > "$pairs_file"

set +e
output="$(check_conflicts "$pairs_file" 2>&1)"
status=$?
set -e
rm -f "$pairs_file"

[ "$status" -eq 0 ] || fail "resolved overlap: expected exit 0, got $status ($output)"
echo "$output" | grep -q 'RESOLVED' || fail "resolved overlap: expected RESOLVED marker in output ($output)"
echo "PASS: resolved overlap passes"

echo "ALL TESTS PASSED"
