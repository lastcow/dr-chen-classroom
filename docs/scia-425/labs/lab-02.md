---
title: "Lab 02: Threat Modeling with STRIDE"
course: SCIA-425
topic: Threat Modeling — Systematic Security Analysis
week: 3
difficulty: ⭐⭐
estimated_time: 90 minutes
---

# Lab 02: Threat Modeling with STRIDE

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 3 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 90 minutes |
| **Topic** | Threat Modeling — Systematic Security Analysis |
| **Prerequisites** | Python 3.10+, `pip install pytm` |
| **Deliverables** | `threat_model.py`, generated DFD, `stride_analysis.json`, `threat_report.md` |

---

## Overview

Threat modeling is the systematic process of identifying and prioritizing threats **before** code is written. In this lab you will model a **Telehealth Appointment System** using the STRIDE methodology, generate a Data Flow Diagram (DFD) programmatically using the `pytm` library, enumerate threats for each element, and produce a structured threat report with mitigations.

STRIDE categories:
| Letter | Threat | Violated Property |
|--------|--------|-------------------|
| **S** | Spoofing | Authentication |
| **T** | Tampering | Integrity |
| **R** | Repudiation | Non-repudiation |
| **I** | Information Disclosure | Confidentiality |
| **D** | Denial of Service | Availability |
| **E** | Elevation of Privilege | Authorization |

---

!!! warning "Docker Required for pytm DFD generation"
    pytm requires Graphviz. Use the provided Docker command instead of installing locally.
    ```bash
    docker run --rm -v "$PWD":/work -w /work python:3.11-slim bash -c \
      "pip install pytm -q && apt-get install -y graphviz -q && python threat_model.py"
    ```

---

## System Description

The **Telehealth Appointment System** has these components:

- **Patient Browser** — Web client used by patients
- **Web Application Server** — Handles appointment booking and video session setup
- **Authentication Service** — Issues JWT tokens, validates credentials
- **Database** — Stores patient records, appointments, provider schedules
- **Video Service** — Third-party integration (e.g., Zoom API)
- **Audit Log Service** — Writes immutable event logs to separate storage

Data flows:
1. Patient → Web App: Login credentials (HTTPS)
2. Web App → Auth Service: Token request (internal, TLS)
3. Auth Service → Web App: JWT token (internal, TLS)
4. Web App → Database: Patient queries (internal, encrypted)
5. Web App → Video Service: Session creation (HTTPS, API key)
6. Web App → Audit Log: Event write (internal, append-only)

---

## Part A — Build the DFD with pytm (25 pts)

Create `threat_model.py` that generates a DFD for the system above:

```python
from pytm import TM, Actor, Process, Datastore, Dataflow, Boundary, Classification

tm = TM("Telehealth Appointment System")
tm.description = "SCIA-425 Lab 02 — STRIDE threat model"
tm.isOrdered = True

# Boundaries
internet = Boundary("Internet")
internal = Boundary("Internal Network")
data_tier = Boundary("Data Tier")

# Elements
patient = Actor("Patient Browser")
patient.inBoundary = internet

web_app = Process("Web Application Server")
web_app.inBoundary = internal

auth_svc = Process("Authentication Service")
auth_svc.inBoundary = internal

database = Datastore("Patient Database")
database.inBoundary = data_tier
database.isEncrypted = True

video_svc = Actor("Video Service (3rd Party)")
video_svc.inBoundary = internet

audit_log = Datastore("Audit Log Service")
audit_log.inBoundary = data_tier

# Dataflows — complete all 6
df1 = Dataflow(patient, web_app, "Login Credentials")
df1.protocol = "HTTPS"
df1.isEncrypted = True
df1.data = Classification.PII

df2 = Dataflow(web_app, auth_svc, "Token Request")
df2.protocol = "TLS"
df2.isEncrypted = True

df3 = Dataflow(auth_svc, web_app, "JWT Token")
df3.protocol = "TLS"
df3.isEncrypted = True

df4 = Dataflow(web_app, database, "Patient Query")
df4.protocol = "TLS"
df4.isEncrypted = True
df4.data = Classification.PII

df5 = Dataflow(web_app, video_svc, "Session Creation")
df5.protocol = "HTTPS"
df5.isEncrypted = True

df6 = Dataflow(web_app, audit_log, "Event Write")
df6.protocol = "TLS"
df6.isEncrypted = True

tm.process()
```

Run it and save the generated DFD image as `dfd.png`. Include it in your report.

**Expected output:** A DFD showing all 6 elements and 6 dataflows across 3 trust boundaries.

