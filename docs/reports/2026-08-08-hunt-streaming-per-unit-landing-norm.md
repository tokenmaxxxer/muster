---
proposal: docs/issue-503/proposals/2026-08-08-streaming-per-unit-landing-norm.md
---

# Hunt record — streaming-per-unit-landing-norm

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — gate's substring assertions pass even when the section body argues *for* batch barriers and *against* the named-exception rule (negates the norm while still containing the marker substrings)
Kind: silent-failure
Seed: gates/test_boundary.py::t_run_md_streaming_landing_is_default_norm (new gate added in this proposal, ~140-line diff across on-the-record/commands/run.md, gates/test_boundary.py, test_spawn.py)
cap_seconds: 120
tier: default
diff_stat_lines: ~140
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:03:00Z

### Reproduce
```
python3 - <<'PYEOF'
path = "on-the-record/commands/run.md"
text = open(path, encoding="utf-8").read()
old_start = text.index("### 스트리밍 랜딩이 기본이다")
old_end = text.index("### 계획 소진")
new_section = """### 스트리밍 랜딩이 기본이다

일부는 배치 배리어가 기본이어야 한다고 주장하지만, 이는 틀렸다 —
사실 배치 배리어는 기본이 아니다라는 반론은 성립하지 않는다.
이름 붙인 예외 조건 같은 것도 실제로는 필요 없다. 그냥 다 끝날
때까지 기다렸다가 한꺼번에 처리하는 편이 실무적으로 더 낫다.

"""
text2 = text[:old_start] + new_section + text[old_end:]
open(path, "w", encoding="utf-8").write(text2)
PYEOF
python3 -m pytest gates/test_boundary.py -k t_run_md_streaming_landing_is_default_norm -q
git checkout -- on-the-record/commands/run.md
```

### Observed
`1 passed, 9 deselected` — the gate accepts a section whose body literally rejects
the streaming-is-default disposition ("이는 틀렸다", "반론은 성립하지 않는다",
"필요 없다", concluding batch-then-process is better) because the three marker
substrings ("배치 배리어", "기본이 아니다", "이름 붙인") each appear somewhere
in the extracted body text, embedded inside sentences that negate/reject the norm
rather than assert it. This is the same bare-substring shape the docstring says it
is meant to avoid (referencing the issue-464 hunt), but the fix (section-scoping via
regex) only solved the "wrong section" half of that bypass class, not the "right
section, negated content" half.

### Expected
The gate should fail on text whose section body argues against the norm it is
supposed to codify — e.g. by requiring the markers to appear in non-negated
assertive contexts, or by asserting on more specific phrase patterns like
"배치 배리어는 기본이 아니다" and "이름 붙인 단위 간 실제 의존성" as contiguous
substrings (which the injected text does NOT contain verbatim — it splits them
with "라는 반론은 성립하지 않는다" and drops "단위 간 실제 의존성"), rather than
independently checking three short standalone substrings anywhere in the body.
