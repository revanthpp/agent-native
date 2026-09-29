from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from agentnative.transactions import IdempotencyRecord, IdempotencyStatus, TransactionSafetyError


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if value else None


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


class SQLiteStateStore:
    """Durable, dependency-free reference store for Retail restart tests.

    Schema migrations are forward-only.  The store is intentionally small but
    persists every value-changing Retail entity rather than rebuilding it from
    process memory after a restart.
    """

    schema_version = 2

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._session() as db:
            existing = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'").fetchone()
            if existing:
                row = db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
                if row and int(row[0]) > self.schema_version:
                    raise TransactionSafetyError("UNSUPPORTED_STORE_SCHEMA", "state store was created by a newer version")
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS idempotency (
                    idempotency_key TEXT PRIMARY KEY, request_hash TEXT NOT NULL, status TEXT NOT NULL,
                    result_reference TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    scenario_id TEXT, owner_execution_id TEXT, error_reference TEXT, expires_at TEXT,
                    logical_transaction_id TEXT, receipt_reference TEXT
                );
                CREATE TABLE IF NOT EXISTS receipts (receipt_id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, payload TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS order_events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL, state TEXT NOT NULL, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS confirmations (confirmation_id TEXT PRIMARY KEY, logical_transaction_id TEXT NOT NULL UNIQUE, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reconciliation (reconciliation_id TEXT PRIMARY KEY, logical_transaction_id TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS retail_entities (
                    entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, tenant_id TEXT NOT NULL DEFAULT '',
                    business_id TEXT NOT NULL DEFAULT '', environment TEXT NOT NULL DEFAULT 'SANDBOX',
                    schema_version INTEGER NOT NULL DEFAULT 2, version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY(entity_type, entity_id)
                );
                CREATE TABLE IF NOT EXISTS inventory (
                    product_id TEXT NOT NULL, variant_id TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity >= 0),
                    resource_version TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(product_id, variant_id)
                );
                CREATE TABLE IF NOT EXISTS pack_state (pack_id TEXT PRIMARY KEY, lifecycle_state TEXT NOT NULL, content_hash TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS evidence (observation_hash TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, pack_id TEXT NOT NULL, field_name TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attestations (attestation_id TEXT PRIMARY KEY, content_hash TEXT NOT NULL, revoked_at TEXT, payload TEXT NOT NULL);
                INSERT OR IGNORE INTO metadata(key, value) VALUES ('schema_version', '2');
                """
            )
            db.execute("UPDATE metadata SET value = ? WHERE key = 'schema_version' AND CAST(value AS INTEGER) < ?", (str(self.schema_version), self.schema_version))

    def schema(self) -> dict[str, str]:
        with self._session() as db:
            return {row["key"]: row["value"] for row in db.execute("SELECT key, value FROM metadata")}

    def claim_idempotency(self, key: str, request_hash: str, *, scenario_id: str | None = None) -> IdempotencyRecord | None:
        now = datetime.now(timezone.utc)
        with self._session() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM idempotency WHERE idempotency_key = ?", (key,)).fetchone()
            if row is None:
                logical_id = f"tx-{request_hash[:24]}"
                db.execute("INSERT INTO idempotency(idempotency_key, request_hash, status, created_at, updated_at, scenario_id, owner_execution_id, logical_transaction_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (key, request_hash, IdempotencyStatus.PENDING.value, _iso(now), _iso(now), scenario_id, request_hash[:16], logical_id))
                db.commit()
                return None
            if row["request_hash"] != request_hash:
                db.rollback()
                raise TransactionSafetyError("IDEMPOTENCY_KEY_REUSE", "idempotency key was reused for a different request")
            db.commit()
            return self._record(row)

    def record_idempotency(self, key: str, request_hash: str, status: str, result_reference: str | None, *, error_reference: str | None = None, logical_id: str | None = None) -> IdempotencyRecord:
        now = datetime.now(timezone.utc)
        with self._session() as db:
            row = db.execute("SELECT * FROM idempotency WHERE idempotency_key = ?", (key,)).fetchone()
            if row is None:
                db.execute("INSERT INTO idempotency(idempotency_key, request_hash, status, result_reference, created_at, updated_at, error_reference, logical_transaction_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (key, request_hash, status, result_reference, _iso(now), _iso(now), error_reference, logical_id or f"tx-{request_hash[:24]}"))
            else:
                db.execute("UPDATE idempotency SET status = ?, result_reference = ?, updated_at = ?, error_reference = ?, logical_transaction_id = COALESCE(?, logical_transaction_id) WHERE idempotency_key = ? AND request_hash = ?", (status, result_reference, _iso(now), error_reference, logical_id, key, request_hash))
            saved = db.execute("SELECT * FROM idempotency WHERE idempotency_key = ?", (key,)).fetchone()
        return self._record(saved)

    def _record(self, row: sqlite3.Row) -> IdempotencyRecord:
        return IdempotencyRecord(row["idempotency_key"], row["request_hash"], row["status"], row["result_reference"], _datetime(row["created_at"]) or datetime.now(timezone.utc), _datetime(row["updated_at"]) or datetime.now(timezone.utc), row["scenario_id"], row["owner_execution_id"], row["error_reference"], _datetime(row["expires_at"]), row["logical_transaction_id"], row["receipt_reference"])

    def attach_receipt(self, key: str, request_hash: str, receipt: Any) -> None:
        payload = receipt.to_dict() if hasattr(receipt, "to_dict") else dict(receipt)
        with self._session() as db:
            db.execute("INSERT OR REPLACE INTO receipts(receipt_id, request_hash, payload) VALUES (?, ?, ?)", (payload["receipt_id"], request_hash, json.dumps(payload, sort_keys=True)))
            db.execute("UPDATE idempotency SET receipt_reference = ? WHERE idempotency_key = ? AND request_hash = ?", (payload["receipt_id"], key, request_hash))

    def get_receipt(self, key: str, request_hash: str) -> dict[str, Any] | None:
        with self._session() as db:
            row = db.execute("SELECT r.payload FROM receipts r JOIN idempotency i ON i.receipt_reference = r.receipt_id WHERE i.idempotency_key = ? AND i.request_hash = ?", (key, request_hash)).fetchone()
        return json.loads(row["payload"]) if row else None

    def save_order(self, order: Any, *, event_type: str = "ORDER_STATE") -> None:
        payload = order.to_dict() if hasattr(order, "to_dict") else dict(order)
        with self._session() as db:
            current = db.execute("SELECT version FROM orders WHERE order_id = ?", (payload["order_id"],)).fetchone()
            version = int(current["version"] + 1) if current else 1
            db.execute("INSERT OR REPLACE INTO orders(order_id, payload, version) VALUES (?, ?, ?)", (payload["order_id"], json.dumps(payload, sort_keys=True), version))
            db.execute("INSERT INTO order_events(order_id, state, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?)", (payload["order_id"], payload.get("state", ""), event_type, json.dumps(payload, sort_keys=True), _iso(datetime.now(timezone.utc))))

    def transition_order(self, order_id: str, *, expected_states: set[str], new_state: str) -> bool:
        with self._session() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload, version FROM orders WHERE order_id = ?", (order_id,)).fetchone()
            if not row:
                db.rollback()
                return False
            payload = json.loads(row["payload"])
            if payload.get("state") not in expected_states:
                db.rollback()
                return False
            payload["state"] = new_state
            now = _iso(datetime.now(timezone.utc))
            db.execute("UPDATE orders SET payload = ?, version = ? WHERE order_id = ?", (json.dumps(payload, sort_keys=True), int(row["version"]) + 1, order_id))
            db.execute("INSERT INTO order_events(order_id, state, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?)", (order_id, new_state, "ORDER_STATE", json.dumps(payload, sort_keys=True), now))
            db.execute("UPDATE retail_entities SET payload = ?, version = ?, updated_at = ? WHERE entity_type = 'order' AND entity_id = ?", (json.dumps(payload, sort_keys=True), int(row["version"]) + 1, now, order_id))
            db.commit()
            return True

    def commit_order(self, *, order: Any, key: str, request_hash: str, logical_id: str, receipt: Any, product_id: str, variant_id: str, quantity: int, tenant_id: str = "", business_id: str = "", environment: str = "SANDBOX") -> None:
        """Commit inventory, idempotency, order, receipt, and event atomically."""
        order_payload = order.to_dict() if hasattr(order, "to_dict") else dict(order)
        receipt_payload = receipt.to_dict() if hasattr(receipt, "to_dict") else dict(receipt)
        now = _iso(datetime.now(timezone.utc))
        with self._session() as db:
            db.execute("BEGIN IMMEDIATE")
            updated = db.execute("UPDATE inventory SET quantity = quantity - ?, resource_version = CAST(CAST(resource_version AS INTEGER) + 1 AS TEXT), updated_at = ? WHERE product_id = ? AND variant_id = ? AND quantity >= ?", (quantity, now, product_id, variant_id, quantity))
            if updated.rowcount != 1:
                db.rollback()
                raise TransactionSafetyError("INVENTORY_UNAVAILABLE", "inventory was lost before atomic commit")
            current = db.execute("SELECT version FROM orders WHERE order_id = ?", (order_payload["order_id"],)).fetchone()
            version = int(current["version"] + 1) if current else 1
            db.execute("INSERT OR REPLACE INTO orders(order_id, payload, version) VALUES (?, ?, ?)", (order_payload["order_id"], json.dumps(order_payload, sort_keys=True), version))
            db.execute("INSERT INTO order_events(order_id, state, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?)", (order_payload["order_id"], order_payload.get("state", ""), "ORDER_ACCEPTED", json.dumps(order_payload, sort_keys=True), now))
            db.execute("UPDATE idempotency SET status = ?, result_reference = ?, updated_at = ?, logical_transaction_id = ? WHERE idempotency_key = ? AND request_hash = ?", ("SUCCEEDED", order_payload["order_id"], now, logical_id, key, request_hash))
            db.execute("INSERT OR REPLACE INTO receipts(receipt_id, request_hash, payload) VALUES (?, ?, ?)", (receipt_payload["receipt_id"], request_hash, json.dumps(receipt_payload, sort_keys=True)))
            db.execute("UPDATE idempotency SET receipt_reference = ? WHERE idempotency_key = ? AND request_hash = ?", (receipt_payload["receipt_id"], key, request_hash))
            db.execute("INSERT OR REPLACE INTO retail_entities(entity_type, entity_id, tenant_id, business_id, environment, schema_version, version, created_at, updated_at, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("order", order_payload["order_id"], tenant_id, business_id, environment, self.schema_version, version, now, now, json.dumps(order_payload, sort_keys=True)))
            db.commit()

    def load_orders(self) -> list[dict[str, Any]]:
        with self._session() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM orders ORDER BY order_id")]

    def seed_inventory(self, product_id: str, variant_id: str, quantity: int, resource_version: str = "1") -> None:
        if quantity < 0:
            raise ValueError("inventory cannot be negative")
        with self._session() as db:
            db.execute("INSERT OR IGNORE INTO inventory(product_id, variant_id, quantity, resource_version, updated_at) VALUES (?, ?, ?, ?, ?)", (product_id, variant_id, quantity, resource_version, _iso(datetime.now(timezone.utc))))

    def inventory(self, product_id: str, variant_id: str) -> int | None:
        with self._session() as db:
            row = db.execute("SELECT quantity FROM inventory WHERE product_id = ? AND variant_id = ?", (product_id, variant_id)).fetchone()
        return int(row["quantity"]) if row else None

    def save_entity(self, entity_type: str, entity: Any, *, entity_id: str, tenant_id: str = "", business_id: str = "", environment: str = "SANDBOX") -> None:
        payload = entity.to_dict() if hasattr(entity, "to_dict") else dict(entity)
        now = _iso(datetime.now(timezone.utc))
        with self._session() as db:
            current = db.execute("SELECT version, created_at FROM retail_entities WHERE entity_type = ? AND entity_id = ?", (entity_type, entity_id)).fetchone()
            version = int(current["version"] + 1) if current else 1
            db.execute("INSERT OR REPLACE INTO retail_entities(entity_type, entity_id, tenant_id, business_id, environment, schema_version, version, created_at, updated_at, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (entity_type, entity_id, tenant_id, business_id, environment, self.schema_version, version, current["created_at"] if current else now, now, json.dumps(payload, sort_keys=True)))

    def load_entities(self, entity_type: str) -> list[dict[str, Any]]:
        with self._session() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM retail_entities WHERE entity_type = ? ORDER BY entity_id", (entity_type,))]

    def commit_refund(self, *, refund: Any, key: str, request_hash: str, receipt: Any, tenant_id: str = "", business_id: str = "", environment: str = "SANDBOX") -> None:
        refund_payload = refund.to_dict() if hasattr(refund, "to_dict") else dict(refund)
        receipt_payload = receipt.to_dict() if hasattr(receipt, "to_dict") else dict(receipt)
        now = _iso(datetime.now(timezone.utc))
        with self._session() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT payload FROM retail_entities WHERE entity_type = 'refund' AND json_extract(payload, '$.order_id') = ?", (refund_payload["order_id"],)).fetchall()
            prior = sum(float(json.loads(row["payload"]).get("amount", 0)) for row in rows if json.loads(row["payload"]).get("state") == "REFUNDED")
            order = db.execute("SELECT payload FROM orders WHERE order_id = ?", (refund_payload["order_id"],)).fetchone()
            order_amount = float(json.loads(order["payload"]).get("amount", 0)) if order else 0.0
            if refund_payload.get("amount", 0) <= 0 or prior + float(refund_payload["amount"]) > order_amount:
                db.rollback()
                raise TransactionSafetyError("REFUND_EXCEEDS_ELIGIBLE_VALUE", "refund amount exceeds the captured value remaining")
            db.execute("UPDATE idempotency SET status = ?, result_reference = ?, updated_at = ? WHERE idempotency_key = ? AND request_hash = ?", ("SUCCEEDED", refund_payload["refund_id"], now, key, request_hash))
            db.execute("INSERT OR REPLACE INTO receipts(receipt_id, request_hash, payload) VALUES (?, ?, ?)", (receipt_payload["receipt_id"], request_hash, json.dumps(receipt_payload, sort_keys=True)))
            db.execute("UPDATE idempotency SET receipt_reference = ? WHERE idempotency_key = ? AND request_hash = ?", (receipt_payload["receipt_id"], key, request_hash))
            db.execute("INSERT OR REPLACE INTO retail_entities(entity_type, entity_id, tenant_id, business_id, environment, schema_version, version, created_at, updated_at, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("refund", refund_payload["refund_id"], tenant_id, business_id, environment, self.schema_version, 1, now, now, json.dumps(refund_payload, sort_keys=True)))
            db.commit()

    def reconciliation_items(self, *, status: str | None = None) -> list[dict[str, Any]]:
        with self._session() as db:
            query = "SELECT reconciliation_id, logical_transaction_id, payload, status FROM reconciliation"
            rows = db.execute(query + (" WHERE status = ?" if status else "") + " ORDER BY reconciliation_id", (status,) if status else ()).fetchall()
        return [{"reconciliation_id": row["reconciliation_id"], "logical_transaction_id": row["logical_transaction_id"], "payload": json.loads(row["payload"]), "status": row["status"]} for row in rows]

    def resolve_reconciliation(self, reconciliation_id: str, *, status: str, verification: dict[str, Any]) -> None:
        if status not in {"SUCCEEDED", "FAILED", "MANUAL_ESCALATION"}:
            raise ValueError("invalid terminal reconciliation status")
        with self._session() as db:
            db.execute("UPDATE reconciliation SET status = ?, payload = json_set(payload, '$.verification', json(?), '$.resolved_at', ?) WHERE reconciliation_id = ?", (status, json.dumps(verification, sort_keys=True), _iso(datetime.now(timezone.utc)), reconciliation_id))

    def add_reconciliation(self, *, reconciliation_id: str, logical_transaction_id: str, payload: dict[str, Any], status: str = "PENDING") -> None:
        with self._session() as db:
            db.execute("INSERT OR REPLACE INTO reconciliation(reconciliation_id, logical_transaction_id, payload, status) VALUES (?, ?, ?, ?)", (reconciliation_id, logical_transaction_id, json.dumps(payload, sort_keys=True), status))

    def save_attestation(self, attestation: Any) -> None:
        payload = attestation.to_dict()
        with self._session() as db:
            db.execute("INSERT OR REPLACE INTO attestations(attestation_id, content_hash, revoked_at, payload) VALUES (?, ?, ?, ?)", (attestation.attestation_id, attestation.content_hash, attestation.revoked_at, json.dumps(payload, sort_keys=True)))


__all__ = ["SQLiteStateStore"]
