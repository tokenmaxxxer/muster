#!/usr/bin/env python3
"""orchestrator 라우터 — 무상태 배차기.

라벨 수신 → 기계 게이트 → 실행자 스폰 → 산출물 게시 → 라벨 전이.
LLM 호출 0회. 상태는 전부 트래커 라벨과 git 에 있고, 이 프로세스는 죽어도 된다.

워커는 GitHub 토큰을 갖지 않는다. $OUT 에 계약 산출물만 쓰고, 게시(코멘트·PR·
라벨·머지)는 전부 라우터가 한다 — GitHub 은 코멘트 권한과 라벨 권한을 분리하지
않으므로, 워커에게 토큰을 주면 워커가 자기 게이트를 떼어낼 수 있다.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

import gates

ROOT = Path(__file__).resolve().parent.parent
C: dict = {}


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- tracker (gh)

def gh(*args: str, check: bool = True) -> str:
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(f"gh {' '.join(args)}\n{p.stderr.strip()}")
    return p.stdout


def repo_args() -> list[str]:
    return ["--repo", C["repo"]]


def issues() -> list[dict]:
    # --state all 이어야 한다: build 가 만든 PR 본문의 `Closes #N` 이 머지 시점에
    # 이슈를 닫으므로, open 만 보면 머지 직후 qa 스테이지가 영원히 배차되지 않는다.
    # 진행 여부는 이슈 상태가 아니라 라벨이 판정한다.
    # ponytail: 최근 100개 스캔. 이슈가 수천 개가 되면 --search 로 라벨 필터링.
    out = gh("issue", "list", *repo_args(), "--state", "all", "--limit", "100",
             "--json", "number,title,body,labels,updatedAt")
    return json.loads(out)


def labels_of(iss: dict) -> set[str]:
    return {lab["name"] for lab in iss["labels"]}


def relabel(num: int, add: list[str], remove: list[str]) -> None:
    args = ["issue", "edit", str(num), *repo_args()]
    for a in add:
        args += ["--add-label", a]
    for r in remove:
        args += ["--remove-label", r]
    gh(*args)


# 라우터가 트래커에 쓰는 모든 문자열이 여기를 지난다. 실패 메시지에는 명령줄과
# stderr 가 그대로 실려 있어, 자격증명이 섞이면 그대로 공개 코멘트가 된다.
SECRET_RE = re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}|x-access-token:[^@\s]+")


def redact(s: str) -> str:
    return SECRET_RE.sub("«redacted»", s)


def comment(num: int, body: str) -> None:
    gh("issue", "comment", str(num), *repo_args(), "--body", redact(body))


# ------------------------------------------------------------- state machine

def stage_of(labels: set[str]) -> tuple[str | None, bool]:
    """현재 스테이지와 배차 여부. 파이프라인 라벨은 항상 하나만 유지된다."""
    for name in C["stages"]:
        if f"pipeline:{name}:running" in labels:
            return name, True
        if f"pipeline:{name}" in labels:
            return name, False
    return None, False


def attempt_of(labels: set[str]) -> int:
    for lab in labels:
        if lab.startswith("attempt:"):
            return int(lab.split(":")[1])
    return 0


def set_attempt(num: int, old: int, new: int) -> None:
    relabel(num, [f"attempt:{new}"], [f"attempt:{old}"] if old else [])


def escalate(num: int, stage: str, reason: str) -> None:
    log(f"#{num} ESCALATE ({stage}): {reason}")
    comment(num, f"🛑 **에스컬레이션** — 라우터가 손을 뗍니다.\n\n```\n{reason}\n```")
    relabel(num, ["pipeline:human"],
            [f"pipeline:{stage}", f"pipeline:{stage}:running"])


def advance(num: int, stage: str) -> None:
    nxt = C["stages"][stage]["next"]
    add = ["pipeline:done"] if nxt == "done" else [f"pipeline:{nxt}"]
    relabel(num, add, [f"pipeline:{stage}:running"])
    log(f"#{num} {stage} → {nxt}")


def is_stale(iss: dict) -> bool:
    updated = datetime.fromisoformat(iss["updatedAt"])
    age = (datetime.now(timezone.utc) - updated).total_seconds()
    return age > C["stale_seconds"]


# ------------------------------------------------------------------ workspace

def rundir(num: int) -> Path:
    return ROOT / "runs" / str(num)


def prepare(num: int, stage: str) -> Path:
    d = rundir(num)
    (d / "logs").mkdir(parents=True, exist_ok=True)
    out = d / "out"
    if out.exists():
        shutil.rmtree(out)          # 스테이지마다 빈 $OUT — 이전 산출물 재사용 방지
    out.mkdir()
    work = d / "work"
    if not work.exists():
        gh("repo", "clone", C["repo"], str(work))
    else:
        git(work, "fetch", "origin")
    # build 는 매 시도를 main + spec 에서 새로 시작한다. 초기화하지 않으면 회귀
    # 루프(리뷰 기각·QA 실패)에서 이전 시도의 변경 위에 덧쓰여 중복이 쌓인다.
    # review 는 build 가 남긴 트리를 그대로 봐야 하므로 건드리지 않는다.
    if stage in ("build", "qa"):
        git(work, "checkout", "-f", "main")
        git(work, "reset", "--hard", "origin/main")
        git(work, "clean", "-fd")
    return d


def git(work: Path, *args: str, env: dict | None = None) -> str:
    p = subprocess.run(["git", "-C", str(work), *args],
                       capture_output=True, text=True, env=env)
    if p.returncode:
        raise RuntimeError(f"git {' '.join(args)}\n{p.stderr.strip()}")
    return p.stdout


# 토큰을 URL 에 넣으면 argv 에 남아 ps 로 보이고, push 실패 시 예외 메시지(= 명령줄)에
# 실려 이슈 코멘트로 게시된다. 자격증명은 환경변수로만 넘기고 헬퍼가 읽게 한다.
# 앞의 빈 credential.helper 는 시스템 키체인 헬퍼 체인을 끊는다.
CRED_HELPER = ["-c", "credential.helper=", "-c",
               'credential.helper=!f() { echo username=x-access-token; '
               'echo "password=$GIT_TOKEN"; }; f']


# ------------------------------------------------------------------- dispatch

def worker_env(num: int, iss: dict, d: Path) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    # 워커는 gh 인증을 상속하지 않는다. 빈 설정 디렉터리를 주면 호스트 목록이
    # 비어 keyring 조회 자체가 일어나지 않는다.
    # ponytail: 호스트 실행에서의 최선. 진짜 경계는 컨테이너다 (설계문서 참조).
    blind = d / "gh-blind"
    blind.mkdir(exist_ok=True)
    env.update(
        GH_CONFIG_DIR=str(blind),
        ORCH=str(ROOT),
        ISSUE=str(num),
        TITLE=iss["title"],
        OUT=str(d / "out"),
        WORK=str(d / "work"),
        SPEC=str(d / "spec.md"),
        PR=str(find_pr(num) or ""),
    )
    return env


def spawn(num: int, iss: dict, stage: str, d: Path) -> subprocess.Popen:
    # shell=True 는 의도적이다: 어댑터 문자열이 `docker run … claude -p "…"` 같은
    # 실행 환경 전체를 담아야 라우터가 컨테이너를 몰라도 된다.
    # 신뢰할 수 없는 값(이슈 제목·본문)은 문자열 보간이 아니라 환경변수로 넘긴다 —
    # 셸은 확장 결과를 재파싱하지 않으므로 제목에 무엇이 들어와도 명령이 되지 않는다.
    cmd = C["stages"][stage]["cmd"]
    logf = open(d / "logs" / f"{stage}.log", "w")
    return subprocess.Popen(cmd, shell=True, cwd=d / "work",
                            env=worker_env(num, iss, d),
                            stdout=logf, stderr=subprocess.STDOUT)


def dispatch(num: int, iss: dict, stage: str, procs: dict) -> None:
    labels = labels_of(iss)
    attempt = attempt_of(labels)
    if attempt >= C["max_attempts"]:
        escalate(num, stage, f"루프 예산 소진: attempt {attempt}/{C['max_attempts']}")
        return
    relabel(num, [f"pipeline:{stage}:running"], [f"pipeline:{stage}"])
    d = prepare(num, stage)
    log(f"#{num} dispatch {stage} (attempt {attempt})")
    procs[num] = dict(stage=stage, proc=spawn(num, iss, stage, d), dir=d,
                      attempt=attempt, iss=iss)


# -------------------------------------------------------------------- publish

def find_pr(num: int) -> int | None:
    out = gh("pr", "list", *repo_args(), "--head", f"pipeline/issue-{num}",
             "--state", "open", "--json", "number")
    prs = json.loads(out)
    return prs[0]["number"] if prs else None


def token() -> str:
    return gh("auth", "token").strip()


def publish(num: int, stage: str, d: Path, note: str = "") -> None:
    kind = C["stages"][stage]["publish"]
    art = d / "out" / C["stages"][stage]["contract"]
    if kind == "comment":
        comment(num, f"### `{stage}` 산출물\n\n{art.read_text()}")
        if stage == "plan":
            shutil.copy(art, d / "spec.md")     # 다음 스테이지의 계약 입력
    elif kind == "pr":
        work = d / "work"
        branch = f"pipeline/issue-{num}"
        git(work, "checkout", "-B", branch)
        git(work, "add", "-A")
        git(work, "-c", "user.name=orchestrator",
            "-c", "user.email=orchestrator@tokenmaxxxer.local",
            "commit", "-m", f"build: issue #{num}\n\nProposal: pipeline")
        git(work, *CRED_HELPER, "push", "--force", "origin", f"{branch}:{branch}",
            env={**os.environ, "GIT_TOKEN": token()})
        body = f"Closes #{num}\n\n{art.read_text()}"
        # 재시도(리뷰 기각·QA 실패)에서는 브랜치만 갱신하면 된다. PR 을 다시 만들려
        # 들면 "already exists" 로 실패해 회귀 루프가 성립하지 않는다.
        existing = find_pr(num)
        if existing:
            comment(num, f"🔁 PR #{existing} 갱신 (build 재시도)")
        else:
            gh("pr", "create", *repo_args(), "--head", branch, "--base", "main",
               "--title", f"build: issue #{num}", "--body", body)
    elif kind == "merge":
        pr = find_pr(num)
        gh("pr", "merge", str(pr), *repo_args(), "--squash", "--delete-branch")
        # 사람 승인 없이 머지되므로 근거를 남기는 것이 감사 기록의 전부다.
        comment(num, f"✅ PR #{pr} 머지 — 라우터가 머지(워커 아님)\n\n"
                     f"**계약 검증 판정**: {note or '(사유 없음)'}")


def verdict_ok(d: Path, stage: str) -> tuple[bool, str]:
    """review 스테이지: 워커가 낸 판정을 라우터가 전사한다 (판단하지 않는다)."""
    if not C["stages"][stage].get("verdict"):
        return True, ""
    raw = (d / "out" / C["stages"][stage]["contract"]).read_text()
    m = re.search(r"\{.*\}", raw, re.S)
    v = json.loads(m.group(0)) if m else {}
    return bool(v.get("approved")), str(v.get("reason", ""))[:500]


# ----------------------------------------------------------------------- reap

def fail(num: int, stage: str, attempt: int, reason: str) -> None:
    log(f"#{num} FAIL {stage}: {reason}")
    nxt = attempt + 1
    set_attempt(num, attempt, nxt)   # 라벨이 곧 감사 기록이므로 먼저 올린다
    if nxt >= C["max_attempts"]:
        escalate(num, stage, f"{reason}\n(attempt {nxt}/{C['max_attempts']} 소진)")
        return
    comment(num, f"↩︎ `{stage}` 실패 — 재시도 {nxt}/{C['max_attempts']}\n\n```\n{reason}\n```")
    back = C["stages"][stage].get("on_fail", stage)
    relabel(num, [f"pipeline:{back}"], [f"pipeline:{stage}:running"])


def reap(procs: dict) -> bool:
    done = False
    for num in list(procs):
        r = procs[num]
        if r["proc"].poll() is None:
            continue
        procs.pop(num)
        done = True
        stage, d, attempt = r["stage"], r["dir"], r["attempt"]
        rc = r["proc"].returncode
        art = d / "out" / C["stages"][stage]["contract"]

        if rc != 0:
            fail(num, stage, attempt, f"실행자 종료 코드 {rc}")
            continue
        if not (art.exists() and art.stat().st_size > 0):
            fail(num, stage, attempt, f"계약 산출물 없음: {art.name}")
            continue
        bad = gates.check(C["stages"][stage].get("gates", []), d, C)
        if bad:
            escalate(num, stage, "기계 게이트 차단:\n" + "\n".join(bad))
            continue
        ok, why = verdict_ok(d, stage)
        if not ok:
            fail(num, stage, attempt, f"계약 검증 기각: {why}")
            continue
        try:
            publish(num, stage, d, note=why)
        except RuntimeError as e:
            fail(num, stage, attempt, f"게시 실패: {e}")
            continue
        advance(num, stage)
    return done


# ----------------------------------------------------------------------- loop

def tick(procs: dict) -> bool:
    """이번 주기에 일이 있었으면 True. drain 종료 판정에 쓴다."""
    busy = False
    for iss in issues():
        num, labels = iss["number"], labels_of(iss)
        if "pipeline:human" in labels or "pipeline:done" in labels:
            continue
        stage, running = stage_of(labels)
        if stage is None:
            continue
        if running:
            if num not in procs and is_stale(iss):
                escalate(num, stage, "stale: 실행자가 응답하지 않음 (라우터 재시작 또는 워커 사망)")
                busy = True
            continue
        if num in procs:
            continue
        dispatch(num, iss, stage, procs)
        busy = True
    return reap(procs) or busy


def bootstrap() -> None:
    colors = {"plan": "1d76db", "build": "0e8a16", "review": "5319e7",
              "qa": "fbca04", "done": "c5def5", "human": "b60205"}
    names = [f"pipeline:{s}" for s in C["stages"]] + \
            [f"pipeline:{s}:running" for s in C["stages"]] + \
            ["pipeline:done", "pipeline:human"] + \
            [f"attempt:{i}" for i in range(1, C["max_attempts"] + 1)]
    for n in names:
        key = n.split(":")[1] if n.startswith("pipeline:") else "done"
        gh("label", "create", n, *repo_args(), "--force",
           "--color", colors.get(key, "ededed"), "--description", "orchestrator")
    log(f"라벨 {len(names)}개 준비 완료")


def main() -> None:
    global C
    cfg = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "adapters.yml")
    C = yaml.safe_load(cfg.read_text())
    C["stale_seconds"] = int(os.environ.get("STALE_SECONDS", C["stale_seconds"]))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "bootstrap":
        return bootstrap()
    procs: dict = {}
    busy = True
    log(f"라우터 시작 — repo={C['repo']} config={cfg.name}")
    while True:
        try:
            busy = tick(procs)
        except Exception as e:                     # 라우터는 죽지 않는다
            log(f"tick 오류(무시하고 계속): {e}")
            busy = True
        if cmd == "drain" and not procs and not busy:   # 파이프라인이 비면 종료 (E2E용)
            return
        time.sleep(C["poll_seconds"] if cmd != "drain" else 2)


if __name__ == "__main__":
    main()
