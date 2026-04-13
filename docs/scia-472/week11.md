---
title: "Week 11 — Malware Analysis Fundamentals"
description: Learn static and dynamic malware analysis techniques to identify indicators of compromise, classify threats, and understand malware behavior.
---

# Week 11 — Malware Analysis Fundamentals

<div class="week-meta" markdown>
**Course Objectives:** CO6 &nbsp;|&nbsp; **Focus:** Malware Analysis &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Classify malware by type and behavioral characteristics
- [ ] Perform static analysis using file inspection, string extraction, and PE header analysis
- [ ] Conduct dynamic analysis in an isolated sandbox environment
- [ ] Extract indicators of compromise (IoCs) from malware samples
- [ ] Use YARA rules to detect malware by pattern matching

---

## 1. Malware Classification

| Type | Primary Behavior | Notable Examples |
|------|-----------------|-----------------|
| **Virus** | Self-replicates by infecting host files | CIH (Chernobyl), Melissa |
| **Worm** | Self-propagates across networks without host file | WannaCry, Conficker |
| **Trojan** | Disguises as legitimate software | Emotet, Agent Tesla |
| **Ransomware** | Encrypts files; demands payment | LockBit, BlackCat/ALPHV, Conti |
| **Rootkit** | Hides malware/attacker presence from OS | ZeroAccess, Necurs |
| **Spyware/Infostealer** | Silently collects data | RedLine Stealer, Vidar |
| **Keylogger** | Records keystrokes | HawkEye, Olympic Destroyer |
| **Botnet Agent** | Remote command-and-control client | Mirai, Trickbot |
| **RAT** | Full remote administration | DarkComet, njRAT, AsyncRAT |
| **Dropper/Loader** | Delivers second-stage payload | Emotet, Qakbot |
| **Fileless Malware** | Resides in memory/registry; no disk files | PowerSploit, Cobalt Strike beacon |

---

## 2. Analysis Environment Setup

!!! danger "Safe Analysis Environment"
    **Never** analyze malware on production or personal systems. Use:

    - **Isolated VM** with network adapter set to **Host-Only** or **NAT with firewall**
    - **Snapshot** before analysis — revert after
    - **No shared folders** between host and guest
    - **No real credentials** in the VM

```
Recommended Analysis VM Setup:
  OS: Windows 10 (most malware targets Windows)
  Tools pre-installed: Sysinternals Suite, Wireshark, PEStudio, 
                       x64dbg, IDA Free, Ghidra, Flare-VM
  Network: INetSim (simulate internet services locally)
  
  OR: Use REMnux (dedicated malware analysis Linux distro)
      + FlareVM (Windows analysis workstation)
```

---

## 3. Static Analysis

Static analysis examines the malware **without executing it**.

### 3.1 File Identification

```bash
# Identify file type (ignore extension)
file malware.exe
# Output: malware.exe: PE32+ executable (GUI) x86-64, for MS Windows

# Check hash — compare to VirusTotal
md5sum malware.exe
sha256sum malware.exe

# VirusTotal lookup
curl -X POST "https://www.virustotal.com/vtapi/v2/file/report" \
  --data "apikey=YOUR_KEY&resource=SHA256_HASH"
```

### 3.2 String Extraction

```bash
# Extract printable strings
strings malware.exe | grep -iE "(http|cmd|powershell|reg|admin)"
strings -n 6 malware.exe        # Minimum 6 char strings

# Common suspicious strings:
# URLs/IPs      → C2 server addresses
# Registry keys → persistence locations
# cmd.exe       → command execution
# powershell    → script execution
# CreateRemoteThread → process injection
# VirtualAlloc  → memory allocation (shellcode)
# InternetOpenUrl → network communication
# RegSetValueEx → registry modification

# Floss (FireEye) — extracts obfuscated strings
floss malware.exe
```

### 3.3 PE Header Analysis (Windows Executables)

```bash
# PEStudio (Windows GUI tool — excellent for static analysis)
# Analyzes: imports, exports, sections, resources, strings, indicators

# PEview / PE-bear — PE structure visualization

# Key things to examine:
```

| PE Section | Purpose | Suspicious Signs |
|------------|---------|-----------------|
| `.text` | Executable code | Encrypted/packed if small |
| `.data` | Initialized data | Large .data may contain payload |
| `.rsrc` | Resources | Embedded EXEs, scripts |
| `.rdata` | Read-only data | Import/export table |
| `UPX0/UPX1` | UPX packer sections | Packed executable |

**Import Analysis (API calls reveal intent):**

```
Suspicious Imports:
  CreateRemoteThread + VirtualAllocEx   → Process injection
  WriteProcessMemory                    → Code injection
  URLDownloadToFile + CreateProcess     → Download and execute
  RegSetValueEx + HKEY_RUN             → Registry persistence
  GetAsyncKeyState                      → Keylogger
  CryptEncrypt                          → Ransomware encryption
  WSAConnect / InternetOpenUrl          → Network C2
  NtQuerySystemInformation              → Rootkit/anti-analysis
```

### 3.4 YARA Rules

YARA matches files based on byte patterns, strings, and conditions:

```yara
rule WannaCry_Ransomware {
    meta:
        description = "Detects WannaCry ransomware"
        author = "Security Team"
        date = "2017-05-12"
        
    strings:
        $s1 = "WANACRY!" ascii
        $s2 = ".WNCRY" ascii
        $s3 = "WanaCrypt0r" ascii
        $s4 = "tasksche.exe" ascii
        $s5 = { 45 78 70 6C 6F 72 65 72 2E 65 78 65 }  // "Explorer.exe" hex
        
    condition:
        uint16(0) == 0x5A4D and    // MZ header (PE file)
        3 of ($s*)                  // Match 3 of the 5 strings
}
```

