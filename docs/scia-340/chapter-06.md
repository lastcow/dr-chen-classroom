---
title: "Database Encryption — Protecting Data at Rest"
week: 6
chapter: 6
course: SCIA-340
---

# Chapter 6: Database Encryption — Protecting Data at Rest

## Introduction

Encryption has long been the cornerstone of data confidentiality, but its application to databases introduces unique architectural challenges that go far beyond simply "turning it on." Data at rest — data sitting in data files, tablespaces, backups, and transaction logs — represents a significant and often underestimated risk. Breaches involving stolen backup tapes, decommissioned hard drives resold without proper sanitization, and physical intrusion into data centers demonstrate that perimeter and network-level defenses alone are insufficient. When a drive leaves a data center without proper encryption, every record on it is readable by anyone with basic forensic tools. This chapter explores the encryption architectures, tools, algorithms, and operational practices that protect database data at rest.

---

## 6.1 Why Encryption at Rest Matters

The threat model for data at rest is distinct from network-based attacks. Consider three concrete scenarios:

**Stolen or lost backup media.** Organizations routinely ship backup tapes and drives offsite for disaster recovery. If those tapes are unencrypted, a thief who intercepts a delivery truck walks away with a complete copy of your database. High-profile incidents — including breaches at healthcare organizations and financial institutions — have originated from exactly this vector.

**Decommissioned hardware.** Enterprise-grade storage and servers are routinely resold or donated. Even after a standard format, data can be recovered using readily available tools. Regulatory fines have been issued to healthcare organizations whose decommissioned servers were resold with patient data intact.

**Physical access attacks.** Insiders, cleaning staff, or contractors with physical access to a server room can attach a bootable USB drive and copy raw data files. Without file-level or disk-level encryption, the database engine's access controls are irrelevant — the attacker bypasses the DBMS entirely and reads the raw pages.

> **Key Concept:** Encryption at rest protects data from threats that bypass the database engine itself — theft of physical storage media, direct filesystem access, and backup interception. It does *not* protect data from authorized or unauthorized queries once the database is running.

These scenarios share a common thread: the attacker never touches a running, authenticated database session. They operate at the filesystem or physical layer. Encryption at rest is the primary control for this threat category.

---

## 6.2 Transparent Data Encryption (TDE)

Transparent Data Encryption (TDE) is the most widely deployed database encryption technology for protecting data at rest. The term "transparent" means that applications see no difference — queries and transactions work exactly as before, and the encryption and decryption happen automatically within the database engine.

### 6.2.1 How TDE Works

TDE encrypts data pages as they are written to disk and decrypts them as they are read into the buffer pool (in-memory cache). Crucially, data in the buffer pool is *unencrypted*; TDE protects only what is on disk. This is the core trade-off of TDE: it is straightforward to deploy and has minimal application impact, but an attacker who can query the running database or access memory dumps still sees plaintext.

The encryption operates at the page or file level. In SQL Server, for example, the 8 KB data pages are encrypted before being written to .mdf and .ldf files. In Oracle, encryption happens at the block level within tablespaces. The database engine handles the keys transparently during normal operation.

### 6.2.2 The TDE Key Hierarchy

TDE uses a layered key hierarchy to enable secure key management:

| Layer | Name | Description |
|---|---|---|
| 1 | Master Key / Master Encryption Key (MEK) | Top-level key, typically stored in an HSM or key vault |
| 2 | Database Encryption Key (DEK) | Per-database key, encrypted by the MEK |
| 3 | Data Pages / Tablespace | Encrypted by the DEK |

This hierarchy matters because it allows **key rotation without re-encrypting all data**. To rotate the MEK, you decrypt and re-encrypt the DEK with the new MEK — a fast operation. Only a full DEK rotation requires re-encrypting all data pages.

### 6.2.3 TDE in Major Database Platforms

**SQL Server TDE:**
```sql
-- Step 1: Create a master key in the master database
USE master;
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'S3cur3P@ss!2024';

-- Step 2: Create a certificate to protect the DEK
CREATE CERTIFICATE TDECert WITH SUBJECT = 'TDE Certificate';

-- Step 3: Create the Database Encryption Key in the target database
USE SensitiveDB;
CREATE DATABASE ENCRYPTION KEY
  WITH ALGORITHM = AES_256
  ENCRYPTION BY SERVER CERTIFICATE TDECert;

-- Step 4: Enable encryption
ALTER DATABASE SensitiveDB SET ENCRYPTION ON;
```

