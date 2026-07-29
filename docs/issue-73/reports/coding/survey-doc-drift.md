# 이슈 #73 현재 상태 서베이 — v2 잔재 문서 드리프트

## 범위

이 문서는 이슈 #73("docs lag the code after the v3 migration")이 지목한, v2→v3
계약 마이그레이션 이후 코드는 옮겨졌지만 산문(prose)은 남겨진 세 항목을 측정한다.

1. `protocol.md` / `protocol.ko.md` 의 v2 잔재 서술.
2. `README.md:280` 의 존재하지 않는 `approve` 커맨드 광고.
3. `ledger/collect.py:26,69` 의 v2 주석.

이슈 본문의 4번째 항목(`docs/superpowers/` 를 6개 표준 버킷 위반으로 정리하고
`docs/decisions/` 로 소멸하지 않는 자산을 추출하는 작업)은 이번 서베이 태스크
지시(steps 1-5)에 포함되지 않아 정식으로 측정하지 않았다. 존재만 "미확정/판단
필요"에 기록해 둔다.

**v3 계약 원문의 소재.** 이슈 본문이 말하는 그대로, 계약 원문
`core/contract/role-handoff-contract.md` 은 `tokenmaxxxer-core` 레포에만 있고
이 레포(`muster`)에는 사본이 없다. `docs/specs/role-handoff-contract.md` 파일도,
`tokenmaxxxer-core` 디렉터리도 이 레포 트리에 존재하지 않는다(확인:
`find . -iname "role-handoff-contract*"` 무결과, `find . -iname
"*tokenmaxxxer-core*"` 무결과). 따라서 "v3 가 실제로 뭐라고 하는가"는 계약
원문 대신 이 레포 안에서 v3 에 맞춰 이미 갱신된 살아있는 근거로 재구성했다:

- `README.md:79-85` "v3 notes" 단락 — 보드 경로가
  `docs/issue-<n>/reports/<role>.md` 이고 `main`-머지분만 본다는 것, 계약
  원문은 `tokenmaxxxer-core` 에만 있고 레포는 사본을 갖지 않는다는 것,
  보드 마커가 `docs/specs/approvers.md` 라는 것, `spawn.py approve` 는
  사라졌다는 것을 이미 정확히 서술한다.
- `README.md:109-117` 의 9개 역할 표(product, ux-design, feasibility, coding,
  qa, review, verify, reflect, ops). 코드 근거는 `spawn.py:616-617` 의
  `ROLES = ("product", "ux-design", "feasibility", "coding", "qa", "review",
  "verify", "reflect", "ops")` — 정확히 9개.
- `spawn.py:1388-1390` — `a.role == "approve"` 분기가 `sys.exit`로 즉시
  종료하며 "v3: 승인은 파일 발행이 아니라 GitHub 행위다"라고 말한다.
- `ledger/collect.py:73` — 코드가 이미 `board.glob("issue-*/reports/
  review.md")`(즉 `docs/issue-*/reports/review.md`, v3 경로)를 글롭한다.
  `ledger/collect.py:126-127` 의 `report()` 출력도 이미 "v3 는
  docs/issue-<n>/reports/review.md 다"라고 v3 용어를 쓴다.
- `orchestrate/hooks/directive.sh:71-79`, `orchestrate/commands/run.md:106` —
  승인이 `APPROVED` PR 리뷰, 또는 정확히 `APPROVE issue-<n>/<role>` 문자열인
  코멘트라는 GitHub 행위임을 서술한다.
- `gates/gates.py:27-30` — `PROTECTED_ROOT_FILES` 에 `"protocol.md",
  "protocol.ko.md"` 가 들어 있어, 이슈의 "Both files are gate-protected root
  paths" 경고가 사실임을 확인한다.
- Bash 도구 실행 중 걸린 `board-gate.sh` 훅(플러그인 경로에서 실행되어 이
  레포 트리에는 파일이 없음)이 다음을 그대로 인용해준다: "docs/issue- is
  neither docs/README.md, one of the six standing buckets (_assets, decisions,
  handbooks, proposals, reports, specs), nor an issue tree (docs/issue-<n>/).
  (contract v3 s10)" — 이슈가 말한 6개 표준 버킷 목록과 정확히 일치한다.

