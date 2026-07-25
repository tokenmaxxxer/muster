# harness

tokenmaxxxer 의 하네스 — **역할별 환경으로 에이전트를 켜주는 것**.

배차 기사가 아니라 콘센트다. 상태는 각 에이전트가 갖고, harness 는 읽기만 한다.

```
protocol.md   규약 — harness 가 하는 일 셋, 상태 노출 계약, 격리
roles/        역할 하나 = 파일 하나. 플러그인 셋 + 샌드박스 경계
spawn.py      역할 환경으로 헤드리스 세션을 띄운다
gates/        결정론 검사. LLM 0회
ledger/       성적표
```

## 왜 필요한가

레포의 `.claude/settings.json` 을 고치면 그 레포에서 일하는 **모든** 에이전트에
적용된다. 코딩 에이전트가 QA 룰북까지 읽는다. 플러그인 스코핑의 경계는 **세션**
이므로, 역할마다 세션을 따로 띄우는 수밖에 없다. 그게 harness 다.

## 쓰기

```bash
python3 spawn.py review "PR 12 를 리뷰해라" -C ~/work/some-repo
python3 spawn.py qa "/testrun:testrun smoke"  -C ~/work/some-repo
python3 spawn.py coding "<spec.md 내용>"      -C ~/work/some-repo

python3 spawn.py review "x" --dry-run    # 합쳐진 설정만 본다
```

인증은 로그인된 것을 그대로 쓴다. 토큰도 시크릿도 필요 없다.

## 격리 — 컨테이너가 아니라 샌드박스

Claude Code 의 Bash 샌드박스가 우리가 필요한 것을 더 잘 준다. macOS 는 Seatbelt 라
설치할 것이 없다.

| 필요한 것 | 컨테이너(hosted CI) | Bash 샌드박스 |
|---|---|---|
| egress 통제 | **불가** (`--network` 미지원) | `network.allowedDomains` |
| 자격증명 격리 | 시크릿 명시 주입 | `credentials.envVars` 마스킹 + `injectHosts` |
| 파일시스템 경계 | 컨테이너 경계 | `filesystem.denyRead/allowWrite`, OS 강제 |
| 인증 | 별도 토큰 시크릿 필요 | **로그인된 것 그대로** |

## 실측으로 확인한 함정 셋

**① `--settings` 는 병합이지 교체가 아니다.** 역할 파일에 qa 플러그인만 적어도
사용자 전역 플러그인 17개가 딸려온다. `spawn.py` 가 전역 목록을 읽어 역할이 켜지
않은 것을 전부 `false` 로 덮는다. 이걸 안 하면 격리가 이름뿐이다.

**② 첫 스폰은 룰북 0개로 돈다.** 마켓플레이스를 등록만 하고 플러그인은 다음
실행부터 붙는다. 겉보기엔 성공이라 ablation 결과를 통째로 오염시킨다. `spawn.py`
가 `installed_plugins.json` 을 확인해 미설치면 **멈춘다**.

**③ 샌드박스는 기본이 fallback 허용이다.** 명령이 경계에 막히면 에이전트가 그대로
샌드박스를 끄고 다시 돌린다 — 실측에서 `denyRead` 로 막은 `~/.claude` 를 그렇게
읽어냈다. `spawn.py` 가 `allowUnsandboxedCommands: false` 를 강제한다.

**`CLAUDE_CONFIG_DIR` 로 통째 격리하지 않는 이유**: 설정은 완전히 갈리지만 macOS
키체인 항목이 설정 디렉터리에 묶여 있어 인증이 끊긴다. 인증을 그대로 쓰는 것이
샌드박스를 고른 이유이므로 그 이점을 버리지 않는다.

## 자체 점검

```bash
python3 test_orchestrator.py     # 게이트·순수함수
```

## 미해결

- **coding 룰북의 상태 노출** — 지금은 상태기계가 없다. `qa-cycle` 같은 승격이
  필요한지 미정.
- **승인자를 LLM 으로 바꾸는 결정** — `qa-cycle` 의 verdict 토큰은 사람 전용이다.
  토큰이 보장하는 성질은 "사람이 했다"가 아니라 "행위자가 자기 승인을 스스로 만들
  수 없다"이므로 별도 컨텍스트 에이전트로 바꿔도 성질은 살지만, 그건 룰북 소유자의
  결정이다. harness 가 우회해서는 안 된다.
- **harness 를 무엇이 부르는가** — 지금은 사람이 직접. 상시 프로세스를 만들지 않는다.

## 은퇴

`src/main.py`(라우터 데몬), `adapters*.yml`, `e2e/workers/`, `agents/`(CI 워크플로),
`images/`(컨테이너). 지우지 않고 두는 것은 실측 기록이기 때문이다 —
`orchestrator-design-2026-07.md` §9 참조.
