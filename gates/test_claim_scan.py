#!/usr/bin/env python3
"""issue #476 H1 — `gates/claim_scan.py` 단위 테스트. 네트워크 없이 돈다.

  python3 gates/test_claim_scan.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claim_scan


def t_bare_claim_with_no_evidence_is_a_finding():
    findings = claim_scan.scan_text("the fix was verified and works now.")
    assert len(findings) == 1, findings
    assert "없다" in findings[0].reason, findings[0].reason


def t_claim_with_repro_marker_nearby_is_not_a_bare_finding():
    text = "the tests passed.\nRepro: python3 gates/test_skip_gate.py\n"
    findings = claim_scan.scan_text(text)
    assert findings == [], findings


def t_claim_with_fenced_block_nearby_is_not_a_bare_finding():
    text = "confirmed via:\n```\npython3 -m pytest gates/test_gates.py\n```\n"
    findings = claim_scan.scan_text(text)
    assert findings == [], findings


def t_evidence_outside_adjacency_window_still_a_finding():
    filler = "\n".join(f"line {i}" for i in range(claim_scan.ADJACENCY_LINES + 5))
    text = f"reproduced.\n{filler}\nRepro: python3 gates/test_skip_gate.py\n"
    findings = claim_scan.scan_text(text)
    assert len(findings) == 1, findings


def t_target_not_in_repo_is_a_finding_when_repo_targets_given():
    text = "verified.\nRepro: python3 gates/test_nonexistent_module.py\n"
    findings = claim_scan.scan_text(text, repo_targets={"gates/test_skip_gate.py"})
    assert len(findings) >= 1, findings
    assert all("없다" in f.reason for f in findings), findings


def t_target_in_repo_clears_when_repo_targets_given():
    text = "verified.\nRepro: python3 gates/test_skip_gate.py\n"
    findings = claim_scan.scan_text(text, repo_targets={"gates/test_skip_gate.py"})
    assert findings == [], findings


def t_case0_real_but_out_of_diff_target_is_a_finding_when_base_scoped():
    # pilot case0 shape: cited file is real (tracked) but not part of the
    # diff under test — whole-repo git ls-files would clear it silently.
    text = "verified.\nRepro: python3 gates/claim_scan.py --help\n"
    findings = claim_scan.scan_text(
        text, repo_targets={"gates/reexecution_gate.py"})
    assert len(findings) >= 1, findings
    assert all("없다" in f.reason for f in findings), findings


def t_honest2_dotted_function_citation_clears_when_module_in_repo():
    # pilot honest2 shape: repro cites `module.function()`, not a file
    # path — must resolve back to its containing file before matching.
    text = 'verified.\nRepro: python3 -c "import claim_scan; ' \
           'assert claim_scan.scan_text(\'\') == []"\n'
    findings = claim_scan.scan_text(
        text, repo_targets={"gates/claim_scan.py"})
    assert findings == [], findings


def t_base_resolution_failure_hard_fails_instead_of_falling_back():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=td, check=True)
        try:
            claim_scan._repo_targets(Path(td), base="nonexistent-ref-xyz")
        except claim_scan.BaseResolutionError:
            pass
        else:
            raise AssertionError("expected BaseResolutionError")


def t_no_claim_language_is_clean():
    findings = claim_scan.scan_text("this changes the widget rendering.")
    assert findings == [], findings


def t_main_exits_nonzero_on_bare_claim(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "record.md"
        f.write_text("this was reproduced.\n")
        rc = claim_scan.main([str(f), "--repo", td])
        assert rc != 0, rc


def t_main_exits_zero_on_clean_text():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "record.md"
        f.write_text("no claim language here.\n")
        rc = claim_scan.main([str(f), "--repo", td])
        assert rc == 0, rc


def t_dotted_citation_does_not_match_unrelated_same_basename_file():
    # before-landing hunt finding: a claim citing an untouched module
    # (pkgB.utils.f) must not clear just because an unrelated file with
    # the same basename (pkgA/utils.py) happens to be in repo_targets.
    text = "verified.\nRepro: pkgB.utils.f()\n"
    findings = claim_scan.scan_text(text, repo_targets={"pkgA/utils.py"})
    assert len(findings) >= 1, findings
    assert all("없다" in f.reason for f in findings), findings


def t_main_hard_fails_on_broken_base_instead_of_scanning_whole_repo():
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "init", "-q"], cwd=td, check=True)
        f = Path(td) / "record.md"
        f.write_text("this was reproduced.\n")
        rc = claim_scan.main([str(f), "--repo", td, "--base", "no-such-ref"])
        assert rc == 2, rc


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
