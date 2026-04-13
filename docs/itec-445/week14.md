---
title: "Week 14 — NoSQL, NewSQL & Cloud Database Systems"
description: "Explore the CAP theorem, NoSQL paradigms (document, key-value, column-family, graph), NewSQL distributed databases, cloud services, and polyglot persistence patterns."
---

# Week 14 — NoSQL, NewSQL & Cloud Database Systems

**Course Objectives: CO8, CO9** | **Focus: NoSQL, NewSQL, Cloud Databases** | **Difficulty: ⭐⭐⭐☆☆**

---

## Learning Objectives

By the end of this week, you should be able to:

- [ ] Explain the CAP theorem and classify real database systems as CP, AP, or CA
- [ ] Describe the four primary NoSQL paradigms and give real-world use cases for each
- [ ] Write MongoDB CRUD operations and basic aggregation pipeline stages
- [ ] Compare MongoDB schema design patterns — embedding vs referencing — for a given workload
- [ ] Explain Redis data structures and implement common caching and session patterns
- [ ] Describe how NewSQL systems (Spanner, CockroachDB, TiDB) achieve horizontal scale with ACID
- [ ] Use MySQL's JSON data type with `JSON_EXTRACT`, `JSON_TABLE`, and generated column indexes
- [ ] Compare major cloud database services across pricing, features, and appropriate use cases
- [ ] Apply a structured database selection framework to a real scenario
- [ ] Design a polyglot persistence architecture for a multi-service application

---

## 1. The CAP Theorem

### 1.1 The Three Properties

The **CAP Theorem** (Brewer, 2000; formally proven by Gilbert and Lynch, 2002) states that a distributed data store can provide at most **two** of the following three guarantees simultaneously:

| Property | Meaning |
|----------|---------|
| **C — Consistency** | Every read receives the most recent write or an error. All nodes see the same data at the same time. |
| **A — Availability** | Every request receives a (non-error) response, though the response may not contain the most recent data. |
| **P — Partition Tolerance** | The system continues to operate even when network messages between nodes are lost or delayed. |

!!! info "Partition Tolerance is Not Optional"
    In any real distributed system, network partitions *will* occur. You cannot simply "choose" not to have partition tolerance. The real trade-off in practice is: **when a partition occurs, do you sacrifice Consistency or Availability?** This makes the practical choice CP vs AP.

### 1.2 Real System Classifications

| System | Type | Trade-off |
|--------|------|-----------|
| MySQL (single node) | CA | Not distributed; no partition concerns |
| MySQL InnoDB Cluster | CP | On partition: refuses writes to preserve consistency |
| MongoDB (default) | CP | Primary stepdown during partition; secondaries not writable |
| MongoDB (eventually consistent reads) | AP | Reads from stale secondaries; data may lag |
| Cassandra | AP | Always accepts writes; eventual consistency |
| Redis Cluster | AP | Accepts reads/writes; partitioned nodes may diverge |
| Google Spanner | CP (effectively CA) | Uses TrueTime API + synchronised clocks to minimise partition effects |
| DynamoDB | AP (configurable) | Strong consistency available, but not default |
| CockroachDB | CP | Raft consensus; partitioned nodes halt writes |

### 1.3 Beyond CAP — the PACELC Model

The PACELC extension recognises that even *without* a partition, there is a latency/consistency trade-off:

```
PACELC: if Partition → (A vs C);
        Else         → (L vs C)
```

A system like DynamoDB: **PA/EL** — in partition favours availability; in normal operation favours low latency over consistency.

---

## 2. NoSQL Paradigms

### 2.1 The Four NoSQL Categories

| Category | Model | Examples | Best For |
|----------|-------|---------|---------|
| **Document** | JSON/BSON documents | MongoDB, CouchDB, Firestore | Flexible schemas, content management, user profiles |
| **Key-Value** | Opaque value behind a key | Redis, DynamoDB, Riak | Sessions, caching, shopping carts, real-time data |
| **Column-Family** | Rows with sparse columns | Cassandra, HBase, Bigtable | Write-heavy time series, IoT, event logs |
| **Graph** | Nodes and edges | Neo4j, Amazon Neptune, TigerGraph | Social networks, recommendations, fraud detection |