**이전 리프레시 이력.** `docs/proposals/2026-07-27-muster-portability-and-doc-
refresh.md` 는 바로 이 두 파일(`protocol.md`/`protocol.ko.md`)을 대상으로 한
**이전** 문서 리프레시 제안서다(v1→v2 반영: "no rulebook has landed [contract
v2]"를 "all eight rulebooks have since landed board/contract v2"로 갱신하는
작업). 지금 두 파일에 남아 있는 "v2" 서술은 그 작업의 결과물이며, 그 뒤에 일어난
v2→v3 마이그레이션(토큰 폐지, 보드 경로 변경, 6→9 역할 등)이 아직 반영되지
않았다는 것이 이슈 #73 의 정확한 진단이다.

**네트워크 메모.** `gh` CLI 는 이 샌드박스에서 TLS 인증서 검증에 실패해
(`tls: failed to verify certificate: x509: OSStatus -26276`, `gh issue view`
및 `gh api` 양쪽 모두) 쓸 수 없었다. 대신 `curl -sS
https://api.github.com/repos/tokenmaxxxer/muster/issues/73`로 GitHub REST API
를 직접 호출해 이슈 본문을 받았다(같은 호스트에 대해 `curl`은 정상 동작).

## 현재 상태 (파일:줄 인용)

### 1. `protocol.md` / `protocol.ko.md` — 이슈가 지목한 자리

#### (1) 계약 권위 서술 — 폐지된 v2 사본 경로 + "역할 6개"

`protocol.md:44-47`:
> **`docs/specs/role-handoff-contract.md` (v2, `status: final`) is the authority
> here, not this document.** It lives in `review-agent-rulebook` and defines the
> shared record format for all six roles. What follows is only what muster needs
> in order to read the board; where the two disagree, the contract wins.

`protocol.ko.md:43-46`:
> **여기서의 권위는 이 문서가 아니라 `docs/specs/role-handoff-contract.md`
> (v2, `status: final`) 다.** `review-agent-rulebook` 에 있고 역할 6개의 공유 기록
> 형식을 정의한다. 아래는 muster 가 보드를 읽는 데 필요한 것만 추린 것이고, 둘이
> 어긋나면 계약이 이긴다.

