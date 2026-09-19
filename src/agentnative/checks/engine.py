from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from agentnative.checks.catalog import CHECKS
from agentnative.models import Artifact, CheckResult, DiscoveredSurface, Evidence, ResultStatus, SideEffect, Target, utc_now
from agentnative.security.sanitize import Sanitizer
from agentnative.security.secrets import SecretDetector


EvidenceSource = tuple[Artifact, str, dict[str, Any]]
Evaluator = Callable[[DiscoveredSurface, Target, str], tuple[ResultStatus, str, float, list[EvidenceSource]]]
_SANITIZER = Sanitizer()
_DETECTOR: SecretDetector = _SANITIZER.detector


def run_checks(surface: DiscoveredSurface, target: Target, scan_id: str) -> list[CheckResult]:
    evaluators: dict[str, Evaluator] = {
        "AR-001": _https,
        "AR-002": _redirects,
        "AR-003": _discoverable,
        "AR-004": _version,
        "AR-005": _operation_ids,
        "AR-006": _inputs,
        "AR-007": _outputs,
        "AR-008": _auth,
        "AR-009": _scopes,
        "AR-010": _wildcards,
        "AR-011": _side_effects,
        "AR-012": _quote,
        "AR-013": _confirmation,
        "AR-014": _idempotency,
        "AR-015": _cancellation,
        "AR-016": _retry,
        "AR-017": _errors,
        "AR-018": _correlation,
        "AR-019": _escalation,
        "AR-020": _secrets,
    }
    results: list[CheckResult] = []
    for check in CHECKS:
        try:
            status, explanation, confidence, sources = evaluators[check.id](surface, target, scan_id)
            evidence = [_evidence(check.id, source) for source in sources]
            results.append(CheckResult(check, status, explanation, check.remediation, confidence, evidence))
        except Exception as exc:
            results.append(CheckResult(check, ResultStatus.ERROR, f"Check failed safely: {type(exc).__name__}: {exc}", check.remediation, 0.0, []))
    return results


def _evidence(check_id: str, source: EvidenceSource) -> Evidence:
    artifact, fragment, normalized = source
    clean_fragment, changed = _SANITIZER.text(fragment)
    safe_normalized = {
        "artifact_id": artifact.artifact_id,
        "confidence": normalized.get("confidence", 0.9),
        **{key: value for key, value in normalized.items() if key not in {"content_hash", "artifact_id"}},
    }
    return Evidence(
        evidence_id=f"ev-{uuid.uuid5(uuid.NAMESPACE_URL, f'{check_id}:{artifact.artifact_id}:{fragment}')}",
        source_uri=artifact.uri,
        artifact_type=artifact.artifact_type,
        acquisition_timestamp=utc_now(),
        content_hash=artifact.content_hash,
        artifact_id=artifact.artifact_id,
        check_id=check_id,
        relevant_fragment=clean_fragment[:800],
        normalized_representation=safe_normalized,
        observation=clean_fragment[:800],
        confidence=float(safe_normalized["confidence"]),
        redaction_status="redacted" if changed else "not_required",
    )


def _src(artifacts: list[Artifact], fragment: str, normalized: dict[str, Any] | None = None) -> list[EvidenceSource]:
    return [(artifact, fragment, {"confidence": 0.9, **(normalized or {})}) for artifact in artifacts if artifact.content_hash]


def _root(surface: DiscoveredSurface) -> list[Artifact]:
    return [artifact for artifact in surface.artifacts[:1] if artifact.content_hash]


def _html(surface: DiscoveredSurface) -> list[Artifact]:
    return [artifact for artifact in surface.artifacts if artifact.content_hash and artifact.uri.lower().endswith((".html", ".htm", "/"))]


def _openapi(surface: DiscoveredSurface) -> list[Artifact]:
    uris = {document.uri for document in surface.openapi}
    return [artifact for artifact in surface.artifacts if artifact.content_hash and artifact.uri in uris]


def _interface(surface: DiscoveredSurface) -> list[Artifact]:
    artifacts = _openapi(surface) + _html(surface)
    artifacts += [artifact for artifact in surface.artifacts if artifact.content_hash and any(marker in artifact.uri.lower() for marker in ("agent-card", "agent.json"))]
    return list({artifact.artifact_id: artifact for artifact in artifacts}.values())