### 2.2 When NOT to Use NoSQL

!!! warning "NoSQL Is Not a Silver Bullet"
    NoSQL databases sacrifice ACID guarantees (or implement them differently). Do not use NoSQL when:
    
    - You need **multi-table transactions** (e.g., financial systems with consistent balances)
    - Your data is **highly relational** and you need complex joins
    - Your team's expertise is SQL and the project timeline is tight
    - **Regulatory compliance** requires auditable, consistent records (HIPAA, SOX, PCI-DSS)

---

## 3. MongoDB Deep Dive

### 3.1 Document Model vs Relational

In MongoDB, data is stored as **BSON** (Binary JSON) documents in **collections** (not tables). There is no enforced schema by default.

=== "Relational Model"

    ```sql title="University enrollment — relational"
    -- Three separate tables with foreign keys
    SELECT s.first_name, s.last_name,
           c.title, c.course_code, g.numeric_grade
    FROM   students    s
    JOIN   enrollments e ON e.student_id = s.student_id
    JOIN   sections    sc ON sc.section_id = e.section_id
    JOIN   courses     c  ON c.course_id   = sc.course_id
    LEFT JOIN grades   g  ON g.enrollment_id = e.enrollment_id
    WHERE  s.student_id = 1001;
    ```

=== "MongoDB Document Model"

    ```javascript title="MongoDB — embedded document model"
    // Students collection — one document per student
    // Enrollments embedded within the student document
    db.students.insertOne({
      _id: ObjectId("64a1b2c3d4e5f6789abcdef0"),
      student_id: 1001,
      first_name: "Maria",
      last_name:  "Hernandez",
      email:      "mhernandez@frostburg.edu",
      gpa:        3.72,
      enrollments: [
        {
          section_id:   201,
          course_code:  "ITEC445",
          title:        "Database Systems II",
          semester:     "Fall2025",
          grade:        { numeric: 94.5, letter: "A" }
        },
        {
          section_id:   187,
          course_code:  "ITEC412",
          title:        "Cloud Computing",
          semester:     "Fall2025",
          grade:        null     // not yet graded
        }
      ]
    });
    ```

### 3.2 MongoDB CRUD Operations

```javascript title="MongoDB CRUD"
// ---- INSERT ------------------------------------------------
db.students.insertOne({
  student_id: 1002,
  first_name: "James",
  last_name:  "Okafor",
  email:      "jokafor@frostburg.edu",
  gpa:        3.15
});

db.students.insertMany([
  { student_id: 1003, first_name: "Priya", last_name: "Nair",   gpa: 3.90 },
  { student_id: 1004, first_name: "David", last_name: "Kim",    gpa: 2.85 }
]);

// ---- READ --------------------------------------------------
// Find all students with GPA >= 3.5
db.students.find(
  { gpa: { $gte: 3.5 } },
  { first_name: 1, last_name: 1, gpa: 1, _id: 0 }   // projection
).sort({ gpa: -1 });

// Find with nested field filter
db.students.find({
  "enrollments.semester": "Fall2025",
  "enrollments.course_code": "ITEC445"
});

// ---- UPDATE ------------------------------------------------
// Update GPA for one student
db.students.updateOne(
  { student_id: 1001 },
  { $set: { gpa: 3.75, last_updated: new Date() } }
);

// Set a grade in an embedded array element (arrayFilters)
db.students.updateOne(
  { student_id: 1001 },
  { $set: { "enrollments.$[elem].grade": { numeric: 96.0, letter: "A" } } },
  { arrayFilters: [ { "elem.section_id": 201 } ] }
);

// ---- DELETE ------------------------------------------------
db.students.deleteOne({ student_id: 1004 });

// Delete all students with GPA below 1.0 (academic suspension)
db.students.deleteMany({ gpa: { $lt: 1.0 } });
```

