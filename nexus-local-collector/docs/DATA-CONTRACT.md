# NEXUS OBSERVE - Local Collector Data Contract
**Component**: NEXUS Local Collector  
**Target Consumer**: NEXUS Central SaaS  
**Version**: 1.0.0 (CICADA 2026)  
**Status**: APPROVED

---

## 1. Executive Summary

This document defines the strict data contract governing all telemetry collected, sanitized, approved, and transmitted by the NEXUS Local Collector to NEXUS Central SaaS. 

In accordance with the NEXUS Privacy & Security Principles:
- **Raw Credentials Never Leave Local Scope**: Passwords, API keys, database connection strings, bearer tokens, authorization headers, and personal identifying information (PII) must be redacted or masked prior to egress.
- **Strict Human Approval Required**: No telemetry is transmitted without explicit, cryptographically verifiable administrator approval.
- **Immutable Payload Hash**: Telemetry is bound to a SHA-256 canonical integrity hash upon human approval. If any field is mutated post-approval, the integrity check fails and transmission is blocked.

---

## 2. Ingestion & Egress Payloads

### 2.1 Egress Telemetry Schema (`TelemetryPayload`)

All outbound submissions sent to `POST /api/v1/telemetry/ingest` on NEXUS Central SaaS adhere to the following JSON structure:

```json
{
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
    "network_interfaces": {
      "lo0": {"bytes_sent": 524288, "bytes_recv": 524288}
    },
    "timestamp": "2026-11-21T00:15:00.000000Z"
  },
  "application_metrics": {
    "service_name": "nexus-demo-portal-backend",
    "status": "healthy",
    "http_requests_total": 1420,
    "http_errors_total": 3,
    "error_rate": 0.0021,
    "avg_response_time_ms": 14.2,
    "p95_response_time_ms": 38.6,
    "active_db_connections": 5,
    "db_query_errors": 0,
    "raw_metrics": {
      "http_requests_by_method": {"GET": 1200, "POST": 220}
    },
    "timestamp": "2026-11-21T00:15:00.000000Z"
  },
  "logs": [
    {
      "timestamp": "2026-11-21T00:14:58.000000Z",
      "level": "INFO",
      "message": "User authentication succeeded for user: [REDACTED_EMAIL]",
      "service": "demo-portal",
      "event_type": "AUTH_SUCCESS",
      "attributes": {
        "status_code": 200,
        "token_preview": "[REDACTED_SECRET]"
      }
    }
  ],
  "custom_events": [],
  "metadata": {
    "collector_version": "1.0.0",
    "filtering_applied": true,
    "protection_applied": true
  },
  "is_sanitized": true,
  "sanitization_summary": {
    "emails_masked": 1,
    "secrets_redacted": 1,
    "total_fields_modified": 2
  }
}
```

---

## 3. Field Specifications & Constraints

| Field Path | Type | Nullable | Description & Constraints |
| :--- | :--- | :--- | :--- |
| `payload_id` | UUID (string) | No | Unique ID generated per collection cycle. |
| `source.source_id` | string (1-128 chars) | No | Registered source identifier (e.g. `nexus-demo-portal`). |
| `source.source_type` | enum (`HOST`, `APPLICATION`, `NETWORK`, `LOG`) | No | Origin category. |
| `source.environment` | string (1-64 chars) | No | Deployment tier (`production`, `staging`, `local`). |
| `collected_at` | ISO 8601 UTC string | No | UTC timestamp of initial collection. |
| `system_metrics` | object (`SystemMetricsData`) | Yes | Host system health and performance statistics. |
| `application_metrics`| object (`ApplicationMetricsData`) | Yes | Monitored application metrics and health state. |
| `logs` | array of `LogEntry` | No | Sanitized structured application logs. Max 500 entries per batch. |
| `is_sanitized` | boolean | No | **Must be `true`** for egress. Policy validation enforces this. |
| `sanitization_summary` | object | Yes | Summary counts of masking/redaction actions taken. |

---

## 4. Human Approval Submission Contract

Central SaaS will only accept payloads encapsulated in an authenticated submission envelope signed by an authorized local administrator.

### 4.1 Egress Envelope (`POST /api/v1/telemetry/submit`)

```json
{
  "request_id": "c1f76e33-728b-4b2a-bf31-0dfae16f21a4",
  "decision": "APPROVED",
  "decision_by": "admin",
  "decision_at": "2026-11-21T00:15:30.000000Z",
  "reason": "Routine hourly telemetry export inspected and approved",
  "approved_payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "sanitized_payload": { ... }
}
```

### 4.2 Revalidation Workflow Prior to Transmission
1. Prior to transmission, the Collector re-computes `sha256(canonical_json(sanitized_payload))`.
2. The computed hash MUST exactly match `approved_payload_hash`.
3. If hashes mismatch, transmission is aborted immediately and an audit alert is triggered.
4. If hashes match, HTTP POST with an API bearer token is dispatched to NEXUS Central SaaS.
