# NEXUS Central SaaS
**Component 3 of 3 in NEXUS OBSERVE for CICADA 2026**

NEXUS Central SaaS is the centralized observability, system health monitoring, incident detection, engineer approval, and problem resolution platform. It strictly receives only policy-compliant, sanitized, and administrator-approved telemetry from NEXUS Local Collector.

## Locked Core Features
1. **Receive Data**: Authenticated ingestion (`POST /api/v1/ingest` and `/api/v1/saas/ingest`), payload validation, and persistence.
2. **System Health Monitoring**: Real-time evaluation into 4 standard health states (Excellent, Good, Fair, Poor) with stale telemetry detection.
3. **Incident Detection**: Anomaly identification for high CPU, memory, disk, network, slow API, application errors, backend down, DB failures, and repeated failed logins.
4. **Engineer Approval**: Explicit engineer authorization interface binding decisions to permitted resolution actions.
5. **Resolve Problem**: Execution of explicitly permitted resolution operations with truthful outcome reporting.

## Port Assignments
- **Backend API**: `http://localhost:8002`
- **Frontend Dashboard**: `http://localhost:3001`
- **Monitored Demo Portal**: `http://localhost:8000` (Backend), `http://localhost:3000` (Frontend)
- **Local Collector Gateway**: `http://localhost:8001`
