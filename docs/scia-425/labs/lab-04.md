---
title: "Lab 04: Static Analysis & Code Inspection"
course: SCIA-425
topic: Static Analysis and Code Inspection
week: 5
difficulty: ⭐⭐
estimated_time: 80 minutes
---

# Lab 04: Static Analysis & Code Inspection

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 5 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 80 minutes |
| **Topic** | Static Analysis and Code Inspection |
| **Prerequisites** | Docker installed and running |
| **Deliverables** | `bandit_report.json`, `semgrep_report.json`, `findings_analysis.md`, fixed `secure_app.py` |

---

## Overview

Static analysis examines source code without executing it, finding security vulnerabilities, code quality defects, and policy violations at zero runtime cost. In this lab you will run **Bandit** and **Semgrep** on a deliberately vulnerable Python web application, analyze and triage their findings, then produce a remediated version that passes both tools with zero High-severity findings.

All tools run inside Docker — no local installation needed.

---

## Setup — The Vulnerable Application

Create `vulnerable_app.py`:

```python
# vulnerable_app.py — INTENTIONALLY INSECURE — FOR LAB USE ONLY
import sqlite3
import subprocess
import hashlib
import pickle
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = "hardcoded_secret_key_12345"  # CWE-798
DB_PATH = "/tmp/users.db"

def get_db():
    return sqlite3.connect(DB_PATH)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    # SQL injection: CWE-89
    conn = get_db()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = conn.execute(query).fetchone()
    if result:
        return jsonify({"status": "ok", "user": result[0]})
    return jsonify({"status": "fail"}), 401

@app.route("/search")
def search():
    term = request.args.get("q", "")
    # Command injection: CWE-78
    output = subprocess.check_output(f"grep -r {term} /var/log/app/", shell=True)
    return output.decode()

@app.route("/hash")
def make_hash():
    data = request.args.get("data", "")
    # Weak hash: CWE-327
    return hashlib.md5(data.encode()).hexdigest()

@app.route("/load_session")
def load_session():
    session_data = request.cookies.get("session", "")
    # Insecure deserialization: CWE-502
    obj = pickle.loads(bytes.fromhex(session_data))
    return str(obj)

@app.route("/ping")
def ping():
    host = request.args.get("host", "localhost")
    # OS command injection: CWE-78
    result = os.popen(f"ping -c 1 {host}").read()
    return result

@app.route("/admin")
def admin():
    # Missing authentication: CWE-306
    # Returns all users
    conn = get_db()
    users = conn.execute("SELECT username, password FROM users").fetchall()
    return jsonify(users)

if __name__ == "__main__":
    app.run(debug=True)  # Debug mode in production: CWE-94
```

---

## Part A — Run Bandit (25 pts)

Bandit is a Python-specific SAST tool that checks for common security issues.

```bash
# Run bandit in Docker, save JSON report
docker run --rm \
  -v "$PWD":/code \
  -w /code \
  python:3.11-slim \
  bash -c "pip install bandit -q && bandit -r vulnerable_app.py -f json -o bandit_report.json -ll && echo DONE"

# View summary
docker run --rm -v "$PWD":/code -w /code python:3.11-slim \
  bash -c "pip install bandit -q && bandit -r vulnerable_app.py -ll"
```

**Analysis tasks for `findings_analysis.md`:**

1. How many HIGH severity issues did Bandit find?
2. For each HIGH finding, record:
   - Bandit test ID (e.g., B608)
   - CWE reference
   - Exact line number
   - Why this is exploitable (1–2 sentences)
3. Were there any False Positives? Justify.

---

## Part B — Run Semgrep (25 pts)

Semgrep finds both language-specific and OWASP patterns across many languages.

