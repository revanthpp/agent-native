from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agentnative.capabilities import CapabilityGraph
from agentnative.capabilities.models import Capability
from agentnative.delegation import DelegationGrant
from agentnative.identity import AgentIdentity, IntegrityResult, ReplayStore, SignedRequest, TrustClass, content_digest, verify_dpop_proof, verify_signed_request
from agentnative.identity.signatures import _covered
from agentnative.policy import Decision, PolicyEngine, PolicyLinter, PolicyRule, authorize_state_change
from agentnative.protocols import A2AAdapter, AdapterRegistry, MCPAdapter, OpenAPIAdapter, ProtocolAdapter
from agentnative.protocols.models import ActionClass, AdapterResult, Limitation
from agentnative.protocols.openapi.refs import RemoteArtifact


RESULTS: list[dict[str, Any]] = []


def rec(name: str, passed: bool, detail: Any = None) -> None:
    RESULTS.append({"name": name, "passed": bool(passed), "detail": detail})


def result_payload(result: AdapterResult) -> dict[str, Any]:
    return {
        "protocol_family": result.protocol_family,
        "version": result.protocol_version,
        "validity": result.validity,
        "detected": result.detected,
        "errors": result.errors,
        "error_evidence": [getattr(item, "__dict__", str(item)) for item in getattr(result, "error_evidence", [])],
        "limitations": [getattr(item, "__dict__", str(item)) for item in result.limitations],
        "artifacts": [getattr(item, "__dict__", str(item)) for item in result.artifacts],
        "capabilities": [item.capability_id for item in result.capabilities],
    }


def no_hostile_echo(payload: dict[str, Any]) -> bool:
    text = json.dumps(payload, default=str)
    banned = ["os.system", "audit-test", "python/object", "python/name", "SECRET_TOKEN_SHOULD_NOT_ECHO"]
    return not any(item in text for item in banned)


HOSTILE_YAML = {
    "apply": 'openapi: 3.1.0\npaths: !!python/object/apply:os.system ["echo audit-test"]\n',
    "new": "openapi: 3.1.0\npaths: !!python/object/new:builtins.dict []\n",
    "name": "openapi: 3.1.0\npaths: !!python/name:os.system\n",
    "custom": "openapi: 3.1.0\npaths: !AuditCustom {x: y}\n",
    "malformed": "openapi: 3.1.0\npaths:\n  /x: [unterminated\n",
}


def check_openapi_boundary() -> None:
    adapter = OpenAPIAdapter()
    details = {}
    for label, document in HOSTILE_YAML.items():
        try:
            detected = adapter.detect(document)
            parsed = adapter.parse(document, f"https://audit.example/{label}.yaml")
            direct_exception = None
        except Exception as exc:  # noqa: BLE001 - audit must record leaks
            detected = None
            parsed = None
            direct_exception = f"{type(exc).__name__}: {exc}"
        registry = AdapterRegistry([adapter]).analyze([(document, f"https://audit.example/{label}.yaml")])
        parsed_payload = result_payload(parsed) if parsed else None
        registry_payload = result_payload(registry[0]) if registry else None
        details[label] = {
            "detect": detected,
            "direct_exception": direct_exception,
            "direct": parsed_payload,
            "registry": registry_payload,
            "sanitized": no_hostile_echo(parsed_payload or {}) and no_hostile_echo(registry_payload or {}),
        }
    passed = all(
        item["direct_exception"] is None
        and item["detect"] is False
        and item["direct"]["validity"] == "INVALID"
        and item["direct"]["errors"]
        and item["registry"]["validity"] in {"INVALID", "ERROR"}
        and item["sanitized"]
        for item in details.values()
    )
    rec("prior_openapi_yaml_boundary_closed", passed, details)


def check_public_operations() -> None:
    adapter = OpenAPIAdapter()
    doc = HOSTILE_YAML["apply"]
    operations = {}
    for name, fn in {
        "validate": lambda: adapter.validate(doc),
        "normalize": lambda: adapter.normalize(doc),
        "enumerate_capabilities": lambda: adapter.enumerate_capabilities(doc),
        "enumerate_auth_requirements": lambda: adapter.enumerate_auth_requirements(doc),
        "enumerate_actions": lambda: adapter.enumerate_actions(doc),
        "enumerate_errors": lambda: adapter.enumerate_errors(doc),
        "enumerate_protocol_limitations": lambda: adapter.enumerate_protocol_limitations(doc),
    }.items():
        try:
            value = fn()
            operations[name] = {"exception": None, "type": type(value).__name__, "value": str(value)[:400]}
        except Exception as exc:  # noqa: BLE001
            operations[name] = {"exception": type(exc).__name__, "message": str(exc)}
    rec("openapi_public_operations_do_not_leak_constructor_error", all(item["exception"] is None for item in operations.values()), operations)


