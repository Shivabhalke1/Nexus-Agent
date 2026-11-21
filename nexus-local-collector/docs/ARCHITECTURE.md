# NEXUS Local Collector — Architecture Specification

## 1. System Overview
NEXUS Local Collector is the privacy-enforcing, local telemetry ingestion, sanitization, and policy enforcement component of **NEXUS OBSERVE**.

It guarantees that raw telemetry, passwords, API keys, tokens, and sensitive customer information remain strictly inside the customer's perimeter.

## 2. 7-Stage Pipeline Architecture

```
[Monitored Sources: Host psutil, Demo Portal :8000, Network Stats]
                           │
                           ▼
          Stage 1: DATA COLLECTION ENGINE
          • System Metrics (psutil)
          • Application Metrics & Health
          • Structured Events & Logs
                           │
                           ▼
          Stage 2: SENSITIVE DATA DETECTION ENGINE
          • Pattern Matching & Classification
          • Passwords, API Keys, Tokens, PII
          • Structured JSON & Nested Object Inspection
                           │
                           ▼
          Stage 3: DATA FILTERING ENGINE
          • Allowlist & Denylist Rules
          • Unwanted Metadata & Log Removal
                           │
                           ▼
          Stage 4: DATA PROTECTION ENGINE
          • Field-Level Masking & Redaction
          • Privacy Sanitization
                           │
                           ▼
          Stage 5: LOCAL ANALYSIS ENGINE
          • Configurable Thresholds & Baselines
          • Anomaly Alerts (CPU, Latency, Errors, Logins)
                           │
                           ▼
          Stage 6: POLICY VALIDATION ENGINE
          • Privacy & Security Policy Compliance
          • Hard Policy Blocking (Cannot be bypassed)
                           │
                           ▼
          Stage 7: HUMAN APPROVAL INTERFACE
          • Exact Sanitized JSON Payload Viewer
          • Cryptographic Integrity Verification (SHA-256)
          • Explicit Admin Approve / Reject
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
        [APPROVE]                    [REJECT]
             │                           │
    Revalidate Integrity                 ▼
             │                   DO NOT TRANSMIT
             ▼
   [NEXUS Central SaaS (HTTPS)]
```

## 3. Cryptographic Integrity Guarantee
Before presenting a sanitized payload to the human administrator, a canonical SHA-256 integrity hash is computed:
`hash = SHA-256(canonical_json(payload))`
Immediately before transmission to Central SaaS, the hash is re-computed and re-validated against active policies. If even a single byte changes, the transmission is aborted.
