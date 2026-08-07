---
kind: decision
date: 2026-08-07
status: landed
subject: issue-327
---

# `roster_watchdog()` return value now carries meaning

`roster_watchdog()` (`spawn.py:1542`) previously always returned `0`,
regardless of what it found. It now returns the count of roster entries
that produced at least one `watchdog_check_one` anomaly — `0` on a clean
scan (unchanged from before), non-zero otherwise.

Because `spawn.py watchdog`'s CLI dispatch passes this value straight
through as the process exit code (`spawn.py:2445`), a non-zero exit now
means "an idle-waiting, deadlock-shaped, or unnecessary-work session was
found" — checkable by a caller that only reads the exit code, without
parsing stdout. This discharges #327's acceptance bar per #310: an
executable artifact (`test_spawn.py`'s
`test_roster_watchdog_returns_anomaly_count_for_stalled_entry`, and
`spawn.py watchdog`'s own exit code against a stale-log fixture) fails on
regression.

**Reaches beyond its own acceptance criteria (per #330):** any existing or
future caller of `roster_watchdog()` in Python — not only the `watchdog`
CLI subcommand — now receives a non-zero return whenever an anomaly was
found, not just `0`. A caller written against the old "always 0" behavior
(e.g. code that used the return value only as a success/failure flag for
the scan itself completing, rather than for what it found) would see its
meaning change. A repo-wide grep at write time found exactly one call site
(`spawn.py:2445`, the CLI dispatch already covered above); no other
caller exists.

No new detection logic was added — the four anomaly signals
(`watchdog_check_one`'s `log-silence`, `denied-tool-calls`,
`background-delegation-phrasing`, `no-commits-late`) are unchanged, still
computed exactly as before. `auto_respawn=True`'s crashed-only
respawn/cap-comment side effects are unchanged. `watchdog_check_one`
itself is untouched and stays observe-only.
