# NEXUS Demo Portal — Controlled Failure Simulator Specification

## 1. Overview
The Controlled Failure Simulator allows operators and automated test harnesses to inject controlled, non-destructive anomalies to test **NEXUS OBSERVE** and the **NEXUS Local Collector**.

## 2. Six Controlled Failure Scenarios

### Scenario 1 — High CPU Utilization
- **ID**: `high_cpu`
- **Behavior**: Spawns mathematical worker thread burning CPU cycles.
- **Safety Limits**: Default 15s, maximum 60s. Auto-terminates after timer expiration.
- **Observable Telemetry**: `nexus_system_cpu_percent` in `/metrics` surges upward; host telemetry in `/api/v1/metrics/system` reflects increased host CPU load.

### Scenario 2 — Slow API Response
- **ID**: `slow_api`
- **Behavior**: Injects configurable artificial delay (default 1500ms) into `/api/v1/products` requests.
- **Observable Telemetry**: `X-Response-Time-Ms` response header surges to >1500ms; `nexus_response_time_avg_ms` increases; latency histogram buckets populate `gt_1000ms`.

### Scenario 3 — Backend Unavailable
- **ID**: `backend_unavailable`
- **Behavior**: Intercepts requests on designated target routes, immediately returning `HTTP 503 Service Unavailable`.
- **Observable Telemetry**: Error counter surges; status code counter for `503` increments.

### Scenario 4 — Database Connection Failure
- **ID**: `database_failure`
- **Behavior**: Injects database connectivity fault. Health probe `/api/v1/health` and `/api/v1/health/ready` return `HTTP 503`, and catalog queries fail safely.
- **Safety**: Purely non-destructive; zero tables or records are modified, truncated, or dropped.

### Scenario 5 — Increased Application Errors
- **ID**: `increased_errors`
- **Behavior**: Forces targeted endpoints to return `HTTP 500 Internal Server Error` with `code="INTERNAL_SERVER_ERROR"`.
- **Observable Telemetry**: `nexus_errors_total` and `status_codes[500]` increment rapidly.

### Scenario 6 — Repeated Failed Login Attempts
- **ID**: `failed_logins`
- **Behavior**: Generates batch of synthetic failed authentication attempts recorded as `AUTH_LOGIN_FAILED` in application events.
- **Safety**: Synthetic targets (`@anomaly-simulation.test`), never emits real passwords.

## 3. Controls & Security
- **Endpoints**:
  - `GET /api/v1/simulator/status`: View scenario active state and remaining seconds.
  - `POST /api/v1/simulator/scenarios/{name}/activate`: Activate scenario with duration.
  - `POST /api/v1/simulator/scenarios/{name}/deactivate`: Stop scenario immediately.
  - `POST /api/v1/simulator/reset`: Emergency reset disarming all scenarios.
- **Protection**: Guarded by `ENABLE_FAILURE_SIMULATOR=true` and optional `X-Simulation-Key` header.
