---
proposal: docs/issue-93/proposals/coding.md
---

# Hunt record — role-model-builtin-sonnet-default

## after-proposal — stance 1: silent failure / composition regression from resolved_role_model() now always non-empty

Verdict: FINDING — README.ko.md still documents the pre-#93 behavior ("두 계층 모두에서 비어 있거나 공백뿐인 값은 미설정과 동일하게 처리한다... `--model` 플래그 없음, 오늘의 기본값" / "기본은 미설정 — 이 경우 역할 세션은 CLI 기본 모델로 돈다"), which now contradicts spawn.py's actual behavior (always attaches `--model sonnet`). The English README.md was updated for issue #93 but README.ko.md was not, so the Korean docs now silently describe a code path that no longer exists.
Kind: silent-failure
Seed: spawn.py resolved_role_model() diff (env > config > built-in "sonnet"), README.md precedence sentence updated around line 88-100; README.ko.md not touched by the change.

### Reproduce
```
grep -n "우선순위\|미설정\|role_model" README.ko.md | sed -n '1,10p'
python3 -m unittest test_spawn.SpawnCmd.test_role_model_unset_uses_builtin_default -v
```

### Observed
README.ko.md line ~90-95:
"우선순위는 `MUSTER_ROLE_MODEL`(env) > `role_model.txt`(config) > 없음이다: ... 두 계층 모두에서 비어 있거나 공백뿐인 값은 미설정과 동일하게 처리한다(`--model` 플래그 없음, 오늘의 기본값)."
and line ~84-85: "기본은 미설정 — 이 경우 역할 세션은 CLI 기본 모델로 돈다."

Meanwhile the passing test confirms current code behavior: with MUSTER_ROLE_MODEL unset and no role_model.txt, spawn_cmd() now always includes `--model sonnet` in argv — the Korean doc's claimed "없음" (no `--model` flag) terminal case is gone from the code but still asserted in README.ko.md.

### Expected
README.ko.md's precedence description should match README.md's updated precedence (`MUSTER_ROLE_MODEL` (env) > `role_model.txt` (config) > `sonnet` (built-in default)), with the "미설정 시 --model 플래그 없음" claim removed, since it no longer holds.
