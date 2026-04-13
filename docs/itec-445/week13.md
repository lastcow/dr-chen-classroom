---
title: "Week 13 — Monitoring, Performance Tuning & Server Administration"
description: "Use the Performance Schema, sys schema, InnoDB internals, and OS-level tools to diagnose and resolve MySQL performance problems in production."
---

# Week 13 — Monitoring, Performance Tuning & Server Administration

**Course Objectives: CO8** | **Focus: Performance Tuning, Monitoring, Administration** | **Difficulty: ⭐⭐⭐⭐☆**

---

## Learning Objectives

By the end of this week, you should be able to:

- [ ] Query the Performance Schema to identify the top SQL statements by latency and wait events
- [ ] Use the `sys` schema convenience views to diagnose I/O, connections, and slow statements
- [ ] Set the five most impactful MySQL server variables correctly for a given hardware profile
- [ ] Describe what each InnoDB subsystem (buffer pool, redo log, change buffer, doublewrite) does and how it affects write performance
- [ ] Identify and terminate long-running or blocking queries using `SHOW PROCESSLIST` and `KILL`
- [ ] Read a deadlock report from `SHOW ENGINE INNODB STATUS` and identify the conflicting transactions
- [ ] Choose when to run `OPTIMIZE TABLE`, `ANALYZE TABLE`, `CHECK TABLE`, or `REPAIR TABLE`
- [ ] Measure MySQL disk I/O using OS tools (`iostat`, `df`, `du`) and Performance Schema file summary tables
- [ ] Compare PMM, MySQL Enterprise Monitor, and Prometheus/Grafana for monitoring architecture
- [ ] Diagnose OS-level memory pressure, swap usage, and OOM events that impact MySQL

---

## 1. MySQL Performance Schema

The Performance Schema (`performance_schema` database) is an instrumentation engine built into MySQL that collects metrics about query execution, wait events, I/O, memory, and network — with sub-microsecond precision.

### 1.1 Architecture — Instruments and Consumers

```sql title="Performance Schema control tables"
-- List all instrument categories
SELECT SUBSTRING_INDEX(NAME, '/', 1) AS category, COUNT(*) AS cnt
FROM   performance_schema.setup_instruments
GROUP  BY category
ORDER  BY cnt DESC;

-- Enable all statement instruments (usually already on)
UPDATE performance_schema.setup_instruments
SET    ENABLED = 'YES', TIMED = 'YES'
WHERE  NAME LIKE 'statement/%';

-- Enable all consumers (where data is stored)
UPDATE performance_schema.setup_consumers
SET    ENABLED = 'YES'
WHERE  NAME LIKE '%statements%'
   OR  NAME LIKE '%waits%';
```

!!! info "Performance Schema Overhead"
    The Performance Schema is designed for always-on use. At typical settings, it adds 3–5% CPU overhead. Enabling every instrument simultaneously can increase this, so in extreme OLTP scenarios be selective about which instruments are active.

### 1.2 Key Performance Schema Tables

=== "Statement Summary"

    ```sql title="Top SQL by total latency"
    SELECT
        DIGEST_TEXT,
        COUNT_STAR               AS exec_count,
        ROUND(SUM_TIMER_WAIT / 1e12, 3)  AS total_latency_s,
        ROUND(AVG_TIMER_WAIT   / 1e9,  3)  AS avg_latency_ms,
        SUM_ROWS_EXAMINED,
        SUM_ROWS_SENT,
        ROUND(SUM_ROWS_EXAMINED / NULLIF(SUM_ROWS_SENT, 0), 1) AS rows_examined_per_sent
    FROM performance_schema.events_statements_summary_by_digest
    ORDER BY SUM_TIMER_WAIT DESC
    LIMIT 10;
    ```
    
    The `rows_examined_per_sent` ratio tells you query efficiency. A ratio of 1000 means the engine scanned 1000 rows to return 1 — a strong signal of a missing index.

