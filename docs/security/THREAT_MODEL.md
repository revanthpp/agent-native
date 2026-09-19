# Threat Model

Agent Native treats every target as hostile and every fetched artifact as tainted data.

| Asset | Attacker | Trust boundary | Attack path | Impact | Mitigation | Residual risk | Verification |
|---|---|---|---|---|---|---|---|
| Scanner network | External attacker | URL input to socket | SSRF, redirect, DNS rebinding | Internal access or metadata exposure | HTTPS-only default, DNS/IP validation, manual redirects, bounded requests | The host OS/network must still enforce egress controls in hosted deployments | `test_private_targets_blocked`, redirect policy tests |
| Parser process | Target owner | Bytes to parser | Giant/malformed HTML or OpenAPI | Crash or resource exhaustion | response byte cap, no code evaluation, isolated evaluator errors | CPU/depth limits need expansion for hosted sandbox | malformed parser tests |
| Evaluator integrity | Target owner | Target text to checks | Prompt injection or deceptive descriptions | False PASS / unsafe classification | deterministic structural checks, no LLM in v0.1, contradiction warnings | Static metadata cannot prove runtime behavior | prompt-injection fixture |
| Evidence/report | Target content | Artifact to output | Secrets or ANSI/control text in content | Leakage or terminal deception | redaction, bounded evidence fragments, plain terminal output | Secret patterns are heuristic | secret-bearing fixture |
| Availability | Hostile target | Target response to worker | Slow or oversized response | Scan hangs or monopolizes worker | timeout, request/redirect/size budgets | Hosted deployment still needs process/container quotas | bounded fetch tests |
| Future active simulator | Misconfigured user/target | Verified environment boundary | Mutation or credential reuse | Real side effect or credential leak | out of scope for anonymous v0.1; staging and ownership required later | active testing is not implemented yet | deferred release gate |

## Required invariants

- zero successful private-network fetches in the adversarial suite;
- no target JavaScript execution;
- no target-provided credentials sent by the scanner;
- no secret-like values persisted in evidence output;
- one failed artifact cannot prevent a partial report.

## Prompt-injection stance

Text such as `ignore previous instructions` is never interpreted as policy. In v0.1 it is only a string inspected by deterministic checks. Future semantic evaluators must receive sanitized excerpts with no network or tool access and must remain non-authoritative.