After this, all data files including the transaction log are encrypted. Crucially, you must back up the certificate and private key to a secure, separate location — losing them means losing your data.

**Oracle TDE** (Oracle Advanced Security, 12c+):
```sql
-- Configure wallet location in sqlnet.ora, then:
ADMINISTER KEY MANAGEMENT SET KEYSTORE OPEN
  IDENTIFIED BY wallet_password;

ADMINISTER KEY MANAGEMENT SET KEY
  IDENTIFIED BY wallet_password WITH BACKUP;

-- Encrypt a tablespace
ALTER TABLESPACE users ENCRYPTION USING AES256 ENCRYPT;
```

Oracle supports both tablespace-level and column-level TDE, offering granularity SQL Server's TDE lacks natively.

**MySQL InnoDB TDE** (MySQL 5.7.11+):
```ini
# In my.cnf
[mysqld]
early-plugin-load=keyring_file.so
keyring_file_data=/var/lib/mysql-keyring/keyring
```
```sql
CREATE TABLE sensitive_data (id INT, ssn VARCHAR(11))
  ENCRYPTION='Y';
```

**PostgreSQL** does not include native TDE as of PostgreSQL 16, though it is under active development. The common approach is to use filesystem-level encryption (dm-crypt/LUKS on Linux) or the `pgcrypto` extension for column-level encryption (covered in Section 6.4).

---

## 6.3 Key Management: HSMs, Key Vaults, and EKM

The security of TDE is entirely dependent on protecting the master encryption key. Storing the MEK in the same system it protects — or in a flat file on the same server — provides weak protection. A best practice is to use dedicated key management infrastructure.

**Hardware Security Modules (HSMs)** are tamper-resistant physical devices designed specifically for cryptographic key storage and operations. The private key never leaves the HSM in plaintext; the HSM performs encryption/decryption operations internally. AWS CloudHSM, Thales Luna, and nCipher nShield are common enterprise HSMs.

**Oracle Key Vault (OKV)** is Oracle's centralized key management appliance. It manages TDE wallets across multiple Oracle databases, enabling centralized key rotation, access control to keys, and audit trails for key operations.

**SQL Server Extensible Key Management (EKM)** allows SQL Server to integrate with external key management providers, including HSMs. Rather than managing the master key internally, the HSM holds it, and SQL Server calls the EKM provider's API for cryptographic operations.

> **⚠️ Anti-Pattern Warning:** Never store encryption keys in the same database they encrypt. This is analogous to locking your house key inside the house. A common mistake is creating the SQL Server master key with a simple password stored in a nearby config file — both are then accessible to any attacker who compromises the server.

---

## 6.4 Column-Level Encryption (CLE)

While TDE encrypts entire data files, Column-Level Encryption (CLE) targets specific sensitive columns — Social Security Numbers, credit card numbers, medical record identifiers, passwords — while leaving other data unencrypted. This provides surgical protection but introduces significant complexity.

**SQL Server CLE** uses symmetric keys protected by the master key:
```sql
-- Open the symmetric key
OPEN SYMMETRIC KEY SSN_Key DECRYPTION BY CERTIFICATE DataProtectCert;

-- Insert encrypted data
INSERT INTO Patients (Name, SSN_Encrypted)
VALUES ('Jane Doe', EncryptByKey(Key_GUID('SSN_Key'), '123-45-6789'));

-- Decrypt for authorized users
SELECT Name,
       CONVERT(VARCHAR, DecryptByKey(SSN_Encrypted)) AS SSN
FROM Patients;

CLOSE SYMMETRIC KEY SSN_Key;
```

**PostgreSQL with pgcrypto:**
```sql
-- Enable the extension
CREATE EXTENSION pgcrypto;

-- Encrypt with PGP symmetric encryption
INSERT INTO patients (name, ssn_encrypted)
VALUES ('Jane Doe',
        pgp_sym_encrypt('123-45-6789', 'encryption_passphrase'));

-- Decrypt
SELECT name,
       pgp_sym_decrypt(ssn_encrypted::bytea, 'encryption_passphrase') AS ssn
FROM patients;
```

### 6.4.1 TDE vs. Column-Level vs. Application-Level Encryption

| Feature | TDE | Column-Level | Application-Level |
|---|---|---|---|
| Scope | Entire database/tablespace | Specific columns | Data before it reaches DB |
| Complexity | Low | Medium | High |
| Performance impact | Low–Medium | Medium–High | Varies |
| Protects from DB admin? | No | Partially | Yes (if keys managed externally) |
| Searchability | Full | Deterministic only | Deterministic only |
| Key management | DB engine | DB engine or external | Application |

