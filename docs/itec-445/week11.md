---
title: "Week 11 — Database Scripting & Automation"
description: "Automate DBA tasks using MySQL CLI scripting, shell scripts, Python, SQLAlchemy, the MySQL Event Scheduler, and idempotent migration tooling."
---

# Week 11 — Database Scripting & Automation

**Course Objectives: CO6** | **Focus: Scripting, Automation, Scheduling** | **Difficulty: ⭐⭐⭐☆☆**

---

## Learning Objectives

By the end of this week, you should be able to:

- [ ] Execute MySQL commands non-interactively using `mysql -e`, batch files, and heredoc patterns
- [ ] Write Bash shell scripts that drive MySQL and handle exit codes and logging robustly
- [ ] Create, enable, disable, and drop MySQL Events using the Event Scheduler
- [ ] Compare the MySQL Event Scheduler to OS-level cron jobs and select the right tool
- [ ] Write Python scripts using `mysql-connector-python` with connection pooling and transaction management
- [ ] Use SQLAlchemy Core to build database-agnostic automation scripts
- [ ] Build a production-grade automated backup script with compression and retention policies
- [ ] Write a database health-check script that alerts on replication lag, long-running queries, and disk pressure
- [ ] Construct and execute dynamic SQL using `PREPARE`, `EXECUTE`, and `DEALLOCATE PREPARE`
- [ ] Design idempotent migration scripts using version tables, `IF NOT EXISTS` guards, and Flyway/Liquibase

---

## 1. MySQL Command-Line Client Scripting

The `mysql` command-line client is far more than an interactive prompt—it is a powerful scripting engine that forms the backbone of many DBA automation workflows.

### 1.1 Non-Interactive Execution with `-e`

The `-e` (execute) flag lets you run one or more SQL statements without entering the interactive shell. This is the simplest form of automation:

```bash title="mysql -e basics"
# Run a single statement
mysql -u root -p"$DB_PASS" -e "SHOW DATABASES;"

# Run against a specific schema
mysql -u root -p"$DB_PASS" university -e "SELECT COUNT(*) AS total_students FROM students;"

# Multiple statements separated by semicolons
mysql -u root -p"$DB_PASS" university \
  -e "SELECT table_name, table_rows FROM information_schema.tables
      WHERE table_schema = 'university' ORDER BY table_rows DESC;"
```

!!! tip "Suppress Column Headers with `--skip-column-names`"
    When parsing `mysql -e` output in a shell script, combine `--skip-column-names` (or `-N`) with `--batch` (`-B`) to get tab-separated values without headers — ideal for piping into `awk` or `cut`.

### 1.2 Batch Mode and Output Flags

| Flag | Long Form | Effect |
|------|-----------|--------|
| `-B` | `--batch` | Tab-separated output, no borders |
| `-N` | `--skip-column-names` | Omit header row |
| `-s` | `--silent` | Reduce noise; less verbose errors |
| `-E` | `--vertical` | Print each row as `field: value` pairs |
| `--html` | | Output as HTML table |
| `--xml` | | Output as XML |
| `--tee=file` | | Also write output to a file |

```bash title="Batch mode output for scripting"
# Get tab-separated data, no headers
mysql -u root -p"$DB_PASS" -B -N university \
  -e "SELECT student_id, last_name, gpa FROM students WHERE gpa < 2.0;"

# Vertical output — great for wide rows
mysql -u root -p"$DB_PASS" -E university \
  -e "SELECT * FROM enrollments WHERE enrollment_id = 1001;"
```

### 1.3 Heredoc Execution and Batch Files

For multi-statement scripts that don't warrant a separate `.sql` file, heredoc syntax keeps everything in one shell script:

```bash title="Heredoc SQL execution"
#!/usr/bin/env bash
# run_weekly_report.sh

DB_USER="report_user"
DB_PASS="${MYSQL_REPORT_PASS}"
DB_NAME="university"

mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" <<'EOF'
-- Weekly enrollment summary
SELECT
    d.dept_name,
    COUNT(DISTINCT e.student_id) AS enrolled_students,
    COUNT(DISTINCT s.section_id)  AS active_sections
FROM departments d
JOIN courses c      ON c.dept_id      = d.dept_id
JOIN sections s     ON s.course_id    = c.course_id
JOIN enrollments e  ON e.section_id   = s.section_id
WHERE s.semester = 'Fall2025'
GROUP BY d.dept_name
ORDER BY enrolled_students DESC;
EOF
```

For longer scripts, redirect a `.sql` file:

```bash title="Running an external SQL file"
mysql -u root -p"$DB_PASS" university < /opt/db/scripts/monthly_cleanup.sql
```

