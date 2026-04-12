---
title: "Database Authentication — Mechanisms and Hardening"
chapter: 4
week: 4
course: SCIA-340
---

# Chapter 4: Database Authentication — Mechanisms and Hardening

## Authentication Fundamentals in Database Contexts

Authentication answers the fundamental question: **who is connecting to this database?** Before the database engine enforces any access controls, it must verify the identity of the connecting principal. Authentication failures — weak passwords, default credentials, misconfigured trust relationships — are among the most common root causes of database breaches. A database with perfect access controls is completely undermined if those access controls can be bypassed by authenticating as an administrative account with a default or guessable password.

Database authentication differs from web application authentication in several important ways. Database connections are typically long-lived, stateful sessions rather than stateless HTTP requests. Database clients range from human administrators using interactive tools like SQL*Plus or pgAdmin, to application servers maintaining persistent connection pools with hundreds of simultaneous connections, to automated scripts performing scheduled jobs. Each connection type has different authentication requirements and security considerations.

The authentication process involves three components: **identification** (the user presents an identity claim, such as a username), **authentication** (the user proves that claim through credentials), and **authorization** (the system determines what the authenticated identity is permitted to do). This chapter focuses on the authentication step — authorization is covered in Chapter 5.

## OS Authentication vs. Database Authentication

### Operating System Authentication

OS authentication (called "external authentication" in some RDBMS documentation) delegates identity verification to the host operating system. When a user is logged into the OS under a particular account, the database trusts that the OS has already verified their identity and allows connection without additional database credentials.

**Oracle OS authentication** works through the `IDENTIFIED EXTERNALLY` clause. An Oracle user created with this clause can connect using the slash (`/`) syntax without supplying a password: `sqlplus /`. Oracle trusts the OS username and maps it to the Oracle user account. This is convenient for DBA scripts and scheduled jobs on the database server itself but is inappropriate for network connections because it requires OS access.

**PostgreSQL peer authentication** (`peer` method in `pg_hba.conf`) operates similarly for local connections — the database trusts the OS user identity for socket connections. A user logged in as `postgres` on the OS can connect to the database as the `postgres` role without a password via the Unix domain socket.

**SQL Server Windows Authentication** is the most sophisticated implementation of OS authentication among major RDBMS products, using Kerberos (in domain environments) or NTLM for identity verification. Windows Authentication is strongly preferred over SQL Server Authentication because passwords are managed by Active Directory policy, authentication is handled by the OS/Kerberos infrastructure, and sessions can be audited with full user identity throughout the enterprise.

**Advantages of OS authentication**: No additional password to manage, integrates with enterprise identity management, reduces credential sprawl, benefits from OS-level lockout and password policies.

**Disadvantages of OS authentication**: Ties database identity to OS identity — OS compromise means database compromise. Network database authentication typically requires additional protocol support (Kerberos). Less granular than database-native authentication.

### Database-Native Authentication

Database-native authentication requires users to supply credentials (typically username/password) that are verified against the database's own security catalog. This is the most common authentication mode for application service accounts and remote connections.

## Password-Based Authentication Deep Dive

### Default Credentials — The #1 Database Vulnerability

Default credentials are the single most commonly exploited database vulnerability in both external attacks and penetration tests. Every major RDBMS ships with predefined accounts, and many organizations fail to change their passwords or disable unnecessary accounts before deploying databases to production.

| RDBMS | Default Accounts | Default Password |
|-------|-----------------|-----------------|
| Oracle | SYS | `change_on_install` |
| Oracle | SYSTEM | `manager` |
| Oracle | SCOTT | `tiger` |
| Oracle | DBSNMP | `dbsnmp` |
| SQL Server | SA | (blank in some versions) |
| MySQL | root@localhost | (blank in some versions) |
| MySQL | root@'%' | (blank — remote access enabled) |
| PostgreSQL | postgres | (set during install, often blank) |

> **⚠ Warning**: Automated scanning tools routinely probe database listener ports for default credentials. Databases deployed with default accounts and passwords will typically be compromised within hours on a public network. Changing or disabling default credentials must be the first hardening step on any new database deployment.

### How Databases Store Passwords