def _all(surface: DiscoveredSurface) -> list[Artifact]:
    return [artifact for artifact in surface.artifacts if artifact.content_hash]


def _operation_artifacts(surface: DiscoveredSurface, operations: list[Any] | None = None) -> list[Artifact]:
    operations = operations if operations is not None else _ops(surface)
    uris = {operation.source_uri for operation in operations}
    artifacts = [artifact for artifact in surface.artifacts if artifact.content_hash and artifact.uri in uris]
    return artifacts or _openapi(surface) or _root(surface)


def _ops(surface: DiscoveredSurface) -> list[Any]:
    return surface.operations


def _has_interface(surface: DiscoveredSurface) -> bool:
    return bool(surface.openapi or surface.structured_metadata or surface.agent_metadata)


def _https(surface: DiscoveredSurface, target: Target, scan_id: str):
    if target.kind == "local":
        return ResultStatus.NOT_APPLICABLE, "Local fixture input has no public transport to assess.", 1.0, []
    if target.canonical.startswith("https://"):
        return ResultStatus.PASS, "Target uses HTTPS and passed outbound URL policy validation.", 1.0, _src(_root(surface), target.canonical)
    return ResultStatus.FAIL, "Target is not HTTPS.", 1.0, _src(_root(surface), target.canonical)


def _redirects(surface: DiscoveredSurface, target: Target, scan_id: str):
    if target.kind == "local":
        return ResultStatus.NOT_APPLICABLE, "Redirect policy is only evaluated for network acquisition.", 1.0, []
    unsafe = [item for item in surface.limitations if "private" in str(item).lower() or "redirect" in str(item).lower()]
    if unsafe:
        return ResultStatus.FAIL, str(unsafe[0]), 1.0, _src(_root(surface), str(unsafe[0]))
    return ResultStatus.PASS, "No unsafe redirect was observed within the bounded acquisition policy.", 0.95, _src(_root(surface), "bounded redirect policy accepted target")


def _discoverable(surface: DiscoveredSurface, target: Target, scan_id: str):
    if _has_interface(surface):
        return ResultStatus.PASS, "A machine-readable artifact or structured capability metadata was discovered.", 0.95, _src(_interface(surface), f"openapi={len(surface.openapi)} structured={len(surface.structured_metadata)} agent={len(surface.agent_metadata)}")
    return ResultStatus.NOT_OBSERVED, "No supported machine-readable interface was observed in the bounded artifact set.", 0.95, _src(_all(surface), "supported machine-readable interface not observed")


def _version(surface: DiscoveredSurface, target: Target, scan_id: str):
    versions = [document.version for document in surface.openapi if document.version]
    versions += [str(item.get("version")) for item in surface.agent_metadata if item.get("version")]
    if versions:
        return ResultStatus.PASS, f"Interface version observed: {', '.join(versions)}.", 0.95, _src(_interface(surface), ", ".join(versions))
    if _has_interface(surface):
        return ResultStatus.NOT_OBSERVED, "A supported interface was found but no explicit service/interface version was observed.", 0.9, _src(_interface(surface), "version not observed")
    return ResultStatus.NOT_APPLICABLE, "No machine interface was discovered.", 1.0, []


def _operation_ids(surface: DiscoveredSurface, target: Target, scan_id: str):
    ops = _ops(surface)
    if not ops:
        return ResultStatus.NOT_OBSERVED, "No operations or tools were observed.", 0.9, _src(_openapi(surface) or _interface(surface), "operations not observed")
    ids = [op.operation_id for op in ops]
    artifacts = _operation_artifacts(surface, ops)
    if all(ids) and len(set(ids)) == len(ids):
        return ResultStatus.PASS, f"All {len(ids)} observed operations have unique identifiers.", 0.98, _src(artifacts, ", ".join(ids))
    return ResultStatus.FAIL, "At least one operation is missing a stable identifier or identifiers are duplicated.", 0.98, _src(artifacts, str(ids))