### 3.3 Aggregation Pipeline

The MongoDB aggregation pipeline processes documents through a series of stages:

```javascript title="Aggregation pipeline — department GPA summary"
db.students.aggregate([
  // Stage 1: Filter active students
  { $match: { status: "active" } },

  // Stage 2: Unwind enrollments array
  { $unwind: "$enrollments" },

  // Stage 3: Filter for Fall2025
  { $match: { "enrollments.semester": "Fall2025" } },

  // Stage 4: Extract department from course code
  { $addFields: {
      dept_code: { $substr: ["$enrollments.course_code", 0, 4] }
  }},

  // Stage 5: Group by department
  { $group: {
      _id:            "$dept_code",
      avg_gpa:        { $avg: "$gpa" },
      total_students: { $addToSet: "$student_id" },
      enrollment_count: { $sum: 1 }
  }},

  // Stage 6: Add computed field
  { $addFields: {
      unique_students: { $size: "$total_students" }
  }},

  // Stage 7: Sort
  { $sort: { avg_gpa: -1 } },

  // Stage 8: Project final shape
  { $project: {
      _id:              0,
      department:       "$_id",
      avg_gpa:          { $round: ["$avg_gpa", 2] },
      unique_students:  1,
      enrollment_count: 1
  }}
]);
```

### 3.4 Schema Design — Embedding vs Referencing

| Criteria | Embedding | Referencing |
|---------|-----------|-------------|
| Relationship cardinality | One-to-few | One-to-many or many-to-many |
| Access pattern | Child data always accessed with parent | Child data queried independently |
| Update frequency | Child rarely updated | Child updated frequently |
| Document size risk | Low | N/A — data in separate collection |
| Join required? | ❌ No ($lookup equivalent available) | ✅ `$lookup` pipeline stage |
| Duplication | Possible | Normalised |

```javascript title="MongoDB $lookup (join equivalent)"
// Get students with their course details (referenced pattern)
db.enrollments.aggregate([
  { $lookup: {
      from:         "courses",
      localField:   "course_id",
      foreignField: "_id",
      as:           "course_info"
  }},
  { $unwind: "$course_info" },
  { $project: {
      student_id: 1,
      course_code: "$course_info.course_code",
      title:       "$course_info.title"
  }}
]);
```

---

## 4. Redis — Data Structures and Use Cases

### 4.1 Core Data Structures

```bash title="Redis CLI — core data structure operations"
# ---- STRING (most basic) -----------------------------------
SET   session:user:1001 '{"userId":1001,"role":"student","exp":1728000000}'
GET   session:user:1001
TTL   session:user:1001          # Remaining TTL in seconds
EXPIRE session:user:1001 3600    # Set TTL of 1 hour
DEL   session:user:1001

# ---- LIST (ordered, allows duplicates) ---------------------
RPUSH notification_queue '{"type":"email","to":"mhernandez@frostburg.edu"}'
RPUSH notification_queue '{"type":"sms","to":"+13015551234"}'
LLEN  notification_queue         # 2
BLPOP notification_queue 30      # Blocking pop (30s timeout) — worker pattern

# ---- SET (unique members, unordered) -----------------------
SADD  enrolled_sections:1001 201 187 203
SISMEMBER enrolled_sections:1001 201  # 1 (true)
SMEMBERS enrolled_sections:1001       # {201, 187, 203}
SCARD enrolled_sections:1001          # 3

# ---- SORTED SET (unique members with score) ----------------
ZADD  course_leaderboard 96.5 "student:1001"
ZADD  course_leaderboard 91.0 "student:1003"
ZADD  course_leaderboard 88.5 "student:1002"
ZREVRANGE course_leaderboard 0 9 WITHSCORES   # Top 10 with scores
ZRANK     course_leaderboard "student:1001"   # Rank (0-indexed)

# ---- HASH (field-value map for an object) ------------------
HSET    student:1001 first_name "Maria" last_name "Hernandez" gpa 3.72
HGET    student:1001 gpa                    # "3.72"
HGETALL student:1001                        # All fields
HINCRBY student:1001 login_count 1          # Atomic increment
```

