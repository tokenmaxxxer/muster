# muster hardening + observability (M1–M6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the orchestrator self-mint hole, fix silent Write denial, capture session results into a run ledger with outcome classification, extend the repo-config refusal, drop the pre-approved cp, and add a hook-firing canary — changes M1–M6 of `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md`.

**Architecture:** All changes are muster-side. A new pure function `spawn_cmd()` owns the claude invocation (flags + env stamps) so it is testable without spawning; `main()` gains JSON result capture, a board snapshot before/after, an outcome verdict, and one JSONL ledger line per spawn under muster's own `runs/` (already gitignored — muster stays read-only toward target repos). `spawn.py doctor` becomes the canary that proves plugin hooks fire headless on the installed CLI, and spawns halt until the current CLI version has a doctor pass.

**Tech Stack:** Python 3 stdlib only. Tests follow `test_gates.py`'s unittest style, run as `python3 test_spawn.py`.

## Global Constraints

- Python 3 standard library only.
- Code comments and user-facing strings in spawn.py are Korean — match the file's existing voice.
- muster never writes into a target repo (protocol §1). All new state lives under muster's own `runs/` (gitignored).
- Fail closed: an unreadable/unparseable session result is reported as such, never as success. Report-only remains report-only: muster does not judge, retry, or block on outcomes.
- Do not regress the measured pitfalls: --settings global-plugin force-disable stays; allowUnsandboxedCommands:false stays; stdin task passing stays (argv risks flag-swallowing and shell interpolation).

---

### Task 1: Extend the repo-config refusal (M4) and create test_spawn.py

**Files:**
- Modify: `spawn.py:542` (the `REPO_CONFIG` tuple)
- Create: `test_spawn.py`

**Interfaces:**
- Consumes: `spawn.REPO_CONFIG`, `spawn.require_no_repo_config(cwd, override)` (exists).
- Produces: `test_spawn.py` with unittest scaffolding later tasks extend.

- [ ] **Step 1: Write the failing test**

`test_spawn.py`:

```python
#!/usr/bin/env python3
"""spawn.py 의 순수 함수들 — 세션을 띄우지 않고 검사한다."""
import json
import os
import tempfile
import unittest
from pathlib import Path

import spawn


class RepoConfigRefusal(unittest.TestCase):
    def test_agents_and_mcp_are_rogue(self):
        # 프로젝트 스코프 에이전트 파일은 hooks/permissionMode frontmatter 를
        # 존중하고(sub-agents 문서), .mcp.json 은 레포가 적은 프로세스 실행
        # 표면이다 — 실측된 레포-커밋-훅 탈출과 같은 부류.
        for p in (".claude/agents", ".mcp.json"):
            self.assertIn(p, spawn.REPO_CONFIG, p)

    def test_refusal_fires_on_agents_dir(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / ".claude" / "agents").mkdir(parents=True)
            with self.assertRaises(SystemExit):
                spawn.require_no_repo_config(td, override=False)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 test_spawn.py -v`
Expected: FAIL — `'.claude/agents' not found in` the tuple.

- [ ] **Step 3: Extend the tuple**

In `spawn.py`, change:

```python
REPO_CONFIG = (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks")
```

to:

```python
REPO_CONFIG = (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks",
               ".claude/agents", ".mcp.json")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 test_spawn.py -v` → PASS (2 tests).
Also run: `python3 test_gates.py` → unchanged, all pass.

- [ ] **Step 5: Commit**

```bash
git add spawn.py test_spawn.py
git commit -m "Refuse repo-shipped .claude/agents and .mcp.json too

Project-scope agent files honor hooks and permissionMode frontmatter, and
.mcp.json is a repo-authored process-execution surface — the same class as
the measured repo-committed-hook sandbox escape REPO_CONFIG already stops."
```

---

### Task 2: One place builds the claude invocation — stamps, permission mode, JSON output (M1+M2, half of M3)

**Files:**
- Modify: `spawn.py` (new function above `main()`; `main()` argparse + spawn block)
- Test: `test_spawn.py` (extend)

**Interfaces:**
- Consumes: nothing new.
- Produces: `spawn.spawn_cmd(settings_path: str, role: str, unattended: bool) -> tuple[list[str], dict[str, str]]` — the exact argv and the env **additions** (caller merges over os.environ). Task 3 wires it; tests assert on it.

