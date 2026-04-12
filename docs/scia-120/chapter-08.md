---
title: "Chapter 8: Internet Security"
chapter: 8
week: 8
course: SCIA-120
description: "A comprehensive examination of internet security topics including web security, OWASP Top 10, browser security, email protocols, DNS security, privacy, IoT security, and secure online practices."
---

# Chapter 8: Internet Security

## Introduction

The internet was not designed with security in mind. Its foundational protocols — TCP/IP, HTTP, DNS, SMTP — were developed in an era when the network's user base was small, relatively trusted, and primarily academic. The explosive growth of the internet into a global infrastructure carrying financial transactions, medical records, political communications, and the private lives of billions of people has exposed the fundamental security limitations of this open architecture.

This chapter examines internet security from multiple angles: the vulnerabilities inherent in web applications and browsers, the protocols that protect (or fail to protect) web and email communication, the tools available for privacy and anonymity, the security challenges of the Internet of Things, and the practical habits that individuals and organizations can adopt to remain safer online. Many of the topics here build directly on the cryptography covered in Chapter 6 and the network security concepts in Chapter 7.

---

## 8.1 Internet Architecture and Security Implications

The internet is a network of networks: thousands of autonomous systems (AS) — ISPs, universities, corporations — interconnected through **BGP (Border Gateway Protocol)**, which routes traffic between them. This decentralized architecture provides resilience (no single point of failure) but creates security implications that are difficult to fully address.

**BGP hijacking**, for example, occurs when an AS maliciously or accidentally announces ownership of IP address blocks it doesn't control, attracting and potentially intercepting traffic destined for other networks. Notable incidents include Pakistan Telecom briefly hijacking YouTube's IP addresses in 2008 and, more seriously, nation-state-attributed BGP hijacking incidents targeting financial institutions. **RPKI (Resource Public Key Infrastructure)** provides cryptographic validation of BGP route announcements but is not yet universally deployed.

The distributed nature of the internet also means that any communication traverses many intermediate networks and systems — each a potential point of eavesdropping or interception. This is precisely why **end-to-end encryption** (such as TLS) is so critical: it ensures that only the communicating endpoints can read the content, even if every intermediate router and ISP can see the encrypted packets passing through.

---

## 8.2 Web Security Fundamentals

### HTTPS and TLS in Practice