v3 는 이렇게 말한다(위 근거): 계약 원문은 `core/contract/role-handoff-
contract.md` 하나로 `tokenmaxxxer-core` 에만 있고(`README.md:79-81` "the
canonical contract lives ONLY in tokenmaxxxer-core — repos carry no copy"),
역할은 9개다(`spawn.py:616-617`, `README.md:109-117`). `docs/specs/role-
handoff-contract.md` 라는 파일 자체가 이 레포에 존재하지 않는다(그렙 무결과).

#### (2) 보드 경로 — 폐지된 `docs/reports/records/<subject>/<role>.md`

`protocol.md:49-51`:
> The board is fully in-repo (contract §10): every role writes one status record
> at `docs/reports/records/<subject>/<role>.md`, inside doctrine's `reports`
> bucket. muster reads the frontmatter and nothing else.

`protocol.ko.md:48-50`:
> 보드는 전부 대상 레포 안에 있다(계약 §10). 각 역할이 상태 기록 하나를
> `docs/reports/records/<subject>/<역할>.md` 에 쓴다 — doctrine 의 `reports` 버킷
> 안이다. muster 는 frontmatter 만 읽는다.

v3 는 `docs/issue-<n>/reports/<role>.md`, `main`-머지분만이라고 말한다
(`README.md:79-80`, `ledger/collect.py:73` 의 실제 글롭 패턴). 보드 opt-in
마커는 `docs/specs/approvers.md`(`README.md:71,81-82`, `ledger`/`spawn.py`
에서는 `MARKER = "docs/specs/approvers.md"`, `spawn.py:619`).

같은 폐지된 경로가 이 두 파일 안에서 한 번 더 나온다(이슈가 명시하지 않은
동일 패턴의 반복): `protocol.md:96` / `protocol.ko.md:91`:
> `docs/reports/records/<subject>/qa.md` and `docs/reports/records/<subject>/qa/**`,
> the same place every other role's record lives.

#### (3) "역할 6개" → 9개

위 (1)의 인용문 안에 있는 것과 동일한 문장("all six roles" / "역할 6개")이다.
근거는 위 (1) 참고.

#### (4) §5 "Approval — tokens" — 폐지된 토큰 장치

`protocol.md:175-194` (섹션 전체):
> ## 5. Approval — tokens
>
> `qa-cycle`'s four human-only transitions (`Confirmed-Defect`, `Go`, `No-Go`,
> `Shipped-Under-Exception`) require a verdict token minted by `signoff`, and the
> token is consumed the moment it passes.
>
> What a token actually guarantees is not "a human did this" but **"an actor
> cannot mint its own approval."**
>
> **Whether an agent may ever hold that seat is settled elsewhere, and currently
> settled as no.** Contract §8 ("The human's seat") names four judgment points
> reserved for a human — minting or retiring a `subject`, the verdict tokens the
> contract reserves (qa's is-this-a-defect call), resolving cross-role disputes,
> and **approving scope changes**. warrant halting a headless coding run at
> `proposed → approved` is that clause being honoured, not a defect.
>
> > ⚠️ Moving any of those four to an agent is an amendment to the handoff
> > contract, decided there. muster must not route around it, and neither must a
> > single rulebook's hook. A proposal that tried exactly that was withdrawn on
> > 2026-07-26.

`protocol.ko.md:161-179` (섹션 전체, 위와 대응하는 한국어 원문 — 지면상 생략,
파일 참조).

v3 는 이렇게 말한다(위 근거): 토큰 장치는 통째로 삭제되었고, 승인은 GitHub
행위다 — `APPROVED` PR 리뷰, 또는 정확히 `APPROVE issue-<n>/<role>` 문자열인
코멘트를, `approvers.md` 에 등록된 로그인이 남기는 것
(`orchestrate/hooks/directive.sh:73`, `orchestrate/commands/run.md:106`).
1계정 기본 설정에서 이를 지키는 것은 `gh-guard`다(`README.md:45`,
`spawn.py:1283,1286`).

#### (5) 불변식 4 — "행위자가 자기 승인을 스스로 만들 수 없다"

`protocol.md:203-204`:
> 4. **An actor cannot mint its own approval.** Only a separate session in a
>    separate context can.

`protocol.ko.md:186`:
> 4. **승인은 행위자가 스스로 만들 수 없다.** 별도 세션·별도 컨텍스트에서만.

"mint"(발행)라는 동사 자체가 토큰 장치의 잔재다 — v3 에는 발행할 것이 없다
(이슈: "there is nothing left to mint").

#### (6) 출하 순서 5번 행 — "별도 컨텍스트가 발행한 토큰"

`protocol.md:221`:
> | 5 | an approving agent | a token minted by a separate context |

`protocol.ko.md:200`:
> | 5 | 승인 에이전트 | 토큰을 별도 컨텍스트가 발행 |

#### (7) §8 미확정 — WAKES-ON 감시자가 "아직 안 만들어졌다"

`protocol.md:225-229`:
> - **A WAKES-ON watcher** — contract §3 names "a future automated watcher, if one
>   is built" as the thing that could carry the table instead of a human. That is
>   muster's job, and it implements §3's table rather than inventing a schedule.
>   Now that all eight rulebooks have a board, this is buildable but not yet
>   built.

`protocol.ko.md:204-207`:
> - **WAKES-ON 감시자** — 계약 §3 이 "만들어진다면 미래의 자동 감시자"를 그 표를
>   사람 대신 짊어질 것으로 지목한다. 그게 muster 의 일이고, 일정을 지어내는 게
>   아니라 §3 의 표를 구현하는 것이다. 룰북 여덟 개 모두 보드가 생긴 지금은 만들
>   수 있지만, 아직 만들지 않았다.

이슈 본문: "`wakes.py` + `spawn.py drive` are that watcher"(이미 만들어졌다).
확인: `wakes.py` 가 존재하고(`wakes.py:2` "WAKES-ON 평가기"), `spawn.py:1391-
1396` 에 `a.role == "drive"` 분기가 `drive(a.cwd, a.unattended, a.limit)` 를
호출하며, `drive` 함수 정의는 `spawn.py:1093`에 있다. 다만 이것이 "완전히
built"인지(자동 스케줄러까지 포함하는지, 아니면 수동 호출 가능한 평가기+실행기
수준인지)는 코드 동작을 더 깊이 확인해야 한다 — 아래 "미확정" 참고.

