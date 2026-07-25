# 워커 격리 프로파일

프로파일 = **이미지 + 마운트 + egress + 토큰 스코프**. 라우터는 프로파일을 모른다 —
`adapters.yml` 의 명령 문자열이 통째로 담는다.

| 스테이지 | 이미지 | 마운트 | egress | 주입 토큰 |
|---|---|---|---|---|
| research | reader | `/in` ro | **웹 전체** (조사가 목적) | 없음 |
| plan | builder | 워크트리 rw | api.anthropic.com | 없음 |
| build | builder | 워크트리 rw | api + 패키지 레지스트리 | 없음 |
| review | reader | 워크트리 ro | api | 없음 |
| qa | prober | 테스트 대상 | 테스트 환경 | 테스트 전용 |
| diagnose | prod-ro | 없음 | 모니터링 API만 | 프로덕션 read-only |

fetch/write 분리가 이미지 경계로 표현된다: research 는 egress 가 가장 넓지만 write 와
크리덴셜이 0 이고, build 는 write 가 있지만 egress 가 좁다.

## 현재 구현 수준 (호스트 실행)

E2E 는 컨테이너 없이 호스트에서 돌았고, 격리는 두 겹이다:

1. `--safe-mode` — 플러그인·훅·CLAUDE.md·MCP 를 끈 워커. (아래 "왜 safe-mode 인가")
2. `GH_CONFIG_DIR` 을 빈 디렉터리로 교체 + `GH_TOKEN`/`GITHUB_TOKEN` 제거 →
   워커 안에서 `gh` 는 미인증. 실증:

```
$ env -u GH_TOKEN GH_CONFIG_DIR=$(mktemp -d) gh issue edit 1 --add-label pipeline:done
To get started with GitHub CLI, please run:  gh auth login
```

**한계**: 워커는 여전히 호스트 파일시스템과 네트워크에 닿는다. 무감독 실행
(사람 머지 게이트 제거)과 프로덕션 크리덴셜(diagnose)이 들어오는 시점에는
커스텀 컨테이너가 강제된다. 그때 `adapters.yml` 의 명령 앞에 `docker run` 이 붙고
라우터는 바뀌지 않는다.

## 왜 `--safe-mode` 인가

기본 실행은 설치된 tokenmaxxxer 스택 전체를 로드한다. 두 가지 문제가 있다.

1. **비용** — 플러그인·CLAUDE.md 가 매 워커마다 컨텍스트에 실린다. "PONG" 한 마디를
   시키는 데 $0.199 가 들었다. `--safe-mode` 로 같은 급의 호출이 $0.16 이하로 떨어진다.
2. **훅 교착** — `warrant` 는 앞단에 승인 게이트를 두고 그 밖의 편집을 거부한다.
   헤드리스에는 승인할 사람이 없으므로 build 워커가 그대로 막힌다.

즉 **룰북을 실행자로 쓰려면 warrant 의 승인 게이트가 spec 의 write-set 으로
충족되어야 한다.** 그 연결이 생기기 전까지 워커는 `--safe-mode` 로 돈다.