!!! warning "Password Security"
    Never hard-code passwords directly on the command line where they appear in shell history and `ps aux` output. Use a `~/.my.cnf` option file or the `MYSQL_PWD` environment variable (still readable in `/proc`, so prefer option files):
    ```ini title="~/.my.cnf"
    [client]
    user     = root
    password = s3cr3t!
    host     = 127.0.0.1
    ```
    Lock this file: `chmod 600 ~/.my.cnf`

---

## 2. Shell Scripts for DBA Tasks

Well-written Bash scripts are the workhorse of database operations. This section covers patterns for reliability, error handling, and logging.

### 2.1 Bash + MySQL CLI Patterns

Every DBA script should follow a standard structure:

```bash title="dba_script_template.sh"
#!/usr/bin/env bash
# ============================================================
# Script  : dba_script_template.sh
# Purpose : Template for MySQL DBA automation scripts
# Author  : DBA Team
# Modified: 2025-10-01
# ============================================================
set -euo pipefail           # Exit on error, undefined vars, pipe failures

# ---- Configuration -----------------------------------------
readonly DB_HOST="127.0.0.1"
readonly DB_PORT="3306"
readonly DB_USER="dba_admin"
readonly DB_NAME="university"
readonly LOG_FILE="/var/log/mysql/dba_$(date +%Y%m%d).log"
readonly LOCK_FILE="/tmp/dba_script.lock"

# ---- Logging -----------------------------------------------
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
die() { log "FATAL: $*"; exit 1; }

# ---- Lock (prevent concurrent runs) ------------------------
exec 200>"$LOCK_FILE"
flock -n 200 || die "Another instance is already running."

# ---- MySQL helper ------------------------------------------
mysql_cmd() {
    mysql --defaults-file=/etc/mysql/dba.cnf \
          -h "$DB_HOST" -P "$DB_PORT" \
          -B -N "$DB_NAME" \
          -e "$1"
}

log "Script started"
# ... your logic here ...
log "Script completed successfully"
```

### 2.2 Checking Exit Codes and Logging Output

MySQL CLI returns a non-zero exit code on failure. Capture this and log diagnostics:

```bash title="Exit code checking and logging"
#!/usr/bin/env bash
set -uo pipefail

LOG="/var/log/mysql/schema_update.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

run_sql() {
    local stmt="$1"
    local output
    output=$(mysql --defaults-file=/etc/mysql/dba.cnf university \
                   -B -N -e "$stmt" 2>&1)
    local rc=$?
    if [[ $rc -ne 0 ]]; then
        log "ERROR (rc=$rc): $stmt"
        log "Output: $output"
        return $rc
    fi
    echo "$output"
    return 0
}

# Check if a table exists before altering it
TABLE_EXISTS=$(run_sql \
  "SELECT COUNT(*) FROM information_schema.tables
   WHERE table_schema='university' AND table_name='audit_log';")

if [[ "$TABLE_EXISTS" -eq 0 ]]; then
    log "audit_log table missing — creating"
    run_sql "CREATE TABLE university.audit_log (
               log_id    INT AUTO_INCREMENT PRIMARY KEY,
               event_ts  DATETIME DEFAULT CURRENT_TIMESTAMP,
               user_name VARCHAR(50),
               action    VARCHAR(255)
             );" || { log "Table creation failed"; exit 1; }
    log "audit_log created successfully"
else
    log "audit_log already exists — skipping"
fi
```

!!! info "Capturing Both stdout and stderr"
    Use `2>&1` to capture MySQL error messages. MySQL writes errors to `stderr`, so without redirection your `output` variable will be empty even on failure.

---

## 3. Scheduled Automation — Event Scheduler vs Cron

### 3.1 MySQL Event Scheduler

The MySQL Event Scheduler is a built-in job scheduler that runs SQL at specified times — without requiring access to the operating system.

```sql title="Enable the Event Scheduler"
-- Check current status
SHOW VARIABLES LIKE 'event_scheduler';

-- Enable (runtime — does not persist across restarts)
SET GLOBAL event_scheduler = ON;

-- To persist: add to /etc/mysql/mysql.conf.d/mysqld.cnf
-- event_scheduler = ON
```

**CREATE EVENT syntax:**

```sql title="CREATE EVENT full syntax"
CREATE [DEFINER = user] EVENT [IF NOT EXISTS] event_name
ON SCHEDULE
    { AT timestamp [+ INTERVAL interval] ...
    | EVERY interval
      [STARTS timestamp]
      [ENDS   timestamp] }
[ON COMPLETION [NOT] PRESERVE]
[ENABLE | DISABLE | DISABLE ON SLAVE]
[COMMENT 'comment']
DO event_body;
```

### 3.2 Real Event Scheduler Examples