- [ ] **Step 1: Write the failing tests** (append to `test_spawn.py`)

```python
class SpawnCmd(unittest.TestCase):
    def test_flags(self):
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn("--settings", cmd)
        self.assertEqual(cmd[cmd.index("--settings") + 1], "/tmp/s.json")
        # 실측 2026-07-27: 권한 설정 없는 headless 는 Write 를 조용히 거부한다
        # (permission_denials 에만 남고 겉은 성공). acceptEdits 가 그 프롬프트를
        # 없애고, PreToolUse exit 2 게이트는 acceptEdits 아래서도 여전히 막는다.
        self.assertIn("acceptEdits", cmd)
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "acceptEdits")
        # 결과 포착 없이는 세션이 "아무것도 안 하고 exit 0" 해도 모른다.
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "json")

    def test_env_stamps(self):
        # D1: 스폰된 세션의 UserPromptSubmit 은 오케스트레이터가 쓴 텍스트다.
        # 그 턴이 사람 턴으로 오인되어 mint 되는 일이 없도록 도장을 찍는다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
        self.assertEqual(env["CLAUDE_ROLE"], "qa")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")
        self.assertNotIn("TOKENMAXXXER_UNATTENDED", env)

    def test_unattended_is_separate(self):
        # SPAWNED(사람 턴 아님)와 UNATTENDED(사람 부재)는 다른 사실이다.
        # 겹쳐 쓰면 attended 스폰이 깨진다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=True)
        self.assertEqual(env["TOKENMAXXXER_UNATTENDED"], "1")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 test_spawn.py -v`
Expected: FAIL — `AttributeError: module 'spawn' has no attribute 'spawn_cmd'`.

- [ ] **Step 3: Implement `spawn_cmd`** (place directly above `main()` in spawn.py)

```python
def spawn_cmd(settings_path: str, role: str,
              unattended: bool) -> tuple[list[str], dict[str, str]]:
    """세션 argv 와 env **추가분**. 호출자가 os.environ 위에 얹는다.

    --permission-mode acceptEdits: 실측 2026-07-27 — 권한 설정 없는 headless 는
    Write 를 조용히 거부한다(permission_denials 에만 남는다). acceptEdits 는
    대답할 사람이 없는 프롬프트를 없앨 뿐이고, 거부는 계속 게이트의 몫이다 —
    PreToolUse exit 2 가 acceptEdits 아래서도 막는 것을 같은 날 실측했다.
    샌드박스 Bash 는 원래 자동 허용이고, 비샌드박스 재실행은 이미
    allowUnsandboxedCommands:false 가 막는다.

    TOKENMAXXXER_SPAWNED: 스폰된 세션의 프롬프트는 오케스트레이터가 쓴
    텍스트이지 사람 턴이 아니다. core 의 mint 훅이 이 도장을 보고 발행을
    거른다. UNATTENDED 와 별개다 — 그쪽은 "사람이 없다"는 사실이고, 겹쳐
    쓰면 attended 스폰이 깨진다.
    """
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "acceptEdits", "--output-format", "json"]
    env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}
    if unattended:
        env["TOKENMAXXXER_UNATTENDED"] = "1"
    return cmd, env
```

- [ ] **Step 4: Add the argparse flag** (in `main()`, after `--trust-repo-config`)

```python
    ap.add_argument("--unattended", action="store_true",
                    help="사람이 없는 실행. mint 는 안 되고, 휴먼 게이트는 선다")
```

- [ ] **Step 5: Run the tests**

Run: `python3 test_spawn.py -v` → PASS. (`main()` wiring lands in Task 3 — spawn_cmd is not yet called; that is fine, tests pin its contract first.)

- [ ] **Step 6: Commit**

```bash
git add spawn.py test_spawn.py
git commit -m "Stamp spawned sessions and stop losing writes to silent denial

TOKENMAXXXER_SPAWNED marks every spawned session's prompts as
orchestrator-authored so core's mint hook can refuse them — a spawn task of
exactly the challenge line must not mint (measured: the stdin task arrives
verbatim as UserPromptSubmit). --permission-mode acceptEdits removes the
nobody-to-answer prompts that silently denied Write (measured), while
PreToolUse gates still refuse under it (also measured). --unattended stays
a separate fact: human absent, judge eligible."
```