=== "Wait Events Summary"

    ```sql title="Top wait events by total time"
    SELECT
        EVENT_NAME,
        COUNT_STAR             AS wait_count,
        ROUND(SUM_TIMER_WAIT / 1e12, 3) AS total_wait_s,
        ROUND(AVG_TIMER_WAIT  / 1e9, 3) AS avg_wait_ms
    FROM performance_schema.events_waits_summary_global_by_event_name
    WHERE SUM_TIMER_WAIT > 0
    ORDER BY SUM_TIMER_WAIT DESC
    LIMIT 15;
    ```
    
    Common top wait events and their meanings:
    
    | Wait Event | Meaning | Typical Fix |
    |-----------|---------|-------------|
    | `wait/io/file/innodb/innodb_data_file` | InnoDB data file I/O | Faster disk, larger buffer pool |
    | `wait/io/file/sql/binlog` | Binary log writes | SSD for binlog, tune `sync_binlog` |
    | `wait/synch/mutex/innodb/buf_pool_mutex` | Buffer pool contention | Split buffer pool into multiple instances |
    | `wait/lock/table/sql/handler` | Table-level lock waits | Convert MyISAM to InnoDB |
    | `wait/synch/rwlock/innodb/dict_operation_lock` | Data dictionary lock | Reduce DDL frequency |

=== "File I/O Summary"

    ```sql title="Top files by I/O bytes"
    SELECT
        FILE_NAME,
        COUNT_READ,
        COUNT_WRITE,
        ROUND(SUM_NUMBER_OF_BYTES_READ  / 1048576, 1) AS read_mb,
        ROUND(SUM_NUMBER_OF_BYTES_WRITE / 1048576, 1) AS write_mb
    FROM performance_schema.file_summary_by_instance
    WHERE SUM_NUMBER_OF_BYTES_READ + SUM_NUMBER_OF_BYTES_WRITE > 0
    ORDER BY SUM_NUMBER_OF_BYTES_READ + SUM_NUMBER_OF_BYTES_WRITE DESC
    LIMIT 10;
    ```

### 1.3 Resetting Performance Schema Counters

```sql title="Reset Performance Schema accumulated stats"
-- Reset statement digests
TRUNCATE TABLE performance_schema.events_statements_summary_by_digest;

-- Reset wait summaries
TRUNCATE TABLE performance_schema.events_waits_summary_global_by_event_name;

-- Reset file I/O
TRUNCATE TABLE performance_schema.file_summary_by_instance;
```

---

## 2. The sys Schema

The `sys` schema (shipped with MySQL 5.7.7+) provides curated views over Performance Schema data, formatted for human readability (bytes → MB, picoseconds → ms).

### 2.1 Most Useful sys Views

```sql title="sys schema diagnostic queries"
-- Top statements by runtime (95th percentile latency)
SELECT query, exec_count, avg_latency, rows_examined_avg
FROM   sys.statements_with_runtimes_in_95th_percentile
ORDER  BY avg_latency DESC
LIMIT  10;

-- Global I/O by file in MB
SELECT file, total_read, total_written, total
FROM   sys.io_global_by_file_by_bytes
ORDER  BY total DESC
LIMIT  10;

-- User connection summary
SELECT user, total_connections, current_connections,
       statement_avg_latency, rows_examined_avg
FROM   sys.user_summary
ORDER  BY current_connections DESC;

-- Tables with full table scans
SELECT object_schema, object_name, count_read,
       rows_full_scanned, latency
FROM   sys.schema_tables_with_full_table_scans
ORDER  BY rows_full_scanned DESC
LIMIT  10;

-- Indexes never used
SELECT object_schema, object_name, index_name
FROM   sys.schema_unused_indexes
WHERE  object_schema = 'university';

-- Current blocking transactions
SELECT waiting_query, waiting_age, blocking_query,
       blocking_pid
FROM   sys.innodb_lock_waits;
```

!!! tip "Start Your Diagnosis with `sys` Schema"
    When troubleshooting an unknown performance problem, start with `sys.statements_with_runtimes_in_95th_percentile` and `sys.schema_tables_with_full_table_scans`. These two views identify the most common root causes (slow queries and missing indexes) in under a minute.

---

## 3. Key Server Variables to Tune

### 3.1 The Most Impactful Variables

