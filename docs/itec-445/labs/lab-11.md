---
title: "Lab 11: Database Scripting & Automation"
course: ITEC-445
topic: Database Scripting & Automation
week: 11
difficulty: ⭐⭐⭐
estimated_time: 80 minutes
---

# Lab 11: Database Scripting & Automation

| Field | Details |
|---|---|
| **Course** | ITEC-445 — Advanced Database Management |
| **Week** | 11 |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 80 minutes |
| **Topic** | Database Scripting & Automation |
| **Prerequisites** | Lab 01 schema on Neon branch `lab-11`, Python 3.10+, `pip install psycopg2-binary pandas` |
| **Deliverables** | Python scripts, idempotent migration, health check procedure, `verify_lab11()` PASS |

---

## Overview

Manual database administration doesn't scale. Professional DBAs automate everything: health checks, batch jobs, data migrations, report generation, and schema changes. In this lab you will write production-quality Python automation scripts, build idempotent SQL migration scripts, and implement a database health-check procedure.

---

!!! warning "Branch Requirement"
    Create branch **`lab-11`** with Lab 01 schema + Lab 06 seed data (500+ students).

---

## Part A — psql Non-Interactive Scripting (15 pts)

`psql` can be used as a scripting engine. Create the following shell scripts:

**A1.** `db_summary.sh` — quick database stats via psql:

```bash
#!/bin/bash
# db_summary.sh — Frostburg DB quick stats
set -e

DATABASE_URL="${DATABASE_URL:?DATABASE_URL must be set}"

echo "=== Frostburg University DB Summary ==="
echo "Timestamp: $(date)"
echo ""

psql "$DATABASE_URL" --tuples-only --no-align << 'EOF'
SET search_path = fsu;
SELECT 'Tables' AS category, COUNT(*)::TEXT AS value
FROM information_schema.tables WHERE table_schema = 'fsu' AND table_type = 'BASE TABLE'
UNION ALL
SELECT 'Students',      COUNT(*)::TEXT FROM fsu.students
UNION ALL
SELECT 'Enrollments',   COUNT(*)::TEXT FROM fsu.enrollments
UNION ALL
SELECT 'Avg GPA',       ROUND(AVG(gpa)::NUMERIC,2)::TEXT FROM fsu.students WHERE gpa IS NOT NULL
UNION ALL
SELECT 'Indexes',       COUNT(*)::TEXT FROM pg_indexes WHERE schemaname = 'fsu'
ORDER BY 1;
EOF

echo ""
echo "=== Done ==="
```

Run:
```bash
chmod +x db_summary.sh
./db_summary.sh
```

**A2.** `run_sql.sh` — safe SQL file executor with logging:

```bash
#!/bin/bash
# run_sql.sh <sql_file> — runs a SQL file and logs output + errors
SQL_FILE="${1:?Usage: run_sql.sh <file.sql>}"
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(basename "$SQL_FILE" .sql)_$(date +%Y%m%d_%H%M%S).log"

echo "Running $SQL_FILE at $(date)" | tee "$LOG_FILE"

psql "$DATABASE_URL" \
    --set ON_ERROR_STOP=1 \
    --echo-all \
    -f "$SQL_FILE" \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS — log: $LOG_FILE"
else
    echo "FAILED (exit $EXIT_CODE) — see $LOG_FILE"
    exit $EXIT_CODE
fi
```

---

## Part B — Python Automation (35 pts)

**B1.** `db_health_check.py` — comprehensive health check script:

```python
#!/usr/bin/env python3
"""
db_health_check.py — Frostburg University Database Health Check
Checks: connection, row counts, GPA anomalies, orphaned records, index coverage
"""
import os
import sys
import psycopg2
from datetime import datetime

def check(name: str, query: str, threshold=None, operator='>='):
    """Run a check query and report pass/fail."""
    try:
        cur.execute(query)
        row = cur.fetchone()
        value = row[0] if row else None

        if threshold is not None:
            if operator == '>=' and value >= threshold:
                status = 'PASS'
            elif operator == '<=' and value <= threshold:
                status = 'PASS'
            elif operator == '==' and value == threshold:
                status = 'PASS'
            else:
                status = 'WARN'
        else:
            status = 'INFO'

        icon = {'PASS': '✓', 'WARN': '⚠', 'INFO': 'ℹ'}[status]
        print(f"  [{icon}] {name}: {value}  {'(threshold: ' + str(threshold) + ')' if threshold else ''}")
        return status, value
    except Exception as e:
        print(f"  [✗] {name}: ERROR — {e}")
        return 'ERROR', None

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SET search_path = fsu")

print(f"=== DB Health Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

print("Row Counts:")
check("Students",       "SELECT COUNT(*) FROM students",     500)
check("Enrollments",    "SELECT COUNT(*) FROM enrollments", 1000)
check("Courses",        "SELECT COUNT(*) FROM courses",       10)
check("Departments",    "SELECT COUNT(*) FROM departments",    5)

print("\nData Quality:")
check("Students with NULL GPA", "SELECT COUNT(*) FROM students WHERE gpa IS NULL", 50, '<=')
check("Invalid GPA (>4.0)",     "SELECT COUNT(*) FROM students WHERE gpa > 4.0",   0,  '==')
check("Orphaned enrollments",
      "SELECT COUNT(*) FROM enrollments e LEFT JOIN students s ON e.student_id=s.student_id WHERE s.student_id IS NULL",
      0, '==')
check("Duplicate enrollments",
      "SELECT COUNT(*) FROM (SELECT student_id,course_id,semester,COUNT(*) FROM enrollments GROUP BY 1,2,3 HAVING COUNT(*)>1) x",
      0, '==')

print("\nIndex Coverage:")
check("Non-PK indexes",
      "SELECT COUNT(*) FROM pg_indexes WHERE schemaname='fsu' AND indexname NOT LIKE '%pkey%'",
      3)

print("\nRecent Activity:")
check("Audit log entries",
      "SELECT COALESCE((SELECT COUNT(*) FROM audit_log),0)",
      0)

conn.close()
print("\n=== Health check complete ===")
```

Run:
```bash
python db_health_check.py
```

**B2.** `batch_gpa_update.py` — batch GPA recalculation with progress reporting:

```python
#!/usr/bin/env python3
"""
batch_gpa_update.py — Recalculate GPAs for all students in batches
Uses chunked processing to avoid long-running transactions.
"""
import os, psycopg2

BATCH_SIZE = 50

conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.autocommit = False
cur = conn.cursor()
cur.execute("SET search_path = fsu")

# Get all student IDs
cur.execute("SELECT student_id FROM students ORDER BY student_id")
all_ids = [row[0] for row in cur.fetchall()]

total = len(all_ids)
updated = 0
unchanged = 0

print(f"Processing {total} students in batches of {BATCH_SIZE}...")

for i in range(0, total, BATCH_SIZE):
    batch = all_ids[i:i+BATCH_SIZE]

    for student_id in batch:
        # Calculate new GPA from grade_points view
        cur.execute("""
            SELECT ROUND(AVG(points)::NUMERIC, 2)
            FROM grade_points
            WHERE student_id = %s AND points IS NOT NULL
        """, (student_id,))
        new_gpa = cur.fetchone()[0]

        # Only update if different
        cur.execute("SELECT gpa FROM students WHERE student_id = %s", (student_id,))
        old_gpa = cur.fetchone()[0]

        if new_gpa != old_gpa:
            cur.execute("UPDATE students SET gpa = %s WHERE student_id = %s",
                       (new_gpa, student_id))
            updated += 1
        else:
            unchanged += 1

    conn.commit()
    progress = min(i + BATCH_SIZE, total)
    print(f"  Batch complete: {progress}/{total} processed ({updated} updated so far)")

conn.close()
print(f"\nDone: {updated} updated, {unchanged} unchanged out of {total} students")
```

---

## Part C — Idempotent Migration Script (25 pts)

Professional schema changes must be idempotent — safe to run multiple times. Write `migrations/V003__add_scholarship_table.sql`:

```sql
-- Migration: V003 — Add scholarship tracking
-- Idempotent: safe to run multiple times
-- Author: [Your Name]
-- Date: [Date]

SET search_path = fsu;

-- Version tracking table (create if not exists)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(20) PRIMARY KEY,
    description TEXT,
    applied_at  TIMESTAMPTZ DEFAULT NOW(),
    applied_by  TEXT DEFAULT current_user
);

-- Guard: skip if already applied
DO $$
BEGIN
    IF EXISTS(SELECT 1 FROM schema_migrations WHERE version = 'V003') THEN
        RAISE NOTICE 'Migration V003 already applied — skipping';
        RETURN;
    END IF;

    -- Create scholarships table
    CREATE TABLE IF NOT EXISTS scholarships (
        scholarship_id SERIAL       PRIMARY KEY,
        name           VARCHAR(100) NOT NULL,
        amount         NUMERIC(10,2) NOT NULL CHECK (amount > 0),
        dept_id        INT          REFERENCES departments(dept_id),
        min_gpa        NUMERIC(3,2) DEFAULT 3.0,
        created_at     TIMESTAMPTZ  DEFAULT NOW()
    );

    -- Create student_scholarships junction table
    CREATE TABLE IF NOT EXISTS student_scholarships (
        student_id     INT NOT NULL REFERENCES students(student_id),
        scholarship_id INT NOT NULL REFERENCES scholarships(scholarship_id),
        awarded_year   SMALLINT NOT NULL,
        amount_awarded NUMERIC(10,2),
        PRIMARY KEY (student_id, scholarship_id, awarded_year)
    );

    -- Add index for scholarship lookups by department
    CREATE INDEX IF NOT EXISTS idx_scholarships_dept ON scholarships(dept_id);

    -- Seed initial scholarships
    INSERT INTO scholarships (name, amount, dept_id, min_gpa) VALUES
        ('Dean''s Excellence Award', 5000.00, NULL, 3.8),
        ('CS Department Award',      2500.00, 1,    3.5),
        ('Math Department Award',    2500.00, 2,    3.5),
        ('General Merit Award',      1000.00, NULL, 3.0)
    ON CONFLICT DO NOTHING;

    -- Record migration as applied
    INSERT INTO schema_migrations (version, description)
    VALUES ('V003', 'Add scholarship and student_scholarships tables');

    RAISE NOTICE 'Migration V003 applied successfully';
END;
$$;

-- Verify
SELECT version, description, applied_at FROM schema_migrations ORDER BY version;
```

Run it twice:
```bash
psql "$DATABASE_URL" -f migrations/V003__add_scholarship_table.sql
psql "$DATABASE_URL" -f migrations/V003__add_scholarship_table.sql  # should skip
```

Second run should print: `NOTICE: Migration V003 already applied — skipping`

---

## Part D — PL/pgSQL Health Check Procedure (15 pts)

Write a stored procedure `db_health_report()` that runs entirely in-database:

```sql
CREATE OR REPLACE FUNCTION db_health_report()
RETURNS TABLE(check_name TEXT, value TEXT, status TEXT) AS $$
BEGIN
    -- Student count
    RETURN QUERY SELECT 'Student count'::TEXT,
        (SELECT COUNT(*)::TEXT FROM students),
        CASE WHEN (SELECT COUNT(*) FROM students) >= 500 THEN 'OK' ELSE 'LOW' END;

    -- GPA anomalies
    RETURN QUERY SELECT 'Invalid GPA count'::TEXT,
        (SELECT COUNT(*)::TEXT FROM students WHERE gpa > 4.0 OR gpa < 0),
        CASE WHEN (SELECT COUNT(*) FROM students WHERE gpa > 4.0 OR gpa < 0) = 0
             THEN 'OK' ELSE 'ERROR' END;

    -- Orphaned enrollments
    RETURN QUERY SELECT 'Orphaned enrollments'::TEXT,
        (SELECT COUNT(*)::TEXT FROM enrollments e
         WHERE NOT EXISTS(SELECT 1 FROM students s WHERE s.student_id = e.student_id)),
        CASE WHEN (SELECT COUNT(*) FROM enrollments e
                   WHERE NOT EXISTS(SELECT 1 FROM students s WHERE s.student_id=e.student_id)) = 0
             THEN 'OK' ELSE 'ERROR' END;

    -- Index count
    RETURN QUERY SELECT 'Non-PK index count'::TEXT,
        (SELECT COUNT(*)::TEXT FROM pg_indexes WHERE schemaname='fsu' AND indexname NOT LIKE '%pkey%'),
        CASE WHEN (SELECT COUNT(*) FROM pg_indexes WHERE schemaname='fsu' AND indexname NOT LIKE '%pkey%') >= 3
             THEN 'OK' ELSE 'LOW' END;
END;
$$ LANGUAGE plpgsql;

SELECT * FROM db_health_report();
```

