---
title: "SQL Security and SQL Injection — Deep Dive"
chapter: 3
week: 3
course: SCIA-340
---

# Chapter 3: SQL Security and SQL Injection — Deep Dive

## SQL Reviewed Through a Security Lens

SQL (Structured Query Language) is organized into four sub-languages, each with distinct security implications.

**DDL (Data Definition Language)** — `CREATE`, `ALTER`, `DROP`, `TRUNCATE` — defines database structure. DDL privileges should be restricted to DBAs and schema owners, not application accounts. An application account that can execute `DROP TABLE orders` represents a catastrophic misconfiguration.

**DML (Data Manipulation Language)** — `SELECT`, `INSERT`, `UPDATE`, `DELETE` — manipulates data. Application accounts typically need some DML privileges, but the principle of least privilege requires restricting which tables they can access and which operations they can perform. A reporting application needs only `SELECT`; a data entry application may need `INSERT` and `UPDATE` but not `DELETE`.

**DCL (Data Control Language)** — `GRANT`, `REVOKE` — manages privileges. DCL privileges should be restricted to database administrators and security administrators. An application account that can `GRANT` privileges to itself or others represents a direct privilege escalation path.

**TCL (Transaction Control Language)** — `COMMIT`, `ROLLBACK`, `SAVEPOINT` — manages transactions. While most applications use these implicitly, understanding transaction semantics is important because uncommitted data is visible within the current session, which matters for SQL injection payloads that exploit transaction isolation.

## The Anatomy of SQL Injection

SQL injection (SQLi) is the most prevalent and damaging web application vulnerability, consistently appearing at or near the top of the OWASP Top 10. To defend against it, you must understand exactly how it works at the parser level — not just recognize it as a "bad practice."

Consider a PHP login form that queries a database to verify credentials:

```php
// VULNERABLE CODE — DO NOT USE
$username = $_POST['username'];
$password = $_POST['password'];

$query = "SELECT * FROM users 
          WHERE username = '" . $username . "'
          AND password = '" . $password . "'";

$result = mysqli_query($conn, $query);
if (mysqli_num_rows($result) > 0) {
    // Login successful
}
```

When a normal user submits `alice` and `correcthorse`, the query becomes:
```sql
SELECT * FROM users WHERE username = 'alice' AND password = 'correcthorse'
```

This is syntactically valid SQL that returns one row if the credentials are correct — the intended behavior.

Now consider what happens when an attacker submits `' OR '1'='1' --` as the username and anything as the password. The query becomes:

```sql
SELECT * FROM users WHERE username = '' OR '1'='1' --' AND password = 'anything'
```

The `--` begins a SQL comment, causing the password check to be discarded. The condition `'1'='1'` is always true, so the query returns all users. The parser processes this as perfectly valid SQL because the attacker's input has successfully broken out of the string literal context and injected new SQL syntax.

> **Key Concept**: SQL injection works because the application constructs SQL by concatenating strings, allowing attacker-controlled input to be **interpreted as SQL syntax** by the database parser, rather than treated as a **data value**. The fundamental fix is ensuring the parser receives the query structure separately from data values — which is exactly what parameterized queries accomplish.

## Types of SQL Injection

### Classic / In-Band SQL Injection

In-band SQLi is the most common form, where the attacker receives results directly in the same channel used to send the attack.

**Error-based injection** uses database error messages to extract information. When a database error reveals table names, column names, or data types, the attacker uses this information to refine their attack. For example, injecting `'` into a field may produce: `You have an error in your SQL syntax; check the manual that corresponds to your MySQL 8.0 server version for the right syntax to use near ''' at line 1`. This confirms MySQL is in use and that the input is not sanitized.

**UNION-based injection** uses the SQL `UNION` operator to append additional SELECT statements to the original query, extracting data from other tables:

```sql
-- Original query (attacker knows this returns 2 columns of type string):
SELECT product_name, description FROM products WHERE id = 1

-- After injection into the id parameter with value: 1 UNION SELECT username, password FROM users --
SELECT product_name, description FROM products WHERE id = 1
UNION
SELECT username, password FROM users --
```

The second SELECT retrieves usernames and passwords from the users table, and they appear in the application's output alongside or instead of the product data.

### Blind SQL Injection

Blind injection is used when the application doesn't return query results or error messages directly, but the attacker can infer information through indirect signals.

**Boolean-based blind injection** asks yes/no questions by altering query behavior. If the application returns different content for queries that return results vs. no results, an attacker can extract information one bit at a time:

```sql
-- Does the first character of the admin password start with 'a'?
' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin') = 'a' --
-- If the page renders normally, yes; if not, no.
```

**Time-based blind injection** uses database timing functions to signal answers when there is no visible difference between true and false responses:

```sql
-- MySQL: If admin password starts with 'a', sleep 5 seconds
' AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a', SLEEP(5), 0) --

-- PostgreSQL equivalent:
' AND (SELECT CASE WHEN (username='admin' AND SUBSTRING(password,1,1)='a') 
       THEN pg_sleep(5) ELSE pg_sleep(0) END FROM users) --
```

### Out-of-Band SQL Injection

Out-of-band injection exfiltrates data through a completely different channel — such as DNS requests or HTTP requests triggered from the database server. This technique is used when the application response provides no useful feedback. SQL Server's `xp_dirtree` and Oracle's `UTL_HTTP` package have been used in out-of-band injection attacks. This technique requires that the database server have outbound network access, which hardening should restrict.

### Second-Order SQL Injection

Second-order injection is particularly insidious because the malicious payload is stored in the database during one operation and executed during a later, different operation. For example, an attacker might register a username like `admin'--`. This input may be safely parameterized during registration. However, if a subsequent password-change function constructs a query by reading the username from the database and concatenating it into a new query without parameterization, the stored malicious username enables injection at that point. Second-order injection demonstrates that input validation at the point of entry is insufficient — every place where data is used in a SQL query must use parameterized queries.

### NoSQL Injection

SQL injection is not limited to relational databases. Document databases like MongoDB are vulnerable to operator injection. MongoDB queries use JSON-like objects, and if user input is inserted into query objects directly, attackers can inject MongoDB operators:

```javascript
// Vulnerable Node.js code
const user = await db.collection('users').findOne({
    username: req.body.username,
    password: req.body.password
});

// Attacker submits: { "$gt": "" } as the password field
// Resulting query: { username: "admin", password: { $gt: "" } }
// $gt: "" matches any non-empty string — authentication bypassed
```

Defending against NoSQL injection requires the same principle: treat input as data, not as query structure. Use the database driver's parameterized query interface and validate that inputs are of expected types before incorporating them into queries.

## Parameterized Queries and Prepared Statements

Parameterized queries (also called prepared statements) are the primary defense against SQL injection. Understanding why they work requires understanding what happens at the database protocol level.

When a parameterized query is used, the SQL statement and the data values are sent to the database **as separate messages**. The database driver first sends the query template with parameter placeholders to the database, which parses and compiles it. Then the driver sends the parameter values, which the database **binds** to the already-compiled query. Since the query structure has already been parsed, there is no opportunity for parameter values to be interpreted as SQL syntax — they are bound as pure data values.

```python
# VULNERABLE - string concatenation
cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")

# SECURE - parameterized query
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

```java
// VULNERABLE
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(
    "SELECT * FROM users WHERE id = " + userId);

// SECURE - PreparedStatement
PreparedStatement pstmt = conn.prepareStatement(
    "SELECT * FROM users WHERE id = ?");
pstmt.setInt(1, userId);  // userId is bound as an integer data value
ResultSet rs = pstmt.executeQuery();
```

```php
// SECURE - PDO prepared statement
$stmt = $pdo->prepare("SELECT * FROM users WHERE username = :username AND password = :password");
$stmt->bindParam(':username', $username, PDO::PARAM_STR);
$stmt->bindParam(':password', $password, PDO::PARAM_STR);
$stmt->execute();
```

> **⚠ Warning**: Parameterized queries cannot be used for dynamic SQL identifiers — table names and column names cannot be parameterized. If dynamic identifier names are necessary, they must be validated against an explicit allowlist of known-good values. Never incorporate user input directly into SQL identifiers.

## Stored Procedures — Security Benefits and Risks

Stored procedures, when used correctly, provide several security benefits. Application accounts can be granted `EXECUTE` permission on specific stored procedures while having no direct table privileges. This means even if an attacker compromises the application account's credentials, they cannot issue arbitrary SQL — only the specific operations exposed through stored procedures. All data access passes through the stored procedure's logic, which includes input validation and authorization checks.

However, stored procedures are not inherently injection-safe. The danger arises when stored procedures use dynamic SQL internally:

```sql
-- VULNERABLE stored procedure using dynamic SQL
CREATE PROCEDURE search_products(@search_term NVARCHAR(100))
AS BEGIN
    DECLARE @sql NVARCHAR(500)
    SET @sql = 'SELECT * FROM products WHERE name LIKE ''%' + @search_term + '%'''
    EXEC(@sql)  -- This executes dynamic SQL — still vulnerable to injection!
END

-- SECURE version using parameterized dynamic SQL
CREATE PROCEDURE search_products_safe(@search_term NVARCHAR(100))
AS BEGIN
    DECLARE @sql NVARCHAR(500)
    SET @sql = N'SELECT * FROM products WHERE name LIKE @term'
    EXEC sp_executesql @sql, N'@term NVARCHAR(100)', @term = '%' + @search_term + '%'