def _inputs(surface: DiscoveredSurface, target: Target, scan_id: str):
    ops = _ops(surface)
    artifacts = _operation_artifacts(surface, ops)
    if not ops:
        return ResultStatus.NOT_OBSERVED, "No operations were observed, so input schemas could not be evaluated.", 0.9, _src(artifacts, "input schemas not observed")
    missing: list[str] = []
    for op in ops:
        for param in op.parameters:
            if "schema" not in param and "type" not in param:
                missing.append(op.operation_id or op.path)
            if "required" not in param:
                missing.append(op.operation_id or op.path)
        if op.request_body is not None and not isinstance(op.request_body.get("content"), dict):
            missing.append(op.operation_id or op.path)
    if not missing:
        return ResultStatus.PASS, "Observed parameters expose types/schemas and requiredness.", 0.95, _src(artifacts, "typed input metadata present")
    return ResultStatus.FAIL, f"Input metadata is incomplete for: {', '.join(dict.fromkeys(missing))}.", 0.95, _src(artifacts, str(missing))


def _outputs(surface: DiscoveredSurface, target: Target, scan_id: str):
    ops = _ops(surface)
    artifacts = _operation_artifacts(surface, ops)
    if not ops:
        return ResultStatus.NOT_OBSERVED, "No operations were observed, so output schemas could not be evaluated.", 0.9, _src(artifacts, "output schemas not observed")
    missing = [op.operation_id or op.path for op in ops if not op.responses or not any(isinstance(value, dict) and (value.get("content") or value.get("schema") or value.get("description")) for value in op.responses.values())]
    if not missing:
        return ResultStatus.PASS, "Observed operations expose response descriptions or structured response metadata.", 0.95, _src(artifacts, "structured output metadata present")
    return ResultStatus.FAIL, f"Response metadata is incomplete for: {', '.join(missing)}.", 0.95, _src(artifacts, str(missing))


def _auth(surface: DiscoveredSurface, target: Target, scan_id: str):
    artifacts = _interface(surface)
    if not _has_interface(surface):
        return ResultStatus.NOT_APPLICABLE, "No machine interface was discovered.", 1.0, []
    if surface.security_schemes or any(item.get("auth") or item.get("authentication") for item in surface.agent_metadata):
        return ResultStatus.PASS, "Authentication metadata is machine-identifiable.", 0.95, _src(artifacts, str(list(surface.security_schemes)))
    return ResultStatus.NOT_OBSERVED, "No authentication declaration was observed; passive inspection does not prove the interface is unauthenticated.", 0.95, _src(artifacts, "authentication declaration not observed")


def _scopes(surface: DiscoveredSurface, target: Target, scan_id: str):
    artifacts = _openapi(surface) or _interface(surface)
    schemes = surface.security_schemes
    if not schemes:
        return ResultStatus.NOT_OBSERVED, "No OAuth/OIDC-style scope declaration was observed.", 0.9, _src(artifacts, "authorization scopes not observed")
    scope_names = [scope for scheme in schemes.values() for flow in (scheme.get("flows") or {}).values() if isinstance(flow, dict) for scope in (flow.get("scopes") or {})]
    if scope_names:
        return ResultStatus.PASS, f"Observed {len(scope_names)} declared authorization scope(s).", 0.96, _src(artifacts, ", ".join(scope_names))
    return ResultStatus.NOT_OBSERVED, "Authentication is declared but no authorization scopes were observed.", 0.9, _src(artifacts, "scope declaration not observed")


def _wildcards(surface: DiscoveredSurface, target: Target, scan_id: str):
    mutation = [op for op in _ops(surface) if op.side_effect != SideEffect.NONE]
    artifacts = _operation_artifacts(surface, mutation)
    if not mutation:
        return ResultStatus.NOT_APPLICABLE, "No mutating operation was observed.", 1.0, []
    scopes = [scope.lower() for scheme in surface.security_schemes.values() for flow in (scheme.get("flows") or {}).values() if isinstance(flow, dict) for scope in (flow.get("scopes") or {})]
    broad = [scope for scope in scopes if scope in {"*", "admin", "admin:*", "full_access", "root"} or scope.endswith(":*")]
    if broad:
        return ResultStatus.FAIL, f"Broad scope(s) observed for a surface with mutations: {', '.join(broad)}.", 0.98, _src(artifacts, ", ".join(broad))
    if scopes:
        return ResultStatus.PASS, "No obvious wildcard or global authorization scope was observed.", 0.85, _src(artifacts, ", ".join(scopes))
    return ResultStatus.NOT_OBSERVED, "Mutating operations were observed, but scope breadth could not be established.", 0.9, _src(artifacts, "scope breadth not observed")


