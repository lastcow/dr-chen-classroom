---
title: "Lab 12: Backup, Recovery & Neon Branching"
course: ITEC-445
topic: Backup, Recovery & High Availability
week: 12
difficulty: ⭐⭐⭐
estimated_time: 80 minutes
---

# Lab 12: Backup, Recovery & Neon Branching

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 12 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 80 minutes |
| **Topic** | Backup, Recovery & High Availability |
| **Prerequisites** | Lab 01 schema + all previous labs on Neon branch `lab-12` |
| **Deliverables** | pg_dump backup, recovery simulation, Neon branch strategy, `verify_lab12()` PASS |

---

## Overview

Data loss is career-ending. Backup and recovery skills are the most operationally critical skills in database administration. In this lab you will use `pg_dump` for logical backups of Neon, simulate a disaster scenario, practice point-in-time recovery using Neon's branch feature (which provides database-level time travel), and design a backup strategy with defined RTO and RPO targets.

---

!!! warning "Branch Requirement"
    Create branch **`lab-12`** with the full accumulated schema from Labs 01–11 (or at minimum Lab 01 + Lab 06 seed data). This is the database you will "back up" and "recover."

---

## Part A — Logical Backup with pg_dump (25 pts)

`pg_dump` creates a portable logical backup of a PostgreSQL database. It works natively with Neon.

### A1. Full schema + data backup

```bash
# Full backup — schema and data, custom format (compressed, supports selective restore)
pg_dump "$DATABASE_URL" \
    --format=custom \
    --compress=9 \
    --schema=fsu \
    --file=fsu_backup_$(date +%Y%m%d_%H%M%S).dump \
    --verbose

# Verify the backup file
ls -lh fsu_backup_*.dump
```

### A2. Schema-only backup (DDL without data)

```bash
# Useful for deploying to a new environment
pg_dump "$DATABASE_URL" \
    --schema-only \
    --schema=fsu \
    --file=fsu_schema_$(date +%Y%m%d).sql

# View the schema DDL
head -80 fsu_schema_*.sql
```

### A3. Data-only backup for specific tables

```bash
# Export just the students and enrollments tables as INSERT statements
pg_dump "$DATABASE_URL" \
    --data-only \
    --schema=fsu \
    --table=fsu.students \
    --table=fsu.enrollments \
    --inserts \
    --file=fsu_data_only_$(date +%Y%m%d).sql

wc -l fsu_data_only_*.sql  # count lines to verify
```

### A4. List backup contents

```bash
# pg_restore --list shows what's in the custom-format dump
pg_restore --list fsu_backup_*.dump | head -30
```

---

## Part B — Disaster Simulation & Recovery (30 pts)

### B1. Simulate a disaster — accidental data deletion

```sql
SET search_path = fsu;

-- Record the count before the disaster
SELECT 'Before disaster:' AS event, COUNT(*) AS students FROM students
UNION ALL
SELECT 'Enrollments:', COUNT(*) FROM enrollments;

-- THE DISASTER: someone accidentally deletes all CS department students
BEGIN;
DELETE FROM enrollments
WHERE student_id IN (SELECT student_id FROM students WHERE dept_id = 1);

DELETE FROM students WHERE dept_id = 1;

-- "Oops" — how many rows deleted?
SELECT 'After disaster:' AS event, COUNT(*) AS students FROM students
UNION ALL
SELECT 'Enrollments:', COUNT(*) FROM enrollments;

-- DO NOT COMMIT — we'll recover two ways
ROLLBACK;  -- first recovery: transaction rollback
```

### B2. Verify transaction rollback worked

```sql
SELECT 'After rollback:' AS event, COUNT(*) AS students FROM students;
-- Should be back to original count
```

### B3. Simulate a committed disaster (harder recovery)

