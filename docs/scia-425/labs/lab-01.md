---
title: "Lab 01: Security Requirements & Misuse Cases"
course: SCIA-425
topic: Security Requirements and Specifications
week: 2
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 01: Security Requirements & Misuse Cases

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 2 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 75 minutes |
| **Topic** | Security Requirements and Specifications |
| **Prerequisites** | Python 3.10+, `pip install jsonschema pytest` |
| **Deliverables** | `requirements.json`, `misuse_cases.json`, `test_requirements.py` passing output |

---

## Overview

Security requirements are the most neglected — and most expensive to ignore — phase of software development. A missing or incorrect requirement cannot be patched out later. In this lab you will practice writing structured security requirements in a machine-readable format, model adversarial misuse cases for each requirement, and validate the requirement set automatically using a Python schema checker.

The target system is a **Healthcare Patient Portal** — a web application that allows patients to view lab results, schedule appointments, and message their care team.

---

!!! info "No special accounts needed"
    This lab runs entirely locally with Python. No cloud services required.

---

## Part A — Taxonomy Review (10 pts)

Before writing requirements, categorize each of the following into **Functional**, **Non-Functional**, or **Constraint**:

| # | Requirement Statement | Category |
|---|----------------------|----------|
| 1 | The system shall authenticate all API requests using OAuth 2.0 Bearer tokens | |
| 2 | The system shall rate-limit login attempts to 5 per IP per minute | |
| 3 | All ePHI must be encrypted at rest per HIPAA §164.312(a)(2)(iv) | |
| 4 | The system shall log every authentication event with timestamp, user ID, and outcome | |
| 5 | Session tokens shall expire after 30 minutes of inactivity | |
| 6 | The system shall maintain 99.5% availability under 10 Gbps DDoS conditions | |

Write your answers in `answers.md`.

---

## Part B — Write Structured Requirements (30 pts)

Create a file `requirements.json` with at least **8 security requirements** for the Patient Portal. Each requirement must follow this schema:

```json
{
  "id": "SR-001",
  "type": "functional",
  "category": "authentication",
  "statement": "The system shall authenticate all API requests using OAuth 2.0 Bearer tokens validated against the authorization server.",
  "rationale": "Unauthenticated API access exposes ePHI to unauthorized parties (HIPAA §164.312(d)).",
  "regulation": "HIPAA §164.312(d)",
  "testable": true,
  "acceptance_criteria": "A request without a valid Bearer token returns HTTP 401 within 200ms."
}
```

**Required categories to cover** (at least one requirement each):
- `authentication`
- `authorization`
- `encryption`
- `audit_logging`
- `input_validation`
- `session_management`

**Schema validator** — run this to check your file:

```python
# validate_requirements.py
import json, jsonschema, sys

SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "type", "category", "statement", "rationale", "testable", "acceptance_criteria"],
        "properties": {
            "id": {"type": "string", "pattern": "^SR-\\d{3}$"},
            "type": {"enum": ["functional", "non-functional", "constraint"]},
            "category": {"type": "string"},
            "statement": {"type": "string", "minLength": 20},
            "rationale": {"type": "string", "minLength": 10},
            "testable": {"type": "boolean"},
            "acceptance_criteria": {"type": "string", "minLength": 10}
        }
    },
    "minItems": 8
}

with open("requirements.json") as f:
    data = json.load(f)

jsonschema.validate(data, SCHEMA)

# Check category coverage
required_cats = {"authentication","authorization","encryption","audit_logging","input_validation","session_management"}
found_cats = {r["category"] for r in data}
missing = required_cats - found_cats
if missing:
    print(f"FAIL: Missing categories: {missing}")
    sys.exit(1)

# Check all are testable
non_testable = [r["id"] for r in data if not r["testable"]]
if non_testable:
    print(f"WARNING: Non-testable requirements: {non_testable}")

print(f"PASS: {len(data)} requirements validated, all 6 categories covered.")
```

```bash
python validate_requirements.py
```

---

## Part C — Misuse Case Modeling (30 pts)

For **each** of the 6 required categories, write one misuse case in `misuse_cases.json`. A misuse case describes how an adversary attempts to violate the corresponding requirement.

```json
[
  {
    "id": "MC-001",
    "targets_requirement": "SR-001",
    "actor": "External Attacker",
    "goal": "Access patient lab results without credentials",
    "attack_steps": [
      "Discover API endpoint via directory brute-force",
      "Send API request with no Authorization header",
      "Receive 200 OK response with ePHI data"
    ],
    "likelihood": "High",
    "impact": "Critical",
    "mitigations": [
      "Enforce Bearer token validation on all routes (SR-001)",
      "Return 401 with no data disclosure on missing/invalid token"
    ]
  }
]
```

**Grading criteria for each misuse case:**
- Realistic adversary goal ✓
- At least 3 concrete attack steps ✓
- Correct likelihood/impact rating (justify in `answers.md`) ✓
- At least 2 mitigations linking back to SR- IDs ✓

---

## Part D — Automated Requirement Tests (20 pts)

Write `test_requirements.py` — a pytest suite that validates your `requirements.json` programmatically. You must include these test functions:

```python
import json, pytest

@pytest.fixture
def reqs():
    with open("requirements.json") as f:
        return json.load(f)

def test_minimum_count(reqs):
    assert len(reqs) >= 8, "Must have at least 8 requirements"

def test_unique_ids(reqs):
    ids = [r["id"] for r in reqs]
    assert len(ids) == len(set(ids)), "Requirement IDs must be unique"

def test_all_testable(reqs):
    non_testable = [r["id"] for r in reqs if not r["testable"]]
    assert not non_testable, f"All requirements must be testable: {non_testable}"

def test_category_coverage(reqs):
    required = {"authentication","authorization","encryption","audit_logging","input_validation","session_management"}
    found = {r["category"] for r in reqs}
    assert required.issubset(found), f"Missing: {required - found}"

def test_acceptance_criteria_length(reqs):
    short = [r["id"] for r in reqs if len(r.get("acceptance_criteria","")) < 20]
    assert not short, f"Acceptance criteria too short: {short}"

# YOUR ADDITIONAL TEST (required for full credit):
# Add at least one test of your own that checks something meaningful
# about your requirement set. Comment explaining what and why.
```

Run:
```bash
pytest test_requirements.py -v
```

**All tests must pass. Screenshot your passing output.**

---

## Submission Checklist

- [ ] `answers.md` — Part A category answers
- [ ] `requirements.json` — 8+ requirements, schema-valid
- [ ] `misuse_cases.json` — 6 misuse cases, one per category
- [ ] `test_requirements.py` — all tests passing (screenshot)
- [ ] `validate_requirements.py` output showing PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Taxonomy (6 correct) | 10 |
| Part B — requirements.json (schema-valid, 8+, all categories) | 30 |
| Part C — Misuse cases (6 cases, realistic, linked mitigations) | 30 |
| Part D — pytest suite (all tests pass + custom test) | 20 |
| Overall quality & professional writing | 10 |
| **Total** | **100** |
