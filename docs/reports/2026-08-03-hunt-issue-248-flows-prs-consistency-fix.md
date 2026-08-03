# Hunt — issue #248 `flows[].prs`/`decision_queue` consistency fix (phase 2, before landing)

이 세션에도 `warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아
(available agent 목록에 `claude`/`Explore`/`freelunch:freelunch-worker`/
`general-purpose`/`Plan`/`statusline-setup`뿐, issue #216 헌트와 동일 상황),
`general-purpose` 에이전트에 고정 stance 프롬프트를 직접 넣어 대체
디스패치했다. stance 1개로 고정: "composition regression — 이번에 고친
`flows[].prs`가 같은 payload의 다른 필드(`decision_queue`,
`flows[].roles`, `hygiene.unapproved_open_prs`, `schema_version`)및
`flows-schema.md` 문서 계약과 어떻게 상호작용하는지 살피고, 각각은 맞는데
조합하면 틀리는 지점을 찾아라."

코드 리뷰 대상: 이 세션의 워킹 트리 diff — `gates/flows.py`(`prs_by_subject`
추가), `docs/specs/flows-schema.md`(§2.2 `prs` 설명 + 일관성 문단),
`test_spawn.py`(회귀 테스트 2건).

## Observed — 에이전트가 재현으로 확인한 1건

**FINDING (design-error)**: 이번 수정으로 `docs/specs/flows-schema.md`
§2.2에 내가 새로 쓴 문단의 "`decision_queue`와 `flows[].prs`가 결코
불일치하지 않는다" 주장이, **`flows[]`에 아예 엔트리가 없는 subject**에서는
성립하지 않는다 — `decision_queue`는 `all_subjects` 게이트 없이(issue
#216) 열린 PR을 전부 잡지만, `flows[]`는 여전히 `all_subjects`(board
레코드가 하나라도 있거나 `## 실행 계획` 블록이 있는 열린 이슈)로 게이트돼
있어(이번 수정이 건드리지 않은 부분), board 레코드도 계획 블록도 없는
subject의 PR은 `decision_queue`엔 뜨지만 `flows[]`엔 그 subject 자체가
없다 — "그 PR이 나타날 flows[].prs" 자체가 존재하지 않는다.

재현 (기존 회귀 테스트
`test_decision_queue_from_open_pr_with_no_board_record`의 픽스처를
`flows_payload()`에 직접 통과):

```python
import sys, tempfile
from pathlib import Path
sys.path.insert(0, '.'); sys.path.insert(0, 'gates')
import spawn, flows
root = Path(tempfile.mkdtemp())
spawn.ROOT = root
spawn._repo_slug = lambda root: 'acme/repo'
spawn._issue_comments = lambda root, n: []
spawn._roster_load = lambda: {}
flows._pr_list_all = lambda root: [dict(number=86, headRefName='issue-86/product-discovery',
                                        createdAt='2026-07-30T00:00:00Z', body='', reviews=[])]
flows._issue_list_all = lambda root: []
import closure_sweep
closure_sweep.find_violations = lambda root, subjects=None, issue_states=None: []
p = flows.flows_payload(root)
print('decision_queue:', p['decision_queue'])
print('flows:', p['flows'])
```

관측: `decision_queue`에 issue 86/PR 86 항목이 뜨지만 `flows: []` — issue
86의 `flows[]` 엔트리 자체가 없다. 문서 문단이 주장한 "결코 불일치하지
않는다"를 글자 그대로 읽으면 이 케이스에서 어긋난다.

## Disposition — 문서 문단 범위를 좁혀서 종결(write set 확장 아님)

이 결함은 코드 동작 결함이 아니라 **이번 phase-2 작업 중 내가 새로
작성한 문서 문장의 과잉 일반화**다 — 제안서가 요구한 것은
"decision_queue와 flows[].prs가 같은 PR에 대해 불일치하지 않음"(수용
기준 문구 그대로)이지 "모든 subject가 flows[]에 나타난다"가 아니다.
`flows[]` 자체의 `all_subjects` 게이트는 이번 이슈의 write set 밖(issue
#216에서 이미 결정된 기존 동작, 이번 제안의 Out of scope와도 일치)이므로
동작을 바꾸지 않고, `docs/specs/flows-schema.md` §2.2의 해당 문단을
"`flows[]`에 엔트리가 있는 subject에 한해" 성립하는 것으로 명시적으로
좁혀 고쳤다(같은 파일, 같은 섹션 — write set 안).

blocking finding 아님 — verify가 다르게 판단하면 재개봉 가능하다.