```ini title="Production-tuned my.cnf — annotated"
[mysqld]
# ============================================================
# InnoDB Buffer Pool — THE most important variable.
# Rule: 70-80% of available RAM on a dedicated MySQL server.
# On a 32 GB server: 24-26 GB
# ============================================================
innodb_buffer_pool_size     = 24G

# Multiple instances reduce mutex contention. Use 1 per GB
# of buffer pool, up to 64.
innodb_buffer_pool_instances = 24

# ============================================================
# InnoDB Redo Log
# Larger = less frequent checkpoints = better write throughput.
# But: longer crash recovery time.
# MySQL 8.0.30+: use innodb_redo_log_capacity instead.
# ============================================================
innodb_log_file_size        = 2G        # MySQL 8.0 < 8.0.30
# innodb_redo_log_capacity  = 4G        # MySQL 8.0.30+

# ============================================================
# Flush behaviour
# 1 = safest (flush log + data at commit) — use for financial
# 2 = flush log once per second; data at commit — safe compromise
# 0 = flush once per second only — highest throughput, data loss risk
# ============================================================
innodb_flush_log_at_trx_commit = 1

# ============================================================
# Connections
# Each connection = ~1 MB RAM (thread stack + buffers).
# On 32 GB server, ~500-1000 is reasonable.
# Use ProxySQL/connection pooling to limit actual connections.
# ============================================================
max_connections             = 500
thread_cache_size           = 100       # Reuse threads; reduce create cost

# ============================================================
# Temporary tables (for GROUP BY, ORDER BY, subqueries)
# If tmp_table exceeds this, spills to disk (slow!)
# ============================================================
tmp_table_size              = 128M
max_heap_table_size         = 128M      # Must match tmp_table_size

# ============================================================
# Sort / join buffers (per-connection, not global pool)
# Increase only for specific slow queries, not globally
# ============================================================
sort_buffer_size            = 2M
join_buffer_size            = 4M
read_rnd_buffer_size        = 2M

# ============================================================
# Query cache — DEPRECATED in MySQL 5.7, REMOVED in 8.0
# Do NOT use. Acts as a global mutex under write load.
# ============================================================
# query_cache_type = 0   (default in 8.0 — already off)

# ============================================================
# Slow query log — essential for production tuning
# ============================================================
slow_query_log              = ON
slow_query_log_file         = /var/log/mysql/slow.log
long_query_time             = 1.0       # Log queries > 1 second
log_queries_not_using_indexes = ON
```

### 3.2 Variable Tuning Decision Table

| Variable | Default | Conservative | Aggressive | Notes |
|----------|---------|-------------|-----------|-------|
| `innodb_buffer_pool_size` | 128M | 50% RAM | 80% RAM | Dedicated server: 70-80% |
| `innodb_log_file_size` | 48M | 512M | 4G | Bigger = less I/O, slower crash recovery |
| `innodb_flush_log_at_trx_commit` | 1 | 1 | 2 | Never set 0 for OLTP |
| `max_connections` | 151 | 200 | 2000 | Balance with memory; use pooling |
| `tmp_table_size` | 16M | 64M | 256M | Per-connection; watch total RAM |

---

## 4. InnoDB Internals That Affect Performance

### 4.1 The Buffer Pool

The buffer pool is the most critical InnoDB memory structure — it caches data pages and index pages to avoid disk reads.

```
┌─────────────────────────────────────────────────────┐
│                   Buffer Pool                       │
│                                                     │
│  ┌──────────────┐   ┌──────────────┐               │
│  │  Data Pages  │   │ Index Pages  │               │
│  │  (16 KB each)│   │  (B-Tree)    │               │
│  └──────────────┘   └──────────────┘               │
│                                                     │
│  LRU List: [New sublist (5/8)] | [Old sublist (3/8)]│
│  • Newly read pages enter Old sublist head          │
│  • Stay in Old if accessed within innodb_old_blocks_time│
│  • Promoted to New sublist head on second access    │
└─────────────────────────────────────────────────────┘
```

```sql title="Buffer pool statistics"
SHOW STATUS LIKE 'Innodb_buffer_pool%';
-- Key metrics:
-- Innodb_buffer_pool_read_requests: Total read requests
-- Innodb_buffer_pool_reads:         Reads that required disk I/O
-- Hit rate = 1 - (reads / read_requests) — target > 99%

SELECT
    ROUND(100 * (1 - (
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status
         WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads')
        /
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status
         WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
    )), 2) AS buffer_pool_hit_rate_pct;
```

### 4.2 InnoDB Subsystems Summary

