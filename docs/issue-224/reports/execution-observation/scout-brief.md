# Scout brief — issue #224, `execution-observation`

**Mode:** parallel WebSearch, 2 stages (stage 1 sweep = 4 concurrent
angles aimed at survey gaps G1–G4; stage 2 = 1 deepening round, 2
concurrent snowball calls on G1/G2). Saturation reached at judge point 2
— a third round would not change which checks this observation runs.
Segment: not product-shaped; the deliverable's kind is *an audit of a
liveness/pagination reliability change*, so the field scouted is what
strong reviews of that change-class check.

**Category must-bes (what strong audits of this change class assume):**

1. **A liveness registry's entry lifetime must be checked against the
   completion record's write time, not assumed to match.** The
   canonical defect is removing the pid/registry entry *before* the
   process finishes its shutdown work; the stated rule is to delete the
   pidfile *after* the application has stopped, not before, precisely
   because a monitor reading the gap calls a live process dead
   (spring-boot#4369, freedesktop#45713). The patent-literature framing
   of the same idea: a registry entry "can be removed … when a process
   ends normally," which is exactly why entry-absence is not a crash
   signal by itself.
2. **A regression test must construct a state production can actually
   reach.** Mocks that do not behave realistically give false
   confidence; a green test whose setup diverges from the real
   dependency's state is the named failure mode, not an edge case
   (Microsoft engineering playbook; WWT).
3. **`gh api --paginate` alone does not produce valid JSON** — each
   page is a separate array and `--slurp` is the documented wrapper
   (cli/cli#10459, gh-api manual). An audit therefore checks the
   flatten step, not just the flag.
4. **A distinct exit code per distinct operator response.** Shell
   convention reserves 1–127 for handled application errors and
   128+N for signal deaths (Baeldung), so a small free integer for
   "target died" is the conventional choice, not a novel one.

**Performance axes this class competes on:** (a) *detection latency* —
how fast a genuinely dead target is reported; (b) *false-positive rate*
— how often a live-but-quiet target is called dead. The two trade off
directly, which is why the liveness signal and the idle timeout must
stay separate signals rather than one racing the other.

**Adopt:** must-be 1 as the primary check of this observation — read the
registry entry's removal site against the completion record's write
site, in the produced artifact, and see which one the predicate reads
first. **Adopt:** must-be 2 as the secondary check — read the new
regression test's `setUp`/arrange block against that same ordering.
**Skip:** re-deriving `--paginate --slurp` semantics experimentally
(prohibited re-execution, and the observed role's own record already
cites a real-`gh` check); the audit instead checks that the flatten step
and the zero-comment shape are both covered.

**GAP LINE:** of the four must-bes, the observed artifact already meets
3 (`--paginate --slurp` + flatten at `c71faba05:spawn.py:830-857`) and 4
(`WATCH_CRASH_RC = 2` plus a decision doc at
`docs/issue-224/decisions/watch-crash-exit-code.md`). Must-bes 1 and 2
are the ones the survey could not confirm from the artifact alone
(survey unknowns 1–2, observations O6–O8) — so this observation's
checks aim there, not at the pagination or exit-code surfaces.

**Sources:**
- https://github.com/cli/cli/issues/10459 (`--paginate --slurp` semantics)
- https://cli.github.com/manual/gh_api (`--slurp` wraps pages in an outer array)
- https://github.com/cli/cli/issues/13270 (`--paginate` reliability caveats)
- https://github.com/spring-projects/spring-boot/issues/4369 (delete pidfile after stop, not before)
- https://bugs.freedesktop.org/show_bug.cgi?id=45713 (stale/absent pidfile handling)
- https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8239709 (registry entry removed on normal exit)
- https://microsoft.github.io/code-with-engineering-playbook/automated-testing/unit-testing/mocking/ (unrealistic mocks → false confidence)
- https://www.wwt.com/article/test-doubles-can-you-tell-fake-from-mock (test doubles diverging from real behavior)
- https://www.baeldung.com/linux/status-codes (1–127 vs 128+N exit-code convention)
