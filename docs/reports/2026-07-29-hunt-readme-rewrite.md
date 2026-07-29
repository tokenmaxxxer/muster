---
proposal: docs/issue-85/proposals/readme-rewrite.md
---

# Hunt record — readme-rewrite

## after-proposal — stance 1: broken relative links/anchors, factual contradictions, Korean/English structural parity gaps, skeleton deviations from proposal

Verdict: NO FINDING
Seed: commit e7a6a33 (README.md +44/-4, README.ko.md +229/-25) rewriting both READMEs per docs/issue-85/proposals/readme-rewrite.md.

Checked:
- Cross-links `README.md:3` -> `README.ko.md` and `README.ko.md:3` -> `README.md` both resolve (files exist at repo root).
- No `](#...)` anchor-fragment links exist in either file, so no broken-anchor risk from the reorg.
- `## `-level and `### `-level section lists in README.md vs README.ko.md line up 1:1 in the same order (Five walls / brand line / Getting started / Why / Roles / Using it / Installing / board opt-in / loop / conversation / every command / session end / where it stops / isolation / three traps / package-registry / web access / default-open / gates / self-check / open) — no parity gap.
- Newly-added Korean subsections (패키지 레지스트리 접근, 웹 접근, 기본 개방 태세, 시작하기) were diffed word-for-word against their English counterparts and against spawn.py's actual `PACKAGE_REGISTRY_HOSTS`, `WEB_ACCESS_DOMAINS`, and the six `role_settings()` open-by-default keys (`allowAllUnixSockets`, `allowLocalBinding`, `allowMachLookup`, `enableWeakerNetworkIsolation`, `allowAppleEvents`, `enableWeakerNestedSandbox`) — all six named identically in both languages and all match spawn.py's source names.
- Numeric claims (issue #38/#58/#65/#69/#72, "3/6 survey targets", "188 lines", "345-line"/"533-line" contract split) match between the two files.
- The one pre-existing oddity (`README.md:112` reads `python3 on-the-record/spawn.py init` while `README.md:254` and the rest of the doc use `python3 spawn.py init`) predates this commit — confirmed via `git show e7a6a33 -- README.md`, that hunk is untouched by the rewrite — so it is out of scope for this diff.

No reproduction found for any broken link, contradicted fact, or parity gap introduced by this commit.