| Subsystem | What it does | Performance Impact |
|-----------|-------------|-------------------|
| **Buffer Pool** | Caches data and index pages in RAM | #1 factor; larger = fewer disk reads |
| **Change Buffer** | Batches secondary index changes for non-resident pages | Reduces random I/O for INSERT/UPDATE; coalesced on page load |
| **Redo Log** | Write-ahead log ensuring durability | Sequential writes are fast; larger log = fewer checkpoints |
| **Undo Log** | Stores old row versions for MVCC and rollback | Long transactions bloat undo; purge thread reclaims space |
| **Doublewrite Buffer** | Writes pages to a separate area before the real data files | Prevents partial-page writes during crash; ~5% write overhead |

### 4.3 InnoDB Status Deep Dive

```sql title="SHOW ENGINE INNODB STATUS sections"
SHOW ENGINE INNODB STATUS\G
-- Sections to read:
-- BUFFER POOL AND MEMORY: hit rate, dirty pages, free pages
-- ROW OPERATIONS: rows inserted/read/updated/deleted/s
-- LOG: LSN, checkpoint, log waits (if > 0, redo log is too small)
-- TRANSACTIONS: active transactions, lock waits
-- LATEST DETECTED DEADLOCK: last deadlock graph
```

---

## 5. Managing Long-Running Queries and Deadlocks

### 5.1 Finding and Killing Long-Running Queries

```sql title="Process list investigation"
-- Quick overview
SHOW FULL PROCESSLIST;

-- Filtered view — queries running > 30 seconds
SELECT
    ID, USER, HOST, DB,
    COMMAND, TIME, STATE,
    LEFT(INFO, 120) AS query_snippet
FROM information_schema.PROCESSLIST
WHERE COMMAND NOT IN ('Sleep', 'Binlog Dump')
  AND TIME > 30
ORDER BY TIME DESC;

-- Kill a specific query (keeps connection open)
KILL QUERY 1042;

-- Kill entire connection
KILL 1042;
```

```bash title="Script to kill all queries over threshold"
#!/usr/bin/env bash
# kill_long_queries.sh — kill queries running > 5 minutes
THRESHOLD=300

mysql --defaults-file=/etc/mysql/dba.cnf -B -N \
  -e "SELECT ID FROM information_schema.PROCESSLIST
      WHERE COMMAND NOT IN ('Sleep','Binlog Dump')
        AND TIME > ${THRESHOLD};" \
| while read -r pid; do
    echo "Killing PID $pid (running > ${THRESHOLD}s)"
    mysql --defaults-file=/etc/mysql/dba.cnf -e "KILL QUERY ${pid};"
done
```

### 5.2 Deadlock Analysis

A **deadlock** occurs when two transactions each hold a lock the other needs, creating a circular wait. InnoDB automatically detects deadlocks and rolls back the transaction with the lower cost (usually the one that modified fewer rows).

```sql title="Reading the deadlock report"
SHOW ENGINE INNODB STATUS\G
-- Look for LATEST DETECTED DEADLOCK section:
--
-- TRANSACTION 1, ACTIVE 2 sec starting index read
-- MySQL thread id 45, OS thread id 140..., query id 8921 localhost app_user
-- UPDATE enrollments SET status='enrolled' WHERE section_id=10 AND student_id=201
-- WAITING FOR THIS LOCK TO BE GRANTED:
-- RECORD LOCKS space id 234 page no 7 n bits 72 index PRIMARY
-- of table `university`.`enrollments` trx id 42001 lock_mode X locks rec
--
-- TRANSACTION 2, ACTIVE 2 sec starting index read
-- UPDATE sections SET enrolled_count=enrolled_count+1 WHERE section_id=10
-- HOLDS THE LOCK(S):
-- RECORD LOCKS ... index PRIMARY of table `university`.`sections`
-- WAITING FOR THIS LOCK TO BE GRANTED:
-- RECORD LOCKS ... index PRIMARY of table `university`.`enrollments`
```

**Deadlock prevention strategies:**

```sql title="Consistent lock ordering prevents deadlocks"
-- BAD: Transaction A locks enrollments then sections
--      Transaction B locks sections then enrollments  → DEADLOCK

-- GOOD: Both transactions always lock in the same order
-- Procedure sp_enroll_student: ALWAYS lock sections first, then enrollments
BEGIN;
    SELECT * FROM sections    WHERE section_id = 10 FOR UPDATE;  -- 1st
    SELECT * FROM enrollments WHERE student_id  = 201
                               AND section_id   = 10 FOR UPDATE; -- 2nd
    -- ... rest of logic
COMMIT;
```

