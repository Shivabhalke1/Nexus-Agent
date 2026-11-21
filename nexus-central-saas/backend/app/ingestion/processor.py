"""Telemetry Ingestion Processor and Persistence"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import TelemetryRecord, Collector
from app.schemas.approval import ApprovedSubmission
from app.core.logging_config import get_logger

logger = get_logger("ingestion_processor")


class TelemetryProcessor:
    """Processes, validates, and persists accepted approved telemetry."""

    @staticmethod
    def process_submission(submission: ApprovedSubmission, db: Session) -> Dict[str, Any]:
        """Validate and persist an approved submission."""
        payload = submission.sanitized_payload
        payload_dict = payload.model_dump(mode="json")

        # 1. Update or register collector
        collector = db.query(Collector).filter(Collector.collector_id == payload.source.source_id).first()
        if not collector:
            collector = Collector(
                collector_id=payload.source.source_id,
                name=payload.source.source_id,
                api_key="registered",
                environment=payload.source.environment,
                last_seen_at=datetime.now(timezone.utc),
            )
            db.add(collector)
        else:
            collector.last_seen_at = datetime.now(timezone.utc)

        # 2. Persist or update TelemetryRecord (idempotent ingestion)
        rec = db.query(TelemetryRecord).filter(TelemetryRecord.payload_id == payload.payload_id).first()
        if rec:
            rec.request_id = submission.request_id
            rec.source_id = payload.source.source_id
            rec.environment = payload.source.environment
            rec.is_sanitized = payload.is_sanitized
            rec.payload_hash = submission.approved_payload_hash
            rec.received_at = datetime.now(timezone.utc)
            rec.payload_json = json.dumps(payload_dict)
        else:
            rec = TelemetryRecord(
                payload_id=payload.payload_id,
                request_id=submission.request_id,
                source_id=payload.source.source_id,
                environment=payload.source.environment,
                is_sanitized=payload.is_sanitized,
                payload_hash=submission.approved_payload_hash,
                received_at=datetime.now(timezone.utc),
                payload_json=json.dumps(payload_dict),
            )
            db.add(rec)
        db.commit()

        # 3. Trigger Central SaaS Incident Detection Engine
        try:
            from app.detection.engine import IncidentDetectionEngine
            IncidentDetectionEngine.evaluate_payload(payload_dict, db)
        except Exception as det_err:
            logger.error(f"Error during incident detection: {det_err}")

        logger.info(
            f"Successfully ingested telemetry: payload_id={payload.payload_id}, "
            f"source={payload.source.source_id}, hash={submission.approved_payload_hash[:16]}..."
        )

        return {
            "status": "ACCEPTED",
            "ingestion_id": f"ingest_{rec.id}",
            "received_at": rec.received_at.isoformat(),
            "payload_id": payload.payload_id,
            "source_id": payload.source.source_id,
        }

    @staticmethod
    def get_recent_telemetry(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent telemetry records."""
        records = db.query(TelemetryRecord).order_by(TelemetryRecord.received_at.desc()).limit(limit).all()
        result = []
        for r in records:
            result.append({
                "payload_id": r.payload_id,
                "request_id": r.request_id,
                "source_id": r.source_id,
                "environment": r.environment,
                "is_sanitized": r.is_sanitized,
                "payload_hash": r.payload_hash,
                "received_at": r.received_at.isoformat(),
                "payload": json.loads(r.payload_json),
            })
        return result