def check_internal_error_separation() -> None:
    class BrokenOpenAPIAdapter(OpenAPIAdapter):
        def _parse_document(self, document: Any) -> dict[str, Any]:
            raise RuntimeError("audit internal defect")

    direct = {}
    try:
        BrokenOpenAPIAdapter().parse("openapi: 3.1.0\npaths: {}\n")
        direct["exception"] = None
    except Exception as exc:  # noqa: BLE001
        direct["exception"] = type(exc).__name__
        direct["message"] = str(exc)
    registry = AdapterRegistry([BrokenOpenAPIAdapter()]).analyze([("openapi: 3.1.0\npaths: {}\n", "memory://broken")])
    payload = result_payload(registry[0]) if registry else {}
    rec(
        "internal_errors_distinguishable_from_target_input",
        direct.get("exception") == "RuntimeError" and payload.get("validity") == "ERROR" and payload.get("errors"),
        {"direct": direct, "registry": payload},
    )


def check_cli_sanitization() -> None:
    executable = Path(sys.executable).parent / "agentnative"
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "hostile.yaml"
        fixture.write_text('openapi: 3.1.0\npaths: !!python/object/apply:os.system ["echo SECRET_TOKEN_SHOULD_NOT_ECHO"]\n', encoding="utf-8")
        proc = subprocess.run([str(executable), "protocols", str(fixture)], text=True, capture_output=True, check=False)
    combined = proc.stdout + proc.stderr
    rec(
        "cli_malicious_yaml_sanitized",
        proc.returncode != 0 and "Traceback" not in combined and "ConstructorError" not in combined and "SECRET_TOKEN_SHOULD_NOT_ECHO" not in combined and "OPENAPI_YAML_PARSE_INVALID" in combined,
        {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr},
    )


def check_cross_adapter_boundaries() -> None:
    mcp_cases = {
        "wrong_top": ["not", "object"],
        "bad_tools": {"tools": "not-list"},
        "bad_schema": {"tools": [{"name": "x", "inputSchema": "bad", "outputSchema": []}]},
        "bad_auth": {"tools": [{"name": "x", "auth": "bad"}]},
        "nested": {"tools": [{"name": "x", "description": {"not": "text"}}], "extensions": {"unknown": {"x": object()}}},
    }
    a2a_cases = {
        "wrong_top": ["not", "object"],
        "missing": {"name": "agent"},
        "bad_skill": {"skills": ["bad"]},
        "bad_auth": {"skills": [{"id": "x", "auth": "bad"}]},
        "duplicate": {"skills": [{"id": "x"}, {"id": "x"}]},
    }
    details = {"mcp": {}, "a2a": {}}
    for label, document in mcp_cases.items():
        try:
            result = MCPAdapter().parse(document)
            details["mcp"][label] = {"exception": None, "result": result_payload(result)}
        except Exception as exc:  # noqa: BLE001
            details["mcp"][label] = {"exception": type(exc).__name__, "message": str(exc)}
    for label, document in a2a_cases.items():
        try:
            result = A2AAdapter().parse(document)
            details["a2a"][label] = {"exception": None, "result": result_payload(result)}
        except Exception as exc:  # noqa: BLE001
            details["a2a"][label] = {"exception": type(exc).__name__, "message": str(exc)}
    passed = all(item["exception"] is None for group in details.values() for item in group.values())
    passed = passed and all(
        item["result"]["errors"] or item["result"]["limitations"] or item["result"]["validity"] in {"INVALID", "NOT_DETECTED", "VALID_WITH_WARNINGS"}
        for group in details.values()
        for item in group.values()
    )
    rec("mcp_a2a_malformed_inputs_structured", passed, details)


class DummyAdapter(ProtocolAdapter):
    protocol_family = "DUMMY"
    protocol_version = "audit"

    def detect(self, document: Any) -> bool:
        return isinstance(document, dict) and document.get("kind") == "dummy"

    def parse(self, document: Any, uri: str = "memory://dummy") -> AdapterResult:
        if document.get("explode"):
            raise RuntimeError("dummy failure")
        return AdapterResult("DUMMY", "audit", self.adapter_version, "audit", limitations=[Limitation("DUMMY", "dummy", uri)])


