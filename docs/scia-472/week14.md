---
title: "Week 14 — Digital Forensics Fundamentals"
description: Apply digital forensics methodology — disk imaging, file system analysis, memory forensics, timeline reconstruction, and evidence integrity.
---

# Week 14 — Digital Forensics Fundamentals

<div class="week-meta" markdown>
**Course Objectives:** CO7 &nbsp;|&nbsp; **Focus:** Digital Forensics &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Explain the digital forensics methodology and chain of custody requirements
- [ ] Create forensically sound disk images using write blockers
- [ ] Analyze NTFS file system artifacts including MFT, $LogFile, and Recycle Bin
- [ ] Perform memory forensics using Volatility to extract processes, network connections, and malware
- [ ] Reconstruct attack timelines from multiple evidence sources

---

## 1. Digital Forensics Overview

**Digital forensics** is the application of scientifically derived and proven methods for the collection, preservation, analysis, and presentation of digital evidence.

!!! info "Forensics vs. Incident Response"
    **Incident Response** goal: Stop the attack, restore operations (speed priority)  
    **Forensics** goal: Understand what happened, gather evidence (integrity priority)  
    In practice, IR and forensics must balance both — integrity enables accurate response.

### Forensics Principles

1. **Preservation** — Never modify original evidence
2. **Authenticity** — Provably the same as when collected (hash verification)
3. **Chain of Custody** — Documented handling from collection to court
4. **Reproducibility** — Same analysis yields same results
5. **Non-repudiation** — Evidence provably collected and untampered

---

## 2. Disk Imaging

### 2.1 Write Blockers

A write blocker prevents any writes to the evidence drive while allowing reads:

```
Hardware Write Blockers (preferred):
  Tableau T35u (Forensic USB Bridge)
  Logicube Falcon
  WiebeTech UltraDock

Software Write Blockers:
  Linux: mount -o ro,noatime /dev/sdb /mnt/evidence
  Windows: Registry key (FDPolicies WriteProtect)
  
Connection: Evidence Drive → Write Blocker → Analysis Workstation
```

### 2.2 Forensic Imaging with FTK Imager

```bash
# FTK Imager (Windows GUI — industry standard)
# 1. File → Add Evidence Item → Physical Drive
# 2. Image Destination → E01 (EnCase) or RAW (dd) format
# 3. Fragmented E01 recommended (segment size: 4096 MB)
# 4. Enable MD5 and SHA-256 hash verification
# 5. Image includes: hash before + hash after = proves integrity

# Command-line alternative (Linux)
# Raw (dd) image
dc3dd if=/dev/sdb of=/mnt/storage/evidence.dd hash=sha256 hlog=hash.log
# Verify
sha256sum /dev/sdb > original_hash.txt
sha256sum evidence.dd > image_hash.txt
diff original_hash.txt image_hash.txt  # Should be identical

# ewfacquire — E01 format from Linux
ewfacquire /dev/sdb -t /mnt/storage/evidence \
  -C "Case 2026-001" -D "Dell Latitude 7490 SSD" \
  -e "John Smith, GCFE" -f encase6 -m removable
```

---

## 3. Windows File System Forensics (NTFS)

### 3.1 Master File Table ($MFT)

The MFT is the core NTFS metadata structure — every file has an MFT entry:

```
MFT ENTRY ATTRIBUTES:
  $STANDARD_INFORMATION: Created, Modified, MFT Modified, Accessed timestamps
  $FILE_NAME: 8.3 and long file name, parent directory reference
  $DATA: File content (or pointer to clusters if file is large)
  $BITMAP: Allocated clusters tracking
  
KEY TIMESTAMPS (MACE):
  M = Modified        (file content last changed)
  A = Accessed        (last read — often disabled in modern Windows)
  C = Changed (MFT)   ($MFT entry last changed — often timestomped)
  E = Entry Modified  (same as C, different tool convention)

TIMESTOMPING:
  Attackers modify MACE times to hide activity
  $STANDARD_INFORMATION timestamps are easily changed via API
  $FILE_NAME timestamps are NOT easily changed — use for validation
  Discrepancy between SI and FN timestamps = evidence of timestomping
```

```bash
# Parse MFT with mftdump/MFTECmd
MFTECmd.exe -f C:\Windows\$MFT --csv C:\output\

# Analyze with Timeline Explorer (EZTools)
# Sort by Created, Modified timestamps to see activity during attack window
```

### 3.2 Windows Prefetch

Prefetch records evidence of program execution — crucial for proving an executable ran:

```
Location: C:\Windows\Prefetch\
Format: PROGNAME-XXXXXXXX.pf

Contents:
  - Executable name
  - Run count
  - Last 8 run timestamps (Windows 8+)
  - Files and directories accessed by the executable

Forensic value:
  - Proves malware.exe was executed (even if deleted!)
  - Timestamp of first and last execution
  - Files accessed (dropped files, C2 connections)

Analysis:
  PECmd.exe -f malware.exe-XXXXXXXX.pf    # Parse single prefetch
  PECmd.exe -d C:\Windows\Prefetch\ --csv C:\output\  # Parse all
```

### 3.3 Windows Registry Forensics

```
KEY FORENSIC REGISTRY ARTIFACTS:

PERSISTENCE:
  HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
  HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
  HKLM\SYSTEM\CurrentControlSet\Services  (services)

USER ACTIVITY:
  HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs
  HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths
  HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU

INSTALLED SOFTWARE:
  HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
  HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall

SHELLBAGS (folder access history — survives deletion):
  HKCU\SOFTWARE\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU
  Analysis: SBECmd.exe --csv output\

USB DEVICES:
  HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR
  HKLM\SYSTEM\CurrentControlSet\Enum\USB
```

### 3.4 Recycle Bin Analysis