### 4.2 Real-World Use Cases

=== "Session Store"

    ```python title="Redis session management"
    import redis
    import json
    import uuid
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    SESSION_TTL = 3600  # 1 hour
    
    def create_session(user_id: int, role: str) -> str:
        token = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "role":    role,
            "created": "2025-10-15T09:00:00"
        }
        r.setex(
            f"session:{token}",
            SESSION_TTL,
            json.dumps(session_data)
        )
        return token
    
    def get_session(token: str) -> dict | None:
        data = r.get(f"session:{token}")
        if data:
            r.expire(f"session:{token}", SESSION_TTL)  # Sliding expiry
            return json.loads(data)
        return None
    ```

=== "Rate Limiting"

    ```python title="Redis sliding window rate limiter"
    import redis, time
    
    r = redis.Redis(host='localhost', port=6379)
    
    def is_rate_limited(user_id: int, limit: int = 100, window_secs: int = 60) -> bool:
        """Allow at most `limit` requests per `window_secs`."""
        key = f"ratelimit:{user_id}"
        now = time.time()
        window_start = now - window_secs
    
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)   # Remove old entries
        pipe.zadd(key, {str(now): now})               # Add this request
        pipe.zcard(key)                               # Count in window
        pipe.expire(key, window_secs + 1)             # Auto-cleanup
        results = pipe.execute()
    
        request_count = results[2]
        return request_count > limit
    ```

=== "Pub/Sub Messaging"

    ```python title="Redis pub/sub — real-time notifications"
    import redis, threading, json
    
    r = redis.Redis(host='localhost', decode_responses=True)
    
    def publish_enrollment_event(student_id: int, section_id: int):
        """Publish event for all interested subscribers."""
        message = json.dumps({
            "event":     "enrollment_confirmed",
            "student_id": student_id,
            "section_id": section_id
        })
        r.publish("enrollment_events", message)
    
    def enrollment_listener():
        """Subscribe and process events."""
        pubsub = r.pubsub()
        pubsub.subscribe("enrollment_events")
        for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                print(f"Sending confirmation to student {data['student_id']}")
    ```

### 4.3 Redis Persistence Options

| Mode | How It Works | Durability | Performance |
|------|-------------|-----------|-------------|
| **RDB** (snapshot) | Periodic fork + dump to `.rdb` file | May lose data since last snapshot | Fastest reads; compact file |
| **AOF** (append-only file) | Log every write command | At most 1 second loss (fsync=everysec) | Slightly slower; larger file |
| **RDB + AOF** | Both enabled; AOF used for recovery | Best durability | Moderate overhead |
| **No persistence** | In-memory only | Complete loss on restart | Maximum performance |

### 4.4 Eviction Policies

```bash title="Redis memory management"
# Set max memory limit
CONFIG SET maxmemory 4gb

# Set eviction policy
CONFIG SET maxmemory-policy allkeys-lru
# Policies:
# noeviction     — return error when memory full (default)
# allkeys-lru    — evict LRU key from all keys
# allkeys-lfu    — evict least-frequently-used key
# volatile-lru   — evict LRU key from keys with TTL
# volatile-ttl   — evict key with shortest TTL
# allkeys-random — evict random key
```

---

## 5. NewSQL — Distributed SQL

NewSQL systems provide the scalability of NoSQL with the ACID guarantees and SQL interface of traditional relational databases.

### 5.1 NewSQL Architecture

```
Traditional SQL:         NewSQL:
┌───────────┐            ┌─────┐ ┌─────┐ ┌─────┐
│  MySQL    │            │Node1│ │Node2│ │Node3│
│ (single   │            └──┬──┘ └──┬──┘ └──┬──┘
│  server)  │               └───────┴───────┘
└───────────┘             Distributed Raft Consensus
                          Horizontal sharding
                          SQL interface preserved
                          ACID via consensus protocol
```

### 5.2 NewSQL System Comparison

