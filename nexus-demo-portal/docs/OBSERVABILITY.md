# NEXUS Demo Portal — Observability & Telemetry Specification

## 1. Overview
The NEXUS Demo Portal exposes rich application and system telemetry designed for consumption by the **NEXUS Local Collector**.

## 2. Telemetry Endpoints

| Endpoint | Format | Description |
|---|---|---|
| `GET /metrics` | Prometheus Text (`text/plain`) | OpenMetrics/Prometheus formatted gauge and counter metrics |
| `GET /api/v1/metrics` | JSON | Application and host telemetry summary |
| `GET /api/v1/metrics/system` | JSON | Direct host resource metrics (`psutil`: CPU, RAM, Disk, Uptime) |
| `GET /api/v1/metrics/events` | JSON | Recent structured application audit and anomaly events |
| `GET /api/v1/health` | JSON | Component-level status probe (API runtime + Database connectivity) |
| `GET /api/v1/health/live` | JSON | Container/Process liveness probe |
| `GET /api/v1/health/ready` | JSON | Database readiness probe |

## 3. Metrics Exposed

### System Metrics (Host)
- `nexus_system_cpu_percent`: Instantaneous host CPU utilization percentage.
- `nexus_system_memory_percent`: Host RAM utilization percentage.
- `nexus_system_uptime_seconds`: Continuous application uptime in seconds.
- `process_memory_mb`: Process Resident Set Size (RSS).
- `process_threads`: Active OS threads within the backend process.

### Application Metrics
- `nexus_requests_total`: Cumulative counter of all processed HTTP requests.
- `nexus_errors_total`: Cumulative counter of HTTP 4xx and 5xx responses.
- `nexus_response_time_avg_ms`: Rolling average response duration in milliseconds.
- `nexus_http_requests_by_status`: Counters partitioned by HTTP status code (`200`, `201`, `400`, `401`, `404`, `500`).
- Latency histogram buckets: `le_10ms`, `le_50ms`, `le_100ms`, `le_250ms`, `le_500ms`, `le_1000ms`, `gt_1000ms`.

## 4. Structured JSON Logging
Every request produces a structured JSON log entry:
```json
{
  "timestamp": "2026-11-20 23:55:00,123",
  "level": "INFO",
  "logger": "nexus-demo-backend",
  "message": "HTTP POST /api/v1/orders/checkout -> 201 (18.4ms)",
  "request_id": "893c5fa2-938b-4a57-814d-fa38f830a612",
  "endpoint": "/api/v1/orders/checkout",
  "status_code": 201,
  "duration_ms": 18.4
}
```

## 5. Privacy & Sanitization Compliance
1. **Passwords**: Plaintext passwords in registration or login are filtered at schema and logging boundaries.
2. **Tokens**: JWT access tokens in headers or logs are automatically redacted to `Bearer [REDACTED]`.
3. **PII**: Customer email domains are stored in events without sensitive personal identity data.
4. **Secrets**: Database credentials and simulation API keys are excluded from telemetry payloads.
