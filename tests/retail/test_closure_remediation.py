from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from agentnative.packs import CoreGuaranteeRegistry, RetailProduct, RetailReferenceEnvironment, RetailVariant
from agentnative.persistence import SQLiteStateStore
from agentnative.retail_product import RetailProductError, SCENARIO_REGISTRY, simulate_workspace, validate_workspace
from agentnative.transactions import Confirmation


ROOT = Path(__file__).resolve().parents[2]
CLOCK = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _environment(storage: SQLiteStateStore | None = None) -> RetailReferenceEnvironment:
    environment = RetailReferenceEnvironment(business_id="merchant:closure", core_guarantees=CoreGuaranteeRegistry.for_test(), storage=storage)
    environment.add_product(RetailProduct("prod:closure", "Closure Product", {"variant:one": RetailVariant("variant:one", {}, 10.0, "USD", 1)}))
    return environment


class ClosureRemediationTests(unittest.TestCase):
    def test_registry_is_complete_and_unknown_scenarios_fail_closed(self) -> None:
        self.assertEqual(len(SCENARIO_REGISTRY), 16)
        for item in SCENARIO_REGISTRY:
            result = simulate_workspace(ROOT / "examples" / "retail" / "direct-ready", item.scenario_id)
            self.assertEqual(result["contract"]["expected_status"], result["contract"]["observed_status"], item.scenario_id)
        with self.assertRaises(RetailProductError) as error:
            simulate_workspace(ROOT / "examples" / "retail" / "direct-ready", "not-a-scenario")
        self.assertEqual(error.exception.code, "UNKNOWN_SCENARIO")

    def test_strict_workspace_validation_reports_paths_and_rejects_readiness_self_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "project.yaml").write_text("project_id: bad\nproject_version: '9.0'\n", encoding="utf-8")
            with self.assertRaises(RetailProductError) as error:
                validate_workspace(path)
            self.assertEqual(error.exception.code, "UNSUPPORTED_WORKSPACE_VERSION")
            self.assertTrue(error.exception.errors[0]["json_path"])

    def test_init_refuses_overwrite_and_force_keeps_backup(self) -> None:
        from agentnative.retail_product import init_workspace

        with tempfile.TemporaryDirectory() as directory:
            init_workspace(directory, project_id="one", example="direct")
            with self.assertRaises(RetailProductError) as error:
                init_workspace(directory, project_id="two", example="platform")
            self.assertEqual(error.exception.code, "WORKSPACE_EXISTS")
            init_workspace(directory, project_id="two", example="platform", force=True)
            self.assertTrue(Path(directory, "project.yaml.bak").exists())

    def test_storage_restart_reloads_payment_return_refund_and_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteStateStore(Path(directory) / "retail.db")
            environment = _environment(store)
            quote = environment.create_quote(product_id="prod:closure", variant_id="variant:one", principal_id="principal:closure", now=CLOCK)
            accepted = environment.submit_order(retail_quote=quote, principal_id="principal:closure", agent_id="agent:closure", provider_id="provider:closure", trust_class="VERIFIED", idempotency_key="order:closure", confirmation=Confirmation.create(quote.quote, now=CLOCK), now=CLOCK)
            payment = environment.authorize_payment(order_id=accepted.order.order_id, principal_id="principal:closure", idempotency_key="payment:closure")
            environment.orders[accepted.order.order_id].state = __import__("agentnative.packs", fromlist=["RetailJourneyState"]).RetailJourneyState.FULFILLED
            store.save_order(environment.orders[accepted.order.order_id], event_type="FULFILLED")
            return_request = environment.create_return_request(order_id=accepted.order.order_id, principal_id="principal:closure", reason="test", idempotency_key="return:closure")
            environment.approve_return(return_request.return_id)
            environment.receive_return(return_request.return_id)
            refund_request = environment.request_refund(return_id=return_request.return_id, principal_id="principal:closure", idempotency_key="refund-request:closure")
            refund = environment.execute_refund(refund_id=refund_request.refund_id, principal_id="principal:closure", idempotency_key="refund:closure")
            self.assertEqual(payment.state.value, "AUTHORIZED")
            self.assertEqual(refund.state.value, "REFUNDED")
            restarted = _environment(SQLiteStateStore(Path(directory) / "retail.db"))
            self.assertIn(payment.authorization_id, restarted.payments)
            self.assertIn(return_request.return_id, restarted.returns)
            self.assertEqual(restarted.refunds[refund.refund_id].state.value, "REFUNDED")

    def test_atomic_inventory_allows_one_of_two_concurrent_distinct_purchases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "retail.db"
            first = _environment(SQLiteStateStore(db))
            quote = first.create_quote(product_id="prod:closure", variant_id="variant:one", principal_id="principal:one", now=CLOCK)

            def submit(key: str, principal: str):
                environment = _environment(SQLiteStateStore(db))
                local_quote = environment.create_quote(product_id="prod:closure", variant_id="variant:one", principal_id=principal, now=CLOCK)
                return environment.submit_order(retail_quote=local_quote, principal_id=principal, agent_id="agent:closure", provider_id="provider:closure", trust_class="VERIFIED", idempotency_key=key, confirmation=Confirmation.create(local_quote.quote, now=CLOCK), now=CLOCK)

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda args: submit(*args), [("order:one", "principal:one"), ("order:two", "principal:two")]))
            self.assertEqual(sum(result.status == "ORDER_ACCEPTED" for result in results), 1)
            self.assertEqual(SQLiteStateStore(db).inventory("prod:closure", "variant:one"), 0)

    def test_clean_cli_unknown_scenario_is_structured_and_nonzero(self) -> None:
        environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        completed = subprocess.run([str(ROOT / ".venv/bin/python"), "-m", "agentnative", "retail", "simulate", str(ROOT / "examples/retail/direct-ready"), "--scenario", "bogus"], cwd=ROOT, env=environment, capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stderr)["error_code"], "UNKNOWN_SCENARIO")


if __name__ == "__main__":
    unittest.main()
