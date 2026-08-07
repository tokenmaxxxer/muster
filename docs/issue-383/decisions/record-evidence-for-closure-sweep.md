# Decision: closure_sweep reuses #284's record evidence, not a new keyword requirement

`gates/closure_sweep.py::classify()` now treats a phase-2 record file's
existence (non-empty `loop_state`, via `ci._phase2_record_evidence`) as
alternate evidence of a merged delivery, the same evidence #284's
closes-gate already accepts. The alternative — making the system emit
`Closes #n` itself — was rejected because it re-imposes on the write
side exactly the rigidity #284 removed (a phase-2 PR body no longer has
to be rewritten after approval flips the phase). Reading the same
evidence #284 already trusts keeps both the closes-gate and the
closure-consistency sweep agreeing on one definition of "delivered."
