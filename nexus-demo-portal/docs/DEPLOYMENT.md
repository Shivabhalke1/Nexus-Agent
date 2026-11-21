# NEXUS Demo Portal — Deployment Guide

## 1. Local Development Setup (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm 9+

### Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Prometheus Metrics: `http://localhost:8000/metrics`
- Health Probe: `http://localhost:8000/api/v1/health`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:3000`
- Failure Simulator Control: `http://localhost:3000/simulator`

---

## 2. Containerized Deployment (Docker Compose)

The multi-container orchestration spins up a PostgreSQL 16 database, FastAPI backend, and Next.js frontend with isolated networking and healthchecks:

```bash
cd docker
docker compose up -d --build
```

### Checking Services
```bash
docker compose ps
docker compose logs -f backend
```

---

## 3. Environment Configuration (`.env`)

| Variable | Default Value | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Set to `production` in staging/prod |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/nexus_demo_portal` | PostgreSQL connection URL |
| `SECRET_KEY` | *(Random 32-char secret)* | JWT signature secret key |
| `ENABLE_FAILURE_SIMULATOR` | `true` | Restrict to `false` in live production |
| `SIMULATION_AUTH_KEY` | `dev-nexus-simulation-key-2026` | API key required to trigger failures |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed web origins |

---

## 4. Production Security Hardening
1. Set `ENABLE_FAILURE_SIMULATOR=false` or enforce strong `SIMULATION_AUTH_KEY` headers in staging.
2. Change default `SECRET_KEY` to a high-entropy cryptographically random string.
3. Configure reverse proxy (Nginx, Caddy, Cloudflare) with HTTPS termination.
4. Mount PostgreSQL on a persistent encrypted volume with regular automated snapshots.