| System | Origin | Consistency | SQL Compatibility | Sharding |
|--------|--------|-------------|------------------|---------|
| **Google Spanner** | Google (2012) | External consistency (stronger than serialisable) | ANSI SQL + extensions | Automatic (F1 driver) |
| **CockroachDB** | Cockroach Labs | Serialisable | PostgreSQL-compatible | Automatic (range-based) |
| **TiDB** | PingCAP | Snapshot isolation | MySQL-compatible | Automatic (region-based) |

```sql title="CockroachDB — SQL looks like PostgreSQL"
-- CockroachDB syntax is nearly identical to PostgreSQL
CREATE TABLE students (
    student_id  INT          DEFAULT unique_rowid() PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    gpa         DECIMAL(3,2) DEFAULT 0.00
);

-- Distribute table data across zones
ALTER TABLE enrollments
PARTITION BY LIST (semester) (
  PARTITION fall2025 VALUES IN ('Fall2025'),
  PARTITION spring2026 VALUES IN ('Spring2026')
);
```

---

## 6. MySQL as a Document Store

### 6.1 JSON Data Type in MySQL 8.0

MySQL's native JSON type validates, stores, and indexes JSON without requiring a separate NoSQL system:

```sql title="MySQL JSON data type"
-- Table with JSON column
CREATE TABLE student_profiles (
    student_id   INT          PRIMARY KEY,
    profile_json JSON         NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Insert JSON document
INSERT INTO student_profiles (student_id, profile_json)
VALUES (1001, '{
  "major":       "Computer Science",
  "minor":       "Mathematics",
  "advisor_id":  42,
  "preferences": { "notifications": true, "theme": "dark" },
  "tags":        ["honors", "research_track"]
}');

-- JSON_EXTRACT: retrieve nested value
SELECT
    student_id,
    JSON_EXTRACT(profile_json, '$.major')                  AS major,
    JSON_UNQUOTE(JSON_EXTRACT(profile_json, '$.preferences.theme')) AS theme,
    JSON_EXTRACT(profile_json, '$.tags[0]')                AS first_tag
FROM student_profiles
WHERE student_id = 1001;

-- Shorthand arrow operator (->) — equivalent to JSON_EXTRACT
SELECT
    student_id,
    profile_json -> '$.major'            AS major,
    profile_json ->> '$.preferences.theme' AS theme   -- ->> unquotes
FROM student_profiles;
```

### 6.2 JSON_TABLE — Shredding JSON into Relational Rows

```sql title="JSON_TABLE converts JSON arrays to rows"
SELECT jt.*
FROM   student_profiles sp,
       JSON_TABLE(
           sp.profile_json,
           '$.tags[*]'
           COLUMNS (
               tag VARCHAR(50) PATH '$'
           )
       ) AS jt
WHERE  sp.student_id = 1001;
-- Returns:
-- tag
-- --------
-- honors
-- research_track
```

### 6.3 Generated Columns and Functional Indexes on JSON

```sql title="Virtual generated column + index on JSON path"
-- Add a virtual column extracting major from JSON
ALTER TABLE student_profiles
ADD COLUMN major VARCHAR(100)
    GENERATED ALWAYS AS (JSON_UNQUOTE(profile_json ->> '$.major'))
    VIRTUAL;

-- Index the generated column for fast lookups
CREATE INDEX idx_major ON student_profiles (major);

-- Now this query uses the index:
EXPLAIN SELECT student_id, major
FROM    student_profiles
WHERE   major = 'Computer Science';
```

---

## 7. Cloud Database Services Comparison

### 7.1 AWS Cloud Databases

=== "Amazon RDS"

    **Managed relational DB (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server)**
    
    - Automated backups, patches, minor version upgrades
    - Multi-AZ for HA; read replicas for scale-out
    - Pricing: instance hours + storage + I/O + data transfer
    - Best for: lift-and-shift of existing relational workloads
    
    ```bash title="RDS read replica creation"
    aws rds create-db-instance-read-replica \
      --db-instance-identifier university-replica-1 \
      --source-db-instance-identifier university-prod \
      --db-instance-class db.r6g.large \
      --availability-zone us-east-1b
    ```