---

### Task 3: Capture the session result, classify the outcome, write the ledger (rest of M3)

**Files:**
- Modify: `spawn.py` (helpers above `main()`; the spawn block inside `main()`)
- Test: `test_spawn.py` (extend)

**Interfaces:**
- Consumes: `spawn_cmd` (Task 2); `spawn.BOARD` (`"docs/reports/records"`); `wakes.evaluate(cwd) -> (woken, judged, blocked)`; `spawn.ROOT` (muster dir).
- Produces:
  - `spawn.board_snapshot(cwd: str) -> dict[str, str]` — relpath → sha256 for every file under BOARD.
  - `spawn.session_result(stdout: str) -> dict` — parsed `--output-format json` object, `{}` on any parse failure.
  - `spawn.classify(rc: int, result: dict, delta: list[str], blocked: list) -> str` — `"errored" | "progressed" | "waiting-on-human" | "silent-failure"`.
  - `spawn.ledger_write(entry: dict) -> Path` — appends one JSON line to `ROOT/runs/ledger.jsonl`, creating `runs/`.

- [ ] **Step 1: Write the failing tests** (append to `test_spawn.py`)

```python
class BoardSnapshot(unittest.TestCase):
    def test_delta_shows_changed_and_new(self):
        with tempfile.TemporaryDirectory() as td:
            rec = Path(td) / spawn.BOARD / "alpha"
            rec.mkdir(parents=True)
            (rec / "qa.md").write_text("loop_state: probing\n")
            before = spawn.board_snapshot(td)
            (rec / "qa.md").write_text("loop_state: reproduced\n")
            (rec / "coding.md").write_text("new\n")
            after = spawn.board_snapshot(td)
            delta = sorted(p for p in after if after.get(p) != before.get(p))
            self.assertEqual(delta, [f"{spawn.BOARD}/alpha/coding.md",
                                     f"{spawn.BOARD}/alpha/qa.md"])

    def test_no_board_is_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(spawn.board_snapshot(td), {})


class SessionResult(unittest.TestCase):
    def test_parses_json(self):
        got = spawn.session_result('{"session_id": "abc", "total_cost_usd": 0.5}')
        self.assertEqual(got["session_id"], "abc")

    def test_garbage_is_empty_dict(self):
        # 파싱 불가를 성공으로 취급하지 않는다 — 빈 dict 는 아래 classify 에서
        # is_error 도 아니고 필드도 없는, "모른다" 그대로다.
        self.assertEqual(spawn.session_result("not json"), {})
        self.assertEqual(spawn.session_result(""), {})


class Classify(unittest.TestCase):
    def test_errored_wins(self):
        self.assertEqual(spawn.classify(1, {}, [], []), "errored")
        self.assertEqual(spawn.classify(0, {"is_error": True}, ["x"], []), "errored")

    def test_progressed_on_delta(self):
        self.assertEqual(spawn.classify(0, {}, ["records/a/qa.md"], []), "progressed")

    def test_waiting_on_human(self):
        blocked = [("coding", "…§19 가 막는다")]
        self.assertEqual(spawn.classify(0, {}, [], blocked), "waiting-on-human")

    def test_silent_failure_is_loud(self):
        # 실측된 침묵-사망 모드: exit 0, 보드 무변화, 막힌 줄도 없음.
        self.assertEqual(spawn.classify(0, {}, [], []), "silent-failure")


class Ledger(unittest.TestCase):
    def test_appends_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            old = spawn.ROOT
            spawn.ROOT = Path(td)
            try:
                p = spawn.ledger_write({"role": "qa", "outcome": "progressed"})
                p2 = spawn.ledger_write({"role": "review", "outcome": "errored"})
            finally:
                spawn.ROOT = old
            self.assertEqual(p, p2)
            lines = [json.loads(l) for l in p.read_text().splitlines()]
            self.assertEqual([l["role"] for l in lines], ["qa", "review"])
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 test_spawn.py -v`
Expected: FAIL — no attribute `board_snapshot` (etc.).

- [ ] **Step 3: Implement the helpers** (above `main()`)