def check_phase2a_spots() -> None:
    required = ["detect", "parse", "validate", "normalize", "enumerate_capabilities", "enumerate_auth_requirements", "enumerate_actions", "enumerate_errors", "enumerate_protocol_limitations"]
    contract = {adapter.protocol_family: all(callable(getattr(adapter, name, None)) for name in required) for adapter in (OpenAPIAdapter(), MCPAdapter(), A2AAdapter(), DummyAdapter())}
    registry = AdapterRegistry([DummyAdapter()])
    extension_ok = len(registry.analyze([({"kind": "dummy"}, "memory://dummy")])) == 1 and registry.analyze([({"kind": "dummy", "explode": True}, "memory://dummy")])[0].errors
    root = {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": "schema.json#/Ok"}}}}}}
    ref = OpenAPIAdapter().parse(root, "https://audit.example/openapi.json", fetch=lambda uri: RemoteArtifact(uri, {"Ok": {"description": "ok"}}, "hash-ok"))
    redirect = OpenAPIAdapter().parse(root, "https://audit.example/openapi.json", fetch=lambda uri: RemoteArtifact(uri, {"Ok": {}}, "h", "https://evil.example/schema.json"))
    oas = OpenAPIAdapter().parse({"openapi": "3.1.0", "paths": {"/reserve": {"post": {"operationId": "create_reservation"}}}}, "memory://oas")
    mcp = MCPAdapter().parse({"tools": [{"name": "create_reservation"}]}, "memory://mcp")
    a2a = A2AAdapter().parse({"skills": [{"id": "create_reservation"}]}, "memory://a2a")
    graph = CapabilityGraph("business")
    for result in (oas, mcp, a2a):
        for capability in result.capabilities:
            graph.add(capability)
    passed = all(contract.values()) and extension_ok and not ref.errors and any(a.content_hash == "hash-ok" for a in ref.artifacts) and "OAS_REF_REDIRECT_BLOCKED" in {l.code for l in redirect.limitations} and len(graph.values()) == 1
    rec("phase2a_regression_spots", passed, {"contract": contract, "extension_ok": bool(extension_ok), "ref": result_payload(ref), "redirect": result_payload(redirect), "graph_count": len(graph.values())})


def check_phase2b_spots() -> None:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    body = b"{}"
    now = int(datetime.now(timezone.utc).timestamp())
    components = '"@method" "@target-uri" "content-digest"'
    params = f'sig1=({components});created={now};keyid="k";alg="ed25519";nonce="n"'
    unsigned = SignedRequest("POST", "https://audit.example/pay", {"content-digest": content_digest(body)}, body, params, "")
    sig = private.sign(_covered(unsigned, components, str(now), "k", "ed25519", "n"))
    request = SignedRequest(unsigned.method, unsigned.target_uri, unsigned.headers, unsigned.body, params, "sig1=:" + base64.b64encode(sig).decode() + ":")
    replay = ReplayStore()
    valid = verify_signed_request(request, lambda key: (public, "agent"), replay, require_content_digest=True, now=now)
    replayed = verify_signed_request(request, lambda key: (public, "agent"), replay, require_content_digest=True, now=now)
    promoted = AgentIdentity.from_integrity(provider_id="provider", display_name="Agent", integrity=valid)
    capability = Capability("cap:purchase", "business", "purchase", action_class=ActionClass.PURCHASE)
    identity = AgentIdentity("agent", "provider", "Agent", TrustClass.PARTNER)
    grant = DelegationGrant("grant", "principal", "agent", "provider", frozenset({"cap:purchase"}), audience="api", resource_boundary="r1", value_limit=10)
    engine = PolicyEngine([
        PolicyRule("allow", trust_class="PARTNER", capability="cap:purchase", decision=Decision.ALLOW, owner="security"),
        PolicyRule("deny", trust_class="PARTNER", capability="cap:purchase", decision=Decision.DENY, owner="security", priority=10),
    ])
    deny = authorize_state_change(owner_verified=True, identity=identity, integrity=valid, grant=grant, capability=capability, engine=engine, context={"principal": "principal", "audience": "api", "resource": "r1", "value": 1})
    missing_policy = authorize_state_change(owner_verified=True, identity=identity, integrity=valid, grant=grant, capability=capability, engine=PolicyEngine([]), context={"principal": "principal", "audience": "api", "resource": "r1", "value": 1})
    confused = grant.authorize(principal="other", agent_id="agent", provider_id="provider", capability_id="cap:purchase", resource="r1", audience="api", value=1)
    lint = PolicyLinter().lint([PolicyRule("allow", capability="cap:purchase", decision=Decision.ALLOW)])
    dpop_invalid = verify_dpop_proof("not.a.jwt", method="POST", target_uri="https://audit.example/pay", replay=ReplayStore(), now=now)
    passed = valid.valid and replayed.reason == "replay_detected" and promoted.trust_class == TrustClass.CRYPTOGRAPHICALLY_VERIFIED and deny.decision == Decision.DENY and missing_policy.decision == Decision.DENY and confused[0] is False and lint and dpop_invalid.status.value == "INVALID"
    rec("phase2b_regression_spots", passed, {"valid": asdict(valid), "replay": asdict(replayed), "trust": promoted.trust_class.value, "deny": asdict(deny), "missing_policy": asdict(missing_policy), "confused": confused, "lint": lint, "dpop": asdict(dpop_invalid)})


def main() -> int:
    for fn in (
        check_openapi_boundary,
        check_public_operations,
        check_internal_error_separation,
        check_cli_sanitization,
        check_cross_adapter_boundaries,
        check_phase2a_spots,
        check_phase2b_spots,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            rec(fn.__name__, False, {"exception": type(exc).__name__, "message": str(exc)})
    payload = {"passed": sum(1 for item in RESULTS if item["passed"]), "total": len(RESULTS), "results": RESULTS}
    print(json.dumps(payload, indent=2, default=str))
    return 0 if all(item["passed"] for item in RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
