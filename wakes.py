#!/usr/bin/env python3
"""WAKES-ON 평가기 — 계약 v2 §3 의 표를 기계로 판정한다.

계약 §3 이 이 자리를 명시적으로 비워 두었다: "WAKES-ON tells the human (**or a
future automated watcher, if one is built**) *whom* to open." 이 파일이 그
감시자다. **일정을 지어내지 않는다** — §3 의 표 아홉 줄이 전부다.

아홉 줄 중 일곱만 기계로 판정된다. 나머지 둘은 계약이 판단으로 적은 것이고,
§14("Mechanical checks are not substantive checks")가 그 구분을 지키라고 한다.
표 밖의 간선 둘은 계약이 **자동화를 금지**했으므로 아예 판정하지 않는다.

  기계 판정 가능        feasibility, coding, qa, review, ux-design, verify, reflect
  판단이 필요           product ("content questions the acceptance criteria")
                        ops    ("ready to roll out")
  자동화 금지           finding 해소 재검증(§15), 라운드 종료 게이트(§18)

**판정 불가를 "안 깨어남"으로 보고하지 않는다.** 그 둘은 정반대 처분을 받아야
한다.

§3 표와 §5 의 어긋남: §5 는 "each row in section 3 already includes its role's
finding trigger" 라고 하지만, §3 표에서 finding 을 실제로 적은 줄은 coding
하나뿐이다. §5 의 진술을 따랐다 — 어느 역할이든 자기 앞으로 온 finding 에
깨어난다. 표만 따르면 coding 외의 역할에게 온 finding 은 아무도 안 본다.
"""
import re
import subprocess
from pathlib import Path

import spawn

# §3 이 기계로 못 재는 두 줄. 왜 못 재는지를 같이 들고 다닌다.
JUDGEMENT = {
    "product": "qa/review 결과가 합의된 수용 기준을 흔드는가 — 내용 판단이다",
    "ops": "머지된 변경이 '내보낼 준비가 됐는가' — 판단이다",
}
# §3 이 표 밖에 둔 두 간선. 본문이 **"human-consulted, never automated"** 라고
# 직접 못박았으므로 기계가 판정해서는 안 된다. 못 재는 것과 성격이 다르다 —
# 이쪽은 **재면 안 되는 것**이다.
HUMAN_ONLY = {
    "finding 해소 후 재검증": "blocking finding 을 올린 역할이 findings-resolved 에 "
                              "다시 깨어난다 (§15). 계약이 자동화를 금지한다",
    "라운드 종료 가치 게이트": "candidate-round-done 이 사람을 깨워 §18 의 게이트 "
                               "둘을 돌린다. 계약이 자동화를 금지한다",
    "사전 승인 게이트": "front record 가 scope-proposed 에 닿으면 사람이 읽고 "
                        "scope-approved 로 올린다 (§19). 그 상태로 가는 **유일한** "
                        "경로이고, 어떤 역할도 자기 것이든 남의 것이든 승인하지 못한다",
}
UPSTREAM = re.compile(r"^\s*-\s*path:\s*(\S+)", re.M)
UP_SHA = re.compile(r"^\s*sha:\s*(\S+)", re.M)


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


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
    d = root / "docs" / "proposals"
    if not d.is_dir():
        return []
    return [p for p in sorted(d.glob("*.md"))
            if spawn.frontmatter(p).get("kind") == "hypothesis"]


def _findings_to(root: Path, role: str) -> list[str]:
    """`finding` 은 다른 역할 기록의 **본문 안에** 인라인으로 산다 (§2 표, §5).
    frontmatter 가 아니므로 본문 전체를 봐야 한다."""
    recs = root / spawn.BOARD
    if not recs.is_dir():
        return []
    hits = []
    for f in sorted(recs.rglob("*.md")):
        try:
            text = f.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if re.search(rf"^\s*addressed_to:\s*{re.escape(role)}\s*(#.*)?$", text, re.M):
            hits.append(str(f.relative_to(root)))
    return hits


def _front(root: Path, subject: str, roles: dict) -> str | None:
    """그 subject 의 front record — subject 를 처음 연 역할 (§19, §9).

    §1 이 체인 루트를 `upstream: []` 로 정의하므로 그게 기계적 판별이다. 못 가리면
    §19 가 적은 통상 순서(product, 아니면 feasibility)로 물러난다.
    """
    rootless = [r for r in roles
                if not upstream(root / spawn.BOARD / subject / f"{r}.md")]
    if len(rootless) == 1:
        return rootless[0]
    for r in ("product", "feasibility"):
        if r in roles:
            return r
    return None


