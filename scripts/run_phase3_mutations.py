"""Run the 20 required Phase 3 Gate 2 mutants in isolated source copies.

Unlike the retired harness, this runner never substitutes a Boolean for a
mutant. Every case edits one production source pattern, records the diff, and
runs a named behavioral oracle in a clean subprocess.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Mutant:
    mutation_id: str
    file: str
    needle: str
    replacement: str
    detecting_test: str
    control: str


def _mutants() -> tuple[Mutant, ...]:
    return (
        Mutant("M3-UNKNOWN-SCENARIO", "src/agentnative/retail_product.py", "if scenario_id not in SCENARIO_BY_ID:\n        raise RetailProductError(f\"unknown Retail scenario: {scenario}\", code=\"UNKNOWN_SCENARIO\", json_path=\"$.scenario\", remediation=\"Use one of: \" + \", \".join(item.scenario_id for item in SCENARIO_REGISTRY))", "if scenario_id not in SCENARIO_BY_ID:\n        scenario_id = \"positive\"", "test_unknown_scenario", "unknown scenarios fail closed"),
        Mutant("M3-CAPABILITY-GATE", "src/agentnative/retail_product.py", "if not record:", "if False:", "test_capability_gate", "missing journey capabilities block direct activation"),
        Mutant("M3-DECLARED-READINESS", "src/agentnative/retail_product.py", "if state not in {CapabilityState.TESTED.value, CapabilityState.EXECUTABLE_IN_SIMULATION.value, CapabilityState.EXECUTABLE_IN_SANDBOX.value}:", "if state not in {CapabilityState.DECLARED.value, CapabilityState.TESTED.value, CapabilityState.EXECUTABLE_IN_SIMULATION.value, CapabilityState.EXECUTABLE_IN_SANDBOX.value}:", "test_declared_readiness", "declared capability metadata is not executable evidence"),
        Mutant("M3-EVIDENCE-STATE", "src/agentnative/retail_product.py", "verified_refs = [ref for ref in refs if evidence.get(ref) and evidence[ref].get(\"state\") == \"KNOWN_TRUE\" and evidence[ref].get(\"source_type\") in {\"test_result\", \"connector_evidence\", \"reference_fixture\", \"expert_review\"}]", "verified_refs = [ref for ref in refs if evidence.get(ref) and evidence[ref].get(\"source_type\") in {\"test_result\", \"connector_evidence\", \"reference_fixture\", \"expert_review\"}]", "test_evidence_state", "stale or conflicting evidence cannot promote a journey"),
        Mutant("M3-PROTOCOL-HASH", "src/agentnative/retail_product.py", "verified = bool(expected and supplied == expected)", "verified = bool(expected)", "test_protocol_hash", "protocol readiness compares the expected fixture hash"),
        Mutant("M3-CONFIRMATION-POLICY", "src/agentnative/retail_product.py", "if \"submit_order\" not in required_confirmation and \"execute_refund\" not in required_confirmation:", "if False:", "test_confirmation_policy", "value-changing journeys require confirmation policy"),
        Mutant("M3-IDEMPOTENCY-PRINCIPAL", "src/agentnative/transactions/core.py", "\"principal_id\": _identity_text(principal_id),", "\"principal_id\": \"\",", "test_idempotency_principal", "transaction identity binds the principal"),
        Mutant("M3-IDEMPOTENCY-ENV", "src/agentnative/transactions/core.py", "\"environment\": environment_value,", "\"environment\": \"\",", "test_idempotency_environment", "transaction identity binds the environment"),
        Mutant("M3-ORDER-ATOMICITY", "src/agentnative/packs/retail.py", "self.storage.commit_order(order=order, key=idempotency_key, request_hash=request_hash, logical_id=logical_id, receipt=receipt, product_id=retail_quote.product_id, variant_id=retail_quote.variant_id, quantity=quantity, business_id=self.business_id, environment=self.environment.value)", "self.storage.record_idempotency(idempotency_key, request_hash, \"SUCCEEDED\", order_id, logical_id=logical_id)", "test_order_atomicity", "inventory, order, idempotency, receipt, and event commit atomically"),
        Mutant("M3-INVENTORY-BOUND", "src/agentnative/persistence.py", "quantity >= ?\"", "quantity >= ? OR 1=1\"", "test_inventory_bound", "inventory decrement is conditionally bounded"),
        Mutant("M3-REFUND-CEILING", "src/agentnative/persistence.py", "if refund_payload.get(\"amount\", 0) <= 0 or prior + float(refund_payload[\"amount\"]) > order_amount:", "if refund_payload.get(\"amount\", 0) <= 0:", "test_refund_ceiling", "aggregate refunds cannot exceed captured value"),
        Mutant("M3-UNKNOWN-RETRY", "src/agentnative/packs/retail.py", "if existing is not None:\n                if existing.status != \"SUCCEEDED\":", "if False:\n                if existing.status != \"SUCCEEDED\":", "test_unknown_retry", "unknown outcomes reconcile and replay instead of blind retry"),
        Mutant("M3-PAYMENT-RESTART", "src/agentnative/packs/retail.py", "self.payments.update({item.authorization_id: item for item in (PaymentAuthorization.from_dict(raw) for raw in self.storage.load_entities(\"payment\"))})", "self.payments.update({})", "test_payment_restart", "payment authorization state survives restart"),
        Mutant("M3-REFUND-RESTART", "src/agentnative/packs/retail.py", "self.refunds.update({item.refund_id: item for item in (RetailRefund.from_dict(raw) for raw in self.storage.load_entities(\"refund\"))})", "self.refunds.update({})", "test_refund_restart", "refund state survives restart"),
        Mutant("M3-DELEGATION-EXPIRY", "src/agentnative/packs/retail.py", "if delegation_expires_at is not None and delegation_expires_at <= clock:", "if False:", "test_delegation_expiry", "expired delegations are denied at the injected clock"),
        Mutant("M3-OUTPUT-REDACTION", "src/agentnative/reporting/output.py", "if detector.detect_text(output):", "if False:", "test_output_redaction", "secret-bearing output is blocked before publication"),
        Mutant("M3-EVIDENCE-MISSING", "scripts/verify_phase3b_evidence.py", "if role not in seen_roles:", "if False:", "test_evidence_missing", "the verifier requires every evidence role"),
        Mutant("M3-PROVENANCE-SHA", "scripts/verify_phase3b_evidence.py", "values = {field: manifest.get(field) for field in (\"source_commit_sha\", \"reviewed_commit_sha\", \"evidence_commit_sha\")}\n    if any(not isinstance(value, str) or not SHA_RE.fullmatch(value) for value in values.values()):", "return\n    values = {field: manifest.get(field) for field in (\"source_commit_sha\", \"reviewed_commit_sha\", \"evidence_commit_sha\")}\n    if any(not isinstance(value, str) or not SHA_RE.fullmatch(value) for value in values.values()):", "test_provenance_sha", "provenance commits must have real existence and ancestry"),
        Mutant("M3-CI-BINDING", "scripts/verify_phase3b_evidence.py", "if ci.get(field) != actual:", "if False:", "test_ci_binding", "CI run identity binds to the claimed reviewed commit"),
        Mutant("M3-WHEEL-ISOLATION", "scripts/run_phase3b_wheel_smoke.py", "environment.pop(key, None)", "environment[\"PYTHONPATH\"] = str(Path(__file__).resolve().parents[1] / \"src\")", "test_wheel_isolation", "wheel smoke clears source-checkout import paths"),
    )


def _copy_isolated(root: Path, destination: Path) -> None:
    ignored = shutil.ignore_patterns(".venv", "dist", "__pycache__", ".pytest_cache", ".ruff_cache")
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("src", "scripts", "examples", "V3", "audit_v3", "tests"):
        source = root / name
        if source.exists():
            shutil.copytree(source, destination / name, ignore=ignored)
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(root / name, destination / name)
    if (root / ".git").exists():
        shutil.copytree(root / ".git", destination / ".git", ignore=shutil.ignore_patterns("*.lock"))


def _apply_mutation(path: Path, mutant: Mutant) -> str:
    original = path.read_text(encoding="utf-8")
    count = original.count(mutant.needle)
    if count != 1:
        raise ValueError(f"target pattern count is {count}, expected exactly one")
    mutated = original.replace(mutant.needle, mutant.replacement, 1)
    path.write_text(mutated, encoding="utf-8")
    diff = "".join(difflib.unified_diff(original.splitlines(True), mutated.splitlines(True), fromfile=str(path), tofile=str(path)))
    return diff


def _run_mutant(mutant: Mutant) -> dict[str, object]:
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"agentnative-{mutant.mutation_id.lower()}-") as temporary:
        isolated = Path(temporary) / "repo"
        _copy_isolated(ROOT, isolated)
        target = isolated / mutant.file
        try:
            original = target.read_text(encoding="utf-8")
            target_hash = hashlib.sha256(mutant.needle.encode("utf-8")).hexdigest()
            diff = _apply_mutation(target, mutant)
        except Exception as exc:
            return {"mutation_id": mutant.mutation_id, "file": mutant.file, "target_hash": target_hash if "target_hash" in locals() else None, "applied_diff": "", "test_command": [], "detecting_test": mutant.detecting_test, "exit_code": None, "classification": "INVALID_MUTANT", "duration_seconds": round(time.monotonic() - started, 6), "output_sha256": "", "error": str(exc), "control": mutant.control}
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(isolated / "src")
        environment["AGENTNATIVE_REPO_ROOT"] = str(isolated)
        command = [sys.executable, str(isolated / "scripts" / "phase3_gate2_mutant_tests.py"), mutant.mutation_id]
        try:
            completed = subprocess.run(command, cwd=isolated, env=environment, text=True, capture_output=True, check=False, timeout=60)
            combined = completed.stdout + "\n" + completed.stderr
            detected = completed.returncode != 0 and "\"status\": \"MUTANT_DETECTED\"" in combined
            classification = "KILLED" if detected else ("SURVIVED" if completed.returncode == 0 else "INVALID_MUTANT")
            return {"mutation_id": mutant.mutation_id, "file": mutant.file, "target_hash": target_hash, "applied_diff": diff, "test_command": command, "detecting_test": mutant.detecting_test, "exit_code": completed.returncode, "classification": classification, "duration_seconds": round(time.monotonic() - started, 6), "output_sha256": hashlib.sha256(combined.encode()).hexdigest(), "output_tail": combined[-4000:], "control": mutant.control}
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") + "\n" + (exc.stderr or "")
            return {"mutation_id": mutant.mutation_id, "file": mutant.file, "target_hash": target_hash, "applied_diff": diff, "test_command": command, "detecting_test": mutant.detecting_test, "exit_code": None, "classification": "TIMED_OUT", "duration_seconds": round(time.monotonic() - started, 6), "output_sha256": hashlib.sha256(output.encode()).hexdigest(), "output_tail": output[-4000:], "control": mutant.control}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    baseline_command = [sys.executable, str(ROOT / "scripts" / "phase3_gate2_mutant_tests.py"), "--baseline"]
    baseline_env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), AGENTNATIVE_REPO_ROOT=str(ROOT))
    baseline = subprocess.run(baseline_command, cwd=ROOT, env=baseline_env, text=True, capture_output=True, check=False, timeout=120)
    if baseline.returncode != 0:
        print(baseline.stdout)
        print(baseline.stderr, file=sys.stderr)
        return 1
    results = [_run_mutant(mutant) for mutant in _mutants()]
    counts = {name.lower(): sum(item["classification"] == name for item in results) for name in ("KILLED", "SURVIVED", "INVALID_MUTANT", "TIMED_OUT")}
    counts["excluded"] = 0
    payload = {"schema_version": "phase3b-mutation-results-1", "status": "PASS" if counts["killed"] == 20 and counts["survived"] == 0 and counts["invalid_mutant"] == 0 and counts["timed_out"] == 0 else "FAIL", "counts": {"total": len(results), **counts}, "mutation_score": counts["killed"] / (counts["killed"] + counts["survived"]) if counts["killed"] + counts["survived"] else 0.0, "baseline": {"exit_code": baseline.returncode, "output_sha256": hashlib.sha256((baseline.stdout + "\n" + baseline.stderr).encode()).hexdigest()}, "mutants": results}
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