=== "Nightly Session Cleanup"

    ```sql title="Nightly expired session cleanup"
    DELIMITER $$
    CREATE EVENT IF NOT EXISTS e_cleanup_expired_sessions
    ON SCHEDULE EVERY 1 DAY
    STARTS TIMESTAMP(CURRENT_DATE, '02:00:00')   -- 2 AM every night
    ON COMPLETION PRESERVE
    ENABLE
    COMMENT 'Delete sessions older than 24 hours'
    DO
    BEGIN
        DECLARE rows_deleted INT DEFAULT 0;

        DELETE FROM user_sessions
        WHERE last_activity < NOW() - INTERVAL 24 HOUR;

        SET rows_deleted = ROW_COUNT();

        INSERT INTO audit_log (user_name, action)
        VALUES ('EVENT_SCHEDULER',
                CONCAT('Deleted ', rows_deleted, ' expired sessions'));
    END$$
    DELIMITER ;
    ```

=== "Weekly Stats Aggregation"

    ```sql title="Weekly enrollment statistics rollup"
    DELIMITER $$
    CREATE EVENT IF NOT EXISTS e_weekly_enrollment_stats
    ON SCHEDULE EVERY 1 WEEK
    STARTS '2025-09-01 03:00:00'
    ON COMPLETION PRESERVE
    ENABLE
    DO
    BEGIN
        INSERT INTO enrollment_stats_weekly
            (week_start, dept_id, total_enrollments, avg_gpa)
        SELECT
            DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY) AS week_start,
            c.dept_id,
            COUNT(*)                             AS total_enrollments,
            AVG(g.numeric_grade)                 AS avg_gpa
        FROM enrollments e
        JOIN sections    s ON s.section_id  = e.section_id
        JOIN courses     c ON c.course_id   = s.course_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        GROUP BY c.dept_id;
    END$$
    DELIMITER ;
    ```

=== "Monthly Report"

    ```sql title="Monthly report generation"
    DELIMITER $$
    CREATE EVENT IF NOT EXISTS e_monthly_dept_report
    ON SCHEDULE EVERY 1 MONTH
    STARTS '2025-10-01 04:00:00'
    ON COMPLETION PRESERVE
    ENABLE
    DO
    BEGIN
        -- Truncate and repopulate the monthly report table
        TRUNCATE TABLE monthly_dept_report;

        INSERT INTO monthly_dept_report
            (report_month, dept_id, dept_name,
             new_enrollments, completions, avg_grade)
        SELECT
            DATE_FORMAT(NOW(), '%Y-%m-01')  AS report_month,
            d.dept_id,
            d.dept_name,
            COUNT(DISTINCT e.enrollment_id) AS new_enrollments,
            SUM(CASE WHEN g.numeric_grade IS NOT NULL THEN 1 ELSE 0 END) AS completions,
            AVG(g.numeric_grade)            AS avg_grade
        FROM departments d
        LEFT JOIN courses     c ON c.dept_id      = d.dept_id
        LEFT JOIN sections    s ON s.course_id    = c.course_id
        LEFT JOIN enrollments e ON e.section_id   = s.section_id
        LEFT JOIN grades      g ON g.enrollment_id = e.enrollment_id
        WHERE MONTH(e.enrolled_at) = MONTH(NOW())
          AND YEAR(e.enrolled_at)  = YEAR(NOW())
        GROUP BY d.dept_id, d.dept_name;
    END$$
    DELIMITER ;
    ```

=== "Log Rotation"

    ```sql title="Audit log rotation (keep 90 days)"
    DELIMITER $$
    CREATE EVENT IF NOT EXISTS e_rotate_audit_log
    ON SCHEDULE EVERY 1 DAY
    STARTS TIMESTAMP(CURRENT_DATE, '01:00:00')
    ON COMPLETION PRESERVE
    ENABLE
    DO
    BEGIN
        DELETE FROM audit_log
        WHERE event_ts < NOW() - INTERVAL 90 DAY;

        OPTIMIZE TABLE audit_log;   -- Reclaim fragmented space
    END$$
    DELIMITER ;
    ```

### 3.3 Managing Events

```sql title="Event management commands"
-- List all events
SHOW EVENTS FROM university;
SELECT * FROM information_schema.EVENTS WHERE EVENT_SCHEMA = 'university'\G

-- Disable (pause) an event
ALTER EVENT e_cleanup_expired_sessions DISABLE;

-- Re-enable
ALTER EVENT e_cleanup_expired_sessions ENABLE;

-- Drop an event
DROP EVENT IF EXISTS e_cleanup_expired_sessions;

-- Modify schedule
ALTER EVENT e_weekly_enrollment_stats
ON SCHEDULE EVERY 1 WEEK
STARTS '2025-10-06 03:00:00';
```

### 3.4 Event Scheduler vs. Cron — Comparison

