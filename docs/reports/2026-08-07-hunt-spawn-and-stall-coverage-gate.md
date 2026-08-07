---
proposal: docs/issue-325/proposals/2026-08-07-spawn-and-stall-coverage-gate.md
---

# Hunt record — spawn-and-stall-coverage-gate

## before-landing — stance 0: assume the gate/check just touched is bypassable — find the bypass

Verdict: FINDING — when `gh issue list` fails, `gates/spawn_coverage.py` prints a warning to stderr but returns exit code 0 (success), the same code it uses for "no uncovered issues found" — so any CI step that gates only on exit code (as the docstring itself says: "종료 코드 0 (커버되지 않은 이슈 없음) / 1 (있음)") silently treats a broken `gh` call as a clean coverage run, defeating the whole point of the gate.
Kind: silent-failure
Seed: gates/spawn_coverage.py — `_list_open_issues` returns None on `gh` failure; `main()` does `if open_issues is None: print(...); return 0`
cap_seconds: 120
tier: default
diff_stat_lines: spawn.py +30/-1, test_gates.py +29, test_spawn.py +66, gates/spawn_coverage.py new (~90 lines)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:08:00Z

### Reproduce
```
mkdir -p .gate_test_bin
printf '#!/bin/bash\nexit 1\n' > .gate_test_bin/gh
chmod +x .gate_test_bin/gh
PATH=".gate_test_bin:/usr/bin:/bin" python3 gates/spawn_coverage.py --repo .
echo "EXIT_CODE=$?"
```

### Observed
```
스폰-커버리지: 이슈 목록을 읽을 수 없다 (gh 실패)
EXIT_CODE=0
```

### Expected
When `gh` fails to list issues (auth expired, rate-limited, network error, etc.), the gate cannot know whether uncovered issues exist and should fail loudly (non-zero exit, e.g. 2) rather than reuse the same exit code 0 as "coverage confirmed clean." As written, a broken `gh` invocation is indistinguishable from a passing gate to any CI step that checks only the exit code, which is exactly the silent-failure class this gate exists to prevent.