def _side_effects(surface: DiscoveredSurface, target: Target, scan_id: str):
    ops = _ops(surface)
    artifacts = _operation_artifacts(surface, ops)
    if not ops:
        return ResultStatus.NOT_OBSERVED, "No operations were observed.", 0.9, _src(artifacts, "side-effect semantics not observed")
    contradictions = [op.operation_id or op.path for op in ops if op.risk.contradiction]
    if contradictions:
        return ResultStatus.WARN, f"Side-effect metadata contradicts structural evidence for: {', '.join(contradictions)}.", 0.98, _src(artifacts, str(contradictions))
    return ResultStatus.PASS, "All observed operations receive a conservative structural side-effect classification.", 0.9, _src(artifacts, ", ".join(f"{op.operation_id or op.path}:{op.side_effect.value}" for op in ops))


def _mutation_gap(surface: DiscoveredSurface) -> list[Any]:
    return [op for op in _ops(surface) if op.side_effect != SideEffect.NONE]


def _quote(surface: DiscoveredSurface, target: Target, scan_id: str):
    mutations = _mutation_gap(surface)
    artifacts = _operation_artifacts(surface, mutations)
    costly = [op for op in mutations if any(word in op.text for word in ("price", "cost", "purchase", "book", "reserve", "transfer", "payment"))]
    if not costly:
        return ResultStatus.NOT_APPLICABLE, "No cost-bearing or high-impact operation was observed.", 0.85, []
    has_quote = any(any(word in op.text for word in ("quote", "preview", "estimate")) for op in _ops(surface))
    if has_quote:
        return ResultStatus.PASS, "A quote, preview, or estimate operation is present before a cost-bearing mutation.", 0.92, _src(artifacts, "quote/preview operation observed")
    return ResultStatus.WARN, "A cost-bearing operation was observed without a clearly discoverable quote or preview boundary.", 0.9, _src(artifacts, ", ".join(op.operation_id or op.path for op in costly))


def _confirmation(surface: DiscoveredSurface, target: Target, scan_id: str):
    high = [op for op in _mutation_gap(surface) if op.side_effect == SideEffect.IRREVERSIBLE]
    artifacts = _operation_artifacts(surface, high)
    if not high:
        return ResultStatus.NOT_APPLICABLE, "No irreversible operation was observed.", 1.0, []
    confirmed = [op for op in high if op.extensions.get("x-confirmation-required") is True or "confirm" in op.text]
    if len(confirmed) == len(high):
        return ResultStatus.PASS, "All observed irreversible operations expose confirmation semantics.", 0.92, _src(artifacts, ", ".join(op.operation_id or op.path for op in confirmed))
    return ResultStatus.WARN, "At least one irreversible operation lacks a machine-observable confirmation requirement.", 0.9, _src(artifacts, ", ".join(op.operation_id or op.path for op in high))


def _idempotency(surface: DiscoveredSurface, target: Target, scan_id: str):
    mutations = _mutation_gap(surface)
    artifacts = _operation_artifacts(surface, mutations)
    if not mutations:
        return ResultStatus.NOT_APPLICABLE, "No mutating operation was observed.", 1.0, []
    markers = ["idempotency", "dedup", "duplicate"]
    supported = [op for op in mutations if any(marker in op.text for marker in markers) or any("idempotency" in str(param).lower() for param in op.parameters) or "x-idempotent" in op.extensions]
    if len(supported) == len(mutations):
        return ResultStatus.PASS, "All observed mutation operations expose idempotency or dedupe evidence.", 0.9, _src(artifacts, "idempotency/dedupe semantics observed")
    return ResultStatus.WARN, "Some mutating operations lack observable idempotency or dedupe semantics.", 0.9, _src(artifacts, str([op.operation_id or op.path for op in mutations if op not in supported]))


