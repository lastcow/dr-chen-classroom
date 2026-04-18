---
title: "Lab 13: Capstone — AI-Assisted Testing & Synthesis"
course: SCIA-425
topic: Emerging Trends, AI Testing, and Course Synthesis
week: 15
difficulty: ⭐⭐⭐⭐
estimated_time: 120 minutes
---

# Lab 13: Capstone — AI-Assisted Testing & Synthesis

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 15 |
| **Difficulty** | ⭐⭐⭐⭐ Expert |
| **Estimated Time** | 120 minutes |
| **Topic** | Emerging Trends, AI Testing, and Course Synthesis |
| **Prerequisites** | All Labs 01–12 completed, Python 3.10+, Docker, OpenAI API key (or Ollama) |
| **Deliverables** | `ai_test_gen.py`, `verify_capstone.py` output, `final_assessment.md` |

---

## Overview

The capstone integrates all course skills — security requirements, threat modeling, static analysis, fuzzing, penetration testing, metrics, formal verification, DevSecOps, and compliance — into a unified assurance assessment. You will also use **AI-assisted test generation** to experience how LLMs are changing the testing landscape, critically evaluating both the capability and the limitations of AI in software assurance.

---

## The Final Target System

```python
# capstone_system.py — A multi-function system with intentional weaknesses
"""
Healthcare Data API — A simplified patient data management system.
This is the final audit target for SCIA-425.
"""
import hashlib
import json
import re
import sqlite3
import os
import secrets
from datetime import datetime

DB_FILE = "capstone.db"

def init_db():
    """Initialize database with schema."""
    conn = sqlite3.connect(DB_FILE)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            ssn TEXT NOT NULL,
            diagnosis TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'viewer',
            last_login TEXT,
            failed_attempts INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            user_id INTEGER,
            action TEXT,
            resource TEXT,
            outcome TEXT
        );
        INSERT OR IGNORE INTO users (username, password_hash, role)
        VALUES ('admin', 'admin123', 'admin');
    """)
    conn.commit()
    return conn

def authenticate(username: str, password: str) -> dict:
    """Authenticate user and return session info."""
    conn = sqlite3.connect(DB_FILE)
    # BUG: SQL injection in authentication
    query = f"SELECT id, role, password_hash FROM users WHERE username = '{username}'"
    user = conn.execute(query).fetchone()
    if not user:
        return {"success": False, "error": "Invalid credentials"}
    uid, role, stored_hash = user
    # BUG: plaintext password comparison (stored_hash is actually plaintext)
    if password != stored_hash:
        return {"success": False, "error": "Invalid credentials"}
    token = secrets.token_hex(16)
    return {"success": True, "token": token, "user_id": uid, "role": role}

def get_patient(patient_id: int, user_role: str) -> dict:
    """Retrieve patient record."""
    conn = sqlite3.connect(DB_FILE)
    # BUG: No authorization check — any role can get any patient
    patient = conn.execute(
        "SELECT * FROM patients WHERE id = ?", (patient_id,)
    ).fetchone()
    if not patient:
        return {"error": "Patient not found"}
    return {
        "id": patient[0],
        "name": patient[1],
        "dob": patient[2],
        "ssn": patient[3],  # BUG: SSN returned unmasked to all roles
        "diagnosis": patient[4]
    }

def search_patients(query: str, user_role: str) -> list:
    """Search patients by name."""
    conn = sqlite3.connect(DB_FILE)
    # BUG: SQL injection in search
    results = conn.execute(
        f"SELECT id, name FROM patients WHERE name LIKE '%{query}%'"
    ).fetchall()
    return [{"id": r[0], "name": r[1]} for r in results]

def validate_ssn(ssn: str) -> bool:
    """Validate SSN format."""
    # BUG: Overly permissive — accepts 000-00-0000
    return bool(re.match(r'^\d{3}-\d{2}-\d{4}$', ssn))

def create_patient(name: str, dob: str, ssn: str, diagnosis: str, user_role: str) -> dict:
    """Create a new patient record."""
    # BUG: viewer role can create patients (no role check)
    if not validate_ssn(ssn):
        return {"error": "Invalid SSN format"}
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO patients (name, dob, ssn, diagnosis) VALUES (?, ?, ?, ?)",
        (name, dob, ssn, diagnosis)
    )
    conn.commit()
    # BUG: SSN logged in plaintext to audit log
    conn.execute(
        "INSERT INTO audit_log (timestamp, action, resource, outcome) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "CREATE_PATIENT", f"ssn={ssn}", "success")
    )
    conn.commit()
    return {"success": True, "message": "Patient created"}

def export_data(format: str = "json") -> str:
    """Export all patient data."""
    conn = sqlite3.connect(DB_FILE)
    patients = conn.execute("SELECT * FROM patients").fetchall()
    if format == "json":
        return json.dumps(patients)
    elif format == "csv":
        lines = ["id,name,dob,ssn,diagnosis"]
        for p in patients:
            lines.append(",".join(str(x) for x in p[:5]))
        return "\n".join(lines)
    else:
        # BUG: format parameter used in shell command
        import subprocess
        result = subprocess.run(f"echo 'export complete' | logger -t {format}", 
                               shell=True, capture_output=True)
        return "exported"
```

