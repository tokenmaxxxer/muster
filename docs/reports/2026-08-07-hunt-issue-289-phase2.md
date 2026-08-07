---
proposal: docs/issue-289/proposals/implementation.md
---

# Hunt record — issue-289-phase2

## before-landing — stance 1: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — the exclude-write dedupe in issue_workspace() uses a bare substring check (`ln.rstrip("/") not in existing`) against the raw text of `.git/info/exclude`, so any pre-existing unrelated text that happens to contain a dotfile name as a substring (e.g. a human comment mentioning `.bashrc`, or any other file/pattern already containing one of the target names) causes that dotfile line to be silently skipped and never appended — the guard believes the exclusion already exists when it does not, and the sandbox-leaked dotfile (e.g. `.bashrc`, `.gitconfig`) remains eligible to be picked up by `git add -A` with no error or log output.
Kind: silent-failure
Seed: spawn.py issue_workspace() dedupe-by-substring diff (`missing = [ln for ln in lines if ln.rstrip("/") not in existing]`), spawn.py lines ~2751-2769
cap_seconds: 120
tier: default
diff_stat_lines: ~35 (spawn.py dotfile-exclude + regex hunks; protocol.md/.ko.md note; test_spawn.py 2 tests)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:02:00Z

### Reproduce
```python
existing = "# NOTE: don't accidentally commit .bashrc modifications\n.muster-cache/\n"
lines = [".muster-cache/", ".bashrc", ".bash_profile", ".profile", ".zshrc",
          ".zprofile", ".gitconfig", ".gitmodules", ".mcp.json",
          ".claude/", ".idea", ".vscode", ".ripgreprc"]
missing = [ln for ln in lines if ln.rstrip("/") not in existing]
print(missing)
print(".bashrc" in missing)
```

### Observed
```
missing: ['.bash_profile', '.profile', '.zshrc', '.zprofile', '.gitconfig', '.gitmodules', '.mcp.json', '.claude/', '.idea', '.vscode', '.ripgreprc']
False
```
`.bashrc` is dropped from `missing` and therefore never written to `.git/info/exclude`, even though no actual `.bashrc` exclude pattern exists in the file — only an unrelated comment sentence that happens to contain the substring `.bashrc`.

### Expected
The dedupe should only suppress a line when that exact pattern is already present as an exclude entry (e.g. matched line-by-line, not via whole-file substring search), so incidental substring collisions in comments or other patterns don't cause a real dotfile-leak protection to be silently skipped.
