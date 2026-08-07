#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
H="$HERE/../on-the-record/hooks"
pass=0; fail=0
report() { if [ "$2" = "$1" ]; then pass=$((pass+1)); printf 'ok     %-34s %s\n' "$3" "$2"; else fail=$((fail+1)); printf 'FAIL   %-34s want=%s got=%s\n' "$3" "$1" "$2"; fi; }

run() { # $1 = last_assistant_message
  python3 -c 'import json,sys; print(json.dumps({"last_assistant_message": sys.argv[1]}))' "$1" \
    | env -u CLAUDE_ROLE /bin/bash "$H/stop-gate.sh"
}

# (a) approval-shaped, missing risk clause -> additionalContext names it
out="$(run 'Requesting approve for #411 — this will change stop-gate.sh.')"
case "$out" in *"risk/tradeoff statement"*) report x x missing-risk-clause-caught ;; *) report "risk/tradeoff statement" "$out" missing-risk-clause-caught ;; esac

# (b) approval-shaped, all three clauses present -> silent exit 0
out="$(run 'Requesting approve for #411 — this will change stop-gate.sh. Risk: a false positive could misfire on an unusual reply.')"
[ -z "$out" ] && report x x compliant-silent || report "" "$out" compliant-silent

# (c) non-approval-shaped -> pass-through, no output
out="$(run 'Here is a status update on the current task, nothing to approve.')"
[ -z "$out" ] && report x x non-approval-passthrough || report "" "$out" non-approval-passthrough

# CLAUDE_ROLE set -> pass-through regardless of content
out="$(printf '{"last_assistant_message":"approve #411 with no clauses"}' | CLAUDE_ROLE=qa /bin/bash "$H/stop-gate.sh")"
[ -z "$out" ] && report x x role-session-passthrough || report "" "$out" role-session-passthrough

echo "---"
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
