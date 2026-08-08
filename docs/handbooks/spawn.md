# spawn.py — self-hosted hook wiring

이슈 #508. `spawn.py` 가 자기 자신(on-the-record 레포)을 대상으로 역할
세션을 띄울 때, 컨슈머 설치 경로에서 나가는 `on-the-record/hooks/hooks.json`
을 그 세션에도 켠다.

## 왜 필요했나

`on-the-record/hooks/hooks.json` 은 마켓플레이스로 설치한 컨슈머 세션에는
`--plugin-dir` 을 통해 켜지지만, on-the-record 자신의 레포에는 체크인된
`.claude/settings.json` 이 없어 이 저장소를 대상으로 한 역할 세션에서는
계속 inert 였다 — preflight/가드/stop-gate 전부 안 붙는 채로 이 저장소
자신의 커밋이 돌아갔다는 뜻이다.

## 왜 체크인된 `.claude/settings.json` 이 아니라 spawn-time 병합인가

`spawn.py:require_no_repo_config()` 는 스폰 **대상** 레포가 자기
`.claude/settings.json`/`.claude/hooks`/등을 들고 있으면 멈춘다 —
그 파일의 훅은 스폰이 선언한 `sandbox.filesystem` 경계를 받지 않고 전체
사용자 권한으로 돈다(2026-07-27 실측 사고). on-the-record 는 자기 자신을
대상으로 스폰할 때마다 정확히 이 "대상 레포가 자기 설정을 들고 있다" 케이스가
되므로, 체크인된 파일로 풀면 그 정지를 매번 트립시키고 매번 신뢰 고정이
필요해진다. 대신 `role_settings()` 가 이미 만드는 `--settings` 임시 파일에
직접 병합해 넣는다 — `require_no_repo_config` 가 보는 파일시스템 표면을
전혀 건드리지 않는다.

## 동작

- `spawn.self_hosted_hooks(cwd)`: `<cwd>/on-the-record/hooks/hooks.json`
  이 존재하면 그 `"hooks"` 값을 읽고, `${CLAUDE_PLUGIN_ROOT}` 를
  `<cwd>/on-the-record` 로 치환해 돌려준다. 없으면 `None`.
  (컨슈머 설치 경로에서는 Claude CLI 가 `--plugin-dir` 로 이 변수를
  채우지만, 여기서는 그 경로로 로드하지 않으므로 spawn.py 가 직접 치환한다.)
- `spawn.role_settings(role, cwd=None)`: `cwd` 가 self-hosted 대상으로
  판정되면(위 함수가 `None` 이 아닌 값을 돌려주면) 반환하는 설정 dict 에
  `"hooks"` 키를 추가로 얹는다. 다른 모든 대상 레포에는 아무 변화 없음
  (additive, opt-in by target detection).
- 두 호출부(`main()` 의 `--dry-run` 경로, `_spawn_one()`) 모두 `cwd` 를
  넘긴다.

## 정합성 보장

`gates/test_hooks_parity.py` 가 `on-the-record/hooks/hooks.json` 의 모든
(event, matcher, script) 삼중항이 `self_hosted_hooks()` 출력에 그대로
있는지 매 실행마다 대조한다 — 손으로 유지하는 두 번째 목록이 아니라
hooks.json 자체를 읽어 낸다. 같은 파일이 실제 git 저장소에서 `git commit`
시도를 살려/거부하는 live-fire red/green 페어도 돈다.

```
python3 gates/test_hooks_parity.py
```
