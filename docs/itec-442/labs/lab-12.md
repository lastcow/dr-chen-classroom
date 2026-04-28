---
title: "Lab 12: E-Government Service Analysis"
course: ITEC-442
topic: E-Government & Digital Public Services
week: 12
difficulty: ⭐⭐
estimated_time: 70 minutes
---

# Lab 12: E-Government Service Analysis

| Field | Details |
|---|---|
| **Course** | ITEC-442 — Electronic Commerce |
| **Week** | 12 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 70 minutes |
| **Topic** | E-Government & Digital Public Services |
| **Prerequisites** | Python 3.10+, `pip install requests` |
| **Deliverables** | `egov_analysis.md`, `accessibility_checker.py`, `improvement_proposal.md` |

---

## Overview

Governments are among the largest digital service providers — processing tax returns, vehicle registrations, benefit applications, and permit requests at massive scale with strict equity requirements. Unlike commercial e-commerce, government services must serve everyone including elderly, disabled, rural, and low-income citizens who may lack broadband, smartphones, or digital literacy. In this lab you will evaluate two real government digital services against usability, accessibility, and equity standards, then propose concrete improvements.

---

## Part A — Select Your Services (5 pts)

Choose **two government digital services** from different levels (federal, state, local, or international):

**Federal options:**
- IRS Free File (irs.gov/freefile)
- Social Security My Account (ssa.gov/myaccount)
- FAFSA (studentaid.gov)
- USPS Informed Delivery (informeddelivery.usps.com)
- USA.gov services

**State/Local options:**
- Your state's DMV online renewal
- State unemployment benefits portal
- City/county business license application
- State job board
- Voter registration portal

Document in `egov_analysis.md`:
- Service 1: URL, purpose, primary user group, transaction volume (if known)
- Service 2: URL, purpose, primary user group, transaction volume (if known)
- Why you chose these two for comparison

---

## Part B — Usability Evaluation (25 pts)

For **each service**, complete the following usability evaluation. Visit as a first-time user (incognito mode, no account) and document your experience:

```markdown
## Service: [Name]

### Task Completion Test
**Task:** [e.g., "Find out what documents I need to renew my driver's license online"]
**Time to complete:** ___ minutes
**Successful?** Yes / No / Partially
**Obstacles encountered:** ...

### Findability Assessment
- How many clicks from the home page to the primary service? ___
- Is the service name recognizable to a non-expert citizen?
- Is there a clear search function?
- Does Google find the right page if you search "[agency] + [service]"?

### Form Design Evaluation
- Number of form fields on the primary form: ___
- Are fields labeled clearly (not just placeholder text)?
- Are error messages helpful or cryptic?
- Can you save progress and return?
- Is there a progress indicator?

### Trust & Clarity
- Is the official government ownership clear? (.gov domain, official seal)
- Are fees stated clearly before you begin?
- Is the expected processing time communicated?
- Is there a status tracking mechanism?

### Mobile Responsiveness
- Does the service work on mobile?
- Are form fields tap-friendly?
- Is the service accessible without downloading an app?

### Overall Usability Score: ___/25
```

---

## Part C — Accessibility Checker (25 pts)

Build `accessibility_checker.py` — an automated accessibility and performance audit:

```python
# accessibility_checker.py
import requests
import re
from urllib.parse import urlparse

def check_accessibility(url: str) -> dict:
    """Basic automated accessibility checks via passive HTML inspection."""
    results = {"url": url, "checks": {}, "score": 0, "max_score": 0}

    try:
        resp = requests.get(url, timeout=15,
                           headers={"User-Agent": "Mozilla/5.0 (Accessibility Audit)"})
        html = resp.text
        headers = resp.headers
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return results

    checks = []

    def check(name: str, passed: bool, weight: int = 1, note: str = ""):
        icon = "✓" if passed else "✗"
        checks.append({"name": name, "passed": passed, "weight": weight, "note": note})
        results["max_score"] += weight
        if passed:
            results["score"] += weight
        print(f"  {icon} [{weight}pt] {name}" + (f" — {note}" if note else ""))

    print(f"\n{'='*60}")
    print(f"Accessibility Audit: {url}")
    print(f"{'='*60}")
    print(f"HTTP Status: {resp.status_code}\n")

    # ── Basic HTML Structure ───────────────────────────────────────
    print("HTML Structure:")
    check("Has <html lang> attribute",
          bool(re.search(r'<html[^>]+lang=', html, re.I)), 2,
          "Required for screen readers")
    check("Has <title> tag",
          bool(re.search(r'<title>[^<]+</title>', html, re.I)), 1)
    check("Has <main> landmark",
          bool(re.search(r'<main', html, re.I)), 2,
          "WCAG 2.1 landmark regions")
    check("Has <nav> landmark",
          bool(re.search(r'<nav', html, re.I)), 1)
    check("Has skip navigation link",
          bool(re.search(r'skip.*(nav|content|main)', html, re.I)), 2,
          "Critical for keyboard-only users")

    # ── Images & Media ────────────────────────────────────────────
    print("\nImages & Media:")
    img_tags = re.findall(r'<img[^>]+>', html, re.I)
    imgs_with_alt = sum(1 for img in img_tags if 'alt=' in img.lower())
    check(f"Images have alt text ({imgs_with_alt}/{len(img_tags)})",
          imgs_with_alt == len(img_tags) or len(img_tags) == 0, 3,
          f"{len(img_tags)} images found")

    # ── Forms ─────────────────────────────────────────────────────
    print("\nForms:")
    inputs = re.findall(r'<input[^>]+>', html, re.I)
    labels = re.findall(r'<label[^>]+>', html, re.I)
    check("Form labels present",
          len(labels) >= len([i for i in inputs if 'type="hidden"' not in i.lower()]),
          3, f"{len(inputs)} inputs, {len(labels)} labels")
    check("No autocomplete=off on form fields",
          'autocomplete="off"' not in html.lower(), 1,
          "Blocks password managers")

    # ── Security & Privacy ────────────────────────────────────────
    print("\nSecurity Headers:")
    check("HTTPS", url.startswith("https://"), 3)
    check("HSTS header",
          "Strict-Transport-Security" in headers, 2)
    check("Content-Security-Policy",
          "Content-Security-Policy" in headers, 2)
    check(".gov or .mil domain",
          urlparse(url).netloc.endswith((".gov", ".mil")), 2,
          "Official government domain")

    # ── Performance Hints ─────────────────────────────────────────
    print("\nPerformance:")
    check("Page under 500KB",
          len(html) < 500_000, 1,
          f"HTML size: {len(html)/1024:.0f}KB")
    check("No inline scripts (CSP-friendly)",
          len(re.findall(r'<script[^>]*>(?!src)', html, re.I)) < 5, 1)

    results["checks"] = checks
    pct = results["score"] / results["max_score"] * 100 if results["max_score"] else 0

    print(f"\n{'='*40}")
    print(f"Score: {results['score']}/{results['max_score']} ({pct:.0f}%)")
    if pct >= 80:   print("Rating: ACCESSIBLE ✓")
    elif pct >= 60: print("Rating: PARTIAL ⚠")
    else:           print("Rating: NEEDS WORK ✗")

    return results


if __name__ == "__main__":
    # Run on both your chosen services
    services = [
        "https://www.irs.gov/filing/free-file-do-your-federal-taxes-for-free",
        "https://www.ssa.gov/myaccount/",
    ]
    for url in services:
        check_accessibility(url)
```