---

## Part B — STRIDE Analysis (40 pts)

For each of the 6 system elements, apply all 6 STRIDE categories. Record your findings in `stride_analysis.json`:

```json
[
  {
    "element": "Web Application Server",
    "element_type": "Process",
    "threats": [
      {
        "stride_category": "Spoofing",
        "applies": true,
        "description": "Attacker sends requests impersonating a legitimate patient session using a stolen JWT",
        "likelihood": "Medium",
        "impact": "High",
        "risk_score": 6,
        "mitigation": "Implement JWT binding to client IP and user-agent; short token expiry (15 min)"
      },
      {
        "stride_category": "Tampering",
        "applies": true,
        "description": "Attacker modifies appointment data in transit by intercepting an unencrypted internal connection",
        "likelihood": "Low",
        "impact": "High",
        "risk_score": 4,
        "mitigation": "Enforce TLS on all internal dataflows; validate HMAC signatures on appointment records"
      }
    ]
  }
]
```

**Requirements:**
- Cover all 6 elements
- For each element, evaluate all 6 STRIDE categories (mark `"applies": false` with brief justification if not applicable)
- `risk_score` = likelihood × impact on 1-3 scale (1=Low, 2=Med, 3=High), so range 1–9
- At least **15 total applicable threats** across all elements

---

## Part C — Attack Tree (15 pts)

Choose the **highest risk_score threat** from your STRIDE analysis. Draw an attack tree for it in ASCII or Markdown:

```
GOAL: Attacker reads patient ePHI without authorization
├── OR
│   ├── Steal valid JWT token
│   │   ├── AND
│   │   │   ├── Compromise patient device (malware)
│   │   │   └── Extract token from browser storage
│   │   └── Intercept token in transit
│   │       └── Downgrade TLS connection (requires network position)
│   ├── Exploit SQL injection in patient query endpoint
│   │   ├── Find injectable parameter (automated scanner)
│   │   └── Extract rows from patient table
│   └── Compromise Auth Service
│       ├── Steal signing key
│       └── Forge arbitrary JWT
```

Include this tree in `threat_report.md`. Annotate each leaf node with: `[FEASIBLE/MITIGATED/RESIDUAL RISK]`.

---

## Part D — Threat Report (20 pts)

Write `threat_report.md` with these sections:

1. **System Overview** — 1 paragraph, include the DFD image
2. **Threat Summary Table** — aggregate by STRIDE category: count of applicable threats, avg risk score, top finding
3. **Top 3 Risks** — full description, risk score, recommended mitigation priority
4. **Attack Tree** — from Part C
5. **Residual Risk Statement** — what threats remain after mitigations, and why they are accepted

---

## Verification Script

Run this to check your `stride_analysis.json` is complete:

```python
# verify_lab02.py
import json, sys

with open("stride_analysis.json") as f:
    data = json.load(f)

STRIDE = ["Spoofing","Tampering","Repudiation","Information Disclosure","Denial of Service","Elevation of Privilege"]
ELEMENTS = ["Web Application Server","Authentication Service","Patient Database","Patient Browser","Video Service (3rd Party)","Audit Log Service"]

print(f"Elements analyzed: {len(data)}")
for elem in data:
    cats = {t["stride_category"] for t in elem["threats"]}
    missing = set(STRIDE) - cats
    if missing:
        print(f"  WARN {elem['element']}: missing {missing}")

applicable = [t for e in data for t in e["threats"] if t.get("applies")]
print(f"Total applicable threats: {len(applicable)}")

if len(applicable) < 15:
    print("FAIL: Need at least 15 applicable threats"); sys.exit(1)

high_risk = [t for t in applicable if t.get("risk_score", 0) >= 6]
print(f"High-risk threats (score ≥6): {len(high_risk)}")
print("PASS: stride_analysis.json verified.")
```

```bash
python verify_lab02.py
```

---

## Submission Checklist

- [ ] `threat_model.py` — pytm model (runs without error)
- [ ] `dfd.png` — generated Data Flow Diagram
- [ ] `stride_analysis.json` — verified (15+ applicable threats)
- [ ] `threat_report.md` — all 5 sections present
- [ ] `verify_lab02.py` output showing PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — DFD generated (6 elements, 6 flows, 3 boundaries) | 25 |
| Part B — STRIDE analysis (15+ threats, all elements covered) | 40 |
| Part C — Attack tree (correct structure, annotated leaves) | 15 |
| Part D — Threat report (all 5 sections, professional quality) | 20 |
| **Total** | **100** |
