#!/usr/bin/env python3
"""ablation 러너 — 룰북을 켜고 끈 두 팔을 같은 표적에 돌린다.

  python3 bench/run.py --role qa --target todo-cli --reps 3
  python3 bench/run.py --role qa --target todo-cli --reps 1 --arms on   # 한 팔만

프로토콜은 `qa-agent-rulebook/bench/README.md` 를 그대로 따른다. 러너를 on-the-record 에
두는 이유는 **계측기가 측정 대상 안에 있으면 다른 룰북을 못 재기 때문**이다.
표적과 정답 키는 각 룰북이 자기 `bench/` 에 갖고 온다.

정답 키는 실행 환경에 **절대 들어가지 않는다.** 표적 디렉터리만 임시 폴더로 복사하고
`answers/` 는 두고 온다 — 그게 숨김 기전의 전부다.

채점은 자동화하지 않는다. 발견이 키 항목을 맞혔는지는 "트리거 행동과 잘못된 결과를
지목했는가"로 사람이 판정한다(키의 adjudication 조항). 러너는 **채점표를 만들어
준다** — 자동 판정을 흉내 내면 원장이 거짓말을 시작한다.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import spawn as spawn_mod
BARE = ("QA this app: run it, try the main flows and obvious failure paths, "
        "write findings to qa/runs/ with evidence.")


def rulebook_bench(role: str) -> Path:
    """역할의 룰북에서 bench 디렉터리. 역할 파일이 룰북 경로를 안다."""
    spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())
    b = Path(spec["path"]) / "bench"
    if not b.exists():
        sys.exit(f"[{role}] 룰북에 bench/ 가 없다: {b}")
    return b


def one_run(role: str, arm: str, target: Path, i: int, out: Path) -> dict:
    """한 번의 실행. 표적 사본과 워크스페이스는 매번 새로 만든다."""
    work = out / f"{arm}-{i}"
    shutil.copytree(target, work)
    subprocess.run(["git", "init", "-q"], cwd=work)
    subprocess.run(["git", "add", "-A"], cwd=work, capture_output=True)
    subprocess.run(["git", "-c", "user.email=b@b", "-c", "user.name=b",
                    "commit", "-qm", "bench"], cwd=work, capture_output=True)
    ws = out / f"{arm}-{i}-workspace"
    ws.mkdir()

    env = {**os.environ, "QA_WORKSPACE": str(ws)}
    if arm == "on":
        cmd = [sys.executable, str(ROOT / "spawn.py"), role,
               "/testrun:testrun", "-C", str(work)]
        task = None
    else:
        # off 팔은 룰북이 하나도 없어야 한다. 사용자 전역 플러그인까지 꺼야
        # 비교가 성립한다 — spawn.py 가 하는 그 차단을 여기서도 한다.
        s = {"enabledPlugins": {k: False for k in json.loads(
            (Path.home() / ".claude/settings.json").read_text()).get("enabledPlugins", {})}}
        sf = out / f"off-{i}.json"
        sf.write_text(json.dumps(s))
        cmd = ["claude", "-p", "--settings", str(sf)]
        task = BARE

    log = out / f"{arm}-{i}.log"
    with log.open("w") as f:
        p = subprocess.run(cmd, cwd=work, input=task, text=True,
                           stdout=f, stderr=subprocess.STDOUT, env=env)

    # 제품 파일을 건드렸는가. on 팔은 워크스페이스 계약상 **어떤 쓰기도** 위반이고,
    # off 팔은 qa/ 밖 쓰기가 위반이다.
    touched = subprocess.run(["git", "status", "--porcelain", "-uall"],
                             cwd=work, capture_output=True, text=True).stdout.split("\n")
    touched = [t[3:] for t in touched if t.strip()]
    violations = [t for t in touched if arm == "on" or not t.startswith("qa/")]

    # 기록이 runs/ 바로 아래일 수도, runs/<타임스탬프>/ 아래일 수도 있다. 얕게 훑으면
    # **산출물이 있는데 0건으로 보고**해서 팔 하나가 통째로 실패한 것처럼 보인다.
    records = sorted({str(p.relative_to(out)) for p in
                      list(ws.rglob("runs/**/*.md")) + list(work.rglob("runs/**/*.md"))
                      if p.is_file()})
    return {"arm": arm, "rep": i, "exit": p.returncode, "log": log.name,
            "run_records": records, "touched": touched, "product_writes": violations}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="qa")
    ap.add_argument("--target", default="todo-cli")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--arms", default="on,off")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    bench = rulebook_bench(a.role)
    target = bench / "targets" / a.target
    key = bench / "answers" / f"{a.target}.json"
    if not target.exists():
        sys.exit(f"표적 없음: {target}")
    if not key.exists():
        sys.exit(f"정답 키 없음: {key}  — 키 없이 돌리면 채점할 수 없다")

    # 룰북 버전을 결과에 박는다. 역할 파일은 룰북을 로컬 디렉터리로 가리키므로
    # 핀이 없다 — 그 순간 체크아웃된 것이 돈다. 어느 룰북을 쟀는지 안 남기면
    # "룰북 켜고 끄고를 쟀다"는 문장이 검증 불가능한 주장이 된다.
    version = spawn_mod.rulebook_version(a.role)
    if "커밋안됨" in version:
        sys.exit(f"[{a.role}] 룰북에 커밋 안 된 수정이 있다: {version}\n"
                 f"  이대로 재면 결과가 어느 코드에서 나왔는지 아무도 재현할 수 없다.\n"
                 f"  커밋하거나 되돌린 뒤 다시 돌린다.")

    out = Path(a.out) if a.out else Path(tempfile.mkdtemp(prefix=f"bench-{a.target}-"))
    out.mkdir(parents=True, exist_ok=True)
    print(f"표적 {a.target}  팔 {a.arms}  반복 {a.reps}  룰북 {version}  →  {out}",
          file=sys.stderr)

    runs = []
    for arm in a.arms.split(","):
        for i in range(1, a.reps + 1):
            print(f"  {arm}-{i} …", file=sys.stderr, flush=True)
            runs.append(one_run(a.role, arm, target, i, out))

    # 채점표: 정답 키 × 실행. 사람이 채운다.
    seeded = json.loads(key.read_text())["seeded"]
    sheet = {"target": a.target, "out": str(out), "role": a.role,
             "rulebook": version, "runs": runs,
             "score": [{"id": s["id"], "class": s["class"], "trigger": s["trigger"],
                        "detected": {f"{r['arm']}-{r['rep']}": None for r in runs}}
                       for s in seeded]}
    (out / "scoresheet.json").write_text(json.dumps(sheet, ensure_ascii=False, indent=2))

    print(f"\n실행 {len(runs)}건 완료. 채점표: {out}/scoresheet.json", file=sys.stderr)
    for r in runs:
        flag = f"  ⚠ 제품 쓰기 {len(r['product_writes'])}건" if r["product_writes"] else ""
        print(f"  {r['arm']}-{r['rep']}  종료 {r['exit']}  "
              f"기록 {len(r['run_records'])}건{flag}", file=sys.stderr)
    print("\n다음: 각 실행의 run record 를 읽고 scoresheet 의 detected 를 채운다. "
          "키의 adjudication 조항이 판정 기준이다.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
