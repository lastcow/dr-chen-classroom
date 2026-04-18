---
title: "SCIA-425 Labs"
course: SCIA-425
---

# SCIA-425 — Software Assurance & Quality: Labs

These 13 hands-on labs correspond to the weekly readings and build cumulatively toward the capstone. Each lab produces **verifiable artifacts** — scan reports, test results, proof outputs, or pipeline runs — not just screenshots of reading.

---

## Lab Overview

| # | Lab | Week | Topic | Tools | Difficulty |
|---|-----|------|-------|-------|-----------|
| [01](lab-01.md) | Security Requirements & Misuse Cases | 2 | Ch02 | Python, jsonschema, pytest | ⭐⭐ |
| [02](lab-02.md) | Threat Modeling with STRIDE | 3 | Ch03 | pytm, Docker | ⭐⭐ |
| [03](lab-03.md) | Architecture Security Review | 4 | Ch04 | Python, CWE/CAPEC | ⭐⭐⭐ |
| [04](lab-04.md) | Static Analysis & Code Inspection | 5 | Ch05 | Bandit, Semgrep, Docker | ⭐⭐ |
| [05](lab-05.md) | Test Design: Coverage, Equivalence & Mutation | 6 | Ch06 | pytest, pytest-cov, mutmut | ⭐⭐⭐ |
| [06](lab-06.md) | Fuzzing & Dynamic Testing | 7 | Ch07 | Hypothesis, Docker | ⭐⭐⭐ |
| [07](lab-07.md) | Security Testing & Penetration Testing | 8 | Ch08 | OWASP ZAP, DVWA, Docker | ⭐⭐⭐ |
| [08](lab-08.md) | Quality Metrics & Statistical QC | 10 | Ch10 | Radon, matplotlib, scipy | ⭐⭐ |
| [09](lab-09.md) | Formal Verification & Model Checking | 11 | Ch11 | Z3 theorem prover | ⭐⭐⭐⭐ |
| [10](lab-10.md) | DevSecOps Pipeline | 12 | Ch12 | GitHub Actions, Gitleaks, Safety | ⭐⭐⭐ |
| [11](lab-11.md) | Compliance Testing & Regulatory Assurance | 13 | Ch13 | ASVS checker, HIPAA evidence | ⭐⭐⭐ |
| [12](lab-12.md) | Software Quality Audit & SQA Plan | 14 | Ch14 | Radon, pygount, IEEE 730 | ⭐⭐⭐ |
| [13](lab-13.md) | Capstone: AI-Assisted Testing & Synthesis | 15 | Ch15 | All tools + OpenAI/Ollama | ⭐⭐⭐⭐ |

---

## Difficulty Key

| Rating | Meaning |
|--------|---------|
| ⭐ | Introductory — follows guided steps |
| ⭐⭐ | Intermediate — applies concepts with scaffolding |
| ⭐⭐⭐ | Advanced — requires independent reasoning and tool mastery |
| ⭐⭐⭐⭐ | Expert — integrates multiple skills, open-ended analysis |

---

## Tool Stack Summary

```
Python Tools:          pytest, pytest-cov, mutmut, hypothesis, radon, bandit, safety, z3-solver
Container Tools:       Docker (Semgrep, ZAP, pytm/Graphviz, DVWA)
CI/CD:                 GitHub Actions (Lab 10)
Visualization:         matplotlib, pandas
Formal Methods:        Z3 SMT Solver
AI Assistance:         OpenAI API or Ollama (Lab 13)
```

## Prerequisites

- **All labs:** Python 3.10+, Docker Desktop or Docker Engine
- **Lab 10:** GitHub account (free tier sufficient)
- **Lab 13:** OpenAI API key (optional — Ollama can substitute)

No cloud database accounts are required (unlike SCIA-340).

---

## Capstone Dependency Map

```
Lab 01 (Requirements) ──► Lab 02 (Threat Model) ──► Lab 03 (Architecture)
         │                                                    │
         └──► Lab 04 (SAST) ──► Lab 05 (Tests) ──► Lab 06 (Fuzzing)
                                                             │
Lab 07 (Pentest) ──► Lab 08 (Metrics) ──► Lab 09 (Formal) ──┤
         │                                                   │
         └──► Lab 10 (DevSecOps) ──► Lab 11 (Compliance) ───┤
                                           │                 │
                                     Lab 12 (Audit) ─────►  Lab 13 (Capstone)
```

All skills from Labs 01–12 are exercised in the Lab 13 capstone assessment.