| Deadlock Prevention Strategy | How It Works |
|------------------------------|-------------|
| **Consistent lock ordering** | All transactions acquire locks in the same order on the same tables |
| **Short transactions** | Minimise the time locks are held; commit quickly |
| **Avoid user interaction mid-transaction** | Don't leave a transaction open waiting for user input |
| **Use `SELECT ... FOR UPDATE` early** | Acquire the lock at the start rather than upgrading a shared lock |
| **Index your WHERE clauses** | Without an index, InnoDB may escalate to next-key or gap locks |

---

## 6. Table Maintenance Operations

```sql title="Table maintenance commands"
-- ANALYZE TABLE: Update statistics used by the query optimizer.
-- Run after large bulk loads or significant data changes.
ANALYZE TABLE students, enrollments, sections;

-- OPTIMIZE TABLE: Rebuild table to reclaim fragmented space and
-- re-sort data. Equivalent to ALTER TABLE ... ENGINE=InnoDB.
-- WARNING: Takes a full table copy — use during maintenance window.
OPTIMIZE TABLE audit_log;   -- Good for tables with heavy deletes

-- CHECK TABLE: Verify table integrity (mostly useful for MyISAM).
-- For InnoDB, equivalent to CHECK TABLESPACE.
CHECK TABLE enrollments EXTENDED;

-- REPAIR TABLE: Attempt to repair corrupted MyISAM table.
-- InnoDB tables cannot be repaired this way; restore from backup.
REPAIR TABLE myisam_legacy_table;
```

| Operation | Engine | Use When | Side Effect |
|-----------|--------|----------|-------------|
| `ANALYZE TABLE` | InnoDB, MyISAM | After bulk load, unusual query plans | Minimal lock, fast |
| `OPTIMIZE TABLE` | InnoDB | High fragmentation (many DELETEs) | Full table rebuild, MDL lock |
| `CHECK TABLE` | MyISAM mainly | Suspected corruption | Read lock |
| `REPAIR TABLE` | MyISAM only | Corruption confirmed | Exclusive lock, data risk |

!!! warning "OPTIMIZE TABLE on Large InnoDB Tables"
    On a 100 GB InnoDB table, `OPTIMIZE TABLE` can take hours and holds a metadata lock preventing concurrent DDL. For online defragmentation without a full lock, use `ALTER TABLE t ENGINE=InnoDB` with the `ALGORITHM=INPLACE` option (MySQL 8.0) or `pt-online-schema-change` from Percona Toolkit.

---

## 7. Disk and I/O Monitoring

### 7.1 Operating System Tools

```bash title="OS-level I/O monitoring"
# iostat: device-level I/O statistics
# -x = extended stats, -d = device only, 2 = refresh every 2s, 5 = 5 samples
iostat -xd 2 5
# Key columns:
# %util  — how busy the device is (>80% = saturated)
# await  — average I/O wait (ms); < 1ms NVMe, < 5ms SSD, < 20ms HDD
# r/s, w/s — reads and writes per second

# Disk space
df -h /var/lib/mysql    # Free space on MySQL data directory
du -sh /var/lib/mysql/* | sort -rh | head -20   # Largest files

# Real-time I/O by process
iotop -oP    # Show only processes doing I/O; requires root
```

### 7.2 MySQL I/O from Performance Schema

```sql title="I/O-intensive tables via Performance Schema"
-- Which tablespace files are generating the most I/O?
SELECT
    SUBSTRING_INDEX(FILE_NAME, '/', -1) AS filename,
    COUNT_READ,
    COUNT_WRITE,
    ROUND(SUM_NUMBER_OF_BYTES_READ  / 1048576, 1) AS read_MB,
    ROUND(SUM_NUMBER_OF_BYTES_WRITE / 1048576, 1) AS write_MB,
    ROUND((SUM_TIMER_READ + SUM_TIMER_WRITE) / 1e12, 3) AS total_io_s
FROM performance_schema.file_summary_by_instance
WHERE FILE_NAME LIKE '%university%'
ORDER BY total_io_s DESC
LIMIT 10;
```

---

## 8. MySQL Monitoring Tools

### 8.1 Percona Monitoring and Management (PMM)

