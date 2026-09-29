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
    """Durable, dependency-free reference store for RC1 restart tests."""

    schema_version = 1

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
                CREATE TABLE IF NOT EXISTS pack_state (pack_id TEXT PRIMARY KEY, lifecycle_state TEXT NOT NULL, content_hash TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS evidence (observation_hash TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, pack_id TEXT NOT NULL, field_name TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attestations (attestation_id TEXT PRIMARY KEY, content_hash TEXT NOT NULL, revoked_at TEXT, payload TEXT NOT NULL);
                INSERT OR IGNORE INTO metadata(key, value) VALUES ('schema_version', '1');
                """
            )

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

    def load_orders(self) -> list[dict[str, Any]]:
        with self._session() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM orders ORDER BY order_id")]

    def add_reconciliation(self, *, reconciliation_id: str, logical_transaction_id: str, payload: dict[str, Any], status: str = "PENDING") -> None:
        with self._session() as db:
            db.execute("INSERT OR REPLACE INTO reconciliation(reconciliation_id, logical_transaction_id, payload, status) VALUES (?, ?, ?, ?)", (reconciliation_id, logical_transaction_id, json.dumps(payload, sort_keys=True), status))

    def save_attestation(self, attestation: Any) -> None:
        payload = attestation.to_dict()
        with self._session() as db:
            db.execute("INSERT OR REPLACE INTO attestations(attestation_id, content_hash, revoked_at, payload) VALUES (?, ?, ?, ?)", (attestation.attestation_id, attestation.content_hash, attestation.revoked_at, json.dumps(payload, sort_keys=True)))


__all__ = ["SQLiteStateStore"]