=== "Amazon Aurora"

    **MySQL/PostgreSQL-compatible with proprietary distributed storage**
    
    - Storage auto-scales to 128 TB; 6-way replication across 3 AZs at storage layer
    - Up to 15 read replicas with < 10ms replica lag
    - **Aurora Serverless v2**: auto-scales capacity in ACU (Aurora Capacity Units)
    - 2–3× performance vs RDS MySQL on same hardware
    - Best for: high-throughput MySQL workloads, variable traffic
    
    | Feature | RDS MySQL | Aurora MySQL |
    |---------|-----------|-------------|
    | Max storage | 64 TB | 128 TB |
    | Failover time | 60–120s | < 30s |
    | Read replicas | 5 | 15 |
    | Replica lag | Seconds | < 100ms |
    | Cost | Lower | ~20% more |

=== "Amazon DynamoDB"

    **Fully managed serverless key-value and document DB**
    
    - Single-digit millisecond latency at any scale
    - No capacity planning: On-Demand mode scales automatically
    - Global Tables: multi-region active-active replication
    - Pricing: read/write capacity units or on-demand per request
    - Best for: session stores, shopping carts, gaming leaderboards, IoT
    
    ```python title="DynamoDB boto3 example"
    import boto3
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table    = dynamodb.Table('UserSessions')
    
    # Put item
    table.put_item(Item={
        'session_id': 'abc-123',
        'user_id':    1001,
        'ttl':        1728000000   # DynamoDB TTL auto-deletion
    })
    
    # Get item
    response = table.get_item(Key={'session_id': 'abc-123'})
    session  = response.get('Item')
    ```

### 7.2 Multi-Cloud Comparison

| Service | Provider | Engine | HA | Serverless | Best For |
|---------|---------|--------|-----|-----------|---------|
| Cloud SQL | GCP | MySQL 8.0, PG 16 | Regional failover | ❌ | Standard relational workloads on GCP |
| Cloud Spanner | GCP | Spanner (NewSQL) | Multi-region | ✅ (autoscale) | Global, strongly-consistent transactional |
| Firestore | GCP | Document (NoSQL) | Multi-region | ✅ | Mobile/web apps, hierarchical data |
| Azure Database for MySQL | Azure | MySQL 8.0 | Zone-redundant | ❌ | MySQL workloads in Azure ecosystem |
| Azure CosmosDB | Azure | Multi-model | Multi-region | ✅ | Globally distributed, multiple APIs |
| Azure SQL | Azure | SQL Server | Zone-redundant | ✅ (Serverless) | SQL Server workloads, Azure ecosystem |

---

## 8. Database Selection Framework

### 8.1 Selection Criteria

When selecting a database for a new system, evaluate these dimensions:

```
┌─────────────────────────────────────────────────────┐
│               DATABASE SELECTION FRAMEWORK          │
│                                                     │
│  1. DATA MODEL                                      │
│     • Relational / Tabular → SQL (MySQL, PostgreSQL)│
│     • Documents / Flexible → MongoDB, Firestore     │
│     • Key-Value / Cache    → Redis, DynamoDB        │
│     • Time Series          → TimescaleDB, InfluxDB  │
│     • Graph                → Neo4j, Neptune         │
│                                                     │
│  2. CONSISTENCY REQUIREMENTS                        │
│     • Strict ACID (financial, medical) → SQL        │
│     • Eventual OK (social, analytics) → AP NoSQL    │
│                                                     │
│  3. SCALE PROFILE                                   │
│     • < 1 TB, moderate load  → Single MySQL server  │
│     • Read scale-out needed  → Replication + proxy  │
│     • Write scale-out needed → NewSQL / NoSQL shard │
│                                                     │
│  4. QUERY COMPLEXITY                                │
│     • Complex joins, reporting → SQL                │
│     • Simple key lookups       → Redis / DynamoDB   │
│     • Aggregation pipelines    → MongoDB            │
│                                                     │
│  5. OPERATIONAL OVERHEAD                            │
│     • Small team / startup → Managed cloud service  │
│     • Large team / on-prem → Self-hosted            │
└─────────────────────────────────────────────────────┘
```