Understanding how RDBMS products hash and store passwords informs both hardening decisions and incident response (when a database's security catalog is accessed, what does the attacker actually get?).

**MySQL Evolution**: MySQL's original `mysql_old_password` used a weak, proprietary 16-byte hash that was trivially reversible with lookup tables. MySQL 4.1 introduced `mysql_native_password` using SHA-1, which was still not salted individually. MySQL 8.0 introduced `caching_sha2_password` as the default — it uses SHA-256 with per-user salts and is significantly more resistant to offline cracking. Any MySQL installation should be verified to use `caching_sha2_password` and not the legacy plugin.

```sql
-- MySQL: Check which authentication plugin each user is using
SELECT user, host, plugin FROM mysql.user;

-- Force a user to the modern auth plugin
ALTER USER 'appuser'@'%' IDENTIFIED WITH caching_sha2_password BY 'new_secure_password';
```

**SQL Server**: Uses PWDENCRYPT/PWDCOMPARE for password storage, implementing SHA-512 with salt. SQL Server's password hashing is generally considered adequate, though the SA account and its password remain critical to protect.

**PostgreSQL**: Supports MD5 (legacy, should not be used — MD5 hashed passwords with username as salt are weak) and `scram-sha-256` (recommended). SCRAM-SHA-256 implements the Salted Challenge Response Authentication Mechanism, providing mutual authentication (the client verifies the server's identity as well as the server verifying the client's password) and is resistant to offline dictionary attacks.

```
# PostgreSQL: Enforce scram-sha-256 globally
# In postgresql.conf:
password_encryption = scram-sha-256

# In pg_hba.conf, require scram-sha-256 (not md5) for all connections:
host    all    all    0.0.0.0/0    scram-sha-256
```

### Password Policies and Account Lockout

All production databases should enforce password complexity and rotation policies. Most enterprise RDBMS products support configuring these policies natively or through profiles.

```sql
-- Oracle: Creating a password profile with complexity and lockout requirements
CREATE PROFILE app_profile LIMIT
    FAILED_LOGIN_ATTEMPTS    5
    PASSWORD_LOCK_TIME       1/24  -- 1 hour
    PASSWORD_LIFE_TIME       90
    PASSWORD_REUSE_TIME      365
    PASSWORD_REUSE_MAX       10
    PASSWORD_VERIFY_FUNCTION ora12c_strong_pwd_verify_function;

-- Assign the profile to a user
ALTER USER app_user PROFILE app_profile;
```

```sql
-- SQL Server: Configure login policy (uses Windows Password Policy if enabled)
ALTER LOGIN app_user WITH
    CHECK_POLICY = ON,
    CHECK_EXPIRATION = ON;
```

## Certificate-Based Authentication

Certificate-based authentication uses X.509 digital certificates to verify identity, providing stronger security than passwords because private keys cannot be guessed or phished — they must be physically compromised.

**PostgreSQL certificate authentication** (`cert` method in `pg_hba.conf`) requires the client to present an X.509 certificate signed by a CA that the server trusts. The database username is matched against the certificate's CN (Common Name) or mapped through a `pg_ident.conf` mapping:

```
# pg_hba.conf - require certificate for DBA access
hostssl  all  dba_user  10.0.2.0/24  cert  clientcert=verify-full
```

For this to work, the server must be configured with TLS using a trusted CA certificate, and the client must present a certificate signed by that CA. The private key never leaves the client system, making credential theft significantly harder than password theft.

**MySQL SSL/X.509** authentication can be configured to require a valid client certificate. The `REQUIRE X509` clause on a MySQL user account enforces certificate authentication for that account:

```sql
-- MySQL: Require client certificate for a database account
CREATE USER 'secure_app'@'%' IDENTIFIED BY 'password'
REQUIRE SUBJECT '/CN=secure_app/O=MyOrg'
AND ISSUER '/CN=MyCA/O=MyOrg';
```

**SQL Server certificate authentication** is used primarily for server-to-server authentication (linked servers, database mirroring, availability group endpoints) rather than client authentication, where Windows Authentication (Kerberos) is preferred.

## Kerberos Authentication for Databases

Kerberos is a network authentication protocol that uses symmetric key cryptography to provide mutual authentication without transmitting passwords over the network. In enterprise environments with Active Directory, Kerberos authentication for databases provides single sign-on, strong authentication, and centralized audit trails.

**SQL Server Windows Authentication** is the most seamless implementation. When a Windows domain user connects to SQL Server using a domain account, the SQL Server driver automatically obtains a Kerberos ticket from the domain controller and presents it to SQL Server. No password prompt appears, and the password is never transmitted. The SQL Server service must have a properly configured Service Principal Name (SPN) registered in Active Directory for Kerberos to succeed; without a correct SPN, Windows Authentication falls back to NTLM, which is weaker.

**Oracle Kerberos** integration uses the Kerberos authentication adapter, configured through `sqlnet.ora`. Oracle users are created as externally identified via Kerberos:

```sql
-- Oracle: Create user authenticated via Kerberos
CREATE USER scott IDENTIFIED EXTERNALLY AS 'scott@EXAMPLE.COM';
```

**PostgreSQL Kerberos/GSSAPI** authentication is configured in `pg_hba.conf` using the `gss` method. It requires an appropriate Kerberos keytab on the server and properly configured SPN entries.

## LDAP and Active Directory Integration

LDAP (Lightweight Directory Access Protocol) integration allows databases to authenticate users against a central directory — typically Microsoft Active Directory or OpenLDAP — rather than maintaining a local password database. This centralizes identity management: password policies, account lockouts, and account provisioning are all managed in the directory.

```
# PostgreSQL LDAP authentication in pg_hba.conf
host    all    all    0.0.0.0/0    ldap 
  ldapserver=dc.example.com
  ldapbasedn="ou=dbusers,dc=example,dc=com"
  ldapbinddn="cn=pg_ldap_bind,ou=service,dc=example,dc=com"
  ldapbindpasswd="bind_password"
  ldapsearchattribute=sAMAccountName
```

> **⚠ Warning**: LDAP bind passwords in database configuration files must be protected carefully. If the configuration file is readable by unauthorized users or stored in a version control system, the LDAP bind credential — which may have broad directory read access — is exposed.

## Multi-Factor Authentication for Privileged Access

Standard username/password authentication for DBA accounts is insufficient for high-privilege access to sensitive databases. Multi-factor authentication (MFA) adds a second verification factor — typically a time-based one-time password (TOTP), push notification, or hardware token — that must be presented in addition to the password.

**Privileged Access Management (PAM) solutions** such as CyberArk Privileged Access Security, BeyondTrust Password Safe, and Delinea (formerly Thycotic) Secret Server provide MFA for database access as part of a broader privileged access management platform. These solutions typically:

- Require MFA before granting DBA access to database management tools
- Store DBA credentials in an encrypted vault and inject them at connection time (so the DBA never knows the actual password)
- Record full session video of DBA sessions for post-incident forensic review
- Automatically rotate credentials after each use or on a schedule

For databases that support it natively, PostgreSQL's PAM authentication module integrates with Linux-PAM, enabling the use of PAM modules (including Google Authenticator PAM module) for MFA:

```
# pg_hba.conf using PAM (with PAM configured to enforce MFA)
host    all    all    0.0.0.0/0    pam pamservice=postgresql
```

## Service Accounts and Secrets Management

Application-to-database authentication presents unique challenges. Unlike human users who can type a password, applications must store credentials somewhere accessible at runtime. Poor secrets management is one of the most common real-world database security failures.

### The Problem with Connection Strings

The traditional approach of embedding database credentials in configuration files or — even worse — in application source code creates severe risks:

```
# INSECURE - credentials in plaintext config file
DATABASE_URL=postgresql://app_user:SuperSecret123@db.internal:5432/myapp

# CATASTROPHICALLY INSECURE - credentials in source code
connection = psycopg2.connect(
    host="db.internal", database="myapp",
    user="app_user", password="SuperSecret123"
)
```

If this source code is committed to a Git repository — even a private one — the credentials are exposed to everyone with repository access and persist in commit history forever. Security researcher Brian Krebs and others have documented numerous incidents where credentials were found in public GitHub repositories.

### Secrets Management Solutions

**HashiCorp Vault** is the leading open-source secrets management solution. Vault can generate short-lived, dynamic database credentials: rather than the application having a static username/password, it requests credentials from Vault at startup. Vault creates a database user with a time-limited lease, the application uses those credentials, and Vault automatically revokes them when the lease expires. Even if credentials are captured, they are useless within minutes to hours.

```bash
# Example: Vault dynamic secrets — application requests temporary DB credentials
vault read database/creds/readonly-role
# Returns:
# lease_id: database/creds/readonly-role/abc123
# lease_duration: 1h
# username: v-app-readonly-xyz789
# password: A1b2-C3d4-E5f6-G7h8
```

**AWS Secrets Manager** stores and automatically rotates secrets for AWS RDS, Aurora, and Redshift databases. Lambda rotation functions update the database password and store the new secret, eliminating the need for manual rotation.

**Azure Key Vault** provides similar functionality for Azure SQL Database and other Azure services, with managed identities allowing applications to authenticate to Key Vault without any stored credentials.

## Connection Pooling and Authentication

Connection poolers such as **PgBouncer** (PostgreSQL) and **ProxySQL** (MySQL) sit between application servers and the database, maintaining a pool of persistent database connections and multiplexing client requests over them. This dramatically reduces connection overhead but creates authentication complications.

PgBouncer can operate in three pooling modes: session pooling (one pool connection per client session), transaction pooling (pool connection is held only for the duration of a transaction), and statement pooling (pool connection released after each statement). In session pooling mode, each client authenticates individually against the database. In transaction and statement pooling modes, PgBouncer authenticates to the database using a single service account, and client authentication is handled by PgBouncer itself using its local `userlist.txt` or `auth_query` configuration.

> **⚠ Warning**: When a connection pooler handles authentication, audit logs on the database server show only the pooler's service account as the connecting user, not the actual end user. This breaks per-user audit trails. Consider using `application_name` connection parameters or SET statements to propagate user identity into database session context for auditing purposes.

## Hardening Default Accounts

Removing or disabling default database accounts is a foundational hardening step that must be completed before a database is placed in production.

### Oracle
```sql
-- Check status of all accounts
SELECT username, account_status FROM dba_users ORDER BY account_status;

-- Lock and expire unnecessary default accounts
ALTER USER SCOTT ACCOUNT LOCK PASSWORD EXPIRE;
ALTER USER ANONYMOUS ACCOUNT LOCK PASSWORD EXPIRE;
ALTER USER OUTLN ACCOUNT LOCK PASSWORD EXPIRE;
-- Change SYS and SYSTEM passwords immediately
ALTER USER SYS IDENTIFIED BY "StrongNewPassword1!";
ALTER USER SYSTEM IDENTIFIED BY "StrongNewPassword2!";
```

### MySQL
```sql
-- Remove anonymous accounts (MySQL 5.x legacy)
DROP USER ''@'localhost';
DROP USER ''@'%';

-- Remove remote root access (root should only be localhost)
DROP USER 'root'@'%';

-- Verify remaining root access
SELECT user, host FROM mysql.user WHERE user='root';
-- Should only show root@localhost
```

### SQL Server
```sql
-- Disable the SA account (use Windows Authentication instead)
ALTER LOGIN [sa] DISABLE;

-- Rename SA to make it harder to target (security through obscurity, 
-- but defense-in-depth)
ALTER LOGIN [sa] WITH NAME = [disabled_sa];

-- Review all SQL Server logins
SELECT name, is_disabled, create_date FROM sys.server_principals
WHERE type_desc = 'SQL_LOGIN' ORDER BY create_date;
```

---

## Key Terms

| Term | Definition |
|------|------------|
| **Authentication** | The process of verifying the claimed identity of a connecting principal |
| **OS Authentication** | Database authentication delegated to the operating system's identity verification |
| **Database-Native Authentication** | Authentication using credentials stored in the database's own security catalog |
| **Default Credentials** | Pre-configured usernames and passwords shipped with RDBMS products |
| **Password Hashing** | One-way transformation of passwords into stored hash values that cannot be reversed to plaintext |
| **SCRAM-SHA-256** | Salted Challenge Response Authentication Mechanism using SHA-256; PostgreSQL's recommended auth protocol |
| **caching_sha2_password** | MySQL 8.0's default authentication plugin using SHA-256 |
| **Kerberos** | Network authentication protocol using symmetric key cryptography and ticket-granting infrastructure |
| **Service Principal Name (SPN)** | Active Directory identifier for a service, required for Kerberos authentication |
| **LDAP** | Lightweight Directory Access Protocol — protocol for accessing directory services like Active Directory |
| **Multi-Factor Authentication (MFA)** | Authentication requiring two or more independent verification factors |
| **Privileged Access Management (PAM)** | Tools and processes for controlling, monitoring, and auditing high-privilege account access |
| **Connection Pool** | A cache of reusable database connections maintained by a pooler (PgBouncer, ProxySQL) |
| **HashiCorp Vault** | Open-source secrets management platform supporting dynamic database credential generation |
| **Dynamic Credentials** | Short-lived database credentials generated on-demand and automatically revoked after a lease period |
| **Certificate-Based Auth** | Authentication using X.509 digital certificates and public key cryptography |
| **pg_hba.conf** | PostgreSQL's host-based authentication configuration file |
| **SA Account** | SQL Server's built-in System Administrator login — should be disabled in production |
| **Mutual TLS (mTLS)** | TLS configuration where both client and server present certificates for mutual authentication |
| **Secrets Management** | Secure storage, access, and rotation of credentials and other sensitive configuration values |

---

## Review Questions

1. **Conceptual**: Explain why SQL Server Windows Authentication (Kerberos) is considered more secure than SQL Server Authentication (native username/password). What specific attack scenarios does Kerberos mitigate that native authentication does not?

2. **Applied**: Audit a MySQL 8.0 database for authentication security issues. Write the SQL queries you would use to identify: (a) accounts using the legacy `mysql_native_password` plugin, (b) accounts with no password, (c) accounts accessible from any host (`'%'`). What remediation steps would you take for each finding?

3. **Conceptual**: A developer proposes storing the database password in a `.env` file at the project root, which is listed in `.gitignore`. Evaluate this approach — what risks remain, and what would you recommend instead?

4. **Applied**: Design a secrets management architecture for a web application that connects to a PostgreSQL database, using HashiCorp Vault for dynamic credentials. Describe how the application obtains credentials at startup, how credential rotation works, and what happens when the lease expires while the application is running.

5. **Conceptual**: Explain how PgBouncer in transaction pooling mode affects database-level audit logging. What compensating controls can restore per-user audit trail visibility when a connection pooler is in use?

6. **Applied**: Write the PostgreSQL `pg_hba.conf` entries and `postgresql.conf` settings required to: (a) enforce SCRAM-SHA-256 authentication for all remote connections, (b) allow local `postgres` OS user to connect via peer authentication, (c) require client certificates for a `dba_user` account connecting from a specific subnet.

7. **Conceptual**: What is a Privileged Access Management (PAM) solution, and what capabilities does it provide beyond simple MFA? Why is PAM considered essential for DBA account management in regulated industries?

8. **Applied**: Using Oracle's profile system, design and create a profile for application service accounts that enforces: a 90-day password lifetime, lockout after 3 failed attempts with a 30-minute unlock delay, password history preventing reuse of the last 12 passwords. Write the SQL and explain each parameter.

9. **Conceptual**: Compare the security properties of `caching_sha2_password` (MySQL) and `scram-sha-256` (PostgreSQL). What does SCRAM provide that a simple hashed-password comparison does not? Why does mutual authentication matter?

10. **Applied**: You are hardening a newly installed Oracle 19c database. List all the default Oracle accounts you would lock and expire, the ones you would leave active but with changed passwords, and explain your reasoning for each decision.

---

## Further Reading

- **HashiCorp. (2024). *Vault Database Secrets Engine Documentation*.** Covers dynamic credential generation, lease management, and rotation for PostgreSQL, MySQL, Oracle, and SQL Server. Available at developer.hashicorp.com/vault.

- **Microsoft. (2024). *Kerberos Authentication Overview for SQL Server*.** Technical deep-dive into SPN configuration, Kerberos ticket flow, and troubleshooting Windows Authentication. Available at docs.microsoft.com.

- **Bellovin, S. M., & Merritt, M. (1994). "Encrypted Key Exchange: Password-based protocols secure against dictionary attacks." *Proceedings of the IEEE Symposium on Research in Security and Privacy*.** Foundational academic paper that informs the SCRAM authentication mechanism used in PostgreSQL.

- **CyberArk. (2023). *Privileged Access Management for Database Security*.** Whitepaper covering DBA session recording, credential vaulting, and just-in-time privileged access for database environments. Available at cyberark.com.

- **National Institute of Standards and Technology. (2020). *NIST Special Publication 800-63B: Digital Identity Guidelines — Authentication and Lifecycle Management*.** The authoritative U.S. government guidance on authentication assurance levels, password requirements, and MFA. Available at pages.nist.gov/800-63-3.
