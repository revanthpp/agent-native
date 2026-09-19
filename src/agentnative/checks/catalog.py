from __future__ import annotations

from agentnative.models import CheckDefinition, Severity


def _check(
    check_id: str,
    name: str,
    domain: str,
    severity: Severity,
    description: str,
    remediation: str,
    *,
    rationale: str = "A machine client needs explicit, inspectable evidence.",
) -> CheckDefinition:
    return CheckDefinition(
        id=check_id,
        name=name,
        domain=domain,
        version="1.0.0",
        severity=severity,
        description=description,
        rationale=rationale,
        evidence_required="A source artifact or an explicit NOT_OBSERVED explanation.",
        evaluation_method="deterministic passive inspection",
        remediation=remediation,
        references=("BRD:AR-" + check_id[-3:],),
        passive_or_active="passive",
        confidence_method="structural evidence and source provenance",
    )


CHECKS = [
    _check("AR-001", "HTTPS and public routing", "Identity & authentication", Severity.HIGH, "The target uses HTTPS and resolves to public routing.", "Serve the public machine interface over HTTPS with valid public DNS."),
    _check("AR-002", "Safe redirect chain", "Security & abuse resistance", Severity.CRITICAL, "Redirects stay inside the safe outbound network policy.", "Keep redirects on approved public HTTPS hosts and avoid private or reserved destinations."),
    _check("AR-003", "Machine interface discoverability", "Discoverability", Severity.MEDIUM, "A public machine-readable interface or structured capability artifact is discoverable.", "Publish an OpenAPI document, agent metadata, or structured capability description from the public surface."),
    _check("AR-004", "Explicit interface version", "Interoperability", Severity.LOW, "A discovered machine interface declares a version.", "Declare the OpenAPI/protocol version and a service version."),
    _check("AR-005", "Stable operation identifiers", "Capability semantics", Severity.MEDIUM, "Discovered operations have unique non-empty identifiers.", "Give every operation a stable operationId or tool identifier."),
    _check("AR-006", "Typed inputs and requiredness", "Capability semantics", Severity.MEDIUM, "Inputs expose types and required or optional status.", "Describe input schemas with types and explicit requiredness."),
    _check("AR-007", "Structured outputs", "Capability semantics", Severity.MEDIUM, "Operations expose structured response schemas or media types.", "Document response content types and schemas for every operation."),
    _check("AR-008", "Authentication declaration", "Identity & authentication", Severity.HIGH, "Authentication methods are machine-identifiable.", "Declare the authentication scheme without embedding credentials."),
    _check("AR-009", "Authorization scopes", "Authorization & delegated consent", Severity.HIGH, "Authorization scopes or permissions are declared where applicable.", "Use explicit, narrow scopes for protected operations."),
    _check("AR-010", "Avoid wildcard authorization", "Authorization & delegated consent", Severity.CRITICAL, "Sensitive operations do not advertise obviously global or wildcard scopes.", "Replace wildcard or administrator scopes with action- and resource-specific permissions."),
    _check("AR-011", "Side-effect classification", "Transaction safety", Severity.HIGH, "Read and mutating operations can be distinguished structurally.", "Declare side-effect semantics and keep them consistent with HTTP methods and paths."),
    _check("AR-012", "Quote or preview before commit", "Transaction safety", Severity.HIGH, "Cost-bearing or high-impact actions expose pre-commit information.", "Add a quote or preview step with price, terms, and expiry before commit."),
    _check("AR-013", "Confirmation boundary", "Transaction safety", Severity.HIGH, "Irreversible or high-impact actions expose a confirmation requirement.", "Require explicit human confirmation before irreversible commit operations."),
    _check("AR-014", "Idempotency or dedupe", "Reliability & recovery", Severity.HIGH, "Mutation operations expose idempotency or duplicate-suppression semantics.", "Support Idempotency-Key or document equivalent deduplication behavior."),
    _check("AR-015", "Cancellation or compensation", "Reliability & recovery", Severity.MEDIUM, "Reversible actions expose cancellation, rollback, or compensation semantics.", "Document and expose a cancellation or compensating action."),
    _check("AR-016", "Rate-limit and retry guidance", "Reliability & recovery", Severity.MEDIUM, "The interface documents rate-limit or retry behavior.", "Document Retry-After, backoff, rate limits, and retryable conditions."),
    _check("AR-017", "Structured error semantics", "Reliability & recovery", Severity.MEDIUM, "Errors distinguish validation, authorization, conflict, retryable, and terminal classes.", "Publish structured error responses with machine-readable categories."),
    _check("AR-018", "Correlation identifiers", "Observability & provenance", Severity.LOW, "Requests and responses support correlation or trace identifiers.", "Propagate a request or trace ID in headers and receipts."),
    _check("AR-019", "Human escalation path", "Governance & human control", Severity.LOW, "The public surface exposes support or human escalation for failures.", "Publish a support or escalation path for ambiguous and failed workflows."),
    _check("AR-020", "No exposed secrets", "Security & abuse resistance", Severity.CRITICAL, "Public artifacts contain no obvious credentials or secret examples.", "Remove secrets from public specifications, examples, logs, and descriptions."),
]

CHECK_BY_ID = {check.id: check for check in CHECKS}