### 8.2 Polyglot Persistence in Practice

**Polyglot persistence** means using multiple database systems within one application, each chosen for the type of data it manages best.

```
University Application — Polyglot Persistence Architecture:

┌─────────────────────────────────────────────────────────┐
│                    Application Services                 │
│                                                         │
│  Enrollment Service ──── MySQL 8.0 ──── Transactional   │
│  (registration, grades, transcripts)    ACID required   │
│                                                         │
│  Session Service ──────── Redis ──────── Fast K/V       │
│  (auth tokens, user state)               < 1ms access   │
│                                                         │
│  Search Service ────── Elasticsearch ── Full-text       │
│  (course catalog search)                 Inverted index  │
│                                                         │
│  Analytics Service ──── ClickHouse ───── OLAP           │
│  (enrollment trends, reporting)          Columnar store  │
│                                                         │
│  Profile Service ──────── MongoDB ────── Flexible docs  │
│  (student preferences, social data)      Schema-free     │
└─────────────────────────────────────────────────────────┘
```

!!! tip "Polyglot Persistence Trade-offs"
    Using multiple databases provides performance and flexibility benefits, but adds operational complexity: more systems to monitor, back up, upgrade, and staff expertise in. Apply polyglot persistence only when the benefit of a specialised database demonstrably outweighs the cost of managing it.

### 8.3 Relational to Document Migration Considerations

```python title="ETL: Relational to MongoDB (denormalisation)"
"""
Migrate university enrollments from MySQL to MongoDB.
Demonstrates denormalisation for document model.
"""
import mysql.connector
from pymongo import MongoClient
import json

# Source: MySQL
mysql_conn = mysql.connector.connect(
    host="localhost", database="university",
    user="etl_user", password="etl_pass"
)
cursor = mysql_conn.cursor(dictionary=True)

# Destination: MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db     = mongo_client["university_nosql"]
students_col = mongo_db["students"]

# Fetch students with all enrollments in one query
cursor.execute("""
    SELECT
        s.student_id, s.first_name, s.last_name, s.email, s.gpa,
        c.course_code, c.title AS course_title,
        sec.section_num, sec.semester,
        g.numeric_grade, g.letter_grade
    FROM students s
    LEFT JOIN enrollments e  ON e.student_id   = s.student_id
    LEFT JOIN sections    sec ON sec.section_id = e.section_id
    LEFT JOIN courses     c   ON c.course_id   = sec.course_id
    LEFT JOIN grades      g   ON g.enrollment_id = e.enrollment_id
    ORDER BY s.student_id
""")

students = {}
for row in cursor.fetchall():
    sid = row["student_id"]
    if sid not in students:
        students[sid] = {
            "student_id": sid,
            "first_name": row["first_name"],
            "last_name":  row["last_name"],
            "email":      row["email"],
            "gpa":        float(row["gpa"]) if row["gpa"] else None,
            "enrollments": []
        }
    if row["course_code"]:
        students[sid]["enrollments"].append({
            "course_code":   row["course_code"],
            "title":         row["course_title"],
            "section_num":   row["section_num"],
            "semester":      row["semester"],
            "numeric_grade": float(row["numeric_grade"]) if row["numeric_grade"] else None,
            "letter_grade":  row["letter_grade"]
        })

# Insert into MongoDB
docs = list(students.values())
if docs:
    result = students_col.insert_many(docs)
    print(f"Migrated {len(result.inserted_ids)} students to MongoDB")

cursor.close()
mysql_conn.close()
mongo_client.close()
```

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **CAP Theorem** | Distributed systems cannot guarantee Consistency, Availability, and Partition Tolerance simultaneously |
| **CP system** | Chooses Consistency over Availability during a network partition |
| **AP system** | Chooses Availability over Consistency during a network partition |
| **NoSQL** | Broad category of non-relational databases: document, key-value, column-family, graph |
| **Document database** | Stores semi-structured JSON/BSON documents; flexible schema; example: MongoDB |
| **Key-value store** | Maps opaque keys to values; ultra-fast lookups; example: Redis |
| **Column-family** | Organises data as columns that can be grouped; great for sparse, wide data; example: Cassandra |
| **Graph database** | Stores entities as nodes and relationships as edges; example: Neo4j |
| **BSON** | Binary JSON — MongoDB's wire and storage format; supports more types than JSON |
| **Aggregation pipeline** | MongoDB's data transformation framework; chain of processing stages |
| **Embedding** | MongoDB pattern: store related data inside a single document |
| **Referencing** | MongoDB pattern: store related data in a separate collection with a foreign key |
| **NewSQL** | Database category providing SQL ACID guarantees with horizontal NoSQL scalability |
| **GTID (Spanner)** | Google TrueTime — globally ordered timestamps using GPS/atomic clocks |
| **Raft consensus** | Distributed consensus algorithm used by CockroachDB, TiDB, etcd for leader election |
| **JSON_EXTRACT** | MySQL function to retrieve a value at a JSON path expression |
| **Generated column** | MySQL column whose value is computed from an expression; can be indexed |
| **TTL** | Time To Live — automatic expiry setting for cache entries |
| **Eviction policy** | Redis rule determining which key is removed when memory is full |
| **Polyglot persistence** | Architecture using multiple specialised databases within one application |

