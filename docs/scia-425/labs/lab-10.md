---
title: "Lab 10: DevSecOps Pipeline"
course: SCIA-425
topic: DevSecOps — Integrating Assurance into Pipelines
week: 12
difficulty: ⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 10: DevSecOps Pipeline

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 12 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90 minutes |
| **Topic** | DevSecOps — Integrating Assurance into Pipelines |
| **Prerequisites** | Docker, Git, GitHub account (free), `pip install bandit safety` |
| **Deliverables** | `.github/workflows/devsecops.yml`, pipeline run screenshot, `pipeline_analysis.md` |

---

## Overview

DevSecOps shifts security left by automating security gates inside CI/CD pipelines. Every pull request becomes a security checkpoint. In this lab you will build a **GitHub Actions DevSecOps pipeline** that automatically runs SAST, dependency scanning, secrets detection, and a policy gate — and fails the build if any gate is violated.

---

## Setup — Create Your Repository

```bash
# Create a new GitHub repo for this lab
# Option A: via GitHub web UI → New Repository → "scia425-lab10"
# Option B: via gh CLI if installed
gh repo create scia425-lab10 --private --clone
cd scia425-lab10
```

Create a simple Python application to protect:

```bash
mkdir -p src tests
```

`src/app.py`:
```python
import os
import sqlite3
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("app.db")
    return conn

@app.route("/users/<user_id>")
def get_user(user_id):
    conn = get_db()
    # Intentionally vulnerable — for pipeline to catch
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = conn.execute(query).fetchone()
    return jsonify(result)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

if __name__ == "__main__":
    app.run()
```

`requirements.txt`:
```
flask==2.3.3
requests==2.28.0
cryptography==38.0.4
```

!!! warning "Intentional vulnerabilities"
    `src/app.py` has a SQL injection and `requirements.txt` has outdated/vulnerable packages — intentionally. Your pipeline should catch these automatically.

---

## Part A — Build the DevSecOps Pipeline (50 pts)

Create `.github/workflows/devsecops.yml`:

```yaml
name: DevSecOps Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # ── Gate 1: SAST — Static Application Security Testing ─────────
  sast:
    name: "🔍 SAST — Bandit"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Bandit
        run: pip install bandit

      - name: Run Bandit SAST
        run: |
          bandit -r src/ -f json -o bandit-report.json -ll || true
          bandit -r src/ -ll  # human-readable output
          # Fail if HIGH severity issues found
          python -c "
          import json, sys
          with open('bandit-report.json') as f:
              report = json.load(f)
          highs = [r for r in report.get('results',[]) if r['issue_severity'] == 'HIGH']
          if highs:
              print(f'PIPELINE GATE FAILED: {len(highs)} HIGH severity issues found')
              for h in highs:
                  print(f'  [{h[\"issue_severity\"]}] {h[\"issue_text\"]} (line {h[\"line_number\"]})')
              sys.exit(1)
          print(f'SAST GATE PASSED: No HIGH severity issues')
          "

      - name: Upload SAST Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: bandit-report
          path: bandit-report.json

  # ── Gate 2: Dependency Scanning ────────────────────────────────
  dependency-scan:
    name: "📦 Dependency Scan — Safety"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Safety
        run: pip install safety

      - name: Scan Dependencies
        run: |
          pip install -r requirements.txt
          safety check --json --output safety-report.json || true
          safety check  # human-readable
          # Fail on CRITICAL vulnerabilities
          python -c "
          import json, sys
          try:
              with open('safety-report.json') as f:
                  data = json.load(f)
              vulns = data.get('vulnerabilities', [])
              critical = [v for v in vulns if v.get('severity','').upper() == 'CRITICAL']
              if critical:
                  print(f'DEPENDENCY GATE FAILED: {len(critical)} CRITICAL vulnerabilities')
                  for v in critical:
                      print(f'  {v[\"package_name\"]} {v[\"analyzed_version\"]}: {v[\"vulnerability_id\"]}')
                  sys.exit(1)
              print(f'DEPENDENCY GATE PASSED (found {len(vulns)} non-critical issues)')
          except Exception as e:
              print(f'Note: {e}')
          "

      - name: Upload Dependency Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: safety-report
          path: safety-report.json

  # ── Gate 3: Secrets Detection ───────────────────────────────────
  secrets-scan:
    name: "🔑 Secrets Detection — Gitleaks"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # full history for Gitleaks

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # ── Gate 4: Policy Gate — All must pass ─────────────────────────
  policy-gate:
    name: "🚦 Policy Gate"
    runs-on: ubuntu-latest
    needs: [sast, dependency-scan, secrets-scan]
    if: always()
    steps:
      - name: Evaluate Gates
        run: |
          SAST="${{ needs.sast.result }}"
          DEPS="${{ needs.dependency-scan.result }}"
          SECRETS="${{ needs.secrets-scan.result }}"

          echo "Gate Results:"
          echo "  SAST:         $SAST"
          echo "  Dependencies: $DEPS"
          echo "  Secrets:      $SECRETS"

          if [ "$SAST" != "success" ] || [ "$DEPS" != "success" ] || [ "$SECRETS" != "success" ]; then
            echo ""
            echo "POLICY GATE FAILED — Build blocked from merging to main"
            exit 1
          fi

          echo ""
          echo "ALL GATES PASSED — Safe to merge"
```