```sql
-- This time, commit the deletion — simulating a real production incident
BEGIN;
DELETE FROM enrollments WHERE student_id IN (
    SELECT student_id FROM students WHERE dept_id = 1 LIMIT 10
);
DELETE FROM students WHERE dept_id = 1 AND student_id IN (
    SELECT student_id FROM students WHERE dept_id = 1 LIMIT 10
);
COMMIT;  -- data is gone — need to recover from backup

SELECT 'After committed delete:', COUNT(*) FROM students WHERE dept_id=1;
```

### B4. Recovery from pg_dump backup

```bash
# Recover just the students table from backup
pg_restore \
    --dbname "$DATABASE_URL" \
    --schema=fsu \
    --table=students \
    --data-only \
    --single-transaction \
    --verbose \
    fsu_backup_*.dump
```

After restore:
```sql
-- Verify recovery
SELECT 'After restore:', COUNT(*) FROM fsu.students WHERE dept_id = 1;
```

---

## Part C — Neon Branch-Based Point-in-Time Recovery (25 pts)

Neon's branch feature provides instant database-level snapshots — equivalent to point-in-time recovery but without binary log replay.

### C1. Create a "before" snapshot branch

```bash
# Via Neon CLI (if installed)
# Or via Neon web UI: your project → Branches → Create branch

# Name: lab-12-checkpoint-before-delete
# Created from: lab-12 branch at current timestamp
```

Via the Neon web UI:
1. Go to your project → **Branches** tab
2. Click **Create branch**
3. Name it `lab-12-checkpoint`
4. Leave timestamp as "now" (captures current state)
5. Screenshot the branch creation

### C2. Perform destructive changes on the main branch

```sql
-- On lab-12 branch: simulate more data changes
UPDATE fsu.students SET gpa = 0.00 WHERE student_id <= 20;
DELETE FROM fsu.enrollments WHERE semester = '2023SP';

SELECT 'Corrupted students:', COUNT(*) FROM fsu.students WHERE gpa = 0;
SELECT '2023SP enrollments:', COUNT(*) FROM fsu.enrollments WHERE semester = '2023SP';
```

### C3. "Recover" by connecting to the checkpoint branch

```bash
# Get the checkpoint branch connection string from Neon UI
# Connection Details → select "lab-12-checkpoint" branch
export CHECKPOINT_URL="postgresql://user:***@ep-checkpoint.neon.tech/neondb?sslmode=require"

# Verify the checkpoint has good data
psql "$CHECKPOINT_URL" -c "SELECT COUNT(*) FROM fsu.students WHERE gpa > 0;"
psql "$CHECKPOINT_URL" -c "SELECT COUNT(*) FROM fsu.enrollments WHERE semester='2023SP';"
```

### C4. Branch comparison report

Write `branch_comparison.sql`:
```sql
-- Run this on the CORRUPTED branch (lab-12)
-- Compare with the output from the CHECKPOINT branch

SELECT
    'lab-12 (corrupted)' AS branch,
    COUNT(*) AS total_students,
    COUNT(CASE WHEN gpa = 0 THEN 1 END) AS zero_gpa_students,
    (SELECT COUNT(*) FROM enrollments WHERE semester='2023SP') AS sp23_enrollments
FROM fsu.students;
```

Screenshot results from both branches side-by-side.

---

## Part D — Backup Strategy Design (20 pts)

Write `lab12_backup_strategy.md` — a formal backup strategy document for the Frostburg University database:

```markdown
# Frostburg University Database — Backup & Recovery Strategy

## 1. Recovery Objectives

| Scenario | RTO Target | RPO Target |
|----------|-----------|-----------|
| Accidental row deletion | < 15 min | < 1 hour |
| Schema corruption | < 30 min | < 4 hours |
| Full database loss | < 2 hours | < 24 hours |
| Ransomware/site disaster | < 4 hours | < 1 week |

## 2. Backup Schedule

| Backup Type | Frequency | Retention | Tool |
|-------------|-----------|-----------|------|
| Full logical backup | Daily (off-peak) | 30 days | pg_dump |
| Schema-only DDL | Weekly | 1 year | pg_dump --schema-only |
| Neon branch checkpoint | Before major changes | 7 days | Neon branching |
| Off-site copy | Weekly | 90 days | S3/cloud copy of dump |

## 3. Recovery Procedures (step-by-step)

### Scenario A: Accidental data deletion (< 1 hour ago)
1. ...

### Scenario B: Recovery from pg_dump backup
1. ...

## 4. Testing Schedule
- Monthly: simulate data deletion + recover from pg_dump
- Quarterly: simulate full schema recovery
- Annual: full disaster recovery drill

## 5. Neon-Specific Considerations
- Neon branches are instantaneous (copy-on-write, no clone time)
- Neon free tier retains 7 days of history for PITR
- ...
```

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab12()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'Students table has 500+ rows (recovery successful)',
        CASE WHEN (SELECT COUNT(*) FROM students) >= 500 THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'CS dept students exist (dept_id=1)',
        CASE WHEN (SELECT COUNT(*) FROM students WHERE dept_id=1) > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'No students have GPA=0 after recovery',
        CASE WHEN (SELECT COUNT(*) FROM students WHERE gpa = 0) = 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'Enrollments table has 1000+ rows',
        CASE WHEN (SELECT COUNT(*) FROM enrollments) >= 1000 THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', '2024FA enrollments still exist',
        CASE WHEN (SELECT COUNT(*) FROM enrollments WHERE semester='2024FA') > 0
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'All departments have at least 1 student',
        CASE WHEN NOT EXISTS(
            SELECT dept_id FROM departments d
            WHERE NOT EXISTS(SELECT 1 FROM students s WHERE s.dept_id=d.dept_id)
        ) THEN 'PASS' ELSE 'NEEDS_RECOVERY' END, 10;

    RETURN QUERY SELECT '07', 'fsu schema intact (5 base tables)',
        CASE WHEN (SELECT COUNT(*) FROM information_schema.tables
                   WHERE table_schema='fsu' AND table_type='BASE TABLE') >= 5
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'grade_points view exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.views
                         WHERE table_schema='fsu' AND table_name='grade_points')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'Indexes still present after recovery',
        CASE WHEN (SELECT COUNT(*) FROM pg_indexes WHERE schemaname='fsu'
                   AND indexname NOT LIKE '%pkey%') >= 3
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'schema_migrations table intact',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='schema_migrations')
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab12()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write an automated backup verification script `verify_backup.sh` that:
1. Takes a `.dump` file as argument
2. Creates a fresh Neon branch (or uses a test connection) to restore into
3. Runs `SELECT COUNT(*) FROM fsu.students` and `fsu.enrollments` against the restored data
4. Compares counts against a baseline `expected_counts.json` file
5. Exits 0 (success) or 1 (failure) based on match

This demonstrates "backup is only as good as its last tested restore."

---

## Submission Checklist

- [ ] `fsu_backup_*.dump` — pg_dump custom format backup (verify with pg_restore --list)
- [ ] `fsu_schema_*.sql` — schema-only DDL backup
- [ ] Neon branch `lab-12-checkpoint` — screenshot of creation in Neon UI
- [ ] Screenshots: corrupted state vs checkpoint state (branch comparison)
- [ ] `lab12_backup_strategy.md` — formal strategy document
- [ ] `verify_backup.sh` — additional requirement
- [ ] `verify_lab12()` screenshot — all PASS (on recovered branch)

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — pg_dump (3 backup types, all files present) | 25 |
| Part B — Disaster simulation + recovery (transaction rollback + pg_restore) | 30 |
| Part C — Neon branch checkpoint (created, compared, screenshots) | 25 |
| Part D — Backup strategy document (all sections, RTO/RPO defined) | 20 |
| Additional requirement — verify_backup.sh | 20 |
| **Total** | **120** |