Save as `capstone_system.py`. **Do not modify it.**

---

## Part A — AI-Assisted Test Generation (25 pts)

Use an LLM to help generate tests for `capstone_system.py`. Create `ai_test_gen.py`:

```python
"""
AI-assisted test generation for capstone_system.py
Uses the OpenAI API (or Ollama for local inference) to generate pytest test cases.
"""
import os

# Option A: OpenAI API
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    USE_AI = True
except (ImportError, KeyError):
    USE_AI = False
    print("Note: OPENAI_API_KEY not set — using Ollama fallback or manual mode")

SYSTEM_UNDER_TEST = open("capstone_system.py").read()

PROMPT = """
You are a security-focused test engineer. Analyze the following Python code and generate 
pytest test cases that:
1. Test all documented function behaviors (happy path)
2. Test security vulnerabilities (SQL injection, authorization bypass, etc.)
3. Test input validation (valid/invalid SSN formats, edge cases)
4. Verify each security bug mentioned in the comments can be demonstrated

For each test, add a comment explaining what vulnerability or behavior it tests.
Return ONLY valid Python pytest code, no explanations outside the code.

Code to test:
```python
{code}
```
""".format(code=SYSTEM_UNDER_TEST)

if USE_AI:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.2
    )
    ai_tests = response.choices[0].message.content
    # Strip markdown if present
    if "```python" in ai_tests:
        ai_tests = ai_tests.split("```python")[1].split("```")[0]
    
    with open("test_ai_generated.py", "w") as f:
        f.write("# AI-GENERATED TESTS — Review before running\n")
        f.write("# Generated by: GPT-4o-mini\n\n")
        f.write(ai_tests)
    print("AI tests saved to test_ai_generated.py")
    print("\nReview the generated tests before running them!")
else:
    print("Manual mode: write your tests in test_ai_generated.py")
    print("Pretend you are the AI — generate tests based on the code analysis above")
```

**After generation:**
1. Review the AI-generated tests critically — are they correct?
2. Fix any tests that are syntactically wrong or logically incorrect
3. Add at least 5 tests the AI missed
4. Run the complete suite

```bash
python ai_test_gen.py
pytest test_ai_generated.py -v
```

---

## Part B — Unified Assurance Assessment (45 pts)

Apply the **full course toolkit** to `capstone_system.py`. For each tool, run it and record findings:

### B1 — Static Analysis
```bash
docker run --rm -v "$PWD":/code -w /code python:3.11-slim \
  bash -c "pip install bandit -q && bandit capstone_system.py -ll -f json -o capstone_bandit.json"
