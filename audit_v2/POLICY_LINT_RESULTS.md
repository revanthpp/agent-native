# Policy Lint Results

Independent linter probes triggered the expected classes:

- missing default;
- unowned rule;
- expired rule;
- future-rule ambiguity;
- wildcard privilege;
- contradictory rules;
- duplicate ambiguity;
- sensitive/high-risk action without confirmation;
- environment inconsistency.

Safe case produced no lint findings.

CLI semantic check passed: `agentnative policy lint` returned nonzero and emitted JSON findings including missing default, unowned rule, wildcard privilege, and high-risk-without-confirmation for an unsafe fixture.

Policy precedence/fail-closed checks passed:

- specific `DENY` beats broad `ALLOW`;
- missing policy for state-changing action returns `DENY`;
- decision payload remains explainable.