```python
def board_snapshot(cwd: str) -> dict[str, str]:
    """보드 파일들의 내용 해시. 세션 전후를 비교해 §6 의 '바뀐 보드'를 잰다.

    git 이 아니라 파일 내용을 재는 이유: 세션이 커밋했든 안 했든 바뀐 것은
    바뀐 것이고, 계약 §6 의 단위는 커밋이 아니라 보드다.
    """
    root = Path(cwd).resolve() / BOARD
    if not root.is_dir():
        return {}
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(Path(cwd).resolve()))
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def session_result(stdout: str) -> dict:
    """--output-format json 의 결과 오브젝트. 파싱 불가면 빈 dict — 모르는
    것을 성공으로 취급하지 않는다."""
    try:
        got = json.loads(stdout)
        return got if isinstance(got, dict) else {}
    except ValueError:
        return {}


def classify(rc: int, result: dict, delta: list, blocked: list) -> str:
    """세션 하나의 처분. 판정하지 않는다 — 이름만 붙인다 (보고 전용).

    silent-failure 가 넷째 값인 이유: exit 0 에 보드 무변화가 실측된
    침묵-사망 모드다. 조용히 넘어가지 않는 것이 이 함수의 존재 이유다.
    """
    if rc != 0 or result.get("is_error"):
        return "errored"
    if delta:
        return "progressed"
    if blocked:
        return "waiting-on-human"
    return "silent-failure"


def ledger_write(entry: dict) -> Path:
    """runs/ledger.jsonl 에 한 줄. runs/ 는 gitignore 되어 있다 — 측정 데이터는
    소스가 아니다."""
    d = ROOT / "runs"
    d.mkdir(exist_ok=True)
    p = d / "ledger.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return p
```

Add `import hashlib` and `import time` to spawn.py's imports if absent.

- [ ] **Step 4: Run the helper tests**

Run: `python3 test_spawn.py -v` → PASS.

- [ ] **Step 5: Wire into `main()`** — replace the spawn block

Replace:

```python
        rc = subprocess.run(
            ["claude", "-p", "--settings", settings],
            cwd=a.cwd, input=a.task, text=True,
            env={**os.environ, "CLAUDE_ROLE": a.role},
        ).returncode
    finally:
        os.unlink(settings)

    for line in gate_report(a.cwd):
        print(line, file=sys.stderr)
    return rc
```

with:

```python
        cmd, extra_env = spawn_cmd(settings, a.role, a.unattended)
        before = board_snapshot(a.cwd)
        t0 = time.monotonic()
        # stdout 만 잡는다 — --output-format json 의 결과 오브젝트가 거기 온다.
        # stderr 는 그대로 흘린다: 진행 로그는 사람 것이다.
        proc = subprocess.run(
            cmd, cwd=a.cwd, input=a.task, text=True,
            stdout=subprocess.PIPE,
            env={**os.environ, **extra_env},
        )
        rc = proc.returncode
    finally:
        os.unlink(settings)

    result = session_result(proc.stdout)
    if result.get("result"):
        print(result["result"])                  # 세션의 마지막 답 — 기존 UX
    elif proc.stdout.strip():
        print(proc.stdout, end="")               # JSON 이 아니면 그대로 — 숨기지 않는다

    after = board_snapshot(a.cwd)
    delta = sorted(p for p in set(before) | set(after)
                   if before.get(p) != after.get(p))
    import wakes
    try:
        _, _, blocked = wakes.evaluate(a.cwd)
    except Exception:
        blocked = []                             # 분류 보조일 뿐, 평가 실패로 스폰 결과를 잃지 않는다

    gates = gate_report(a.cwd)
    outcome = classify(rc, result, delta, blocked)
    denials = result.get("permission_denials") or []
    ledger_write({
        "ts": int(time.time()), "role": a.role, "cwd": str(Path(a.cwd).resolve()),
        "session_id": result.get("session_id"),
        "cost_usd": result.get("total_cost_usd"),
        "turns": result.get("num_turns"), "rc": rc, "outcome": outcome,
        "board_delta": delta, "denials": len(denials),
        "duration_s": round(time.monotonic() - t0, 1),
        "rulebook": rulebook_version(a.role),
        "gates": gates,
    })

    for line in gates:
        print(line, file=sys.stderr)
    print(f"[{a.role}] {outcome}"
          + (f", 보드 변화 {len(delta)}건" if delta else ", 보드 무변화")
          + (f", 비용 ${result.get('total_cost_usd'):.2f}"
             if isinstance(result.get("total_cost_usd"), (int, float)) else ""),
          file=sys.stderr)
    if denials:
        print(f"[{a.role}] 권한 거부 {len(denials)}건 — 세션이 요청했지만 답할 사람이 "
              f"없어 거부된 도구 호출이다. runs/ledger.jsonl 과 대조하라", file=sys.stderr)
    if outcome == "silent-failure":
        print(f"[{a.role}] exit 0 인데 보드가 안 바뀌었다 — 성공이 아니라 "
              f"실측된 침묵-사망 모드다. 세션 로그를 확인하라"
              + (f" (session {result.get('session_id')})" if result.get("session_id") else ""),
              file=sys.stderr)
    return rc
```

