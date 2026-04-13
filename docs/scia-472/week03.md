---
title: "Week 3 — Network Scanning & Enumeration"
description: Master Nmap, service fingerprinting, OS detection, and network enumeration to build a complete target network map.
---

# Week 3 — Network Scanning & Enumeration

<div class="week-meta" markdown>
**Course Objectives:** CO2 &nbsp;|&nbsp; **Focus:** Network Mapping &nbsp;|&nbsp; **Difficulty:** ⭐⭐☆☆☆
</div>

---

## Learning Objectives

- [ ] Perform TCP/UDP port scanning with Nmap across various scan types
- [ ] Detect operating systems and service versions through fingerprinting
- [ ] Enumerate SMB, SNMP, LDAP, and RPC services for credential and configuration data
- [ ] Interpret Nmap NSE script output for automated service analysis
- [ ] Evade common network detection mechanisms during scanning

---

## 1. TCP/IP Fundamentals for Scanners

Understanding the TCP three-way handshake is essential for interpreting scan results:

```
CLIENT                        SERVER
  │                              │
  │──── SYN ──────────────────→ │   (initiate connection)
  │ ←── SYN/ACK ─────────────── │   (server acknowledges)
  │──── ACK ──────────────────→ │   (connection established)
  │                              │
  │──── RST ──────────────────→ │   (or: immediate reset = port open but refused)
  │                              │
  [No Response]                     port filtered (firewall drops)
  [RST/ACK]                         port closed (TCP stack responds)
```

**Port States:**

| State | Meaning |
|-------|---------|
| **Open** | Service actively accepting connections |
| **Closed** | Port reachable but no service listening |
| **Filtered** | Firewall/ACL dropping packets (no response) |
| **Unfiltered** | Port reachable but state unknown (ACK scan) |
| **Open\|Filtered** | Cannot determine (no response to UDP/FIN/Null/Xmas) |

---

## 2. Nmap — The Network Mapper

Nmap is the industry-standard tool for network discovery and security auditing.

### 2.1 Scan Types

```bash
# Host Discovery (ping sweep — no port scan)
nmap -sn 192.168.1.0/24

# SYN Scan (default, requires root, fast, stealthy)
nmap -sS 192.168.1.100

# TCP Connect Scan (no root needed, fully logged by target)
nmap -sT 192.168.1.100

# UDP Scan (slow, important for DNS/SNMP/TFTP/NTP)
nmap -sU 192.168.1.100

# Aggressive Scan (OS detect + version + scripts + traceroute)
nmap -A 192.168.1.100

# Null Scan (no flags — evades some firewalls)
nmap -sN 192.168.1.100

# FIN Scan (FIN flag only)
nmap -sF 192.168.1.100

# Xmas Scan (FIN+PSH+URG flags — "lit up like a Christmas tree")
nmap -sX 192.168.1.100

# ACK Scan (determine firewall rules, not open ports)
nmap -sA 192.168.1.100
```

### 2.2 Port Specification

```bash
# Scan specific ports
nmap -p 22,80,443,3389 target

# Scan port range
nmap -p 1-1024 target

# Scan all 65535 ports
nmap -p- target

# Top 1000 ports (default)
nmap target

# Top 100 ports (fast recon)
nmap -F target

# Common service ports
nmap -p 21,22,23,25,53,80,110,143,443,445,3306,3389,8080,8443 target
```

### 2.3 Service Version Detection

```bash
# Version detection (-sV)
nmap -sV 192.168.1.100

# Sample output:
# 22/tcp  open  ssh     OpenSSH 7.4 (protocol 2.0)
# 80/tcp  open  http    Apache httpd 2.4.6 ((CentOS))
# 443/tcp open  ssl/http nginx 1.16.1
# 3306/tcp open mysql   MySQL 5.7.34

# Intensity levels (0=light, 9=most aggressive)
nmap -sV --version-intensity 9 target
```

