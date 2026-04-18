---
title: "Lab 13: Capstone — Frostburg Course Registration System"
course: ITEC-445
topic: Advanced Project Implementation & Capstone Review
week: 15
difficulty: ⭐⭐⭐⭐⭐
estimated_time: 150 minutes
---

# Lab 13: Capstone — Frostburg Course Registration System

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 15 |
| **Difficulty** | ⭐⭐⭐⭐⭐ Expert |
| **Estimated Time** | 150 minutes |
| **Topic** | Advanced Project Implementation & Capstone Review |
| **Prerequisites** | All Labs 01–12 completed, Neon branch `lab-13` |
| **Deliverables** | Complete FCRS database, `verify_capstone()` 10/10 checks PASS (80 pts automated) |

---

## Overview

The capstone integrates every skill from ITEC-445 into a single production-quality database system: the **Frostburg Course Registration System (FCRS)**. You will build the full schema, implement stored procedures and triggers, design a complete RBAC model, add encryption for sensitive data, and expose a clean view layer — then prove it all works via an automated 10-check verification function.

Dr. Chen grades by running:
```sql
SELECT check_id, description, result, earned FROM verify_capstone() ORDER BY check_id;
```

A result of 10/10 PASS = 80 points. The remaining 20 points come from code quality and the design document.

---

!!! warning "Fresh Branch Required"
    Create a **new Neon branch `lab-13`** from scratch (not from a previous lab). This is a clean implementation of the full FCRS.

---

## System Requirements

Build the **Frostburg Course Registration System** with these specifications:

### 1. Schema (fully normalized, 9 tables)

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `departments` | dept_id, name, building, budget | |
| `instructors` | instructor_id, name, email, dept_id, salary | Salary encrypted |
| `courses` | course_id, code, title, credits, dept_id | |
| `prerequisites` | course_id, prereq_id | Self-referential M:M |
| `sections` | section_id, course_id, instructor_id, semester, capacity, room | |
| `students` | student_id, name, email, gpa, dept_id, ssn_hash | SSN as search hash only |
| `enrollments` | enrollment_id, student_id, section_id, status, grade | status: enrolled/waitlisted/dropped |
| `audit_log` | log_id, table_name, operation, record_id, old_data, new_data, changed_at | JSONB audit |
| `schema_migrations` | version, description, applied_at | Version tracking |

### 2. Stored Procedures (4 required)

- `register_student(student_id, section_id)` — validates prerequisites, checks capacity, handles waitlist
- `drop_course(student_id, section_id)` — drops enrollment, promotes waitlisted student
- `assign_final_grade(student_id, section_id, grade)` — assigns grade, updates student GPA
- `semester_rollover(from_sem, to_sem)` — re-enrolls passing students in next semester

### 3. Functions (3 required)

- `calculate_gpa(student_id)` — computes GPA from all graded enrollments
- `has_prerequisite(student_id, course_id)` — checks if student has completed all prerequisites
- `section_availability(section_id)` — returns `enrolled_count`, `capacity`, `seats_remaining`, `waitlist_count`

### 4. Triggers (3 required)

- Audit trigger on `students` — logs all INSERT/UPDATE/DELETE to `audit_log`
- Audit trigger on `enrollments` — logs all changes
- GPA auto-update trigger — fires AFTER grade is assigned in `enrollments`

### 5. RBAC (4 roles)

- `role_registrar` — manage students and enrollments
- `role_instructor` — view own sections, assign grades
- `role_student_portal` — read-only access to own records (via RLS)
- `role_reporting` — read-only views

### 6. Views (3 required)

- `v_section_roster` — students enrolled in each section with grades
- `v_student_transcript` — full course history per student
- `v_waitlist` — ordered waitlist for each section

### 7. Indexes (at least 5)

Justify each with a comment in your SQL.

---

## Implementation Guide

### Step 1 — Schema DDL