| Criterion | MySQL Event Scheduler | OS Cron |
|-----------|-----------------------|---------|
| Location | Lives inside the database | Lives on the OS |
| Language | SQL (and stored procedures) | Any shell/script |
| Portability | Moves with database dump | Must be re-created on new host |
| Precision | 1-second granularity | 1-minute granularity |
| Non-SQL tasks | ❌ Cannot send email, copy files | ✅ Full shell access |
| Visibility | `SHOW EVENTS` / `information_schema` | `crontab -l` |
| Clustering | One event runs per cluster, not per node | Runs on every node unless guarded |
| Logging | `mysql.event` table | `/var/log/cron` |

!!! tip "Best Practice"
    Use the **Event Scheduler** for purely SQL tasks (cleanup, aggregation, status updates). Use **cron** when the job must touch the OS — file copies, email alerts, external API calls.

---

## 4. Python Database Scripting

Python has become the preferred language for DBA automation beyond simple SQL tasks.

### 4.1 mysql-connector-python with Connection Pooling

```python title="connection_pool.py"
"""
MySQL connection pool for University database automation.
Install: pip install mysql-connector-python
"""
import mysql.connector
from mysql.connector import pooling, Error
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ---- Connection Pool Configuration -------------------------
DB_CONFIG = {
    "host":     "127.0.0.1",
    "port":     3306,
    "user":     "app_user",
    "password": "app_password",   # Use env vars in production
    "database": "university",
    "charset":  "utf8mb4",
    "use_unicode": True,
    "connect_timeout": 10,
    "autocommit": False,          # Explicit transaction management
}

pool = pooling.MySQLConnectionPool(
    pool_name="uni_pool",
    pool_size=5,                  # 5 concurrent connections
    **DB_CONFIG
)

def get_connection():
    """Acquire a connection from the pool."""
    return pool.get_connection()


# ---- Execute a DML with Transaction Management -------------
def enroll_student(student_id: int, section_id: int) -> bool:
    """Enroll a student, returning True on success."""
    conn = None
    cursor = None
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check capacity
        cursor.execute(
            "SELECT capacity, enrolled_count "
            "FROM sections WHERE section_id = %s FOR UPDATE",
            (section_id,)
        )
        section = cursor.fetchone()
        if not section:
            logger.warning("Section %s not found", section_id)
            return False

        if section["enrolled_count"] >= section["capacity"]:
            logger.warning("Section %s is at capacity", section_id)
            return False

        # Insert enrollment
        cursor.execute(
            "INSERT INTO enrollments (student_id, section_id, enrolled_at) "
            "VALUES (%s, %s, NOW())",
            (student_id, section_id)
        )
        # Update count
        cursor.execute(
            "UPDATE sections SET enrolled_count = enrolled_count + 1 "
            "WHERE section_id = %s",
            (section_id,)
        )
        conn.commit()
        logger.info("Enrolled student %s in section %s", student_id, section_id)
        return True

    except Error as exc:
        logger.error("DB error during enrollment: %s", exc)
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()   # Returns connection to pool


# ---- Fetch Results (DDL) ------------------------------------
def get_low_gpa_students(threshold: float = 2.0) -> list[dict]:
    """Return students with GPA below threshold."""
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT student_id, first_name, last_name, gpa "
            "FROM students WHERE gpa < %s ORDER BY gpa",
            (threshold,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    students = get_low_gpa_students(2.0)
    for s in students:
        logger.info("At-risk student: %s %s (GPA %.2f)",
                    s["first_name"], s["last_name"], s["gpa"])
```

### 4.2 SQLAlchemy Core for Database-Agnostic Scripting

```python title="sqlalchemy_automation.py"
"""
SQLAlchemy Core example — database-agnostic DBA scripting.
Install: pip install sqlalchemy pymysql
"""
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

# ---- Engine Creation (connection string formats) -----------
# MySQL via PyMySQL:
engine = create_engine(
    "mysql+pymysql://dba_user:dba_pass@127.0.0.1:3306/university",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,    # Validate connections before use
    echo=False,            # Set True to log all SQL
)

# ---- Executing Parameterised Queries -----------------------
def get_enrollment_summary(semester: str) -> list[dict]:
    """Return course enrollment counts for a semester."""
    sql = text("""
        SELECT
            c.course_code,
            c.title,
            s.section_num,
            COUNT(e.enrollment_id) AS enrolled,
            s.capacity
        FROM sections    s
        JOIN courses     c ON c.course_id   = s.course_id
        LEFT JOIN enrollments e ON e.section_id = s.section_id
        WHERE s.semester = :semester
        GROUP BY s.section_id
        ORDER BY c.course_code, s.section_num
    """)
    with engine.connect() as conn:
        result = conn.execute(sql, {"semester": semester})
        return [dict(row._mapping) for row in result]


# ---- Transactional DDL Migration ----------------------------
def add_column_if_missing(table: str, column: str, col_def: str) -> None:
    """Idempotently add a column to a table."""
    check_sql = text("""
        SELECT COUNT(*) AS cnt
        FROM   information_schema.columns
        WHERE  table_schema = DATABASE()
          AND  table_name   = :tbl
          AND  column_name  = :col
    """)
    alter_sql = text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_def}")

    with engine.begin() as conn:       # begin() auto-commits on exit
        row = conn.execute(check_sql, {"tbl": table, "col": column}).fetchone()
        if row[0] == 0:
            logger.info("Adding column %s.%s", table, column)
            conn.execute(alter_sql)
        else:
            logger.info("Column %s.%s already exists — skipping", table, column)


if __name__ == "__main__":
    summary = get_enrollment_summary("Fall2025")
    for row in summary:
        print(f"{row['course_code']} S{row['section_num']}: "
              f"{row['enrolled']}/{row['capacity']}")

    add_column_if_missing("students", "preferred_name", "VARCHAR(60) NULL")
```

