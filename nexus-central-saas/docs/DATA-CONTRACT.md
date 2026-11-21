# NEXUS Central SaaS - Telemetry Integration Contract
**Component**: NEXUS Central SaaS  
**Partner Component**: NEXUS Local Collector  
**Version**: 1.0.0 (CICADA 2026)  
**Status**: VERIFIED & APPROVED

---

## 1. Integration Overview

NEXUS Central SaaS receives approved, sanitized telemetry payloads from authorized NEXUS Local Collectors.
Communication occurs over HTTP/TLS POST to either `/api/v1/ingest` or `/api/v1/saas/ingest`.

---

## 2. Ingestion Endpoint Specification

- **Method**: `POST`
- **Paths**: `/api/v1/ingest`, `/api/v1/saas/ingest`
- **Authentication**: `X-API-Key` header with pre-shared collector secret (`COLLECTOR_API_KEY`)
- **Content-Type**: `application/json`

### 2.1 Inbound Submission Envelope (`ApprovedSubmission`)

```json
{
  "request_id": "c1f76e33-728b-4b2a-bf31-0dfae16f21a4",
  "decision": "APPROVED",
  "decision_by": "admin",
  "decision_at": "2026-11-21T00:15:30.000000Z",
  "reason": "Routine hourly telemetry export inspected and approved",
  "approved_payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "sanitized_payload": {
    "payload_id": "a8b34c2e-4890-4a81-b219-509930f4cfd1",
    "source": {
      "source_id": "nexus-demo-portal",
      "source_type": "APPLICATION",
      "environment": "production",
      "hostname": "collector-node-01",
      "ip_address": "127.0.0.1"
    },
    "collected_at": "2026-11-21T00:15:00.000000Z",
    "system_metrics": {
      "cpu_utilization_percent": 18.5,
      "memory_utilization_percent": 42.1,
      "memory_used_bytes": 3532652544,
      "memory_total_bytes": 8388608000,
      "disk_utilization_percent": 34.0,
      "disk_used_bytes": 17179869184,
      "disk_total_bytes": 50529027072,
      "network_bytes_sent": 1048576,
      "network_bytes_recv": 2097152,
      "network_interfaces": {},
      "timestamp": "2026-11-21T00:15:00.000000Z"
    },
    "application_metrics": {
      "service_name": "nexus-demo-portal",
      "status": "healthy",
      "http_requests_total": 1420,
      "http_errors_total": 3,
      "error_rate": 0.0021,
      "avg_response_time_ms": 14.2,
      "p95_response_time_ms": 38.6,
      "active_db_connections": 5,
      "db_query_errors": 0,
      "raw_metrics": {},
      "timestamp": "2026-11-21T00:15:00.000000Z"
    },
    "logs": [],
    "custom_events": [],
    "metadata": {
      "collector_version": "1.0.0",
      "sanitization_summary": {
        "secrets_redacted": 1
      }
    },
    "is_sanitized": true,
    "sanitization_summary": {
      "total_fields_modified": 1
    }
  }
}
```

---

## 3. Ingestion Validation Invariants

1. **Authentication**: `X-API-Key` must match configured key. Mismatches return `HTTP 401 Unauthorized`.
2. **Sanitization Mandatory**: `sanitized_payload.is_sanitized` must be `true`. Payloads with `false` return `HTTP 400 Bad Request`.
3. **Approved Decision**: `decision` must be `"APPROVED"`.
4. **Required Attributes**: `payload_id`, `source.source_id`, `collected_at`, and `approved_payload_hash` must be present.
5. **Ingestion Response**:
```json
{
  "status": "ACCEPTED",
  "ingestion_id": "saas_ingest_1",
  "received_at": "2026-11-21T00:15:30.000000Z",
  "payload_id": "a8b34c2e-4890-4a81-b219-509930f4cfd1"
}
```