```bash
# Run semgrep with Python security ruleset
docker run --rm \
  -v "$PWD":/src \
  returntocorp/semgrep \
  semgrep --config "p/python" --config "p/owasp-top-ten" \
  --json --output /src/semgrep_report.json \
  /src/vulnerable_app.py

# Human-readable summary
docker run --rm \
  -v "$PWD":/src \
  returntocorp/semgrep \
  semgrep --config "p/python" --config "p/owasp-top-ten" \
  /src/vulnerable_app.py
```

**Analysis tasks (add to `findings_analysis.md`):**

1. How many Semgrep rules matched?
2. Which OWASP Top 10 categories are represented?
3. Did Semgrep find anything Bandit missed? (Compare the two reports)
4. Did Bandit find anything Semgrep missed?

---

## Part C — Findings Triage (20 pts)

In `findings_analysis.md`, create a **consolidated findings table** merging both tools:

| Finding ID | Tool | Severity | CWE | Line | Vulnerability Type | Exploitability | Priority |
|-----------|------|----------|-----|------|-------------------|----------------|----------|
| F-01 | Bandit | HIGH | CWE-89 | 24 | SQL Injection | Critical — direct string interpolation in query | P1 |
| ... | | | | | | | |

**Triage rules:**
- P1: Directly exploitable, HIGH severity from either tool
- P2: Exploitable under specific conditions, MEDIUM severity
- P3: Defense-in-depth or informational (LOW)

Expected: at least 6 distinct vulnerabilities mapped.

---

## Part D — Remediate the Code (30 pts)

Create `secure_app.py` — a fixed version of `vulnerable_app.py`. Fix **all P1 findings** and as many P2 as possible.

Required fixes:
- SQL injection → parameterized queries
- Command injection → remove `shell=True`, use argument lists, allowlist validation
- Hardcoded secret → read from `os.environ`
- Weak hash → use `hashlib.sha256` or `bcrypt` for passwords
- Insecure deserialization → replace pickle with `json`
- Missing auth on `/admin` → add API key check from environment variable
- Debug mode → `app.run(debug=False)` or use env variable

After fixing, verify both tools pass:

```bash
# Bandit must report zero HIGH severity
docker run --rm -v "$PWD":/code -w /code python:3.11-slim \
  bash -c "pip install bandit -q && bandit -r secure_app.py -ll"

# Semgrep must show zero ERROR-level matches
docker run --rm -v "$PWD":/src returntocorp/semgrep \
  semgrep --config "p/python" --config "p/owasp-top-ten" /src/secure_app.py
```

**Screenshot both tool outputs on `secure_app.py` showing clean (or reduced) results.**

---

## Part E — Additional Challenge (bonus 10 pts)

Write a custom Semgrep rule `custom_rule.yaml` that detects the specific pattern of using `os.popen()` with user-controlled input:

```yaml
rules:
  - id: os-popen-user-input
    pattern: os.popen(... + request.args.get(...) + ...)
    message: "os.popen with user input enables OS command injection (CWE-78)"
    languages: [python]
    severity: ERROR
```

Test it:
```bash
docker run --rm -v "$PWD":/src returntocorp/semgrep \
  semgrep --config /src/custom_rule.yaml /src/vulnerable_app.py
```

---

## Submission Checklist

- [ ] `vulnerable_app.py` — original (do not modify)
- [ ] `bandit_report.json` — Bandit output
- [ ] `semgrep_report.json` — Semgrep output
- [ ] `findings_analysis.md` — triage table + analysis (Parts A, B, C)
- [ ] `secure_app.py` — remediated version
- [ ] Screenshots: Bandit + Semgrep on `secure_app.py`

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Bandit analysis, findings correctly described | 25 |
| Part B — Semgrep analysis, OWASP mapping, tool comparison | 25 |
| Part C — Consolidated triage table (6+ findings, correct priorities) | 20 |
| Part D — secure_app.py (all P1 fixed, tools show improvement) | 30 |
| Part E — Custom Semgrep rule (bonus) | +10 |
| **Total** | **100** |
