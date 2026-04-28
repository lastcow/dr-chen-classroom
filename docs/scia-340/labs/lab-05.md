---
title: "Lab 05: Role-Based Access Control (RBAC) — Building a Privilege Hierarchy"
course: SCIA-340
topic: "Access Control Models — DAC, MAC, RBAC"
week: "5 (Part A)"
difficulty: ⭐⭐
estimated_time: 75 minutes
---

# Lab 05: Role-Based Access Control (RBAC) — Building a Privilege Hierarchy

| Field | Details |
|---|---|
| **Course** | SCIA-340 — Database Security |
| **Week** | 5 (Part A) |
| **Difficulty** | ⭐⭐ Foundational |
| **Estimated Time** | 75 minutes |
| **Topic** | Access Control Models — DAC, MAC, RBAC |
| **Prerequisites** | Labs 01–04 complete; familiarity with PostgreSQL roles and GRANT syntax |
| **Deliverables** | Screenshots at each checkpoint + verification script output + fourth-tier implementation |

---

## Overview

Role-Based Access Control (RBAC) is the primary access control model in PostgreSQL. Rather than granting privileges directly to individual users, RBAC assigns users to **roles** that carry privileges — making administration of hundreds of users tractable and auditable. In this lab you will:

1. Design a three-tier role hierarchy for a corporate database: read-only, analyst, and DBA.
2. Assign granular, table-level privileges to each tier.
3. Create login users that inherit privileges through role membership.
4. Verify the privilege matrix using `has_table_privilege()` — the same function used in security audits.
5. Extend the hierarchy with a fourth branch (Finance) in the additional requirement.

---

!!! warning "Branch Requirement"
    All SQL must be executed on your Neon branch. **Name your branch `lab-05` before starting.**
    All roles, schemas, and tables in this lab must be present on the `lab-05` branch when the verification script runs.