def evaluate(cwd: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]],
                                list[tuple[str, str]]]:
    """(깨어난 역할, 판정 불가한 줄, §19 에 막힌 줄). **아무것도 쓰지 않는다.**"""
    root = Path(cwd).resolve()
    b = spawn.board(root)
    woken: list[tuple[str, str]] = []
    blocked: list[tuple[str, str]] = []

    # ── feasibility: 새롭거나 바뀐 hypothesis 가 보드에 나타남
    feas_records = [(root / spawn.BOARD / s / "feasibility.md")
                    for s, r in b.items() if "feasibility" in r]
    acked = {p: sha for rec in feas_records for p, sha in upstream(rec).items()}
    for h in _hypotheses(root):
        rel = str(h.relative_to(root))
        if rel not in acked:
            woken.append(("feasibility", f"hypothesis {rel} — feasibility 가 아직 안 읽었다"))
        elif acked[rel] and acked[rel] != _head_sha(root, rel):
            woken.append(("feasibility", f"hypothesis {rel} 가 기록된 sha 이후 바뀜"))

    # ── §19 사전 승인 게이트. coding 의 **첫 빌드 진입**에만 붙는다.
    #    네 갈래 전부에 얹히는 전제조건이지 다섯 번째 갈래가 아니다 — 병렬 간선으로
    #    두면 기존 갈래들이 저 혼자 첫 빌드를 깨워 게이트가 무력해진다(§19 본문이
    #    이 함정을 명시적으로 지목한다). 이미 빌드에 들어간 subject 의 재깨움은
    #    게이트 밖이다.
    def wake_coding(subject: str, why: str) -> None:
        roles = b[subject]
        if "coding" in roles:
            woken.append(("coding", f"{subject}: {why}"))
            return
        f = _front(root, subject, roles)
        state = roles.get(f, {}).get("loop_state") if f else None
        if state == "scope-approved":
            woken.append(("coding", f"{subject}: {why}"))
        else:
            blocked.append(("coding",
                            f"{subject}: {why} — 그러나 첫 빌드다. front record"
                            f"({f or '없음'}) 가 {state or '없음'} 이라 §19 가 막는다"))

    # ── coding: 세 갈래 중 하나만 서도 깨어난다
    for subject, roles in b.items():
        if roles.get("feasibility", {}).get("verdict") == "go":
            wake_coding(subject, "feasibility verdict: go")
        if roles.get("qa", {}).get("loop_state") == "handed-off":
            wake_coding(subject, "qa handed-off — 사람의 결함 판정이 끝났다")

    # ── ux-design: 새롭거나 바뀐 product-record (체인 루트면 hypothesis)
    for subject, roles in b.items():
        if "product" in roles and "ux-design" not in roles:
            woken.append(("ux-design", f"{subject}: product-record 가 있고 ux-design 기록이 없다"))

    # ── coding 의 네 번째 갈래: ux-design-record 가 reviewed 에 도달
    for subject, roles in b.items():
        if roles.get("ux-design", {}).get("loop_state") == "reviewed":
            wake_coding(subject, "ux-design loop_state: reviewed")

    # ── verify: coding 과 qa 가 **둘 다** 산출물을 낸 subject (첫 깨움)
    for subject, roles in b.items():
        if "coding" in roles and "qa" in roles and "verify" not in roles:
            woken.append(("verify", f"{subject}: coding 과 qa 가 둘 다 기록을 냈다"))

    # ── reflect: verify 가 cleared 이거나 review 가 reported
    for subject, roles in b.items():
        if roles.get("verify", {}).get("loop_state") == "cleared":
            woken.append(("reflect", f"{subject}: verify loop_state: cleared"))
        elif roles.get("review", {}).get("loop_state") == "reported":
            woken.append(("reflect", f"{subject}: review loop_state: reported"))

    # ── qa: 도는 시스템의 src/ 또는 tests/ 를 건드린 커밋
    if _git(root, "log", "-1", "--format=%H", "--", "src/", "tests/"):
        woken.append(("qa", "src/ 또는 tests/ 를 건드린 커밋이 있다"))

    # ── review: coding 이 착지시킨 변경
    for subject, roles in b.items():
        if roles.get("coding", {}).get("loop_state") == "landed":
            woken.append(("review", f"{subject}: coding loop_state: landed"))

    # ── finding 되돌이 간선 (§5). 표에는 coding 줄에만 적혀 있지만 §5 는 모든
    #    역할이 자기 앞으로 온 finding 에 깨어난다고 말한다.
    for role in spawn.ROLES:
        for f in _findings_to(root, role):
            if role == "coding":
                # §19 는 finding 갈래도 똑같이 막는다 — 네 갈래 전부가 대상이다.
                subject = Path(f).parent.name
                if subject in b:
                    wake_coding(subject, f"finding addressed_to: coding — {f}")
                    continue
            woken.append((role, f"finding addressed_to: {role} — {f}"))

    def _uniq(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen, out = set(), []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    return _uniq(woken), sorted(JUDGEMENT.items()), _uniq(blocked)


def report(cwd: str) -> list[str]:
    woken, judged, blocked = evaluate(cwd)
    out = ["깨어난 역할 (계약 §3):"] if woken else ["기계로 판정되는 일곱 줄 중 선 것 없음."]
    out += [f"  [{role}] {why}" for role, why in woken]
    out.append("")
    if blocked:
        # 막힌 것을 안 깨어난 것으로 보고하면 사람이 자기 차례인 줄 모른다.
        out.append("갈래는 섰는데 §19 승인 게이트가 막고 있다 — **사람이 승인해야 열린다**:")
        out += [f"  [{role}] {why}" for role, why in blocked]
        out.append("")
    out.append("기계로 판정하지 않는 줄 — **안 깨어난 것이 아니라 못 재는 것이다**:")
    out += [f"  [{role}] {why}" for role, why in judged]
    out.append("")
    out.append("계약이 자동화를 **금지한** 간선 — 사람이 판단한다:")
    out += [f"  [{name}] {why}" for name, why in sorted(HUMAN_ONLY.items())]
    return out