---

## 6.5 SQL Server Always Encrypted

SQL Server's **Always Encrypted** feature represents a different paradigm: the database server *never* sees plaintext. Encryption and decryption happen entirely in the client driver, using keys that the server does not possess. Even a compromised DBA account or database administrator cannot read protected columns.

Always Encrypted supports two encryption types:

- **Deterministic encryption**: The same plaintext always produces the same ciphertext. Supports equality comparisons and joins, but leaks information about value frequency.
- **Randomized encryption**: Uses a random IV, so the same plaintext produces different ciphertext each time. Provides stronger confidentiality but prevents equality searches, joins, or grouping on the column.

The column encryption key (CEK) is encrypted by a column master key (CMK) stored outside SQL Server — typically in Windows Certificate Store, Azure Key Vault, or an HSM. The client application holds the CMK and performs all cryptographic operations locally before sending data to the server.

---

## 6.6 Encrypting Database Backups

A database with TDE enabled does not automatically produce encrypted backups — this depends on platform and configuration. SQL Server backups of a TDE-protected database are automatically encrypted because the backup contains the encrypted data pages. However, the backup file is useless without the certificate and private key used to create the DEK. This makes certificate backup and escrow a critical operational process.

PostgreSQL and MySQL backups are typically plain SQL dumps or binary copies. These require explicit encryption:

```bash
# Encrypted PostgreSQL backup using GPG
pg_dump mydb | gpg --encrypt --recipient backup-key@example.com > mydb.sql.gpg

# Encrypted MySQL backup
mysqldump --all-databases | openssl enc -aes-256-cbc -pbkdf2 \
  -pass file:/secure/backup.key > all_databases.sql.enc
```

> **⚠️ Critical Risk:** Unencrypted database backups are frequently the path of least resistance for attackers. Organizations that implement TDE on production databases often fail to encrypt backup media, negating the protection entirely.

---

## 6.7 Data Masking vs. Encryption vs. Tokenization

These three techniques serve related but distinct purposes:

**Encryption** transforms data using a reversible algorithm and a key. The original data can be recovered with the correct key. Used for data that must be stored and later retrieved in its original form.

**Data Masking** replaces sensitive data with realistic but fake data. *Static data masking* creates a sanitized copy of a database for use in development/test environments. *Dynamic data masking (DDM)* in SQL Server and Oracle presents masked data to unauthorized users while returning real data to authorized users — without modifying the stored data.

```sql
-- SQL Server Dynamic Data Masking
CREATE TABLE Customers (
    ID INT,
    Email VARCHAR(100) MASKED WITH (FUNCTION = 'email()'),
    SSN VARCHAR(11) MASKED WITH (FUNCTION = 'partial(0,"XXX-XX-",4)'),
    CreditCard VARCHAR(16) MASKED WITH (FUNCTION = 'partial(0,"XXXX-XXXX-XXXX-",4)')
);
```

**Tokenization** replaces sensitive data with a non-sensitive placeholder (token) that has no mathematical relationship to the original value. A separate token vault maps tokens to real values. Tokenization is widely used for PCI DSS compliance — the card number is replaced with a token throughout the application, and only the token vault (which may be operated by a third-party payment processor) holds the real PAN.

---

## 6.8 Performance Impact and Hardware Acceleration

Modern x86-64 processors include the **AES-NI** (Advanced Encryption Standard New Instructions) instruction set extension, which performs AES operations in hardware at speeds that make the performance cost of TDE negligible for most workloads. Benchmarks on AES-NI–capable hardware typically show 1–5% throughput reduction with AES-256 TDE enabled, a cost that is acceptable for the security benefit.

Workloads that are heavily I/O bound and do not benefit from AES-NI may see 10–15% overhead, but this is increasingly rare on modern hardware. Column-level encryption has higher overhead because it occurs per-value rather than per-page and may prevent index use on encrypted columns.

---

## 6.9 Key Rotation

Key rotation is the practice of periodically replacing encryption keys. Rotation limits the exposure window if a key is compromised. In a TDE context:

1. Generate a new DEK or MEK.
2. Re-encrypt the DEK with the new MEK (fast — does not require re-encrypting data).
3. For full DEK rotation, the database engine re-encrypts all data pages in the background — this can take hours on large databases.
4. Revoke and archive the old key according to retention policy.

Automate rotation schedules and test the rotation process in staging before applying to production. Key rotation that has never been tested is key rotation that will fail when it matters most.

---