- [ ] **Step 6: Full test pass + dry-run sanity**

Run: `python3 test_spawn.py -v && python3 test_gates.py` → all PASS.
Run: `python3 spawn.py qa "x" --dry-run -C /tmp` inside a tempdir with a contract? — simpler: `python3 -c "import spawn; print(spawn.spawn_cmd('/s','qa',False))"` → shows the argv with acceptEdits/json.

- [ ] **Step 7: Commit**

```bash
git add spawn.py test_spawn.py
git commit -m "Capture what a session actually did, and say it out loud

--output-format json gives session_id, cost, turns and permission denials;
a board snapshot before/after gives the contract-§6 change signal. Each
spawn appends one JSONL ledger line under muster's runs/ and prints one
verdict: errored, progressed, waiting-on-human, or silent-failure — the
measured exit-0-having-done-nothing mode stops being silent. Report-only:
muster still does not judge or retry."
```

---

### Task 4: Drop `Bash(cp:*)` from the orchestrate command (M5)

**Files:**
- Modify: `orchestrate/commands/run.md:2`

**Interfaces:** none.

- [ ] **Step 1: Edit the allowed-tools line**

Change line 2 from:

```
allowed-tools: Bash(python3:*), Bash(git remote:*), Bash(git status:*), Bash(cp:*), Bash(ls:*), Read
```

to:

```
allowed-tools: Bash(python3:*), Bash(git remote:*), Bash(git status:*), Bash(ls:*), Read
```

- [ ] **Step 2: Verify and check for cp usage in the body**

Run: `grep -n 'cp ' orchestrate/commands/run.md`
If the body instructs a `cp` (contract install), leave the instruction — it now goes through the normal permission prompt where the human sees it. Add one line near it: `cp 는 일부러 사전 승인하지 않는다 — 게이트 없는 세션의 사전 승인된 cp 는 위조 토큰을 심을 수 있다(2026-07-27 리뷰 D2). 프롬프트에서 사람이 본다.`

- [ ] **Step 3: Commit**

```bash
git add orchestrate/commands/run.md
git commit -m "Stop pre-approving cp in the gate-free orchestrator session

The /orchestrate:run session carries zero rulebook gates (rulebooks are
deliberately globally disabled), so a pre-approved cp could plant a forged
approval token on the board silently. The one legitimate cp — installing
the contract — now goes through the permission prompt where the human sees
it."
```

---

### Task 5: `spawn.py doctor` — the hook-firing canary (M6)

**Files:**
- Modify: `spawn.py` (two functions above `main()`; `main()` dispatch + gate)
- Test: `test_spawn.py` (extend)

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `spawn.doctor() -> int` — runs the probe, writes `ROOT/runs/doctor-ok` (the `claude --version` line) on success.
  - `spawn.require_doctor(version: str | None = None) -> None` — sys.exit unless `runs/doctor-ok` matches the current version. Called in `main()` before a real spawn (not for dry-run/init/update/wake/doctor).

- [ ] **Step 1: Write the failing tests** (append to `test_spawn.py`)