!!! info "SQLAlchemy Core vs ORM"
    **Core** gives you SQL-centric control — you write explicit SQL with `text()` or expression language. The **ORM** maps Python classes to tables and is better for application code. For DBA scripts, Core is preferred because the SQL is explicit and debuggable.

---

## 5. Automating Backups

### 5.1 Production Backup Script

```bash title="automated_backup.sh — production-grade"
#!/usr/bin/env bash
# ============================================================
# automated_backup.sh
# Performs daily/weekly MySQL backups with compression,
# remote copy, and retention enforcement.
# ============================================================
set -euo pipefail

# ---- Configuration -----------------------------------------
readonly DB_HOST="127.0.0.1"
readonly DB_USER="backup_user"
readonly DB_NAME="university"
readonly BACKUP_DIR="/var/backups/mysql"
readonly REMOTE_HOST="backup.university.edu"
readonly REMOTE_DIR="/backups/mysql/$(hostname)"
readonly KEEP_DAILY=7
readonly KEEP_WEEKLY=4
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)
readonly DAY_OF_WEEK=$(date +%u)   # 1=Mon … 7=Sun
readonly LOG="/var/log/mysql/backup_${TIMESTAMP}.log"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
die()  { log "FATAL: $*"; exit 1; }

# ---- Determine backup type ---------------------------------
if [[ "$DAY_OF_WEEK" -eq 7 ]]; then
    BACKUP_TYPE="weekly"
else
    BACKUP_TYPE="daily"
fi

BACKUP_FILE="${BACKUP_DIR}/${BACKUP_TYPE}/${DB_NAME}_${TIMESTAMP}.sql.gz"
mkdir -p "${BACKUP_DIR}/daily" "${BACKUP_DIR}/weekly"

log "Starting $BACKUP_TYPE backup of $DB_NAME"

# ---- Run mysqldump -----------------------------------------
mysqldump \
    --defaults-file=/etc/mysql/backup.cnf \
    --host="$DB_HOST" \
    --single-transaction \      # Consistent snapshot (InnoDB)
    --flush-logs \               # Rotate binlog at snapshot point
    --master-data=2 \            # Comment with binlog position
    --routines \                 # Include stored procedures/functions
    --triggers \                 # Include triggers
    --events \                   # Include scheduled events
    --add-drop-table \           # Safe for restore
    --hex-blob \                 # Binary fields as hex
    "$DB_NAME" \
  | gzip -9 > "$BACKUP_FILE" \
  || die "mysqldump failed"

log "Backup created: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# ---- Verify backup is non-empty ----------------------------
[[ -s "$BACKUP_FILE" ]] || die "Backup file is empty!"

# ---- Remote copy via rsync ---------------------------------
log "Copying to remote host $REMOTE_HOST"
rsync -az --timeout=120 \
      "$BACKUP_FILE" \
      "${REMOTE_HOST}:${REMOTE_DIR}/" \
  || log "WARNING: Remote copy failed — local backup retained"

# ---- Retention enforcement ---------------------------------
log "Enforcing retention: keep $KEEP_DAILY daily, $KEEP_WEEKLY weekly"

prune_old_backups() {
    local dir="$1"
    local keep="$2"
    # List by modification time, skip the newest $keep, delete the rest
    ls -1t "${dir}/"*.sql.gz 2>/dev/null \
      | tail -n "+$((keep + 1))" \
      | while read -r f; do
            log "Pruning old backup: $f"
            rm -f "$f"
        done
}

prune_old_backups "${BACKUP_DIR}/daily"  "$KEEP_DAILY"
prune_old_backups "${BACKUP_DIR}/weekly" "$KEEP_WEEKLY"

log "Backup job completed successfully"
```

### 5.2 Backup Verification Script

