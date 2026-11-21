"""Local Approval Store using SQLite
Persists pending telemetry requests and immutable audit logs locally.
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Dict, List, Optional
from app.schemas.approval import (
    ApprovalDecisionEnum,
    ApprovalRequest,
    ApprovalAuditRecord,
    ApprovedSubmission,
)
from app.schemas.telemetry import TelemetryPayload
from app.schemas.policy import PolicyValidationResult
from app.core.security import compute_payload_integrity_hash
from app.core.logging_config import get_logger

logger = get_logger("approval_store")


class ApprovalStore:
    """Thread-safe SQLite store for pending approval requests and audit records."""

    def __init__(self, db_path: str = "collector_approval.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_requests (
                    request_id TEXT PRIMARY KEY,
                    payload_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    source_json TEXT NOT NULL,
                    sanitized_payload_json TEXT NOT NULL,
                    payload_integrity_hash TEXT NOT NULL,
                    policy_validation_json TEXT NOT NULL,
                    detection_summary_json TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_audit_log (
                    audit_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    payload_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    decided_by TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload_integrity_hash TEXT NOT NULL,
                    transmission_status TEXT NOT NULL,
                    notes TEXT
                )
                """
            )
            conn.commit()

    def save_request(self, req: ApprovalRequest) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO approval_requests (
                    request_id, payload_id, status, created_at, source_json,
                    sanitized_payload_json, payload_integrity_hash,
                    policy_validation_json, detection_summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    req.request_id,
                    req.payload_id,
                    req.status.value,
                    req.created_at.isoformat(),
                    json.dumps(req.source.model_dump(mode="json")),
                    json.dumps(req.sanitized_payload.model_dump(mode="json")),
                    req.payload_integrity_hash,
                    json.dumps(req.policy_validation.model_dump(mode="json")),
                    json.dumps(req.detection_summary),
                ),
            )
            conn.commit()

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approval_requests WHERE request_id = ?", (request_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_request(row)

    def list_pending(self) -> List[ApprovalRequest]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC",
                (ApprovalDecisionEnum.PENDING.value,),
            )
            rows = cursor.fetchall()
            return [self._row_to_request(r) for r in rows]

    def purge_old_pending(self, keep_latest: int = 10) -> int:
        """Purge stale pending requests, keeping only the most recent N items."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT request_id FROM approval_requests WHERE status = ? ORDER BY created_at DESC",
                (ApprovalDecisionEnum.PENDING.value,),
            )
            rows = cursor.fetchall()
            if len(rows) > keep_latest:
                to_delete = [r["request_id"] for r in rows[keep_latest:]]
                cursor.executemany(
                    "DELETE FROM approval_requests WHERE request_id = ?",
                    [(rid,) for rid in to_delete],
                )
                conn.commit()
                return len(to_delete)
            return 0

    def update_status(self, request_id: str, new_status: ApprovalDecisionEnum) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE approval_requests SET status = ? WHERE request_id = ?",
                (new_status.value, request_id),
            )
            conn.commit()

    def update_audit_transmission_status(self, request_id: str, status: str) -> None:
        """Update transmission status in the audit log for a request."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE approval_audit_log SET transmission_status = ? WHERE request_id = ?",
                (status, request_id),
            )
            conn.commit()

    def record_audit(self, audit: ApprovalAuditRecord) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO approval_audit_log (
                    audit_id, request_id, payload_id, decision, decided_by,
                    timestamp, payload_integrity_hash, transmission_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.audit_id,
                    audit.request_id,
                    audit.payload_id,
                    audit.decision.value,
                    audit.decided_by,
                    audit.timestamp.isoformat(),
                    audit.payload_integrity_hash,
                    audit.transmission_status,
                    audit.notes,
                ),
            )
            conn.commit()

    def list_audit_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM approval_audit_log ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def _row_to_request(self, row: sqlite3.Row) -> ApprovalRequest:
        payload_data = json.loads(row["sanitized_payload_json"])
        source_data = json.loads(row["source_json"])
        policy_data = json.loads(row["policy_validation_json"])
        detection_data = json.loads(row["detection_summary_json"])

        return ApprovalRequest(
            request_id=row["request_id"],
            payload_id=row["payload_id"],
            status=ApprovalDecisionEnum(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            source=source_data,
            sanitized_payload=payload_data,
            payload_integrity_hash=row["payload_integrity_hash"],
            policy_validation=policy_data,
            detection_summary=detection_data,
        )