PMM is an open-source, fully featured MySQL (and PostgreSQL) monitoring platform built on Prometheus and Grafana.

```bash title="PMM 2 server and agent setup"
# Deploy PMM Server (Docker)
docker pull percona/pmm-server:2
docker run -d \
  --name pmm-server \
  -p 443:443 \
  -v pmm-data:/srv \
  percona/pmm-server:2

# Install PMM Client on MySQL host
apt-get install -y pmm2-client

# Register client with server
pmm-admin config --server-insecure-tls \
  --server-url="https://admin:admin@pmm-server:443"

# Add MySQL instance
pmm-admin add mysql \
  --username=pmm_user \
  --password=pmm_pass \
  --query-source=perfschema \
  --service-name=university-prod
```

### 8.2 Prometheus + mysqld_exporter

```yaml title="prometheus.yml scrape config"
scrape_configs:
  - job_name: 'mysql'
    static_configs:
      - targets: ['mysql-host:9104']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
```

```bash title="mysqld_exporter setup"
# Download and install
wget https://github.com/prometheus/mysqld_exporter/releases/download/v0.15.1/mysqld_exporter-0.15.1.linux-amd64.tar.gz
tar xvf mysqld_exporter-*.tar.gz

# Create MySQL user for exporter
mysql -e "CREATE USER 'exporter'@'127.0.0.1'
            IDENTIFIED BY 'exporter_pass' WITH MAX_USER_CONNECTIONS 3;
          GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'127.0.0.1';"

# Run exporter
./mysqld_exporter \
  --config.my-cnf=/etc/mysql/exporter.cnf \
  --collect.info_schema.processlist \
  --collect.info_schema.innodb_metrics \
  --collect.perf_schema.eventsstatements \
  --web.listen-address=":9104"
```

### 8.3 Monitoring Tool Comparison

| Feature | PMM | MySQL Enterprise Monitor | Prometheus + Grafana |
|---------|-----|--------------------------|---------------------|
| Cost | Free (open source) | Paid (Oracle license) | Free (open source) |
| Setup complexity | Medium (Docker) | Low (agent only) | High (custom dashboards) |
| MySQL-specific dashboards | ✅ Rich, pre-built | ✅ Rich, pre-built | ⚠️ Community dashboards |
| Query analytics | ✅ QAN included | ✅ | ❌ (not built-in) |
| Alerting | ✅ Grafana-based | ✅ Built-in | ✅ Alertmanager |
| Multi-DB support | ✅ (MySQL, PG, MongoDB) | MySQL only | ✅ Any exporter |

---

## 9. Operating System Level Tuning

### 9.1 Memory Pressure and the OOM Killer

```bash title="OOM killer and swap monitoring"
# Check if OOM killer has fired on MySQL
dmesg | grep -i "out of memory"
grep "mysql" /var/log/kern.log | grep -i "killed"

# Current swap usage
free -h
vmstat -s | grep -i swap

# MySQL-specific memory usage
ps -o pid,vsz,rss,comm -p $(pgrep mysqld)

# Protect MySQL from OOM killer (lower score = less likely to be killed)
echo -1000 > /proc/$(pgrep mysqld)/oom_score_adj
# To persist: add to systemd service file:
# OOMScoreAdjust=-900
```

### 9.2 OS Tuning for MySQL

