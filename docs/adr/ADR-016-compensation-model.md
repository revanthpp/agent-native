# ADR-016: Compensation Model

Status: Accepted

Partial outcomes are first-class. A scenario may require a compensation
adapter call; successful restoration becomes `COMPENSATED`, while a failed
compensation remains `PARTIAL` with an explicit finding.
