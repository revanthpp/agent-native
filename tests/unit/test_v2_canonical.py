import base64
import json
import hashlib
import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ec import ECDSA, SECP256R1
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from agentnative.capabilities import CapabilityGraph
from agentnative.capabilities.models import Capability
from agentnative.identity import AgentIdentity, TrustClass
from agentnative.mutation import MutationCase, MutationHarness
from agentnative.policy import Decision, PolicyEngine, PolicyRule, authorize_state_change
from agentnative.policy_store import VersionedPolicyStore
from agentnative.protocols import A2AAdapter, MCPAdapter, OpenAPIAdapter
from agentnative.request_integrity import ReplayStore, SignedRequest, _covered, content_digest, verify_signed_request
from agentnative.oauth import EvidenceStatus, verify_dpop_proof
from agentnative.protocols.models import ActionClass
from agentnative.cli.main import main as cli_main


class CanonicalV2Tests(unittest.TestCase):
    def test_protocols_and_graph_are_root_canonical(self):
        oas = OpenAPIAdapter().parse("openapi: 3.1.0\npaths:\n  /search:\n    get:\n      operationId: search_orders\n")
        mcp = MCPAdapter().parse({"tools": [{"name": "search_orders"}]})
        a2a = A2AAdapter().parse({"name": "Agent", "skills": [{"id": "search_orders"}]})
        graph = CapabilityGraph("business")
        for result in (oas, mcp, a2a): graph.values(); [graph.add(capability) for capability in result.capabilities]
        self.assertEqual(len(graph.values()), 1)
        self.assertEqual(len(graph.values()[0].protocol_sources), 3)

    def test_signature_replay_and_verified_identity(self):
        private = Ed25519PrivateKey.generate(); public = private.public_key().public_bytes_raw(); body = b"{}"; now = int(datetime.now(timezone.utc).timestamp()); components = '"@method" "@target-uri" "content-digest"'
        params = f'sig1=({components});created={now};keyid="k";alg="ed25519";nonce="n"'
        unsigned = SignedRequest("POST", "https://business.test/purchase", {"content-digest": content_digest(body)}, body, params, "")
        sig = private.sign(_covered(unsigned, components, str(now), "k", "ed25519", "n"))
        request = SignedRequest(unsigned.method, unsigned.target_uri, unsigned.headers, unsigned.body, params, "sig1=:" + base64.b64encode(sig).decode() + ":")
        result = verify_signed_request(request, lambda key: (public, "agent-1"), ReplayStore(), require_content_digest=True, now=now)
        self.assertTrue(result.valid)
        self.assertEqual(AgentIdentity.from_integrity(provider_id="provider", display_name="Agent", integrity=result).trust_class, TrustClass.CRYPTOGRAPHICALLY_VERIFIED)

    def test_policy_store_and_mutation_harness(self):
        store = VersionedPolicyStore(); rule = PolicyRule("default", decision=Decision.DENY, owner="security")
        store.activate("p", "1", [rule], "security", "initial"); store.activate("p", "2", [rule], "security", "deny")
        self.assertEqual(store.get("p").version, "2")
        result = MutationHarness().run([MutationCase("M-DEFAULT", "default-deny", "allow", lambda: False, lambda: True)])[0]
        self.assertTrue(result.caught)

    def test_state_change_pipeline_fails_closed_until_every_gate_is_present(self):
        capability = Capability("cap:purchase", "business", "purchase", action_class=ActionClass.PURCHASE)
        engine = PolicyEngine([PolicyRule("allow", trust_class="PARTNER", capability="cap:purchase", decision=Decision.ALLOW, owner="security")])
        identity = AgentIdentity("agent", "provider", "Agent", TrustClass.PARTNER)
        grant = __import__("agentnative.delegation", fromlist=["DelegationGrant"]).DelegationGrant("grant", "principal", "agent", "provider", frozenset({"cap:purchase"}), audience="api")
        invalid = type("Integrity", (), {"valid": False})()
        self.assertEqual(authorize_state_change(owner_verified=False, identity=identity, integrity=invalid, grant=grant, capability=capability, engine=engine, context={"principal": "principal", "audience": "api"}).decision, Decision.DENY)
        self.assertEqual(authorize_state_change(owner_verified=True, identity=identity, integrity=invalid, grant=grant, capability=capability, engine=engine, context={"principal": "principal", "audience": "api"}).decision, Decision.DENY)
        valid = type("Integrity", (), {"valid": True})()
        self.assertEqual(authorize_state_change(owner_verified=True, identity=identity, integrity=valid, grant=None, capability=capability, engine=engine, context={"principal": "principal", "audience": "api"}).decision, Decision.DENY)
        self.assertEqual(authorize_state_change(owner_verified=True, identity=identity, integrity=valid, grant=grant, capability=capability, engine=engine, context={"principal": "principal", "audience": "api"}).decision, Decision.ALLOW)

    def test_production_source_has_no_deprecated_import(self):
        root = Path(__file__).resolve().parents[2] / "src" / "agentnative"
        source = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))
        self.assertNotIn("agentnative_v2", source)

    def test_dpop_validity_and_replay(self):
        key = __import__("cryptography.hazmat.primitives.asymmetric.ec", fromlist=["generate_private_key"]).generate_private_key(SECP256R1())
        numbers = key.public_key().public_numbers()
        enc = lambda value: base64.urlsafe_b64encode(value.to_bytes(32, "big")).rstrip(b"=").decode()
        header = {"typ": "dpop+jwt", "alg": "ES256", "jwk": {"kty": "EC", "crv": "P-256", "x": enc(numbers.x), "y": enc(numbers.y)}}
        now = int(datetime.now(timezone.utc).timestamp()); payload = {"htm": "POST", "htu": "https://business.test/purchase", "iat": now, "jti": "proof-1"}
        b64 = lambda value: base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=").decode()
        signing = b64(header) + "." + b64(payload); r, s = decode_dss_signature(key.sign(signing.encode(), ECDSA(SHA256())))
        proof = signing + "." + base64.urlsafe_b64encode(r.to_bytes(32, "big") + s.to_bytes(32, "big")).rstrip(b"=").decode()
        replay = ReplayStore(); result = verify_dpop_proof(proof, method="POST", target_uri="https://business.test/purchase", replay=replay, now=now)
        self.assertEqual(result.status, EvidenceStatus.VERIFIED)
        self.assertEqual(verify_dpop_proof(proof, method="POST", target_uri="https://business.test/purchase", replay=replay, now=now).reason, "replay_detected")
        self.assertEqual(verify_dpop_proof(proof, method="GET", target_uri="https://business.test/purchase", replay=ReplayStore(), now=now).status, EvidenceStatus.INVALID)
        self.assertEqual(verify_dpop_proof(proof, method="POST", target_uri="https://other.test/purchase", replay=ReplayStore(), now=now).status, EvidenceStatus.INVALID)
        self.assertEqual(verify_dpop_proof(proof, method="POST", target_uri="https://business.test/purchase", replay=ReplayStore(), now=now + 301).status, EvidenceStatus.INVALID)
        self.assertEqual(verify_dpop_proof(proof, method="POST", target_uri="https://business.test/purchase", replay=ReplayStore(), access_token="token", now=now).status, EvidenceStatus.INVALID)
        self.assertEqual(verify_dpop_proof(proof, method="POST", target_uri="https://business.test/purchase", replay=ReplayStore(), expected_nonce="server-nonce", now=now).status, EvidenceStatus.INVALID)
        self.assertEqual(verify_dpop_proof("not.a.proof", method="POST", target_uri="https://business.test/purchase", replay=ReplayStore(), now=now).status, EvidenceStatus.INVALID)

    def test_policy_lint_cli_uses_canonical_linter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as policy_file:
            policy_file.write('{"rules": [{"policy_id": "allow", "capability": "read", "decision": "ALLOW", "owner": "security"}]}')
            policy_file.flush()
            self.assertEqual(cli_main(["policy", "lint", policy_file.name]), 1)


if __name__ == "__main__":
    unittest.main()
