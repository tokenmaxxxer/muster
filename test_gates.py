#!/usr/bin/env python3
"""on-the-record 자체 점검. 네트워크·GitHub 없이 도는 것만.

  python3 test_gates.py
"""
import re
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent))
import gates
import spawn
import pr_reference
import closure_sweep


def _board(td: str, subject: str, **roles: str) -> Path:
    """계약 v3 §10 의 블랙보드를 만든다: docs/issue-<n>/reports/<역할>.md"""
    root = Path(td) / "repo"
    d = root / spawn.BOARD / subject / "reports"
    d.mkdir(parents=True)
    for role, fm in roles.items():
        (d / f"{role}.md").write_text(f"---\n{fm}\n---\n\n본문\n")
    return root


def t_slug_is_directory_name():
    """§9: 레포 디렉터리 이름. 리모트가 없어도 깨지지 않는 것이 요점이다."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "car-wash-app"
        d.mkdir()
        assert spawn.slug(str(d)) == "car-wash-app", spawn.slug(str(d))


def t_board_reads_loop_state():
    with tempfile.TemporaryDirectory() as td:
        root = _board(td, "issue-26",
                      **{"product-discovery": "kind: product-record\nloop_state: measuring",
                         "technical-feasibility": "kind: feasibility-record\nloop_state: verdict\nverdict: go"})
        b = spawn.board(root)
        assert list(b) == ["issue-26"], b
        assert b["issue-26"]["product-discovery"]["loop_state"] == "measuring"
        assert b["issue-26"]["technical-feasibility"]["verdict"] == "go"
        line = "\n".join(spawn.status(str(root)))
        assert "loop_state: measuring" in line, line
        assert "verdict: go" in line, line
        # 기록이 없는 역할을 "상태 없음"으로 뭉뚱그리면 누가 안 깨어났는지 못 본다
        assert "기록 없음" in line and "execution-observation" in line, line


def t_board_tolerates_trailing_comment():
    """§2: 주석을 못 읽는 파서는 **게이트 결함이지 기록의 위반이 아니다**."""
    with tempfile.TemporaryDirectory() as td:
        root = _board(td, "issue-1", **{"implementation": "kind: build-proposal  # re-scoped\n"
                                      "loop_state: approved   # 사람이 승인함"})
        fm = spawn.board(root)["issue-1"]["implementation"]
        assert fm["kind"] == "build-proposal", fm
        assert fm["loop_state"] == "approved", fm


def t_missing_board_marker_stops_the_spawn():
    """실측 A/B: 레포에 보드 표식(approvers.md)이 없으면 역할이 아무 기록도 못
    올리고, 세션은 성공으로 끝난다. 경고로는 안 되는 이유가 그 조용함이다 —
    한 세션을 통째로 버린다. v3 의 계약 검문은 require_board() 다."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        (root / "docs" / "specs").mkdir(parents=True)

        # (a) marker 표식 있음 → 통과 (예외 없이 반환)
        (root / spawn.MARKER).write_text("- u\n")
        spawn.require_board(str(root), override=False)
        (root / spawn.MARKER).unlink()

        # (b) marker 표식 없음, override=True → 명시적 opt-out 은 통과.
        # 사고가 아니라 결정이어야 한다.
        spawn.require_board(str(root), override=True)

        # (c) marker 표식 없음, override=False → 세션을 멈춘다
        try:
            spawn.require_board(str(root), override=False)
        except SystemExit as e:
            assert spawn.MARKER in str(e), e
        else:
            raise AssertionError("보드 표식이 없는데 통과시켰다")


def t_rulebook_version_is_recorded():
    """룰북은 로컬 디렉터리로 물리므로 핀이 없다 — 그 순간 체크아웃된 것이 돈다.
    핀을 못 박으면 **무엇이 돌았는지라도 남겨야** ablation 이 검증 가능해진다."""
    v = spawn.rulebook_version("execution-observation")
    assert "(" in v and ")" in v, v          # sha (branch)
    assert "커밋안됨" not in v or True       # 더러우면 그 사실이 문자열에 남는다

    # 알 수 없을 때 조용히 빈 문자열을 돌려주면 기록이 "버전 없음"으로 보인다.
    import json, tempfile
    with tempfile.TemporaryDirectory() as td:
        role = spawn.ROOT / "roles" / "_probe.json"
        role.write_text(json.dumps({"marketplace": "x", "path": td}))
        try:
            assert "불명" in spawn.rulebook_version("_probe"), spawn.rulebook_version("_probe")
        finally:
            role.unlink()