### 2.4 OS Detection

```bash
# OS fingerprinting (-O)
nmap -O 192.168.1.100

# Combined with version detection
nmap -O -sV 192.168.1.100

# Sample OS detection output:
# OS CPE: cpe:/o:linux:linux_kernel:3.16
# OS details: Linux 3.16 - 4.6
# Network Distance: 1 hop
```

### 2.5 Nmap Scripting Engine (NSE)

NSE extends Nmap with hundreds of scripts for automated service analysis:

```bash
# Run default safe scripts
nmap -sC 192.168.1.100

# Run scripts for specific category
nmap --script=vuln 192.168.1.100          # Vulnerability detection
nmap --script=auth 192.168.1.100          # Authentication bypass
nmap --script=brute 192.168.1.100         # Brute force
nmap --script=discovery 192.168.1.100     # Service discovery
nmap --script=malware 192.168.1.100       # Malware indicators

# Specific useful scripts:
nmap --script=smb-vuln-ms17-010 192.168.1.100    # EternalBlue
nmap --script=http-title 192.168.1.0/24          # Grab HTTP titles
nmap --script=ssl-cert target                     # Inspect SSL cert
nmap --script=dns-zone-transfer --script-args dns-zone-transfer.domain=target.com ns1.target.com
```

### 2.6 Output Formats

```bash
# Normal output
nmap -oN scan.txt target

# XML (for import into other tools)
nmap -oX scan.xml target

# Grepable format
nmap -oG scan.gnmap target

# All formats simultaneously
nmap -oA scan_results target

# Parse with grep
grep "open" scan.gnmap | awk '{print $2, $5}'
```

---

## 3. Service Enumeration

### 3.1 SMB Enumeration (TCP 445)

SMB (Server Message Block) is the Windows file/printer sharing protocol — historically one of the most exploited services:

```bash
# Enumerate shares, users, groups via smbclient
smbclient -L //192.168.1.100 -N         # List shares (null session)
smbclient //192.168.1.100/SHARE -N      # Connect to share

# enum4linux — comprehensive SMB enumeration
enum4linux -a 192.168.1.100

# Output includes:
# - OS version, workgroup, domain
# - Users and groups (via RPC)
# - Password policy
# - Shares and permissions
# - Printer information

# Nmap SMB scripts
nmap --script smb-enum-shares,smb-enum-users -p 445 192.168.1.100
nmap --script smb-security-mode -p 445 192.168.1.100

# CrackMapExec — modern SMB Swiss Army knife
crackmapexec smb 192.168.1.0/24         # Host discovery
crackmapexec smb 192.168.1.100 -u '' -p '' --shares  # Null session shares
```

### 3.2 SNMP Enumeration (UDP 161)

SNMP (Simple Network Management Protocol) — if community string is "public" (default), massive data exposure:

```bash
# snmpwalk — enumerate entire MIB tree
snmpwalk -v2c -c public 192.168.1.100

# Critical OIDs:
# 1.3.6.1.2.1.1.1.0  → System description (OS version)
# 1.3.6.1.2.1.1.5.0  → Hostname
# 1.3.6.1.2.1.25.4.2 → Running processes
# 1.3.6.1.2.1.25.6.3 → Installed software
# 1.3.6.1.4.1.77.1.2.25 → User accounts (Windows)

# onesixtyone — fast SNMP community string brute force
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt 192.168.1.100

# snmp-check — formatted SNMP enumeration
snmp-check 192.168.1.100 -c public
```

### 3.3 LDAP Enumeration (TCP 389/636)

If LDAP allows anonymous bind, entire AD structure may be exposed:

```bash
# ldapsearch — query LDAP/Active Directory
ldapsearch -x -H ldap://192.168.1.100 -b "DC=company,DC=com"

# Enumerate users
ldapsearch -x -H ldap://192.168.1.100 -b "DC=company,DC=com" "(objectClass=person)"

# Enumerate groups  
ldapsearch -x -H ldap://192.168.1.100 -b "DC=company,DC=com" "(objectClass=group)"

# Nmap script
nmap --script ldap-rootdse -p 389 192.168.1.100
```

