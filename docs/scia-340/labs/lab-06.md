---
title: "Lab 06: Row-Level Security — Multi-Tenant Data Isolation"
course: SCIA-340
topic: Access Control — Row Level Security
week: "5 (Part B)"
difficulty: ⭐⭐⭐
estimated_time: 75 min
---

# Lab 06: Row-Level Security — Multi-Tenant Data Isolation

!!! info "Neon Connection"
    Connect to your Neon Postgres instance for all work in this lab:
    ```bash
    psql $DATABASE_URL
    ```
    Branch naming convention: `lab-06-<your-username>` (e.g., `lab-06-jsmith`)

!!! warning "Branch Requirement"
    Work on branch **lab-06**. All SQL runs on your Neon Postgres instance.
    Create the branch in the Neon console before starting, then update `$DATABASE_URL` to point to it.

---

## Overview

Row-Level Security (RLS) enforces access control at the **row** level, not just the table level. Rather than permitting or denying access to an entire table, RLS allows fine-grained rules that determine which rows a given database role may see or modify.

This makes RLS the cornerstone of **multi-tenant SaaS architecture**: each customer (tenant) must only ever see their own data, even though all tenants share the same underlying table. A misconfigured application query cannot leak cross-tenant data — the database engine itself enforces the boundary.

By the end of this lab you will:

- Create a shared multi-tenant table and observe unrestricted access before RLS
- Enable and force RLS, then create per-tenant isolation policies
- Verify isolation using `SET ROLE` simulation
- Confirm that `WITH CHECK` blocks cross-tenant writes
- Understand the superuser bypass caveat
- (Additional) Replace role-per-tenant with a dynamic `current_tenant()` function

---

## Part 1 — Multi-Tenant Setup

### Step 1.1 — Create the tenant schema and shared table

```sql
CREATE SCHEMA IF NOT EXISTS saas;

CREATE TABLE saas.tenant_data (
  id          SERIAL PRIMARY KEY,
  tenant_id   TEXT NOT NULL,
  data_type   TEXT NOT NULL,
  content     TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO saas.tenant_data (tenant_id, data_type, content) VALUES
  ('acme',    'document', 'Acme Corp Q4 Strategy Plan'),
  ('acme',    'contact',  'CEO: John Smith, CEO@acme.com'),
  ('globex',  'document', 'Globex Nuclear Plant Blueprint'),
  ('globex',  'contact',  'CFO: Hank Scorpio, hank@globex.com'),
  ('initech', 'document', 'Initech TPS Report Template'),
  ('initech', 'contact',  'Director: Bill Lumbergh, bill@initech.com');
```

### Step 1.2 — Confirm all data is visible before RLS

```sql
-- Current count per tenant — all rows visible with no restrictions
SELECT tenant_id, COUNT(*) AS row_count
FROM saas.tenant_data
GROUP BY tenant_id
ORDER BY tenant_id;
```

**Expected:** Three rows — acme: 2, globex: 2, initech: 2.

📸 **Screenshot checkpoint** — capture this result showing all tenants' data visible before any RLS policy is applied.

---

## Part 2 — Enable Row Level Security

### Step 2.1 — Enable and force RLS on the table

```sql
-- ENABLE: activates RLS (table owner still bypasses by default)
ALTER TABLE saas.tenant_data ENABLE ROW LEVEL SECURITY;

-- FORCE: table owner is also subject to RLS — critical for SaaS!
ALTER TABLE saas.tenant_data FORCE ROW LEVEL SECURITY;
```

!!! note "What's the difference?"
    `ENABLE ROW LEVEL SECURITY` activates the feature but exempts the table owner.
    `FORCE ROW LEVEL SECURITY` removes that exemption — the owner sees only what the policies allow.
    For a shared SaaS database, always use **FORCE**.

### Step 2.2 — Create one database role per tenant