END
```

## Input Validation and Allowlisting

Input validation is a defense-in-depth measure, not a primary defense against SQL injection. Parameterized queries should always be the primary defense. Input validation should additionally restrict inputs to expected formats, types, and value ranges.

**Allowlisting** (formerly called whitelisting) specifies what is permitted and rejects everything else. For a user ID field, allowlist integers only. For a product category field, allowlist known category names only. Do not attempt to detect and block malicious patterns (denylisting/blacklisting) — attackers can often bypass pattern-based filters through encoding tricks, case variation, or alternate SQL syntax.

## Error Handling and Information Leakage

Verbose database error messages are a reconnaissance gift to attackers. Error messages that reveal database software version, table names, column names, or query structure allow attackers to precisely tailor their injection attempts. Production applications must:

1. Catch database exceptions and log them server-side with full detail
2. Return only generic error messages to users ("An error occurred. Please try again.")
3. Never expose stack traces, SQL queries, or database driver error text to end users

```python
# INSECURE - error propagated to user
try:
    cursor.execute(query)
except Exception as e:
    return f"Database error: {str(e)}"  # Reveals query structure and DB details

# SECURE - error logged, generic message returned
try:
    cursor.execute(query)
except Exception as e:
    logger.error(f"DB query failed for user {session['user']}: {str(e)}")
    return "An unexpected error occurred. Our team has been notified."
```

## Detecting SQL Injection — Database Activity Monitoring

Database Activity Monitoring (DAM) tools sit between applications and the database, analyzing queries in real time. They can detect injection attacks by identifying queries that deviate from a learned baseline, queries containing suspicious patterns (UNION SELECT, comment sequences, stacked queries), unusual data volumes (exfiltration), and queries issued from unexpected source IP addresses or accounts.

**SQLMap** is the most widely used open-source automated SQL injection detection and exploitation tool. From a defensive perspective, security teams should run SQLMap against their own applications in controlled test environments to identify vulnerabilities before attackers do. SQLMap can automatically identify injectable parameters, determine the database backend, extract table schemas, and dump data.

Web Application Firewalls (WAFs) such as ModSecurity, AWS WAF, and Cloudflare WAF can detect and block SQL injection attempts in HTTP requests. WAFs are a valuable defense-in-depth layer but should not be the primary defense — a skilled attacker can often bypass WAF rules through obfuscation, encoding, or splitting payloads across requests.

## Why Encoding and Escaping Are Insufficient

Some developers attempt to defend against SQL injection by escaping special characters — replacing `'` with `\'` or doubling it to `''`. While database-specific escaping functions (`mysql_real_escape_string`, `pg_escape_string`) are better than nothing, they have historically been vulnerable to multi-byte character encoding attacks and are easily forgotten or misapplied. Parameterized queries provide a mechanically guaranteed defense at the protocol level; escaping requires correct, consistent application of a complex transformation that developers frequently get wrong.

## Case Study: Heartland Payment Systems 2008

The Heartland Payment Systems breach of 2008 is a landmark case in the history of SQL injection attacks and its consequences for the payment card industry. Heartland, a credit card payment processor, processed approximately 100 million card transactions per month for 250,000 merchants. Attackers used SQL injection to gain initial access to Heartland's web application servers, then installed packet-sniffing malware that captured card data as it flowed through the payment processing network in plaintext.

The breach resulted in the compromise of approximately **130 million credit and debit card numbers** — at the time, the largest data breach ever reported in the United States. Heartland faced over $140 million in compensation payments to Visa and MasterCard, multiple class action lawsuits, and temporary suspension from the Visa payment network. The attack demonstrated that SQL injection is not merely an academic vulnerability — when combined with network visibility, it can enable catastrophic exfiltration from complex enterprise environments.

The Heartland breach drove several industry changes: PCI DSS requirements for end-to-end encryption of card data at rest and in transit were strengthened, and the breach became a foundational case study in why application-layer vulnerabilities can undermine network-layer data protections.

---

## Key Terms

