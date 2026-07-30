# scout-brief: issue-132 (session-end trichotomy + capped auto-respawn)

Mode: 1 stage, batched (single WebSearch call — angle: process-supervisor
crash-vs-hang restart design, the field this deliverable's category belongs
to). No fan-out needed at this size; budget not stressed.

## Must-bes (from supervisor exemplars: systemd Restart=/StartLimitBurst,
## WatchdogSec, k8s CrashLoopBackOff)
- Exit-based restart (`Restart=on-failure`) and liveness-based restart
  (`WatchdogSec`/heartbeat) are treated as **separate mechanisms** — a dead
  PID and an alive-but-frozen PID are different failure classes with
  different evidence and different fixes.
- Restart attempts are **rate/count-limited** (`StartLimitBurst` +
  `StartLimitIntervalSec`), and exceeding the limit is a **hard stop with a
  visible signal** (systemd: unit enters `failed`, journald record), never a
  silent infinite loop and never a silent give-up.
- Hang detection tools (WatchdogSec) explicitly do **not** auto-restart on
  their own signal in the safest configs — many stacks treat "still running,
  but silent" as a paging/alert condition for a human rather than an
  automatic kill, because "is it truly stuck or just slow" is not always
  decidable from outside.

## Performance axes strong designs compete on
1. Speed/cost of detection (poll interval vs missed-crash window).
2. False-restart avoidance (never restart something that's actually still
   working — a live PID with a merely-quiet log is not proof of death).
3. Escalation clarity when the automatic path gives up (where does the
   human find out, and how fast).

## Adopt
- Two-track judgment, PID-liveness-first: no session-end event AND process
  dead = crashed; no session-end event AND process alive = stalled. This
  matches issue #132's (b)/(c) split exactly and matches WatchdogSec's
  separation of concerns.
- Bounded auto-restart with a hard cap and a mandatory terminal signal on
  cap (systemd's `StartLimitBurst` + failed-unit visibility) → issue's
  "≤2 auto-respawns, then a mandatory issue comment."

## Skip
- Heartbeat/liveness pings (WatchdogSec-style active check-ins from inside
  the Claude session) — out of scope for #132 and not requested; the repo's
  existing `roster_watchdog` log-mtime staleness check already plays that
  role passively, and #132 only asks to *classify and act on* crashed, not
  to add new liveness telemetry.
- Auto-restart on `stalled` — deliberately not adopted. The issue's spec
  explicitly scopes auto-respawn to `crashed` only ("crashed 에 한해");
  this matches the exemplar caution that "alive but quiet" is not
  reliably distinguishable from "still legitimately working" without a
  human, and `roster_watchdog` already surfaces staleness for a human to
  act on.

## Gap line
The repo already has the *live-session* half of this pattern
(`roster_watchdog`, observe-only staleness detection) but has **no
dead-session half** (no dead-PID scan, no session-end-vs-liveness cross
check, no restart counter, no cap-exceeded signal) — issue #132 is exactly
that missing half, not a re-do of the existing watchdog.

## Segment fit
This is internal infra reliability tooling, not a user product — the bar is
"matches how mature process supervisors reason about crash vs hang," not
UX polish.

Stages used: 1 (sweep only; judge point 1 found no reason to deepen —
the pattern converged immediately across systemd/WatchdogSec/k8s framing
and is directly actionable against the issue's stated 3-way split).

Sources:
- [systemd restart on failure :: IT'S FOSS](https://itsfoss.gitlab.io/blog/systemd-restart-on-failure/)
- [How to Configure systemd RestartSec and WatchdogSec on Ubuntu](https://oneuptime.com/blog/post/2026-03-02-configure-systemd-restartsec-watchdogsec-ubuntu/view)
- [How to Set Up systemd Watchdog Monitoring for Critical Services on RHEL](https://oneuptime.com/blog/post/2026-03-04-set-up-systemd-watchdog-monitoring-for-critical-services/view)