#### 추가 잔재 — 이슈가 명시하지 않았지만 그렙으로 발견한 동일 패턴

`protocol.md:84` / `protocol.ko.md:80` (전이-상태 단락, 항목 (2)와 다른 자리):
> ...and as of 2026-07-27 **all eight rulebooks have landed it:
> every repository has a v2 board.**

> ...2026-07-27 현재 **룰북 여덟 개 모두 내려왔다 — 모든 레포에 v2 보드가
> 있다.**

"eight" 자체가 "역할 6→9"와 같은 숫자 갱신 누락 패턴이고("v2 board"라는 용어도
동일 계열의 잔재), `README.md:109-117` 의 9개 역할 표와 어긋난다.

`protocol.md:85-90` / `protocol.ko.md:81-85` (같은 단락의 나머지):
> muster reads the v2 board first and, if a
> given repo somehow still lacks one, falls back to the v1 locations
> (`review-record.md`, `feasibility-record.md`, `state.md`, `product-record.md`)
> — not to use them, but to say *"this repo has not moved to v2 yet"* instead of
> the flat "nothing in progress" that a v1 repo would otherwise get.

이 단락 전체가 "v2 가 현재판"이라는 틀로 쓰여 있는데, 지금은 v3 가 현재판이므로
용어가 한 단계 더 밀렸다.

### 2. `README.md:280` — 존재하지 않는 `approve` 커맨드

`README.md:280` ("Every command" 표 안):
> python3 spawn.py approve <kind> --subject <s> # mint an approval token yourself (needs a TTY)

바로 인접한 `README.md:277`:
> python3 spawn.py <role> "x" --unattended      # human absent: mint off, human gates stand

이 두 줄은 **같은 파일 안에서** `README.md:83`과 정면으로 모순된다:
> `spawn.py approve` is gone — approval is a GitHub act the orchestrator

**그렙으로 검증**: `approve`라는 토큰이 실행 가능한 커맨드/엔트리포인트로
존재하는지 `grep -rn "\bapprove\b" --include="*.py" --include="*.json"
--include="*.sh" .` 로 확인한 결과, 매치는 딱 두 줄이다.

`spawn.py:1388-1390`:
```
if a.role == "approve":
    sys.exit("v3: 승인은 파일 발행이 아니라 GitHub 행위다 — 오케스트레이터가\n"
             "  사용자와의 대화에서 gh pr review --approve / gh pr merge 로 중계한다.")
```

즉 `approve`는 **거부만 하는 분기**로만 존재한다 — README.md:280 이 광고하는
"mint an approval token yourself"라는 동작은 코드 어디에도 없다. `roles/`
디렉터리에도 `approve.json` 같은 역할 파일이 없다(`ls roles/` 확인, `grep -n
"approve" roles/*.json` 무결과). 이슈가 인용한 줄 번호는 `spawn.py:1353-1355`
인데, 실제로 찾은 위치는 `spawn.py:1388-1390`이다 — 이슈 작성 이후 파일이
편집되어 줄이 밀렸을 가능성이 있다(아래 "미확정" 참고).

### 3. `ledger/collect.py:26,69` — v2 주석, v3 코드

`ledger/collect.py:26`:
> # 계약 v2 의 보드 자리. subject 마다 한 판씩 있고, 전부 합쳐서 센다.

`ledger/collect.py:69` (`records()` 함수의 docstring):
> """셀 review 기록들의 레포 상대 경로. v2 를 먼저 보고, 없으면 v1 자리."""

그런데 같은 파일의 실제 코드(`ledger/collect.py:70-76`)는 이미 v3 경로를
글롭한다:
```
def records(repo: Path) -> list[str]:
    """셀 review 기록들의 레포 상대 경로. v2 를 먼저 보고, 없으면 v1 자리."""
    board = repo / BOARD
    if board.is_dir():
        found = sorted(str(p.relative_to(repo))
                       for p in board.glob("issue-*/reports/review.md") if p.is_file())
```
(`BOARD = "docs"`이므로 실제 글롭 대상은 `docs/issue-*/reports/review.md`,
즉 v3 보드 경로다.) 그리고 이 파일의 `report()` 함수(`ledger/collect.py:126-
127`)는 이미 올바르게 "v3" 라는 단어를 쓴다:
> ⚠ v1 자리({LEGACY})를 읽었다 — v3 는
> docs/issue-<n>/reports/review.md 다. 아직 안 옮긴 레포다.

