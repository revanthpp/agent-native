from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agentnative.capabilities import CapabilityGraph
from agentnative.capabilities.models import Capability
from agentnative.delegation import DelegationGrant
from agentnative.identity import AgentIdentity, IntegrityResult, ReplayStore, SignedRequest, TrustClass, content_digest, verify_signed_request
from agentnative.identity.signatures import _covered
from agentnative.policy import Decision, PolicyEngine, PolicyLinter, PolicyRule, authorize_state_change
from agentnative.protocols import A2AAdapter, AdapterRegistry, MCPAdapter, OpenAPIAdapter, ProtocolAdapter
from agentnative.protocols.models import ActionClass, AdapterResult, Limitation, SideEffect
from agentnative.protocols.openapi.refs import RemoteArtifact


RESULTS: list[dict[str, Any]] = []


def record(name: str, passed: bool, detail: Any = None) -> None:
    RESULTS.append({"name": name, "passed": bool(passed), "detail": detail})


def codes(result: AdapterResult) -> set[str]:
    return {item.code for item in result.limitations}


class IndependentDummyAdapter(ProtocolAdapter):
    protocol_family = "DUMMY"
    protocol_version = "audit-1"

    def detect(self, document: Any) -> bool:
        return isinstance(document, dict) and document.get("kind") == "dummy"

    def parse(self, document: Any, uri: str = "memory://dummy") -> AdapterResult:
        if document.get("explode"):
            raise RuntimeError("boom")
        result = AdapterResult("DUMMY", self.protocol_version, self.adapter_version, "audit")
        result.limitations.append(Limitation("DUMMY_LIMIT", "audit limitation", uri))
        result.capabilities.append(Capability("dummy:act", "business", "dummy_act", protocol_sources=[uri], action_class=ActionClass.READ))
        result.auth_requirements.append({"type": "none"})
        return result


def check_adapter_contract() -> None:
    required = ["detect", "parse", "validate", "normalize", "enumerate_capabilities", "enumerate_auth_requirements", "enumerate_actions", "enumerate_errors", "enumerate_protocol_limitations"]
    matrix = {}
    for adapter in (OpenAPIAdapter(), MCPAdapter(), A2AAdapter(), IndependentDummyAdapter()):
        matrix[adapter.protocol_family] = {name: callable(getattr(adapter, name, None)) for name in required}
    registry = AdapterRegistry([IndependentDummyAdapter()])
    ok = registry.analyze([({"kind": "dummy"}, "memory://ok")])
    fail = registry.analyze([({"kind": "dummy", "explode": True}, "memory://fail")])
    record("adapter_contract_methods", all(all(row.values()) for row in matrix.values()), matrix)
    record("extension_registration_and_failure_isolation", len(ok) == 1 and ok[0].capabilities and len(fail) == 1 and fail[0].errors, {"ok": len(ok), "fail_errors": fail[0].errors if fail else None})


