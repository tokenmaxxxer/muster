#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
H="$HERE/../on-the-record/hooks"
pass=0; fail=0
report() { if [ "$2" = "$1" ]; then pass=$((pass+1)); printf 'ok     %-34s %s\n' "$3" "$2"; else fail=$((fail+1)); printf 'FAIL   %-34s want=%s got=%s\n' "$3" "$1" "$2"; fi; }

# manifest exists and wires the three hooks (the PR#10 regression)
python3 - "$H/hooks.json" <<'PY'
import json,sys
h=json.load(open(sys.argv[1]))["hooks"]
assert "SessionStart" in h and "UserPromptSubmit" in h and "PreToolUse" in h
print("ok     hooks.json wires SessionStart+UserPromptSubmit+PreToolUse")
PY
[ $? -eq 0 ] && pass=$((pass+1)) || fail=$((fail+1))

# directive injects on prompt, silent for role sessions
out=$(env -u CLAUDE_ROLE /bin/bash "$H/directive.sh" | head -1)
case "$out" in "[orchestrate]"*) report x x directive-injects ;; *) report inject none directive-injects ;; esac
lines=$(CLAUDE_ROLE=qa /bin/bash "$H/directive.sh" | wc -l)
[ "$lines" = 0 ] && report x x directive-silent-for-roles || report 0 "$lines" directive-silent-for-roles

guard() { # want name file_path board(yes/no)
  td="$(cd "$(mktemp -d)" && pwd -P)"; git init -q "$td"
  [ "$4" = yes ] && { mkdir -p "$td/docs/specs"; echo "- u" > "$td/docs/specs/approvers.md"; }
  printf '{"tool_name":"Write","tool_input":{"file_path":"%s","content":"x"},"cwd":"%s"}' "$td/$3" "$td" \
    | env -u CLAUDE_ROLE /bin/bash "$H/deliverable-guard.sh" >/dev/null 2>&1
  rc=$?; case "$rc" in 0) got=allow ;; 2) got=deny ;; *) got="exit-$rc" ;; esac
  rm -rf "$td"; report "$1" "$got" "$2"
}
guard deny  guard-docs-in-board      docs/issue-3/reports/product.md yes
guard deny  guard-src-in-board       src/app.py                      yes
guard deny  guard-tests-in-board     tests/test_app.py               yes
guard allow guard-approvers-ok       docs/specs/approvers.md         yes
guard allow guard-nonboard-repo      docs/notes.md                   no
guard allow guard-outside-trees      scratch/notes.md                yes

# issue #287 S4: an unparseable stdin payload must DENY, not silently ALLOW —
# a delivery failure on stdin is not evidence the write is safe.
guard_raw() { # want name payload
  printf '%s' "$3" | env -u CLAUDE_ROLE /bin/bash "$H/deliverable-guard.sh" >/dev/null 2>&1
  rc=$?; case "$rc" in 0) got=allow ;; 2) got=deny ;; *) got="exit-$rc" ;; esac
  report "$1" "$got" "$2"
}
guard_raw deny guard-empty-stdin      ''
guard_raw deny guard-non-json-stdin   'not json at all'
guard_raw deny guard-non-dict-json    '["a","b"]'
guard_raw deny guard-missing-file-path '{"tool_name":"Write","tool_input":{"content":"x"}}'

printf '\n== %d passed, %d failed ==\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