**HTTPS (HTTP Secure)** is HTTP carried over a TLS connection. It provides three essential properties for web communication: **confidentiality** (the content of pages and form submissions cannot be read by eavesdroppers), **integrity** (the content cannot be modified in transit without detection), and **authentication** (the server's identity is verified through its certificate, confirming you are actually communicating with the intended site and not an impersonator).

The presence of a padlock icon in a browser's address bar indicates a valid TLS certificate, but it does *not* mean the site itself is trustworthy or not malicious — only that the connection to it is encrypted. Phishing sites routinely obtain valid TLS certificates for their fraudulent domains.

**HSTS (HTTP Strict Transport Security)** is a security header that instructs browsers to only connect to a domain over HTTPS, never falling back to plain HTTP, for a specified duration. This prevents SSL stripping attacks, in which an attacker downgrades a victim's HTTPS connection to HTTP. The HSTS preload list, maintained by browsers, contains domains that should always use HTTPS, even on the very first connection.

### OWASP Top 10

The **Open Web Application Security Project (OWASP)** publishes the **OWASP Top 10**, a periodically updated list of the most critical web application security risks. It is the de facto standard reference for web application security. The 2021 edition identifies:

**1. Broken Access Control**: Users acting outside of their intended permissions — accessing other users' data, elevating privileges, or bypassing authorization checks. This is the most prevalent web security failure, found in 94% of tested applications.

**2. Cryptographic Failures**: Previously called "Sensitive Data Exposure," this covers failures in cryptography that result in exposure of sensitive data — transmitting data in cleartext, using weak or deprecated cryptographic algorithms (MD5, SHA-1, DES), improper key management.

**3. Injection**: User-supplied data is sent to an interpreter (SQL, OS, LDAP, XPATH) as part of a command or query. **SQL injection** is the most common form: when user input is directly concatenated into a SQL query, an attacker can manipulate the query to dump, modify, or delete database content. Example of vulnerable code: `query = "SELECT * FROM users WHERE username = '" + username + "'"`. An attacker entering `' OR '1'='1` would make the query always true, returning all users.

**4. Insecure Design**: Security was not considered during application design, leading to architectural flaws that cannot be fixed by implementation changes alone. This category emphasizes the need for threat modeling and secure design principles from the start.

**5. Security Misconfiguration**: Unnecessary features enabled, default credentials unchanged, overly verbose error messages, missing security headers, unpatched systems. The most common example is cloud storage (S3 buckets, Azure Blob Storage) configured for public access, inadvertently exposing sensitive data.

**6. Vulnerable and Outdated Components**: Using libraries, frameworks, or other software components with known vulnerabilities. The 2021 Log4Shell vulnerability (CVE-2021-44228) in the Log4j library, which allowed remote code execution and affected hundreds of millions of systems worldwide, exemplified this risk.

**7. Identification and Authentication Failures**: Weaknesses in session management (predictable session IDs, insufficient session expiration), credential management (permitting weak passwords, insecure credential storage), and authentication mechanisms (missing MFA, default credentials).

**8. Software and Data Integrity Failures**: Code and infrastructure that does not verify software integrity — auto-update functionality that downloads without signature verification, insecure CI/CD pipelines, deserialization of untrusted data.

**9. Security Logging and Monitoring Failures**: Insufficient logging and monitoring allows breaches to go undetected. Organizations take an average of 207 days to identify a data breach (IBM Cost of Data Breach Report), largely due to inadequate monitoring.

**10. Server-Side Request Forgery (SSRF)**: The application fetches a remote resource specified by user-supplied input without validating the URL, allowing attackers to cause the server to connect to internal services, cloud metadata endpoints, or arbitrary external systems.

> 📌 **Key Concept — Cross-Site Scripting (XSS)**: XSS attacks, while folded into the Injection category, deserve special attention. **Reflected XSS** involves malicious script embedded in a URL that the server reflects back in its response. **Stored XSS** involves malicious script persisted in the application (in a database, comment field, etc.) and executed when other users view that content. **DOM-based XSS** is manipulated entirely in the browser's DOM without server involvement. All forms of XSS can be used to steal session cookies, redirect users to phishing pages, or perform actions on behalf of the victim.

> 📌 **Key Concept — CSRF (Cross-Site Request Forgery)**: CSRF tricks a victim's browser into sending authenticated requests to another site where the victim is logged in, exploiting the browser's automatic inclusion of cookies. If a victim visits a malicious page while logged into their bank, a hidden `<img>` or `<form>` tag can trigger a fund transfer. CSRF is mitigated through anti-CSRF tokens (secret values that the attacker cannot predict) and the `SameSite` cookie attribute.

---

## 8.3 Browser Security

### The Same-Origin Policy

The **Same-Origin Policy (SOP)** is a fundamental browser security mechanism that restricts how scripts loaded from one origin (defined as the combination of scheme, hostname, and port) can interact with resources from another origin. Without SOP, a malicious script could silently read your email, your bank balance, or any other data from any site you are logged into.

**CORS (Cross-Origin Resource Sharing)** is a controlled relaxation of SOP that allows servers to explicitly declare which origins may access their resources, using HTTP headers (e.g., `Access-Control-Allow-Origin`). Misconfigured CORS policies (e.g., `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`) can re-open the vulnerabilities that SOP prevents.

### Cookies and Session Management

**HTTP cookies** are small pieces of data stored by the browser and automatically sent with every request to the domain that set them. They are the primary mechanism for maintaining session state in stateless HTTP. Security-relevant cookie attributes:

- **`Secure`**: Cookie is only sent over HTTPS connections.
- **`HttpOnly`**: Cookie is inaccessible to JavaScript, preventing theft via XSS.
- **`SameSite`**: Controls when cookies are sent with cross-origin requests (`Strict` blocks all cross-site cookie sending; `Lax` allows top-level navigation; `None` requires the `Secure` attribute).
- **`Domain` and `Path`**: Restrict the scope of cookie sending.

Session cookies should use cryptographically random session identifiers (at least 128 bits of entropy), be regenerated after authentication, and expire after a reasonable idle period.

### Content Security Policy (CSP)

**Content Security Policy (CSP)** is an HTTP response header that tells the browser which sources of content (scripts, styles, images, fonts, etc.) are legitimate for a given page. By specifying a strict CSP (e.g., `script-src 'self'`), an application can prevent the execution of injected scripts even if an XSS vulnerability exists, providing a powerful defense-in-depth layer against XSS attacks. CSP is not a substitute for fixing XSS vulnerabilities but significantly raises the bar for exploitation.

---

## 8.4 Email Security Protocols

Email's foundational protocols (SMTP, POP3, IMAP) were designed without authentication, making email domain spoofing trivially easy — anyone can send an email claiming to be from `ceo@yourcompany.com`. Three complementary standards have been developed to address this:

### SPF (Sender Policy Framework)

**SPF** allows domain owners to publish, via DNS TXT records, a list of mail servers authorized to send email on behalf of their domain. When a receiving mail server gets a message, it checks whether the sending server's IP is listed in the sender domain's SPF record. This prevents unauthorized servers from sending mail as your domain.

However, SPF only validates the *envelope sender* (the SMTP MAIL FROM address), not the visible *From:* header. It also breaks when emails are legitimately forwarded.

### DKIM (DomainKeys Identified Mail)

**DKIM** allows sending mail servers to attach a cryptographic signature to outgoing messages. The signature covers specified headers and the message body. The corresponding public key is published in the sending domain's DNS records. Receiving servers verify the signature, confirming that the message was sent by an authorized server and has not been modified in transit.

DKIM is more robust than SPF for integrity verification, but by itself, it does not tell receiving servers what to do with messages that fail verification.

### DMARC (Domain-based Message Authentication, Reporting, and Conformance)

**DMARC** builds on SPF and DKIM by allowing domain owners to specify what should happen to messages that fail authentication (nothing, quarantine to spam, or reject outright) and to receive aggregate reports about email traffic patterns. A properly configured DMARC policy (especially with `p=reject`) dramatically reduces spoofed email successfully reaching recipients.

> ⚠️ **Warning**: Email without SPF, DKIM, and DMARC is easily spoofed. Many phishing attacks succeed because recipient organizations do not validate the sender's domain. Organizations should configure SPF, DKIM, and DMARC for all domains, including parked domains that never send email.

---

## 8.5 DNS Security and DNSSEC

The DNS infrastructure underpins nearly all internet communication — every web request, email, and API call typically begins with a DNS lookup. Yet traditional DNS provides no authentication: resolvers cannot verify that the responses they receive are from the authoritative name server for a domain and haven't been tampered with.

**DNSSEC (DNS Security Extensions)** adds cryptographic signatures to DNS records. Each zone has a key pair; resource records are signed with the private key, and resolvers can verify these signatures using the public key published in the zone. A chain of trust runs from the DNS root zone (maintained by ICANN) down through TLDs (.com, .org) to individual domains.

DNSSEC prevents DNS cache poisoning but adds complexity and is not universally deployed. **DNS over HTTPS (DoH)** and **DNS over TLS (DoT)** are complementary protocols that encrypt DNS queries themselves, preventing eavesdropping on what domains you are looking up — an important privacy protection, especially on untrusted Wi-Fi networks.

---

## 8.6 Anonymity Networks, the Dark Web, and VPNs

### VPN Use for Privacy

Beyond their role in securing remote access (covered in Chapter 7), VPNs are widely used for privacy: by routing all traffic through the VPN provider's servers, the user's ISP and local network see only encrypted traffic to the VPN, not the final destinations. However, this only shifts trust to the VPN provider, who can see all the user's traffic. Users should choose VPN providers with strong no-logging policies and ideally those that have been independently audited.

### Tor and Onion Routing

**Tor (The Onion Router)** provides anonymity through a technique called *onion routing*. When a Tor user connects to a website, their traffic is encrypted in multiple layers and relayed through a circuit of three volunteer-operated **Tor relays** (the guard/entry node, a middle relay, and an exit node). Each relay decrypts one layer, learning only the previous and next hop — no single relay knows both the origin and destination of the traffic.

Tor is used by journalists, activists, whistleblowers, and ordinary users who need strong anonymity. It is also used by criminals, which is why Tor has a controversial reputation. Tor is slow due to the multi-hop routing and is vulnerable to *traffic correlation attacks* by adversaries who can observe both the entry and exit of the network.

**Tor Hidden Services** (.onion addresses) allow servers to be hosted on the Tor network without revealing the server's IP address, creating the infrastructure of the **dark web**.

### The Dark Web

The **dark web** refers to overlay networks (primarily Tor, but also I2P and Freenet) that require specific software to access and provide anonymity to both clients and servers. It hosts a range of content: privacy-focused services (SecureDrop for whistleblowing), forums, and unfortunately, markets for illegal goods and cybercrime-as-a-service operations.

From a security perspective, the dark web is significant as a marketplace for stolen credentials, ransomware tools, zero-day exploits, and personal data from breaches. Organizations monitor dark web forums and marketplaces for indications that their data or credentials have been compromised.

---

## 8.7 IoT Security

The **Internet of Things (IoT)** encompasses the vast and growing ecosystem of network-connected devices beyond traditional computers: smart thermostats, IP cameras, smart TVs, medical devices, industrial control systems, and home appliances. By 2030, an estimated 25 billion IoT devices will be deployed.

IoT devices present severe security challenges:

- **Insecure defaults**: Many devices ship with default credentials (admin/admin, admin/password) that many users never change. The Mirai botnet (2016), which launched record-breaking DDoS attacks, was built from hundreds of thousands of IoT devices compromised using default credentials.
- **Infrequent updates**: Many IoT devices run outdated firmware and do not automatically update. Manufacturers may abandon devices entirely (ceasing to provide security patches) within a few years of sale.
- **Lack of encryption**: Many IoT protocols (Zigbee, Z-Wave, older Bluetooth profiles) lack strong encryption by default.
- **Large attack surface**: IoT devices often run full operating systems with many services enabled that are not needed for their purpose.
- **Physical security limitations**: Devices deployed in public or exposed locations may be subject to physical tampering.

The NIST Cybersecurity for IoT Program and the UK's Product Security and Telecommunications Infrastructure (PSTI) Act 2022 are examples of regulatory efforts to impose baseline security requirements on IoT manufacturers, including banning default credentials and requiring vulnerability disclosure programs.

---

## 8.8 Secure Online Transactions and Payment Security

### PCI-DSS

The **Payment Card Industry Data Security Standard (PCI-DSS)** is a set of security standards developed by the PCI Security Standards Council (founded by major card brands: Visa, Mastercard, American Express, Discover) that applies to any organization that stores, processes, or transmits cardholder data. PCI-DSS includes requirements for network security (firewalls, encryption in transit), access control (least privilege, MFA), vulnerability management (patching, security testing), and monitoring.

PCI-DSS compliance is not a guarantee of security, but it establishes a meaningful baseline. Merchants who achieve compliance through compliance-checking exercises alone without actually improving security ("checkbox compliance") continue to be breached.

**EMV (Europay, Mastercard, Visa)** chip technology, now standard on credit and debit cards, uses a cryptographic challenge-response protocol that makes card-present transaction data useless for fraudulent transactions even if captured — unlike the static data on magnetic stripes. This has shifted card fraud toward card-not-present (online) transactions, which require other mitigations such as 3D Secure (3DS) protocols.

---

## 8.9 Tracking, Privacy, and Personal Data

### Cookies, Fingerprinting, and Trackers

While first-party cookies serve legitimate purposes (session state, preferences), **third-party tracking cookies** enable advertising networks and data brokers to track users' browsing behavior across unrelated websites. Modern browsers (Safari, Firefox, Brave) and privacy regulations (GDPR, CCPA) have increasingly restricted third-party cookies.

As cookie-based tracking becomes harder, advertisers have increasingly turned to **browser fingerprinting**: collecting a set of characteristics from the browser and device (screen resolution, installed fonts, browser plugins, canvas rendering, WebGL data, time zone, etc.) that are individually common but together form a near-unique identifier. Users can test their fingerprint uniqueness at sites like coveryourtracks.eff.org.

**Data brokers** aggregate personal data from public records, social media, loyalty programs, and purchased datasets, building detailed profiles on individuals that are sold to marketers, law enforcement, and — sometimes — stalkers or malicious actors.

### Privacy Hygiene Best Practices

- **Password managers** (Bitwarden, 1Password, KeePass) enable the use of unique, strong passwords for every account, eliminating credential reuse.
- **Multi-Factor Authentication (MFA)**: Enable MFA — preferably hardware security keys (FIDO2/WebAuthn) or TOTP apps — on all accounts, especially email, banking, and cloud storage. SMS-based MFA is better than nothing but vulnerable to SIM swapping.
- **Browser privacy**: Use a privacy-focused browser (Firefox with uBlock Origin, Brave) or configure your existing browser to block trackers. Consider using separate browser profiles for different purposes.
- **HTTPS Everywhere**: Modern browsers now warn on HTTP sites; always verify the HTTPS padlock for sensitive operations.
- **DNS privacy**: Configure DNS over HTTPS or DNS over TLS (e.g., 1.1.1.1 with DoH) to prevent DNS eavesdropping.
- **Social media hygiene**: Review privacy settings, minimize the data shared in profiles, and think critically before posting personal information.
- **Email security**: Be suspicious of unexpected emails with links or attachments; verify requests through a secondary channel. Use email providers with strong security practices.

---

## Key Terms

- **HTTPS**: HTTP carried over TLS, providing encrypted and authenticated web communication.
- **HSTS (HTTP Strict Transport Security)**: A header instructing browsers to only use HTTPS for a domain.
- **OWASP Top 10**: A list of the most critical web application security risks, maintained by OWASP.
- **SQL Injection**: An attack injecting SQL code into user input to manipulate database queries.
- **XSS (Cross-Site Scripting)**: An attack injecting malicious scripts into web pages viewed by other users.
- **CSRF (Cross-Site Request Forgery)**: An attack tricking a victim's browser into making authenticated requests to another site.
- **Same-Origin Policy (SOP)**: A browser security mechanism restricting cross-origin script access.
- **CORS (Cross-Origin Resource Sharing)**: A controlled, server-specified relaxation of the Same-Origin Policy.
- **Content Security Policy (CSP)**: An HTTP header specifying legitimate content sources to mitigate XSS.
- **SPF (Sender Policy Framework)**: A DNS-based email sender validation mechanism.
- **DKIM (DomainKeys Identified Mail)**: A cryptographic email signing mechanism.
- **DMARC**: A policy framework specifying how to handle email failing SPF/DKIM validation.
- **DNSSEC**: DNS extensions adding cryptographic authentication to DNS records.
- **DoH (DNS over HTTPS)**: DNS queries encrypted with HTTPS for privacy.
- **Tor**: An anonymity network using onion routing to conceal user identity and location.
- **Dark Web**: Overlay networks (primarily Tor) hosting content/services inaccessible to standard browsers.
- **IoT (Internet of Things)**: Network-connected devices beyond traditional computers.
- **PCI-DSS**: Payment card industry security standard for organizations handling cardholder data.
- **Browser Fingerprinting**: Identifying users by their unique browser/device configuration characteristics.
- **Data Broker**: An organization that collects and sells personal data profiles.
- **MFA (Multi-Factor Authentication)**: Authentication requiring two or more verification factors.
- **SSRF (Server-Side Request Forgery)**: An attack causing the server to make requests to unintended destinations.
- **BGP Hijacking**: Malicious or accidental announcement of IP routes an AS doesn't own.

---

## Review Questions

1. Explain why the presence of an HTTPS padlock icon does not necessarily mean a website is trustworthy. What does HTTPS actually guarantee, and what are its limitations?

2. Describe a SQL injection attack in detail. Write an example of vulnerable pseudocode and explain what an attacker could do by exploiting it. How does parameterized query/prepared statement implementation prevent this attack?

3. Compare reflected XSS, stored XSS, and DOM-based XSS. Give an example scenario for each. How does the `HttpOnly` cookie attribute help mitigate XSS attacks?

4. Explain the Same-Origin Policy and why it is important for browser security. What is CORS, and how does a misconfigured CORS policy create a security vulnerability?

5. A company's domain is being used to send phishing emails that appear to come from `accounts@theircompany.com`. Explain how SPF, DKIM, and DMARC each help address this problem, and describe what a complete email authentication deployment would look like.

6. Describe how Tor provides anonymity through onion routing. What are the limitations of Tor's anonymity model? Under what circumstances can a Tor user be de-anonymized?

7. What security risks do IoT devices introduce to a home or enterprise network? Describe the Mirai botnet attack and what specific security failures it exploited.

8. Explain how browser fingerprinting works. Why is it more resistant to user countermeasures than cookie-based tracking? What steps can a user take to reduce their fingerprint uniqueness?

9. A small e-commerce website needs to process credit card payments. Explain the relevance of PCI-DSS to this organization and describe three specific technical controls PCI-DSS would require.

10. You are advising a journalist who needs to communicate sensitive information with a source while protecting both their identities. What combination of tools and practices would you recommend, and why?

---

## Further Reading

1. OWASP Foundation. (2021). *OWASP Top Ten*. Available at: https://owasp.org/www-project-top-ten/ — The definitive reference for web application security risks.

2. Soghoian, C., & Stamm, S. (2010). "Certified Lies: Detecting and Defeating Government Interception Attacks Against SSL." *Financial Cryptography*. — Examines PKI and certificate authority trust issues.

3. Dingledine, R., Mathewson, N., & Syverson, P. (2004). "Tor: The Second-Generation Onion Router." *Proceedings of the USENIX Security Symposium*. — The original Tor design paper.

4. FTC. (2014). *Data Brokers: A Call for Transparency and Accountability*. Federal Trade Commission. — Examines the data broker industry and its privacy implications.

5. ENISA. (2020). *Guidelines for Securing the Internet of Things*. European Union Agency for Cybersecurity. Available at: https://www.enisa.europa.eu/publications/guidelines-for-securing-the-internet-of-things
