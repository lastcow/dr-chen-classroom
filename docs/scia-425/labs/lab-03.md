---
title: "Lab 03: Architecture Security Review"
course: SCIA-425
topic: Quality in Architecture and Design
week: 4
difficulty: ⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 03: Architecture Security Review

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 4 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90 minutes |
| **Topic** | Quality in Architecture and Design |
| **Prerequisites** | Python 3.10+, `pip install pytest` |
| **Deliverables** | `findings.json`, `risk_register.py` output, `architecture_review.md` |

---

## Overview

Architecture security review (ASR) identifies design-level flaws before a single line of implementation code is written. Design flaws are the most expensive category of security defect — they require structural changes, not just patches. In this lab you will analyze a **deliberately flawed** e-commerce architecture, map each flaw to the CWE/CAPEC taxonomy, quantify risk, and prescribe prioritized architectural mitigations.

---

## The Flawed Architecture

You are reviewing the proposed architecture for **ShopFast** — a new e-commerce platform handling payment card data. The architecture team has shared this design:

```
┌─────────────────────────────────────────────────────────┐
│                     INTERNET                            │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
              ┌────────▼────────┐
              │   Load Balancer  │  (no WAF)
              └────────┬─────────┘
                       │ HTTP (internal, unencrypted)
         ┌─────────────┼──────────────┐
         │             │              │
    ┌────▼───┐   ┌─────▼──┐   ┌──────▼───┐
    │ API    │   │ Admin  │   │ Payment  │
    │ Server │   │ Panel  │   │ Service  │
    └────┬───┘   └─────┬──┘   └──────┬───┘
         │  shared DB conn    shared DB conn
         └─────────────┼──────────────┘
                  ┌────▼────┐
                  │  MySQL  │  (single DB, all services share
                  │   DB    │   one privileged account: root)
                  └─────────┘

Notes from architect:
- Admin panel accessible on port 8080, no VPN required
- All services use DB user: root / password: shopfast2024
- Internal traffic not encrypted (saves SSL overhead)
- Logs written to same DB as production data
- Payment card numbers stored as plaintext for "easy debugging"
- No input validation — "the frontend handles it"
- Session tokens: MD5(username + timestamp)
```

---

## Part A — Flaw Identification (35 pts)

Identify **at least 8 architectural flaws** in the ShopFast design. For each flaw:

1. Describe the flaw clearly
2. Map it to a **CWE** (Common Weakness Enumeration) ID and name
3. Map it to a **CAPEC** (Common Attack Pattern) ID and name
4. Assign a CVSS base score estimate (0.0–10.0) with justification

Record in `findings.json`:

```json
[
  {
    "id": "F-001",
    "title": "Plaintext Internal Traffic",
    "description": "Internal communication between load balancer and application servers uses HTTP, allowing network-level eavesdropping of all request data including session tokens and ePHI.",
    "cwe_id": "CWE-319",
    "cwe_name": "Cleartext Transmission of Sensitive Information",
    "capec_id": "CAPEC-157",
    "capec_name": "Sniffing Attacks",
    "cvss_score": 7.5,
    "cvss_justification": "Network AV, Low complexity, No privileges required, impacts confidentiality and integrity",
    "component": "Load Balancer → Application Servers",
    "pci_dss_violation": "Requirement 4.2.1"
  }
]
```

**Required CWE categories to include** (at least one each):
- Authentication/credential flaw (CWE-2xx or CWE-5xx)
- Cryptographic flaw (CWE-3xx)
- Access control flaw (CWE-2xx)
- Injection surface (CWE-7xx or CWE-89)
- Session management flaw (CWE-384 or similar)

---

## Part B — Risk Register (25 pts)

Create `risk_register.py` that reads `findings.json` and produces a prioritized risk matrix:

```python
import json

with open("findings.json") as f:
    findings = json.load(f)

# Sort by CVSS descending
findings.sort(key=lambda f: f["cvss_score"], reverse=True)

print("=" * 70)
print(f"{'ID':<8} {'CVSS':>6}  {'Title':<35} {'CWE':<12}")
print("=" * 70)
for f in findings:
    severity = "CRITICAL" if f["cvss_score"] >= 9 else \
               "HIGH" if f["cvss_score"] >= 7 else \
               "MEDIUM" if f["cvss_score"] >= 4 else "LOW"
    print(f"{f['id']:<8} {f['cvss_score']:>6.1f}  {f['title']:<35} {f['cwe_id']:<12}  [{severity}]")

print()
critical = [f for f in findings if f["cvss_score"] >= 9]
high = [f for f in findings if 7 <= f["cvss_score"] < 9]
medium = [f for f in findings if 4 <= f["cvss_score"] < 7]
print(f"Summary: {len(critical)} CRITICAL  {len(high)} HIGH  {len(medium)} MEDIUM")

# PCI DSS violations
pci = [f for f in findings if f.get("pci_dss_violation")]
if pci:
    print(f"\nPCI DSS Violations ({len(pci)}):")
    for f in pci:
        print(f"  {f['id']}: {f['pci_dss_violation']} — {f['title']}")
```

Run:
```bash
python risk_register.py
```

Screenshot the output. You should have at least 2 CRITICAL or HIGH findings.

---

## Part C — Architectural Mitigations (25 pts)

For each finding in `findings.json`, add a `mitigation` field:

```json
{
  "mitigation": {
    "description": "Enforce mutual TLS (mTLS) on all internal service-to-service communication using a service mesh (e.g., Istio) or at minimum TLS 1.3 with certificate pinning between known service pairs.",
    "effort": "High",
    "priority": 1,
    "architectural_pattern": "Defense in Depth",
    "replaces_component": "HTTP internal links → mTLS encrypted channels"
  }
}
```

**Architectural patterns** to apply (from Ch04):
- Defense in Depth
- Least Privilege
- Separation of Concerns
- Fail Secure
- Complete Mediation

Each mitigation must name which pattern it applies and explain why that pattern is appropriate.

---

## Part D — Architecture Review Report (15 pts)

Write `architecture_review.md` with:

1. **Executive Summary** (5 sentences max) — overall risk posture of ShopFast
2. **Findings Table** — all findings sorted by CVSS with severity badges
3. **PCI DSS Compliance Gap Analysis** — which PCI DSS requirements are violated and by which findings
4. **Recommended Architecture Diagram** — describe (in text or ASCII) what the fixed architecture looks like
5. **Remediation Roadmap** — 3 phases: Immediate (≤1 week), Short-term (≤1 month), Long-term (≤1 quarter)

---

## Verification

```bash
python -c "
import json, sys
with open('findings.json') as f:
    data = json.load(f)
assert len(data) >= 8, 'Need 8+ findings'
required_keys = {'id','title','description','cwe_id','cwe_name','capec_id','cvss_score','mitigation'}
for d in data:
    missing = required_keys - set(d.keys())
    assert not missing, f'{d[\"id\"]} missing: {missing}'
scores = [d['cvss_score'] for d in data]
assert max(scores) >= 7.0, 'Expected at least one HIGH/CRITICAL finding'
print(f'PASS: {len(data)} findings, max CVSS {max(scores):.1f}')
"
```

---

## Submission Checklist

- [ ] `findings.json` — 8+ findings, all required fields + mitigations
- [ ] `risk_register.py` output screenshot (2+ HIGH/CRITICAL)
- [ ] `architecture_review.md` — all 5 sections

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — 8+ findings, correct CWE/CAPEC mapping, CVSS scores | 35 |
| Part B — risk_register.py output, correct prioritization | 25 |
| Part C — mitigations with named architectural patterns | 25 |
| Part D — architecture review report, all 5 sections | 15 |
| **Total** | **100** |