즉 이 파일 안에서만도 "v2"(주석, 26·69행), "v1"(변수명 `LEGACY`, 정상),
"v3"(리포트 문구, 126행)가 뒤섞여 있고, 26·69행의 "v2"는 76행 코드가 실제로
글롭하는 경로 및 126행 리포트 문구와 어긋난다.

## 변경 대상 write set (예상)

| 위치 | 현재 | 변경안(예상) |
|---|---|---|
| `protocol.md:44-47` | "`docs/specs/role-handoff-contract.md` (v2, `status: final`) is the authority here, not this document.** It lives in `review-agent-rulebook` and defines the shared record format for all six roles." | "**The role-handoff contract (v3) is the authority here, not this document.** It lives only in `core/contract/role-handoff-contract.md` in `tokenmaxxxer-core` — repos carry no copy — and defines the shared record format for all nine roles." |
| `protocol.ko.md:43-46` | "여기서의 권위는 이 문서가 아니라 `docs/specs/role-handoff-contract.md` (v2, `status: final`) 다.** `review-agent-rulebook` 에 있고 역할 6개의 공유 기록 형식을 정의한다." | "**여기서의 권위는 이 문서가 아니라 인계 계약(v3) 이다.** `tokenmaxxxer-core` 의 `core/contract/role-handoff-contract.md` 에만 있고(레포에는 사본이 없다) 역할 9개의 공유 기록 형식을 정의한다." |
| `protocol.md:49-51` | "every role writes one status record at `docs/reports/records/<subject>/<role>.md`, inside doctrine's `reports` bucket." | "every role writes one status record at `docs/issue-<n>/reports/<role>.md`, `main`-merged only. The board opt-in marker is `docs/specs/approvers.md`." |
| `protocol.ko.md:48-50` | "각 역할이 상태 기록 하나를 `docs/reports/records/<subject>/<역할>.md` 에 쓴다 — doctrine 의 `reports` 버킷 안이다." | "각 역할이 상태 기록 하나를 `docs/issue-<n>/reports/<역할>.md` 에 쓰고, `main` 머지분만 본다. 보드 opt-in 마커는 `docs/specs/approvers.md` 다." |
| `protocol.md:96` | "`docs/reports/records/<subject>/qa.md` and `docs/reports/records/<subject>/qa/**`" | "`docs/issue-<n>/reports/qa.md` and `docs/issue-<n>/reports/qa/**`" |
| `protocol.ko.md:91` | "`docs/reports/records/<subject>/qa.md` 와 `docs/reports/records/<subject>/qa/**`" | "`docs/issue-<n>/reports/qa.md` 와 `docs/issue-<n>/reports/qa/**`" |
| `protocol.md:175` | "## 5. Approval — tokens" | "## 5. Approval — a GitHub act" |
| `protocol.ko.md:161` | "## 5. 승인 — 토큰" | "## 5. 승인 — GitHub 행위" |
| `protocol.md:177-182` | "require a verdict token minted by `signoff`... What a token actually guarantees is not \"a human did this\" but **\"an actor cannot mint its own approval.\"**" | "Approval is a GitHub act: an `APPROVED` PR review, or a comment that is exactly `APPROVE issue-<n>/<role>`, from a login in `docs/specs/approvers.md`. `gh-guard` keeps that honest in the default single-account setup. What that guarantees is not \"a human did this\" but **\"an actor cannot approve its own change.\"**" |
| `protocol.ko.md:163-168` | "`signoff` 가 발행한 verdict 토큰이 있어야 통과하고... **\"행위자가 자기 승인을 스스로 만들 수 없다\"**" | "승인은 GitHub 행위다: PR 의 `APPROVED` 리뷰, 또는 정확히 `APPROVE issue-<n>/<role>` 문자열인 코멘트를 `docs/specs/approvers.md` 에 등록된 로그인이 남기는 것. 1계정 기본 설정에서는 `gh-guard` 가 이를 지킨다. **\"행위자가 자기 변경을 스스로 승인할 수 없다\"**" |
| `protocol.md:203-204` | "4. **An actor cannot mint its own approval.** Only a separate session in a separate context can." | "4. **An actor cannot approve its own change.** Approval is a GitHub act — an `APPROVED` review or an `APPROVE issue-<n>/<role>` comment from a login in `approvers.md` — relayed by a separate session in a separate context." |
| `protocol.ko.md:186` | "4. **승인은 행위자가 스스로 만들 수 없다.** 별도 세션·별도 컨텍스트에서만." | "4. **행위자는 자기 변경을 스스로 승인할 수 없다.** 승인은 GitHub 행위(`APPROVED` 리뷰 또는 `approvers.md` 의 로그인이 남긴 `APPROVE issue-<n>/<role>` 코멘트)이고, 별도 세션·별도 컨텍스트가 중계한다." |
| `protocol.md:221` | "\| 5 \| an approving agent \| a token minted by a separate context \|" | "\| 5 \| an approving agent \| a GitHub approval (review/comment) relayed by a separate context \|" |
| `protocol.ko.md:200` | "\| 5 \| 승인 에이전트 \| 토큰을 별도 컨텍스트가 발행 \|" | "\| 5 \| 승인 에이전트 \| 별도 컨텍스트가 중계하는 GitHub 승인(리뷰/코멘트) \|" |
| `protocol.md:228-229` | "Now that all eight rulebooks have a board, this is buildable but not yet built." | "`wakes.py` plus `spawn.py drive` are that watcher — built, now that all nine rulebooks have a board." |
| `protocol.ko.md:206-207` | "룰북 여덟 개 모두 보드가 생긴 지금은 만들 수 있지만, 아직 만들지 않았다." | "`wakes.py` 와 `spawn.py drive` 가 그 감시자다 — 룰북 아홉 개 모두 보드가 생긴 지금, 이미 만들어졌다." |
| `protocol.md:84` | "as of 2026-07-27 **all eight rulebooks have landed it: every repository has a v2 board.**" | "as of 2026-07-27 **all nine rulebooks have landed it: every repository has a v3 board.**" |
| `protocol.ko.md:80` | "2026-07-27 현재 **룰북 여덟 개 모두 내려왔다 — 모든 레포에 v2 보드가 있다.**" | "2026-07-27 현재 **룰북 아홉 개 모두 내려왔다 — 모든 레포에 v3 보드가 있다.**" |
| `protocol.md:85-90` | "muster reads the v2 board first... to say \"this repo has not moved to v2 yet\"" | "muster reads the v3 board first... to say \"this repo has not moved to v3 yet\"" |
| `protocol.ko.md:81-85` | "muster 는 v2 보드를 먼저 읽고... \"이 레포는 아직 v2 로 안 옮겨졌다\"" | "muster 는 v3 보드를 먼저 읽고... \"이 레포는 아직 v3 로 안 옮겨졌다\"" |
| `README.md:280` | "python3 spawn.py approve <kind> --subject <s> # mint an approval token yourself (needs a TTY)" | 표에서 이 행을 삭제. (대체 문구를 남긴다면 "approval is a GitHub act — see README.md:79-85" 정도의 참조 각주.) |
| `README.md:277` | "python3 spawn.py <role> \"x\" --unattended      # human absent: mint off, human gates stand" | "mint off"가 실제로 무엇을 가리키는지 코드 확인 후 문구 교체 필요 — 미확정(아래) |
| `ledger/collect.py:26` | "# 계약 v2 의 보드 자리. subject 마다 한 판씩 있고, 전부 합쳐서 센다." | "# 계약 v3 의 보드 자리(docs/issue-<n>/reports/review.md). subject 마다 한 판씩 있고, 전부 합쳐서 센다." |
| `ledger/collect.py:69` | "\"\"\"셀 review 기록들의 레포 상대 경로. v2 를 먼저 보고, 없으면 v1 자리.\"\"\"" | "\"\"\"셀 review 기록들의 레포 상대 경로. v3 를 먼저 보고, 없으면 v1 자리.\"\"\"" |

