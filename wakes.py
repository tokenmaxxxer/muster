#!/usr/bin/env python3
"""WAKES-ON 평가기 — docs/specs/wake-routing.md 의 표를 기계로 판정한다.

이 파일이 그 감시자다: "WAKES-ON tells the human (**or a future automated
watcher, if one is built**) *whom* to open." **일정을 지어내지 않는다** —
docs/specs/wake-routing.md 의 표 아홉 줄이 전부다.

아홉 줄 중 일곱만 기계로 판정된다. 나머지 둘은 그 문서가 판단으로 적은
것이고, mechanical checks 는 substantive checks 가 아니라는 구분을 지킨다.
표 밖의 간선 둘은 그 문서가 **자동화를 금지**했으므로 아예 판정하지 않는다.

  기계 판정 가능        feasibility, coding, qa, review, ux-design, verify, reflect
  판단이 필요           product ("content questions the acceptance criteria")
                        ops    ("ready to roll out")
  자동화 금지           finding 해소 재검증, 라운드 종료 게이트

**판정 불가를 "안 깨어남"으로 보고하지 않는다.** 그 둘은 정반대 처분을 받아야
한다.

finding 되돌이 간선: docs/specs/wake-routing.md 는 이 파일이 이미 실제로
하는 일 그대로 이 결정을 적어 둔다 — 어느 역할이든 자기 앞으로 온 finding 에
깨어난다. 표만 따르면 coding 외의 역할에게 온 finding 은 아무도 안 본다.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

import spawn

# docs/specs/wake-routing.md 가 기계로 못 재는 두 줄. 왜 못 재는지를 같이 들고 다닌다.
JUDGEMENT = {
    "product": "qa/review 결과가 합의된 수용 기준을 흔드는가 — 내용 판단이다",
    "ops": "머지된 변경이 '내보낼 준비가 됐는가' — 판단이다",
}
# docs/specs/wake-routing.md 가 표 밖에 둔 두 간선. 본문이 **"human-consulted, never automated"** 라고
# 직접 못박았으므로 기계가 판정해서는 안 된다. 못 재는 것과 성격이 다르다 —
# 이쪽은 **재면 안 되는 것**이다.
HUMAN_ONLY = {
    "finding 해소 후 재검증": "blocking finding 을 올린 역할이 findings-resolved 에 "
                              "다시 깨어난다. 자동화를 금지한다",
    "라운드 종료 가치 게이트": "candidate-round-done 이 사람을 깨워 게이트 "
                               "둘을 돌린다. 자동화를 금지한다",
    "사전 승인 게이트": "front record 가 scope-proposed 에 닿으면 사람이 읽고 "
                        "scope-approved 로 올린다. 그 상태로 가는 **유일한** "
                        "경로이고, 어떤 역할도 자기 것이든 남의 것이든 승인하지 못한다",
    "conditional 검증 재확정": "feasibility 의 verdict: conditional 이 사람의 "
                                "결정(PR Approve 또는 APPROVE 댓글, "
                                "docs/specs/approvers.md)으로 풀리면 feasibility "
                                "자신이 verdict 를 go 로 다시 쓴다. wakes.py 는 "
                                "GitHub PR/댓글 상태를 읽지 않으므로 이 재기록은 "
                                "자동화되지 않는다 — docs/specs/wake-routing.md "
                                "'Conditional verdict resolution' 참고",
}
UPSTREAM = re.compile(r"^\s*-\s*path:\s*(\S+)", re.M)
UP_SHA = re.compile(r"^\s*sha:\s*(\S+)", re.M)


class Row(NamedTuple):
    """깨어난 줄 하나. `key` 는 그 줄의 신원이고, `sig` 는 그 줄이 **근거로 든
    상태**의 해시다.

    계약 §6 은 "wake 는 그 결과 기록이 쓰여야 소비된다"고 말한다. 그 문장을
    기계로 옮기면: 어떤 역할을 띄웠고 그 세션이 보드를 실제로 바꿨으면, 그때
    서 있던 줄들의 sig 를 적어 둔다. 다음 평가에서 sig 가 그대로면 같은 근거가
    두 번 깨우지 않고, 근거가 바뀌면 다시 깨운다.

    이게 없으면 조건들이 **래치**된다 — verdict: go 가 기록에 남아 있는 한
    coding 이, loop_state: landed 가 남아 있는 한 review 가 영원히 깨어난다.
    qa 줄이 가장 심한데, src/ 를 건드린 커밋이 하나라도 있는 레포에서는 무조건
    선다(실측 2026-07-27).
    """
    role: str
    why: str
    key: str
    sig: str


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def _sig(root: Path, *rels: str) -> str:
    """근거가 된 파일들의 내용 해시. 없는 파일은 없다는 사실 자체가 근거다."""
    h = hashlib.sha256()
    for rel in rels:
        p = root / rel
        h.update(rel.encode())
        try:
            h.update(hashlib.sha256(p.read_bytes()).digest())
        except OSError:
            h.update(b"\0absent")
    return h.hexdigest()[:16]


def _rec(subject: str, role: str) -> str:
    return f"{spawn.BOARD}/{subject}/reports/{role}.md"


def observed_path(cwd: str) -> Path:
    """관찰 기록은 **on-the-record 안에** 산다. 대상 레포는 읽기 전용이다(규약 §1).

    경로로 키를 잡는다 — 슬러그만 쓰면 이름이 같은 두 레포가 서로의 소비
    기록을 지운다.
    """
    root = Path(cwd).resolve()
    tag = hashlib.sha256(str(root).encode()).hexdigest()[:8]
    return spawn.ROOT / "runs" / "observed" / f"{spawn.slug(cwd)}-{tag}.json"


def observed(cwd: str) -> dict[str, str]:
    try:
        return json.loads(observed_path(cwd).read_text())
    except (OSError, ValueError):
        return {}


def consume(cwd: str, rows: list[Row]) -> None:
    """이 줄들이 답해졌다고 적는다. **보드가 실제로 바뀐 뒤에만** 부른다 —
    §6 은 wake 가 결과 기록으로 소비된다고 말하지 띄우는 것으로 소비된다고
    말하지 않는다."""
    if not rows:
        return
    p = observed_path(cwd)
    seen = observed(cwd)
    seen.update({r.key: r.sig for r in rows})
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(seen, indent=1, sort_keys=True, ensure_ascii=False))
    except OSError:
        pass          # 관찰 기록을 못 써도 보고는 계속된다 — 중복이 안전한 쪽이다


def fresh(cwd: str) -> tuple[list[Row], list[Row]]:
    """(아직 안 답해진 줄, 이미 답해진 줄). 억제된 줄도 **세어서 보고한다** —
    조용히 사라지는 것이 이 레포가 가장 싫어하는 실패다."""
    seen = observed(cwd)
    rows, _ = _rows(cwd)
    new = [r for r in rows if seen.get(r.key) != r.sig]
    old = [r for r in rows if seen.get(r.key) == r.sig]
    return new, old


def _head_sha(root: Path, path: str) -> str:
    """path 를 마지막으로 건드린 커밋 — 계약 §12 가 staleness 를 재는 방식."""
    return _git(root, "log", "-1", "--format=%H", "--", path)


def upstream(record: Path) -> dict[str, str]:
    """기록의 `upstream:` 목록을 path → sha 로 읽는다.

    frontmatter 의 중첩 블록이라 spawn.frontmatter() 의 평면 파서로는 안 잡힌다.
    """
    try:
        text = record.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)
    if len(block) < 3:
        return {}
    out, cur = {}, None
    for line in block[1].splitlines():
        m = UPSTREAM.match(line)
        if m:
            cur = m.group(1)
            out[cur] = ""
            continue
        s = UP_SHA.match(line)
        if s and cur:
            # acknowledged_sha 가 있으면 그쪽이 최신 확인점이다 (§12)
            out[cur] = out[cur] or s.group(1)
    return out


def _hypotheses(root: Path) -> list[Path]:
    # v3: per-subject proposals live inside each issue tree.
    out = []
    docs = root / "docs"
    if not docs.is_dir():
        return []
    for d in sorted(docs.glob("issue-*/proposals")):
        out += [p for p in sorted(d.glob("*.md"))
                if spawn.frontmatter(p).get("kind") == "hypothesis"]
    return out


def _findings_to(root: Path, role: str) -> list[str]:
    """`finding` 은 다른 역할 기록의 **본문 안에** 인라인으로 산다 (§2 표,
    docs/specs/wake-routing.md 의 finding 되돌이 간선).
    frontmatter 가 아니므로 본문 전체를 봐야 한다."""
    recs = root / spawn.BOARD
    if not recs.is_dir():
        return []
    hits = []
    for f in sorted(recs.glob("issue-*/reports/**/*.md")):
        try:
            text = f.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if re.search(rf"^\s*addressed_to:\s*{re.escape(role)}\s*(#.*)?$", text, re.M):
            hits.append(str(f.relative_to(root)))
    return hits


def _front(root: Path, subject: str, roles: dict) -> str | None:
    """그 subject 의 front record — subject 를 처음 연 역할 (§9, 첫 빌드 승인 게이트).

    §1 이 체인 루트를 `upstream: []` 로 정의하므로 그게 기계적 판별이다. 못 가리면
    docs/specs/wake-routing.md 가 적은 통상 순서(product, 아니면 feasibility)로
    물러난다.
    """
    rootless = [r for r in roles
                if not upstream(root / spawn.BOARD / subject / "reports" / f"{r}.md")]
    if len(rootless) == 1:
        return rootless[0]
    for r in ("product", "feasibility"):
        if r in roles:
            return r
    return None


def evaluate(cwd: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]],
                                list[tuple[str, str]]]:
    """(깨어난 역할, 판정 불가한 줄, 승인 게이트에 막힌 줄). **아무것도 쓰지 않는다.**

    소비 기록을 보지 않는 순수 평가다 — 보드가 지금 무엇을 말하는가만 답한다.
    이미 답해진 줄을 걸러낸 것이 필요하면 fresh() 를 쓴다.
    """
    woken, blocked = _rows(cwd)
    return ([(r.role, r.why) for r in woken], sorted(JUDGEMENT.items()),
            [(r.role, r.why) for r in blocked])


def _rows(cwd: str) -> tuple[list[Row], list[Row]]:
    """(깨어난 줄, 승인 게이트에 막힌 줄) — 각 줄이 무엇을 근거로 들었는지까지."""
    root = Path(cwd).resolve()
    b = spawn.board(root)
    woken: list[Row] = []
    blocked: list[Row] = []

    # ── feasibility: 새롭거나 바뀐 hypothesis 가 보드에 나타남
    feas_records = [(root / spawn.BOARD / s / "reports" / "feasibility.md")
                    for s, r in b.items() if "feasibility" in r]
    acked = {p: sha for rec in feas_records for p, sha in upstream(rec).items()}
    for h in _hypotheses(root):
        rel = str(h.relative_to(root))
        if rel not in acked:
            woken.append(Row("feasibility",
                             f"hypothesis {rel} — feasibility 가 아직 안 읽었다",
                             f"feasibility|{rel}", _sig(root, rel)))
        elif acked[rel] and acked[rel] != _head_sha(root, rel):
            woken.append(Row("feasibility", f"hypothesis {rel} 가 기록된 sha 이후 바뀜",
                             f"feasibility|{rel}", _sig(root, rel)))

    # ── 사전 승인 게이트 (docs/specs/wake-routing.md). coding 의 **첫 빌드
    #    진입**에만 붙는다. 네 갈래 전부에 얹히는 전제조건이지 다섯 번째 갈래가
    #    아니다 — 병렬 간선으로 두면 기존 갈래들이 저 혼자 첫 빌드를 깨워 게이트가
    #    무력해진다(그 문서가 이 함정을 명시적으로 지목한다). 이미 빌드에 들어간
    #    subject 의 재깨움은 게이트 밖이다.
    def wake_coding(subject: str, why: str, cites: str) -> None:
        roles = b[subject]
        key, sig = f"coding|{subject}|{cites}", _sig(root, cites)
        if "coding" in roles:
            woken.append(Row("coding", f"{subject}: {why}", key, sig))
            return
        f = _front(root, subject, roles)
        state = roles.get(f, {}).get("loop_state") if f else None
        # vocab source of truth: docs/specs/loop-state-vocab.md — human-only allowlist
        if state == "scope-approved":
            woken.append(Row("coding", f"{subject}: {why}", key, sig))
        else:
            blocked.append(Row("coding",
                               f"{subject}: {why} — 그러나 첫 빌드다. front record"
                               f"({f or '없음'}) 가 {state or '없음'} 이라 승인 게이트가 막는다",
                               key, sig))

    # ── coding: 세 갈래 중 하나만 서도 깨어난다
    for subject, roles in b.items():
        # exact-match by design: compound/annotated strings are refused, not parsed.
        # resolution path for a settled "conditional" -> "go" re-raise: docs/specs/wake-routing.md#conditional-verdict-resolution
        # vocab source of truth: docs/specs/loop-state-vocab.md (feasibility: verdict)
        if roles.get("feasibility", {}).get("verdict") == "go":
            wake_coding(subject, "feasibility verdict: go", _rec(subject, "feasibility"))
        # vocab source of truth: docs/specs/loop-state-vocab.md (qa: loop_state)
        if roles.get("qa", {}).get("loop_state") == "handed-off":
            wake_coding(subject, "qa handed-off — 사람의 결함 판정이 끝났다",
                        _rec(subject, "qa"))

    # ── ux-design: 새롭거나 바뀐 product-record (체인 루트면 hypothesis)
    for subject, roles in b.items():
        if "product" in roles and "ux-design" not in roles:
            woken.append(Row("ux-design",
                             f"{subject}: product-record 가 있고 ux-design 기록이 없다",
                             f"ux-design|{subject}|product",
                             _sig(root, _rec(subject, "product"))))

    # ── coding 의 네 번째 갈래: ux-design-record 가 reviewed 에 도달
    for subject, roles in b.items():
        # vocab source of truth: docs/specs/loop-state-vocab.md (ux-design: loop_state)
        if roles.get("ux-design", {}).get("loop_state") == "reviewed":
            wake_coding(subject, "ux-design loop_state: reviewed",
                        _rec(subject, "ux-design"))

    # ── verify: coding 과 qa 가 **둘 다** 산출물을 낸 subject (첫 깨움)
    for subject, roles in b.items():
        if "coding" in roles and "qa" in roles and "verify" not in roles:
            woken.append(Row("verify", f"{subject}: coding 과 qa 가 둘 다 기록을 냈다",
                             f"verify|{subject}|coding+qa",
                             _sig(root, _rec(subject, "coding"), _rec(subject, "qa"))))

    # ── reflect: verify 가 cleared 이거나 review 가 reported
    for subject, roles in b.items():
        # vocab source of truth: docs/specs/loop-state-vocab.md (verify: loop_state)
        if roles.get("verify", {}).get("loop_state") == "cleared":
            woken.append(Row("reflect", f"{subject}: verify loop_state: cleared",
                             f"reflect|{subject}|verify",
                             _sig(root, _rec(subject, "verify"))))
        # vocab source of truth: docs/specs/loop-state-vocab.md (review: loop_state)
        elif roles.get("review", {}).get("loop_state") == "reported":
            woken.append(Row("reflect", f"{subject}: review loop_state: reported",
                             f"reflect|{subject}|review",
                             _sig(root, _rec(subject, "review"))))

    # ── qa: 도는 시스템의 src/ 또는 tests/ 를 건드린 커밋
    #    근거는 **그 커밋의 sha** 다. 파일 내용이 아니라 — 소스가 다시 움직였을
    #    때만 다시 깨어나야 하고, 그게 이 줄이 영원히 서 있던 이유였다.
    src_sha = _git(root, "log", "-1", "--format=%H", "--", "src/", "tests/")
    if src_sha:
        woken.append(Row("qa", "src/ 또는 tests/ 를 건드린 커밋이 있다",
                         "qa|src-tests", src_sha[:16]))

    # ── review: coding 이 착지시킨 변경
    for subject, roles in b.items():
        # vocab source of truth: docs/specs/loop-state-vocab.md (coding: loop_state)
        if roles.get("coding", {}).get("loop_state") == "landed":
            woken.append(Row("review", f"{subject}: coding loop_state: landed",
                             f"review|{subject}|landed",
                             _sig(root, _rec(subject, "coding"))))

    # ── finding 되돌이 간선 (docs/specs/wake-routing.md). 표에는 coding 줄에만
    #    적혀 있지만 그 문서는 모든 역할이 자기 앞으로 온 finding 에 깨어난다고
    #    적는다.
    for role in spawn.ROLES:
        for f in _findings_to(root, role):
            if role == "coding":
                # 사전 승인 게이트는 finding 갈래도 똑같이 막는다 — 네 갈래 전부가 대상이다.
                subject = Path(f).parent.name
                if subject in b:
                    wake_coding(subject, f"finding addressed_to: coding — {f}", f)
                    continue
            woken.append(Row(role, f"finding addressed_to: {role} — {f}",
                             f"{role}|finding|{f}", _sig(root, f)))

    def _uniq(rows: list[Row]) -> list[Row]:
        seen, out = set(), []
        for r in rows:
            if r.key not in seen:
                seen.add(r.key)
                out.append(r)
        return out

    return _uniq(woken), _uniq(blocked)


def report(cwd: str, show_answered: bool = False) -> list[str]:
    new, answered = fresh(cwd)
    _, judged, blocked = evaluate(cwd)
    woken = new + answered if show_answered else new
    out = ["깨어난 역할 (docs/specs/wake-routing.md):"] if woken else ["기계로 판정되는 일곱 줄 중 선 것 없음."]
    out += [f"  [{r.role}] {r.why}" for r in woken]
    if answered and not show_answered:
        # 억제된 줄을 그냥 없애면 "왜 안 뜨지"가 된다. 세어서 보여주고, 보는
        # 방법도 같이 준다.
        out.append(f"  ({len(answered)}줄은 근거가 그대로라 다시 안 깨운다 — "
                   f"계약 §6. 보려면 `wake --all`)")
    out.append("")
    if blocked:
        # 막힌 것을 안 깨어난 것으로 보고하면 사람이 자기 차례인 줄 모른다.
        out.append("갈래는 섰는데 사전 승인 게이트가 막고 있다 — **사람이 승인해야 열린다**:")
        out += [f"  [{role}] {why}" for role, why in blocked]
        out.append("")
    out.append("기계로 판정하지 않는 줄 — **안 깨어난 것이 아니라 못 재는 것이다**:")
    out += [f"  [{role}] {why}" for role, why in judged]
    out.append("")
    out.append("docs/specs/wake-routing.md 가 자동화를 **금지한** 간선 — 사람이 판단한다:")
    out += [f"  [{name}] {why}" for name, why in sorted(HUMAN_ONLY.items())]
    return out
