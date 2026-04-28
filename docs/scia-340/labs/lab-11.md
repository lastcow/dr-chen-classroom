---
title: "Lab 11: Cloud Database Security — Neon Branching & Connection Hardening"
course: SCIA-340
topic: Cloud Database Security
week: 11
difficulty: "⭐⭐ Intermediate"
estimated_time: 60 min
---

# Lab 11: Cloud Database Security — Neon Branching & Connection Hardening

**Course:** SCIA-340 · Secure Databases · Frostburg State University
**Week:** 11 &nbsp;|&nbsp; **Difficulty:** ⭐⭐ Intermediate &nbsp;|&nbsp; **Time:** 60 min

---

## Overview

Neon's branching feature mirrors Git branching for databases. Each branch gets its own dedicated compute endpoint with a fully isolated connection string — meaning your `lab-11` branch is completely separate from `main` at the network level, not just at the schema level. In this lab you will:

- Inspect your current Neon branch via SQL metadata
- Document branch configuration in a registry table
- Verify and reason about Neon's always-on SSL/TLS enforcement
- Audit active sessions and connection limits
- Map the cloud shared-responsibility model into a SQL table
- Audit all login roles for over-privilege using `pg_roles`

---

!!! info "Neon Connection"
    Connect to your **lab-11** branch endpoint. Your connection string looks like:

    ```
    postgresql://user:password@ep-xxxx-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
    ```

    Open a `psql` session or use the Neon SQL Editor before starting.

    ```bash
    psql "$NEON_LAB11_CONNECTION_STRING"
    ```

!!! warning "Work on branch `lab-11`"
    All work in this lab **must** be done on the `lab-11` branch, not `main`.
    Create the branch in the Neon console (**Branches → New Branch**) before running any SQL.
    Dr. Chen will connect to this branch to verify your work.

---

## Part 1 — Neon Branch Architecture

### Step 1.1 — Understand Branches via SQL Metadata

Every Neon branch has its own compute endpoint. When you connect, PostgreSQL metadata reflects the current branch's compute node. Run the following to capture your branch's identity:

```sql
-- Each Neon branch has its own endpoint (visible as app_name)
SELECT
  current_database()           AS database,
  current_user                 AS connected_as,
  inet_server_addr()           AS server_ip,
  inet_server_port()           AS port,
  pg_postmaster_start_time()   AS server_started;
```

> **What to observe:** The `server_ip` and `server_started` values will differ between branches even in the same Neon project, confirming compute-level isolation.

📸 **Screenshot checkpoint — Step 1.1:** Capture the full result showing `database`, `connected_as`, `server_ip`, `port`, and `server_started`.

---

### Step 1.2 — Track Branch Configuration

Create a registry table that documents each branch's security posture and purpose:

```sql
CREATE TABLE IF NOT EXISTS public.branch_registry (
  branch_name   TEXT PRIMARY KEY,
  purpose       TEXT NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  ssl_enforced  BOOLEAN DEFAULT TRUE,
  max_conns     INT DEFAULT 10,
  environment   TEXT NOT NULL
                  CHECK (environment IN ('prod','staging','dev','test'))
);

INSERT INTO branch_registry VALUES
  ('main',    'Production database',    NOW(), TRUE, 100, 'prod'),
  ('lab-11',  'Lab 11 branch',          NOW(), TRUE, 10,  'dev'),
  ('staging', 'Pre-production testing', NOW(), TRUE, 50,  'staging')
ON CONFLICT (branch_name) DO NOTHING;

SELECT * FROM branch_registry ORDER BY environment;
```

> **Note:** `ssl_enforced = TRUE` for every row reflects Neon's architecture — TLS is non-negotiable on all branch endpoints.

📸 **Screenshot checkpoint — Step 1.2:** Capture the result showing all three branch rows ordered by environment.

---

## Part 2 — SSL and Connection Security

### Step 2.1 — Verify Neon SSL (Always On)

Neon mandates TLS on every connection. Use `pg_stat_ssl` to confirm the cipher and protocol version for your current session:

```sql
-- Neon always uses SSL; verify TLS version and cipher
SELECT
  ssl,
  version,
  cipher,
  bits,
  client_dn
FROM pg_stat_ssl
WHERE pid = pg_backend_pid();
```

> **Expected:** `ssl = true`, `version` showing TLS 1.3 or 1.2, a strong cipher suite (e.g., `TLS_AES_256_GCM_SHA384`), and `bits >= 128`.

📸 **Screenshot checkpoint — Step 2.1:** Capture the SSL verification row showing `ssl`, `version`, `cipher`, and `bits`.

---

### Step 2.2 — Connection Limit Enforcement

Check how many connections are currently open against the database's configured maximum:

```sql
-- Check current connection count vs limit
SELECT
  datname,
  numbackends AS current_connections,
  (SELECT setting::INT FROM pg_settings
   WHERE name = 'max_connections') AS max_connections
FROM pg_stat_database
WHERE datname = current_database();
```

