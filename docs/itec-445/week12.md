---
title: "Week 12 — Backup, Recovery & High Availability"
description: "Master MySQL backup strategies, binary log point-in-time recovery, replication topology, InnoDB Cluster, and cloud-managed high availability."
---

# Week 12 — Backup, Recovery & High Availability

**Course Objectives: CO8** | **Focus: Backup, Recovery, Replication, HA** | **Difficulty: ⭐⭐⭐⭐☆**

---

## Learning Objectives

By the end of this week, you should be able to:

- [ ] Distinguish logical backups from physical backups and select the appropriate type for a given scenario
- [ ] Execute production-grade `mysqldump` commands with all critical flags for consistency and completeness
- [ ] Describe the Percona XtraBackup full and incremental backup workflow including the prepare phase
- [ ] Enable and interpret the MySQL binary log for point-in-time recovery
- [ ] Walk through three real recovery scenarios: dropped table, corrupt data, and server crash
- [ ] Define RTO and RPO and design a backup strategy that meets stated targets
- [ ] Configure basic MySQL replication (source/replica) and verify its health
- [ ] Explain GTID-based replication and its advantages over file-position replication
- [ ] Describe the InnoDB Cluster architecture and how automatic failover works
- [ ] Compare MySQL Router, ProxySQL, and Amazon RDS Multi-AZ for read/write splitting and failover

---

## 1. Backup Fundamentals — Types and Trade-offs

### 1.1 Logical vs Physical Backups

A **logical backup** exports data as SQL statements or delimited text — it is portable, human-readable, and schema-version-agnostic. A **physical backup** copies the raw data files from disk — it is faster for large databases but tied to the MySQL version and binary format.

| Dimension | Logical (mysqldump) | Physical (XtraBackup) |
|-----------|--------------------|-----------------------|
| Output format | SQL text / CSV | Binary InnoDB files |
| Speed (backup) | Slow (row-by-row) | Fast (block-level) |
| Speed (restore) | Slow (re-inserts all rows) | Fast (copy files back) |
| Portability | Any MySQL version | Same major version |
| Human readable | ✅ Yes | ❌ No |
| Selective restore | ✅ Easy (grep/pipe) | ❌ Requires full copy |
| Online (hot) backup | ✅ (with `--single-transaction`) | ✅ (XtraBackup native) |
| Point-in-time restore | Needs binlog on top | Needs binlog on top |
| Typical use case | Smaller DBs, migrations, dev refresh | Multi-GB/TB production |

### 1.2 Hot, Warm, and Cold Backups

| Type | Database state | Locking | Risk |
|------|---------------|---------|------|
| **Hot** | Fully online, serving traffic | None (InnoDB) or minimal | Lowest downtime impact |
| **Warm** | Online but read-only | Tables locked for reads | Brief read interruption |
| **Cold** | Server stopped | N/A — files copied directly | Requires downtime |

!!! warning "Cold Backups Are Almost Never Acceptable in Production"
    Even a 5-minute maintenance window at 2 AM costs money and violates SLAs for global systems. Use hot backup tooling (`--single-transaction` or XtraBackup) instead.

---

## 2. mysqldump Deep Dive

### 2.1 Essential Flags Explained