### 3.4 RPC Enumeration (TCP 135/111)

```bash
# rpcclient — Windows RPC enumeration (if null session allowed)
rpcclient -U "" -N 192.168.1.100
rpcclient $> enumdomusers       # List domain users
rpcclient $> enumdomgroups      # List domain groups  
rpcclient $> getdompwinfo       # Password policy
rpcclient $> netshareenum       # Share enumeration

# rpcinfo — Linux/Unix RPC services
rpcinfo -p 192.168.1.100
```

---

## 4. Firewall Evasion Techniques

```bash
# Fragment packets (bypass simple packet filters)
nmap -f target

# Use custom MTU
nmap --mtu 24 target

# Decoy scan (hide in crowd of fake source IPs)
nmap -D RND:10 target              # 10 random decoys
nmap -D 10.0.0.1,10.0.0.2,ME target  # Specific decoys

# Source port spoofing (some firewalls allow DNS/HTTP source ports)
nmap --source-port 53 target

# Slow scan (evade rate-based IDS)
nmap -T0 target    # Paranoid: 5 min between probes
nmap -T1 target    # Sneaky: 15 sec between probes
nmap -T2 target    # Polite: 0.4 sec delay
nmap -T3 target    # Normal (default)
nmap -T4 target    # Aggressive (fast)
nmap -T5 target    # Insane (may miss results)

# Idle/Zombie scan (completely anonymous)
nmap -sI zombie_host target
```

---

## 5. Masscan — Internet-Scale Scanning

For very large networks, Masscan can scan the entire internet in ~6 minutes:

```bash
# Scan a /16 network at 100,000 packets/sec
masscan -p 80,443,22,3389 10.0.0.0/16 --rate=100000

# Output Nmap-compatible XML
masscan -p 1-65535 192.168.1.0/24 --rate=1000 -oX masscan.xml

# Combine: masscan for speed, nmap for depth
masscan -p 1-65535 192.168.1.0/24 --rate=1000 -oG masscan.gnmap
grep "open" masscan.gnmap | awk '{print $2}' | sort -u > live_hosts.txt
nmap -sV -sC -iL live_hosts.txt -oA full_scan
```

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Port scanning** | Probing ports to determine open/closed/filtered state |
| **Fingerprinting** | Identifying OS/software from network response characteristics |
| **NSE** | Nmap Scripting Engine — Lua-based scripts for automation |
| **SMB** | Server Message Block — Windows file sharing protocol |
| **SNMP** | Simple Network Management Protocol — device management (UDP 161) |
| **Null session** | Unauthenticated SMB connection (legacy Windows vulnerability) |
| **MIB** | Management Information Base — SNMP data structure |
| **Decoy scan** | Sends probes from multiple IPs to obscure scanner identity |

---

## Review Questions

!!! question "Self-Assessment"
    1. Explain the difference between a SYN scan and a TCP Connect scan. When would you choose each?
    2. A port shows as "filtered" in Nmap. What does this tell you about the network architecture?
    3. SNMP is running with community string "public" on a Windows server. What data can you extract?
    4. Describe how a zombie/idle scan achieves anonymity.
    5. You find an open LDAP port. Describe your enumeration methodology step by step.

---

## Further Reading

- 📖 *Hacking Exposed 7*, Chapter 3 — "Port Scanning"
- 📄 [Nmap Reference Guide](https://nmap.org/book/man.html) — official manual
- 📄 [NSE Documentation](https://nmap.org/nsedoc/) — all scripts catalog
- 📄 SANS: "Nmap Cheat Sheet"
- 📄 MITRE ATT&CK: T1046 — Network Service Scanning

---

*[← Week 2](week02.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 4 →](week04.md)*