> **Why this matters:** Neon's serverless compute imposes connection limits per branch. Exhausting connections is a denial-of-service vector; understanding this limit is part of secure capacity planning.

---

### Step 2.3 — Active Sessions Audit

Audit all active sessions on this branch (excluding your own) to detect unexpected connections:

```sql
SELECT
  pid,
  usename,
  application_name,
  client_addr,
  state,
  wait_event_type,
  query_start,
  LEFT(query, 80) AS current_query
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid != pg_backend_pid()
ORDER BY query_start DESC NULLS LAST;
```

> **In a real environment:** Any unexpected `client_addr` or `usename` here is a red flag that warrants immediate investigation.

📸 **Screenshot checkpoint — Step 2.3:** Capture the active sessions result (even if it returns 0 rows, that is expected for a lab branch).

---

## Part 3 — Neon-Specific Security Features

### Step 3.1 — Shared Responsibility Model Documentation

Cloud databases operate under a shared responsibility model. Create a controls table documenting who is responsible for each security layer:

```sql
CREATE TABLE IF NOT EXISTS public.cloud_security_controls (
  control_id   TEXT PRIMARY KEY,
  category     TEXT NOT NULL,
  responsible  TEXT NOT NULL
                 CHECK (responsible IN ('Neon','Customer','Shared')),
  description  TEXT NOT NULL,
  implemented  BOOLEAN DEFAULT FALSE
);

INSERT INTO cloud_security_controls VALUES
  ('NEON-01', 'Physical Security',     'Neon',     'Data center physical access control',                TRUE),
  ('NEON-02', 'Infrastructure',        'Neon',     'Hypervisor and OS patching',                         TRUE),
  ('NEON-03', 'Network',               'Neon',     'DDoS protection and network isolation',              TRUE),
  ('NEON-04', 'Encryption in transit', 'Neon',     'TLS enforcement on all connections',                 TRUE),
  ('CUST-01', 'Authentication',        'Customer', 'Role passwords and connection limits',               FALSE),
  ('CUST-02', 'Access Control',        'Customer', 'GRANT/REVOKE, RLS, schema privileges',              FALSE),
  ('CUST-03', 'Encryption at rest',    'Customer', 'Column-level encryption with pgcrypto',             FALSE),
  ('CUST-04', 'Auditing',              'Customer', 'Audit triggers and log monitoring',                  FALSE),
  ('CUST-05', 'Branch isolation',      'Customer', 'Use separate branches per environment',              FALSE),
  ('SHR-01',  'Monitoring',            'Shared',   'Neon provides metrics; customer monitors app queries', FALSE)
ON CONFLICT (control_id) DO NOTHING;

SELECT
  responsible,
  COUNT(*)                                           AS control_count,
  SUM(CASE WHEN implemented THEN 1 ELSE 0 END)       AS implemented
FROM cloud_security_controls
GROUP BY responsible
ORDER BY responsible;
```

📸 **Screenshot checkpoint — Step 3.1:** Capture the grouped result showing Neon vs. Customer vs. Shared control counts and implementation status.

---

### Step 3.2 — Mark Customer Controls as Implemented

Based on the controls you implemented in Labs 4–10, update the registry to reflect completed work:

```sql
UPDATE public.cloud_security_controls
SET implemented = TRUE
WHERE responsible = 'Customer'
  AND control_id IN ('CUST-01','CUST-02','CUST-03','CUST-04');

-- Verify implementation status
SELECT
  control_id,
  category,
  responsible,
  implemented
FROM public.cloud_security_controls
ORDER BY responsible, control_id;
```

📸 **Screenshot checkpoint — Step 3.2:** Capture the full controls list showing updated `implemented` values for CUST-01 through CUST-04.

---

## Part 4 — Principle of Least Privilege for Neon Roles

### Step 4.1 — Audit All Login Roles for Over-Privilege

Query `pg_roles` to surface any login roles with dangerous privilege flags. Every flag marked DANGER or RISK requires justification:

```sql
SELECT
  rolname,
  CASE WHEN rolsuper
       THEN 'DANGER: superuser'      ELSE 'ok' END AS superuser_check,
  CASE WHEN rolcreaterole
       THEN 'RISK: can create roles' ELSE 'ok' END AS createrole_check,
  CASE WHEN rolcreatedb
       THEN 'RISK: can create dbs'   ELSE 'ok' END AS createdb_check,
  rolconnlimit,
  rolvaliduntil
FROM pg_roles
WHERE rolcanlogin = TRUE
  AND rolname NOT LIKE 'pg_%'
ORDER BY rolname;
```

> **Best practice:** Application login roles should show `ok` for all three checks, have a positive `rolconnlimit`, and have a `rolvaliduntil` date set. In Neon, the project owner role will appear here — note its flags.

