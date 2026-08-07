#!/usr/bin/env bash
# Detect overlapping frozen `files:` write-set claims between distinct
# issues that each currently have an open PR. See
# docs/specs/parallel-conflict-methodology.md for the methodology.
#
# Reusable: `source scripts/check-write-set-conflicts.sh` (or run with
# --source-only) loads the functions below without executing main — other
# scripts/roles (e.g. issue #324) consume parse_files_frontmatter and
# find_open_issue_proposals instead of writing a second `files:` parser.
set -euo pipefail

# parse_files_frontmatter <proposal-file>
# Prints one write-set path per line from the file's `files:` YAML-ish
# frontmatter list. Prints nothing if the file has no `files:` key.
parse_files_frontmatter() {
  local proposal_file="$1"
  awk '
    /^files:[[:space:]]*$/ { in_files = 1; next }
    in_files && /^[[:space:]]*-[[:space:]]+/ {
      line = $0
      sub(/^[[:space:]]*-[[:space:]]+/, "", line)
      gsub(/[[:space:]]+$/, "", line)
      print line
      next
    }
    in_files && /^[^[:space:]-]/ { in_files = 0 }
    in_files && /^---[[:space:]]*$/ { in_files = 0 }
  ' "$proposal_file"
}

# find_open_issue_proposals
# Prints "<issue-number>\t<proposal-file>" for every proposal belonging to
# an issue that currently has an open PR, one pair per line.
find_open_issue_proposals() {
  local open_issues
  open_issues=$(gh pr list --state open --json headRefName \
    --jq '.[].headRefName' 2>/dev/null \
    | grep -oE '^issue-[0-9]+' | grep -oE '[0-9]+' | sort -u)

  local issue_num proposal_file
  for issue_num in $open_issues; do
    for proposal_file in docs/issue-"$issue_num"/proposals/*.md; do
      [ -f "$proposal_file" ] || continue
      printf '%s\t%s\n' "$issue_num" "$proposal_file"
    done
  done
}

# has_resolution_record <issue-a> <issue-b>
# Returns 0 (found) if either issue's record names the other as resolved.
has_resolution_record() {
  local issue_a="$1" issue_b="$2"
  local record_a="docs/issue-${issue_a}/reports/implementation.md"
  local record_b="docs/issue-${issue_b}/reports/implementation.md"
  local conflict_a="docs/issue-${issue_a}/reports/conflict-${issue_b}.md"
  local conflict_b="docs/issue-${issue_b}/reports/conflict-${issue_a}.md"

  [ -f "$conflict_a" ] && return 0
  [ -f "$conflict_b" ] && return 0
  [ -f "$record_a" ] && grep -qE "issue #${issue_b}([^0-9]|\$)|issue-${issue_b}([^0-9]|\$)" "$record_a" && return 0
  [ -f "$record_b" ] && grep -qE "issue #${issue_a}([^0-9]|\$)|issue-${issue_a}([^0-9]|\$)" "$record_b" && return 0
  return 1
}

# check_conflicts <proposal-pairs-file>
# Reads "<issue>\t<proposal-file>" lines, computes pairwise path
# intersections across distinct issues, prints and returns non-zero on any
# unresolved overlap.
check_conflicts() {
  local pairs_file="$1"
  local found_unresolved=0

  local issues
  issues=$(cut -f1 "$pairs_file" | sort -u)

  local issue_a issue_b
  for issue_a in $issues; do
    for issue_b in $issues; do
      [ "$issue_a" -lt "$issue_b" ] 2>/dev/null || continue

      local files_a files_b overlap
      files_a=$(awk -F'\t' -v i="$issue_a" '$1==i{print $2}' "$pairs_file" \
        | while IFS= read -r f; do parse_files_frontmatter "$f"; done | sort -u)
      files_b=$(awk -F'\t' -v i="$issue_b" '$1==i{print $2}' "$pairs_file" \
        | while IFS= read -r f; do parse_files_frontmatter "$f"; done | sort -u)

      overlap=$(comm -12 <(printf '%s\n' "$files_a") <(printf '%s\n' "$files_b") | grep -v '^$' || true)

      if [ -n "$overlap" ]; then
        if has_resolution_record "$issue_a" "$issue_b"; then
          echo "RESOLVED: issue-${issue_a} and issue-${issue_b} share paths (resolution record found):"
          echo "$overlap" | sed 's/^/  /'
        else
          echo "CONFLICT: issue-${issue_a} and issue-${issue_b} claim overlapping paths with no resolution record:"
          echo "$overlap" | sed 's/^/  /'
          found_unresolved=1
        fi
      fi
    done
  done

  return $found_unresolved
}

main() {
  local pairs_file
  pairs_file="$(mktemp)"
  trap 'rm -f "$pairs_file"' EXIT
  find_open_issue_proposals > "$pairs_file"

  if [ ! -s "$pairs_file" ]; then
    echo "No open PRs with proposals found; nothing to check."
    exit 0
  fi

  check_conflicts "$pairs_file"
}

# Only run main when executed directly, not when sourced for its functions
# (the --source-only flag exists for callers that `bash -c` this file rather
# than `source` it).
if [ "${1:-}" = "--source-only" ]; then
  return 0 2>/dev/null || exit 0
fi
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main "$@"
fi