---

## Self-Assessment

!!! question "Self-Assessment — Week 14"

    **Question 1.** A social media startup says: "We chose Cassandra because it's always available and never rejects writes." A financial services company says: "We use MySQL because data must always be consistent." Explain, using the CAP theorem and PACELC model, why each choice makes sense for its domain. Then describe a scenario where Cassandra's choice would be unacceptable.

    **Question 2.** You are designing a MongoDB schema for a university system. A professor's record includes basic profile data (name, email, department) and a list of courses they have taught over 15 years (potentially 50+ courses). Explain whether you would use embedding or referencing for the courses list, citing at least three specific technical reasons.

    **Question 3.** Your team's Node.js application uses Redis as a session store with a 1-hour sliding TTL. A QA engineer reports that after 55 minutes of inactivity, a user's session is sometimes preserved and sometimes expired. Explain what is happening (at the Redis data structure level) and how the sliding TTL implementation should be corrected.

    **Question 4.** Compare CockroachDB and traditional MySQL replication for a multinational university with campuses in the US, Europe, and Asia. Each campus needs low-latency reads and writes for its own students, and enrollment must be globally consistent (a seat taken in New York cannot be double-booked in London). Which system architecture serves this use case better, and why?

    **Question 5.** MySQL 8.0's JSON type with generated columns and functional indexes can replace some use cases that would otherwise require MongoDB. Describe a scenario where MySQL JSON is the right choice and a scenario where MongoDB's document model is genuinely superior — justify both answers technically.

---

## Further Reading

- [MongoDB Manual — Aggregation Pipeline](https://www.mongodb.com/docs/manual/core/aggregation-pipeline/)
- [Redis Documentation — Data Types](https://redis.io/docs/data-types/)
- [CockroachDB Architecture](https://www.cockroachlabs.com/docs/stable/architecture/overview.html)
- [Google Spanner — Original Paper](https://research.google/pubs/pub39966/)
- [MySQL 8.0 — JSON Functions](https://dev.mysql.com/doc/refman/8.0/en/json-functions.html)
- [AWS Database Selection Guide](https://aws.amazon.com/products/databases/)
- [Martin Kleppmann — Designing Data-Intensive Applications](https://dataintensive.net/) — Chapters 5–9
- [CAP Theorem — Gilbert & Lynch (2002)](https://dl.acm.org/doi/10.1145/564585.564601)

---

[← Week 13](week13.md) | [Course Index](index.md) | [Week 15 →](week15.md)