📸 **Screenshot checkpoint — Step 4.1:** Capture the full login role security audit table.

---

## Assessment

### Verification Script

Run this script and submit the output. Dr. Chen will also run it on your `lab-11` branch.

```sql
-- VERIFY LAB 11
SELECT
  -- Branch registry exists with entries
  (SELECT COUNT(*) FROM public.branch_registry)::INT
    AS branch_entries,

  -- Shared responsibility table filled
  (SELECT COUNT(*) FROM public.cloud_security_controls)::INT
    AS control_count,

  -- Customer controls marked implemented
  (SELECT COUNT(*) FROM public.cloud_security_controls
   WHERE responsible = 'Customer' AND implemented = TRUE)::INT
    AS customer_controls_implemented,

  -- SSL is active (Neon always on)
  (SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid())
    AS ssl_active;
```

**Expected results:**

| branch_entries | control_count | customer_controls_implemented | ssl_active |
|----------------|---------------|-------------------------------|------------|
| ≥ 3 | 10 | ≥ 4 | `true` |

---

### Additional Requirement (20 pts)

Implement a **connection policy checker** for your database. Create the following function:

```sql
CREATE OR REPLACE FUNCTION public.check_connection_policy()
RETURNS TABLE(
  policy_name  TEXT,
  status       TEXT,
  detail       TEXT
) AS $$
BEGIN
  -- Check 1: password encryption method is scram-sha-256
  RETURN QUERY
  SELECT
    'Password Encryption'::TEXT,
    CASE WHEN setting = 'scram-sha-256' THEN 'PASS'
         WHEN setting = 'md5'           THEN 'FAIL'
         ELSE                                'WARN'
    END::TEXT,
    ('Current setting: ' || setting)::TEXT
  FROM pg_settings WHERE name = 'password_encryption';

  -- Check 2: current connection uses SSL
  RETURN QUERY
  SELECT
    'SSL Enforcement'::TEXT,
    CASE WHEN ssl THEN 'PASS' ELSE 'FAIL' END::TEXT,
    CASE WHEN ssl
         THEN ('TLS active — cipher: ' || cipher)
         ELSE 'Connection is NOT encrypted'
    END::TEXT
  FROM pg_stat_ssl WHERE pid = pg_backend_pid();

  -- Check 3: no login role (except postgres) is superuser
  RETURN QUERY
  SELECT
    'No Unexpected Superusers'::TEXT,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END::TEXT,
    CASE WHEN COUNT(*) = 0
         THEN 'No unexpected superuser login roles found'
         ELSE COUNT(*)::TEXT || ' superuser login role(s) found: '
              || STRING_AGG(rolname, ', ')
    END::TEXT
  FROM pg_roles
  WHERE rolcanlogin = TRUE
    AND rolsuper     = TRUE
    AND rolname NOT IN ('postgres')
    AND rolname NOT LIKE 'pg_%';

  -- Check 4: no login role has unlimited connections (rolconnlimit = -1)
  RETURN QUERY
  SELECT
    'Connection Limits Set'::TEXT,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARN' END::TEXT,
    CASE WHEN COUNT(*) = 0
         THEN 'All login roles have explicit connection limits'
         ELSE COUNT(*)::TEXT || ' role(s) with unlimited connections: '
              || STRING_AGG(rolname, ', ')
    END::TEXT
  FROM pg_roles
  WHERE rolcanlogin    = TRUE
    AND rolconnlimit   = -1
    AND rolname NOT LIKE 'pg_%';
END;
$$ LANGUAGE plpgsql;

-- Run the policy check
SELECT * FROM public.check_connection_policy();
```

Submit a screenshot of `SELECT * FROM public.check_connection_policy()` showing all four checks and their PASS/WARN/FAIL status with detail strings.

---

### Reflection Questions

!!! question "Reflection (answer in your lab submission)"
    1. **Branch vs. Schema isolation:** Neon's branching means each lab has its own isolated compute endpoint. How does this differ from just having separate schemas in one database? What security boundaries does a branch provide that a schema does *not*?

    2. **Shared responsibility and credential leakage:** The shared responsibility model shows that Neon handles physical security, network, and infrastructure — but the customer is responsible for authentication, access control, and encryption. A data breach occurs because a customer left their Neon project credentials in a public GitHub repository. Who is responsible: Neon or the customer? Justify your answer with reference to the `cloud_security_controls` table you built.

    3. **Scale-to-zero and session state:** Neon is serverless — compute scales to zero when inactive and spins back up on the next connection. What security implication does "scale to zero" have for audit logs and in-memory state (such as prepared statements or session variables set with `SET LOCAL`)? How does this affect security designs that rely on persistent session state?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Lab steps completed (Parts 1–4, all screenshots) | 50 |
    | Verification script — all expected values correct | 30 |
    | Additional requirement (`check_connection_policy`) | 20 |
    | **Total** | **100** |
