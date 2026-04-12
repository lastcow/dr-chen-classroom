---
title: "Authentication and Access Control"
week: 11
chapter: 11
course: SCIA-120
---

# Chapter 11: Authentication and Access Control

## Introduction

Every secure computing system ultimately depends on one foundational question: *who are you, and what are you allowed to do?* Authentication and access control are the mechanisms that answer these questions, forming the first line of defense against unauthorized use of systems, data, and resources. In this chapter, we examine the principles, technologies, and attack vectors surrounding identity verification and access management — from classic password hashing techniques to modern passwordless authentication, from single sign-on federations to privileged access management in enterprise environments.

Understanding authentication and access control is not merely a technical exercise. It is a study in how trust is established and enforced between humans and machines, and increasingly between machines and other machines. As the digital attack surface expands — with billions of users, IoT devices, cloud workloads, and microservices all needing authenticated access — the robustness of identity infrastructure becomes critical to organizational security.

---

## 11.1 AAA: Authentication, Authorization, and Accounting

Security professionals commonly refer to the "AAA" framework when discussing identity and access:

**Authentication** is the process of verifying that an entity is who it claims to be. A user presenting a username and password, a server presenting a TLS certificate, or a mobile app presenting a cryptographic token — all of these are acts of authentication.

**Authorization** is what happens *after* authentication: determining what an authenticated entity is permitted to do. Even after you prove you are Alice, the system must decide: can Alice read this file? Approve this payment? Modify this configuration? Authorization is governed by policies, roles, and access control models.

**Accounting** (sometimes called *auditing*) refers to the recording and monitoring of what authenticated and authorized users actually do. Accounting data supports forensic investigation, compliance auditing, anomaly detection, and non-repudiation — the ability to prove that a specific user performed a specific action.

These three pillars are often implemented together in protocols like RADIUS (Remote Authentication Dial-In User Service) and TACACS+, which are widely used in network access control for VPNs, Wi-Fi, and managed network devices.

---

## 11.2 Authentication Factors

Authentication is built around three classical categories of evidence, often called *factors*:

### 11.2.1 Something You Know: Passwords

Passwords remain the most prevalent authentication mechanism despite their well-documented weaknesses. A strong password policy includes length requirements (minimum 12–16 characters), complexity, and prohibition of common or previously breached passwords. However, the *storage* of passwords is arguably more important than their complexity.

**Password Hashing**

Passwords should never be stored in plaintext. Instead, systems store a cryptographic hash of the password and compare hashes during login. However, not all hash functions are appropriate for password storage. Fast general-purpose hash functions like MD5 and SHA-256 are unsuitable because they allow attackers to test billions of candidate passwords per second on modern GPU hardware.

Purpose-built *password hashing functions* deliberately incorporate computational cost:

- **bcrypt**: Introduced by Niels Provos and David Mazières in 1999, bcrypt uses the Blowfish cipher in a key-schedule-intensive mode. It includes a configurable *work factor* (cost parameter) that can be increased as hardware improves. A bcrypt hash includes the algorithm identifier, cost factor, salt, and hash output in a single string.

- **Argon2**: The winner of the Password Hashing Competition (2015), Argon2 offers three variants: Argon2d (GPU-resistant), Argon2i (side-channel-resistant), and Argon2id (hybrid, recommended for most use cases). Argon2 allows tuning of time cost, memory cost, and parallelism — making it even more resistant to specialized hardware attacks than bcrypt.

- **scrypt**: Designed by Colin Percival, scrypt is memory-hard (requires significant RAM), which defends against ASIC-based attacks. It predates Argon2 but remains widely used.

**Salting**

A *salt* is a random value generated per-user and appended or prepended to the password before hashing. Salting prevents the use of precomputed *rainbow tables* — databases that map known hash values back to plaintext passwords. Even if two users choose the same password, their stored hashes will differ because their salts differ. Modern password hashing functions like bcrypt and Argon2 handle salting automatically.

