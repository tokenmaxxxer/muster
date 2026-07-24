# orchestrator

tokenmaxxxer 룰북 에이전트들을 이벤트로 배차하는 라우터. 룰북이 아니라 프로그램이다.

라우터는 뇌가 없다 — 라벨을 읽고, 기계 게이트를 돌리고, 어댑터 표대로 실행자를
스폰하고, 산출물을 게시하고, 라벨을 옮긴다. **LLM 호출 0회.**

계약은 [`pipeline.md`](pipeline.md). 설계 근거(형식 결정·에이전트 분해·격리 등급)는
별도 노트 `orchestrator-design-2026-07.md` 에 있고 이 레포에 포함되지 않는다.

```
src/main.py      라우터 (폴링·락·스폰·게시·전이·stale 회수)
src/gates.py     기계 게이트 (writeset·deps)
adapters.yml     스테이지 → 실행자 표 (실제: Claude + Codex 크로스모델)
adapters.e2e.yml 같은 라우터, 결정론적 실행자 (E2E 시나리오용)
pipeline.md      라벨 상태기계·불변식·어댑터 작성 규칙
profiles/        워커 격리 프로파일
e2e/workers/     결정론적 스테이지 실행자
```

## 쓰기

```bash
python3 src/main.py bootstrap          # 라벨 생성 (최초 1회)
python3 src/main.py run                # 상시 구동
python3 src/main.py drain              # 파이프라인이 빌 때까지만 (E2E)
python3 src/main.py run adapters.e2e.yml   # 다른 어댑터 표로

python3 test_orchestrator.py           # 자체 점검 (네트워크·GitHub 불필요)
```

이슈에 `pipeline:plan` 라벨을 붙이면 파이프라인이 시작된다.
`STALE_SECONDS=8` 로 stale 회수 임계값을 덮어쓸 수 있다.

## 상태

E2E 검증 완료 (`tokenmaxxxer/orchestrator-e2e`):

- 실제 LLM 전 구간 — plan/build/qa = Claude, review = Codex(크로스모델),
  이슈 → spec → PR → 자율 머지 → 테스트 기록 → done
- 차단 경로 — 환각 패키지, 보호 경로, 계약 위반, 리뷰 기각 회귀, 루프 예산 소진,
  죽은 워커의 stale 락 회수
- 불변식 — 워커 환경에서 라벨 변경 시도가 인증 실패로 차단됨

미구현: research·diagnose 스테이지, 컨테이너 스폰, 뮤테이션 게이트.
