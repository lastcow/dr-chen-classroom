---
title: "Database Network Security and Communications"
week: 7
chapter: 7
course: SCIA-340
---

# Chapter 7: Database Network Security and Communications

## Introduction

A database sitting behind layers of application code, firewalls, and access controls can still be reached by an attacker who compromises an application server. The network path between client applications and the database server is a critical attack surface that requires deliberate architectural decisions and ongoing monitoring. This chapter examines how databases are exposed over networks, why default configurations are routinely dangerous, and how to layer network-level controls to limit exposure. We cover transport encryption, database firewalls, network segmentation, secure application connection patterns, and the Zero Trust model as applied to database communications.

---

## 7.1 The Database Network Attack Surface

Databases are rarely exposed directly to the internet — intentionally. But they are almost always reachable from application servers, and application servers are reachable from the internet. This creates a common attack path: exploit a web application vulnerability, gain a foothold on the application server, pivot to the database network, and query or exfiltrate data directly. The attacker may use the application server as a stepping stone, running their own SQL queries through a stolen database account or by exploiting the application's database connection.

Understanding which hosts can reach which database ports — and under what authentication — is the foundation of network-level database security.

### Default Ports: Why They Are a Risk

Default ports are widely known, actively scanned, and indexed by services like Shodan. When a database listens on its default port and is reachable from an unnecessarily broad network range, it increases the attack surface significantly.

| Database | Default Port | Protocol |
|---|---|---|
| Oracle Database | 1521 | Oracle TNS |
| SQL Server | 1433 | TDS (Tabular Data Stream) |
| MySQL / MariaDB | 3306 | MySQL protocol |
| PostgreSQL | 5432 | PostgreSQL protocol |
| MongoDB | 27017 | MongoDB Wire Protocol |
| Redis | 6379 | RESP (plain text by default) |
| Cassandra | 9042 | CQL Native Protocol |
| Elasticsearch | 9200 | HTTP (often no auth by default) |

Changing the default port is a minor obfuscation measure, not a real security control. It reduces noise from automated scanners but does not deter a focused attacker. The real control is firewall rules that prevent unauthorized hosts from reaching those ports at all, regardless of the port number.

> **⚠️ Warning — MongoDB and Redis:** These NoSQL databases were historically designed for trusted internal networks and shipped with no authentication enabled by default. Thousands of MongoDB and Redis instances have been found exposed on the public internet with no authentication. Even internally, treat them as requiring explicit access control.

---

## 7.2 Network Segmentation for Databases

The foundational principle is that databases belong in a dedicated, restricted network tier — not in the same segment as web servers or user workstations, and certainly not in the DMZ (demilitarized zone).

### The Three-Tier Architecture

```
Internet
    │
[WAF / Load Balancer]
    │
[DMZ — Web/Application Tier]
    │  ← Firewall (allow only app port to DB tier)
[Private Subnet — Database Tier]
    │
[Database Servers]
```

In a properly segmented architecture:
- The web tier (DMZ) can reach the application tier on specific ports.
- The application tier can reach the database tier on the specific database port — but only from the application server's IP addresses.
- No direct path exists from the internet or web tier to the database tier.
- DBA workstations access the database only through a jump server/bastion host, never directly.

**Cloud security groups** (AWS Security Groups, Azure NSGs, GCP Firewall Rules) implement this at the virtual network level. A database security group should have inbound rules that permit only:
- The application server security group on the database port
- The DBA bastion host security group on the database port and SSH/RDP

Everything else should be denied by default.

---

## 7.3 Database Firewalls

A database firewall (sometimes called a database activity monitor with blocking capability) sits between the application tier and the database, inspecting SQL traffic in real time. Unlike network firewalls that operate at the IP/port level, database firewalls understand SQL and can:

- Block specific SQL statement patterns (e.g., `SELECT *` from a sensitive table by a non-DBA account)
- Detect and block SQL injection attempts
- Enforce a "whitelist" of approved SQL statements — deviations trigger alerts or blocks
- Alert on access to sensitive tables outside business hours
- Rate-limit queries to detect bulk data extraction

**Imperva SecureSphere** and **IBM Guardium** (discussed further in Chapter 8) are the leading enterprise database firewall/monitoring products. They typically operate in one of two modes:

