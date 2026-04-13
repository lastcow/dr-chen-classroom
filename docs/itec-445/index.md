---
title: ITEC 445 — Database Systems II
description: 15-week comprehensive reading guide aligned to course objectives — Frostburg State University
---

# ITEC 445 — Database Systems II

<div class="course-hero" markdown>

> **Department of Computer Science & Information Technology**  
> Frostburg State University · Fall 2026 · Instructor: Dr. Chen  
> Prerequisite: Grade of C or better in ITEC 345

</div>

---

## Course Overview

Database Systems II moves beyond foundational SQL and relational design to master the **advanced engineering, administration, and security of production database environments**. Students develop the skills to architect, optimize, secure, and maintain enterprise-grade database systems — the critical infrastructure behind every modern application.

Topics span the full professional database administrator (DBA) and data engineer spectrum: from advanced SQL and stored procedure development through security hardening, performance tuning, high availability, cloud databases, NoSQL alternatives, and a capstone implementation project.

!!! abstract "What You Will Learn"
    By the end of this course, you will be able to:

    - Write advanced SQL including complex joins, subqueries, window functions, and CTEs
    - Design and implement stored procedures, functions, triggers, and views
    - Import and export data across formats (CSV, JSON, XML, binary) using professional tooling
    - Build and evaluate index strategies to optimize query performance
    - Create and manage database views for abstraction, security, and reporting
    - Write and maintain database scripts for automation and administration
    - Implement comprehensive database security (authentication, RBAC, encryption, auditing)
    - Perform database server administration tasks (backup, recovery, monitoring, replication)
    - Design and implement an advanced database project integrating all course objectives

---

## Course Objectives

| # | Objective |
|---|-----------|
| **CO1** | Write advanced SQL queries including multi-table joins, subqueries, CTEs, and window functions |
| **CO2** | Design and implement stored procedures, user-defined functions, and triggers |
| **CO3** | Import and export data between database systems and external formats (CSV, JSON, XML, Excel) |
| **CO4** | Create, manage, and optimize database indexes to improve query performance |
| **CO5** | Design and implement database views for data abstraction, security, and reporting |
| **CO6** | Write database administration scripts for automation, scheduling, and maintenance |
| **CO7** | Implement database security controls: authentication, authorization, encryption, and auditing |
| **CO8** | Perform database server administration: backup/recovery, monitoring, replication, and tuning |
| **CO9** | Design and deliver an advanced database implementation project meeting professional standards |

---

## 15-Week Reading Schedule

| Week | Topic | Objectives | Focus Area |
|------|-------|------------|------------|
| [**Week 1**](week01.md) | Advanced SQL — Joins, Subqueries & Set Operations | CO1 | 🔍 Advanced SQL |
| [**Week 2**](week02.md) | Window Functions, CTEs & Analytical Queries | CO1 | 📊 Analytics SQL |
| [**Week 3**](week03.md) | Stored Procedures & Control Flow Programming | CO2 | ⚙️ Procedures |
| [**Week 4**](week04.md) | User-Defined Functions & Triggers | CO2 | 🔧 Functions |
| [**Week 5**](week05.md) | Data Import & Export — Formats & Tools | CO3 | 📦 ETL / Import |
| [**Week 6**](week06.md) | Index Design & Query Optimization | CO4 | ⚡ Performance |
| [**Week 7**](week07.md) | Query Execution Plans & Advanced Optimization | CO4, CO1 | 🔬 Optimization |
| [**Week 8**](week08.md) | Database Views — Design, Security & Reporting | CO5 | 👁️ Views |
| [**Week 9**](week09.md) | Database Security — Authentication & Authorization | CO7 | 🔒 Security I |
| [**Week 10**](week10.md) | Database Security — Encryption, Auditing & Compliance | CO7 | 🛡️ Security II |
| [**Week 11**](week11.md) | Database Scripting & Automation | CO6 | 📜 Scripting |
| [**Week 12**](week12.md) | Backup, Recovery & High Availability | CO8 | 💾 Backup/HA |
| [**Week 13**](week13.md) | Monitoring, Replication & Performance Tuning | CO8 | 📈 Tuning |
| [**Week 14**](week14.md) | NoSQL, NewSQL & Cloud Database Systems | CO8, CO9 | ☁️ Modern DBs |
| [**Week 15**](week15.md) | Advanced Project Implementation & Capstone | CO9 | 🚀 Capstone |

---

## Core Textbooks & Resources

!!! book "Primary References"
    - **Database System Concepts, 7th Ed.** — Silberschatz, Korth & Sudarshan (McGraw-Hill)
    - **Learning MySQL, 2nd Ed.** — Dyer & Beighley (O'Reilly)
    - **MySQL Administrator's Bible** — Sheeri K. Cabral & Keith Murphy (Wiley)
    - **PostgreSQL: Up and Running, 3rd Ed.** — Regina Obe & Leo Hsu (O'Reilly)
    - **Designing Data-Intensive Applications** — Martin Kleppmann (O'Reilly)
    - **MySQL Documentation** — dev.mysql.com/doc (official reference, always current)

!!! tool "Technologies & Tools Covered"
    `MySQL 8.x` · `PostgreSQL 16` · `MySQL Workbench` · `pgAdmin` · `SQL Server Management Studio` · `mysqldump` · `mysqlpump` · `xtrabackup` · `Python (mysql-connector, SQLAlchemy)` · `EXPLAIN / EXPLAIN ANALYZE` · `pt-query-digest` · `Percona Toolkit` · `Redis` · `MongoDB` · `Amazon RDS` · `Google Cloud SQL`

---

## Assessment Structure

```
Weekly Labs & Exercises         30%   (hands-on SQL + admin tasks)
Quizzes                         15%   (concepts + syntax, bi-weekly)
Midterm Exam                    20%   (Weeks 1–7)
Security & Admin Assignment     10%   (Weeks 9–11)
Advanced Project                25%   (design + implementation + report)
```

---

## Final Project Overview

!!! info "Capstone: Advanced Database Implementation"
    Individual or pairs design and build a production-grade database system:

    - **Schema Design** — fully normalized (3NF+), proper constraints, documented ERD
    - **Advanced SQL** — stored procedures, functions, triggers, views (minimum 3 each)
    - **Security** — role-based access control, encrypted sensitive fields, audit log table
    - **Performance** — index strategy document, EXPLAIN plan evidence of optimization
    - **Administration** — backup script, automated maintenance job, monitoring query
    - **Data Pipeline** — import/export script handling ≥ 1,000 rows of real or realistic data
    - **Technical Report** — design decisions, performance benchmarks, security architecture

    See [Week 15](week15.md) for full specifications and grading rubric.

---

*Navigate to any week using the table above or the sidebar.*
