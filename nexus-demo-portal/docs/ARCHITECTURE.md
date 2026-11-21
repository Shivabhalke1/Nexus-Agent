# NEXUS Demo Portal — Architecture Specification

## 1. System Overview
NEXUS Demo Portal is an independently runnable e-commerce application designed to simulate normal online shopping workloads and safe, controlled anomaly scenarios. It exposes high-fidelity application and system metrics without requiring direct instrumentation coupling with the NEXUS Local Collector.

```
+-----------------------------------------------------------------------------------------+
|                                    NEXUS DEMO PORTAL                                    |
|                                                                                         |
|  [Frontend (Next.js 15 App Router)]                                                     |
|   ├── Pages: Home, Products, Categories, Cart, Checkout, Orders, Profile, Simulator     |
|   ├── State: TanStack Query (Server State), React Hook Form + Zod (Validation)          |
|   └── UI: Tailwind CSS + Lucide Icons (Responsive, Accessible)                         |
|                                                                                         |
|  [REST API Gateway / Communication (JSON over HTTP)]                                    |
|                                                                                         |
|  [Backend (FastAPI + Python 3.11+)]                                                     |
|   ├── Middleware: Correlation ID (X-Request-ID), Timing, Structured Logger, Simulator   |
|   ├── Observability: /health, /health/live, /health/ready, /metrics (Prometheus-style)  |
|   ├── Failure Simulator: Controlled in-memory state engine (6 Scenarios)                |
|   ├── API Routers: Auth, Users, Products, Categories, Cart, Orders, Simulator, Health   |
|   └── Persistence: SQLAlchemy 2.0 ORM + Alembic Migrations                              |
|                                                                                         |
|  [Storage Tier]                                                                         |
|   └── PostgreSQL (Primary Production Engine) / SQLite (Isolated Testing Mode)          |
+-----------------------------------------------------------------------------------------+
```

## 2. API Design Conventions
- **Base Route**: `/api/v1`
- **Envelope Standard**: Predictable JSON responses containing `status`, `data`, and standard error payloads with `detail` and `code`.
- **Headers**:
  - `X-Request-ID`: Generated for every request if not supplied by the caller, propagated to response headers and log context.
  - `X-Simulation-Key`: Required for accessing and triggering failure simulator endpoints.

## 3. Observability Architecture
- **Host Metrics**: Uses `psutil` to inspect CPU percentage, memory consumption, disk usage, and host process count.
- **Application Metrics**: Thread-safe in-memory sliding counters recording total requests, status codes, route breakdown, and average response times.
- **Structured Logs**: Standard Python `logging` formatted as JSON strings, with timestamps, log levels, request IDs, endpoints, status codes, and execution durations.

## 4. Failure Simulator Architecture
- Scenarios operate via central state registry with auto-expire timers.
- Safety boundaries: Scenarios automatically disarm after configured durations (maximum 300 seconds) and never perform irreversible file or database deletion.