- **Monitoring (non-blocking) mode**: Traffic is inspected and logged but not blocked. Low risk of causing application downtime; used initially to baseline behavior.
- **Blocking mode**: Non-compliant traffic is actively blocked. Requires careful policy tuning to avoid false positives that impact legitimate application traffic.

---

## 7.4 Encrypting Database Connections in Transit

Encrypting data at rest (Chapter 6) is only half the picture. Data in transit — traveling between the application server and the database — must also be encrypted to prevent eavesdropping and man-in-the-middle attacks, especially in environments where traffic traverses shared network infrastructure (cloud provider backbones, shared VLANs, or compromised routers).

### 7.4.1 TLS for Database Protocols

All major database platforms support TLS (Transport Layer Security) for client connections.

**PostgreSQL TLS Configuration:**
```ini
# postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = 'root.crt'
ssl_min_protocol_version = 'TLSv1.2'
```

```ini
# pg_hba.conf — require SSL for the app user
hostssl  appdb  appuser  10.0.1.0/24  scram-sha-256
```

Client connection string with full certificate verification:
```
postgresql://appuser@dbhost:5432/appdb?sslmode=verify-full&sslrootcert=root.crt
```

**MySQL TLS Configuration:**
```ini
# my.cnf
[mysqld]
require_secure_transport = ON
ssl_ca = /etc/mysql/certs/ca.pem
ssl_cert = /etc/mysql/certs/server-cert.pem
ssl_key = /etc/mysql/certs/server-key.pem
```

**SQL Server:**
In SQL Server Configuration Manager, enable "Force Encryption" to require TLS for all incoming connections. Supply a valid certificate from a trusted CA.

### 7.4.2 The sslmode=require Trap

PostgreSQL's `sslmode=require` setting enables SSL but does **not** verify the server's certificate. This protects against passive eavesdropping but does *not* protect against an active man-in-the-middle attack, where an attacker intercepts and impersonates the server. Only `sslmode=verify-full` (which checks both the certificate chain and the hostname) provides full protection.

> **⚠️ Critical Warning:** `sslmode=require` is not equivalent to `sslmode=verify-full`. A developer who sets `sslmode=require` and believes they are fully protected against MITM attacks is mistaken. Always use `verify-full` or `verify-ca` in production, and supply the CA certificate.

This pattern appears in other databases too. SQL Server applications that accept any certificate (`TrustServerCertificate=True` in the connection string) are equally vulnerable.

---

## 7.5 Secure Connection Strings in Application Code

Connection strings are a frequent source of credential exposure and misconfiguration. Common vulnerabilities include:

**Hardcoded credentials in source code:**
```python
# BAD — never do this
conn = psycopg2.connect("host=db.internal user=appuser password=supersecret dbname=appdb")
```

**Disabled certificate validation:**
```python
# BAD — vulnerable to MITM
conn = psycopg2.connect("host=db.internal sslmode=require")
# GOOD
conn = psycopg2.connect("host=db.internal sslmode=verify-full sslrootcert=/etc/ssl/certs/db-ca.crt")
```

Best practices for connection strings:
- Store credentials in environment variables, secrets managers (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault), or encrypted configuration files — never in source code or version control.
- Use `sslmode=verify-full` and supply the CA certificate.
- Use the principle of least privilege for the database account in the connection string.
- Rotate database passwords regularly and ensure the secrets manager integration supports automated rotation.

---

## 7.6 Database Proxies

Database proxies sit between applications and database servers, providing connection pooling, security, and abstraction. They offer several security benefits:

**ProxySQL** (MySQL/MariaDB) and **PgBouncer** (PostgreSQL) provide connection pooling, which limits the number of direct connections to the database. From a security perspective, they also allow:
- Centralized SSL termination
- Query rewriting and filtering
- Read/write splitting (directing reads to replicas, reducing primary exposure)
- Credential abstraction — applications authenticate to the proxy, and the proxy uses its own credentials to connect to the database, reducing credential exposure

**AWS RDS Proxy** is a fully managed proxy for RDS and Aurora databases. It enforces IAM authentication between the application and the proxy, eliminating long-lived database passwords in application code.

---

## 7.7 Network Scanning and Exposed Databases