!!! info "Neon Setup — How to Connect"
    1. Log in to [https://neon.tech](https://neon.tech) and select your **`lab-05`** branch.
    2. Copy the connection string from **Dashboard → Connection Details**.
    3. Connect:
       ```bash
       export DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/scia340?sslmode=require"
       psql $DATABASE_URL
       ```
       ```
       \c scia340
       ```

---

## Part 1 — Design the Schema and Data

### Step 1.1 — Create Corporate Schema and Tables

We create a realistic corporate database with three tables of varying sensitivity:

- `corp.customers` — customer PII (moderately sensitive)
- `corp.orders` — transaction records (business-critical)
- `corp.salaries` — compensation data (highly sensitive — HR only)

```sql
CREATE SCHEMA IF NOT EXISTS corp;

CREATE TABLE corp.customers (
  id           SERIAL PRIMARY KEY,
  name         TEXT          NOT NULL,
  email        TEXT          NOT NULL,
  credit_limit NUMERIC(10,2) DEFAULT 1000
);

CREATE TABLE corp.orders (
  id          SERIAL PRIMARY KEY,
  customer_id INT           REFERENCES corp.customers(id),
  product     TEXT          NOT NULL,
  amount      NUMERIC(10,2) NOT NULL,
  created_at  TIMESTAMPTZ   DEFAULT NOW()
);

CREATE TABLE corp.salaries (
  id         SERIAL PRIMARY KEY,
  employee   TEXT          NOT NULL,
  department TEXT          NOT NULL,
  salary     NUMERIC(10,2) NOT NULL
);

-- Seed data
INSERT INTO corp.customers (name, email, credit_limit) VALUES
  ('Alice Corp', 'billing@alice.com', 5000),
  ('Bob Inc',    'ap@bob.com',        2500);

INSERT INTO corp.orders (customer_id, product, amount) VALUES
  (1, 'Enterprise License', 4999.00),
  (2, 'Support Package',     999.00);

INSERT INTO corp.salaries (employee, department, salary) VALUES
  ('Alice Chen', 'Engineering', 95000),
  ('Bob Smith',  'Sales',       72000);
```

Verify:

```sql
SELECT * FROM corp.customers;
SELECT * FROM corp.orders;
SELECT * FROM corp.salaries;
```

---

## Part 2 — Build Role Hierarchy

### Step 2.1 — Create the Three Tiers

The hierarchy is built from group roles (NOLOGIN) that carry privileges. Login users are created separately and placed into these groups — they never receive table privileges directly.

```sql
-- Tier 1: Read-only (customer service, help desk, support staff)
CREATE ROLE role_readonly NOLOGIN;

-- Tier 2: Analyst (data team — reads everything, writes orders)
CREATE ROLE role_analyst NOLOGIN;

-- Tier 3: DBA (full control — schema management and administration)
CREATE ROLE role_dba NOLOGIN;

-- All tiers need USAGE on the corp schema to see objects inside it
GRANT USAGE ON SCHEMA corp TO role_readonly, role_analyst, role_dba;
```

!!! info "USAGE vs SELECT"
    `GRANT USAGE ON SCHEMA` allows a role to **see into** the schema (resolve object names). It does not grant access to any individual table. You still need explicit `SELECT`, `INSERT`, etc. grants on each table.

---

### Step 2.2 — Assign Granular Privileges

```sql
-- ----------------------------------------------------------------
-- TIER 1: role_readonly
-- Can read customers and orders. Cannot see salaries at all.
-- ----------------------------------------------------------------
GRANT SELECT ON corp.customers TO role_readonly;
GRANT SELECT ON corp.orders    TO role_readonly;
-- NO grant on corp.salaries — intentionally omitted

-- ----------------------------------------------------------------
-- TIER 2: role_analyst
-- Inherits Tier 1 via role membership, plus write access to orders
-- and read access to salaries.
-- ----------------------------------------------------------------
GRANT role_readonly TO role_analyst;   -- inheritance: analyst gets all readonly privs

GRANT SELECT, INSERT, UPDATE ON corp.orders     TO role_analyst;
GRANT USAGE  ON SEQUENCE corp.orders_id_seq     TO role_analyst;
GRANT SELECT ON corp.salaries                   TO role_analyst;

-- ----------------------------------------------------------------
-- TIER 3: role_dba
-- Inherits Tier 2 via role membership, plus full control on all
-- tables and sequences in the corp schema.
-- ----------------------------------------------------------------
GRANT role_analyst TO role_dba;   -- inheritance: dba gets all analyst privs

GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA corp TO role_dba;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA corp TO role_dba;
```

**Expected privilege matrix after grants:**

| Role | customers SELECT | orders SELECT | orders INSERT | salaries SELECT | salaries DELETE |
|---|---|---|---|---|---|
| `role_readonly` | ✓ | ✓ | ✗ | ✗ | ✗ |
| `role_analyst` | ✓ | ✓ | ✓ | ✓ | ✗ |
| `role_dba` | ✓ | ✓ | ✓ | ✓ | ✓ |

---

### Step 2.3 — Create Login Users Assigned to Tiers

```sql
-- Login users are created with IN ROLE to immediately assign tier membership
CREATE ROLE user_support
  LOGIN
  PASSWORD 'Support_Secure#2026'
  IN ROLE role_readonly;

CREATE ROLE user_analyst
  LOGIN
  PASSWORD 'Analyst_Secure#2026'
  IN ROLE role_analyst;

CREATE ROLE user_dba
  LOGIN
  PASSWORD 'DBA_Secure#2026'
  IN ROLE role_dba;
```

!!! tip "Best Practice: Separate Identity from Privilege"
    By granting privileges to **group roles** (`role_readonly` etc.) and assigning **login users** to those groups, you gain two benefits: (1) adding a new user with a given access level requires one `GRANT role_X TO new_user` statement, not re-granting every table; (2) removing a user's access tier requires only `REVOKE role_X FROM user` — privileges are never scattered across individual users.

---

## Part 3 — Verify the Privilege Matrix

### Step 3.1 — Test Each Role's Access with `has_table_privilege()`

```sql
SELECT
  r.rolname,
  has_table_privilege(r.rolname, 'corp.customers', 'SELECT') AS read_customers,
  has_table_privilege(r.rolname, 'corp.orders',    'SELECT') AS read_orders,
  has_table_privilege(r.rolname, 'corp.orders',    'INSERT') AS insert_orders,
  has_table_privilege(r.rolname, 'corp.salaries',  'SELECT') AS read_salaries,
  has_table_privilege(r.rolname, 'corp.salaries',  'DELETE') AS delete_salaries
FROM pg_roles r
WHERE r.rolname IN ('role_readonly', 'role_analyst', 'role_dba')
ORDER BY r.rolname;
```

**Expected output:**

| rolname | read_customers | read_orders | insert_orders | read_salaries | delete_salaries |
|---|---|---|---|---|---|
| role_analyst | t | t | t | t | f |
| role_dba | t | t | t | t | t |
| role_readonly | t | t | f | f | f |

📸 **Screenshot checkpoint:** Capture the privilege matrix showing all five columns for all three roles.

---

### Step 3.2 — Verify Role Membership (Inheritance Chain)

```sql
SELECT
  r.rolname                                           AS role,
  string_agg(m.rolname, ' → ' ORDER BY m.rolname)    AS member_of
FROM pg_roles r
LEFT JOIN pg_auth_members am ON am.member  = r.oid
LEFT JOIN pg_roles m         ON m.oid      = am.roleid
WHERE r.rolname IN (
  'role_readonly', 'role_analyst', 'role_dba',
  'user_support', 'user_analyst', 'user_dba'
)
GROUP BY r.rolname
ORDER BY r.rolname;
```

This query shows the direct membership relationships. You should see:

- `role_analyst` → member of `role_readonly`
- `role_dba` → member of `role_analyst`
- `user_support` → member of `role_readonly`
- `user_analyst` → member of `role_analyst`
- `user_dba` → member of `role_dba`

📸 **Screenshot checkpoint:** Capture the role membership chain.

---

### Step 3.3 — Verify Login Users Inherit Group Role Privileges

```sql
SELECT
  u.rolname                                                       AS login_user,
  has_table_privilege(u.rolname, 'corp.customers', 'SELECT')     AS can_read_customers,
  has_table_privilege(u.rolname, 'corp.salaries',  'SELECT')     AS can_read_salaries,
  has_table_privilege(u.rolname, 'corp.salaries',  'DELETE')     AS can_delete_salaries
FROM pg_roles u
WHERE u.rolname IN ('user_support', 'user_analyst', 'user_dba')
ORDER BY u.rolname;
```

**Expected:**

| login_user | can_read_customers | can_read_salaries | can_delete_salaries |
|---|---|---|---|
| user_analyst | t | t | f |
| user_dba | t | t | t |
| user_support | t | f | f |

📸 **Screenshot checkpoint:** Capture the login user privilege verification.

---

## Cleanup / Reset

To remove all objects created in this lab:

```sql
-- Remove login users first (cannot drop roles with members without REASSIGN/DROP)
DROP ROLE IF EXISTS user_support;
DROP ROLE IF EXISTS user_analyst;
DROP ROLE IF EXISTS user_dba;

-- Remove group roles
DROP ROLE IF EXISTS role_readonly;
DROP ROLE IF EXISTS role_analyst;
DROP ROLE IF EXISTS role_dba;

-- Remove schema and all tables
DROP SCHEMA IF EXISTS corp CASCADE;
```

!!! warning
    Run cleanup only when explicitly resetting. The verification script requires all roles and tables to exist.

---

## Assessment

### Verification Script

Dr. Chen will run the following script against your Neon `lab-05` branch connection string.

```sql
-- VERIFY LAB 05

SELECT
  -- All three tier group roles exist
  (SELECT COUNT(*)
   FROM pg_roles
   WHERE rolname IN ('role_readonly','role_analyst','role_dba'))::INT
                                                                    AS tiers_created,

  -- role_readonly can select customers
  has_table_privilege('role_readonly', 'corp.customers', 'SELECT') AS readonly_can_select,

  -- role_readonly CANNOT select salaries (confirms tier restriction)
  has_table_privilege('role_readonly', 'corp.salaries',  'SELECT') AS readonly_cannot_see_salaries,

  -- role_analyst CAN select salaries
  has_table_privilege('role_analyst',  'corp.salaries',  'SELECT') AS analyst_can_see_salaries,

  -- role_analyst CAN insert orders
  has_table_privilege('role_analyst',  'corp.orders',    'INSERT') AS analyst_can_insert_orders,

  -- role_dba CAN delete from salaries (full control)
  has_table_privilege('role_dba',      'corp.salaries',  'DELETE') AS dba_can_delete;
```

**Expected results:**

| tiers_created | readonly_can_select | readonly_cannot_see_salaries | analyst_can_see_salaries | analyst_can_insert_orders | dba_can_delete |
|---|---|---|---|---|---|
| 3 | true | **false** | true | true | true |

!!! warning "Note on `readonly_cannot_see_salaries`"
    This column must return **`false`** to pass. `false` is the **correct** security outcome — it confirms the tier restriction is working. A value of `true` here would mean `role_readonly` can see salary data, which is a configuration failure.

---

### Additional Requirement

**Fourth tier: Finance role** *(20 pts)*

Add a separate branch to the hierarchy. The Finance role needs access to financial and operational data but should **not** see customer PII.

Implement the following:

1. Create the group role:

```sql
CREATE ROLE role_finance NOLOGIN;
GRANT USAGE ON SCHEMA corp TO role_finance;
```

2. Grant privileges — Finance can read salaries and orders, **but NOT customers**:

```sql
GRANT SELECT ON corp.salaries TO role_finance;
GRANT SELECT ON corp.orders   TO role_finance;
-- Intentionally NO grant on corp.customers
```

3. Create the login user:

```sql
CREATE ROLE user_finance
  LOGIN
  PASSWORD 'Finance_Secure#2026'
  IN ROLE role_finance;
```

!!! info "Independent Branch Design"
    `role_finance` must **not** be granted `role_readonly` membership — it is a separate branch of the hierarchy, not a sub-tier of readonly. Finance can see salaries (which readonly cannot) but cannot see customers (which readonly can). This is impossible to model with simple inheritance; it requires a separate independent role.

4. Verify with `has_table_privilege()`:

```sql
SELECT
  u.rolname,
  has_table_privilege(u.rolname, 'corp.customers', 'SELECT') AS read_customers,
  has_table_privilege(u.rolname, 'corp.orders',    'SELECT') AS read_orders,
  has_table_privilege(u.rolname, 'corp.salaries',  'SELECT') AS read_salaries
FROM pg_roles u
WHERE u.rolname IN ('user_support','user_analyst','user_dba','user_finance')
ORDER BY u.rolname;
```

5. Show the **full updated privilege matrix** for all four tiers (including `role_finance`):

```sql
SELECT
  r.rolname,
  has_table_privilege(r.rolname, 'corp.customers', 'SELECT') AS read_customers,
  has_table_privilege(r.rolname, 'corp.orders',    'SELECT') AS read_orders,
  has_table_privilege(r.rolname, 'corp.orders',    'INSERT') AS insert_orders,
  has_table_privilege(r.rolname, 'corp.salaries',  'SELECT') AS read_salaries,
  has_table_privilege(r.rolname, 'corp.salaries',  'DELETE') AS delete_salaries
FROM pg_roles r
WHERE r.rolname IN ('role_readonly','role_analyst','role_dba','role_finance')
ORDER BY r.rolname;
```

**Submit:** All SQL from steps 1–5, and a screenshot of the four-tier privilege matrix. The `role_finance` row must show `read_customers = false`, `read_orders = true`, `read_salaries = true`.

---

### Reflection Questions

Answer each question in **3–5 sentences** in your lab report.

1. **Inheritance Benefits and Risks** — Role inheritance means `role_analyst` automatically receives all permissions granted to `role_readonly`. What is the security benefit of this cascading design for an administrator managing 200 support staff? What is the security risk if a role accidentally gains membership in a higher-privilege group — and what does the blast radius look like if `role_analyst` were mistakenly granted `role_dba`?

2. **Group Roles vs Direct Grants** — You granted privileges to the **group roles** (`role_readonly`, etc.) rather than to the login users directly. Why is this the architecturally correct approach for a large organization? Describe two specific administrative operations that become dramatically simpler under the group-role model versus the direct-grant model, and explain how each operation would differ.

3. **The Salaries Table and Tier Design** — In this RBAC design, `role_readonly` cannot see `corp.salaries` but `role_analyst` can. Is giving all analysts access to salary data the right security decision for a real organization? Name two roles in a real company that would logically be assigned to `role_analyst` but should **not** see salary data. How would you further restrict the salaries table — within this tier structure — to implement need-to-know access without restructuring the entire hierarchy?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Lab steps completed with screenshots at all checkpoints | 50 |
    | Verification script — all 6 values correct (including `readonly_cannot_see_salaries = false`) | 30 |
    | Additional requirement — `role_finance` and `user_finance` implemented, four-tier matrix screenshot provided | 20 |
    | **Total** | **100** |