Run against your two chosen services and screenshot the results.

---

## Part D — Equity & Digital Divide Assessment (20 pts)

In `egov_analysis.md`, assess each service against these equity dimensions:

**1. Connectivity Equity**
- Does the service require high-speed broadband? (test with browser throttling to "Slow 3G")
- Is there a phone alternative (call center, offline form)?
- What happens if the internet goes down during the transaction?

**2. Device Equity**
- Does it work on an 8-year-old Android phone?
- Does it require JavaScript to function? (try with JS disabled)
- Does it require a specific browser?

**3. Literacy Equity**
- What is the reading level of instructions? (Use an online readability checker — target: 6th grade)
- Is content available in languages other than English?
- Are there video/audio instructions?

**4. Identity Equity**
- Does identity verification create barriers? (e.g., ID.me requires face scan)
- What happens if a citizen lacks a credit history (used by some ID verification systems)?
- Are non-binary gender options available on forms?

**5. Score & Compare**

| Equity Dimension | Service 1 | Service 2 |
|-----------------|:---------:|:---------:|
| Connectivity | /5 | /5 |
| Device | /5 | /5 |
| Literacy | /5 | /5 |
| Identity | /5 | /5 |
| **Total** | /20 | /20 |

---

## Part E — Improvement Proposal (25 pts)

Write `improvement_proposal.md` — a professional service design proposal for **one** of your two chosen services.

Structure:

```markdown
# Digital Service Improvement Proposal
**Service:** [Name & URL]
**Author:** [Your name]
**Date:** [Date]

## Executive Summary (100 words)
Current state, key problems, proposed direction, expected impact.

## Problem Statement
Specific, evidence-based description of what is failing and for whom.
Include: affected user groups, frequency of failure, impact.

## Proposed Improvements

### Improvement 1: [Name]
- Problem it solves:
- Proposed solution:
- Implementation effort: Low/Medium/High
- Expected impact: [metric change expected]
- Precedent: [another government/private service that does this well]

### Improvement 2: ...
### Improvement 3: ...

## Equity Impact Assessment
For each improvement, does it:
- Reduce or increase the digital divide?
- Help or harm non-English speakers?
- Require new hardware/connectivity?

## Success Metrics
How will you know if the improvements worked?
| Metric | Current | Target | Timeframe |
|--------|---------|--------|-----------|
| Task completion rate | ? | ≥85% | 6 months |
| ... | | | |

## Implementation Roadmap
Phase 1 (0–3 months): Quick wins
Phase 2 (3–9 months): Core improvements
Phase 3 (9–18 months): Strategic transformation
```

---

## Submission Checklist

- [ ] `egov_analysis.md` — Parts A, B, D complete
- [ ] `accessibility_checker.py` — runs against both services, output screenshot
- [ ] `improvement_proposal.md` — Part E complete (professional proposal)

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Service selection with rationale | 5 |
| Part B — Usability evaluation (both services, task test + all dimensions) | 25 |
| Part C — accessibility_checker.py (runs on both, results screenshot) | 25 |
| Part D — Equity assessment (all 4 dimensions, both services scored) | 20 |
| Part E — Improvement proposal (professional format, 3 improvements, roadmap) | 25 |
| **Total** | **100** |