def _cancellation(surface: DiscoveredSurface, target: Target, scan_id: str):
    reversible = [op for op in _mutation_gap(surface) if op.side_effect == SideEffect.REVERSIBLE]
    artifacts = _operation_artifacts(surface, reversible)
    if not reversible:
        return ResultStatus.NOT_APPLICABLE, "No reversible mutation was observed.", 1.0, []
    cancel = [op for op in _ops(surface) if any(word in op.text for word in ("cancel", "rollback", "refund", "undo", "compensate"))]
    if cancel:
        return ResultStatus.PASS, "A cancellation or compensating operation is discoverable.", 0.9, _src(_operation_artifacts(surface, cancel), ", ".join(op.operation_id or op.path for op in cancel))
    return ResultStatus.NOT_OBSERVED, "Reversible actions were observed, but no cancellation or compensating action was found.", 0.9, _src(artifacts, "cancellation/compensation not observed")


def _retry(surface: DiscoveredSurface, target: Target, scan_id: str):
    text = " ".join(artifact.content.lower() for artifact in _all(surface))
    if any(marker in text for marker in ("retry-after", "rate limit", "rate-limit", "backoff", "retryable")):
        return ResultStatus.PASS, "Rate-limit or retry guidance is present in the observed artifacts.", 0.85, _src(_all(surface), "retry/rate-limit guidance observed")
    if _ops(surface):
        return ResultStatus.NOT_OBSERVED, "No machine-readable rate-limit or retry guidance was observed.", 0.85, _src(_operation_artifacts(surface), "retry/rate-limit guidance not observed")
    return ResultStatus.NOT_APPLICABLE, "No machine interface was discovered.", 1.0, []


def _errors(surface: DiscoveredSurface, target: Target, scan_id: str):
    ops = _ops(surface)
    artifacts = _operation_artifacts(surface, ops)
    if not ops:
        return ResultStatus.NOT_OBSERVED, "No operations were observed.", 0.9, _src(artifacts, "error semantics not observed")
    good = [op for op in ops if {str(code) for code in op.responses} & {"400", "401", "403", "404", "409", "422", "429", "500", "502", "503"}]
    if len(good) == len(ops):
        return ResultStatus.PASS, "Observed operations document at least one machine-relevant error response.", 0.9, _src(artifacts, "structured error responses observed")
    return ResultStatus.WARN, "Some operations do not document machine-relevant error response classes.", 0.9, _src(artifacts, str([op.operation_id or op.path for op in ops if op not in good]))


def _correlation(surface: DiscoveredSurface, target: Target, scan_id: str):
    text = " ".join(artifact.content.lower() for artifact in _all(surface))
    if any(marker in text for marker in ("x-request-id", "traceparent", "correlation-id", "request id")):
        return ResultStatus.PASS, "Correlation or trace identifier guidance is present.", 0.85, _src(_all(surface), "correlation identifier guidance observed")
    return ResultStatus.NOT_OBSERVED, "No correlation identifier was observed in passive artifacts.", 0.85, _src(_all(surface), "correlation identifier not observed")


def _escalation(surface: DiscoveredSurface, target: Target, scan_id: str):
    text = " ".join(artifact.content.lower() for artifact in _all(surface))
    if any(marker in text for marker in ("mailto:", "support", "contact", "human escalation")):
        return ResultStatus.PASS, "A human support or escalation path is present in the observed public artifacts.", 0.8, _src(_all(surface), "support/contact path observed")
    return ResultStatus.NOT_OBSERVED, "No human escalation path was observed in the bounded artifact set.", 0.8, _src(_all(surface), "support/contact path not observed")


def _secrets(surface: DiscoveredSurface, target: Target, scan_id: str):
    hits: list[Artifact] = []
    for artifact in _all(surface):
        if _DETECTOR.detect_text(artifact.content):
            hits.append(artifact)
    if hits:
        return ResultStatus.FAIL, "An obvious secret-like value was observed and has been redacted from evidence output.", 0.98, _src(hits, ", ".join(artifact.uri for artifact in hits))
    return ResultStatus.PASS, "No obvious credential pattern was observed in the acquired artifacts.", 0.9, _src(_all(surface), "secret pattern scan completed")