```python
class RequireDoctor(unittest.TestCase):
    def _with_root(self, td):
        old = spawn.ROOT
        spawn.ROOT = Path(td)
        return old

    def test_halts_without_doctor_pass(self):
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                with self.assertRaises(SystemExit):
                    spawn.require_doctor(version="2.1.220 (Claude Code)")
            finally:
                spawn.ROOT = old

    def test_halts_on_version_change(self):
        # CLI 는 자동 업데이트된다. 훅이 headless 에서 도는 것은 문서가 아니라
        # 실측이 보증한다 — 버전이 바뀌면 보증도 끝난다.
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                (Path(td) / "runs").mkdir()
                (Path(td) / "runs" / "doctor-ok").write_text("2.1.219 (Claude Code)")
                with self.assertRaises(SystemExit):
                    spawn.require_doctor(version="2.1.220 (Claude Code)")
            finally:
                spawn.ROOT = old

    def test_passes_on_match(self):
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                (Path(td) / "runs").mkdir()
                (Path(td) / "runs" / "doctor-ok").write_text("2.1.220 (Claude Code)")
                spawn.require_doctor(version="2.1.220 (Claude Code)")  # no raise
            finally:
                spawn.ROOT = old
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 test_spawn.py -v` → FAIL, no attribute `require_doctor`.

- [ ] **Step 3: Implement** (above `main()`)

```python
def _claude_version() -> str:
    try:
        out = subprocess.run(["claude", "--version"], capture_output=True,
                             text=True, timeout=30)
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def require_doctor(version: str | None = None) -> None:
    """이 CLI 버전에서 훅이 headless 로 도는 것을 doctor 가 실측했는지 본다.

    룰북 집행 전체가 '플러그인 훅이 -p 세션에서 돈다'는 한 문장 위에 서
    있는데, 그 문장은 공식 문서에 없다 — 실측(2026-07-27, 2.1.220)뿐이다.
    CLI 는 자동 업데이트되므로, 버전이 바뀌면 게이트 전부가 소리 없이
    사라질 수 있다. 그래서 버전마다 한 번, 실측을 다시 요구한다.
    """
    v = version if version is not None else _claude_version()
    ok = ROOT / "runs" / "doctor-ok"
    if not v:
        sys.exit("claude --version 을 읽지 못했다. claude 가 PATH 에 있나?")
    if not ok.is_file() or ok.read_text().strip() != v:
        sys.exit(
            f"이 CLI({v})에서 훅이 headless 로 도는 것을 아직 실측하지 않았다.\n"
            f"먼저 돌려라: python3 spawn.py doctor   (실 세션 1회, 소액 과금)")


def doctor() -> int:
    """프로브 플러그인 하나로 실 세션을 띄워 UserPromptSubmit / PreToolUse 가
    실제로 발화하는지 잰다. 성공하면 runs/doctor-ok 에 CLI 버전을 적는다."""
    v = _claude_version()
    if not v:
        print("claude --version 실패", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        plug = Path(td) / "probe"
        (plug / ".claude-plugin").mkdir(parents=True)
        (plug / "hooks").mkdir()
        (plug / ".claude-plugin" / "plugin.json").write_text(json.dumps(
            {"name": "muster-probe", "version": "0.0.0",
             "description": "hook-firing canary"}))
        ups, pre = Path(td) / "ups", Path(td) / "pre"
        (plug / "hooks" / "hooks.json").write_text(json.dumps({"hooks": {
            "UserPromptSubmit": [{"hooks": [
                {"type": "command", "command": f"touch {ups}"}]}],
            "PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": f"touch {pre}"}]}],
        }}))
        work = Path(td) / "work"
        work.mkdir()
        subprocess.run(["git", "init", "-q", str(work)], check=False)
        # --model haiku: 프로브의 관심사는 훅 로딩이지 모델이 아니다. 싸게 간다.
        r = subprocess.run(
            ["claude", "-p", "--plugin-dir", str(plug), "--model", "haiku",
             "--max-turns", "2", "--output-format", "json"],
            cwd=work, input="Run this exact bash command and nothing else: echo ok",
            text=True, capture_output=True, timeout=180)
        fired_ups, fired_pre = ups.is_file(), pre.is_file()
    print(f"UserPromptSubmit: {'발화' if fired_ups else '침묵'} / "
          f"PreToolUse: {'발화' if fired_pre else '침묵'}  (CLI {v})")
    if fired_ups and fired_pre:
        d = ROOT / "runs"
        d.mkdir(exist_ok=True)
        (d / "doctor-ok").write_text(v)
        print("doctor-ok 기록. 이 버전에서 스폰이 열린다.")
        return 0
    print("훅이 headless 에서 발화하지 않는다 — 이 CLI 버전으로는 룰북 집행이 "
          "성립하지 않는다. 스폰은 계속 막힌다.", file=sys.stderr)
    return 1
```