```bash title="verify_backup.sh"
#!/usr/bin/env bash
# Quick sanity check: decompress + grep for expected tables
BACKUP_FILE="$1"
[[ -z "$BACKUP_FILE" ]] && { echo "Usage: $0 <backup.sql.gz>"; exit 1; }

EXPECTED_TABLES=(students instructors courses sections enrollments grades)

echo "Verifying: $BACKUP_FILE"
for tbl in "${EXPECTED_TABLES[@]}"; do
    if zgrep -q "CREATE TABLE \`${tbl}\`" "$BACKUP_FILE"; then
        echo "  ✓ Table found: $tbl"
    else
        echo "  ✗ MISSING TABLE: $tbl" >&2
    fi
done
echo "Verification complete."
```

---

## 6. Database Health Check Script

### 6.1 Comprehensive Health Monitor

```bash title="db_health_check.sh"
#!/usr/bin/env bash
# ============================================================
# db_health_check.sh
# Checks: replication, long queries, disk space, connections
# Sends alert email if any threshold is exceeded
# ============================================================
set -uo pipefail

readonly ALERT_EMAIL="dba-alerts@university.edu"
readonly MAX_REPLICATION_LAG_SECS=60
readonly MAX_QUERY_RUNTIME_SECS=300
readonly MIN_DISK_FREE_PCT=20
readonly MAX_CONNECTION_PCT=85
ALERTS=()

mysql_q() { mysql --defaults-file=/etc/mysql/monitor.cnf -B -N -e "$1"; }
alert()   { ALERTS+=("$*"); }

# ---- 1. Replication Lag ------------------------------------
check_replication() {
    local lag
    lag=$(mysql_q "SHOW SLAVE STATUS\G" \
          | awk '/Seconds_Behind_Master/ {print $2}' | head -1)

    if [[ "$lag" == "NULL" ]]; then
        alert "REPLICATION: IO or SQL thread is not running!"
    elif [[ -n "$lag" && "$lag" -gt "$MAX_REPLICATION_LAG_SECS" ]]; then
        alert "REPLICATION: Lag is ${lag}s (threshold: ${MAX_REPLICATION_LAG_SECS}s)"
    fi
}

# ---- 2. Long-Running Queries --------------------------------
check_long_queries() {
    local count
    count=$(mysql_q \
      "SELECT COUNT(*) FROM information_schema.PROCESSLIST
       WHERE COMMAND != 'Sleep'
         AND TIME > ${MAX_QUERY_RUNTIME_SECS};")
    if [[ "$count" -gt 0 ]]; then
        local detail
        detail=$(mysql_q \
          "SELECT ID, USER, HOST, DB, TIME, LEFT(INFO,80)
           FROM information_schema.PROCESSLIST
           WHERE COMMAND != 'Sleep' AND TIME > ${MAX_QUERY_RUNTIME_SECS}
           ORDER BY TIME DESC LIMIT 5;")
        alert "LONG QUERIES: $count queries running > ${MAX_QUERY_RUNTIME_SECS}s
$detail"
    fi
}

# ---- 3. Disk Space -----------------------------------------
check_disk_space() {
    local datadir
    datadir=$(mysql_q "SELECT @@datadir;")
    local used_pct
    used_pct=$(df -h "$datadir" | awk 'NR==2 {gsub(/%/,""); print $5}')
    local free_pct=$((100 - used_pct))
    if [[ "$free_pct" -lt "$MIN_DISK_FREE_PCT" ]]; then
        alert "DISK SPACE: Only ${free_pct}% free on MySQL datadir (${datadir})"
    fi
}

# ---- 4. Connection Usage ------------------------------------
check_connections() {
    local max_conn current_conn pct
    max_conn=$(mysql_q "SELECT @@max_connections;")
    current_conn=$(mysql_q "SHOW STATUS LIKE 'Threads_connected';" | awk '{print $2}')
    pct=$(( current_conn * 100 / max_conn ))
    if [[ "$pct" -gt "$MAX_CONNECTION_PCT" ]]; then
        alert "CONNECTIONS: ${current_conn}/${max_conn} (${pct}%) — approaching limit"
    fi
}

# ---- Run all checks -----------------------------------------
check_replication
check_long_queries
check_disk_space
check_connections

# ---- Send alert if needed -----------------------------------
if [[ "${#ALERTS[@]}" -gt 0 ]]; then
    {
        echo "MySQL Health Alert — $(hostname) — $(date)"
        echo "================================================"
        for msg in "${ALERTS[@]}"; do
            echo ""
            echo "⚠️  $msg"
        done
    } | mail -s "[ALERT] MySQL Health Check — $(hostname)" "$ALERT_EMAIL"
    echo "Alert sent to $ALERT_EMAIL"
    exit 1
fi
echo "All health checks passed."
```