---

## Verification

```sql
SET search_path = fsu;

CREATE OR REPLACE FUNCTION verify_lab11()
RETURNS TABLE(check_id TEXT, description TEXT, result TEXT, points INT) AS $$
BEGIN
    RETURN QUERY SELECT '01', 'schema_migrations table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='schema_migrations')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '02', 'V003 migration applied',
        CASE WHEN EXISTS(SELECT 1 FROM schema_migrations WHERE version='V003')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '03', 'scholarships table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='scholarships')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '04', 'scholarships has 4 seed rows',
        CASE WHEN (SELECT COUNT(*) FROM scholarships) = 4
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '05', 'student_scholarships table exists',
        CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables
                         WHERE table_schema='fsu' AND table_name='student_scholarships')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '06', 'db_health_report function exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname='db_health_report')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '07', 'db_health_report returns rows',
        CASE WHEN (SELECT COUNT(*) FROM db_health_report()) >= 4
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '08', 'No orphaned enrollments detected',
        CASE WHEN (
            SELECT value FROM db_health_report() WHERE check_name='Orphaned enrollments'
        ) = '0' THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '09', 'idx_scholarships_dept index exists',
        CASE WHEN EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_scholarships_dept')
             THEN 'PASS' ELSE 'FAIL' END, 10;

    RETURN QUERY SELECT '10', 'Students table has 500+ rows',
        CASE WHEN (SELECT COUNT(*) FROM students) >= 500
             THEN 'PASS' ELSE 'FAIL' END, 10;
END;
$$ LANGUAGE plpgsql;

SELECT check_id, description, result,
       CASE WHEN result = 'PASS' THEN points ELSE 0 END AS earned
FROM verify_lab11()
ORDER BY check_id;
```

---

## Additional Requirement (20 pts)

Write `scholarship_award.py` — a Python script that automatically awards scholarships to eligible students:

1. Queries all scholarships with their `min_gpa` and optional `dept_id`
2. For each scholarship, finds all eligible students (GPA >= min_gpa, matching dept if set)
3. Awards the scholarship to students not already awarded in the current year
4. Inserts rows into `student_scholarships`
5. Prints a summary: `Scholarship X: awarded to N students`

---

## Submission Checklist

- [ ] `db_summary.sh` — runs and shows stats
- [ ] `run_sql.sh` — runs and logs
- [ ] `db_health_check.py` — all checks pass/warn correctly
- [ ] `batch_gpa_update.py` — runs, reports updated/unchanged count
- [ ] `migrations/V003__add_scholarship_table.sql` — idempotent (run twice, second skips)
- [ ] `scholarship_award.py` — additional requirement
- [ ] `verify_lab11()` screenshot — all PASS

---

## Grading

| Component | Points |
|-----------|--------|
| Part A — Shell scripts (db_summary + run_sql, both run correctly) | 15 |
| Part B — Python scripts (health_check + batch_gpa, correct output) | 35 |
| Part C — Idempotent migration (runs twice, second is no-op) | 25 |
| Part D — db_health_report() in-DB function | 15 |
| Additional requirement — scholarship_award.py | 20 |
| **Total** | **110** |
