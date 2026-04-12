---
title: "Chapter 6: Cryptography Fundamentals"
chapter: 6
week: 6
course: SCIA-120
description: "A comprehensive introduction to cryptography, covering historical ciphers, modern symmetric and asymmetric encryption, hash functions, digital signatures, PKI, and the quantum computing threat."
---

# Chapter 6: Cryptography Fundamentals

## Introduction

Cryptography is among the oldest disciplines in the long history of human secrecy and communication. At its core, cryptography is the science and art of transforming information into an unintelligible form so that only authorized parties can read it. The word itself comes from the Greek *kryptos* (hidden) and *graphia* (writing). What began as simple letter substitutions chiseled into stone tablets has evolved, over millennia, into a rigorous mathematical discipline that underpins virtually every secure digital interaction in modern life — from online banking to encrypted messaging applications to the TLS padlock icon in your web browser.

The importance of cryptography in computing and information assurance cannot be overstated. Without it, every password, credit card number, and private message sent across the internet would be available in plaintext to anyone capable of intercepting network traffic. Cryptography is not merely a feature layered on top of systems; it is the foundational mechanism that makes trust possible in an untrusted network environment. Understanding how cryptographic algorithms work, where they succeed, and — equally important — where they fail is essential knowledge for any computing professional.

---

## 6.1 Historical Ciphers and Their Lessons

### The Caesar Cipher

The Caesar cipher, attributed to Julius Caesar, is one of the earliest documented encryption schemes. It works by shifting each letter of the alphabet by a fixed number of positions. For example, with a shift of 3, the letter A becomes D, B becomes E, and so on. The message "ATTACK AT DAWN" would become "DWWDFN DW GDZQ."

Despite its historical significance, the Caesar cipher is trivially weak by modern standards. Because there are only 25 possible shift values (excluding zero), an attacker can break it through *exhaustive key search* — trying all possible keys — in seconds. This illustrates the first principle of modern cryptography: the security of a cipher must not rely on secrecy of the algorithm, only secrecy of the key. This is known as **Kerckhoffs's Principle**, formulated in 1883.

### The Vigenère Cipher

The Vigenère cipher, introduced in the 16th century, improved on Caesar by using a repeating keyword to determine different shifts for different character positions. If the keyword is "KEY" and the message is "HELLOWORLD," then the first letter H is shifted by K (10), E is shifted by E (4), L is shifted by Y (24), and so on. The cipher repeats the keyword cyclically across the message.

For centuries, the Vigenère cipher was considered unbreakable. In the 19th century, however, Charles Babbage and later Friedrich Kasiski independently discovered that the repetitive nature of the keyword creates detectable statistical patterns, particularly if the key is short relative to the message. This led to the development of *frequency analysis* as a cryptanalytic technique and demonstrated that complexity alone does not guarantee security — mathematical rigor does.

### The Enigma Machine

The Enigma machine, used by Nazi Germany during World War II, represented a leap in mechanical cryptographic complexity. It used a series of electromechanical rotors that scrambled electrical signals as a key was pressed, with the rotor positions advancing after each keypress, producing a polyalphabetic substitution cipher of staggering complexity. The number of possible configurations was on the order of 10^23.

Despite this complexity, the Enigma was broken through a combination of mathematical insight (notably by Alan Turing and his colleagues at Bletchley Park), procedural weaknesses in German operators' habits, and captured key sheets. The Enigma story teaches us that even highly complex systems can be defeated when human procedures are weak — a lesson that applies directly to modern information security.

---

## 6.2 Cryptographic Goals

Modern cryptography is defined by four primary security goals:

- **Confidentiality**: Ensuring that information is accessible only to authorized parties. Encryption is the primary mechanism.
- **Integrity**: Ensuring that information has not been altered in an unauthorized manner. Hash functions and MACs (Message Authentication Codes) provide this.
- **Authentication**: Verifying the identity of a communicating party. Digital signatures and certificates enable authentication.
- **Non-repudiation**: Ensuring that a sender cannot deny having sent a message. Digital signatures, properly implemented with a PKI, provide non-repudiation.

> 📌 **Key Concept**: These four goals are sometimes summarized with the acronym **CIA + NR** — Confidentiality, Integrity, Authentication, Non-Repudiation. Not all cryptographic systems provide all four; understanding which goals are met by which mechanism is crucial to designing secure systems.

---

## 6.3 Symmetric Encryption

### How Block Ciphers Work