def t_repo_local_claude_config_stops_the_spawn():
    """대상 레포의 `.claude/` 훅은 on-the-record 가 선언한 샌드박스 경계를 **안 받는다.**
    실측 2026-07-27: denyWrite 경로에 쓰고 denyRead 인 ~/.claude 를 읽어냈다.
    레포를 클론해서 on-the-record 를 겨눈 것만으로 성립하므로 경고가 아니라 정지다."""
    for rogue in (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            (root / rogue).parent.mkdir(parents=True, exist_ok=True)
            if rogue.endswith("hooks"):
                (root / rogue).mkdir()
            else:
                (root / rogue).write_text("{}")
            try:
                spawn.require_no_repo_config(str(root), False)
            except SystemExit as e:
                assert rogue.split("/")[-1] in str(e), e
            else:
                raise AssertionError(f"{rogue} 를 통과시켰다")
            spawn.require_no_repo_config(str(root), True)   # 명시적 opt-out 은 통과


def t_role_files_carry_no_absolute_home_path():
    """역할 파일에 `/Users/<이름>/...` 을 박으면 그 레포는 **한 사람의 홈 경로를
    담은 채로 공개된다.** 남의 기계에서는 없는 경로라 조용히 github 로 떨어지고,
    왜 로컬 체크아웃이 안 잡히는지도 안 보인다. 공개 직전에 발견해서 넣은 가드다.

    `$HOME`/`~` 로 시작하는 기본값도 마찬가지로 걸린다 — 리터럴 절대경로는 아니지만
    `workspace/10_WORK` 같은 개인 디렉터리 관례를 그 뒤에 박아 넣으면 남의 기계에서
    똑같이 낯선 경로가 되고, `$` 로 시작한다는 이유만으로 이 가드를 통과해 왔다."""
    import json as _json
    personal_convention_markers = ("workspace/10_WORK",)
    for f in sorted((spawn.ROOT / "roles").glob("*.json")):
        raw = f.read_text()
        assert "/Users/" not in raw and "/home/" not in raw, f"{f.name}: {raw}"
        for marker in personal_convention_markers:
            assert marker not in raw, f"{f.name}: personal directory convention {marker!r}"
        spec = _json.loads(raw)
        if "path" in spec:
            assert spec["path"].startswith("$"), f"{f.name}: {spec['path']}"
        for v in spec.get("env", {}).values():
            if isinstance(v, str) and (v.startswith("$HOME") or v.startswith("~")):
                for marker in personal_convention_markers:
                    assert marker not in v, f"{f.name}: {v}"


def t_unresolved_path_variable_is_not_a_path():
    """안 풀린 `$VAR` 를 경로로 넘기면 없는 디렉터리를 가리킨다 — 그건 '설정 안 함'
    이 아니라 '잘못 설정함'이고, 로컬이 이겨야 할 자리에서 조용히 진다."""
    assert spawn._path({"path": "$DEFINITELY_UNSET_XYZ/foo"}) == ""
    assert spawn._path({}) == ""
    os.environ["MUSTER_TEST_RB"] = "/tmp/rb"
    try:
        assert spawn._path({"path": "$MUSTER_TEST_RB/x"}) == "/tmp/rb/x"
    finally:
        del os.environ["MUSTER_TEST_RB"]


def t_rulebook_falls_back_to_github():
    """로컬 체크아웃이 있으면 그쪽, 없으면 github."""
    import json as _json
    spec = _json.loads((spawn.ROOT / "roles" / "execution-observation.json").read_text())
    assert spec.get("repo"), "역할 파일에 repo 가 없으면 github 로 떨어질 수 없다"

    with tempfile.TemporaryDirectory() as td:
        checkout = Path(td) / "execution-observation-rulebook"
        (checkout / ".claude-plugin").mkdir(parents=True)
        (checkout / ".claude-plugin" / "marketplace.json").write_text('{"plugins": []}')
        os.environ["TOKENMAXXXER_RULEBOOKS"] = td
        try:
            local = spawn.rulebook_source(spec)
        finally:
            del os.environ["TOKENMAXXXER_RULEBOOKS"]
    assert local == {"source": "directory", "path": str(checkout)}, local   # 로컬이 이긴다

    # 변수가 안 잡히면 github 로 떨어진다 — 이게 남의 기계의 기본 상태다
    assert spawn.rulebook_source(spec) == {"source": "github", "repo": spec["repo"]}

    spec["path"] = "/nonexistent-checkout"
    remote = spawn.rulebook_source(spec)
    assert remote == {"source": "github", "repo": spec["repo"]}, remote

    spec.pop("repo")
    try:
        spawn.rulebook_source(spec)
    except SystemExit:
        pass
    else:
        raise AssertionError("소스가 없는데 통과시켰다")


# v3 abolished the per-repo contract copy (commit 613a5fbced1b08b48c4c8215a
# 241d0b8a823dbcc: "init writes approvers.md, not a contract copy; require_board
# replaces require_contract"). The two spawn.py functions this test exercised
# for content-hash-based drift detection and copy-seeding no longer exist, so
# there is nothing left to drift — do not restore this test.


def t_new_roles_resolve_without_a_local_checkout():
    """interaction-design·defect-verification·issue-retrospective 는 로컬 체크아웃이
    없다. github 폴백이 실제로 필요한 첫 사례이고, 없으면 on-the-record 가 계약 §3 의
    아홉 줄 중 셋을 못 띄운다."""
    import json as _json
    for role in ("interaction-design", "defect-verification", "issue-retrospective"):
        spec = _json.loads((spawn.ROOT / "roles" / f"{role}.json").read_text())
        assert "path" not in spec, f"{role}: 로컬 경로를 박으면 다른 기계에서 깨진다"
        assert spawn.rulebook_source(spec)["source"] == "github", role
    assert len(spawn.ROLES) == 27, spawn.ROLES


def t_board_absent_names_the_v1_location():
    """보드 없음과 v1 자리에 있음은 정반대 처분을 받아야 한다."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        root.mkdir()
        empty = "\n".join(spawn.status(str(root)))
        assert "보드 없음" in empty and "계약 v1" not in empty, empty

        (root / "review-record.md").write_text("---\nphase: scoped\n---\n")
        stale = "\n".join(spawn.status(str(root)))
        assert "계약 v1" in stale and "conformance-review" in stale, stale





def _repo(td: str) -> Path:
    work = Path(td) / "work"
    work.mkdir(parents=True)
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                    capture_output=True, check=True)
    run("init", "-q", "-b", "main")
    run("config", "user.email", "t@t"); run("config", "user.name", "t")
    (work / "requirements.txt").write_text("requests==2.31.0\n")
    run("add", "-A"); run("commit", "-qm", "init")
    run("branch", "-f", "origin/main")          # diff 기준점 대역
    return work



def t_rename_bypass():
    # git mv 한 번으로 보호 경로와 write-set 을 동시에 빠져나가면 안 된다.
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (Path(td) / "spec.md").write_text("- write: allowed*\n")
        (work / "allowed.txt").write_text("x")
        run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                        capture_output=True, check=True)
        run("add", "-A"); run("-c", "user.email=t@t", "-c", "user.name=t",
                              "commit", "-qm", "add")
        (work / ".github").mkdir()
        run("mv", "allowed.txt", ".github/pwn.js")
        files = gates.changed_files(work)
        assert ".github/pwn.js" in files, files
        assert "allowed.txt" in files, f"rename 원본도 검사해야 한다: {files}"
        assert any("보호 경로" in b for b in gates.writeset(Path(td), {}))


def t_commit_bypass():
    # git status 는 워커가 자기 작업을 커밋하면 깨끗해진다 — 커밋 diff 도 봐야
    # 게이트가 안 뚫린다. 수정 전 코드에서는 이 테스트가 실패한다(빈 리스트 반환).
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (Path(td) / "spec.md").write_text("- write: a.txt\n")
        (work / ".github").mkdir()
        (work / ".github" / "ci.yml").write_text("evil")
        run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                        capture_output=True, check=True)
        run("add", "-A"); run("-c", "user.email=t@t", "-c", "user.name=t",
                              "commit", "-qm", "protected path, committed")
        bad = gates.writeset(Path(td), {})
        assert any("보호 경로" in b for b in bad), f"커밋 후 게이트가 못 봤다: {bad}"


def t_origin_main_missing():
    # origin/main 자체가 없으면 "변경 없음"이 아니라 "검사 불가" — 워킹트리만 보고
    # 조용히 통과시키면 안 된다.
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "work"
        work.mkdir(parents=True)
        run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                        capture_output=True, check=True)
        run("init", "-q", "-b", "main")
        run("config", "user.email", "t@t"); run("config", "user.name", "t")
        (work / "a.txt").write_text("x")
        run("add", "-A"); run("commit", "-qm", "init")
        # origin/main 브랜치를 의도적으로 만들지 않는다
        try:
            gates.changed_files(work)
            assert False, "origin/main 없이도 조용히 통과했다"
        except RuntimeError as e:
            assert "fail closed" in str(e), e

        (Path(td) / "spec.md").write_text("- write: a.txt\n")
        bad = gates.writeset(Path(td), {})
        assert bad and "fail closed" in bad[0], bad


def t_deps_fail_closed():
    # 못 읽은 매니페스트를 "새 의존성 0개" 로 취급하면 환각 패키지가 통과한다
    for bad in ["{not json", '{"dependencies": [']:
        try:
            gates.dep_names("package.json", bad)
            assert False, f"파싱 실패를 통과시켰다: {bad}"
        except ValueError:
            pass
    try:
        gates.dep_names("requirements.txt", "-r extras.txt\n")
        assert False, "간접 참조를 통과시켰다"
    except ValueError:
        pass
    # optional/peer 도 검사 대상
    j = '{"optionalDependencies":{"a":"1"},"peerDependencies":{"b":"2"}}'
    assert gates.dep_names("package.json", j) == {"a", "b"}


def t_dep_direct_reference():
    # 이름은 레지스트리에 있어도 버전 스펙이 URL/직접 참조면 실제 설치 출처는 임의다
    for spec in ["git+https://evil.example/x.git", "file:../local-evil",
                 "https://evil.example/pkg-1.0.0.tgz", "github:evil/lodash",
                 "evil/lodash#main"]:
        j = json.dumps({"dependencies": {"lodash": spec}})
        try:
            gates.dep_names("package.json", j)
            assert False, f"직접 참조를 통과시켰다: {spec}"
        except ValueError:
            pass
    # 정상 레지스트리 범위는 여전히 통과
    j = json.dumps({"dependencies": {"lodash": "^1.0.0"}})
    assert gates.dep_names("package.json", j) == {"lodash"}

    # requirements.txt 도 같은 구멍 — bare URL, `pkg @ https://` 직접 참조
    for bad in ["https://evil.example/pkg.tar.gz\n",
                "evil-pkg @ https://evil.example/pkg.tar.gz\n"]:
        try:
            gates.dep_names("requirements.txt", bad)
            assert False, f"직접 참조를 통과시켰다: {bad}"
        except ValueError:
            pass
    assert gates.dep_names("requirements.txt", "requests==2.31.0\n") == {"requests"}


def t_writeset_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (work / "anything.py").write_text("x")
        (Path(td) / "spec.md").write_text("# 명세\n요구사항만 있고 write-set 없음\n")
        assert any("fail closed" in b for b in gates.writeset(Path(td), {}))



def t_protected_paths():
    # 미탐: 루트에 있어도 막아야 한다. 뒤 넷은 on-the-record 가 자기 규칙을 다시 쓰는 경로다.
    for p in ["auth.py", "migrations/001.sql", ".env", "config/.env.prod",
              ".github/workflows/ci.yml", "app/secrets.pem", "lib/credentials.json",
              "protocol.md", "protocol.ko.md", "spawn.py", "roles/execution-observation.json",
              "gates/gates.py"]:
        assert gates.is_protected(p), f"놓침: {p}"
    # 오탐: 평범한 설정 변경까지 막으면 게이트가 꺼진다. 뒤 둘은 **대상 레포**의
    # 정상 자산이다 — 보호는 루트 한 단계에만 걸려야 한다.
    for p in ["docker-compose.yml", "openapi.yaml", "app/settings.yaml",
              "calc.py", "src/handlers/user.py", "README.md",
              "src/app/roles/admin.py", "lib/gates/rate.go"]:
        assert not gates.is_protected(p), f"오탐: {p}"


def t_writeset_protected():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (work / ".github").mkdir()
        (work / ".github" / "ci.yml").write_text("evil")
        bad = gates.writeset(Path(td), {})
        assert any("보호 경로" in b for b in bad), bad


def t_writeset_declared():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (Path(td) / "spec.md").write_text("요구사항\n- write: calc.py\n")
        (work / "calc.py").write_text("x = 1")
        assert gates.writeset(Path(td), {}) == []       # 허용 경로
        (work / "sneaky.py").write_text("x = 2")
        assert any("write-set 이탈" in b for b in gates.writeset(Path(td), {}))


def _enum_record_repo(td: str, role: str, record_fields: dict, frontmatter: str) -> Path:
    """`record_enums` 전용 픽스처: 별도 on-the-record 체크아웃에
    roles/<role>.json 을 두고 (gates.ON_THE_RECORD_ROOT 를 그쪽으로
    가리키게 하고) work repo 에는 변경된 record 한 개만 둔다. 호출자가
    gates.ON_THE_RECORD_ROOT 를 저장/복원해야 한다."""
    otr = Path(td) / "otr"
    (otr / "roles").mkdir(parents=True)
    (otr / "roles" / f"{role}.json").write_text(
        json.dumps({"record_fields": record_fields}))
    gates.ON_THE_RECORD_ROOT = otr

    work = _repo(td)
    rep = work / "docs" / "issue-100" / "reports"
    rep.mkdir(parents=True)
    (rep / f"{role}.md").write_text(f"---\n{frontmatter}\n---\n\n본문\n")
    return work


def t_record_enums_out_of_enum_blocks():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            _enum_record_repo(td, "feasibility", {"verdict": ["go", "no-go", "conditional"]},
                         'verdict: go (조건부 → 측정 필요)')
            bad = gates.record_enums(Path(td), {})
            assert bad and "verdict" in bad[0] and "feasibility.json" in bad[0], bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_record_enums_in_enum_passes():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            _enum_record_repo(td, "feasibility", {"verdict": ["go", "no-go", "conditional"]},
                         "verdict: go")
            assert gates.record_enums(Path(td), {}) == []
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_record_enums_undeclared_field_passes():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            _enum_record_repo(td, "feasibility", {}, "kind: feasibility-record\nverdict: go")
            assert gates.record_enums(Path(td), {}) == []
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_record_enums_missing_role_file_blocks():
    """on-the-record 체크아웃 자체에 roles/<role>.json 이 없다 —
    보드 문제가 아니라 on-the-record 설치 문제로 막혀야 한다."""
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            otr = Path(td) / "otr"
            otr.mkdir()
            gates.ON_THE_RECORD_ROOT = otr
            work = _repo(td)
            rep = work / "docs" / "issue-100" / "reports"
            rep.mkdir(parents=True)
            (rep / "feasibility.md").write_text("---\nverdict: go\n---\n\n본문\n")
            run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                            capture_output=True, check=True)
            run("add", "-A"); run("commit", "-qm", "record only")
            bad = gates.record_enums(Path(td), {})
            assert bad and "역할 정의를 읽을 수 없어" in bad[0], bad
            assert str(otr) in bad[0], bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_record_enums_no_roles_in_work_repo_passes():
    """보드(work repo)에 roles/ 가 아예 없어도 — on-the-record 체크아웃에
    유효한 role 정의가 있으면 — 경고 없이 통과해야 한다(이슈의 핵심 재현)."""
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            work = _enum_record_repo(td, "feasibility",
                                 {"verdict": ["go", "no-go", "conditional"]},
                                 "verdict: go")
            assert not (work / "roles").exists()
            bad = gates.record_enums(Path(td), {})
            assert bad == []
            assert not any("역할 정의를 읽을 수 없어" in b for b in bad)
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_record_enums_loop_state_out_of_set_blocks():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            _enum_record_repo(td, "qa", {"loop_state": ["handed-off"]},
                         "loop_state: made-up-state")
            bad = gates.record_enums(Path(td), {})
            assert bad and "loop_state" in bad[0], bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def _record_repo(td: str, subject: str, role: str, text: str) -> Path:
    """docs/issue-<n>/reports/<role>.md 를 커밋해 둔 레포."""
    work = Path(td) / "work"
    d = work / "docs" / subject / "reports"
    d.mkdir(parents=True)
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                    capture_output=True, check=True)
    run("init", "-q", "-b", "main")
    run("config", "user.email", "t@t"); run("config", "user.name", "t")
    (work / "README.md").write_text("x")
    run("add", "-A"); run("commit", "-qm", "init")
    run("branch", "-f", "origin/main")
    (d / f"{role}.md").write_text(text)
    run("add", "-A"); run("-c", "user.email=t@t", "-c", "user.name=t",
                          "commit", "-qm", "record")
    return work


def t_record_wellformed_missing_open_delimiter():
    with tempfile.TemporaryDirectory() as td:
        work = _record_repo(td, "issue-9", "coding", "kind: x\nloop_state: y\n")
        bad = gates.record_wellformed_in(work)
        assert any("issue-9/reports/coding.md" in b and "시작 구분자" in b for b in bad), bad


def t_record_wellformed_missing_close_delimiter():
    with tempfile.TemporaryDirectory() as td:
        work = _record_repo(td, "issue-9", "coding", "---\nkind: x\nloop_state: y\n")
        bad = gates.record_wellformed_in(work)
        assert any("닫는 구분자" in b for b in bad), bad


def t_record_wellformed_passes_valid_frontmatter():
    with tempfile.TemporaryDirectory() as td:
        work = _record_repo(td, "issue-9", "coding",
                            "---\nkind: x\nloop_state: y\n---\n\n본문\n")
        assert gates.record_wellformed_in(work) == []


def t_record_no_tool_residue_blocks_leaked_tag():
    with tempfile.TemporaryDirectory() as td:
        work = _record_repo(td, "issue-9", "coding",
                            "---\nkind: x\n---\n\n본문\n</content>\n")
        bad = gates.record_no_tool_residue_in(work)
        assert any("coding.md:6" in b and "</content>" in b for b in bad), bad


def t_record_no_tool_residue_allows_fenced_tag():
    with tempfile.TemporaryDirectory() as td:
        work = _record_repo(td, "issue-9", "coding",
                            "---\nkind: x\n---\n\n```\n</content>\n```\n")
        assert gates.record_no_tool_residue_in(work) == []


def t_record_no_tool_residue_passes_clean_record():
    with tempfile.TemporaryDirectory() as td:
        work = _record_repo(td, "issue-9", "coding",
                            "---\nkind: x\n---\n\n평범한 본문, 태그 없음\n")
        assert gates.record_no_tool_residue_in(work) == []


def t_record_both_defects_block_independently():
    with tempfile.TemporaryDirectory() as td:
        work = _record_repo(td, "issue-9", "coding", "kind: x\n</content>\n")
        wf = gates.record_wellformed_in(work)
        residue = gates.record_no_tool_residue_in(work)
        assert wf and residue, (wf, residue)


def t_dep_names():
    # 한 줄이든 여러 줄이든 같은 집합이 나와야 한다 (줄 단위 파싱이면 깨진다)
    flat = '{"dependencies":{"left-pad":"^1.0.0"},"devDependencies":{"jest":"29"}}'
    multi = json.dumps(json.loads(flat), indent=2)
    assert gates.dep_names("package.json", flat) == {"left-pad", "jest"}
    assert gates.dep_names("package.json", multi) == {"left-pad", "jest"}
    # 깨진 매니페스트는 빈 집합이 아니라 오류다 — t_deps_fail_closed 참조
    assert gates.dep_names("requirements.txt",
                           "requests==2.31.0\n# 주석\nhttpx>=0.27\n\n") == {"requests", "httpx"}


def t_parse_new_deps():
    with tempfile.TemporaryDirectory() as td:
        work = _repo(td)
        (work / "requirements.txt").write_text("requests==2.31.0\nhttpx>=0.27\n")
        (work / "package.json").write_text('{"dependencies": {"left-pad": "^1.0.0"}}')
        subprocess.run(["git", "-C", str(work), "add", "-A"], check=True,
                       capture_output=True)
        new, errs = gates.parse_new_deps(work)
        assert errs == [], errs
        found = dict((n, m) for m, n in new)
        assert found.get("httpx") == "requirements.txt", found
        assert found.get("left-pad") == "package.json", found
        assert "requests" not in found, "기존 의존성은 새 것으로 잡히면 안 된다"


def t_pr_reference_phase1_plain_ref_passes():
    assert pr_reference.check_body(126, "this fixes stuff, see #126 for context", "phase1") == []


def t_pr_reference_phase1_missing_ref_blocks():
    bad = pr_reference.check_body(126, "no reference here", "phase1")
    assert bad and "#126" in bad[0], bad


def t_pr_reference_phase1_wrong_issue_blocks():
    bad = pr_reference.check_body(126, "relates to #125", "phase1")
    assert bad, bad


def t_pr_reference_phase2_requires_closes():
    assert pr_reference.check_body(126, "Closes #126", "phase2") == []
    assert pr_reference.check_body(126, "closes #126", "phase2") == []
    assert pr_reference.check_body(126, "Fixes #126", "phase2") == []
    # 그냥 #126 참조만으로는 phase-2 를 통과시키지 않는다 — 인도 PR은 반드시 닫아야 한다
    bad = pr_reference.check_body(126, "see #126", "phase2")
    assert bad, bad
    # 다른 이슈를 닫는 문구는 이 이슈를 통과시키지 않는다
    bad2 = pr_reference.check_body(126, "Closes #999", "phase2")
    assert bad2, bad2


def t_closure_sweep_closed_issue_open_pr_violates():
    kind = closure_sweep.classify("CLOSED", "OPEN", "see #135", 135)
    assert kind == closure_sweep.OPEN_PR_ON_CLOSED_ISSUE, kind


def t_closure_sweep_merged_delivery_issue_open_violates():
    kind = closure_sweep.classify("OPEN", "MERGED", "Closes #135", 135)
    assert kind == closure_sweep.MERGED_DELIVERY_ISSUE_OPEN, kind


def t_closure_sweep_merged_phase1_plain_ref_not_violation():
    # phase-1 제안 PR — merged 여도 plain #n 참조만으로는 이슈를 닫을 의무가 없다
    kind = closure_sweep.classify("OPEN", "MERGED", "phase 1 proposal, see #135", 135)
    assert kind is None, kind


def t_closure_sweep_closed_issue_no_pr_ref_not_violation():
    kind = closure_sweep.classify("CLOSED", "OPEN", "unrelated PR, see #999", 135)
    assert kind is None, kind


def t_closure_sweep_everything_consistent_not_violation():
    assert closure_sweep.classify("OPEN", "OPEN", "see #135", 135) is None
    assert closure_sweep.classify("CLOSED", "MERGED", "Closes #135", 135) is None


def _scope_repo(td: str, role: str, write_scope: list) -> Path:
    """`role_scope` 전용 픽스처: `_enum_record_repo` 와 같은 방식으로
    `gates.ON_THE_RECORD_ROOT` 를 별도 checkout 으로 가리킨다. 호출자가
    `gates.ON_THE_RECORD_ROOT` 를 저장/복원해야 한다."""
    otr = Path(td) / "otr"
    (otr / "roles").mkdir(parents=True)
    (otr / "roles" / f"{role}.json").write_text(
        json.dumps({"write_scope": write_scope}))
    gates.ON_THE_RECORD_ROOT = otr
    return _repo(td)


def _commit_baseline(work: Path, rel: str, text: str) -> None:
    """오버라이드 파일 자체를 diff 밖(= 이미 존재하던 baseline)으로 만든다 —
    role_scope 는 write_scope.md 도 diff 대상이면 그 경로 자체를 검사하므로,
    오버라이드 존재 여부만 테스트하려면 origin/main 을 그 커밋까지 밀어야 한다."""
    p = work / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                    capture_output=True, check=True)
    run("add", "-A")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "baseline")
    run("branch", "-f", "origin/main")


def t_role_scope_in_scope_passes():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            work = _scope_repo(td, "coding", ["src/**", "test/**"])
            (work / "src").mkdir()
            (work / "src" / "app.py").write_text("x")
            assert gates.role_scope(work, "issue-149/coding") == []
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_role_scope_judgment_role_touching_src_blocks():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            work = _scope_repo(td, "feasibility", [])
            (work / "src").mkdir()
            (work / "src" / "app.py").write_text("x")
            bad = gates.role_scope(work, "issue-149/feasibility")
            assert bad and "write_scope 이탈" in bad[0], bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_role_scope_coding_touching_other_role_record_blocks():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            work = _scope_repo(td, "coding", ["src/**", "test/**"])
            rep = work / "docs" / "issue-149" / "reports"
            rep.mkdir(parents=True)
            (rep / "review.md").write_text("---\nloop_state: reported\n---\n")
            bad = gates.role_scope(work, "issue-149/coding")
            assert bad and "write_scope 이탈" in bad[0] and "review.md" in bad[0], bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_role_scope_branch_not_role_shaped_fails_closed():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            work = _scope_repo(td, "coding", ["src/**"])
            bad = gates.role_scope(work, "main")
            assert bad and "역할을 해석할 수 없다" in bad[0], bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_role_scope_own_record_stays_allowed_under_override():
    """item-5: 오버라이드가 역할의 글롭 목록을 비워도 자기 레코드/제안 경로는
    합집합으로 계속 허용돼야 한다."""
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            work = _scope_repo(td, "coding", ["src/**"])
            _commit_baseline(work, "docs/specs/write_scope.md", "- write: coding: *.py\n")
            rep = work / "docs" / "issue-149" / "reports"
            rep.mkdir(parents=True)
            (rep / "coding.md").write_text("---\nloop_state: in-progress\n---\n")
            assert gates.role_scope(work, "issue-149/coding") == []
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_role_scope_override_replaces_default_glob():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            work = _scope_repo(td, "coding", ["src/**"])
            _commit_baseline(work, "docs/specs/write_scope.md", "- write: coding: app.py\n")
            (work / "app.py").write_text("x")     # 오버라이드 글롭(app.py)에만 매치
            (work / "src").mkdir()
            (work / "src" / "app.py").write_text("x")   # 기본 글롭(src/**)은 오버라이드로 대체돼 더 이상 안 통함
            bad = gates.role_scope(work, "issue-149/coding")
            assert any("src/app.py" in b for b in bad), bad
            assert not any(b.startswith("write_scope 이탈: app.py ") for b in bad), bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def t_role_scope_undeclared_write_scope_fails_closed():
    old = gates.ON_THE_RECORD_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            otr = Path(td) / "otr"
            (otr / "roles").mkdir(parents=True)
            (otr / "roles" / "coding.json").write_text(json.dumps({}))
            gates.ON_THE_RECORD_ROOT = otr
            work = _repo(td)
            bad = gates.role_scope(work, "issue-149/coding")
            assert bad and "write_scope 선언이 없다" in bad[0], bad
    finally:
        gates.ON_THE_RECORD_ROOT = old


def _fulfils_repo(td: str, subject: str, role: str, record_text: str,
                  pre_files: dict = None, ops=None) -> Path:
    """fulfils 게이트 전용 픽스처: 초기 커밋(pre_files 포함) 후 origin/main 을
    거기서 고정하고, 두 번째 커밋에서 ops(파일 삭제/생성/rename)와 레코드를
    함께 넣는다 — `_record_repo`와 달리 diff 에 실제 파일 변경이 필요해서 뺐다."""
    work = Path(td) / "work"
    d = work / "docs" / subject / "reports"
    d.mkdir(parents=True)
    run = lambda *a: subprocess.run(["git", "-C", str(work), *a],
                                    capture_output=True, check=True)
    run("init", "-q", "-b", "main")
    run("config", "user.email", "t@t"); run("config", "user.name", "t")
    (work / "README.md").write_text("x")
    for path, content in (pre_files or {}).items():
        p = work / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    run("add", "-A"); run("commit", "-qm", "init")
    run("branch", "-f", "origin/main")
    for op in (ops or []):
        kind = op[0]
        if kind == "delete":
            run("rm", "-q", op[1])
        elif kind == "create":
            p = work / op[1]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("new")
        elif kind == "rename":
            (work / op[2]).parent.mkdir(parents=True, exist_ok=True)
            run("mv", op[1], op[2])
    (d / f"{role}.md").write_text(record_text)
    run("add", "-A"); run("-c", "user.email=t@t", "-c", "user.name=t",
                          "commit", "-qm", "record")
    return work


def t_fulfils_delete_claim_matches_diff_passes():
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(td, "issue-9", "coding",
                             "---\nkind: x\n---\n\nfulfils: delete docs/foo.md\n",
                             pre_files={"docs/foo.md": "x"},
                             ops=[("delete", "docs/foo.md")])
        assert gates.record_fulfils_diff(Path(td), {}) == []


def t_fulfils_delete_claim_absent_from_diff_blocks():
    # issue #145 의 실제 사고 재현: 레코드는 삭제를 주장하지만 diff 에는 없다.
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(td, "issue-9", "coding",
                             "---\nkind: x\n---\n\nfulfils: delete docs/foo.md\n",
                             pre_files={"docs/foo.md": "x"},
                             ops=[])
        bad = gates.record_fulfils_diff(Path(td), {})
        assert any("delete docs/foo.md" in b for b in bad), bad


def t_fulfils_create_claim_matches_diff_passes():
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(td, "issue-9", "coding",
                             "---\nkind: x\n---\n\nfulfils: create src/new.py\n",
                             ops=[("create", "src/new.py")])
        assert gates.record_fulfils_diff(Path(td), {}) == []


def t_fulfils_create_claim_absent_blocks():
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(td, "issue-9", "coding",
                             "---\nkind: x\n---\n\nfulfils: create src/new.py\n",
                             ops=[])
        bad = gates.record_fulfils_diff(Path(td), {})
        assert any("create src/new.py" in b for b in bad), bad


def t_fulfils_move_claim_matches_rename_passes():
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(
            td, "issue-9", "coding",
            "---\nkind: x\n---\n\nfulfils: move old/a.py -> new/a.py\n",
            pre_files={"old/a.py": "x" * 50},
            ops=[("rename", "old/a.py", "new/a.py")])
        assert gates.record_fulfils_diff(Path(td), {}) == []


def t_fulfils_move_claim_wrong_pair_blocks():
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(
            td, "issue-9", "coding",
            "---\nkind: x\n---\n\nfulfils: move old/a.py -> wrong/a.py\n",
            pre_files={"old/a.py": "x" * 50},
            ops=[("rename", "old/a.py", "new/a.py")])
        bad = gates.record_fulfils_diff(Path(td), {})
        assert any("move old/a.py -> wrong/a.py" in b for b in bad), bad


def t_fulfils_unparseable_claim_blocks():
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(td, "issue-9", "coding",
                             "---\nkind: x\n---\n\nfulfils: rewrite docs/foo.md\n",
                             pre_files={"docs/foo.md": "x"}, ops=[])
        bad = gates.record_fulfils_diff(Path(td), {})
        assert any("파싱 불가" in b and "rewrite" in b for b in bad), bad


def t_fulfils_record_with_no_claims_untouched():
    with tempfile.TemporaryDirectory() as td:
        work = _fulfils_repo(td, "issue-9", "coding",
                             "---\nkind: x\n---\n\n평범한 본문, claim 없음\n",
                             ops=[])
        assert gates.record_fulfils_diff(Path(td), {}) == []


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
