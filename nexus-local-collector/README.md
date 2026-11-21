# NEXUS Local Collector

The **NEXUS Local Collector** is the privacy-enforcing, local telemetry processing component of **NEXUS OBSERVE** developed for the **CICADA 2026** hackathon.

It runs entirely inside the customer's on-premises or private cloud environment.

---

## Core Engineering Principle
> **Raw logs, passwords, API keys, tokens, credentials, and sensitive customer information must remain inside the customer's environment by default.**
> Only sanitized, policy-compliant, and administrator-approved telemetry can ever be transmitted to NEXUS Central SaaS.

---

## Locked 7-Stage Pipeline
```
Customer Infrastructure (Demo Portal :8000 / Host psutil)
  │
  ▼
[Stage 1: Data Collection]
  │
  ▼
[Stage 2: Sensitive Data Detection]
  │
  ▼
[Stage 3: Data Filtering]
  │
  ▼
[Stage 4: Data Protection]
  │
  ▼
[Stage 5: Local Analysis]
  │
  ▼
[Stage 6: Policy Validation] ──(Violation)──> HARD STOP (Unapprovable)
  │ (Compliant)
  ▼
[Stage 7: Human Approval] ──(Rejected)──> REJECTED (Do Not Transmit)
  │ (Approved)
  ▼
Revalidation of Cryptographic Hash
  │
  ▼
[NEXUS Central SaaS Egress]
```

---

## Quickstart
```bash
cd collector
cp ../.env.example .env
python3 -m pytest tests/ -v
uvicorn app.main:app --host 0.0.0.0 --port 8001
```
Local Collector API and Approval Engine: [http://localhost:8001](http://localhost:8001)
