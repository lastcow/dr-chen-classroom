---
title: "Lab 12: Software Quality Audit & SQA Plan"
course: SCIA-425
topic: Software Quality Management
week: 14
difficulty: ⭐⭐⭐
estimated_time: 90 minutes
---

# Lab 12: Software Quality Audit & SQA Plan

| Field | Details |
|---|---|
| **Course** | SCIA-425 — Software Assurance and Quality |
| **Week** | 14 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90 minutes |
| **Topic** | Software Quality Management |
| **Prerequisites** | Python 3.10+, Git, `pip install radon pygount` |
| **Deliverables** | `audit_report.md`, `sqa_plan.md`, `audit_metrics.py` output |

---

## Overview

A Software Quality Audit (SQA) is a systematic, independent examination of a software project to determine whether it complies with defined quality standards, plans, and procedures. A Software Quality Assurance Plan (SQAP) specifies the quality activities, standards, and controls that will be applied throughout a project's lifecycle. In this lab you will audit a real open-source project, produce a formal audit report, and write an SQA plan for it.

---

## Select Your Audit Target

Choose **one** of these open-source projects to audit:

| Project | Language | GitHub | Why It's Interesting |
|---------|----------|--------|----------------------|
| **Bottle** | Python | `bottlepy/bottle` | Minimal web framework, single-file |
| **Click** | Python | `pallets/click` | CLI toolkit, well-tested reference |
| **Requests** | Python | `psf/requests` | HTTP library, security-critical |

```bash
# Clone your chosen target
git clone https://github.com/psf/requests.git audit_target
cd audit_target
```

---

## Part A — Quantitative Audit Metrics (35 pts)

Collect objective data about the project. Create `audit_metrics.py`:

```python
import subprocess
import json
import os
from pathlib import Path

TARGET = "audit_target"

print(f"=== Software Quality Audit: {TARGET} ===\n")

# ── 1. Codebase Size ──────────────────────────────────────────────
result = subprocess.run(
    ["pygount", "--format=json", TARGET],
    capture_output=True, text=True
)
if result.stdout:
    size_data = json.loads(result.stdout)
    # pygount summary
    total_code = sum(v.get("Code", 0) for v in size_data.values() if isinstance(v, dict))
    total_doc  = sum(v.get("Documentation", 0) for v in size_data.values() if isinstance(v, dict))
    total_empty = sum(v.get("Empty", 0) for v in size_data.values() if isinstance(v, dict))
    print(f"Codebase Size:")
    print(f"  Code lines:    {total_code:,}")
    print(f"  Comment lines: {total_doc:,}")
    print(f"  Empty lines:   {total_empty:,}")
    comment_ratio = total_doc / max(total_code, 1) * 100
    print(f"  Comment ratio: {comment_ratio:.1f}% (industry standard: 15-25%)")

# ── 2. Test Coverage ───────────────────────────────────────────────
print("\nTest Coverage:")
cov = subprocess.run(
    ["python", "-m", "pytest", "--co", "-q"],
    capture_output=True, text=True, cwd=TARGET
)
test_count = len([l for l in cov.stdout.split("\n") if "::" in l])
print(f"  Test functions found: {test_count}")

# ── 3. Code Complexity ─────────────────────────────────────────────
cc = subprocess.run(
    ["radon", "cc", TARGET, "-s", "-a", "--json"],
    capture_output=True, text=True
)
if cc.stdout:
    try:
        cc_data = json.loads(cc.stdout)
        all_blocks = [b for blocks in cc_data.values() for b in blocks]
        complexities = [b["complexity"] for b in all_blocks]
        if complexities:
            import statistics
            print(f"\nCyclomatic Complexity:")
            print(f"  Functions analyzed: {len(complexities)}")
            print(f"  Average CC: {statistics.mean(complexities):.2f}")
            print(f"  Max CC: {max(complexities)}")
            high_risk = [b for b in all_blocks if b["complexity"] > 10]
            print(f"  High-risk functions (CC>10): {len(high_risk)}")
    except:
        print("  (radon CC parse error — run manually)")

# ── 4. Technical Debt ──────────────────────────────────────────────
print("\nTechnical Debt Indicators:")
todos = subprocess.run(
    ["grep", "-r", "-n", "TODO\\|FIXME\\|HACK\\|XXX\\|NOQA", TARGET, "--include=*.py"],
    capture_output=True, text=True
)
todo_lines = [l for l in todos.stdout.split("\n") if l.strip()]
print(f"  TODO/FIXME/HACK comments: {len(todo_lines)}")
for line in todo_lines[:5]:
    print(f"    {line[:80]}")

# ── 5. Git History ─────────────────────────────────────────────────
print("\nVersion Control Health:")
commits = subprocess.run(
    ["git", "log", "--oneline", "--since=6 months ago"],
    capture_output=True, text=True, cwd=TARGET
)
commit_list = [l for l in commits.stdout.split("\n") if l.strip()]
print(f"  Commits (last 6 months): {len(commit_list)}")

contributors = subprocess.run(
    ["git", "shortlog", "-s", "-n", "--since=6 months ago"],
    capture_output=True, text=True, cwd=TARGET
)
contrib_list = [l for l in contributors.stdout.split("\n") if l.strip()]
print(f"  Active contributors: {len(contrib_list)}")
for c in contrib_list[:5]:
    print(f"    {c.strip()}")

# ── 6. Open Issues (manual check) ─────────────────────────────────
print("\n[Manual] Open Issues: visit https://github.com/<owner>/<repo>/issues")
print("[Manual] Last release date: check GitHub Releases tab")
```