---

## 7. Dynamic SQL with PREPARE / EXECUTE

Sometimes you cannot write the full query at development time — table names, column names, or `ORDER BY` clauses must be built at runtime. MySQL's prepared statement syntax handles this:

### 7.1 PREPARE, EXECUTE, DEALLOCATE PREPARE

```sql title="Dynamic SQL fundamentals"
-- Simple dynamic query
SET @table_name = 'students';
SET @sql = CONCAT('SELECT COUNT(*) FROM ', @table_name);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
```

```sql title="Dynamic ORDER BY — cannot use parameters for identifiers"
DELIMITER $$
CREATE PROCEDURE sp_get_students_sorted(
    IN  sort_column VARCHAR(30),
    IN  sort_dir    VARCHAR(4)      -- 'ASC' or 'DESC'
)
BEGIN
    -- Whitelist to prevent SQL injection
    IF sort_column NOT IN ('last_name','first_name','gpa','student_id') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid sort column';
    END IF;

    IF sort_dir NOT IN ('ASC','DESC') THEN
        SET sort_dir = 'ASC';
    END IF;

    SET @dyn_sql = CONCAT(
        'SELECT student_id, first_name, last_name, gpa ',
        'FROM students ORDER BY ', sort_column, ' ', sort_dir
    );

    PREPARE dyn_stmt FROM @dyn_sql;
    EXECUTE dyn_stmt;
    DEALLOCATE PREPARE dyn_stmt;
END$$
DELIMITER ;

CALL sp_get_students_sorted('gpa', 'DESC');
```

!!! danger "SQL Injection Risk in Dynamic SQL"
    Dynamic SQL with user-supplied values is a **major injection vector**. Always:
    
    1. **Whitelist** identifier values (column/table names) — never pass them as parameters directly
    2. **Use parameterised placeholders** (`?`) for data values in `EXECUTE stmt USING @var`
    3. **Validate and sanitise** all inputs before building SQL strings

```sql title="Using USING clause for safe data parameters"
-- Safe: user-supplied DATA goes through USING, not concatenation
SET @dept_id  = 3;
SET @min_gpa  = 3.0;
SET @dyn_sql  = 'SELECT * FROM students
                  WHERE dept_id = ? AND gpa >= ?
                  ORDER BY last_name';

PREPARE dept_stmt FROM @dyn_sql;
EXECUTE dept_stmt USING @dept_id, @min_gpa;
DEALLOCATE PREPARE dept_stmt;
```

---

## 8. Idempotent Migration Scripts

A migration script is **idempotent** if running it multiple times produces the same result as running it once — no errors, no duplicate data, no orphaned objects.

### 8.1 IF NOT EXISTS Patterns

```sql title="Idempotent DDL patterns"
-- Table
CREATE TABLE IF NOT EXISTS schema_version (
    version_id  INT          NOT NULL,
    description VARCHAR(200) NOT NULL,
    applied_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (version_id)
);

-- Column (no native IF NOT EXISTS in MySQL 8 for ADD COLUMN — use a procedure)
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
DELIMITER $$
CREATE PROCEDURE add_column_if_not_exists(
    IN p_table  VARCHAR(64),
    IN p_column VARCHAR(64),
    IN p_def    VARCHAR(256)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE  table_schema = DATABASE()
          AND  table_name   = p_table
          AND  column_name  = p_column
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', p_table,
                          '` ADD COLUMN `', p_column, '` ', p_def);
        PREPARE s FROM @sql;
        EXECUTE s;
        DEALLOCATE PREPARE s;
    END IF;
END$$
DELIMITER ;

CALL add_column_if_not_exists('students', 'middle_name', 'VARCHAR(50) NULL AFTER first_name');
```

### 8.2 Version Table Pattern

```sql title="Version table migration pattern"
-- V001__initial_schema.sql
INSERT IGNORE INTO schema_version (version_id, description)
VALUES (1, 'Initial university schema');

-- V002__add_waitlist.sql
INSERT IGNORE INTO schema_version (version_id, description)
VALUES (2, 'Add waitlist support');