## 미확정/판단 필요

- **§5 제목 및 문구의 정확한 대체 표현.** v3 계약 원문이 이 섹션 제목을
  뭐라고 부르는지(`"Approval — a GitHub act"`는 이번 서베이의 제안일 뿐,
  계약 원문에 대응하는 공식 표현이 있는지는 이 레포 안에서 확인할 수 없다 —
  원문이 `tokenmaxxxer-core`에만 있기 때문이다).
- **2026-07-26 철회된 제안서 언급**(`protocol.md:193-194`, `protocol.ko.md:
  178-179` "A proposal that tried exactly that was withdrawn on 2026-07-26")
  — 이 문장 자체는 토큰 언어가 아니라서 드리프트가 아닐 수 있지만, 그 제안서가
  지금도 유효한 참조인지, 아니면 v3 마이그레이션으로 이미 무의미해졌는지는
  확인하지 못했다.
- **`README.md:277` 의 "mint off"**가 `--unattended` 플래그의 실제 동작(코드
  상 무엇을 끄는지) 중 정확히 무엇을 가리키는지 `spawn.py`의 `--unattended`
  처리 로직을 더 깊이 읽어야 확정할 수 있다. 이번 서베이에서는 존재만
  확인했다.
- **`spawn.py:1388-1390`의 실제 줄 번호가 이슈 본문이 인용한 `spawn.py:1353-
  1355`와 다르다.** 이슈가 작성된 시점 이후 파일이 편집되어 8행 정도 밀렸을
  가능성이 있다 — 내용은 일치하므로(같은 `sys.exit` 메시지) 같은 자리를
  가리키는 것으로 보이지만, 확정은 이슈 작성 시점의 커밋을 대조해야 한다.
