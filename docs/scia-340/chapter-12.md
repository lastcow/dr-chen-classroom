---
title: "Chapter 12: NoSQL Database Security"
week: 12
chapter: 12
course: SCIA-340
---

# Chapter 12: NoSQL Database Security

## Introduction

The term "NoSQL" covers a diverse family of database systems united by one characteristic: they do not rely primarily on the relational table model or SQL as the query language. Emerging from the demands of web-scale applications in the mid-2000s, NoSQL databases offered horizontal scalability, flexible schemas, and high write throughput that traditional RDBMS architectures struggled to provide at the scale of companies like Google, Amazon, and Facebook. MongoDB, Redis, Cassandra, and Elasticsearch became cornerstones of modern application stacks — and were frequently deployed by teams focused entirely on performance, with security treated as an afterthought.

The consequences have been severe. Researchers using Shodan (a search engine for internet-connected services) have repeatedly found hundreds of thousands of NoSQL databases exposed to the internet with no authentication required. In 2017, a wave of automated attacks targeted open MongoDB instances, deleting databases and leaving ransom notes demanding Bitcoin payments. Understanding why NoSQL databases present unique security challenges — and how to properly secure each major type — is an essential competency for database security professionals.

---

## 12.1 The NoSQL Landscape and Security Challenges

NoSQL databases differ from RDBMS not just in data model, but in their security maturity trajectory. Relational database systems like Oracle and SQL Server have decades of security feature development behind them. Early versions of MongoDB shipped with no authentication required and bound to all network interfaces by default. Redis, designed as an in-memory cache, historically assumed a trusted network environment and provided minimal authentication.

The schema-less nature of document stores means there is no inherent enforcement of what data can be stored in a collection — a field named `ssn` could be added to any document without any schema validation preventing it. This flexibility, while operationally convenient, creates challenges for data classification and access control: you may not know what sensitive data has accumulated in a collection over time.

**Eventual consistency**, common in distributed NoSQL systems, adds a security dimension: audit records or access control updates may not immediately propagate to all nodes, creating brief windows where stale permissions apply.

### NoSQL Database Types and Security Profiles

| Type | Examples | Primary Security Concerns |
|---|---|---|
| Document store | MongoDB, CouchDB, Firestore | Injection via JSON operators, schema flexibility hiding sensitive fields |
| Key-value store | Redis, DynamoDB, Memcached | No built-in auth (legacy), network exposure, dangerous admin commands |
| Column-family | Cassandra, HBase | Default open auth (AllowAll), JMX exposure, inter-node encryption |
| Graph database | Neo4j, Amazon Neptune | Cypher injection, privilege escalation through graph traversal |

---

## 12.2 MongoDB Security Deep Dive

MongoDB has evolved significantly in its security posture. Beginning with version 2.6 and accelerating in version 3.0, MongoDB introduced meaningful authentication and authorization features. By version 4.0, TLS, SCRAM-SHA-256 authentication, and field-level encryption were all available. However, older instances and default configurations still present substantial risk.

### Authentication Mechanisms

MongoDB supports multiple authentication mechanisms:

- **SCRAM (Salted Challenge Response Authentication Mechanism):** The default mechanism for standalone and replica set deployments. SCRAM-SHA-256 (the current default in MongoDB 4.0+) is preferred over SCRAM-SHA-1.
- **x.509 Certificate Authentication:** Clients present a TLS client certificate signed by the same CA trusted by the server. Used in replica sets and sharded clusters for inter-node authentication.
- **LDAP/Active Directory:** MongoDB Enterprise supports proxying authentication to LDAP, enabling centralized identity management.
- **Kerberos:** MongoDB Enterprise supports GSSAPI/Kerberos for environments requiring it.

> **⚠️ Warning:** MongoDB installations with `--auth` not specified, or with `security.authorization: disabled` in the configuration file, allow any connecting client full administrative access. Always enable authentication before exposing any port — even on a "private" network.

### Authorization and Role-Based Access Control

MongoDB implements RBAC through built-in and custom roles. Built-in roles include:

- `read` — read-only access to all non-system collections
- `readWrite` — read and write access to all non-system collections
- `dbAdmin` — administrative tasks but not user management
- `userAdmin` — manage users and roles for the database
- `clusterAdmin` — broadest cluster management role (equivalent to DBA superuser)

Application accounts should be granted only the roles required. A read-only analytics service should receive the `read` role — never `readWrite` or `dbAdmin`. Custom roles allow collection-level granularity:

```javascript
// Create a custom role with read access to only one collection
db.createRole({
  role: "orderReadOnly",
  privileges: [
    {
      resource: { db: "ecommerce", collection: "orders" },
      actions: ["find"]
    }
  ],
  roles: []
});
```

### Network Binding

The `net.bindIp` configuration directive controls which network interfaces MongoDB listens on. The default in MongoDB 3.6+ is `127.0.0.1` (localhost only), a significant improvement over earlier versions that defaulted to all interfaces. In production, `bindIp` should be set to the specific internal IP addresses needed — never `0.0.0.0`, which would expose MongoDB on all interfaces including any public-facing ones.

### Field-Level Encryption (CSFLE)

MongoDB 4.2 introduced Client-Side Field Level Encryption (CSFLE), which allows specific fields within a document to be encrypted on the client before the data reaches the server. The database stores and retrieves the ciphertext; the server never sees the plaintext value. This provides protection even if an attacker gains direct access to the database server, because the encryption keys are held by the client application, not the database.

**MongoDB Atlas** (MongoDB's cloud DBaaS) provides additional security features: IP Access Lists restrict connections to known IP ranges, VPC Peering and Private Link eliminate public internet exposure, and Atlas Encryption at Rest uses cloud KMS integration for key management.

---

## 12.3 NoSQL Injection Attacks

NoSQL databases are not immune to injection — they are vulnerable to different forms of injection that exploit their query languages and operators.

### MongoDB Operator Injection

MongoDB queries are expressed as JSON/BSON documents. When a web application constructs these documents from user input without sanitization, operators like `$gt`, `$regex`, and `$where` can be injected.

Consider a login form that queries MongoDB like this (in Node.js):

```javascript
// VULNERABLE: directly using user-supplied input in query
db.collection('users').findOne({
  username: req.body.username,
  password: req.body.password
});
```

If the attacker submits `{"$gt": ""}` as the password value (in a JSON request body), the query becomes:

```javascript
{ username: "admin", password: { "$gt": "" } }
```

Since every string is "greater than" an empty string, this query matches any user named "admin" regardless of the actual password — a bypass equivalent to SQL's `' OR '1'='1`.

The `$where` operator allows arbitrary JavaScript execution within queries, creating a code injection surface analogous to SQL injection in its severity:

```javascript
// DANGEROUS: $where executes JavaScript server-side
db.users.find({ $where: "this.username == '" + username + "'" });
// If username = "' || '1'=='1", all documents are returned
```

**Mitigation:** Use parameterized query construction, validate and whitelist input types, and for MongoDB specifically, disable server-side JavaScript execution (`security.javascriptEnabled: false`) unless required.

### Redis Command Injection via SSRF

Redis does not use a structured query language — it uses a line-based text protocol (RESP). If an attacker can make a server send raw TCP data to a Redis port (e.g., via SSRF), they can inject Redis commands. Since Redis historically ran without authentication, an SSRF vulnerability reaching an internal Redis port could allow arbitrary command execution, including writing files (via `CONFIG SET dir` and `SAVE`).

---

## 12.4 Redis Security

Redis is widely deployed as a session cache, message queue, and real-time leaderboard store. Its performance-oriented design historically de-prioritized security, but Redis 6.0+ introduced substantial improvements.

### Authentication

**Legacy `requirepass`:** A single shared password for all clients. If compromised, all access is lost. Provides minimal protection against password spraying.

**ACL System (Redis 6.0+):** Access Control Lists allow multiple users with distinct usernames, passwords, and permission sets. Each user can be restricted to specific commands and key patterns:

```bash
# Create a read-only user limited to keys prefixed with "cache:"
ACL SETUSER cacheread on >strongpassword ~cache:* +GET +MGET +EXISTS
```

This is a significant improvement — application accounts should use the ACL system, not the shared `requirepass`.

### Dangerous Commands

Redis includes several commands that, if accessible to unauthorized parties, can cause catastrophic damage or be weaponized:

| Command | Risk |
|---|---|
| `FLUSHALL` | Deletes all data in all Redis databases |
| `FLUSHDB` | Deletes all data in current database |
| `CONFIG SET` | Changes running configuration (can redirect replication, writes) |
| `DEBUG` | Can trigger crashes, sleep delays, or memory dumps |
| `SLAVEOF` / `REPLICAOF` | Can redirect a Redis instance to replicate from an attacker-controlled server |

These commands should be **renamed to random strings** in the Redis configuration to prevent their use even by authenticated clients who shouldn't have access:

```bash
# In redis.conf — rename dangerous commands
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_8f3b2c1d"
rename-command DEBUG ""
```

### Redis Sentinel and Cluster Security

Redis Sentinel (high availability) and Redis Cluster (horizontal shaling) introduce inter-node communication that must also be secured. Authentication should be configured between sentinel nodes and between cluster shards. TLS was added for client-to-server communication in Redis 6.0 and should be enforced in any environment handling sensitive data.

---

## 12.5 Cassandra Security

Apache Cassandra is a distributed column-family store designed for high availability with no single point of failure. Deployed in financial services, telecommunications, and IoT platforms, it requires careful security configuration.

### Authentication and Authorization

Cassandra's authentication is controlled by the `authenticator` setting in `cassandra.yaml`:

- `AllowAllAuthenticator` — **No authentication required.** This is the default and must be changed in any production deployment.
- `PasswordAuthenticator` — Username/password stored in a system table.

Similarly, authorization is controlled by `authorizer`:
- `AllowAllAuthorizer` — **No access controls enforced.**
- `CassandraAuthorizer` — Enables `GRANT`/`REVOKE` permissions on keyspaces and tables.

```cql
-- Create a limited application user in Cassandra
CREATE USER appuser WITH PASSWORD 'securepassword' NOSUPERUSER;
GRANT SELECT ON KEYSPACE ecommerce TO appuser;
```

### JMX Security

Cassandra exposes a Java Management Extensions (JMX) interface for operational monitoring and management tools. By default, JMX is bound to all interfaces on port 7199 with **no authentication**. An attacker reaching this port can execute arbitrary operations — including dumping data and shutting down nodes. JMX must be bound to localhost only, and authentication must be enabled via JMX remote access configuration.

### SSL/TLS

Cassandra supports TLS for both client-to-node (native transport) and node-to-node (internode) communication. Both must be configured explicitly — they are disabled by default.

---

## 12.6 Elasticsearch and OpenSearch Security

Elasticsearch began as a distributed search and analytics engine with no security features whatsoever. Early versions had no authentication, no TLS, and a fully open REST API over HTTP. Shodan researchers have documented over 30,000 publicly accessible Elasticsearch instances at various points in time.

**X-Pack Security** (Elastic's commercial add-on, now free since Elasticsearch 6.8/7.1) provides:
- TLS encryption for inter-node and client communication
- Basic authentication (username/password)
- Role-based access control (RBAC) at the index level

**OpenSearch** (AWS's open-source Elasticsearch fork) includes security via the OpenSearch Security plugin, providing similar TLS, authentication, and RBAC capabilities.

> **Key Definition:** An **index** in Elasticsearch is analogous to a table in RDBMS — the unit of data organization over which access controls are applied. RBAC in Elasticsearch allows restricting users to specific indices and operation types (read, write, delete, manage).

The default configuration of both Elasticsearch and OpenSearch requires explicit security enablement. For OpenSearch managed by AWS (Amazon OpenSearch Service), placing the domain within a VPC and disabling public access is the most impactful security control.

---

## 12.7 Comparing NoSQL vs. RDBMS Security Maturity

Traditional RDBMS platforms like Oracle, SQL Server, and PostgreSQL have decades of security feature development. Built-in auditing, fine-grained access control, row-level security, transparent data encryption, and structured privilege models are mature and well-documented. NoSQL platforms achieved security parity only gradually and inconsistently.

| Feature | Oracle/SQL Server | MongoDB (current) | Redis 6+ | Cassandra |
|---|---|---|---|---|
| Authentication | Mature, multiple methods | SCRAM, x.509, LDAP | ACL system | PasswordAuthenticator |
| Authorization | Column/row level | Collection level | Key/command level | Table/keyspace level |
| Audit logging | Built-in, comprehensive | Available (Enterprise) | Limited | Limited |
| TLS | Default available | Configurable | Configurable | Configurable |
| Default security | Secure defaults | Improved in v3.6+ | Historically open | Open by default |

The takeaway is not that NoSQL databases are inherently insecure, but that their default configurations historically prioritized ease of deployment over security, and administrators must take deliberate steps to close the gaps.

---

## Key Terms

| Term | Definition |
|---|---|
| **NoSQL** | Category of databases not using the relational model or SQL as primary query interface |
| **Document Store** | NoSQL database storing data as flexible JSON/BSON documents (e.g., MongoDB) |
| **Key-Value Store** | NoSQL database storing data as simple key-value pairs (e.g., Redis) |
| **Column-Family Store** | NoSQL database organizing data in column families optimized for read/write performance (e.g., Cassandra) |
| **SCRAM** | Salted Challenge Response Authentication Mechanism — password auth protocol used by MongoDB |
| **CSFLE** | Client-Side Field Level Encryption — MongoDB feature encrypting fields on the client before reaching the server |
| **bindIp** | MongoDB configuration directive controlling which network interfaces the server listens on |
| **NoSQL Injection** | Injection attack exploiting NoSQL query operators or protocols with unsanitized user input |
| **$where** | MongoDB query operator allowing JavaScript execution — highest-risk injection vector |
| **Redis ACL** | Access Control List system in Redis 6+ allowing per-user command and key restrictions |
| **FLUSHALL** | Redis command deleting all data across all databases — must be restricted or renamed |
| **AllowAllAuthenticator** | Cassandra default authenticator requiring no credentials — must be disabled in production |
| **CassandraAuthorizer** | Cassandra authorization plugin enabling GRANT/REVOKE access control |
| **JMX** | Java Management Extensions — Cassandra management interface requiring authentication and restricted binding |
| **X-Pack Security** | Elastic's security module for Elasticsearch providing TLS, authentication, and RBAC |
| **Eventual Consistency** | Distributed database property where all nodes eventually agree on data state, with possible brief inconsistency windows |
| **Shodan** | Internet-connected device search engine used by researchers and attackers to find exposed services |
| **RBAC** | Role-Based Access Control — granting permissions based on roles rather than individual users |

---

## Review Questions

1. **Conceptual:** Why did NoSQL databases historically have weaker security than relational databases? What architectural and cultural factors contributed to this, and how has the ecosystem responded?

2. **Applied:** A MongoDB instance in your organization has `security.authorization` not set in its configuration file. What is the security implication? Write the configuration change needed and the command to verify authentication is enforced after the change.

3. **Applied/Code:** The following Node.js code handles a MongoDB login. Identify the vulnerability, explain how it could be exploited, and rewrite it securely:
   ```javascript
   const user = await db.collection('users').findOne({
     username: req.body.username,
     password: req.body.password
   });
   ```

4. **Conceptual:** Explain the difference between MongoDB's legacy shared-password authentication and the modern ACL system available in Redis 6+. Why is the ACL approach superior for production deployments?

5. **Applied:** List three Redis commands that represent significant security risks if accessible to unauthorized users. For each, explain what damage could be done and how you would mitigate the risk.

6. **Conceptual:** What is Cassandra's `AllowAllAuthenticator`, and why is it particularly dangerous in a production environment? What configuration change is needed to enable proper authentication?

7. **Applied:** An Elasticsearch cluster in your organization is accessible via HTTP on port 9200 from any IP address and has no authentication configured. Outline the remediation steps, prioritizing by criticality.

8. **Conceptual:** Compare MongoDB's CSFLE (Client-Side Field Level Encryption) to traditional database-level encryption. What additional threat does CSFLE protect against that server-side encryption does not?

9. **Applied/Scenario:** You're performing a security review of a Redis instance used as a session cache for a banking application. It uses the legacy `requirepass` directive with a shared password, binds to `0.0.0.0`, does not use TLS, and `FLUSHALL` is not restricted. Rank these issues by severity and provide remediation for each.

10. **Conceptual:** Using the comparison table of NoSQL vs. RDBMS security features in this chapter, explain which gap you consider most critical and why. In what real-world scenario has this gap caused a significant breach?

---

## Further Reading

- MongoDB, Inc. (2024). *MongoDB Security Checklist*. MongoDB Documentation. https://www.mongodb.com/docs/manual/administration/security-checklist/
- Redis Ltd. (2024). *Redis Security*. Redis Documentation. https://redis.io/docs/management/security/
- Elasticsearch B.V. (2024). *Security overview* [Elasticsearch Guide]. Elastic Docs. https://www.elastic.co/guide/en/elasticsearch/reference/current/secure-cluster.html
- Noname Security / Imperva Research Labs. (2022). *NoSQL Injection: The New SQL Injection*. (Technical blog post series on NoSQL injection patterns)
- Apache Software Foundation. (2024). *Apache Cassandra Security*. Cassandra Documentation. https://cassandra.apache.org/doc/latest/cassandra/operating/security.html