```sql
CREATE ROLE tenant_acme    LOGIN PASSWORD 'Acme_Secure#2026'    NOINHERIT;
CREATE ROLE tenant_globex  LOGIN PASSWORD 'Globex_Secure#2026'  NOINHERIT;
CREATE ROLE tenant_initech LOGIN PASSWORD 'Initech_Secure#2026' NOINHERIT;

-- Schema usage
GRANT USAGE ON SCHEMA saas
  TO tenant_acme, tenant_globex, tenant_initech;

-- DML access to the shared table
GRANT SELECT, INSERT, UPDATE, DELETE ON saas.tenant_data
  TO tenant_acme, tenant_globex, tenant_initech;

-- Sequence access for SERIAL inserts
GRANT USAGE ON SEQUENCE saas.tenant_data_id_seq
  TO tenant_acme, tenant_globex, tenant_initech;
```

### Step 2.3 — Create per-tenant isolation policies

```sql
-- acme: can only read/write rows where tenant_id = 'acme'
CREATE POLICY acme_isolation ON saas.tenant_data
  FOR ALL TO tenant_acme
  USING     (tenant_id = 'acme')
  WITH CHECK (tenant_id = 'acme');

-- globex: can only read/write rows where tenant_id = 'globex'
CREATE POLICY globex_isolation ON saas.tenant_data
  FOR ALL TO tenant_globex
  USING     (tenant_id = 'globex')
  WITH CHECK (tenant_id = 'globex');

-- initech: can only read/write rows where tenant_id = 'initech'
CREATE POLICY initech_isolation ON saas.tenant_data
  FOR ALL TO tenant_initech
  USING     (tenant_id = 'initech')
  WITH CHECK (tenant_id = 'initech');
```

!!! note "USING vs WITH CHECK"
    - **`USING`** controls which rows are **visible** (SELECT, UPDATE, DELETE filter)
    - **`WITH CHECK`** controls which rows can be **written** (INSERT, UPDATE validation)
    Both clauses together provide complete read + write isolation.

---

## Part 3 — Verify Isolation

### Step 3.1 — Inspect the defined policies

```sql
SELECT
  policyname,
  tablename,
  roles,
  cmd,
  qual        AS using_expr
FROM pg_policies
WHERE tablename = 'tenant_data'
ORDER BY policyname;
```

📸 **Screenshot checkpoint** — capture the three policy rows from `pg_policies`.

### Step 3.2 — Test isolation using `SET ROLE`

`SET ROLE` temporarily adopts another role's identity within the same session, letting us simulate a tenant login without opening a new connection.

```sql
-- Simulate an acme tenant session
SET ROLE tenant_acme;
SELECT tenant_id, data_type, content FROM saas.tenant_data;
RESET ROLE;
```

**Expected:** Exactly **2 rows** — both with `tenant_id = 'acme'`. Globex and Initech rows are invisible.

📸 **Screenshot checkpoint** — acme session sees only acme data.

```sql
-- Simulate a globex tenant session
SET ROLE tenant_globex;
SELECT tenant_id, data_type, content FROM saas.tenant_data;
RESET ROLE;
```

**Expected:** Exactly **2 rows** — both with `tenant_id = 'globex'`.

📸 **Screenshot checkpoint** — globex session sees only globex data.

### Step 3.3 — Verify `WITH CHECK` blocks cross-tenant writes

```sql
SET ROLE tenant_acme;

-- Attempt to forge a globex row — should be rejected
INSERT INTO saas.tenant_data (tenant_id, data_type, content)
VALUES ('globex', 'forged', 'Acme forged this!');

RESET ROLE;
```

**Expected:**
```
ERROR:  new row violates row-level security policy for table "tenant_data"
```

📸 **Screenshot checkpoint** — cross-tenant insert blocked by `WITH CHECK`.

### Step 3.4 — Inspect RLS metadata in `pg_tables`

```sql
SELECT tablename, rowsecurity, forcerowsecurity
FROM pg_tables
WHERE schemaname = 'saas';
```

**Expected:** `rowsecurity = true`, `forcerowsecurity = true`.

📸 **Screenshot checkpoint** — confirm both flags are active.

---

## Part 4 — Superuser Bypass (Important Caveat)

### Step 4.1 — Superuser sees all rows regardless of RLS

```sql
-- Run this as your superuser / Neon admin account
-- RLS is automatically bypassed for superusers
SELECT tenant_id, content
FROM saas.tenant_data
ORDER BY id;
```

**Expected:** All 6 rows visible — all three tenants.

