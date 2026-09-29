"""Named, independent behavioral oracles for the real Phase 3B mutants.

This module is executed inside each isolated mutant copy. It intentionally does
not ask the production code for an expected result; each function asserts the
control that must remain true from an independent fixture or invariant.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(os.environ.get("AGENTNATIVE_REPO_ROOT", Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(ROOT / "src"))


def _workspace(mutator):
    source = ROOT / "examples" / "retail" / "direct-ready"
    directory = Path(tempfile.mkdtemp(prefix="gate2-workspace-"))
    shutil.copytree(source, directory / "project")
    path = directory / "project" / "project.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutator(raw)
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return directory


def test_unknown_scenario():
    from agentnative.retail_product import RetailProductError, simulate_workspace

    try:
        simulate_workspace(ROOT / "examples" / "retail" / "direct-ready", "not-registered")
    except RetailProductError as exc:
        assert exc.code == "UNKNOWN_SCENARIO"
        return
    raise AssertionError("unknown scenario was accepted")


def _recommendation(project: Path, journey_id: str) -> dict:
    from agentnative.retail_product import assess_workspace

    assessment = assess_workspace(project)
    return next(item["recommendation"] for item in assessment["recommendations"] if item["journey"]["journey_id"] == journey_id)


def test_capability_gate():
    directory = _workspace(lambda raw: raw["capability_inventory"].pop(0))
    try:
        assert _recommendation(directory / "project", "product_discovery")["recommended_pattern"] != "DIRECT"
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_declared_readiness():
    def mutate(raw):
        next(item for item in raw["capability_inventory"] if item["capability_id"] == "submit_order")["state"] = "DECLARED"

    directory = _workspace(mutate)
    try:
        assert _recommendation(directory / "project", "controlled_checkout")["recommended_pattern"] != "DIRECT"
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_evidence_state():
    def mutate(raw):
        raw["evidence_sources"][1]["state"] = "CONFLICTING"

    directory = _workspace(mutate)
    try:
        assert _recommendation(directory / "project", "controlled_checkout")["recommended_pattern"] != "DIRECT"
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_protocol_hash():
    def mutate(raw):
        raw["protocol_profiles"][0]["source_hash"] = "fabricated-fixture"

    directory = _workspace(mutate)
    try:
        assert _recommendation(directory / "project", "controlled_checkout")["recommended_pattern"] != "DIRECT"
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_confirmation_policy():
    def mutate(raw):
        raw["policy_profile"]["require_confirmation_for"] = []

    directory = _workspace(mutate)
    try:
        assert _recommendation(directory / "project", "controlled_checkout")["recommended_pattern"] != "DIRECT"
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_idempotency_principal():
    from agentnative.transactions.core import transaction_fingerprint

    common = dict(business_id="merchant", environment="SANDBOX", agent_id="agent", provider_id="provider", capability_id="purchase", resource_reference="sku", value=10, currency="USD", input_data={})
    assert transaction_fingerprint(principal_id="principal-one", **common) != transaction_fingerprint(principal_id="principal-two", **common)


def test_idempotency_environment():
    from agentnative.transactions.core import transaction_fingerprint

    common = dict(business_id="merchant", principal_id="principal", agent_id="agent", provider_id="provider", capability_id="purchase", resource_reference="sku", value=10, currency="USD", input_data={})
    assert transaction_fingerprint(environment="SANDBOX", **common) != transaction_fingerprint(environment="PRODUCTION_READ_ONLY", **common)


def _retail_environment(storage=None):
    from agentnative.packs import CoreGuaranteeRegistry, RetailProduct, RetailReferenceEnvironment, RetailVariant

    environment = RetailReferenceEnvironment(business_id="merchant:gate2", core_guarantees=CoreGuaranteeRegistry.for_test(), storage=storage)
    environment.add_product(RetailProduct("prod:gate2", "Gate 2 Product", {"variant:one": RetailVariant("variant:one", {}, 10.0, "USD", 1)}))
    return environment


def test_order_atomicity():
    from concurrent.futures import ThreadPoolExecutor
    from agentnative.persistence import SQLiteStateStore
    from agentnative.transactions import Confirmation

    directory = Path(tempfile.mkdtemp(prefix="gate2-db-"))
    try:
        db = directory / "state.db"
        clock = datetime(2026, 1, 1, tzinfo=timezone.utc)
        _retail_environment(SQLiteStateStore(db))

        def submit(principal, key):
            env = _retail_environment(SQLiteStateStore(db))
            quote = env.create_quote(product_id="prod:gate2", variant_id="variant:one", principal_id=principal, now=clock)
            return env.submit_order(retail_quote=quote, principal_id=principal, agent_id="agent", provider_id="provider", trust_class="VERIFIED", idempotency_key=key, confirmation=Confirmation.create(quote.quote, now=clock), now=clock).status

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda args: submit(*args), (("p1", "k1"), ("p2", "k2"))))
        assert outcomes.count("ORDER_ACCEPTED") == 1
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_inventory_bound():
    from agentnative.persistence import SQLiteStateStore
    from agentnative.transactions import Confirmation
    from agentnative.transactions.core import stable_hash
    from dataclasses import replace

    directory = Path(tempfile.mkdtemp(prefix="gate2-db-"))
    try:
        db = directory / "state.db"
        store = SQLiteStateStore(db)
        env = _retail_environment(store)
        clock = datetime(2026, 1, 1, tzinfo=timezone.utc)
        quote = env.create_quote(product_id="prod:gate2", variant_id="variant:one", principal_id="p1", now=clock)
        first = env.submit_order(retail_quote=quote, principal_id="p1", agent_id="agent", provider_id="provider", trust_class="VERIFIED", idempotency_key="inventory-1", confirmation=Confirmation.create(quote.quote, now=clock), now=clock)
        assert first.status == "ORDER_ACCEPTED"
        second_hash = stable_hash({"second": True})
        store.claim_idempotency("inventory-2", second_hash)
        second = replace(first.order, order_id="order-two", principal_id="p2")
        try:
            store.commit_order(order=second, key="inventory-2", request_hash=second_hash, logical_id="tx-second", receipt=first.receipt, product_id="prod:gate2", variant_id="variant:one", quantity=1, business_id=env.business_id, environment=env.environment.value)
        except Exception as exc:
            assert getattr(exc, "code", "") == "INVENTORY_UNAVAILABLE"
        else:
            raise AssertionError("storage allowed a second order after inventory was exhausted")
        assert store.inventory("prod:gate2", "variant:one") == 0
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_refund_ceiling():
    from dataclasses import replace
    from agentnative.persistence import SQLiteStateStore
    from agentnative.transactions import Confirmation
    from agentnative.transactions.core import stable_hash

    directory = Path(tempfile.mkdtemp(prefix="gate2-refund-"))
    try:
        store = SQLiteStateStore(directory / "state.db")
        env = _retail_environment(store)
        clock = datetime(2026, 1, 1, tzinfo=timezone.utc)
        quote = env.create_quote(product_id="prod:gate2", variant_id="variant:one", principal_id="p", now=clock)
        order = env.submit_order(retail_quote=quote, principal_id="p", agent_id="agent", provider_id="provider", trust_class="VERIFIED", idempotency_key="ceiling-order", confirmation=Confirmation.create(quote.quote, now=clock), now=clock).order
        env.authorize_payment(order_id=order.order_id, principal_id="p", idempotency_key="ceiling-payment")
        order.state = type(order.state).FULFILLED
        store.save_order(order, event_type="FULFILLED")
        request = env.create_return_request(order_id=order.order_id, principal_id="p", reason="test", idempotency_key="ceiling-return")
        env.approve_return(request.return_id)
        env.receive_return(request.return_id)
        refund_request = env.request_refund(return_id=request.return_id, principal_id="p", idempotency_key="ceiling-request")
        first = env.execute_refund(refund_id=refund_request.refund_id, principal_id="p", idempotency_key="ceiling-execute")
        over = replace(first, refund_id="refund-over", amount=1.0)
        try:
            store.commit_refund(refund=over, key="ceiling-over", request_hash=stable_hash({"over": True}), receipt=first.receipt, business_id=env.business_id, environment=env.environment.value)
        except Exception as exc:
            assert getattr(exc, "code", "") == "REFUND_EXCEEDS_ELIGIBLE_VALUE"
        else:
            raise AssertionError("storage accepted an aggregate refund above the captured value")
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_unknown_retry():
    from agentnative.retail_product import simulate_workspace

    result = simulate_workspace(ROOT / "examples" / "retail" / "direct-ready", "lost_response")
    assert result["result"]["first"]["status"] == "UNKNOWN_OUTCOME"
    assert result["result"]["retry"]["status"] == "REPLAYED"
    assert result["result"]["reconciliation"]["response_delivery"] == "REPLAYED"


def test_payment_restart():
    from agentnative.persistence import SQLiteStateStore
    from agentnative.transactions import Confirmation

    directory = Path(tempfile.mkdtemp(prefix="gate2-restart-"))
    try:
        db = directory / "state.db"
        env = _retail_environment(SQLiteStateStore(db))
        quote = env.create_quote(product_id="prod:gate2", variant_id="variant:one", principal_id="p", now=datetime(2026, 1, 1, tzinfo=timezone.utc))
        order = env.submit_order(retail_quote=quote, principal_id="p", agent_id="agent", provider_id="provider", trust_class="VERIFIED", idempotency_key="restart-order", confirmation=Confirmation.create(quote.quote, now=datetime(2026, 1, 1, tzinfo=timezone.utc)), now=datetime(2026, 1, 1, tzinfo=timezone.utc)).order
        payment = env.authorize_payment(order_id=order.order_id, principal_id="p", idempotency_key="restart-payment")
        restarted = _retail_environment(SQLiteStateStore(db))
        assert payment.authorization_id in restarted.payments
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_refund_restart():
    from agentnative.persistence import SQLiteStateStore
    from agentnative.transactions import Confirmation

    directory = Path(tempfile.mkdtemp(prefix="gate2-restart-"))
    try:
        db = directory / "state.db"
        env = _retail_environment(SQLiteStateStore(db))
        clock = datetime(2026, 1, 1, tzinfo=timezone.utc)
        quote = env.create_quote(product_id="prod:gate2", variant_id="variant:one", principal_id="p", now=clock)
        order = env.submit_order(retail_quote=quote, principal_id="p", agent_id="agent", provider_id="provider", trust_class="VERIFIED", idempotency_key="refund-order", confirmation=Confirmation.create(quote.quote, now=clock), now=clock).order
        env.authorize_payment(order_id=order.order_id, principal_id="p", idempotency_key="refund-payment")
        order.state = type(order.state).FULFILLED
        env.storage.save_order(order, event_type="FULFILLED")
        request = env.create_return_request(order_id=order.order_id, principal_id="p", reason="test", idempotency_key="return")
        env.approve_return(request.return_id)
        env.receive_return(request.return_id)
        refund_request = env.request_refund(return_id=request.return_id, principal_id="p", idempotency_key="refund-request")
        refund = env.execute_refund(refund_id=refund_request.refund_id, principal_id="p", idempotency_key="refund-execute")
        restarted = _retail_environment(SQLiteStateStore(db))
        assert restarted.refunds[refund.refund_id].state.value == "REFUNDED"
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def test_delegation_expiry():
    from agentnative.retail_product import simulate_workspace

    result = simulate_workspace(ROOT / "examples" / "retail" / "direct-ready", "expired_delegation")
    assert result["result"]["status"] == "DENIED"
    assert result["result"]["findings"] == ["EXPIRED_DELEGATION"]


def test_output_redaction():
    from agentnative.reporting.output import UnsafeReportError, validate_output

    try:
        validate_output("token=FAKE_GATE2_SECRET_123456789")
    except UnsafeReportError:
        return
    raise AssertionError("secret-bearing output was not rejected")


def _manifest_fixture():
    from verify_phase3b_evidence import _canonical_output_digest, digest

    commits = subprocess.run(["git", "rev-list", "--max-count=5", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    assert len(commits) >= 4
    source, alternate, reviewed, evidence = commits[3], commits[2], commits[1], commits[0]
    files = [
        "V3/PHASE_3B_PRODUCTIZATION_BUILD_REPORT.md", "V3/REQUIREMENTS_TRACEABILITY.md", "pyproject.toml",
        "audit_v3/phase3b_closure/rerun_01/findings.json", "audit_v3/phase3b_closure/rerun_01/environment.json",
        "audit_v3/phase3b_closure/rerun_01/commands.log", "audit_v3/phase3b_closure/rerun_01/INDEPENDENT_REVIEW_RESULT.md", "README.md",
    ]
    roles = ("closure_build_report", "requirements_traceability", "wheel", "structured_test_result", "phase2b_mutation_result", "phase2c_mutation_result", "phase3_mutation_result", "wheel_smoke_result")
    artifacts = []
    for role, relative in zip(roles, files):
        path = ROOT / relative
        artifacts.append({"role": role, "path": relative, "sha256": digest(path), "byte_size": path.stat().st_size, "media_type": "text/plain", "producing_command": "gate2-test-fixture"})
    commands = []
    for command_id, role in zip(("baseline_tests", "evidence_tamper_matrix", "phase3_mutations", "wheel_smoke", "manifest_generation", "manifest_local_verification"), roles):
        output = {"stdout": "", "stderr": ""}
        commands.append({"id": command_id, "argv": ["gate2-test", command_id], "exit_code": 0, "started_at": "2026-09-28T12:00:00Z", "ended_at": "2026-09-28T12:00:01Z", "environment": {"python": "test"}, "output": output, "output_sha256": _canonical_output_digest(output), "artifact_refs": [role], "result_counts": {}})
    manifest = {"manifest_version": "phase3b-gate2-1", "status": "BUILDER_EVIDENCE_ONLY", "repository": "revanthpp/agent-native", "source_commit_sha": source, "reviewed_commit_sha": reviewed, "evidence_commit_sha": evidence, "generated_at": "2026-09-28T12:00:00Z", "generator_version": "test", "ci": {"repository": "revanthpp/agent-native", "run_id": 123, "run_attempt": 1, "workflow_path": ".github/workflows/ci.yml", "event": "push", "head_sha": reviewed, "status": "completed", "conclusion": "success", "created_at": "2026-09-28T11:59:00Z", "started_at": "2026-09-28T12:00:00Z", "completed_at": "2026-09-28T12:01:00Z", "url": "https://github.com/revanthpp/agent-native/actions/runs/123", "uploaded_artifact": {"id": 456, "name": "gate2", "digest": "a" * 64, "url": "https://github.com/revanthpp/agent-native/actions/artifacts/456"}}, "artifacts": artifacts, "commands": commands, "results": {"counts": {"passed": 1}}}
    return manifest, source, alternate, reviewed, evidence


def _manifest_path(manifest):
    handle = tempfile.NamedTemporaryFile(prefix="gate2-manifest-", suffix=".json", dir=ROOT, delete=False, mode="w", encoding="utf-8")
    json.dump(manifest, handle, indent=2)
    handle.close()
    return Path(handle.name)


def test_evidence_missing():
    from verify_phase3b_evidence import verify_manifest

    manifest, *_ = _manifest_fixture()
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item["role"] != "wheel"]
    path = _manifest_path(manifest)
    try:
        assert verify_manifest(path, repo_root=ROOT, offline=True)["status"] == "EVIDENCE_INVALID"
    finally:
        path.unlink(missing_ok=True)


def test_provenance_sha():
    from verify_phase3b_evidence import verify_manifest

    manifest, source, _alternate, reviewed, evidence = _manifest_fixture()
    manifest["source_commit_sha"] = "1" * 40
    path = _manifest_path(manifest)
    try:
        assert verify_manifest(path, repo_root=ROOT, offline=True)["status"] == "EVIDENCE_INVALID"
    finally:
        path.unlink(missing_ok=True)


class _FakeGitHub:
    def __init__(self, manifest):
        self.manifest = manifest

    def run(self, repository, run_id):
        ci = self.manifest["ci"]
        return {"id": run_id, "repository": {"full_name": repository}, "head_sha": ci["head_sha"], "status": ci["status"], "conclusion": ci["conclusion"], "path": ci["workflow_path"], "event": ci["event"], "html_url": ci["url"], "created_at": ci["created_at"], "run_started_at": ci["started_at"], "updated_at": ci["completed_at"]}

    def artifacts(self, repository, run_id):
        ci = self.manifest["ci"]
        return {"artifacts": [{"id": ci["uploaded_artifact"]["id"], "digest": "sha256:" + ci["uploaded_artifact"]["digest"], "workflow_run": {}}]}


def test_ci_binding():
    from verify_phase3b_evidence import verify_manifest

    manifest, source, alternate, reviewed, evidence = _manifest_fixture()
    fake = _FakeGitHub(copy.deepcopy(manifest))
    manifest["reviewed_commit_sha"] = alternate
    manifest["ci"]["head_sha"] = alternate
    path = _manifest_path(manifest)
    try:
        assert verify_manifest(path, repo_root=ROOT, offline=False, github=fake)["status"] == "EVIDENCE_INVALID"
    finally:
        path.unlink(missing_ok=True)


def test_wheel_isolation():
    from run_phase3b_wheel_smoke import clean_environment

    environment = clean_environment()
    assert "PYTHONPATH" not in environment
    assert "PYTHONHOME" not in environment


TESTS = {
    "M3-UNKNOWN-SCENARIO": test_unknown_scenario,
    "M3-CAPABILITY-GATE": test_capability_gate,
    "M3-DECLARED-READINESS": test_declared_readiness,
    "M3-EVIDENCE-STATE": test_evidence_state,
    "M3-PROTOCOL-HASH": test_protocol_hash,
    "M3-CONFIRMATION-POLICY": test_confirmation_policy,
    "M3-IDEMPOTENCY-PRINCIPAL": test_idempotency_principal,
    "M3-IDEMPOTENCY-ENV": test_idempotency_environment,
    "M3-ORDER-ATOMICITY": test_order_atomicity,
    "M3-INVENTORY-BOUND": test_inventory_bound,
    "M3-REFUND-CEILING": test_refund_ceiling,
    "M3-UNKNOWN-RETRY": test_unknown_retry,
    "M3-PAYMENT-RESTART": test_payment_restart,
    "M3-REFUND-RESTART": test_refund_restart,
    "M3-DELEGATION-EXPIRY": test_delegation_expiry,
    "M3-OUTPUT-REDACTION": test_output_redaction,
    "M3-EVIDENCE-MISSING": test_evidence_missing,
    "M3-PROVENANCE-SHA": test_provenance_sha,
    "M3-CI-BINDING": test_ci_binding,
    "M3-WHEEL-ISOLATION": test_wheel_isolation,
}


def main() -> int:
    names = list(TESTS) if len(sys.argv) == 1 or sys.argv[1] == "--baseline" else [sys.argv[1]]
    for name in names:
        try:
            TESTS[name]()
        except Exception as exc:
            print(json.dumps({"status": "MUTANT_DETECTED", "detecting_test": name, "error": f"{type(exc).__name__}: {exc}"}))
            return 1
    print(json.dumps({"status": "BASELINE_PASS", "tests": names}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
