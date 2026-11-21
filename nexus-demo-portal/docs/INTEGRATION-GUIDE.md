# NEXUS Demo Portal — Local Collector Integration Guide

## 1. Overview
This guide provides the complete interface specification and data contracts for the **NEXUS Local Collector** team to monitor and extract telemetry from the **NEXUS Demo Portal**.

The Demo Portal operates independently and exposes standardized, privacy-sanitized monitoring endpoints.

---

## 2. Service Identification & Topology

- **Service Name**: `nexus-demo-backend`
- **Application Name**: `NEXUS-Demo-Portal-Backend`
- **Default Port**: `8000`
- **Protocol**: HTTP/1.1 (JSON & OpenMetrics plaintext)
- **Base API URL**: `http://localhost:8000/api/v1`
- **Prometheus Scrape URL**: `http://localhost:8000/metrics`
- **Health Probes**: `http://localhost:8000/api/v1/health` (also aliased at `http://localhost:8000/health`)

---

## 3. Telemetry Ingestion Channels

The Local Collector can pull telemetry through three standardized interfaces:

### Channel A — OpenMetrics / Prometheus Scrape (`GET /metrics`)
Recommended scraping interval: **5 seconds to 15 seconds**.

**Sample Metric Output:**
```prometheus
# HELP nexus_requests_total Total number of HTTP requests processed.
# TYPE nexus_requests_total counter
nexus_requests_total 142

# HELP nexus_errors_total Total number of HTTP errors (status >= 400).
# TYPE nexus_errors_total counter
nexus_errors_total 3

# HELP nexus_response_time_avg_ms Average HTTP response time in milliseconds.
# TYPE nexus_response_time_avg_ms gauge
nexus_response_time_avg_ms 14.82

# HELP nexus_system_cpu_percent Host CPU utilization percentage.
# TYPE nexus_system_cpu_percent gauge
nexus_system_cpu_percent 12.4

# HELP nexus_system_memory_percent Host memory utilization percentage.
# TYPE nexus_system_memory_percent gauge
nexus_system_memory_percent 48.6

# HELP nexus_system_uptime_seconds Application uptime in seconds.
# TYPE nexus_system_uptime_seconds gauge
nexus_system_uptime_seconds 3612.45

# HELP nexus_http_requests_by_status HTTP requests partitioned by status code.
# TYPE nexus_http_requests_by_status counter
nexus_http_requests_by_status{status="200"} 128
nexus_http_requests_by_status{status="201"} 11
nexus_http_requests_by_status{status="401"} 2
nexus_http_requests_by_status{status="404"} 1
```

---

### Channel B — Structured JSON Telemetry (`GET /api/v1/metrics`)
Ideal for JSON-based collectors or web socket pollers.

**Endpoint:** `http://localhost:8000/api/v1/metrics`
```json
{
  "success": true,
  "message": "Metrics snapshot retrieved successfully",
  "data": {
    "application": {
      "total_requests": 142,
      "total_errors": 3,
      "error_rate_percent": 2.11,
      "avg_response_time_ms": 14.82,
      "min_response_time_ms": 2.1,
      "max_response_time_ms": 42.6,
      "requests_by_endpoint": {
        "/api/v1/products": 89,
        "/api/v1/cart": 32,
        "/api/v1/orders/checkout": 11,
        "/api/v1/auth/login": 10
      },
      "status_codes": {
        "200": 128,
        "201": 11,
        "401": 2,
        "404": 1
      },
      "latency_distribution": {
        "le_10ms": 45,
        "le_50ms": 94,
        "le_100ms": 3,
        "le_250ms": 0,
        "le_500ms": 0,
        "le_1000ms": 0,
        "gt_1000ms": 0
      }
    },
    "system": {
      "cpu_percent": 12.4,
      "memory_used_mb": 4210.5,
      "memory_total_mb": 16384.0,
      "memory_percent": 48.6,
      "disk_used_gb": 48.2,
      "disk_total_gb": 256.0,
      "disk_percent": 18.8,
      "process_memory_mb": 62.4,
      "process_threads": 8,
      "uptime_seconds": 3612.45
    }
  }
}
```

---

### Channel C — Structured Audit Events (`GET /api/v1/metrics/events`)
Provides granular event stream for security anomaly detection and transaction auditing.

**Query Parameters:**
- `limit` (int, default 50, max 200)
- `severity` (string, optional: `INFO`, `WARNING`, `ERROR`)

**Sample Event Output:**
```json
{
  "success": true,
  "data": [
    {
      "id": 14,
      "event_type": "ORDER_CREATED",
      "severity": "INFO",
      "request_id": "893c5fa2-938b-4a57-814d-fa38f830a612",
      "timestamp": "2026-11-20T23:55:00.123456",
      "payload": "{\"order_number\": \"NEXUS-20261120-A4B92C\", \"user_id\": 1, \"total_amount\": \"249.99\", \"item_count\": 1}"
    },
    {
      "id": 13,
      "event_type": "AUTH_LOGIN_FAILED",
      "severity": "WARNING",
      "request_id": "c71a39f0-281b-4f90-9511-aa92c8172901",
      "timestamp": "2026-11-20T23:54:32.654321",
      "payload": "{\"event\": \"AUTH_LOGIN_FAILED\", \"user_id\": null, \"email_domain\": \"example.com\", \"error\": \"Invalid credentials\"}"
    }
  ]
}
```

---

## 4. Anomaly Telemetry Signatures (For Collector Triage)

When the 6 controlled failure scenarios are triggered via the simulator, the Local Collector will observe the following distinctive telemetry signatures:

| Scenario | Trigger / Cause | Primary Telemetry Signature | Collector Alert Rule |
|---|---|---|---|
| **Scenario 1 — High CPU** | `high_cpu` activated | `nexus_system_cpu_percent` > 70% | High CPU utilization anomaly |
| **Scenario 2 — Slow API** | `slow_api` activated | `avg_response_time_ms` > 1500ms, `gt_1000ms` bucket increments | High latency / SLA breach alert |
| **Scenario 3 — Backend Unavailable** | `backend_unavailable` activated | Status code `503` surges on targeted routes | Service unavailability incident |
| **Scenario 4 — Database Failure** | `database_failure` activated | `/api/v1/health` reports status `degraded` and database component `unhealthy` | Database connectivity failure |
| **Scenario 5 — High Error Rate** | `increased_errors` activated | Status code `500` surges, `error_rate_percent` reaches 100% | Application error spike |
| **Scenario 6 — Failed Logins** | `failed_logins` activated | Rapid succession of `AUTH_LOGIN_FAILED` events | Brute-force / credential attack alert |

---

## 5. Privacy & Data Protection Safeguards
The Local Collector is guaranteed the following safety guarantees by the Demo Portal:
1. **Zero Passwords**: Neither user-entered passwords nor hashes are ever logged or sent over telemetry APIs.
2. **Redacted Bearer Tokens**: Authorization tokens are stripped to `Bearer [REDACTED]`.
3. **Synthetic Isolation**: Anomaly test accounts utilize synthetic domain patterns (`@anomaly-simulation.test`).
4. **No Internal Secrets**: Database connection strings, API simulation keys, and application signing keys are excluded from telemetry payloads.
