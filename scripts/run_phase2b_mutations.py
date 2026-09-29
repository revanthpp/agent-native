"""Run real Phase 2B control mutations against canonical production seams.

Each mutant disables one injectable production control and re-runs the same
adversarial scenario used by its baseline. The source tree is never rewritten.
A surviving mutant exits nonzero.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentnative.capabilities.models import Capability
from agentnative.identity import AgentIdentity, IntegrityResult, TrustClass
from agentnative.mutation import MutationCase, MutationHarness
from agentnative.policy import AuthorizationControls, Decision, PolicyControls, PolicyEngine, PolicyRule, authorize_state_change
from agentnative.protocols.models import ActionClass
from agentnative.protocols.openapi.adapter import OpenAPIAdapter
from agentnative.protocols.openapi.refs import RemoteArtifact
from agentnative.security.sanitize import Sanitizer


def _scenario(*, identity, integrity, grant, capability, engine, context, controls=None, owner_verified=True):
    return authorize_state_change(
        owner_verified=owner_verified,
        identity=identity,
        integrity=integrity,
        grant=grant,
        capability=capability,
        engine=engine,
        context=context,
        controls=controls,
    ).decision == Decision.DENY


def _auth_case(mutation_id, control, mutation, *, identity, integrity, grant, capability, engine, context, owner_verified=True, mutate):
    baseline_controls = AuthorizationControls()
    mutated_controls = mutate(baseline_controls)
    return MutationCase(
        mutation_id,
        control,
        mutation,
        lambda: _scenario(identity=identity, integrity=integrity, grant=grant, capability=capability, engine=engine, context=context, controls=baseline_controls, owner_verified=owner_verified),
        lambda: _scenario(identity=identity, integrity=integrity, grant=grant, capability=capability, engine=engine, context=context, controls=mutated_controls, owner_verified=owner_verified),
    )


def _engine_for(capability, *, rules=None, version="1"):
    return PolicyEngine(rules if rules is not None else [PolicyRule("allow", trust_class="PARTNER", capability=capability.capability_id, decision=Decision.ALLOW, owner="security")], version=version)


def main() -> int:
    now = datetime.now(timezone.utc)
    identity = AgentIdentity("agent", "provider", "Agent", TrustClass.PARTNER)
    capability = Capability("cap:purchase", "business", "purchase", action_class=ActionClass.PURCHASE)
    valid_integrity = IntegrityResult(True, "verified", "key", "agent", "nonce")
    cases = []
    base_grant = __import__("agentnative.delegation", fromlist=["DelegationGrant"]).DelegationGrant(
        "grant", "principal", "agent", "provider", frozenset({"cap:purchase"}), audience="api", resource_boundary="orders:1", value_limit=10
    )
    context = {"principal": "principal", "audience": "api", "resource": "orders:1", "value": 5}
    cases.append(_auth_case("M-OWNERSHIP", "owner verification", "bypass owner gate", identity=identity, integrity=valid_integrity, grant=base_grant, capability=capability, engine=_engine_for(capability), context=context, owner_verified=False, mutate=lambda c: replace(c, owner_verification=False)))
    cases.append(_auth_case("M-SIGNATURE", "signature verification", "accept invalid signature", identity=identity, integrity=IntegrityResult(False, "invalid_signature"), grant=base_grant, capability=capability, engine=_engine_for(capability), context=context, mutate=lambda c: replace(c, signature_verification=False)))
    cases.append(_auth_case("M-REPLAY", "replay protection", "accept duplicate nonce", identity=identity, integrity=IntegrityResult(True, "replay_detected"), grant=base_grant, capability=capability, engine=_engine_for(capability), context=context, mutate=lambda c: replace(c, replay_protection=False)))

    grant_cases = [
        ("M-GRANT-EXPIRY", "delegation expiry", "accept expired grant", replace(base_grant, expires_at=now - timedelta(seconds=1)), {}, "expiry"),
        ("M-REVOCATION", "delegation revocation", "ignore revoked flag", replace(base_grant, revoked=True), {}, "revocation"),
        ("M-PRINCIPAL", "principal binding", "ignore principal", base_grant, {"principal": "other"}, "principal_binding"),
        ("M-AGENT", "agent binding", "ignore agent", base_grant, {}, "agent_binding", AgentIdentity("other-agent", "provider", "Agent", TrustClass.PARTNER)),
        ("M-PROVIDER", "provider binding", "ignore provider", base_grant, {}, "provider_binding", AgentIdentity("agent", "other-provider", "Agent", TrustClass.PARTNER)),
        ("M-AUDIENCE", "audience binding", "ignore audience", base_grant, {"audience": "other"}, "audience_binding"),
        ("M-CAPABILITY", "capability binding", "ignore capability", base_grant, {}, "capability_binding", None, Capability("cap:other", "business", "other", action_class=ActionClass.PURCHASE)),
        ("M-RESOURCE", "resource binding", "ignore resource", base_grant, {"resource": "orders:2"}, "resource_binding"),
        ("M-VALUE", "value ceiling", "ignore value limit", base_grant, {"value": 11}, "value_limit"),
    ]
    for item in grant_cases:
        mutation_id, control, mutation, grant, overrides, field = item[:6]
        case_identity = item[6] if len(item) > 6 and isinstance(item[6], AgentIdentity) else identity
        case_capability = item[7] if len(item) > 7 and isinstance(item[7], Capability) else capability
        case_context = {**context, **overrides}
        case_engine = _engine_for(case_capability)
        cases.append(_auth_case(mutation_id, control, mutation, identity=case_identity, integrity=valid_integrity, grant=grant, capability=case_capability, engine=case_engine, context=case_context, mutate=lambda c, field=field: replace(c, delegation=replace(c.delegation, **{field: False}))))

    deny_rules = [PolicyRule("allow", trust_class="PARTNER", capability=capability.capability_id, decision=Decision.ALLOW, owner="security"), PolicyRule("deny", trust_class="PARTNER", capability=capability.capability_id, decision=Decision.DENY, owner="security")]
    cases.append(_auth_case("M-DENY", "explicit deny precedence", "allow explicitly denied capability", identity=identity, integrity=valid_integrity, grant=base_grant, capability=capability, engine=_engine_for(capability, rules=deny_rules), context=context, mutate=lambda c: replace(c, policy=replace(c.policy, explicit_deny_precedence=False))))
    cases.append(_auth_case("M-DEFAULT", "state-changing default deny", "default allow", identity=identity, integrity=valid_integrity, grant=base_grant, capability=capability, engine=_engine_for(capability, rules=[]), context=context, mutate=lambda c: replace(c, policy=replace(c.policy, default_deny=False))))
    cases.append(_auth_case("M-VERSION", "policy version", "use stale policy version", identity=identity, integrity=valid_integrity, grant=base_grant, capability=capability, engine=_engine_for(capability, version="2"), context={**context, "policy_version": "1"}, mutate=lambda c: replace(c, policy=replace(c.policy, policy_version=False))))

    secret_case = "token=FAKE_MUTATION_SECRET_1234567890"
    cases.append(MutationCase("M-REDACTION", "secret redaction", "emit raw secret", lambda: "[REDACTED]" in Sanitizer().text(secret_case)[0], lambda: "[REDACTED]" in Sanitizer(redaction_enabled=False).text(secret_case)[0]))

    ref_document = {"openapi": "3.1.0", "paths": {"/x": {"get": {"responses": {"200": {"$ref": "http://127.0.0.1/schema"}}}}}}
    def ref_invariant(enforce):
        calls = []
        result = OpenAPIAdapter().parse(ref_document, "https://business.test/openapi.json", fetch=lambda uri: (calls.append(uri) or RemoteArtifact(uri, {})), enforce_network_policy=enforce)
        return "OAS_REF_PRIVATE_NETWORK" in {item.code for item in result.limitations} and not calls
    cases.append(MutationCase("M-REF-NETWORK", "remote $ref network policy", "fetch unsafe private target", lambda: ref_invariant(True), lambda: ref_invariant(False)))

    hostile_yaml = '!!python/object/apply:os.system ["echo unsafe"]'
    def adapter_error_boundary(normalize):
        adapter = OpenAPIAdapter()
        if not normalize:
            def unsafe_parse(document):
                return yaml.safe_load(document)

            def bypass_normalization(document, uri, exc, *, operation):
                raise exc

            with patch.object(adapter, "_parse_document", unsafe_parse), patch.object(adapter, "_normalize_parse_error", bypass_normalization):
                try:
                    adapter.parse(hostile_yaml, "fixture://hostile")
                except yaml.YAMLError:
                    return False
                return True
        result = adapter.parse(hostile_yaml, "fixture://hostile")
        return result.status == "INVALID" and bool(result.error_details)

    cases.append(MutationCase("M-ADAPTER-YAML-ERROR", "adapter parser-error normalization", "bypass direct OpenAPI YAML error conversion", lambda: adapter_error_boundary(True), lambda: adapter_error_boundary(False)))
    results = MutationHarness().run(cases)
    payload = [{"mutation_id": r.mutation_id, "production_control": r.control, "mutation": r.mutation, "expected_test_failure": r.expected_test_failure, "actual_result": r.actual_result, "caught": r.caught} for r in results]
    print(json.dumps(payload, indent=2))
    return 0 if all(item["caught"] for item in payload) else 1


if __name__ == "__main__":
    raise SystemExit(main())