Organizations should regularly scan their own networks for inadvertently exposed database ports. Attackers certainly do.

**Shodan** (shodan.io) is a search engine for internet-connected devices. Queries like `port:5432 country:US` or `port:27017 product:MongoDB` reveal publicly accessible databases. Defensive use of Shodan — searching for your own IP ranges — is a legitimate security practice.

**nmap** for database discovery:
```bash
# Scan a subnet for common database ports
nmap -p 1433,1521,3306,5432,27017,6379 --open 10.0.0.0/24

# Version detection on a specific host
nmap -sV -p 1433 192.168.1.100

# Use nmap scripts for database enumeration
nmap -p 1433 --script ms-sql-info 192.168.1.100
nmap -p 3306 --script mysql-info 192.168.1.101
```

Banner grabbing via nmap reveals the database type, version, and sometimes patch level — information an attacker uses to select appropriate CVE exploits.

---

## 7.8 Oracle TNS Listener Security

Oracle databases communicate using the Transparent Network Substrate (TNS) protocol, managed by the Oracle Listener process on port 1521. The listener has historically been a significant attack surface.

**CVE-2012-1675 — TNS Listener Poisoning:** This vulnerability (known as the "TNS Listener Poison Attack") allowed an unauthenticated attacker to redirect database clients to a rogue server, enabling credential theft and data manipulation. It affected Oracle Database 10g, 11g, and 12c. Oracle's patch requires setting `VALID_NODE_CHECKING_REGISTRATION` to enforce that only authorized database instances can register with the listener.

Listener hardening checklist:
- Set a listener password (Oracle 10g and earlier — deprecated but still found in older systems)
- Enable `VALID_NODE_CHECKING` and `VALID_NODE_CHECKING_REGISTRATION`
- Restrict external procedure execution (extproc)
- Monitor the listener log for unauthorized registration attempts
- Run the listener as a dedicated, low-privilege OS user

---

## 7.9 VPNs, SSH Tunnels, and Bastion Hosts

Direct DBA access to production databases over the network is a significant risk. The recommended pattern is to require all DBA access to route through a **bastion host** (also called a jump server) — a hardened, heavily monitored server with limited functionality that acts as the single entry point to the database network.

**SSH tunneling** allows encrypted database connections over an SSH session:
```bash
# Forward local port 5433 to the remote PostgreSQL port via the bastion
ssh -L 5433:db.internal:5432 bastion.example.com
# Then connect locally
psql -h localhost -p 5433 -U dba appdb
```

This pattern:
- Encrypts the database connection inside the SSH tunnel
- Creates an audit trail of DBA access through the bastion host's SSH logs
- Avoids exposing the database port outside the internal network
- Enables multi-factor authentication on the SSH connection

In cloud environments, **AWS Systems Manager Session Manager** provides a similar capability without requiring an open SSH port, further reducing the attack surface.

---

## 7.10 Zero Trust Applied to Database Access

Traditional network security assumed that traffic inside the network perimeter was trustworthy. Zero Trust rejects this assumption: no traffic is trusted by default, regardless of source network. Applied to databases:

- **Verify explicitly:** Every database connection must be authenticated and authorized, even from within the data center. Database accounts should not have broad network-level implicit trust.
- **Use least privilege access:** Application accounts should have only the permissions needed for their function. DBA accounts should be used only for administrative tasks, never by applications.
- **Assume breach:** Monitor all database traffic as if an attacker may already be present. Anomalous query patterns, unexpected access times, or unusual volumes of data exported should trigger alerts.
- **Continuous validation:** Database sessions should not persist indefinitely. Short session timeouts and re-authentication requirements limit the window of exposure for a hijacked session.

Cloud-native Zero Trust tools include **Google BeyondCorp**, **Cloudflare Access**, and **AWS Verified Access**, which can enforce contextual access policies before allowing connections to reach database proxies.

---

## Key Terms