CREATE TABLE IF NOT EXISTS waitlist (
    waitlist_id  INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT      NOT NULL,
    section_id   INT      NOT NULL,
    queued_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_waitlist (student_id, section_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (section_id) REFERENCES sections(section_id)
);
```

### 8.3 Flyway and Liquibase Overview

| Feature | Flyway | Liquibase |
|---------|--------|-----------|
| Script format | Plain SQL or Java | SQL, XML, YAML, JSON |
| Version naming | `V1__desc.sql` | Changeset IDs in changelog |
| State tracking | `flyway_schema_history` table | `DATABASECHANGELOG` table |
| Rollback support | Undo scripts (Teams/Enterprise) | Built-in rollback tags |
| CI/CD integration | Maven/Gradle/CLI plugins | Maven/Gradle/CLI plugins |
| Complexity | Simple — minimal config | More powerful, steeper curve |
| Best for | Simpler projects, SQL-native teams | Complex enterprise migrations |

```bash title="Flyway CLI example"
# Run pending migrations
flyway -url=jdbc:mysql://localhost/university \
       -user=flyway_user \
       -password=flyway_pass \
       -locations=filesystem:./migrations \
       migrate

# Check migration status
flyway info
```

!!! success "Key Takeaway"
    Idempotent migrations — whether hand-rolled or managed by Flyway/Liquibase — are the industry standard for database schema management. They enable safe CI/CD deployment, easy environment synchronisation, and auditable change history.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Batch mode** | Running `mysql` without an interactive prompt; output is tab-separated |
| **Heredoc** | Shell syntax `<<'EOF' ... EOF` to embed multi-line strings as stdin |
| **Event Scheduler** | MySQL subsystem that executes SQL at defined times/intervals |
| **`DEFINER`** | MySQL user whose privileges are used when an event/procedure runs |
| **`ON COMPLETION PRESERVE`** | Keep a one-time event after it fires (vs. auto-drop) |
| **Connection pool** | Pre-created set of database connections shared across threads |
| **`mysql-connector-python`** | Official Oracle Python driver for MySQL |
| **SQLAlchemy Core** | SQL-expression layer of SQLAlchemy; database-agnostic but SQL-explicit |
| **`--single-transaction`** | mysqldump flag; takes consistent InnoDB snapshot without locking |
| **`--master-data=2`** | Embeds binlog position as a comment in the dump file |
| **Retention policy** | Rule governing how many backup files are kept before deletion |
| **`PREPARE`** | MySQL statement that compiles a SQL string into an executable statement |
| **`EXECUTE USING`** | Runs a prepared statement with parameterised values (prevents injection) |
| **`DEALLOCATE PREPARE`** | Frees server memory held by a prepared statement |
| **Idempotent migration** | Script that can be run multiple times without side effects |
| **Schema version table** | Table tracking which migration scripts have been applied |
| **Flyway** | Open-source database migration tool using versioned SQL files |
| **Liquibase** | Open-source migration tool supporting XML/YAML/JSON/SQL changelogs |
| **`ROW_COUNT()`** | MySQL function returning rows affected by the last DML statement |
| **`flock`** | Linux utility to acquire an advisory file lock — prevents duplicate cron jobs |

---

## Self-Assessment

!!! question "Self-Assessment — Week 11"

    **Question 1.** A cron job and a MySQL Event both run the same `DELETE FROM sessions WHERE expires < NOW()` every night. The server is a two-node InnoDB Cluster (primary + secondary). What problem arises with the Event Scheduler setup, and how would you fix it?

    **Question 2.** Your backup script uses `mysqldump --single-transaction`. A teammate argues this flag is unnecessary because the `university` database "doesn't use transactions anyway." Explain what `--single-transaction` actually does, why your teammate is likely wrong about InnoDB tables, and what could go wrong without it.

    **Question 3.** A developer asks you to add a stored procedure that builds a `SELECT` query where the `ORDER BY` column is passed in as a parameter. Write the procedure and explain every security measure you include.

    **Question 4.** Compare executing database migrations with a version table (hand-rolled) versus using Flyway. Give two concrete scenarios where Flyway's approach has a meaningful advantage over the hand-rolled method.

    **Question 5.** The health check script calls `SHOW SLAVE STATUS\G` to get `Seconds_Behind_Master`. Describe two distinct root causes that could cause this counter to rise above your 60-second threshold, and for each cause describe a corrective action.

---

## Further Reading

- [MySQL 8.0 Reference — Event Scheduler](https://dev.mysql.com/doc/refman/8.0/en/event-scheduler.html)
- [MySQL 8.0 Reference — PREPARE Statement](https://dev.mysql.com/doc/refman/8.0/en/prepare.html)
- [mysql-connector-python Developer Guide](https://dev.mysql.com/doc/connector-python/en/)
- [SQLAlchemy Core Tutorial](https://docs.sqlalchemy.org/en/20/core/tutorial.html)
- [Flyway Documentation — Getting Started](https://documentation.red-gate.com/fd)
- [Liquibase Getting Started](https://docs.liquibase.com/start/home.html)
- [The Linux Command Line, 2nd Ed.](https://linuxcommand.org/tlcl.php) — Chapters 24–27 (shell scripting)
- Schwartz, Baron et al. *High Performance MySQL, 4th Ed.* — Chapter 11: Server Administration

---

[← Week 10](week10.md) | [Course Index](index.md) | [Week 12 →](week12.md)