```
Location: C:\$Recycle.Bin\{SID}\
Files:
  $I{random}: Metadata (original path, deletion time, file size)
  $R{random}: Actual file content

Analysis:
  RBCmd.exe -d C:\$Recycle.Bin\ --csv output\
  
Forensic value:
  - Deleted files may still be recoverable
  - Original path reveals attacker's file system navigation
  - Deletion timestamp establishes timeline event
```

---

## 4. Memory Forensics with Volatility

Volatile memory (RAM) contains what was running at the moment of capture — processes, network connections, loaded modules, decrypted data, and passwords.

### 4.1 Volatility 3 Basics

```bash
# Identify OS profile (Volatility 3 auto-detects)
vol -f memory.raw windows.info

# List running processes
vol -f memory.raw windows.pslist

# Process tree (parent-child relationships)
vol -f memory.raw windows.pstree

# Detect hidden processes (rootkits use DKOM to hide)
vol -f memory.raw windows.psscan   # Scans memory for EPROCESS structures
# Compare pslist vs psscan — processes in psscan but not pslist = hidden!

# Active network connections
vol -f memory.raw windows.netstat

# Loaded DLLs (per process)
vol -f memory.raw windows.dlllist --pid 1234

# Command line arguments (what commands ran)
vol -f memory.raw windows.cmdline

# Registry hives in memory
vol -f memory.raw windows.registry.hivelist

# Dump specific process memory
vol -f memory.raw windows.memmap --pid 1234 --dump

# Scan for malware indicators
vol -f memory.raw windows.malfind    # Find injected code regions
vol -f memory.raw windows.hollowprocesses  # Detect process hollowing
```

### 4.2 Memory Analysis Workflow

```
STEP 1: Identify all processes
  pslist + pstree → build process timeline
  Look for: unusual parent-child (Word spawning cmd.exe)
  Look for: suspicious names (svchost.exe in wrong path)
  Look for: hidden processes (pslist vs psscan discrepancy)

STEP 2: Network connections
  netstat → active + recently closed connections
  Look for: connections to unusual external IPs
  Look for: listening ports on unexpected processes

STEP 3: Code injection detection
  malfind → memory regions with RWX permissions + code
  Dump injected regions → submit to AV or static analysis

STEP 4: Extract IoCs
  Strings from suspicious process memory
  Decrypt C2 communication if key found in memory
  Browser history, passwords from memory
```

---

## 5. Timeline Analysis

Merging artifacts from multiple sources creates a comprehensive attack timeline:

```bash
# Plaso / log2timeline — automated timeline creation
log2timeline.py --storage-file timeline.plaso image.E01

# Filter and export to CSV
psort.py -o l2tcsv timeline.plaso > timeline.csv

# Super Timeline sources:
# NTFS $MFT timestamps
# Windows Event Logs
# Prefetch files
# Browser history
# Registry LastWrite times
# LNK files (shortcuts)
# Recycle Bin metadata
# SIEM/EDR logs

# Analysis in Timeline Explorer (Eric Zimmerman Tools)
# Filter: time window of incident
# Filter: specific file paths, usernames, process names
```

---

## 6. Log Analysis

```bash
# Windows Event Log analysis with EvtxECmd
EvtxECmd.exe -f Security.evtx --csv output\

# Key log sources:
# Security.evtx     → Authentication, privilege use, policy changes
# System.evtx       → Service installs, driver loads, system events
# Application.evtx  → Application crashes, errors
# Microsoft-Windows-Sysmon/Operational.evtx  → Gold standard if Sysmon deployed

# Sysmon events (if deployed):
# Event 1:  Process creation (full command line + hashes)
# Event 3:  Network connection
# Event 7:  Image loaded (DLL)
# Event 8:  CreateRemoteThread (process injection)
# Event 11: File create
# Event 13: Registry set value
# Event 15: File stream created (ADS)
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Write Blocker** | Hardware/software preventing writes to evidence media |
| **Forensic Image** | Bit-for-bit copy of storage media, hash-verified |
| **MFT** | Master File Table — NTFS core metadata structure |
| **MACE** | Modified, Accessed, Changed, Entry (timestamps) |
| **Timestomping** | Attacker modification of file timestamps to hide activity |
| **Prefetch** | Windows execution artifact proving a program was run |
| **Volatility** | Open-source memory forensics framework |
| **Plaso** | Multi-artifact timeline creation tool (log2timeline) |
| **Sysmon** | Microsoft Sysinternals extended Windows logging |

---

## Review Questions

!!! question "Self-Assessment"
    1. A defender powers off a compromised server before forensics can be performed. List five categories of evidence that were permanently destroyed.
    2. You find `cmd.exe` running as a child process of `winword.exe`. Explain the forensic significance and what it indicates.
    3. Volatility's `pslist` shows 42 processes; `psscan` shows 45. What explains the discrepancy, and what is your next step?
    4. An attacker deleted `malware.exe` from `C:\Temp\` before you captured the disk image. Describe three artifacts that can still prove the file existed and executed.
    5. Explain the forensic significance of the `$FILE_NAME` attribute vs. the `$STANDARD_INFORMATION` attribute in the context of timestomping detection.

---

## Further Reading

- 📖 *The Art of Memory Forensics* — Ligh, Case, Levy, Walters (Wiley)
- 📖 *Digital Forensics with Open Source Tools* — Altheide & Carvey
- 📄 [Eric Zimmerman's Tools](https://ericzimmerman.github.io/#!index.md) — essential free forensics tools
- 📄 [Volatility 3 Documentation](https://volatility3.readthedocs.io/)
- 📄 SANS FOR500 — Windows Forensic Analysis
- 📄 [DFIR.training](https://dfir.training/) — free training resources

---

*[← Week 13](week13.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 15 →](week15.md)*