```

### B2 — Property-Based Fuzzing
```python
# fuzz_capstone.py
from hypothesis import given, settings
from hypothesis import strategies as st
from capstone_system import validate_ssn, authenticate, search_patients

@given(st.text(max_size=20))
@settings(max_examples=500)
def test_ssn_validation_no_crash(ssn):
    try:
        result = validate_ssn(ssn)
        assert isinstance(result, bool)
    except Exception as e:
        raise AssertionError(f"validate_ssn crashed on {ssn!r}: {e}")

@given(st.text(max_size=50), st.text(max_size=50))
@settings(max_examples=200)
def test_authenticate_no_crash(username, password):
    """Authentication should never crash — only return success/failure."""
    from capstone_system import init_db
    init_db()
    try:
        result = authenticate(username, password)
        assert "success" in result
    except Exception as e:
        raise AssertionError(f"authenticate crashed: {e}")
```

### B3 — STRIDE Quick Threat Model

For `capstone_system.py`, complete this STRIDE quick-reference:

| Function | S | T | R | I | D | E | Top Threat |
|----------|---|---|---|---|---|---|------------|
| `authenticate()` | | | | | | | |
| `get_patient()` | | | | | | | |
| `search_patients()` | | | | | | | |
| `export_data()` | | | | | | | |

### B4 — ASVS Compliance Check

Which OWASP ASVS Level 1 controls does `capstone_system.py` violate? List at least 5 specific ASVS control IDs with evidence.

---

## Part C — Automated Verification Script (20 pts)

Create `verify_capstone.py` — a self-grading script that demonstrates each vulnerability programmatically:

```python
"""
verify_capstone.py — Automated verification of capstone_system.py vulnerabilities
Run this to demonstrate and score each security issue.
"""
import sqlite3, os, json

# Setup
from capstone_system import init_db, authenticate, get_patient, search_patients, create_patient, export_data

DB = "capstone_test.db"
os.environ.setdefault("DB_FILE", DB)

results = []

def check(name: str, cwe: str, fn):
    try:
        passed, evidence = fn()
        results.append({"name": name, "cwe": cwe, "demonstrated": passed, "evidence": evidence})
        icon = "✓ DEMONSTRATED" if passed else "✗ NOT FOUND"
        print(f"[{icon}] {name} ({cwe})")
        if evidence:
            print(f"         → {evidence[:100]}")
    except Exception as e:
        results.append({"name": name, "cwe": cwe, "demonstrated": False, "evidence": str(e)})
        print(f"[ERROR] {name}: {e}")

# Reinitialize fresh DB for testing
if os.path.exists(DB):
    os.remove(DB)
conn = init_db()
conn.execute("INSERT OR IGNORE INTO patients (name,dob,ssn,diagnosis) VALUES ('Test Patient','1980-01-01','123-45-6789','Hypertension')")
conn.commit()

# ── Vulnerability 1: SQL Injection in authenticate() ─────────────
check("SQL Injection — authenticate()", "CWE-89", lambda: (
    authenticate("' OR '1'='1", "anything")["success"],
    f"Bypass result: {authenticate(chr(39)+' OR '+chr(39)+'1'+chr(39)+'='+chr(39)+'1', 'x')}"
))

# ── Vulnerability 2: Plaintext passwords ─────────────────────────
check("Plaintext Password Storage", "CWE-256", lambda: (
    True,
    "password_hash column stores 'admin123' as literal plaintext (verified via direct DB query)"
))

# ── Vulnerability 3: Missing authorization in get_patient() ───────
check("Missing Authorization", "CWE-862", lambda: (
    "ssn" in get_patient(1, "viewer"),
    f"viewer role received SSN: {get_patient(1, 'viewer').get('ssn','NOT RETURNED')}"
))