!!! danger "Critical Security Rule"
    PostgreSQL superusers bypass RLS **by design** — they always see everything.
    This is why **application code must never connect as a superuser**.
    Create a dedicated application role with the minimum privileges needed, and let RLS enforce tenant boundaries.

---

## Assessment

### Verification SQL

Dr. Chen will run the following query against your Neon connection string. Ensure all expected values are returned before submitting.

```sql
-- VERIFY LAB 06
SELECT
  -- RLS enabled and forced
  (SELECT rowsecurity
     FROM pg_tables
    WHERE schemaname = 'saas' AND tablename = 'tenant_data')            AS rls_enabled,

  (SELECT forcerowsecurity
     FROM pg_tables
    WHERE schemaname = 'saas' AND tablename = 'tenant_data')            AS rls_forced,

  -- Exactly 3 policies exist
  (SELECT COUNT(*)
     FROM pg_policies
    WHERE tablename = 'tenant_data')::INT                               AS policy_count,

  -- acme role sees only 2 acme rows
  (SELECT COUNT(*)
     FROM (SELECT set_config('role', 'tenant_acme', TRUE)) s,
          saas.tenant_data
    WHERE tenant_id = 'acme')                                           AS acme_row_count,

  -- globex total rows (superuser perspective)
  (SELECT COUNT(*)
     FROM saas.tenant_data
    WHERE tenant_id = 'globex')                                         AS total_globex_rows;
```

**Expected result:** `true | true | 3 | 2 | 2`

---

### Additional Requirement (20 pts)

Implement a **`current_tenant()`** session-variable approach. Instead of one database role per tenant, a single application role sets a session variable that the policy reads dynamically. This is how production multi-tenant apps work at scale.

**Steps:**

1. Create a helper function:

    ```sql
    CREATE OR REPLACE FUNCTION saas.current_tenant()
    RETURNS TEXT LANGUAGE sql STABLE AS $$
      SELECT current_setting('app.current_tenant', TRUE)
    $$;
    ```

2. Drop the existing hardcoded policies and replace them with a single dynamic policy:

    ```sql
    DROP POLICY acme_isolation    ON saas.tenant_data;
    DROP POLICY globex_isolation  ON saas.tenant_data;
    DROP POLICY initech_isolation ON saas.tenant_data;

    -- One policy for ALL roles — filters by session variable
    CREATE POLICY tenant_isolation ON saas.tenant_data
      FOR ALL
      USING     (tenant_id = saas.current_tenant())
      WITH CHECK (tenant_id = saas.current_tenant());
    ```

3. Test the dynamic approach:

    ```sql
    -- Set tenant context in session
    SET LOCAL app.current_tenant = 'acme';
    SELECT tenant_id, data_type, content FROM saas.tenant_data;

    SET LOCAL app.current_tenant = 'globex';
    SELECT tenant_id, data_type, content FROM saas.tenant_data;
    ```

4. Document why `SET LOCAL` (transaction scope) is safer than `SET` (session scope) for web application connection pools.

Submit: the function DDL, the new policy DDL, two SELECT outputs showing correct isolation, and a written explanation of the connection-pool safety argument.

---

### Reflection Questions

1. `FORCE ROW LEVEL SECURITY` means even the table owner is subject to RLS. Without `FORCE`, the table owner can see all rows. Why is `FORCE` important for a SaaS application where the database owner account is also used for schema management? How should schema migrations be handled safely when `FORCE` is active?

2. A developer proposes implementing multi-tenant isolation by appending `WHERE tenant_id = :tenant_id` to every application query rather than using RLS. Why is this approach architecturally inferior? What happens concretely when a single developer forgets the `WHERE` clause in one endpoint? How does RLS eliminate this entire class of vulnerability?

3. RLS policies use `USING` (controls visible rows) and `WITH CHECK` (controls writable rows) as separate clauses. Explain why both are necessary. Specifically: what cross-tenant attack does `WITH CHECK` prevent that `USING` alone cannot stop? Construct a concrete INSERT example that would succeed with only `USING` but is blocked by `WITH CHECK`.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps (Parts 1–4 with screenshots) | 50 |
    | Verification SQL matches expected output | 30 |
    | Additional Requirement (`current_tenant()`) | 20 |
    | **Total** | **100** |