def check_openapi_refs() -> None:
    root = {"openapi": "3.1.0", "paths": {"/reserve": {"post": {"operationId": "create_reservation", "requestBody": {"$ref": "schema.json#/Order"}}}}}
    docs = {
        "https://audit.example/schema.json": RemoteArtifact("https://audit.example/schema.json", {"Order": {"$ref": "nested.json#/Nested"}}, "schema-hash"),
        "https://audit.example/nested.json": RemoteArtifact("https://audit.example/nested.json", {"Nested": {"type": "object"}}, "nested-hash"),
    }
    result = OpenAPIAdapter().parse(root, "https://audit.example/openapi.json", fetch=docs.__getitem__)
    record("same_origin_nested_refs", not result.errors and {"schema-hash", "nested-hash"} <= {artifact.content_hash for artifact in result.artifacts}, [artifact.__dict__ for artifact in result.artifacts])

    unsafe_refs = {
        "localhost": "https://localhost/schema.json",
        "rfc1918": "https://10.0.0.1/schema.json",
        "link_local": "https://169.254.169.254/schema.json",
        "ipv6_loopback": "https://[::1]/schema.json",
        "file": "file:///etc/passwd",
        "ftp": "ftp://audit.example/schema.json",
    }
    blocked = {}
    for label, ref in unsafe_refs.items():
        calls: list[str] = []
        doc = {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": ref}}}}}}
        res = OpenAPIAdapter().parse(doc, "https://audit.example/openapi.json", fetch=lambda uri: calls.append(uri))
        blocked[label] = {"codes": sorted(codes(res)), "fetch_calls": calls}
    record("unsafe_refs_block_without_fetch", all(item["codes"] and not item["fetch_calls"] for item in blocked.values()), blocked)

    redirect = OpenAPIAdapter().parse(
        {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": "schema.json"}}}}}},
        "https://audit.example/openapi.json",
        fetch=lambda uri: RemoteArtifact(uri, {}, final_uri="https://evil.example/schema.json"),
    )
    record("cross_origin_redirect_blocked", "OAS_REF_REDIRECT_BLOCKED" in codes(redirect), sorted(codes(redirect)))

    malformed = OpenAPIAdapter().parse("!!python/object/apply:os.system ['echo nope']")
    record("malicious_yaml_rejected", bool(malformed.errors or "OAS_PARSE_ERROR" in codes(malformed)), {"errors": malformed.errors, "limitations": sorted(codes(malformed))})


def check_protocol_normalization() -> None:
    oas = OpenAPIAdapter().parse({"openapi": "3.1.0", "paths": {"/reservations": {"post": {"operationId": "create_reservation", "description": "reserve a seat", "security": [{"oauth": ["reservations:create"]}]}}}}, "memory://oas")
    mcp = MCPAdapter().parse({"tools": [{"name": "create_reservation", "description": "reserve seat", "inputSchema": {}, "auth": {"type": "oauth"}}]}, "memory://mcp")
    a2a = A2AAdapter().parse({"name": "Audit Agent", "version": "1.0.0", "skills": [{"id": "create_reservation", "description": "reserve seat", "auth": {"type": "oauth"}}]}, "memory://a2a")
    graph = CapabilityGraph("audit-business")
    for result in (oas, mcp, a2a):
        for capability in result.capabilities:
            graph.add(capability)
    values = graph.values()
    record("cross_protocol_capability_graph", len(values) == 1 and set(values[0].protocol_sources) == {"memory://oas", "memory://mcp", "memory://a2a"} and values[0].side_effect in {SideEffect.UNKNOWN, SideEffect.REVERSIBLE}, values[0].__dict__ if values else None)


def check_policy() -> None:
    now = datetime.now(timezone.utc)
    linter = PolicyLinter()
    triggers = {
        "missing_default": [PolicyRule("allow", capability="cap:purchase", decision=Decision.ALLOW, owner="security")],
        "unowned": [PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("x", capability="cap:x")],
        "expired": [PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("x", owner="security", expires_at=now - timedelta(seconds=1))],
        "future": [PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("x", owner="security", effective_at=now + timedelta(hours=1))],
        "wildcard": [PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("x", capability="cap:x", decision=Decision.ALLOW, owner="security")],
        "contradiction": [PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("a", trust_class="PARTNER", capability="cap:x", decision=Decision.ALLOW, owner="security"), PolicyRule("b", trust_class="PARTNER", capability="cap:x", decision=Decision.DENY, owner="security")],
        "sensitive": [PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("x", trust_class="PARTNER", capability="cap:purchase", decision=Decision.ALLOW, owner="security")],
        "environment": [PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("x", environment="PRODUCTION_ACTIVE", decision=Decision.ALLOW, owner="security")],
    }
    found = {name: linter.lint(rules, now=now) for name, rules in triggers.items()}
    safe = linter.lint([PolicyRule("default", decision=Decision.DENY, owner="security"), PolicyRule("safe", trust_class="PARTNER", capability="cap:read", decision=Decision.ALLOW, owner="security", required_confirmation=True)], now=now)
    record("policy_lint_triggers_and_safe_case", all(found.values()) and not safe, {"triggers": found, "safe": safe})

    capability = Capability("cap:purchase", "business", "purchase", action_class=ActionClass.PURCHASE)
    identity = AgentIdentity("agent", "provider", "Agent", TrustClass.PARTNER)
    grant = DelegationGrant("grant", "principal", "agent", "provider", frozenset({"cap:purchase"}), audience="api")
    integrity = IntegrityResult(True, "verified", "key", "agent", "nonce")
    context = {"principal": "principal", "audience": "api"}
    broad_allow = PolicyRule("allow", trust_class="PARTNER", capability="cap:purchase", decision=Decision.ALLOW, owner="security")
    specific_deny = PolicyRule("deny", trust_class="PARTNER", capability="cap:purchase", decision=Decision.DENY, owner="security", priority=10)
    deny_decision = authorize_state_change(owner_verified=True, identity=identity, integrity=integrity, grant=grant, capability=capability, engine=PolicyEngine([broad_allow, specific_deny]), context=context)
    missing_policy = authorize_state_change(owner_verified=True, identity=identity, integrity=integrity, grant=grant, capability=capability, engine=PolicyEngine([]), context=context)
    record("policy_precedence_and_default_deny", deny_decision.decision == Decision.DENY and missing_policy.decision == Decision.DENY, {"specific_deny": deny_decision.__dict__, "missing_policy": missing_policy.__dict__})


def check_identity_delegation() -> None:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    now = int(datetime.now(timezone.utc).timestamp())
    body = b'{"ok":true}'
    components = '"@method" "@target-uri" "content-digest"'
    params = f'sig1=({components});created={now};keyid="key-1";alg="ed25519";nonce="n-1"'
    unsigned = SignedRequest("POST", "https://audit.example/commit", {"content-digest": content_digest(body)}, body, params, "")
    signature = private.sign(_covered(unsigned, components, str(now), "key-1", "ed25519", "n-1"))
    request = SignedRequest(unsigned.method, unsigned.target_uri, unsigned.headers, unsigned.body, params, "sig1=:" + base64.b64encode(signature).decode() + ":")
    replay = ReplayStore()
    valid = verify_signed_request(request, lambda key: (public, "agent-a"), replay, require_content_digest=True, now=now)
    replayed = verify_signed_request(request, lambda key: (public, "agent-a"), replay, require_content_digest=True, now=now)
    tampered = SignedRequest("GET", request.target_uri, request.headers, request.body, request.signature_input, request.signature)
    bad = verify_signed_request(tampered, lambda key: (public, "agent-a"), ReplayStore(), require_content_digest=True, now=now)
    promotion_blocked = False
    try:
        AgentIdentity.from_integrity(provider_id="provider", display_name="Agent", integrity=IntegrityResult(False, "invalid"))
    except ValueError:
        promotion_blocked = True
    record("signature_replay_and_identity_promotion", valid.valid and replayed.reason == "replay_detected" and not bad.valid and promotion_blocked, {"valid": valid.__dict__, "replay": replayed.__dict__, "tampered": bad.__dict__, "promotion_blocked": promotion_blocked})

    grant = DelegationGrant("grant", "principal-a", "agent-a", "provider-a", frozenset({"cap:a"}), resource_boundary="resource:x", value_limit=100, audience="aud")
    cases = {
        "wrong_principal": grant.authorize(principal="principal-b", agent_id="agent-a", provider_id="provider-a", capability_id="cap:a", resource="resource:x", audience="aud", value=1)[0],
        "wrong_agent": grant.authorize(principal="principal-a", agent_id="agent-b", provider_id="provider-a", capability_id="cap:a", resource="resource:x", audience="aud", value=1)[0],
        "wrong_capability": grant.authorize(principal="principal-a", agent_id="agent-a", provider_id="provider-a", capability_id="cap:b", resource="resource:x", audience="aud", value=1)[0],
        "wrong_resource": grant.authorize(principal="principal-a", agent_id="agent-a", provider_id="provider-a", capability_id="cap:a", resource="resource:y", audience="aud", value=1)[0],
        "excessive_value": grant.authorize(principal="principal-a", agent_id="agent-a", provider_id="provider-a", capability_id="cap:a", resource="resource:x", audience="aud", value=1000)[0],
    }
    record("delegation_confused_deputy_denies", not any(cases.values()), cases)


def check_cli_policy_lint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "policy.json"
        path.write_text(json.dumps({"rules": [{"policy_id": "allow", "capability": "cap:purchase", "decision": "ALLOW"}]}), encoding="utf-8")
        executable = str(Path(sys.executable).parent / "agentnative")
        proc = subprocess.run([executable, "policy", "lint", str(path)], text=True, capture_output=True, check=False)
    record("cli_policy_lint_semantics", proc.returncode == 1 and "POL-LINT-001" in proc.stdout and "POL-LINT-005" in proc.stdout, {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})


def main() -> int:
    for fn in (check_adapter_contract, check_openapi_refs, check_protocol_normalization, check_policy, check_identity_delegation, check_cli_policy_lint):
        try:
            fn()
        except Exception as exc:
            record(fn.__name__, False, {"exception": type(exc).__name__, "message": str(exc)})
    print(json.dumps({"passed": sum(1 for item in RESULTS if item["passed"]), "total": len(RESULTS), "results": RESULTS}, indent=2, default=str))
    return 0 if all(item["passed"] for item in RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