```bash title="OS kernel parameters for MySQL performance"
# Add to /etc/sysctl.conf:

# Virtual memory — reduce swappiness (MySQL prefers RAM over swap)
vm.swappiness = 1

# Network — for high-connection servers
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# File descriptors — MySQL may need many open files
fs.file-max = 65536

# Apply immediately
sysctl -p

# MySQL ulimit (file descriptors)
# In /etc/security/limits.conf:
# mysql soft nofile 65536
# mysql hard nofile 65536

# Disable transparent huge pages (causes latency spikes with InnoDB)
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

!!! danger "Transparent Huge Pages and MySQL"
    Transparent Huge Pages (THP) are a Linux memory optimisation that causes severe, unpredictable latency spikes in MySQL and other databases. Always disable THP on MySQL servers. This is one of the most common tuning mistakes found in production environments.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Performance Schema** | MySQL instrumentation database collecting metrics on statements, waits, I/O, and memory |
| **setup_instruments** | Table controlling which events the Performance Schema measures |
| **setup_consumers** | Table controlling which tables store collected Performance Schema data |
| **sys schema** | Collection of views over Performance Schema formatted for human readability |
| **Digest** | Normalised SQL fingerprint that groups similar queries regardless of literal values |
| **Buffer pool hit rate** | Percentage of data page reads served from RAM rather than disk; target > 99% |
| **Change buffer** | InnoDB structure that batches secondary index modifications for pages not in the buffer pool |
| **Redo log** | Write-ahead log ensuring committed transactions survive a crash |
| **Undo log** | Storage for old row versions enabling MVCC and transaction rollback |
| **Doublewrite buffer** | InnoDB mechanism writing pages twice to prevent partial-write corruption |
| **`innodb_flush_log_at_trx_commit`** | Controls how aggressively the redo log is flushed to disk; value 1 = safest |
| **`innodb_buffer_pool_size`** | Amount of RAM allocated to the InnoDB buffer pool; most impactful variable |
| **Deadlock** | Circular lock wait between two or more transactions; InnoDB auto-detects and resolves |
| **`KILL QUERY`** | Terminates the executing statement on a connection without closing the connection |
| **`OPTIMIZE TABLE`** | Rebuilds an InnoDB table to reclaim space after heavy deletions |
| **`ANALYZE TABLE`** | Updates table statistics used by the query optimiser |
| **OOM killer** | Linux kernel mechanism that kills processes to free memory under extreme pressure |
| **`vm.swappiness`** | Kernel parameter controlling aggressiveness of swapping RAM to disk; set to 1 for MySQL |
| **PMM** | Percona Monitoring and Management — open-source MySQL and multi-DB monitoring platform |
| **Transparent Huge Pages** | Linux memory feature that causes latency spikes in MySQL; should be disabled |

---

## Self-Assessment

!!! question "Self-Assessment — Week 13"

    **Question 1.** You query `sys.statements_with_runtimes_in_95th_percentile` and find that a query against the `enrollments` table has `rows_examined_avg = 45000` but `rows_sent_avg = 3`. What does this ratio tell you, and what two diagnostic steps would you take next to determine the root cause and fix?

    **Question 2.** Your server has 64 GB RAM and is dedicated to MySQL. A junior DBA set `innodb_buffer_pool_size = 4G`. Calculate the ideal value and explain what happens at the OS level when the buffer pool is too small — specifically what you would see in the `Innodb_buffer_pool_reads` status variable and in `iostat` output.

    **Question 3.** Explain the purpose of `innodb_flush_log_at_trx_commit` and describe the durability vs performance trade-off for values 0, 1, and 2. Under what circumstances would you accept value 2 instead of 1 in a production system?

    **Question 4.** You observe this in `SHOW ENGINE INNODB STATUS`: two transactions deadlocked on the `sections` and `enrollments` tables. Transaction A holds a lock on `sections(section_id=10)` and waits for `enrollments`, while Transaction B holds `enrollments` and waits for `sections`. Identify the root cause and rewrite the transaction logic to prevent this deadlock without removing any of the business logic.

    **Question 5.** A developer has disabled Transparent Huge Pages on the test server but cannot do so on production because the sysadmin team controls kernel settings. Name two other OS-level or MySQL-level settings you would prioritise to compensate, and explain the mechanism by which each setting helps MySQL performance.

---

## Further Reading

- [MySQL 8.0 Performance Schema](https://dev.mysql.com/doc/refman/8.0/en/performance-schema.html)
- [MySQL 8.0 sys Schema](https://dev.mysql.com/doc/refman/8.0/en/sys-schema.html)
- [Percona PMM Documentation](https://docs.percona.com/percona-monitoring-and-management/latest/)
- [mysqld_exporter GitHub](https://github.com/prometheus/mysqld_exporter)
- [MySQL InnoDB Architecture](https://dev.mysql.com/doc/refman/8.0/en/innodb-architecture.html)
- Schwartz, Baron et al. *High Performance MySQL, 4th Ed.* — Chapters 3, 5, 8
- [Percona Blog: InnoDB Deadlock Detection](https://www.percona.com/blog/innodb-deadlock-detection-performance/)
- [Linux Performance, Brendan Gregg](https://www.brendangregg.com/linuxperf.html)

---

[← Week 12](week12.md) | [Course Index](index.md) | [Week 14 →](week14.md)