Symmetric encryption uses the same key for both encryption and decryption. Modern symmetric ciphers operate as *block ciphers*, processing fixed-size chunks of data (blocks) rather than individual bytes. The plaintext is divided into blocks (typically 128 bits), each block is encrypted with a series of mathematical transformations, and the resulting ciphertext blocks are assembled into the final encrypted output.

The transformations in a modern block cipher typically involve multiple *rounds*, each applying operations such as substitution (replacing bytes with other values using a lookup table called an S-box), permutation (rearranging bits), and mixing with a subkey derived from the main key. This layered approach is called a *substitution-permutation network* (SPN).

### DES and 3DES

The **Data Encryption Standard (DES)** was adopted as a federal standard in 1977. It operates on 64-bit blocks with a 56-bit key, using 16 rounds of a Feistel network structure. By the late 1990s, the short key length had become a critical vulnerability — a special-purpose machine called Deep Crack demonstrated in 1998 that DES could be brute-forced in less than 23 hours.

**Triple DES (3DES)** was introduced as a stopgap, applying DES encryption three times with either two or three independent keys (112-bit or 168-bit effective key length). While substantially more secure than DES, 3DES is slow and has been officially deprecated by NIST as of 2023.

### AES: The Advanced Encryption Standard

The **Advanced Encryption Standard (AES)**, standardized by NIST in 2001, replaced DES and 3DES as the gold standard for symmetric encryption. AES supports key lengths of 128, 192, or 256 bits and operates on 128-bit blocks through 10, 12, or 14 rounds respectively. Its design is based on a substitution-permutation network and has withstood more than two decades of intense cryptanalytic scrutiny.

AES is extraordinarily fast in both hardware and software. Modern Intel and AMD CPUs include AES-NI instruction set extensions that allow AES encryption and decryption to be performed in single clock cycles, making performance essentially a non-issue in most applications.

### Modes of Operation

Even a secure block cipher like AES can be used insecurely if the *mode of operation* is poorly chosen. A mode of operation defines how a block cipher is applied to messages longer than a single block.

- **ECB (Electronic Codebook)**: The simplest mode — each block is encrypted independently. This is **dangerously insecure** for most purposes because identical plaintext blocks produce identical ciphertext blocks, leaking information about patterns in the data. The classic example is the "ECB penguin" — an image of Tux the Linux mascot encrypted with ECB, where the outline of the penguin remains clearly visible in the ciphertext.
- **CBC (Cipher Block Chaining)**: Each plaintext block is XORed with the previous ciphertext block before encryption. This eliminates the identical-block weakness and is widely used. A random *Initialization Vector (IV)* must be used for the first block. However, CBC is vulnerable to certain padding oracle attacks (e.g., POODLE against SSL).
- **GCM (Galois/Counter Mode)**: A modern, authenticated encryption mode that combines counter-mode encryption with a Galois field authentication tag. GCM provides both confidentiality and integrity simultaneously and is the preferred mode for most modern applications, including TLS 1.3.

### Key Management

The security of any symmetric encryption system ultimately depends on the security of the key, not the algorithm. Key management — the processes governing key generation, distribution, storage, rotation, and destruction — is often the weakest link in cryptographic deployments.

Keys must be generated using a cryptographically secure random number generator (CSPRNG). They must be stored securely, ideally in dedicated hardware (HSMs — Hardware Security Modules). Keys should be rotated periodically and destroyed securely when retired. Many high-profile breaches have resulted not from breaking the underlying cipher but from compromised key management.

---

## 6.4 Asymmetric Encryption

### The Public/Private Key Pair

The fundamental limitation of symmetric encryption is the *key distribution problem*: if Alice wants to send Bob an encrypted message, how does she share the symmetric key with him securely over an insecure channel? Asymmetric (or *public-key*) cryptography, introduced by Diffie and Hellman in 1976 and formalized by Rivest, Shamir, and Adleman in 1977, solves this problem elegantly.

In asymmetric cryptography, each party has a *key pair*: a **public key** that can be freely shared with anyone, and a **private key** that is kept absolutely secret. Data encrypted with the public key can only be decrypted with the corresponding private key. Conversely, data signed with the private key can be verified by anyone with the public key.

### RSA: How It Works (Simplified)

**RSA** (Rivest-Shamir-Adleman) is the most widely deployed asymmetric encryption algorithm. Its security rests on the *integer factorization problem*: multiplying two large prime numbers together is computationally easy, but factoring the product back into its prime components is computationally infeasible for sufficiently large numbers.