```bash title="Production mysqldump command"
mysqldump \
  --defaults-file=/etc/mysql/backup.cnf \
  --host=127.0.0.1 \
  --port=3306 \
  \
  --single-transaction \
  # InnoDB: START TRANSACTION WITH CONSISTENT SNAPSHOT.
  # No table locks; consistent point-in-time view.
  \
  --master-data=2 \
  # Writes a CHANGE MASTER TO comment at top of dump.
  # Value 2 = comment (safe); value 1 = active statement.
  # Records exact binlog file + position for PITR.
  \
  --flush-logs \
  # Flushes and rotates binary log immediately before dump.
  # Means recovery only needs logs AFTER this point.
  \
  --routines \
  # Export stored procedures and functions.
  \
  --triggers \
  # Export triggers (included by default, but explicit is safer).
  \
  --events \
  # Export scheduled events.
  \
  --add-drop-table \
  # Prepend DROP TABLE IF EXISTS before each CREATE TABLE.
  # Makes restore idempotent.
  \
  --hex-blob \
  # Export BLOB/BINARY columns as hexadecimal strings.
  # Prevents character encoding corruption.
  \
  --compress \
  # Compress client-server traffic (useful for remote dumps).
  \
  --verbose \
  university \
  | gzip -9 > /var/backups/mysql/university_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 2.2 Dumping Specific Objects

```bash title="Selective mysqldump"
# Single table
mysqldump --defaults-file=/etc/mysql/backup.cnf \
          --single-transaction university students \
          > students_backup.sql

# Multiple databases
mysqldump --defaults-file=/etc/mysql/backup.cnf \
          --databases university hr_system \
          > multi_db_backup.sql

# Schema only (no data)
mysqldump --defaults-file=/etc/mysql/backup.cnf \
          --no-data university > schema_only.sql

# Data only (no schema)
mysqldump --defaults-file=/etc/mysql/backup.cnf \
          --no-create-info university > data_only.sql
```

### 2.3 mysqlpump — Parallel Logical Backup

`mysqlpump` (MySQL 5.7+) parallelises the dump across tables and databases:

```bash title="mysqlpump parallel backup"
mysqlpump \
  --default-parallelism=4 \        # 4 parallel dump threads
  --add-drop-database \
  --exclude-databases=sys,mysql \
  --compress-output=ZLIB \
  university > university_pump.sql.zlib
```

!!! info "mysqldump vs mysqlpump"
    `mysqlpump` can be faster for large multi-table databases but does **not** support `--single-transaction` across all tables simultaneously the same way `mysqldump` does. For strict consistency, `mysqldump --single-transaction` remains the gold standard for logical backups.

---

## 3. Percona XtraBackup

XtraBackup is the open-source standard for hot physical backups of InnoDB databases. It works by copying InnoDB data files while MySQL is running and uses the redo log to make the copy consistent.

### 3.1 Full Backup

```bash title="XtraBackup full backup"
# Install
apt-get install percona-xtrabackup-80   # or yum

# Take full backup
xtrabackup \
  --backup \
  --target-dir=/var/backups/xtrabackup/full_$(date +%Y%m%d) \
  --user=xtrabackup_user \
  --password="$XB_PASS" \
  --host=127.0.0.1 \
  --parallel=4 \
  --compress \
  --compress-threads=4

# Output includes: LSN (Log Sequence Number) in xtrabackup_checkpoints
cat /var/backups/xtrabackup/full_20251001/xtrabackup_checkpoints
# backup_type = full-backuped
# from_lsn = 0
# to_lsn = 1234567
# last_lsn = 1234567
```

### 3.2 Incremental Backup

```bash title="XtraBackup incremental backup"
# After a full backup, take an incremental based on the full's LSN
xtrabackup \
  --backup \
  --target-dir=/var/backups/xtrabackup/inc1_$(date +%Y%m%d) \
  --incremental-basedir=/var/backups/xtrabackup/full_20251001 \
  --user=xtrabackup_user \
  --password="$XB_PASS" \
  --compress

# Second incremental (based on first incremental)
xtrabackup \
  --backup \
  --target-dir=/var/backups/xtrabackup/inc2_$(date +%Y%m%d) \
  --incremental-basedir=/var/backups/xtrabackup/inc1_20251002 \
  --user=xtrabackup_user \
  --password="$XB_PASS"
```

### 3.3 Prepare Phase and Restore

The **prepare** phase applies the redo log to the data files, making them consistent. This step happens *before* you copy files to the target server:

```bash title="XtraBackup prepare and restore"
# Step 1: Decompress
xtrabackup --decompress --target-dir=/var/backups/xtrabackup/full_20251001

