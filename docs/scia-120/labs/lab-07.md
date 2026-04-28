# Lab 07 — Encryption in Practice with OpenSSL

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Cryptography — Symmetric & Asymmetric Encryption  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 6 — Cryptography Fundamentals

---

## Overview

Cryptography is the backbone of modern information security. In this lab you will use **OpenSSL** — the industry-standard cryptography toolkit — entirely inside a Docker container to generate encryption keys, encrypt and decrypt files with both symmetric (AES) and asymmetric (RSA) encryption, and inspect a real TLS certificate. By the end, you will understand *how* encryption actually works at a practical level.

---

## Learning Objectives

1. Encrypt and decrypt a file using AES symmetric encryption.
2. Generate an RSA public/private key pair.
3. Encrypt data with a public key and decrypt with a private key.
4. Understand when to use symmetric vs. asymmetric encryption.
5. Inspect a real TLS certificate and identify its components.

---

## Prerequisites

- Docker Desktop installed and running.

---

## Part 1 — Symmetric Encryption with AES

Symmetric encryption uses the **same key** to encrypt and decrypt. It is fast and used for bulk data encryption.

### Step 1.1 — Start an OpenSSL Container

```bash
docker run --rm -it ubuntu:22.04 bash
```

Install OpenSSL:

```bash
apt-get update -qq && apt-get install -y -qq openssl
```

### Step 1.2 — Create a Sensitive File

```bash
echo "Patient Record: John Smith, DOB: 1985-03-14, Diagnosis: Hypertension" > patient_record.txt
cat patient_record.txt
```

### Step 1.3 — Encrypt with AES-256-CBC

```bash
openssl enc -aes-256-cbc -pbkdf2 -in patient_record.txt -out patient_record.enc
```

You will be prompted for a password — use `SecureKey123`. Enter it twice.

```bash
ls -la patient_record.*
od -c patient_record.enc | head -4
```

The encrypted file is unreadable binary data (gibberish characters).

📸 **Screenshot checkpoint:** Take a screenshot showing the encrypted file content (unreadable ciphertext).

### Step 1.4 — Decrypt the File

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -in patient_record.enc -out patient_recovered.txt
cat patient_recovered.txt
```

Use the same password (`SecureKey123`) when prompted.

📸 **Screenshot checkpoint:** Take a screenshot showing successful decryption — the original plaintext recovered.

### Step 1.5 — Try Decrypting with Wrong Password

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -in patient_record.enc -out wrong_attempt.txt
```

Enter a wrong password. OpenSSL will fail with an error.

📸 **Screenshot checkpoint:** Take a screenshot of the decryption failure with wrong password.

---

## Part 2 — Asymmetric Encryption with RSA

Asymmetric encryption uses a **key pair**: a public key (shared with anyone) and a private key (kept secret). Data encrypted with the public key can **only** be decrypted with the private key.

### Step 2.1 — Generate an RSA Private Key

```bash
openssl genrsa -out private_key.pem 2048
ls -la private_key.pem
head -5 private_key.pem
```

📸 **Screenshot checkpoint:** Take a screenshot showing the RSA private key file (just the header, not the full key).

### Step 2.2 — Extract the Public Key

```bash
openssl rsa -in private_key.pem -pubout -out public_key.pem
cat public_key.pem
```

The public key can be shared freely — you give it to anyone who wants to send you encrypted messages.

📸 **Screenshot checkpoint:** Take a screenshot of the public key output.

### Step 2.3 — Encrypt with the Public Key

```bash
echo "Transfer $50,000 to account 9876" > secret_message.txt
openssl pkeyutl -encrypt -inkey public_key.pem -pubin -in secret_message.txt -out encrypted_message.bin
cat encrypted_message.bin
```

The message is now encrypted — only the holder of the private key can read it.

📸 **Screenshot checkpoint:** Take a screenshot of the unreadable encrypted binary.

### Step 2.4 — Decrypt with the Private Key

```bash
openssl pkeyutl -decrypt -inkey private_key.pem -in encrypted_message.bin -out decrypted_message.txt
cat decrypted_message.txt
```

📸 **Screenshot checkpoint:** Take a screenshot showing the decrypted message.

---

## Part 3 — Digital Signatures

A **digital signature** proves that a message came from who it claims to come from and has not been altered. The sender signs with their **private key**; anyone verifies with the **public key**.

### Step 3.1 — Sign a Document

```bash
echo "I authorize this transaction. - Dr. Chen" > authorization.txt
openssl dgst -sha256 -sign private_key.pem -out authorization.sig authorization.txt
ls -la authorization.sig
```

### Step 3.2 — Verify the Signature

```bash
openssl dgst -sha256 -verify public_key.pem -signature authorization.sig authorization.txt
```

**Expected output:** `Verified OK`

📸 **Screenshot checkpoint:** Take a screenshot showing "Verified OK".

### Step 3.3 — Tamper and Re-Verify

```bash
echo "I authorize this transaction AND a second one. - Dr. Chen" > authorization.txt
openssl dgst -sha256 -verify public_key.pem -signature authorization.sig authorization.txt
```

**Expected output:** `Verification Failure` — tampering detected!

📸 **Screenshot checkpoint:** Take a screenshot showing "Verification Failure" after tampering.

---

## Part 4 — Inspecting a Real TLS Certificate

TLS certificates are how websites prove their identity using asymmetric cryptography.

### Step 4.1 — Download and Inspect a Certificate

```bash
openssl s_client -connect google.com:443 -showcerts </dev/null 2>/dev/null | \
  openssl x509 -noout -text | head -40
```

📸 **Screenshot checkpoint:** Take a screenshot showing the certificate details — Subject, Issuer, validity dates, and key info.

### Step 4.2 — Key Fields to Identify

From the output, find and note:
- **Subject:** who the certificate belongs to
- **Issuer:** who signed/vouched for it (Certificate Authority)
- **Not Before / Not After:** validity period
- **Public Key Algorithm:** RSA or EC
- **Key Size:** 2048-bit, 4096-bit, etc.

Type `exit` when done.

---

## Cleanup

```bash
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-07a` — Encrypted file (unreadable ciphertext)
- [ ] `screenshot-07b` — Successful decryption (plaintext recovered)
- [ ] `screenshot-07c` — Decryption failure with wrong password
- [ ] `screenshot-07d` — RSA private key header
- [ ] `screenshot-07e` — RSA public key content
- [ ] `screenshot-07f` — Encrypted binary message
- [ ] `screenshot-07g` — Decrypted message with private key
- [ ] `screenshot-07h` — Digital signature "Verified OK"
- [ ] `screenshot-07i` — Digital signature "Verification Failure" after tampering
- [ ] `screenshot-07j` — TLS certificate details from google.com

### Reflection Questions

1. What is the fundamental difference between symmetric and asymmetric encryption? When would you prefer each?
2. In RSA encryption, you encrypt with the **public key** and decrypt with the **private key**. Why does it need to be done in this specific order?
3. How do digital signatures prove both **authenticity** (who sent it) and **integrity** (it wasn't changed)? Use Part 3 of this lab to explain.
4. Looking at the TLS certificate for google.com: what does the "Issuer" field mean? Why can't a website just issue its own certificate and have browsers trust it?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Symmetric vs asymmetric comparison noted: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
