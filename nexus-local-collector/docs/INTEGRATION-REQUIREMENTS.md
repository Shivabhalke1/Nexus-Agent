# NEXUS Local Collector — Monitored Sources & Integration Requirements

## 1. Verified Target: NEXUS Demo Portal
The Local Collector interfaces directly with the completed **NEXUS Demo Portal** running on `http://localhost:8000`.

### Monitored Endpoints & Contracts

| Data Source | Endpoint | Format | Telemetry Captured |
|---|---|---|---|
| **Prometheus Scrape** | `http://localhost:8000/metrics` | `text/plain` | `nexus_requests_total`, `nexus_errors_total`, `nexus_response_time_avg_ms`, `nexus_system_cpu_percent`, `nexus_http_requests_by_status` |
| **Structured JSON** | `http://localhost:8000/api/v1/metrics` | `application/json` | Total requests, requests per route, latency distribution (`le_10ms` to `gt_1000ms`), status codes |
| **Component Health** | `http://localhost:8000/api/v1/health` | `application/json` | Service status (`healthy`/`degraded`), API latency, Database latency & connectivity |
| **Audit Events** | `http://localhost:8000/api/v1/metrics/events` | `application/json` | Application audit stream (`USER_REGISTERED`, `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED`, `ORDER_CREATED`) |

---

## 2. Host System Telemetry (Local Node)
- **Engine**: Python `psutil`
- **Metrics Collected**:
  - CPU Utilization percentage (`cpu_percent`)
  - Virtual Memory used/total MB, percentage (`memory_percent`)
  - Disk Space used/total GB, percentage (`disk_percent`)
  - Network interface I/O counters (bytes sent, bytes received, errors)
  - Process RSS memory and thread count

---

## 3. Outbound Egress Target: NEXUS Central SaaS
- **Target URL**: Configurable via `CENTRAL_SAAS_URL` (default: `https://saas.nexus-observe.internal/api/v1/ingest`)
- **Protocol**: HTTPS / REST
- **Authentication**: `Bearer {CENTRAL_SAAS_API_KEY}`
- **Payload Requirement**: Strictly approved, sanitized, and policy-compliant JSON payloads.
