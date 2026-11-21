# NEXUS Demo Portal

The **NEXUS Demo Portal** is a production-grade, highly observable dummy e-commerce application built for the **CICADA 2026** hackathon. It serves as the primary realistic test environment for the **NEXUS OBSERVE** observability platform.

---

## Key Features

- **Realistic E-Commerce Engine**: Complete user journeys including product catalog browsing, faceted search, category filtering, cart management, simulated checkout, and order history.
- **Deep Observability & Telemetry**:
  - Request ID tracing (`X-Request-ID`).
  - System telemetry (Host CPU, Memory, Disk, Uptime via `psutil`).
  - Application metrics (Request counters, response time histograms, error tallies).
  - Standardized health endpoints (`/health`, `/health/live`, `/health/ready`, `/metrics`).
  - Privacy-compliant structured JSON logging (strictly zero passwords, tokens, or PII).
- **Controlled Failure Simulator**:
  - 6 dedicated non-destructive failure scenarios for testing detection and triage capabilities:
    1. High CPU Utilization (configurable load and duration).
    2. Slow API Responses (artificial latency injection).
    3. Backend Service Unavailable (controlled HTTP 503).
    4. Database Connection Failure (controlled DB fault injection).
    5. Increased Application Errors (controlled HTTP 500 bursts).
    6. Repeated Failed Login Attempts (synthetic authentication stress).
  - Developer Control Panel to safely activate, inspect, and recover scenarios.

---

## Technology Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, Lucide Icons, React Hook Form, Zod, TanStack Query.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, Uvicorn.
- **Database**: PostgreSQL (primary with Alembic migrations) + SQLite support for automated isolated testing.
- **Testing**: Pytest for backend and integration tests, Playwright for end-to-end tests.

---

## Directory Structure

```
nexus-demo-portal/
├── frontend/               # Next.js App Router application
├── backend/                # FastAPI application
├── database/               # SQL migrations, seeds, and schemas
├── tests/                  # Cross-tier integration and E2E tests
├── docs/                   # Architecture, API specifications, and guides
├── .env.example            # Environment template
├── .gitignore              # Project-level git ignore rules
└── README.md               # Project documentation
```

---

## Quickstart

### Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Frontend will be available at: [http://localhost:3000](http://localhost:3000)