> **Key Definition — Rainbow Table Attack**: A precomputed lookup table mapping common plaintext values to their hashes. Salting renders rainbow tables useless because the attacker would need a separate table for each unique salt value.

**Password Best Practices**

The National Institute of Standards and Technology (NIST) Special Publication 800-63B offers authoritative guidance on password policies. Key recommendations include:
- Allow passwords up to at least 64 characters
- Check new passwords against known-compromised password lists (e.g., Have I Been Pwned's database)
- Do not enforce mandatory periodic password rotation (it leads to weaker passwords)
- Do not require complexity rules that lead to predictable patterns (e.g., "P@ssw0rd1!")
- Use account lockout or throttling to defend against online guessing attacks

### 11.2.2 Something You Have: Possession Factors

Possession-based authentication relies on a physical or digital artifact that the legitimate user holds:

**One-Time Passwords (OTP)**

An OTP is a password valid for only a single authentication session or time window. TOTP (Time-based OTP, defined in RFC 6238) generates a 6–8 digit code by computing HMAC-SHA1 of a shared secret combined with the current Unix timestamp divided into 30-second windows. Authenticator apps like Google Authenticator, Authy, and Microsoft Authenticator implement TOTP. HOTP (HMAC-based OTP) is similar but counter-based rather than time-based.

**Hardware Tokens**

Dedicated hardware devices like RSA SecurID tokens generate OTPs independently of any connected device. More advanced *hardware security keys* such as YubiKey implement FIDO2/WebAuthn (discussed in Section 11.3) and store cryptographic keys in tamper-resistant silicon, making them far more phishing-resistant than TOTP.

**Smart Cards and PIV Credentials**

Smart cards contain an embedded chip that stores an X.509 certificate and its corresponding private key. The card performs cryptographic operations on-chip, so the private key never leaves the device. U.S. federal agencies use the *Personal Identity Verification* (PIV) standard for smart-card-based authentication. The Common Access Card (CAC) used by the Department of Defense is a PIV implementation.

**FIDO2 and WebAuthn**

The FIDO2 standard, developed by the FIDO Alliance and W3C, represents the most significant advance in authentication security in decades. It comprises two specifications:

- **CTAP (Client to Authenticator Protocol)**: Defines how external authenticators (USB/NFC/BLE security keys) communicate with platforms.
- **WebAuthn**: A browser API that allows websites to perform strong, public-key-based authentication.

During FIDO2 registration, the authenticator generates a public-private key pair scoped to a specific *relying party* (the website). The private key never leaves the authenticator. During authentication, the server presents a challenge; the authenticator signs it with the private key and returns the signature. This architecture is inherently phishing-resistant because the key material is bound to the specific origin domain.

### 11.2.3 Something You Are: Biometrics

Biometric authentication uses measurable physiological or behavioral characteristics:

| Modality | Description | Common Use Cases |
|---|---|---|
| Fingerprint | Ridge patterns on fingertip | Smartphones, laptops, time-and-attendance |
| Face recognition | Geometric features of the face | Smartphones, border control, surveillance |
| Iris recognition | Unique patterns in the colored part of the eye | High-security facilities, border control |
| Voice recognition | Vocal tract characteristics and speech patterns | Phone banking, voice assistants |
| Behavioral biometrics | Typing rhythm, mouse movement, gait | Continuous authentication, fraud detection |

**Accuracy Metrics**

Biometric systems are evaluated using two error rates:

- **False Acceptance Rate (FAR)**: The probability that the system grants access to an unauthorized person (an impostor is accepted). Also called the False Match Rate (FMR).
- **False Rejection Rate (FRR)**: The probability that the system denies access to a legitimate user. Also called the False Non-Match Rate (FNMR).

There is an inherent tradeoff: tightening the acceptance threshold decreases FAR but increases FRR, and vice versa. The *Equal Error Rate* (EER) is the threshold at which FAR equals FRR, and is commonly used to compare biometric systems. Lower EER indicates better overall accuracy.

> **Warning**: Biometric data is immutable — if a password is compromised, you can change it; if your fingerprint template is stolen, you cannot change your fingerprints. Biometric data must be stored as irreversible templates (feature vectors), never as raw images, and protected with strong access controls.

---

## 11.3 Multi-Factor Authentication (MFA)

Multi-factor authentication requires the user to present evidence from *two or more* distinct factor categories (know, have, are). The rationale is straightforward: compromising multiple independent factors simultaneously is significantly harder than compromising any single factor. A password may be phished; a hardware token requires physical possession. A fingerprint may be spoofed; a PIN must still be known.

MFA is one of the most effective controls against account takeover. Studies from Google and Microsoft consistently show that MFA blocks more than 99% of automated credential-stuffing attacks.

**MFA Implementation Considerations**

When deploying MFA, organizations must consider:
- *Enrollment friction*: Users need a smooth path to register second factors.
- *Recovery mechanisms*: What happens when a user loses their second factor? Recovery codes, backup phone numbers, and IT helpdesk processes must be secured to prevent social engineering bypass.
- *Factor downgrade attacks*: Attackers may try to convince systems or users to fall back to single-factor authentication. MFA policies must be enforced server-side.

### 11.3.1 Attacks on MFA

MFA is not impenetrable. Several attack vectors specifically target two-factor authentication:

**SIM Swapping**: The attacker calls a mobile carrier and convinces a customer service representative (through social engineering or stolen personal information) to transfer the victim's phone number to a new SIM card under the attacker's control. Once the number is transferred, any SMS OTPs sent to that number are intercepted by the attacker. SIM swapping has been used in high-profile cryptocurrency thefts worth millions of dollars.

**SS7 Attacks**: The Signaling System No. 7 (SS7) protocol, which routes SMS messages globally, has known vulnerabilities that allow skilled adversaries (typically nation-state actors or sophisticated criminals) to intercept SMS messages and call-forwarding requests at the carrier network level. This renders SMS-based OTP vulnerable to interception without the victim's knowledge.

**OTP Phishing (Real-Time Phishing)**: Automated phishing toolkits like Evilginx2 act as a reverse proxy, capturing both the user's credentials and their OTP code in real-time by sitting between the victim and the legitimate website. The attacker relays the credentials and OTP to the real site immediately, before the OTP expires, and then uses the captured session cookie for persistent access.

**Fatigue Attacks (MFA Bombing)**: When push-notification MFA is in use (e.g., Microsoft Authenticator, Duo), attackers who have the victim's password can flood the victim with repeated push notification approval requests, hoping the victim will eventually approve one out of confusion or frustration. The Uber breach of 2022 was partly enabled by this technique.

These attacks underscore why hardware security keys implementing FIDO2/WebAuthn are considered the gold standard for MFA — they are resistant to phishing and SIM swapping by design.

---

## 11.4 Passwordless Authentication

Passwordless authentication eliminates the shared secret (password) entirely, replacing it with cryptographic mechanisms. FIDO2 passkeys are the leading passwordless standard: a passkey is a FIDO2 credential stored on a device (or in a password manager/cloud keychain) that authenticates using local biometric or device unlock, without transmitting any secret to the server. Passkeys are now supported by Apple, Google, and Microsoft, and are increasingly accepted by major websites.

The security advantages of passwordless authentication are substantial: there is no password to phish, crack, stuff, or breach. The cryptographic challenge-response model means the server never holds anything that could be used to impersonate the user.

---

## 11.5 Single Sign-On and Federated Identity

Managing separate credentials for hundreds of applications is impractical. *Single Sign-On* (SSO) allows a user to authenticate once with a trusted *identity provider* (IdP) and then access multiple *service providers* (SPs) or *relying parties* without re-authenticating for each. Federation extends SSO across organizational boundaries.

### 11.5.1 SAML 2.0

Security Assertion Markup Language (SAML) 2.0 is an XML-based standard for exchanging authentication and authorization data between an IdP and an SP. The typical flow is:

1. User attempts to access an SP (e.g., Salesforce).
2. SP redirects the user to their IdP (e.g., Okta, Azure AD) with a SAML Request.
3. IdP authenticates the user (prompting for credentials and MFA).
4. IdP issues a signed XML *SAML Assertion* and redirects the user back to the SP.
5. SP validates the assertion's signature and grants access.

SAML is widely deployed in enterprise environments for connecting business applications to corporate identity systems.

### 11.5.2 OAuth 2.0

OAuth 2.0 is an authorization framework (not an authentication protocol) that allows a third-party application to obtain limited access to a user's resources on a service provider, with the user's consent, without sharing their credentials. The key OAuth 2.0 roles are:

- **Resource Owner**: The user who owns the data.
- **Client**: The application requesting access.
- **Authorization Server**: Issues access tokens after authenticating the user and obtaining consent.
- **Resource Server**: Hosts the protected resources; accepts access tokens.

OAuth 2.0 defines several *grant types* (flows) for different scenarios: Authorization Code (for server-side web apps), Authorization Code with PKCE (for public clients like mobile apps), Client Credentials (for machine-to-machine), and Implicit (deprecated due to security concerns).

### 11.5.3 OpenID Connect (OIDC)

OpenID Connect is an *authentication* layer built on top of OAuth 2.0. While OAuth 2.0 only addresses authorization (what resources can be accessed), OIDC adds an *ID Token* — a signed JWT (JSON Web Token) that contains claims about the authenticated user (subject, issuer, expiration, email, etc.). OIDC is now the dominant protocol for web and mobile authentication, used by "Sign in with Google," "Sign in with Apple," and enterprise SSO systems.

### 11.5.4 Kerberos

Kerberos is a network authentication protocol developed at MIT, now central to Microsoft Active Directory. It uses symmetric-key cryptography and a trusted third party — the *Key Distribution Center* (KDC) — to authenticate clients and servers without transmitting passwords over the network. The KDC comprises two services: the Authentication Server (AS) and the Ticket-Granting Server (TGS). Upon login, the user receives a *Ticket-Granting Ticket* (TGT); subsequent access to services uses this TGT to request service-specific tickets. Kerberos is subject to specific attacks including *Pass-the-Ticket*, *Golden Ticket* (forging a TGT using the compromised `krbtgt` account hash), and *Kerberoasting* (requesting service tickets and cracking them offline).

---

## 11.6 LDAP and Active Directory

The *Lightweight Directory Access Protocol* (LDAP) is a protocol for accessing and managing directory information — essentially a structured database of network objects: users, groups, computers, printers, and organizational units. Microsoft *Active Directory* (AD) is the most widely deployed LDAP-based directory service, forming the identity backbone of most enterprise Windows environments.

AD organizes objects in a hierarchical structure of *forests*, *domains*, and *organizational units* (OUs). *Group Policy Objects* (GPOs) allow administrators to enforce security configurations across all domain-joined machines. AD authentication is primarily Kerberos-based, falling back to NTLM where Kerberos is unavailable.

Active Directory is a prime target for attackers. Techniques like *DCSync* (simulating a domain controller replication to extract password hashes), *BloodHound/SharpHound* (graphing AD relationships to identify privilege escalation paths), and *AS-REP Roasting* (exploiting accounts with pre-authentication disabled) are standard tools in modern penetration testing and real-world attacks.

---

## 11.7 Access Control Models and Implementation

Once identity is established, access control policies determine what that identity can do. Several formal models guide implementation:

**Discretionary Access Control (DAC)**: Resource owners control access to their own resources. The classic Unix file permission model (owner/group/other, read/write/execute) is DAC. It is flexible but relies on users making correct access decisions — mistakes propagate easily.

**Mandatory Access Control (MAC)**: A central authority defines access policies based on classification labels (e.g., Secret, Top Secret) and subject clearances. Users cannot override these policies. MAC is used in high-security government and military systems (SELinux implements MAC in Linux).

**Role-Based Access Control (RBAC)**: Users are assigned to roles; roles are granted permissions. Access is managed by assigning appropriate roles rather than managing individual permissions per user. RBAC is the dominant model in enterprise applications and cloud IAM systems.

**Attribute-Based Access Control (ABAC)**: Access decisions are made based on attributes of the subject (user department, clearance level), the object (data classification, owner), the action (read, write, delete), and the environment (time of day, location, device type). ABAC is more granular than RBAC and is the basis for modern *Zero Trust* architectures and *Policy Decision Points* (PDPs).

### 11.7.1 Least Privilege and Need-to-Know

The *principle of least privilege* states that every user, process, and system component should have the minimum permissions necessary to perform its intended function — and no more. This limits the blast radius of a compromise: a low-privilege account that is hijacked can cause far less damage than an administrator account.

*Need-to-know* is a related concept: even users with the appropriate clearance or role should only access specific information they need for a specific task. These principles work together to reduce insider threat risk and limit the movement of external attackers through a network.

---

## 11.8 Identity and Access Management (IAM)

*Identity and Access Management* (IAM) is the broader organizational and technical framework for managing digital identities and their access rights throughout their lifecycle: provisioning (creating accounts), maintenance (modifying roles), and deprovisioning (revoking access when an employee leaves or changes roles). Failure to deprovision accounts promptly is a common vulnerability — orphaned accounts are a significant risk.

**Privileged Access Management (PAM)** is a specialized discipline focused on controlling and auditing access by privileged accounts — system administrators, database administrators, network engineers, and service accounts with elevated permissions. PAM solutions like CyberArk, BeyondTrust, and HashiCorp Vault provide:
- Just-in-time (JIT) privileged access (temporary elevation rather than persistent admin rights)
- Password vaulting (centralizing and rotating privileged credentials)
- Session recording (full video/keystroke recording of privileged sessions for audit)
- Approval workflows for sensitive operations

---

## 11.9 Credential Attacks: Stuffing and Spraying

**Credential Stuffing** exploits the widespread reuse of passwords. Attackers obtain large lists of username/password pairs from previous data breaches (billions of credentials are available on criminal forums) and systematically test them against other services. Because many users reuse passwords across sites, a credential set from a gaming site breach may work on banking or email accounts. Defenses include MFA, breach-detection feeds (checking user credentials against known breach databases), and rate limiting.

**Password Spraying** is a variation of brute-force attacks designed to avoid account lockout policies. Instead of trying many passwords against one account (which would trigger lockout), the attacker tries one common password (e.g., "Spring2024!") against a large number of accounts. Because each account only sees a single failed attempt, account lockout thresholds are not exceeded. Password spraying is particularly effective against organizations with predictable password patterns and weak MFA enforcement.

---

## Key Terms

- **Authentication**: The process of verifying the claimed identity of a user, device, or system.
- **Authorization**: The process of determining what permissions an authenticated entity has.
- **Accounting (Auditing)**: The recording of user actions for audit and forensic purposes.
- **Password Hashing**: A one-way transformation of a password using a cryptographic function to avoid storing plaintext passwords.
- **Salt**: A random per-user value mixed with a password before hashing to prevent rainbow table attacks.
- **bcrypt / Argon2**: Purpose-built, computationally expensive password hashing functions designed to resist GPU-based cracking.
- **TOTP**: Time-based One-Time Password; generates short-lived codes using a shared secret and the current time.
- **FIDO2 / WebAuthn**: A W3C/FIDO Alliance standard for cryptographic, phishing-resistant authentication using hardware-bound key pairs.
- **Biometrics**: Authentication based on physiological or behavioral characteristics.
- **FAR / FRR**: False Acceptance Rate and False Rejection Rate; key accuracy metrics for biometric systems.
- **MFA (Multi-Factor Authentication)**: Authentication requiring evidence from two or more distinct factor categories.
- **SIM Swapping**: Social engineering a carrier into transferring a victim's phone number to attacker-controlled SIM, enabling SMS OTP hijacking.
- **SSO (Single Sign-On)**: Authentication mechanism allowing access to multiple services with a single credential event.
- **SAML 2.0**: XML-based protocol for SSO and federated identity between identity providers and service providers.
- **OAuth 2.0**: An authorization delegation framework allowing third-party access to user resources without sharing credentials.
- **OpenID Connect (OIDC)**: An authentication layer built on OAuth 2.0, providing ID tokens with user identity claims.
- **Kerberos**: A symmetric-key network authentication protocol using tickets, used as the basis for Active Directory authentication.
- **Active Directory**: Microsoft's LDAP-based enterprise directory service providing centralized identity management for Windows domains.
- **RBAC**: Role-Based Access Control; permissions are assigned to roles, and users are assigned to roles.
- **Least Privilege**: The principle that entities should have the minimum access needed for their function.
- **PAM (Privileged Access Management)**: Systems and practices for controlling, monitoring, and auditing privileged account usage.
- **Credential Stuffing**: Automated use of breached username/password pairs to attempt logins on other services.
- **Password Spraying**: Testing a single common password against many accounts to avoid lockout thresholds.

---

## Review Questions

1. Explain the distinction between authentication, authorization, and accounting. Give a concrete example of each in the context of a university information system.

2. Why are general-purpose cryptographic hash functions like SHA-256 inappropriate for password storage? What properties make bcrypt and Argon2 better suited for this purpose?

3. Describe how salting a password hash defeats rainbow table attacks. Why is it important that salts be unique per user?

4. A user authenticates to their corporate email using a username, password, and an SMS-based OTP code. Explain how a SIM-swapping attack would allow an attacker to bypass this MFA setup. What authentication method would be resistant to this attack, and why?

5. Compare and contrast OAuth 2.0 and OpenID Connect. What problem does each solve, and why is it important not to confuse them?

6. A new employee joins your organization and is granted access to several systems. Six months later, they transfer to a different department, and a year after that they leave the company entirely. What IAM lifecycle events should occur at each transition, and what are the security risks if they are neglected?

7. Explain the difference between the RBAC and ABAC access control models. Describe a scenario where ABAC provides a security advantage over RBAC.

8. What is credential stuffing, and why is it so effective? What technical and policy controls can an organization implement to defend against it?

9. Describe a real-time phishing attack (e.g., using a tool like Evilginx2) that bypasses TOTP-based MFA. Why would a FIDO2 hardware security key resist this attack?

10. Explain the principle of least privilege. How does Privileged Access Management (PAM) operationalize this principle in an enterprise environment?

---

## Further Reading

- National Institute of Standards and Technology. (2020). *Digital Identity Guidelines: Authentication and Lifecycle Management* (NIST SP 800-63B). https://pages.nist.gov/800-63-3/sp800-63b.html

- FIDO Alliance. (2023). *FIDO2: Moving the World Beyond Passwords*. https://fidoalliance.org/fido2/

- Bonneau, J., Herley, C., van Oorschot, P. C., & Stajano, F. (2012). The quest to replace passwords: A framework for comparative evaluation of web authentication schemes. *2012 IEEE Symposium on Security and Privacy*, 553–567.

- Microsoft Security. (2022). *How MFA Can Prevent 99.9% of Account Compromise Attacks*. Microsoft Security Blog. https://www.microsoft.com/security/blog/

- CyberArk. (2023). *Privileged Access Management Best Practices Guide*. https://www.cyberark.com/resources/