# Step 2: Prepare full backup (apply redo log, but keep log open for incrementals)
xtrabackup --prepare --apply-log-only \
  --target-dir=/var/backups/xtrabackup/full_20251001

# Step 3: Apply each incremental in order
xtrabackup --prepare --apply-log-only \
  --target-dir=/var/backups/xtrabackup/full_20251001 \
  --incremental-dir=/var/backups/xtrabackup/inc1_20251002

# Step 4: Final prepare (no --apply-log-only on last incremental)
xtrabackup --prepare \
  --target-dir=/var/backups/xtrabackup/full_20251001 \
  --incremental-dir=/var/backups/xtrabackup/inc2_20251003

# Step 5: Stop MySQL, remove old data directory, copy files
systemctl stop mysql
rm -rf /var/lib/mysql/*
xtrabackup --copy-back \
  --target-dir=/var/backups/xtrabackup/full_20251001
chown -R mysql:mysql /var/lib/mysql
systemctl start mysql
```

!!! danger "Never Skip the Prepare Phase"
    Restoring unprepared XtraBackup files will corrupt your database. The data files have partially-applied transactions in the redo log that must be rolled forward (and uncommitted transactions rolled back) before the files are usable.

---

## 4. Binary Log and Point-in-Time Recovery

### 4.1 Enabling the Binary Log

```ini title="my.cnf — binary log configuration"
[mysqld]
# Enable binary logging
log_bin                  = /var/log/mysql/mysql-bin
binlog_format            = ROW          # ROW | STATEMENT | MIXED
server_id                = 1            # Required; unique across cluster
expire_logs_days         = 7            # Auto-purge after 7 days (or:)
binlog_expire_logs_seconds = 604800     # MySQL 8.0 preferred
max_binlog_size          = 512M         # Rotate when file reaches 512 MB
sync_binlog              = 1            # Flush to disk every write (safest)
binlog_row_image         = FULL         # Log all columns (vs MINIMAL/NOBLOB)
```

| `binlog_format` | What is logged | Pros | Cons |
|----------------|---------------|------|------|
| `STATEMENT` | SQL statement text | Small log size | Non-deterministic functions (NOW(), RAND()) can differ on replica |
| `ROW` | Before/after image of every row | Exact; safe for PITR | Larger log files |
| `MIXED` | STATEMENT normally; ROW for unsafe statements | Balanced | Complex behaviour |

### 4.2 mysqlbinlog Tool

```bash title="Reading and filtering binary logs"
# Show all events in a binlog file
mysqlbinlog /var/log/mysql/mysql-bin.000042

# Filter by time window
mysqlbinlog \
  --start-datetime="2025-10-05 09:00:00" \
  --stop-datetime="2025-10-05 09:30:00" \
  /var/log/mysql/mysql-bin.000042

# Filter by position (from mysqldump --master-data=2 output)
mysqlbinlog \
  --start-position=4 \
  --stop-position=1048576 \
  /var/log/mysql/mysql-bin.000042

# Apply directly to MySQL
mysqlbinlog /var/log/mysql/mysql-bin.000042 \
  | mysql --defaults-file=/etc/mysql/root.cnf
```

### 4.3 Point-in-Time Recovery Workflow

=== "Dropped Table Recovery"

    **Scenario:** `DROP TABLE grades;` was accidentally run at 14:37.
    
    ```bash
    # 1. Restore last nightly backup (e.g., from 02:00)
    gunzip < /var/backups/mysql/university_20251005_020000.sql.gz \
      | mysql --defaults-file=/etc/mysql/root.cnf university
    
    # 2. Find the binlog position of the DROP TABLE event
    mysqlbinlog \
      --start-datetime="2025-10-05 02:00:00" \
      /var/log/mysql/mysql-bin.000043 \
      | grep -n "DROP TABLE"
    # Output: at position 892144 — the DROP TABLE statement
    
    # 3. Replay binlog UP TO the moment just before the DROP
    mysqlbinlog \
      --start-datetime="2025-10-05 02:00:01" \
      --stop-position=892140 \
      /var/log/mysql/mysql-bin.000043 \
      | mysql --defaults-file=/etc/mysql/root.cnf university
    
    # 4. Verify recovery
    mysql --defaults-file=/etc/mysql/root.cnf university \
      -e "SELECT COUNT(*) FROM grades;"
    ```

=== "Data Corruption Recovery"

    **Scenario:** A bad UPDATE statement corrupted 200 rows in `enrollments`.
    
    ```bash
    # 1. Restore latest clean backup
    gunzip < /var/backups/mysql/university_20251005_020000.sql.gz \
      | mysql university
    
    # 2. Find bad UPDATE in binlog (look for suspicious patterns)
    mysqlbinlog \
      --start-datetime="2025-10-05 02:00:00" \
      --database=university \
      /var/log/mysql/mysql-bin.000043 \
      | grep -A5 "UPDATE enrollments"
    # Found at position 445922
    
    # 3. Replay events BEFORE the bad update
    mysqlbinlog \
      --start-datetime="2025-10-05 02:00:01" \
      --stop-position=445918 \
      /var/log/mysql/mysql-bin.000043 \
      | mysql university
    
    # 4. Skip the bad update and continue from after it
    mysqlbinlog \
      --start-position=446500 \
      /var/log/mysql/mysql-bin.000043 \
      | mysql university
    ```

=== "Server Crash Recovery"

    **Scenario:** Server lost power; MySQL won't start cleanly.
    
    ```bash
    # InnoDB crash recovery is usually automatic on restart.
    # If not, force it:
    # In /etc/mysql/mysql.conf.d/mysqld.cnf:
    # innodb_force_recovery = 1  (try 1 first, up to 6 if needed)
    
    systemctl start mysql
    # Monitor error log:
    tail -f /var/log/mysql/error.log
    
    # Once stable, dump data and restore cleanly:
    mysqldump --all-databases > emergency_dump.sql
    # Set innodb_force_recovery back to 0
    # Restart MySQL normally
    mysql < emergency_dump.sql
    ```

!!! warning "innodb_force_recovery Warning"
    Never run in production with `innodb_force_recovery > 0` longer than necessary to extract data. Higher values (4–6) skip undo logs and background threads — data may be inconsistent. Dump and restore ASAP.

---

## 5. RTO, RPO, and Backup Strategy Design

### 5.1 Definitions

| Metric | Full Name | Meaning | Example |
|--------|-----------|---------|---------|
| **RPO** | Recovery Point Objective | Maximum acceptable data loss measured in time | RPO = 1 hour means you can lose at most 1 hour of transactions |
| **RTO** | Recovery Time Objective | Maximum acceptable downtime for recovery | RTO = 30 min means system must be back up within 30 minutes |

### 5.2 Mapping Requirements to Technology

| RPO Target | RTO Target | Strategy |
|------------|------------|----------|
| ≤ 24 hours | Hours acceptable | Daily mysqldump + binlog | 
| ≤ 1 hour | < 2 hours | Hourly XtraBackup incrementals + binlog |
| ≤ 5 minutes | < 30 minutes | Synchronous replication + rapid failover |
| ≤ 0 (zero loss) | < 60 seconds | MySQL Group Replication (synchronous mode) |

!!! tip "Calculating Effective RPO"
    Effective RPO = time of last backup + binlog replay time. If your last backup was at 02:00 and you have continuous binlogs, your RPO at any moment is essentially the time since the last binlog flush (`sync_binlog=1` means every transaction).

---

## 6. MySQL Replication

### 6.1 Source/Replica Setup

=== "Source Configuration"

    ```ini title="source my.cnf"
    [mysqld]
    server_id   = 1
    log_bin     = /var/log/mysql/mysql-bin
    binlog_format = ROW
    ```
    
    ```sql title="Create replication user on source"
    CREATE USER 'repl_user'@'192.168.10.%'
      IDENTIFIED WITH caching_sha2_password BY 'repl_strong_pass';
    
    GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'192.168.10.%';
    FLUSH PRIVILEGES;
    
    -- Get current binlog position
    SHOW MASTER STATUS\G
    -- File: mysql-bin.000001, Position: 157
    ```

=== "Replica Configuration"

    ```ini title="replica my.cnf"
    [mysqld]
    server_id        = 2
    relay_log        = /var/log/mysql/relay-bin
    read_only        = ON          # Prevent accidental writes to replica
    log_slave_updates = ON         # Replica also writes binlog (for chaining)
    ```
    
    ```sql title="Point replica at source"
    CHANGE MASTER TO
      MASTER_HOST      = '192.168.10.10',
      MASTER_PORT      = 3306,
      MASTER_USER      = 'repl_user',
      MASTER_PASSWORD  = 'repl_strong_pass',
      MASTER_LOG_FILE  = 'mysql-bin.000001',
      MASTER_LOG_POS   = 157;
    
    START SLAVE;
    SHOW SLAVE STATUS\G
    ```

### 6.2 GTID-Based Replication

Global Transaction Identifiers (GTIDs) replace file-position tracking with unique transaction IDs. Each transaction gets a GTID in the format `source_uuid:transaction_id`.

```ini title="GTID configuration (both source and replica)"
[mysqld]
gtid_mode            = ON
enforce_gtid_consistency = ON
log_slave_updates    = ON
```

```sql title="GTID replica setup"
CHANGE MASTER TO
  MASTER_HOST     = '192.168.10.10',
  MASTER_USER     = 'repl_user',
  MASTER_PASSWORD = 'repl_strong_pass',
  MASTER_AUTO_POSITION = 1;    -- GTID: no file/position needed!

START SLAVE;
```

**Advantages of GTID replication:**

- Replicas can auto-reconnect to any source in the topology without knowing binlog coordinates
- Easy to promote a replica to source (no coordinate calculation)
- Enables multi-source replication with clear provenance per transaction
- Required for InnoDB Cluster

### 6.3 Monitoring Replication Health

```sql title="Key replication monitoring queries"
-- Primary status check
SHOW SLAVE STATUS\G

-- Critical fields:
-- Slave_IO_Running: Yes          <- IO thread connected to source
-- Slave_SQL_Running: Yes         <- SQL thread applying events
-- Seconds_Behind_Master: 0       <- Lag in seconds (NULL = disconnected)
-- Last_IO_Error:                 <- Most recent IO error message
-- Last_SQL_Error:                <- Most recent SQL error message

-- Detailed monitoring from Performance Schema (MySQL 8.0)
SELECT
    CHANNEL_NAME,
    SERVICE_STATE,
    LAST_ERROR_MESSAGE,
    LAST_ERROR_TIMESTAMP
FROM performance_schema.replication_connection_status;

SELECT
    CHANNEL_NAME,
    SERVICE_STATE,
    LAST_APPLIED_TRANSACTION,
    APPLYING_TRANSACTION,
    LAST_ERROR_MESSAGE
FROM performance_schema.replication_applier_status_by_worker;
```

| Replication Lag Cause | Symptom | Fix |
|----------------------|---------|-----|
| Large transactions on source | Lag spikes then recovers | Batch large updates; increase `slave_parallel_workers` |
| Slow I/O on replica | Persistent lag | Upgrade replica disk (SSD); tune `innodb_flush_method` |
| Network congestion | IO thread falls behind | Compress replication: `MASTER_COMPRESSION_ALGORITHMS` |
| CPU-intensive SQL threads | SQL thread queue builds up | Enable parallel replication (`slave_parallel_type = LOGICAL_CLOCK`) |

---

## 7. InnoDB Cluster and Group Replication

### 7.1 Group Replication Modes

MySQL Group Replication provides multi-master synchronous replication with automatic failure detection and primary election.

=== "Single-Primary Mode"

    - One writable primary at a time; all others are read-only secondaries
    - Automatic primary election on failure (using group membership protocol)
    - Simpler conflict resolution (no write-write conflicts possible)
    - **Recommended for most production workloads**
    
    ```sql
    -- Check which node is primary
    SELECT MEMBER_HOST, MEMBER_ROLE, MEMBER_STATE
    FROM performance_schema.replication_group_members;
    ```

=== "Multi-Primary Mode"

    - All nodes accept writes simultaneously
    - Requires application-level conflict avoidance (same row cannot be written to two nodes simultaneously)
    - Higher risk; suitable for geographically distributed writes
    - Certification-based conflict detection: transactions are rejected post-commit if conflicting

### 7.2 InnoDB Cluster Setup (MySQL Shell)

```python title="MySQL Shell — InnoDB Cluster setup"
# Run in MySQL Shell (mysqlsh)
shell.connect('root@node1:3306')
dba.checkInstanceConfiguration()

# If checks pass:
cluster = dba.createCluster('UniversityCluster')
cluster.addInstance('root@node2:3306')
cluster.addInstance('root@node3:3306')
cluster.status()
```

### 7.3 MySQL Router and ProxySQL

| Feature | MySQL Router | ProxySQL |
|---------|-------------|---------|
| Read/write splitting | ✅ Basic | ✅ Advanced (rule-based) |
| Connection multiplexing | ❌ | ✅ |
| Query caching | ❌ | ✅ |
| Topology discovery | ✅ Auto (InnoDB Cluster) | Manual or heartbeat |
| Config complexity | Low | High |
| Performance overhead | Very low | Low |
| Best with | InnoDB Cluster | Any topology |

---

## 8. Cloud High Availability

### 8.1 Amazon RDS Multi-AZ

Amazon RDS Multi-AZ maintains a synchronous standby replica in a different Availability Zone. Failover is automatic (typically 60–120 seconds) and DNS-based — your connection string does not change.

```bash title="AWS CLI — create RDS Multi-AZ instance"
aws rds create-db-instance \
  --db-instance-identifier university-prod \
  --db-instance-class db.r6g.xlarge \
  --engine mysql \
  --engine-version 8.0.35 \
  --master-username admin \
  --master-user-password "$RDS_PASS" \
  --db-name university \
  --allocated-storage 100 \
  --storage-type gp3 \
  --multi-az \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --deletion-protection
```

### 8.2 Cloud HA Comparison

| Service | Engine | HA mechanism | Failover time | Read replicas |
|---------|--------|--------------|--------------|---------------|
| Amazon RDS Multi-AZ | MySQL 8.0 | Synchronous standby | 60–120s | Up to 5 |
| Amazon Aurora MySQL | Aurora | Shared storage; 6-way replica | < 30s | Up to 15 |
| Google Cloud SQL | MySQL 8.0 | Failover replica | 60–90s | Up to 10 |
| Azure Database for MySQL | MySQL 8.0 | Zone-redundant HA | 60–120s | Up to 5 |

!!! success "Cloud Managed = Automatic Backups"
    All major cloud managed database services include automated daily backups with point-in-time restore (typically 1–35 day retention). This shifts the operational burden of backup management from the DBA to the cloud provider, but you should still verify backup coverage in your SLA.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Logical backup** | Export of data as SQL statements or CSV; portable and human-readable |
| **Physical backup** | Copy of raw InnoDB data files; fast but version-dependent |
| **Hot backup** | Backup taken while the database is running and serving traffic |
| **`--single-transaction`** | mysqldump flag creating a consistent InnoDB snapshot without table locks |
| **`--master-data=2`** | Embeds CHANGE MASTER TO as a comment with binlog file and position |
| **XtraBackup** | Percona's open-source hot physical backup tool for InnoDB |
| **Prepare phase** | XtraBackup step that applies redo log to copied files, making them consistent |
| **Binary log (binlog)** | Ordered log of all changes to MySQL data; used for replication and PITR |
| **binlog_format ROW** | Logs before/after row images; safest for PITR and replication |
| **GTID** | Global Transaction Identifier — unique UUID:sequence for each transaction |
| **Seconds_Behind_Master** | Replica lag metric — seconds behind the source's latest event |
| **RPO** | Recovery Point Objective — maximum acceptable data loss expressed in time |
| **RTO** | Recovery Time Objective — maximum acceptable time to restore service |
| **PITR** | Point-In-Time Recovery — restoring a database to a specific moment using binlog |
| **Group Replication** | MySQL plugin providing synchronous multi-master replication with auto-failover |
| **InnoDB Cluster** | MySQL HA solution combining Group Replication + MySQL Router + MySQL Shell |
| **ProxySQL** | Open-source MySQL proxy supporting advanced read/write splitting and pooling |
| **Multi-AZ** | AWS RDS feature placing a synchronous standby in a different availability zone |
| **Relay log** | File on a replica that buffers events received from the source before applying |
| **`innodb_force_recovery`** | Emergency setting (1–6) to start MySQL after severe InnoDB corruption |

---

## Self-Assessment

!!! question "Self-Assessment — Week 12"

    **Question 1.** Your university database is 800 GB. A mysqldump takes 4 hours to complete. Management wants RPO ≤ 15 minutes and RTO ≤ 30 minutes. Explain why mysqldump alone cannot meet these targets and design a backup architecture (tools, schedule, components) that does.

    **Question 2.** You run `SHOW SLAVE STATUS\G` and observe: `Slave_IO_Running: Yes`, `Slave_SQL_Running: No`, `Last_SQL_Error: Error 'Duplicate entry 1234 for key PRIMARY'`. Explain what happened, why, and describe two different ways to resolve it — one that skips the error and one that is safer long-term.

    **Question 3.** A developer accidentally ran `UPDATE students SET gpa = 0.0;` without a WHERE clause at 11:42 AM today. Your last backup was at 2:00 AM. You have continuous binary logging enabled. Outline the exact recovery steps in order, including the specific mysqlbinlog flags you would use and how you would identify the position of the erroneous statement.

    **Question 4.** Compare GTID-based replication with traditional binary log file/position replication across four dimensions: failover complexity, multi-source replication support, compatibility with backup tools, and operational risk during topology changes.

    **Question 5.** Your team is debating between deploying MySQL InnoDB Cluster (with MySQL Router) versus using Amazon RDS Multi-AZ. List three factors that would favor each option, and describe the scenario where you would choose InnoDB Cluster over RDS.

---

## Further Reading

- [MySQL 8.0 Backup and Recovery](https://dev.mysql.com/doc/refman/8.0/en/backup-and-recovery.html)
- [Percona XtraBackup Documentation](https://docs.percona.com/percona-xtrabackup/latest/)
- [MySQL 8.0 Binary Log](https://dev.mysql.com/doc/refman/8.0/en/binary-log.html)
- [MySQL 8.0 Replication](https://dev.mysql.com/doc/refman/8.0/en/replication.html)
- [MySQL InnoDB Cluster Documentation](https://dev.mysql.com/doc/mysql-shell/8.0/en/mysql-innodb-cluster.html)
- [ProxySQL Documentation](https://proxysql.com/documentation/)
- [Amazon RDS Multi-AZ Deployments](https://aws.amazon.com/rds/features/multi-az/)
- Schwartz, Baron et al. *High Performance MySQL, 4th Ed.* — Chapters 9 & 10

---

[← Week 11](week11.md) | [Course Index](index.md) | [Week 13 →](week13.md)