- **`wakes.py` + `spawn.py drive`가 "완전히 built"인지.** 함수/분기가
  존재하는 것은 확인했지만(`wakes.py:2`, `spawn.py:1093`, `spawn.py:1391-
  1396`), 자동 스케줄(cron 등) 없이 수동 호출(`spawn.py drive`)만 되는
  수준인지, 아니면 §3 미확정 항목이 요구하는 "자동 감시자" 수준까지
  갖췄는지는 이번 서베이의 그렙 확인을 넘어서는 판단이 필요하다.
  `protocol.md:230-232`/`protocol.ko.md:208-209`의 "What calls muster" 미확정
  항목("사람이 직접 / cron / 이슈 웹훅. 1~2 단계는 사람이 부르는 것으로
  충분하다")은 그대로 두어도 되는지, 아니면 이것도 갱신 대상인지 판단이
  필요하다.
- **`docs/superpowers/` 처리(이슈 4번 항목)는 이번 태스크 지시 범위 밖이라
  측정하지 않았다.** `ls docs/superpowers/` 확인 결과 디렉터리가 존재하며
  `docs/superpowers/plans/*.md`, `docs/superpowers/specs/*.md` 안에도
  `docs/reports/records`(v2 경로) 문자열이 남아 있다(그렙으로 발견). 이
  디렉터리를 이번 write set에 포함할지, `docs/decisions/` 신설과 함께 별도
  단계로 다룰지는 이 서베이가 결정할 수 없다 — 상위 판단이 필요하다.
- **repo 전역에 남아 있는 동일 계열 v2 잔재(참고용, 이번 write set 범위
  아님).** 이번 태스크의 명시적 대상은 `protocol.md`/`protocol.ko.md`,
  `README.md:280`, `ledger/collect.py:26,69` 세 곳뿐이지만, 그렙 중 같은
  패턴이 다른 파일에도 있는 것을 발견했다:
  - `spawn.py:620` — "# 계약 v1 이 쓰던 자리. 아직 v2 로 안 옮긴 레포를
    **말해주기 위해서만** 본다" (같은 파일 616-619행은 이미 v3 상수를 쓴다).
  - `wakes.py:2` — "\"\"\"WAKES-ON 평가기 — 계약 v2 §3 의 표를 기계로
    판정한다." (docstring 첫 줄, 이슈가 "그 watcher"라고 부르는 바로 그
    모듈).
  - `test_gates.py:21` — "\"\"\"계약 v2 §10 의 블랙보드를 만든다:
    docs/reports/records/<subject>/<역할>.md\"\"\"" (테스트 헬퍼 docstring).
  이 세 곳을 이번 write set에 포함할지는 상위 판단이 필요하다 — 태스크
  지시가 명시한 세 파일 밖이기 때문에 이번 문서에서는 "발견"으로만 기록한다.
