# ADR-019: Controlled Failure Injection

Status: Accepted

Failure injection is explicit, typed, bounded, and restricted to the synthetic
adapter/test path. It covers preview, policy, commit, response, verification,
and compensation points without introducing arbitrary network execution.