- [ ] **Step 4: Wire into `main()`**

After the `update` dispatch add:

```python
    if a.role == "doctor":
        # 훅 발화 실측. 버전마다 한 번 — 룰북 집행의 전제조건이다.
        return doctor()
```

In the spawn path, right after `require_no_repo_config(...)` add:

```python
    if not a.dry_run:
        require_doctor()
```

- [ ] **Step 5: Run unit tests, then the real canary once**

Run: `python3 test_spawn.py -v && python3 test_gates.py` → PASS.
Run: `python3 spawn.py doctor` → expect `UserPromptSubmit: 발화 / PreToolUse: 발화`, `doctor-ok 기록`, exit 0. (One real haiku session, ~$0.03.)

- [ ] **Step 6: Commit**

```bash
git add spawn.py test_spawn.py
git commit -m "Make the load-bearing assumption a monitored invariant

Everything rests on plugin hooks firing in headless sessions, and that
sentence appears in no official doc — only in measurement. The CLI
auto-updates, so a regression would remove every gate while sessions keep
exiting 0. spawn.py doctor measures it per CLI version with a probe
plugin; spawns halt until the current version has a pass."
```

---

### Task 6: Document the new surface (README + protocol)

**Files:**
- Modify: `README.md` (명령 전부 section + a short outcomes note)
- Modify: `README.ko.md` (same)

**Interfaces:** none.

- [ ] **Step 1: Extend the command lists in both READMEs**

Add to the commands block (English README, mirrored in Korean):

```
python3 spawn.py doctor                       # measure hook firing on this CLI (once per version)
python3 spawn.py <role> "task" --unattended   # human absent: mint off, human gates stand
```

Add one short paragraph after the loop section (both languages, Korean shown):

```
### 세션이 끝나면

스폰마다 결과 JSON 을 받아 `runs/ledger.jsonl` 에 한 줄을 남기고 처분을
말한다 — `errored` / `progressed`(보드 변화) / `waiting-on-human`(§19 대기)
/ `silent-failure`(exit 0 인데 보드 무변화 — 실측된 침묵-사망 모드).
모든 스폰 세션에는 `TOKENMAXXXER_SPAWNED=1` 도장이 찍힌다: 그 세션의
프롬프트는 오케스트레이터가 쓴 텍스트이지 사람 턴이 아니므로, core 의
mint 훅은 거기서 승인을 발행하지 않는다. 사람의 승인은 사람의 세션에서만
발행된다.
```

- [ ] **Step 2: Verify consistency**

Run: `python3 test_spawn.py && python3 test_gates.py` → PASS.
Run: `grep -c 'doctor' README.md README.ko.md` → ≥1 each.

- [ ] **Step 3: Commit**

```bash
git add README.md README.ko.md
git commit -m "Document doctor, --unattended, the ledger and the spawn stamp"
```

---

## Self-review

**Spec coverage:** M1 → Task 2 (stamps + flag), M2 → Task 2 (acceptEdits),
M3 → Tasks 2+3 (json flag; capture/classify/ledger), M4 → Task 1, M5 →
Task 4, M6 → Task 5. M7–M13 and all C/R items are out of scope by the spec's
roadmap (items 3, 7–10).

**Placeholders:** none — every step carries exact code or the exact command
and expectation.

**Type consistency:** `spawn_cmd(settings_path, role, unattended)` defined in
Task 2, called with `(settings, a.role, a.unattended)` in Task 3.
`board_snapshot/session_result/classify/ledger_write` defined and consumed
with matching signatures. `require_doctor(version=None)` matches all three
tests. `ROOT` is monkeypatched in tests exactly as `spawn.ROOT`.

**Known seam:** Task 3's wiring references `a.unattended` — added in Task 2
Step 4, so tasks must land in order (they do; SDD runs them sequentially).