## Key Terms

| Term | Definition |
|---|---|
| **Transparent Data Encryption (TDE)** | Encryption of database files at the storage layer, transparent to applications |
| **Database Encryption Key (DEK)** | The symmetric key used to encrypt data pages in TDE |
| **Master Encryption Key (MEK)** | The top-level key that protects the DEK in the TDE hierarchy |
| **Hardware Security Module (HSM)** | Tamper-resistant hardware device for cryptographic key storage and operations |
| **Column-Level Encryption (CLE)** | Encrypting specific columns rather than entire data files |
| **Always Encrypted** | SQL Server feature where encryption/decryption occurs only on the client |
| **Deterministic Encryption** | Encryption where identical plaintext always produces identical ciphertext |
| **Randomized Encryption** | Encryption using a random IV so identical plaintexts produce different ciphertexts |
| **AES-256** | Advanced Encryption Standard with 256-bit key; the recommended standard for database encryption |
| **AES-NI** | CPU instruction set extension enabling hardware-accelerated AES operations |
| **pgcrypto** | PostgreSQL extension providing cryptographic functions including column encryption |
| **Oracle Key Vault (OKV)** | Oracle's centralized key management solution |
| **Extensible Key Management (EKM)** | SQL Server framework for integrating external key management providers |
| **Static Data Masking** | Creating a sanitized copy of a database by replacing sensitive data with fake data |
| **Dynamic Data Masking (DDM)** | Presenting masked data to unauthorized users without modifying stored data |
| **Tokenization** | Replacing sensitive data with non-sensitive placeholders mapped in a separate vault |
| **Key Rotation** | Periodic replacement of encryption keys to limit exposure from key compromise |
| **Oracle Advanced Security** | Oracle's suite for TDE and network encryption |
| **PCI DSS** | Payment Card Industry Data Security Standard, requiring encryption of cardholder data |
| **WORM Storage** | Write Once Read Many — storage that prevents modification of written data |

---

## Review Questions

1. **Conceptual:** Explain the threat model that TDE addresses and the threat model it *does not* address. Why does encrypting data files not protect against a malicious DBA querying the running database?

2. **Applied:** A healthcare organization stores patient records in SQL Server. They have TDE enabled on the database. An attacker steals a backup tape. Describe what the attacker would need to successfully decrypt the data from the backup. What operational controls ensure these materials are unavailable to the attacker?

3. **Conceptual:** Compare and contrast deterministic and randomized encryption in the context of SQL Server Always Encrypted. Give a concrete example of a column for which each would be appropriate.

4. **Applied:** Write the SQL Server T-SQL commands to:
   a) Create a master key
   b) Create a certificate
   c) Create an AES-256 database encryption key
   d) Enable TDE on a database called `HospitalDB`

5. **Conceptual:** A developer proposes storing the TDE master key password in an environment variable on the same database server. Why is this an anti-pattern? What is the recommended alternative?

6. **Applied:** Using the `pgcrypto` extension, write a PostgreSQL query that inserts an encrypted credit card number into a `payment_methods` table and a separate query that retrieves and decrypts it.

7. **Analysis:** Compare TDE, column-level encryption, and application-level encryption across these dimensions: protection from a malicious DBA, searchability, complexity, and performance impact. Which approach would you recommend for a PCI DSS-compliant application and why?

8. **Conceptual:** What is the difference between data masking and encryption? A QA team needs a copy of the production customer database to test a new feature. Should they use masking or encryption? Explain your reasoning.

9. **Applied:** Describe the key rotation procedure for TDE in SQL Server. What is the difference between rotating the database encryption key vs. rotating the master key? Which operation is more disruptive and why?

10. **Scenario:** A company uses SQL Server with TDE and ships backup files to an offsite storage facility. A security auditor flags this as insufficient. What additional controls should be in place to protect those backup files, and what SQL Server or OS-level features could provide them?

---

## Further Reading

- Microsoft Documentation. *Transparent Data Encryption (TDE)*. https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/transparent-data-encryption
- Oracle Corporation. *Oracle Advanced Security Administrator's Guide*. Oracle Database Documentation Library.
- National Institute of Standards and Technology. *NIST SP 800-57: Recommendation for Key Management*. https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final
- PostgreSQL Global Development Group. *pgcrypto — Cryptographic Functions*. https://www.postgresql.org/docs/current/pgcrypto.html
- PCI Security Standards Council. *PCI DSS v4.0 — Requirement 3: Protect Stored Account Data*. https://www.pcisecuritystandards.org/
