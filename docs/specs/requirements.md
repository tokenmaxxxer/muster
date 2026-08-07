# Requirements Registry

Append-only. Each entry records one requirement in the operator's own words,
the issue it came from, and the executable artifact that fails if the
requirement's enforcement regresses. Do not edit or remove existing entries
— only append new ones, or update `status` on an existing entry.

Fields:
- `quote`: the operator's verbatim words (Korean or English, unedited).
- `source_issue`: the GitHub issue number the quote came from.
- `check`: `path/to/file.py::name` of the executable artifact that fails on
  regression, or the literal `UNVERIFIABLE: <reason>` when genuinely not
  mechanically checkable (per #310's precedent for stating that plainly).
- `status`: `open` | `enforced` | `stale`. `stale` is computed by
  `gates.requirement_registry`; `open`/`enforced` are set by whichever
  role discharges or re-checks the requirement.

`gates.requirement_registry` (wired into `gates/ci.py`) fails the check for
any entry whose `check` path no longer exists at HEAD — a requirement
quietly losing its enforcement as the codebase moves.

## R001

quote: 기록이 많아짐으로써 사용자가 핵심으로 제시하는 요구사항들이 희석되는 문제 (requirements dilute as the record grows)
source_issue: 321
check: gates/gates.py::requirement_registry
status: enforced