```sql
SET search_path = fcrs;
CREATE SCHEMA IF NOT EXISTS fcrs;
SET search_path = fcrs;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- departments
CREATE TABLE departments (
    dept_id   SERIAL       PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    building  VARCHAR(50),
    budget    NUMERIC(12,2)
);

-- instructors (salary encrypted)
CREATE TABLE instructors (
    instructor_id    SERIAL       PRIMARY KEY,
    first_name       VARCHAR(50)  NOT NULL,
    last_name        VARCHAR(50)  NOT NULL,
    email            VARCHAR(100) UNIQUE NOT NULL,
    dept_id          INT          REFERENCES departments(dept_id),
    hire_date        DATE,
    salary_encrypted BYTEA        -- pgcrypto encrypted
);

-- courses
CREATE TABLE courses (
    course_id   SERIAL       PRIMARY KEY,
    course_code VARCHAR(10)  NOT NULL UNIQUE,
    title       VARCHAR(150) NOT NULL,
    credits     SMALLINT     NOT NULL DEFAULT 3 CHECK (credits BETWEEN 1 AND 6),
    dept_id     INT          REFERENCES departments(dept_id)
);

-- prerequisites (self-referential)
CREATE TABLE prerequisites (
    course_id  INT NOT NULL REFERENCES courses(course_id),
    prereq_id  INT NOT NULL REFERENCES courses(course_id),
    PRIMARY KEY (course_id, prereq_id),
    CHECK (course_id <> prereq_id)
);

-- sections
CREATE TABLE sections (
    section_id    SERIAL       PRIMARY KEY,
    course_id     INT          NOT NULL REFERENCES courses(course_id),
    instructor_id INT          REFERENCES instructors(instructor_id),
    semester      VARCHAR(10)  NOT NULL,
    capacity      SMALLINT     NOT NULL DEFAULT 30 CHECK (capacity > 0),
    room          VARCHAR(30)
);

-- students
CREATE TABLE students (
    student_id  SERIAL       PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    gpa         NUMERIC(3,2) CHECK (gpa BETWEEN 0 AND 4),
    dept_id     INT          REFERENCES departments(dept_id),
    enroll_year SMALLINT,
    ssn_hash    TEXT         -- HMAC hash for lookup, never store plaintext
);

-- enrollments
CREATE TABLE enrollments (
    enrollment_id SERIAL      PRIMARY KEY,
    student_id    INT         NOT NULL REFERENCES students(student_id),
    section_id    INT         NOT NULL REFERENCES sections(section_id),
    status        VARCHAR(15) NOT NULL DEFAULT 'enrolled'
                              CHECK (status IN ('enrolled','waitlisted','dropped','completed')),
    grade         VARCHAR(2),
    enrolled_at   TIMESTAMPTZ DEFAULT NOW(),
    waitlist_pos  SMALLINT,
    UNIQUE (student_id, section_id)
);

-- audit_log
CREATE TABLE audit_log (
    log_id      BIGSERIAL   PRIMARY KEY,
    table_name  TEXT        NOT NULL,
    operation   TEXT        NOT NULL,
    record_id   INT,
    changed_by  TEXT        DEFAULT current_user,
    changed_at  TIMESTAMPTZ DEFAULT NOW(),
    old_data    JSONB,
    new_data    JSONB
);

-- schema_migrations
CREATE TABLE schema_migrations (
    version     VARCHAR(20) PRIMARY KEY,
    description TEXT,
    applied_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO schema_migrations VALUES ('V001', 'Initial FCRS schema', NOW());
```

### Step 2 — Seed Data

Seed at minimum:
- 5 departments
- 8 instructors (with encrypted salaries)
- 12 courses (with at least 3 prerequisites defined)
- 20 sections across 2 semesters (2024FA and 2025SP)
- 50 students
- 150+ enrollments with grades

### Step 3 — Implement All Functions, Procedures & Triggers

Implement all required objects from the spec above. Follow the patterns from Labs 03, 04, and 10.

### Step 4 — RBAC & RLS

Follow Lab 09 pattern. Enable RLS on `students` and `enrollments`.

### Step 5 — Indexes

```sql
-- Examples — add your own with justifications
CREATE INDEX idx_enrollments_student   ON enrollments(student_id);
CREATE INDEX idx_enrollments_section   ON enrollments(section_id) WHERE status = 'enrolled';
CREATE INDEX idx_sections_semester     ON sections(semester, course_id);
CREATE INDEX idx_students_dept         ON students(dept_id);
CREATE INDEX idx_audit_log_table_time  ON audit_log(table_name, changed_at DESC);
```

---

## Verification Function

Create this exactly on your `lab-13` branch:

```sql
SET search_path = fcrs;

CREATE OR REPLACE FUNCTION verify_capstone()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, earned INT) AS $$
BEGIN
    -- Check 1: Core tables exist (8 tables)
    RETURN QUERY SELECT '01', '8 required tables exist',
        CASE WHEN (
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema='fcrs'
            AND table_name IN ('departments','instructors','courses','prerequisites',
                               'sections','students','enrollments','audit_log')
        ) = 8 THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 2: Data volume (50 students, 12 courses, 150 enrollments)
    RETURN QUERY SELECT '02', 'Minimum data: 50 students, 12 courses, 150 enrollments',
        CASE WHEN (SELECT COUNT(*) FROM students) >= 50
             AND  (SELECT COUNT(*) FROM courses)  >= 12
             AND  (SELECT COUNT(*) FROM enrollments) >= 150
             THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 3: Prerequisites defined (at least 3)
    RETURN QUERY SELECT '03', 'At least 3 course prerequisites defined',
        CASE WHEN (SELECT COUNT(*) FROM prerequisites) >= 3
             THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 4: calculate_gpa function works
    RETURN QUERY SELECT '04', 'calculate_gpa() returns valid value for student 1',
        CASE WHEN (
            SELECT calculate_gpa(1) BETWEEN 0 AND 4
        ) THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 5: section_availability function works
    RETURN QUERY SELECT '05', 'section_availability() returns seats_remaining',
        CASE WHEN EXISTS(
            SELECT 1 FROM section_availability(1) WHERE seats_remaining IS NOT NULL
        ) THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 6: has_prerequisite function exists
    RETURN QUERY SELECT '06', 'has_prerequisite() function exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname='has_prerequisite')
             THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 7: Audit triggers fire (audit_log has rows)
    RETURN QUERY SELECT '07', 'audit_log has rows (triggers fired during seed)',
        CASE WHEN (SELECT COUNT(*) FROM audit_log) > 0
             THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 8: RLS enabled on students
    RETURN QUERY SELECT '08', 'Row-Level Security enabled on students',
        CASE WHEN (SELECT rowsecurity FROM pg_tables
                   WHERE schemaname='fcrs' AND tablename='students')
             THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 9: Required views exist
    RETURN QUERY SELECT '09', 'v_section_roster, v_student_transcript, v_waitlist exist',
        CASE WHEN (
            SELECT COUNT(*) FROM information_schema.views
            WHERE table_schema='fcrs'
            AND table_name IN ('v_section_roster','v_student_transcript','v_waitlist')
        ) = 3 THEN 'PASS' ELSE 'FAIL' END, 8;

    -- Check 10: At least 5 non-PK indexes
    RETURN QUERY SELECT '10', 'At least 5 non-PK indexes on fcrs schema',
        CASE WHEN (
            SELECT COUNT(*) FROM pg_indexes
            WHERE schemaname='fcrs' AND indexname NOT LIKE '%pkey%'
        ) >= 5 THEN 'PASS' ELSE 'FAIL' END, 8;
END;
$$ LANGUAGE plpgsql;

-- Grade yourself:
SELECT check_id, description, result,
       CASE WHEN result='PASS' THEN earned ELSE 0 END AS earned_pts
FROM verify_capstone()
ORDER BY check_id;

-- Total score (80 pts max):
SELECT SUM(CASE WHEN result='PASS' THEN earned ELSE 0 END) AS total_score
FROM verify_capstone();
```

---

## Design Document (20 pts)

Write `capstone_design.md` with:

1. **ER Diagram** — ASCII or text description of all 9 tables and their relationships
2. **Procedure Design** — for each of the 4 procedures: inputs, outputs, error cases, transaction boundary
3. **RBAC Matrix** — table of which roles can SELECT/INSERT/UPDATE/DELETE on each table
4. **Index Justification** — table of all 5+ indexes with the query pattern each supports
5. **Course Synthesis** — one sentence per lab (01–12) explaining which skill you used in this capstone
6. **Known Limitations** — at least 2 things you would add in a production system that are out of scope here

---

## Bonus: Advanced Feature (+10 pts)

Implement **one** of the following:

**Option A — Waitlist Automation:**
Trigger that automatically enrolls the next waitlisted student when someone drops a course. Uses `waitlist_pos` ordering, decrements remaining waitlist positions.

**Option B — Grade Distribution Report:**
A materialized view `mv_grade_distribution` showing count of each letter grade per course per semester, plus letter-grade percentages. Auto-refreshes via a procedure call.

**Option C — Python Registration Portal:**
A Python CLI script `register.py` that accepts `--student-id` and `--section-id`, calls `register_student()` on Neon, and reports success/waitlisted/error in a user-friendly format.

---

## Submission Checklist

- [ ] Neon branch `lab-13` — fresh, named correctly
- [ ] All schema DDL executed and verified
- [ ] 50+ students, 12+ courses, 150+ enrollments seeded
- [ ] All 4 procedures, 3 functions, 3 triggers, 3 views, 4 roles, 5+ indexes created
- [ ] `SELECT * FROM verify_capstone()` screenshot — 10/10 PASS
- [ ] `capstone_design.md` — all 6 sections
- [ ] Bonus feature (optional)

---

## Grading

| Component | Points |
|-----------|--------|
| `verify_capstone()` — 10 automated checks × 8 pts each | 80 |
| `capstone_design.md` — all 6 sections, professional quality | 20 |
| Bonus feature (one of A, B, C) | +10 |
| **Total** | **100 (+10 bonus)** |

---

!!! success "Congratulations — ITEC-445 Complete!"
    You have built a production-quality database system from scratch: normalized schema, procedural logic, role-based security, encryption, auditing, views, indexes, automation scripts, and a backup strategy. These are the skills of a professional database engineer.