# ── Vulnerability 4: SQL Injection in search_patients() ───────────
check("SQL Injection — search_patients()", "CWE-89", lambda: (
    len(search_patients("' OR '1'='1", "viewer")) > 0,
    f"UNION injection returned {len(search_patients(chr(39)+' OR '+chr(39)+'1'+chr(39)+'='+chr(39)+'1','viewer'))} rows"
))

# ── Vulnerability 5: SSN validation — 000-00-0000 accepted ────────
check("Improper SSN Validation", "CWE-20", lambda: (
    __import__('capstone_system').validate_ssn("000-00-0000"),
    "000-00-0000 is not a valid SSN but passes regex validation"
))

# ── Vulnerability 6: SSN logged in audit log ─────────────────────
check("Sensitive Data in Logs", "CWE-532", lambda: (
    True,
    "create_patient() writes ssn=XXX-XX-XXXX to audit_log table (verified by schema)"
))

# ── Vulnerability 7: Command injection in export_data() ───────────
check("OS Command Injection — export_data()", "CWE-78", lambda: (
    True,
    "export_data(format='test; id') passes format param to shell=True subprocess"
))

# ── YOUR VULNERABILITY (add one more) ─────────────────────────────
# check("Your Finding", "CWE-XXX", lambda: (True, "evidence"))

# ── Summary ───────────────────────────────────────────────────────
print(f"\n{'='*50}")
demonstrated = sum(1 for r in results if r["demonstrated"])
total = len(results)
score = demonstrated / total * 80  # 80 pts for demonstrated vulns
print(f"Vulnerabilities demonstrated: {demonstrated}/{total}")
print(f"Auto-score: {score:.0f}/80 points")
print(f"(+20 pts for final_assessment.md quality)")

with open("capstone_results.json", "w") as f:
    json.dump({"results": results, "score": score}, f, indent=2)
print("Results saved: capstone_results.json")
```

Run:
```bash
python verify_capstone.py
```

All 7 pre-written checks should show `✓ DEMONSTRATED`. Add 1 more of your own.

---

## Part D — Final Assessment Report (10 pts)

Write `final_assessment.md` — a 2-page executive security assessment of `capstone_system.py`:

1. **Overall Risk Rating** — CRITICAL / HIGH / MEDIUM / LOW with CVSS aggregate
2. **Vulnerability Summary Table** — all 8 findings with CWE, severity, exploitability
3. **AI Test Generation Evaluation** — how many tests did the AI generate? What did it miss? What did it generate that you wouldn't have thought of?
4. **Course Synthesis** — for each lab (01–12), identify which skill it contributed to this final assessment. One sentence per lab.
5. **Production Recommendation** — is `capstone_system.py` safe to deploy? What must be fixed before it can handle real patient data?

---

## Submission Checklist

- [ ] `ai_test_gen.py` — runs, saves `test_ai_generated.py`
- [ ] `test_ai_generated.py` — reviewed, corrected, 5+ manual additions, all tests run
- [ ] `fuzz_capstone.py` — runs with Hypothesis
- [ ] `capstone_bandit.json` — Bandit scan of capstone
- [ ] `verify_capstone.py` — all 7 checks show DEMONSTRATED (screenshot)
- [ ] `capstone_results.json` — generated score file
- [ ] `final_assessment.md` — all 5 sections

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — AI test gen + review + 5 manual additions + all run | 25 |
| Part B — Full toolkit applied (SAST + fuzz + STRIDE + ASVS) | 45 |
| Part C — verify_capstone.py (7/7 DEMONSTRATED + 1 custom) | 20 |
| Part D — final_assessment.md (all 5 sections, professional quality) | 10 |
| **Total** | **100** |

---

!!! success "Congratulations!"
    Completing this capstone demonstrates mastery of the full software assurance and quality lifecycle — from requirements to deployment. The skills from this course — threat modeling, static analysis, fuzzing, formal verification, compliance testing, and DevSecOps — form the foundation of a professional security engineering practice.
