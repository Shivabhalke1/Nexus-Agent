# NEXUS Local Collector - Deployment & Verification Guide
**Component**: NEXUS Local Collector (NEXUS OBSERVE)  
**Version**: 1.0.0 (CICADA 2026)  
**Port**: 8001 (Monitored Demo Portal binds to port 8000)

---

## 1. System Requirements

- **Python**: Python 3.11+ (Python 3.14 compatible)
- **Monitored Service**: NEXUS Demo Portal running on `http://localhost:8000`
- **Dependencies**: `fastapi`, `uvicorn`, `pydantic-settings`, `httpx`, `psutil`, `python-jose`, `bcrypt`, `pytest`, `pytest-asyncio`

---

## 2. Directory Structure

```text
nexus-local-collector/
├── approval-interface/
│   └── index.html               # Human Approval Web Console (Tailwind CSS, dark mode)
├── collector/
│   ├── app/
│   │   ├── analysis/            # Local Analysis Engine (6 failure scenario detectors)
│   │   ├── api/v1/              # FastAPI Router (Auth, Pipeline, Approval)
│   │   ├── approval/            # Approval Service & SQLite Store
│   │   ├── collection/          # Host (psutil) & App (HTTPX) Collectors
│   │   ├── core/                # Configuration, Structured Logging, JWT/Bcrypt/SHA-256
│   │   ├── detection/           # Sensitive Data Detection Engine & Rules
│   │   ├── filtering/           # Allowlist/Denylist Data Filtering Engine
│   │   ├── policies/            # Policy Validation Engine & Hard Blocks
│   │   ├── protection/          # Redaction & Masking Engine
│   │   ├── schemas/             # Pydantic v2 Telemetry Models
│   │   ├── transmission/        # SaaS Client & Mock SaaS Ingestion
│   │   └── main.py              # Application Entry Point
│   ├── requirements.txt
│   └── tests/                   # 57 Automated Unit, Integration & E2E Tests
├── docs/
│   ├── ARCHITECTURE.md          # Component Architecture & Pipeline Flow
│   ├── DATA-CONTRACT.md         # Schema & Egress Transmission Contract
│   ├── INTEGRATION-REQUIREMENTS.md
│   ├── TEST-REPORT.md           # Audit & Verification Results
│   └── DEPLOYMENT.md            # This Deployment Guide
└── scripts/
    └── start-collector.sh       # Executable Production Startup Script
```

---

## 3. Starting the Collector

### Quick Start via Script
```bash
cd nexus-local-collector
./scripts/start-collector.sh
```

### Manual Start via Uvicorn
```bash
cd nexus-local-collector/collector
export PYTHONPATH=.
/Volumes/SHIV\ BHALKE/NEXUS-OBSERVE/nexus-demo-portal/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Once running:
- **Approval Dashboard**: [http://localhost:8001/ui](http://localhost:8001/ui) (or [http://localhost:8001/](http://localhost:8001/))
- **Health Diagnostic**: [http://localhost:8001/health](http://localhost:8001/health)
- **Status Endpoint**: [http://localhost:8001/status](http://localhost:8001/status)
- **API Documentation**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 4. Evaluator Verification Walkthrough

Follow these steps to demonstrate the complete NEXUS Local Collector workflow:

### Step 1: Access the Human Approval Dashboard
Open your web browser and navigate to:
```
http://localhost:8001/ui
```
You will see the **NEXUS Local Collector Privacy Gateway** interface.

### Step 2: Sign in as Administrator
Click the **Login** button in the header:
- **Username**: `admin`
- **Password**: `admin123!`
Click **Sign In**. The header will update to show `Administrator: admin`.

### Step 3: Trigger a Collection Cycle
Click the blue **Run Collection Cycle** button. The Collector will:
1. Sample host CPU, memory, disk, and network stats via `psutil`.
2. Connect to the live NEXUS Demo Portal on port 8000 to ingest application metrics and audit events.
3. Detect sensitive values (passwords, tokens, emails).
4. Filter unnecessary noise fields.
5. Mask and redact all detected credentials into standard tokens (`[REDACTED_SECRET]`, `[REDACTED_EMAIL]`, etc.).
6. Analyze operational metrics for abnormal conditions.
7. Validate outgoing payload against privacy policies.
8. Queue the submission in the **Pending Submissions** list with a green `COMPLIANT` badge.

### Step 4: Inspect the Sanitized Payload
Click on the pending submission item on the left:
- The **Canonical SHA-256 Hash** is displayed in the top banner.
- The **Sanitization Summary** card displays the exact count of modified/redacted fields.
- The **JSON Inspector** displays the exact sanitized payload that will leave the customer environment.
- Confirm that passwords, emails, and tokens are safely redacted with no raw secret leakage.

### Step 5: Approve Telemetry Transmission
Enter optional notes (e.g., `"Inspected and approved by security lead"`) and click **Approve Transmission**:
1. The Collector verifies that no hard policy blocks exist.
2. It re-computes the canonical SHA-256 hash to verify zero post-inspection mutation.
3. It updates the status to `APPROVED` and writes an immutable entry into the **Approval Audit Log** table at the bottom of the page.
4. It dispatches the approved submission to Central SaaS.

### Step 6: Verify Policy Hard Block (Security Demonstration)
To demonstrate privacy guardrails:
If a raw or unsanitized payload is created, the system flags `POLICY BLOCKED`. The **Approve Transmission** button is disabled, and any direct API approval attempt returns `HTTP 400 Bad Request` with `PolicyViolationBlockedError`. Hard policy blocks cannot be bypassed.

---

## 5. Running the Complete Automated Test Suite

```bash
cd nexus-local-collector/collector
/Volumes/SHIV\ BHALKE/NEXUS-OBSERVE/nexus-demo-portal/backend/.venv/bin/pytest tests/ -v
```
All **57 tests** pass cleanly in ~5 seconds.
