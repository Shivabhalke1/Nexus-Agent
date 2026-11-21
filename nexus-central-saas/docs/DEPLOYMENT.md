# NEXUS Central SaaS - Deployment and Demonstration Guide

This guide details running, configuring, and verifying **NEXUS Central SaaS** individually or as part of the complete **NEXUS OBSERVE** 3-component observability architecture.

---

## 1. Port Allocation Matrix

| Component | Backend Port | Frontend / Dashboard Port | Role |
|:---|:---:|:---:|:---|
| **NEXUS Demo Portal** | `8000` | `3000` | Monitored workload & failure simulator |
| **NEXUS Local Collector** | `8001` | `8001` | Local sanitization & admin approval gate |
| **NEXUS Central SaaS** | `8002` | `8002` (`/` or `/ui`) | Centralized monitoring, incident detection & resolution |

---

## 2. Quick Start

### 2.1 Using Startup Script
```bash
cd nexus-central-saas
chmod +x scripts/start-saas.sh
./scripts/start-saas.sh
```

### 2.2 Using Uvicorn Direct
```bash
cd nexus-central-saas/backend
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### 2.3 Using Docker Compose
```bash
cd nexus-central-saas/docker
docker compose up -d
```

---

## 3. Verification Endpoints

- **Dashboard UI:** `http://localhost:8002/` or `http://localhost:8002/ui`
- **Interactive OpenAPI Documentation:** `http://localhost:8002/docs`
- **Service Diagnostics:** `http://localhost:8002/health`
- **Ingestion Endpoint:** `POST http://localhost:8002/api/v1/ingest` (Header `X-API-Key: nexus-collector-auth-key-cicada-2026`)
- **System Health:** `GET http://localhost:8002/api/v1/health/summary`
- **Active Incidents:** `GET http://localhost:8002/api/v1/incidents/active`
- **Pending Approvals:** `GET http://localhost:8002/api/v1/approvals/pending`
- **Permitted Operations:** `GET http://localhost:8002/api/v1/resolution/registry`

---

## 4. Default Engineer Credentials

- **Username:** `engineer`
- **Password:** `engineer123!`
- **Role:** `engineer`
- **Token URL:** `POST /api/v1/auth/login`