| Term | Definition |
|---|---|
| **TNS (Transparent Network Substrate)** | Oracle's proprietary network protocol for database communications |
| **TDS (Tabular Data Stream)** | Microsoft's protocol for SQL Server client-server communication |
| **sslmode=verify-full** | PostgreSQL connection mode that validates server certificate and hostname |
| **Man-in-the-Middle (MITM) Attack** | Attack where an adversary intercepts and potentially alters communication between two parties |
| **Network Segmentation** | Dividing a network into isolated zones to limit lateral movement after a breach |
| **DMZ (Demilitarized Zone)** | Network segment for internet-facing services, separated from internal networks |
| **Database Firewall** | Device or software that inspects and optionally blocks SQL traffic based on policy |
| **Connection Pooling** | Maintaining a pool of database connections to reduce connection overhead |
| **Bastion Host / Jump Server** | Hardened server that acts as the single entry point to a restricted network |
| **ProxySQL** | Open-source MySQL/MariaDB proxy with connection pooling and query routing |
| **PgBouncer** | Lightweight PostgreSQL connection pooler |
| **Shodan** | Internet-connected device search engine used by attackers and defenders |
| **Banner Grabbing** | Retrieving service information (version, type) from a network service response |
| **Zero Trust** | Security model requiring explicit verification of every access request regardless of network location |
| **AWS RDS Proxy** | Managed database proxy for RDS/Aurora supporting IAM authentication |
| **SSH Tunneling** | Encapsulating a network connection inside an encrypted SSH session |
| **VALID_NODE_CHECKING** | Oracle listener parameter restricting which hosts can connect |
| **Force Encryption** | SQL Server configuration option requiring TLS for all client connections |
| **Security Group** | Cloud firewall rules controlling inbound/outbound traffic at the instance level |
| **Imperva SecureSphere** | Enterprise database firewall and activity monitoring platform |

---

## Review Questions

1. **Conceptual:** Explain why databases should not be placed in the DMZ network segment. Draw a simple network diagram showing the proper placement of web servers, application servers, and database servers in a three-tier architecture.

2. **Applied:** A PostgreSQL database has `ssl = on` in its configuration. A developer connects using `sslmode=require`. Is this connection protected against a man-in-the-middle attack? Explain why or why not, and describe what configuration change would provide full protection.

3. **Scenario:** You are reviewing the AWS architecture for a new SaaS application. The RDS PostgreSQL instance has a security group rule: `0.0.0.0/0` (all traffic) on port 5432. What is the immediate risk, and what specific changes would you make to the security group to reduce exposure?

4. **Applied:** Write an `nmap` command to scan the 10.10.0.0/24 subnet for all common database ports and perform version detection on any open ports found.

5. **Conceptual:** What is the difference between a database firewall (like Imperva SecureSphere) and a traditional network firewall? What security capabilities does a database firewall provide that a traditional firewall cannot?

6. **Analysis:** Compare the security implications of an application storing database credentials in: (a) a hardcoded string in the source code, (b) an environment variable on the application server, and (c) AWS Secrets Manager with automatic rotation. Rank these from least to most secure and explain your reasoning.

7. **Applied:** Describe how SSH port forwarding can be used to securely access a PostgreSQL database on an internal server from a remote workstation. Write the specific SSH command. What audit trail does this approach create?

8. **Conceptual:** Oracle's CVE-2012-1675 (TNS Listener Poisoning) allowed attackers to redirect clients to rogue servers. Explain the mechanism of this attack and the Oracle configuration changes that mitigate it.

9. **Applied:** A development team uses the following Python code to connect to their database: `conn = psycopg2.connect("host=db.prod user=admin password=admin123 sslmode=disable")`. Identify all security problems with this connection string and rewrite it using security best practices.

10. **Conceptual:** Explain the Zero Trust principle of "assume breach" in the context of database network security. What monitoring and access controls would you implement to align with this principle for a database environment?

---

## Further Reading

- Imperva. *Database Security Fundamentals*. https://www.imperva.com/learn/data-security/database-security/
- PostgreSQL Global Development Group. *Secure TCP/IP Connections with SSL*. https://www.postgresql.org/docs/current/ssl-tcp.html
- Oracle Corporation. *Oracle Database Net Services Administrator's Guide — Security*. Oracle Documentation Library.
- National Institute of Standards and Technology. *NIST SP 800-41: Guidelines on Firewalls and Firewall Policy*. https://csrc.nist.gov/publications/detail/sp/800-41/rev-1/final
- Shodan Research. *Exposed Databases — A Survey of Internet-Facing Database Services*. https://www.shodan.io/report/databases