Run:
```bash
pip install radon pygount
python audit_metrics.py 2>&1 | tee audit_metrics_output.txt
```

---

## Part B — Audit Criteria & Findings (35 pts)

Evaluate the project against these **IEEE 730 SQA standard criteria**. Record findings in `audit_report.md`:

| # | Criterion | Metric / Evidence | Rating | Finding |
|---|-----------|-----------------|--------|---------|
| QA-01 | **Test Coverage** | Test function count / LOC | | |
| QA-02 | **Documentation** | Comment ratio %, README quality | | |
| QA-03 | **Code Complexity** | Avg CC, functions with CC>10 | | |
| QA-04 | **Technical Debt** | TODO/FIXME count normalized to KLOC | | |
| QA-05 | **Defect Response** | Avg days to close bug issues (sample 10) | | |
| QA-06 | **Contribution Health** | Active contributors, commit frequency | | |
| QA-07 | **Security Posture** | Security policy file, CVE history | | |
| QA-08 | **Dependency Management** | Outdated dependencies count | | |

**Rating scale:** ✅ Satisfactory | ⚠️ Needs Improvement | ❌ Unsatisfactory

For each rating of ⚠️ or ❌, write a **Corrective Action Request (CAR)**:
```
CAR-001: Test Coverage
  Finding: X test functions for Y KLOC (ratio below industry standard of 1 test per 10 LOC)
  Risk: Insufficient coverage increases probability of undetected defects
  Recommended Action: Increase test count targeting uncovered modules identified by coverage report
  Target: Achieve 80%+ statement coverage within 2 sprints
```

---

## Part C — Write the SQA Plan (20 pts)

A Software Quality Assurance Plan (SQAP) per **IEEE 730** must include:

Write `sqa_plan.md` for your audit target (as if you were the QA lead for the next major release):

```markdown
# Software Quality Assurance Plan
**Project:** [Project Name]
**Version:** [Next Release]
**Author:** [Your Name]
**Date:** [Date]
**Standard:** IEEE 730-2014

---

## 1. Purpose and Scope
[What this SQAP covers, what's out of scope]

## 2. Reference Documents
[Standards, regulations, and guidelines followed]

## 3. Management
### 3.1 Organization
[Who is responsible for QA activities]
### 3.2 Tasks and Responsibilities
[QA activities and who owns each]
### 3.3 Quality Gates
[What must pass before each release phase]

## 4. Documentation Requirements
[What documents must exist and be reviewed]

## 5. Standards, Practices, and Conventions
### 5.1 Coding Standards
[e.g., PEP 8, max CC=10, 100% type hints on public API]
### 5.2 Test Standards
[e.g., minimum 80% coverage, all tests must pass before merge]

## 6. Reviews and Audits
### 6.1 Code Review Process
[Who reviews, criteria for approval]
### 6.2 Security Review Checkpoints
[SAST, dependency scan, threat model review]
### 6.3 Audit Schedule
[When audits occur, who performs them]

## 7. Test Plan Summary
[Testing types, tools, success criteria]

## 8. Problem Reporting
[How defects are logged, tracked, and resolved]

## 9. Tools and Infrastructure
[CI/CD tools, static analysis, coverage tools]

## 10. Risk Management
[Top quality risks and mitigation strategies]
```

---

## Part D — Audit Conclusion (10 pts)

End `audit_report.md` with:

1. **Overall Quality Rating** — Satisfactory / Conditionally Satisfactory / Unsatisfactory (with justification)
2. **Top 3 Strengths** — what does this project do well?
3. **Top 3 Improvement Areas** — most critical gaps
4. **Certification Recommendation** — would you certify this release for production? Why or why not?

---

## Submission Checklist

- [ ] `audit_metrics.py` — runs, output captured in `audit_metrics_output.txt`
- [ ] `audit_report.md` — criteria table + CARs + conclusion
- [ ] `sqa_plan.md` — all 10 IEEE 730 sections

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — audit_metrics.py (all 6 metric categories, correct data) | 35 |
| Part B — audit_report.md (all 8 criteria rated, CARs for weak areas) | 35 |
| Part C — sqa_plan.md (all 10 IEEE 730 sections, specific and actionable) | 20 |
| Part D — Audit conclusion (rating justified, 3+3 strengths/gaps) | 10 |
| **Total** | **100** |