```bash
# Scan with YARA rule
yara wannacry.yar suspicious_file.exe
yara -r wannacry.yar /suspicious_directory/

# YARA rule repositories
# THOR APT Scanner rules: https://github.com/Neo23x0/signature-base
# Awesome-YARA: https://github.com/InQuest/awesome-yara
```

---

## 4. Dynamic Analysis

Dynamic analysis **executes the malware** in a controlled environment and observes behavior.

### 4.1 Process Monitoring (Sysinternals)

```
Process Monitor (ProcMon):
  → Captures file system, registry, network, and process activity
  → Filter by: Process Name = malware.exe
  → Look for: registry writes to Run keys, file drops, network connections

Process Explorer:
  → Visual process tree
  → Detect process injection (malware.exe creating threads in legit process)
  → Check signature on running processes
  → Hover on process → see all DLLs loaded

Process Hacker:
  → Similar to Process Explorer but more powerful
  → View process memory regions
  → Detect hollowed processes (legitimate EXE with replaced code)
```

### 4.2 Network Traffic Analysis

```bash
# Wireshark — capture all traffic during execution
# Filters:
# ip.dst == known_c2_ip
# http.request
# dns.qry.name contains "dga"    # Domain Generation Algorithm
# tcp.flags == 0x002              # SYN packets (new connections)

# FakeNet-NG / INetSim — simulate internet services
# Malware thinks it's connecting to real C2 → reveals C2 protocol

# Common C2 behaviors:
# Regular beaconing (every X seconds/minutes)
# DNS queries to random-looking domains (DGA)
# HTTP POST to /gate.php, /upload, /check-in
# HTTPS to self-signed or suspicious certs
```

### 4.3 Automated Sandbox Analysis

```bash
# Cuckoo Sandbox (self-hosted)
# Submit sample → automatic analysis report
cuckoo submit malware.exe

# Online sandboxes (no setup required):
# https://any.run          → Interactive browser-based sandbox
# https://app.tria.ge      → Fast, detailed reports
# https://www.hybrid-analysis.com → Free, FALCON sandbox
# https://sandbox.anlyz.io
# https://www.joesandbox.com

# Report contains:
# - Behavioral timeline
# - Network traffic (PCAP)
# - Dropped files
# - Registry changes
# - Screenshots
# - MITRE ATT&CK mapping
# - Extracted IoCs
```

---

## 5. Indicators of Compromise (IoCs)

IoCs are forensic artifacts that indicate a compromise has occurred:

### IoC Types

```
File-based:          Hash (MD5, SHA-256), filename, file path, file size
Network-based:       IP addresses, domains, URLs, user agents, JA3 hashes
Registry:            Keys created/modified (persistence, configuration)
Process:             Process names, parent-child relationships, command lines
Behavioral:          API call sequences, file access patterns
Certificate:         SSL certificate hashes, issuer, subject
```

### Extracting IoCs from Analysis

```bash
# From static analysis:
strings malware.exe | grep -E "([0-9]{1,3}\.){3}[0-9]{1,3}"  # IPs
strings malware.exe | grep -E "(https?://[^ ]+)"               # URLs

# Domain extraction from PCAP
tshark -r analysis.pcap -Y "dns" -T fields -e dns.qry.name | sort -u

# IoC sharing formats:
# STIX/TAXII    → Structured Threat Information eXpression
# OpenIOC       → Mandiant's format
# MISP          → Open-source threat intelligence platform
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **IoC** | Indicator of Compromise — artifact indicating system breach |
| **Static Analysis** | Examining malware without executing it |
| **Dynamic Analysis** | Executing malware in controlled environment to observe behavior |
| **Sandbox** | Isolated environment for safe malware execution |
| **YARA** | Pattern matching language for malware detection |
| **PE** | Portable Executable — Windows binary format |
| **Packing** | Compressing/encrypting malware to evade static analysis |
| **Process Hollowing** | Replacing legitimate process memory with malware code |
| **DGA** | Domain Generation Algorithm — creates pseudorandom C2 domains |

---

## Review Questions

!!! question "Self-Assessment"
    1. What is the difference between a dropper and a loader? Why do modern malware authors separate these components?
    2. You observe a process named `svchost.exe` running from `C:\Users\Public\`. Why is this suspicious, and how would you investigate?
    3. Write a YARA rule to detect a ransomware family that: creates files with `.locked` extension, contains the string "bitcoin" and "wallet", and is a Windows PE file.
    4. Describe how a Domain Generation Algorithm (DGA) evades blacklist-based network defenses.
    5. Explain the concept of process hollowing and why it's effective at evading EDR solutions.

---

## Further Reading

- 📄 [Malware Traffic Analysis](https://www.malware-traffic-analysis.net/) — practice PCAPs with answers
- 📄 [Any.run](https://app.any.run/) — interactive sandbox (free tier)
- 📄 [MITRE ATT&CK: Execution](https://attack.mitre.org/tactics/TA0002/)
- 📖 *Practical Malware Analysis* — Sikorski & Honig (No Starch Press)
- 📄 [Flare-VM Setup](https://github.com/mandiant/flare-vm) — Windows analysis workstation

---

*[← Week 10](week10.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 12 →](week12.md)*