| Term | Definition |
|------|------------|
| **SQL Injection (SQLi)** | An attack in which malicious SQL is injected through application input to manipulate database queries |
| **In-Band Injection** | SQL injection where results are returned directly through the same application channel |
| **Blind SQL Injection** | SQL injection where the attacker infers information indirectly through application behavior |
| **Boolean-Based Blind Injection** | Blind injection that asks yes/no questions by altering query result set size |
| **Time-Based Blind Injection** | Blind injection that encodes answers as delays using database timing functions |
| **Out-of-Band Injection** | SQL injection that exfiltrates data through a secondary channel (DNS, HTTP) |
| **Second-Order Injection** | Injection where malicious data is stored first, then later incorporated into a vulnerable query |
| **UNION-Based Injection** | Injection using UNION SELECT to append attacker-controlled query results to legitimate output |
| **Parameterized Query** | A query where SQL structure and data values are separated and sent to the database independently |
| **Prepared Statement** | A pre-compiled SQL statement with parameter placeholders, bound to data values before execution |
| **Allowlisting** | Validation approach that defines permitted values/patterns and rejects everything else |
| **Denylisting** | Validation approach that defines forbidden values/patterns — generally insufficient for SQL injection defense |
| **Dynamic SQL** | SQL statements constructed at runtime, potentially from user input — primary injection risk |
| **SQLMap** | Open-source automated tool for detecting and exploiting SQL injection vulnerabilities |
| **Database Activity Monitoring (DAM)** | Real-time monitoring system that analyzes database queries for anomalous or malicious activity |
| **Web Application Firewall (WAF)** | Security appliance or service that inspects HTTP traffic and blocks known attack patterns |
| **NoSQL Injection** | Injection attacks targeting document/key-value databases through operator or document structure manipulation |
| **Error-Based Injection** | SQL injection technique that extracts information from verbose database error messages |
| **DDL** | Data Definition Language — SQL statements that define database structure (CREATE, ALTER, DROP) |
| **DML** | Data Manipulation Language — SQL statements that manipulate data (SELECT, INSERT, UPDATE, DELETE) |

---

## Review Questions

1. **Applied**: Write a vulnerable PHP login function that uses string concatenation to build a SQL query. Then rewrite it using PDO prepared statements. Explain exactly why the prepared statement version prevents the injection that was possible in the vulnerable version.

2. **Conceptual**: Explain the difference between error-based, union-based, boolean-based blind, and time-based blind SQL injection. For each type, describe the application conditions that make that technique necessary or advantageous.

3. **Applied**: A web application has a search field that returns product names matching the search term. Write a time-based blind injection payload that could determine whether the application is running on MySQL or PostgreSQL by exploiting differences in their timing functions. Explain how an attacker would use this for fingerprinting.

4. **Conceptual**: Explain second-order SQL injection. Why does it demonstrate that input sanitization at the point of entry is insufficient? Give a concrete example with a registration/login scenario.

5. **Applied**: The following Python code uses string formatting to build a query: `cursor.execute(f"SELECT * FROM orders WHERE customer_id = {customer_id}")`. Identify the vulnerability, write the fixed version, and explain what database-level controls (such as least privilege for the database account) would limit the damage if injection still occurred.

6. **Conceptual**: Why are WAFs and input escaping considered insufficient as sole defenses against SQL injection? Under what circumstances might WAF bypass be possible?

7. **Applied**: Using SQLMap's documentation, describe the flags you would use to test a login form at `https://example.com/login` for SQL injection, targeting only the `username` and `password` POST parameters without aggressive testing that might crash the application.

8. **Conceptual**: The Heartland breach combined SQL injection with network-level packet sniffing. Explain how encryption in transit (TLS) and at rest (TDE) would have mitigated the impact of this breach, and why SQL injection prevention would still have been the most important control.

9. **Applied**: A stored procedure accepts a `@sort_column` parameter to order query results. Write a version of the stored procedure that safely handles this dynamic identifier using an allowlist approach, and explain why you cannot use parameterization for column names.

10. **Conceptual**: Compare MongoDB operator injection to traditional SQL injection. What are the structural similarities and differences? What is the equivalent of parameterized queries in the MongoDB Node.js driver?

---

## Further Reading

- **OWASP Foundation. (2021). *SQL Injection Prevention Cheat Sheet*.** The definitive reference for parameterized queries across languages and frameworks. Available at cheatsheetseries.owasp.org.

- **Clarke, J. (2009). *SQL Injection Attacks and Defense*. Syngress.** Comprehensive technical book covering injection mechanics, all attack types, and platform-specific defenses for Oracle, SQL Server, MySQL, and PostgreSQL.

- **Stuttard, D., & Pinto, M. (2011). *The Web Application Hacker's Handbook* (2nd ed.). Wiley.** Chapters 9–10 cover SQL injection attack techniques in exhaustive technical detail, essential reading for understanding the attacker perspective.

- **Hoang, T., et al. (2019). "SQLiGoT: Detecting SQL injection attacks using graph of tokens and SVM." *Computers & Security*, 86, 116–127.** Academic study of ML-based SQL injection detection, relevant to the DAM section.

- **PCI Security Standards Council. (2022). *PCI DSS v4.0*.** Requirement 6.2 and associated guidance covers secure development practices including injection prevention. Available at pcisecuritystandards.org.
