---
title: "ITEC-445 Labs"
course: ITEC-445
---

# ITEC-445 — Advanced Database Management: Labs

All 13 labs use **Neon PostgreSQL** — the same platform used in SCIA-340. Students already have accounts. Each lab creates a named branch (`lab-01` through `lab-13`) and ends with a `verify_labXX()` function that Dr. Chen runs to grade automatically.

---

## Lab Overview

| # | Lab | Week | Topic | Key Tools | Difficulty |
|---|-----|------|-------|-----------|-----------|
| [01](lab-01.md) | Advanced SQL — Joins, Subqueries & Set Ops | 1 | Ch01 | PostgreSQL, psql | ⭐⭐ |
| [02](lab-02.md) | Window Functions, CTEs & Analytical Queries | 2 | Ch02 | Window functions, Recursive CTEs | ⭐⭐⭐ |
| [03](lab-03.md) | Stored Procedures & PL/pgSQL Control Flow | 3 | Ch03 | PL/pgSQL, cursors | ⭐⭐⭐ |
| [04](lab-04.md) | User-Defined Functions & Triggers | 4 | Ch04 | UDFs, BEFORE/AFTER triggers | ⭐⭐⭐ |
| [05](lab-05.md) | Data Import, Export & ETL | 5 | Ch05 | `\copy`, JSON, Python psycopg2 | ⭐⭐ |
| [06](lab-06.md) | Index Design & Query Performance | 6 | Ch06 | `EXPLAIN`, B-tree, partial indexes | ⭐⭐⭐ |
| [07](lab-07.md) | Query Execution Plans & Optimization | 7 | Ch07 | `EXPLAIN ANALYZE`, `pg_stat_statements` | ⭐⭐⭐⭐ |
| [08](lab-08.md) | Database Views — Security & Reporting | 8 | Ch08 | Views, materialized views, `WITH CHECK OPTION` | ⭐⭐ |
| [09](lab-09.md) | Security — Authentication & RBAC | 9 | Ch09 | Roles, RLS policies, SQL injection | ⭐⭐⭐ |
| [10](lab-10.md) | Encryption, Auditing & Compliance | 10 | Ch10 | pgcrypto, audit triggers, GDPR | ⭐⭐⭐ |
| [11](lab-11.md) | Database Scripting & Automation | 11 | Ch11 | Python, shell scripts, migrations | ⭐⭐⭐ |
| [12](lab-12.md) | Backup, Recovery & Neon Branching | 12 | Ch12 | pg_dump, Neon branches, PITR | ⭐⭐⭐ |
| [13](lab-13.md) | Capstone — Frostburg Course Registration System | 15 | Ch15 | All tools | ⭐⭐⭐⭐⭐ |

---

## Difficulty Key

| Rating | Meaning |
|--------|---------|
| ⭐ | Introductory |
| ⭐⭐ | Intermediate — guided with scaffolding |
| ⭐⭐⭐ | Advanced — independent reasoning required |
| ⭐⭐⭐⭐ | Expert — integrates multiple concepts |
| ⭐⭐⭐⭐⭐ | Capstone — all skills combined |

---

## The Frostburg University Schema

All labs share the same base schema — `fsu` — set up in Lab 01 and extended in subsequent labs. The schema models Frostburg State University's academic data:

```
departments ──< instructors
departments ──< courses ──< sections ──< enrollments >── students
departments ──< students
```

**Tables:** `departments`, `instructors`, `courses`, `students`, `enrollments`  
**Extended in later labs:** `grade_audit_log`, `gpa_history`, `staging_students`, `scholarships`, `audit_log`, `schema_migrations`

---

## Grading Pattern

Every lab ends with a `verify_labXX()` function. Dr. Chen grades by running:

```sql
SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_labXX()
ORDER BY check_id;
```

No "trust the screenshot" — the database state is the proof.

---

## Branch Naming Convention

| Lab | Branch Name |
|-----|------------|
| Lab 01 | `lab-01` |
| Lab 02 | `lab-02` |
| ... | ... |
| Lab 13 (Capstone) | `lab-13` |

Each branch is independent. For labs that build on a previous lab's data, instructions specify which branch to fork from.

---

## Prerequisites

- Neon account (free tier at [neon.tech](https://neon.tech))
- `psql` installed locally
- Python 3.10+ with `psycopg2-binary` (Labs 05, 09, 11, 12)
- `pg_dump` / `pg_restore` (Lab 12 — ships with PostgreSQL client)

---

## Cumulative Skill Map

```
Lab 01 (SQL) ──► Lab 02 (Analytics) ──► Lab 03 (Procedures)
     │                                         │
     └──► Lab 04 (Functions/Triggers) ─────────┤
                                               │
Lab 05 (ETL) ──► Lab 06 (Indexes) ──► Lab 07 (Optimization)
                                               │
Lab 08 (Views) ──► Lab 09 (RBAC) ──► Lab 10 (Encryption)
                                               │
Lab 11 (Automation) ──► Lab 12 (Backup) ──► Lab 13 (Capstone)
```