The key generation process, in simplified form:

1. Choose two large prime numbers *p* and *q*.
2. Compute *n = p × q* (the modulus, which becomes part of the public key).
3. Compute *φ(n) = (p-1)(q-1)* (Euler's totient function).
4. Choose an integer *e* (public exponent, typically 65537) such that gcd(e, φ(n)) = 1.
5. Compute *d* (the private exponent) such that *d × e ≡ 1 (mod φ(n))*.
6. Public key = (n, e); Private key = (n, d).

Encryption: *C = M^e mod n*. Decryption: *M = C^d mod n*.

The security of RSA depends on the key length. 1024-bit RSA keys are considered weak; 2048-bit keys are the current minimum for most applications; 4096-bit keys provide a larger security margin.

### Elliptic Curve Cryptography (ECC)

**Elliptic Curve Cryptography (ECC)** provides equivalent security to RSA but with much smaller key sizes. A 256-bit ECC key provides roughly the same security as a 3072-bit RSA key. This makes ECC particularly valuable in resource-constrained environments such as mobile devices, embedded systems, and IoT devices. ECC is based on the mathematical properties of elliptic curves over finite fields and the difficulty of the *elliptic curve discrete logarithm problem*.

### Hybrid Encryption

Asymmetric encryption is orders of magnitude slower than symmetric encryption and is generally impractical for encrypting large amounts of data directly. In practice, systems use **hybrid encryption**: asymmetric cryptography is used to securely exchange a symmetric session key, and then symmetric encryption (e.g., AES-GCM) handles the bulk data encryption. This approach, used in TLS and PGP among others, combines the key distribution advantages of asymmetric cryptography with the speed of symmetric cryptography.

---

## 6.5 Hash Functions

A **cryptographic hash function** takes an input of arbitrary length and produces a fixed-size output (the *digest* or *hash*). Unlike encryption, hashing is a one-way operation — given a hash, it should be computationally infeasible to recover the original input.

### Properties of Cryptographic Hash Functions

1. **Preimage resistance**: Given a hash *h*, it should be computationally infeasible to find any input *m* such that hash(*m*) = *h*.
2. **Second preimage resistance**: Given an input *m1*, it should be computationally infeasible to find a different input *m2* such that hash(*m1*) = hash(*m2*).
3. **Collision resistance**: It should be computationally infeasible to find *any* two distinct inputs *m1* and *m2* such that hash(*m1*) = hash(*m2*).

### Common Hash Algorithms

| Algorithm | Output Size | Status |
|-----------|-------------|--------|
| MD5 | 128 bits | **Broken** — collision attacks known; do not use for security |
| SHA-1 | 160 bits | **Deprecated** — collisions demonstrated (SHAttered, 2017) |
| SHA-256 | 256 bits | **Secure** — part of SHA-2 family, widely used |
| SHA-3 (Keccak) | Variable (224–512 bits) | **Secure** — different design from SHA-2, provides algorithm diversity |

SHA-256 and SHA-3 are the current standards for most security applications. MD5 and SHA-1 should never be used for new security-sensitive applications, though they may still appear in legacy systems.

> ⚠️ **Warning**: Hashing passwords with a simple hash function (even SHA-256) is insufficient. Password hashing requires specially designed, computationally expensive algorithms such as **bcrypt**, **Argon2**, or **PBKDF2** to resist brute-force and dictionary attacks. See Chapter 4 for details on password security.

### The Birthday Attack

The **birthday attack** is a cryptanalytic technique exploiting the surprising probability that in a group of only 23 randomly chosen people, there is a greater than 50% chance that two of them share a birthday — the "birthday paradox." Applied to hash functions: for a hash with *n*-bit output, an attacker needs only approximately 2^(n/2) hash computations (not 2^n) to find a collision. This is why MD5 (128-bit output) is particularly weak — finding a collision requires only about 2^64 computations, which is feasible with modern hardware.

---

## 6.6 Digital Signatures and Certificates

### Digital Signatures

A **digital signature** provides authentication, integrity, and non-repudiation for digital documents. The process works as follows:

1. Alice computes the hash of her message: *h = hash(message)*.
2. Alice encrypts the hash with her private key: *signature = RSA_decrypt(private_key, h)* (conceptually — in practice, this is more precisely described as "signing" using the private key operation).
3. Alice sends the message and the signature to Bob.
4. Bob computes the hash of the received message and decrypts Alice's signature with her public key: *h' = RSA_encrypt(Alice_public_key, signature)*.
5. If *h == h'*, the signature is valid — the message has not been altered and was signed by Alice (assuming only Alice holds her private key).

Common digital signature algorithms include **RSA-PSS**, **DSA (Digital Signature Algorithm)**, and **ECDSA (Elliptic Curve DSA)**.

### Public Key Infrastructure (PKI)

A critical problem with public-key cryptography is: how do you know that a public key actually belongs to who you think it does? An attacker could substitute their own public key, impersonating another party. The **Public Key Infrastructure (PKI)** solves this through digital certificates.

A **digital certificate** (most commonly an X.509 certificate) binds a public key to an identity (a person, organization, or domain name). This binding is attested to by a trusted third party called a **Certificate Authority (CA)**. The CA verifies the identity of the certificate requestor and then digitally signs the certificate with its own private key. Anyone who trusts the CA can verify the certificate signature and trust that the public key truly belongs to the identified entity.

CAs are arranged in a hierarchy — **root CAs** at the top, which sign certificates for **intermediate CAs**, which in turn sign **end-entity certificates**. Web browsers and operating systems come pre-loaded with a set of trusted root CA certificates (the "root store").

---

## 6.7 TLS/SSL: The Handshake Explained

**TLS (Transport Layer Security)** and its predecessor SSL (now deprecated) are cryptographic protocols that provide secure communication over the internet. Every HTTPS connection uses TLS. The TLS handshake establishes a secure session between client and server:

**TLS 1.3 Handshake (Simplified):**

1. **ClientHello**: The client sends its supported TLS version, cipher suites, and a random nonce to the server.
2. **ServerHello**: The server selects the cipher suite and TLS version, sends its own random nonce, and transmits its certificate (containing its public key).
3. **Certificate Verification**: The client verifies the server's certificate against its trusted root store, confirming the server's identity.
4. **Key Exchange**: Both parties perform a Diffie-Hellman key exchange to derive a shared symmetric session key. This is done without transmitting the key itself, providing *forward secrecy*.
5. **Finished**: Both parties send a "Finished" message authenticated with the derived session key. If both messages verify correctly, the secure channel is established.
6. **Application Data**: All subsequent data is encrypted with the negotiated symmetric cipher (typically AES-GCM or ChaCha20-Poly1305).

TLS 1.3, introduced in 2018, eliminated many legacy cryptographic options and significantly simplified and hardened the handshake compared to TLS 1.2.

---

## 6.8 Cryptographic Attacks

### Brute Force

A **brute-force attack** systematically tries every possible key until the correct one is found. The feasibility depends entirely on key length. A 128-bit key has 2^128 ≈ 3.4 × 10^38 possible values — trying all of them is computationally impossible with current technology. A 40-bit key, by contrast, has only about 10^12 possible values, feasibly searched in seconds by modern hardware.

### Man-in-the-Middle (MitM)

In a **man-in-the-middle attack**, an adversary intercepts communication between two parties, relaying messages while potentially reading or modifying them. Cryptographic authentication (through digital certificates and PKI) is specifically designed to detect and prevent MitM attacks. If a MitM attacker tries to substitute their own certificate, the client will detect that the certificate is not signed by a trusted CA.

### Side-Channel Attacks

**Side-channel attacks** do not attack the mathematical properties of a cipher but instead exploit information leaked by the physical implementation: timing variations, power consumption patterns, electromagnetic radiation, or even acoustic signals. For example, RSA implementations that do not use constant-time operations may leak information about the private key through variations in execution time.

---

## 6.9 Quantum Computing and Post-Quantum Cryptography

Quantum computers, leveraging principles of quantum mechanics such as superposition and entanglement, can theoretically solve certain mathematical problems exponentially faster than classical computers. Two algorithms pose existential threats to current cryptographic systems:

- **Shor's Algorithm**: Can factor large integers and solve discrete logarithm problems in polynomial time, breaking RSA and ECC.
- **Grover's Algorithm**: Provides a quadratic speedup for searching unsorted databases, effectively halving the security of symmetric keys (a 256-bit AES key would provide only ~128 bits of security against a quantum computer).

While large-scale, fault-tolerant quantum computers do not yet exist, NIST launched a Post-Quantum Cryptography (PQC) standardization project and in 2024 published the first PQC standards: **CRYSTALS-Kyber** (key encapsulation), **CRYSTALS-Dilithium**, **FALCON**, and **SPHINCS+** (digital signatures). These algorithms are based on mathematical problems believed to be hard even for quantum computers, primarily *lattice-based* problems and *hash-based* constructions. Organizations should begin planning for cryptographic agility — designing systems to swap out cryptographic algorithms as the quantum threat matures.

---

## Key Terms

- **Plaintext**: The original, readable data before encryption.
- **Ciphertext**: The encrypted, unintelligible output of an encryption process.
- **Symmetric Encryption**: Encryption using the same key for both encryption and decryption.
- **Asymmetric Encryption**: Encryption using a mathematically related key pair (public and private).
- **Block Cipher**: A cipher that operates on fixed-size blocks of data.
- **AES (Advanced Encryption Standard)**: The current NIST-standard symmetric block cipher; supports 128/192/256-bit keys.
- **RSA**: A widely used asymmetric algorithm based on integer factorization.
- **ECC (Elliptic Curve Cryptography)**: Asymmetric cryptography using elliptic curves; provides high security with smaller keys.
- **Hash Function**: A one-way function producing a fixed-size digest of arbitrary-length input.
- **Collision Resistance**: The property that it is computationally infeasible to find two inputs producing the same hash output.
- **Digital Signature**: A cryptographic mechanism proving the authenticity and integrity of a message.
- **Certificate Authority (CA)**: A trusted entity that issues and signs digital certificates.
- **PKI (Public Key Infrastructure)**: The system of hardware, software, policies, and standards for managing digital certificates.
- **TLS (Transport Layer Security)**: The cryptographic protocol securing HTTPS and many other internet communications.
- **Forward Secrecy**: The property that compromise of long-term keys does not compromise past session keys.
- **Birthday Attack**: A cryptanalytic technique exploiting collision probability to find hash collisions with 2^(n/2) effort.
- **Post-Quantum Cryptography**: Cryptographic algorithms designed to be secure against quantum computers.
- **Kerckhoffs's Principle**: The security of a cipher should depend only on secrecy of the key, not the algorithm.
- **Hybrid Encryption**: Combining asymmetric key exchange with symmetric bulk encryption.
- **Mode of Operation**: Defines how a block cipher is applied to data longer than one block (ECB, CBC, GCM).

---

## Review Questions

1. Explain Kerckhoffs's Principle and why it is foundational to modern cryptography. Why is "security through obscurity" considered insufficient?

2. Compare and contrast symmetric and asymmetric encryption in terms of speed, key management, and appropriate use cases. Why do real-world systems typically use both (hybrid encryption)?

3. A colleague proposes storing user passwords by hashing them with SHA-256. Explain why this is insufficient and describe a better approach.

4. An organization is deploying a new file encryption system. They propose using AES in ECB mode for simplicity. Explain the security weakness of ECB mode and recommend an alternative, justifying your choice.

5. Walk through the steps of the RSA key generation process. What mathematical problem does RSA's security depend on, and how does key length affect security?

6. Describe the TLS 1.3 handshake process step by step. What role does the Certificate Authority play, and how does the handshake provide forward secrecy?

7. What is a birthday attack? If a hash function produces 160-bit outputs (like SHA-1), how many hash computations would an attacker theoretically need to find a collision?

8. Explain the difference between preimage resistance and collision resistance in hash functions. Which property is more difficult to achieve?

9. You are reviewing a web application and discover it uses MD5 to generate file integrity checksums for software downloads. What risks does this create, and what should you recommend instead?

10. Describe the threat that quantum computers pose to current cryptographic systems. Which algorithms are most at risk, and what is the current state of post-quantum cryptography standardization?

---

## Further Reading

1. Paar, C., & Pelzl, J. (2010). *Understanding Cryptography: A Textbook for Students and Practitioners*. Springer. — An excellent, mathematically accessible introduction to modern cryptography.

2. Schneier, B. (1996). *Applied Cryptography: Protocols, Algorithms, and Source Code in C* (2nd ed.). Wiley. — A classic reference covering practical cryptographic implementation.

3. NIST. (2001). *Advanced Encryption Standard (FIPS PUB 197)*. National Institute of Standards and Technology. Available at: https://csrc.nist.gov/publications/detail/fips/197/final

4. Bernstein, D.J., & Lange, T. (2017). "Post-quantum cryptography." *Nature*, 549(7671), 188–194. — A clear overview of the post-quantum landscape.

5. Rescorla, E. (2018). *The Transport Layer Security (TLS) Protocol Version 1.3* (RFC 8446). Internet Engineering Task Force. Available at: https://datatracker.ietf.org/doc/html/rfc8446
