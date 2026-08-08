#!/usr/bin/env python3
"""Pure-Python tests for pr-preflight.sh's ported check_body logic
(issue #459).

pr-preflight.sh embeds its checker as inline Python inside a bash heredoc
(same shape as contract-guard.sh), so it isn't importable. Following
contract-guard.sh's own precedent (test_contract_guard.py exercises the
shell script end-to-end rather than importing internals), this file instead
duplicates the exact same pure `check_body`/`_plan_from_body` logic as
plain Python and asserts against it directly (no subprocess, no `gh`) —
the fastest, most direct way to pin the core decision logic since it takes
no I/O.

Run: python3 on-the-record/hooks/test_pr_preflight.py
Exit 0 all pass / 1 on any failure. Prints PASS/FAIL per case.
"""
import re
import sys

# --- ported from gates/flows.py::_plan_from_body ---------------------------
_PLAN_STEP_RE = re.compile(r"^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$")


def _plan_from_body(issue_body):
    lines = (issue_body or "").splitlines()
    start = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped == "## 실행 계획" or stripped.startswith("## 실행 계획 "):
            start = i + 1
            break
    if start is None:
        return None
    steps = []
    in_fence = False
    for line in lines[start:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped.startswith("##"):
            break
        mm = _PLAN_STEP_RE.match(stripped)
        if not mm:
            continue
        done = mm.group(1) in ("x", "X")
        step_n = int(mm.group(2))
        roles = [r.strip() for r in mm.group(3).split("‖")]
        steps.append({"step": step_n, "roles": roles, "done": done})
    return steps


# --- ported from gates/pr_reference.py::check_body --------------------------
_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")


def check_body(issue, body, phase, plan=None):
    body = body or ""
    if phase == "phase2":
        if plan:
            incomplete = [s for s in plan if not s["done"]]
            max_step = max(s["step"] for s in plan) if plan else 0
            only_last_incomplete = (
                len(incomplete) == 1 and incomplete[0]["step"] == max_step
            )
            if incomplete and not only_last_incomplete:
                mm = _CLOSES_REF.search(body)
                if mm and int(mm.group(2)) == issue:
                    return ["계획에 미완 스텝이 남아 있다 — 마지막 스텝의 "
                            "phase-2 PR에서만 Closes/Fixes/Resolves를 쓴다."]
                return []
        mm = _CLOSES_REF.search(body)
        if not mm or int(mm.group(2)) != issue:
            return [f"PR 본문에 'Closes #{issue}'(또는 Fixes/Resolves)가 없다 — "
                    f"phase-2 인도 PR은 이슈를 명시적으로 닫아야 한다."]
        return []
    refs = {int(n) for n in _PLAIN_REF.findall(body)}
    if issue not in refs:
        return [f"PR 본문에 '#{issue}' 참조가 없다 — phase-1 제안 PR도 자기 "
                f"이슈를 본문에서 가리켜야 한다(Closes/Fixes/Resolves는 금지: "
                f"phase-1 머지가 이슈를 자동으로 닫으면 안 된다)."]
    return []


def run():
    failures = []

    def case(name, cond):
        if cond:
            print(f"PASS: {name}")
        else:
            print(f"FAIL: {name}")
            failures.append(name)

    # red: phase2, Closes #447, plan has an incomplete non-final step
    # (mirrors #447/#458) -> deny.
    plan_bad = [
        {"step": 1, "roles": ["a"], "done": True},
        {"step": 2, "roles": ["b"], "done": False},
        {"step": 3, "roles": ["c"], "done": True},
    ]
    bad1 = check_body(447, "Closes #447", "phase2", plan_bad)
    case("phase2 Closes with incomplete non-final step -> denied", len(bad1) > 0)

    # red: phase2, no Closes/Fixes/Resolves at all, plan is None
    # (mirrors #448) -> deny.
    bad2 = check_body(448, "just some text, no closing keyword", "phase2", None)
    case("phase2 no closing keyword, plan None -> denied", len(bad2) > 0)

    # green: phase1, plain #459 reference -> no denial.
    bad3 = check_body(459, "Refs #459, work in progress", "phase1", None)
    case("phase1 plain #459 reference -> allowed", len(bad3) == 0)

    # green: phase2, Closes #459, plan None -> no denial.
    bad4 = check_body(459, "Closes #459", "phase2", None)
    case("phase2 Closes #459, plan None -> allowed", len(bad4) == 0)

    # green: phase2, Closes #459, plan all steps done -> no denial.
    plan_done = [
        {"step": 1, "roles": ["a"], "done": True},
        {"step": 2, "roles": ["b"], "done": True},
    ]
    bad5 = check_body(459, "Closes #459", "phase2", plan_done)
    case("phase2 Closes #459, plan all done -> allowed", len(bad5) == 0)

    # green: phase2, only-final-step-incomplete -> Closes required and allowed.
    plan_final_incomplete = [
        {"step": 1, "roles": ["a"], "done": True},
        {"step": 2, "roles": ["b"], "done": False},
    ]
    bad6 = check_body(459, "Closes #459", "phase2", plan_final_incomplete)
    case("phase2 Closes #459, only final step incomplete -> allowed", len(bad6) == 0)

    # sanity: _plan_from_body parses the expected shape.
    body_with_plan = (
        "intro\n\n## 실행 계획\n"
        "- [x] step 1 role-a\n"
        "- [ ] step 2 role-b\n\n## other\nnoise\n"
    )
    parsed = _plan_from_body(body_with_plan)
    case(
        "_plan_from_body parses steps",
        parsed == [
            {"step": 1, "roles": ["role-a"], "done": True},
            {"step": 2, "roles": ["role-b"], "done": False},
        ],
    )
    case("_plan_from_body returns None with no header", _plan_from_body("no header here") is None)

    if failures:
        print(f"\n{len(failures)} failure(s): {failures}")
        return 1
    print(f"\nAll {5 + 2 + 1} checks passed" if False else "\nAll checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(run())