**Commit and push to trigger the pipeline:**
```bash
git add .
git commit -m "feat: add DevSecOps pipeline + intentionally vulnerable app"
git push origin main
```

Watch the Actions tab on GitHub. Screenshot the failing pipeline (the SAST gate should fail due to SQL injection).

---

## Part B — Fix and Re-run (20 pts)

Create `src/app_secure.py` with the SQL injection fixed using parameterized queries. Update the pipeline to scan `src/app_secure.py` instead. Also update `requirements.txt` to use current, non-vulnerable package versions.

```bash
# Check current safe versions
pip index versions flask
pip index versions cryptography
```

After fixing, push again and screenshot the green (all passing) pipeline.

---

## Part C — Add Semgrep Gate (bonus 10 pts)

Add a 4th job to the pipeline:

```yaml
  semgrep:
    name: "🔎 Semgrep SAST"
    runs-on: ubuntu-latest
    container:
      image: returntocorp/semgrep
    steps:
      - uses: actions/checkout@v4
      - run: semgrep --config "p/python" --config "p/owasp-top-ten" src/ --error
```

---

## Part D — Pipeline Analysis Report (30 pts)

Write `pipeline_analysis.md` with:

1. **Pipeline Architecture Diagram** — ASCII diagram showing the 4 jobs and their dependency relationships

2. **Gate Results Table** — for both the failing run and the fixed run:
   | Gate | Run 1 (Vulnerable) | Run 2 (Fixed) |
   |------|-------------------|---------------|
   | SAST | ❌ FAIL — SQL injection (B608, line X) | ✅ PASS |
   | ... | | |

3. **DevSecOps Principles Applied** — for each of these principles, explain how your pipeline implements it:
   - **Shift Left**: Security checks happen at...
   - **Fail Fast**: The pipeline stops when...
   - **Automation**: Manual steps replaced by...
   - **Auditability**: Evidence is preserved via...

4. **Gap Analysis** — what security checks does your pipeline NOT cover that a production pipeline should? List at least 3 with a tool recommendation for each.

5. **False Positive Handling** — if Bandit flags a finding that's a false positive, how should a team handle it? Describe the process (suppression comment, justification, approval).

---

## Submission Checklist

- [ ] GitHub repo link (share with Dr. Chen or set to public for submission)
- [ ] `.github/workflows/devsecops.yml` — pipeline file
- [ ] Screenshot: failing pipeline run (SAST gate red)
- [ ] Screenshot: passing pipeline run (all gates green)
- [ ] `pipeline_analysis.md` — all 5 sections

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Pipeline YAML (4 gates, correct structure, triggers correctly) | 50 |
| Part B — Fixed code + passing pipeline screenshot | 20 |
| Part C — Semgrep gate added (bonus) | +10 |
| Part D — pipeline_analysis.md (all 5 sections, correct principles) | 30 |
| **Total** | **100** |
