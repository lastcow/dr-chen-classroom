---
title: "Lab 12 — Digital Forensics: Disk Imaging & Evidence Analysis"
course: SCIA-472
week: 14
difficulty: "⭐⭐⭐"
estimated_time: "75–90 min"
tags:
  - digital-forensics
  - disk-imaging
  - sleuth-kit
  - chain-of-custody
  - timeline-analysis
  - evidence-preservation
---

# Lab 12 — Digital Forensics: Disk Imaging & Evidence Analysis

| Field | Value |
|---|---|
| **Course** | SCIA-472 — Ethical Hacking & Penetration Testing |
| **Week** | 14 |
| **Difficulty** | ⭐⭐⭐ |
| **Estimated Time** | 75–90 minutes |
| **Prerequisites** | Labs 01–11 completed; Docker running |

## Overview

Digital forensics **preserves and analyzes evidence** from compromised systems. The forensic process must be legally defensible — every action is documented, and evidence integrity is verified with cryptographic hashes.

Students create forensically sound disk images with `dd`, verify integrity with hash chains, analyze filesystem artifacts with **Sleuth Kit** (`fsstat`, `fls`, `icat`), and build a forensic timeline reconstructing an attacker's activity.

This lab covers:

- Forensically sound disk imaging with `dd`
- Hash-based chain of custody verification
- Filesystem metadata analysis with `fsstat`
- Hidden file discovery with `fls`
- File recovery from disk images with `icat`
- Forensic timeline reconstruction

---

!!! warning "Ethical Use — Read Before Proceeding"
    Digital forensics techniques applied to systems, storage devices, or accounts without authorization constitute unauthorized computer access. All evidence analysis in this lab is performed on disk images **you create**. Never image or analyze storage you do not own or have written authorization to examine.

---

## Part 1 — Forensically Sound Disk Imaging

The gold standard of digital forensics requires creating a **bit-for-bit copy** of the original evidence before any analysis. The original is hashed, sealed, and stored. All analysis occurs on the copy.

### Step 1.1 — Create a Simulated Evidence Disk

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq file e2fsprogs 2>/dev/null

# Create simulated disk with evidence
dd if=/dev/zero of=/tmp/evidence.img bs=1M count=20 2>&1
file /tmp/evidence.img
echo 'Disk image created: 20MB'

# Format with ext2 (simple, no journaling)
mkfs.ext2 -F /tmp/evidence.img 2>&1 | grep -E 'Creating|blocks|Filesystem'"
```

!!! success "Expected Output"
    `dd` creates a 20MB image from `/dev/zero`. `mkfs.ext2` formats it. The `file` command confirms it is a data file before formatting.

📸 **Screenshot checkpoint 12a** — Capture the `dd` output with block counts and the `mkfs.ext2` confirmation.

---

### Step 1.2 — Write Evidence Data and Document Original Hash

This step populates the disk image with simulated normal files and attacker artifacts, then documents the cryptographic hash of the **original unmodified evidence**.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq e2fsprogs file 2>/dev/null
dd if=/dev/zero of=/tmp/evidence.img bs=1M count=20 2>/dev/null
mkfs.ext2 -F /tmp/evidence.img 2>&1 | tail -2

# Mount and write evidence
mkdir -p /mnt/evidence
mount -o loop /tmp/evidence.img /mnt/evidence
mkdir -p /mnt/evidence/documents

# Create 'normal' files
echo 'Q4 2026 Budget: \$2.4M approved' > /mnt/evidence/documents/budget.txt
echo 'Meeting notes: Project Alpha discussion' > /mnt/evidence/documents/meeting_notes.txt

# Create 'suspicious' files (attacker artifacts)
mkdir -p /mnt/evidence/.hidden
echo '185.220.101.45:4444' > /mnt/evidence/.hidden/c2_config.txt
echo '#!/bin/bash\ncurl -s http://185.220.101.45/beacon' > /mnt/evidence/.hidden/beacon.sh
chmod +x /mnt/evidence/.hidden/beacon.sh

# Create and then delete a sensitive file (will be recoverable)
echo 'STOLEN_CREDENTIALS: admin:SuperSecret2024' > /mnt/evidence/creds.txt
rm /mnt/evidence/creds.txt  # Deleted but recoverable!

umount /mnt/evidence

# Hash BEFORE acquisition (original)
echo '=== ORIGINAL EVIDENCE HASH (pre-acquisition) ==='
md5sum /tmp/evidence.img
sha256sum /tmp/evidence.img"
```

!!! note "Deleted File Recovery"
    `creds.txt` is deleted with `rm`, but the data blocks remain on the disk until overwritten. Forensic tools can recover the content — this is demonstrated in Part 2.

📸 **Screenshot checkpoint 12a** *(continued)* — Capture the MD5 and SHA-256 hashes of the original evidence disk.

---

### Step 1.3 — Forensic Image Acquisition

The `dd` acquisition uses `conv=noerror,sync` to handle read errors gracefully — errors are padded with zeros rather than aborting, preserving the exact byte layout.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq e2fsprogs 2>/dev/null
dd if=/dev/zero of=/tmp/evidence.img bs=1M count=20 2>/dev/null
mkfs.ext2 -F /tmp/evidence.img 2>/dev/null
mkdir -p /mnt/evidence
mount -o loop /tmp/evidence.img /mnt/evidence
echo 'test evidence' > /mnt/evidence/testfile.txt
mkdir /mnt/evidence/.hidden
echo 'c2=185.220.101.45' > /mnt/evidence/.hidden/config.txt
umount /mnt/evidence

# Forensic acquisition with dd
echo '=== FORENSIC ACQUISITION ==='
dd if=/tmp/evidence.img of=/tmp/forensic_copy.img bs=4096 conv=noerror,sync 2>&1 | grep -E 'records|bytes|copied'

# Verify integrity
echo ''
echo '=== HASH VERIFICATION (Chain of Custody) ==='
ORIG_MD5=\$(md5sum /tmp/evidence.img | awk '{print \$1}')
COPY_MD5=\$(md5sum /tmp/forensic_copy.img | awk '{print \$1}')
echo \"Original: \$ORIG_MD5\"
echo \"Copy:     \$COPY_MD5\"
if [ \"\$ORIG_MD5\" = \"\$COPY_MD5\" ]; then
  echo 'VERIFIED: Hashes match - forensic copy is intact'
else
  echo 'ERROR: Hash mismatch - copy may be corrupted'
fi"
```

!!! success "Expected Output"
    ```
    VERIFIED: Hashes match - forensic copy is intact
    ```
    The original and forensic copy have identical MD5 hashes, proving the copy is an exact bit-for-bit duplicate.

📸 **Screenshot checkpoint 12b** — Capture the hash verification output showing both hashes and the `VERIFIED` message.

---

## Part 2 — Filesystem Analysis with Sleuth Kit

The Sleuth Kit provides forensic tools that operate directly on disk images without mounting them — avoiding any modification of MAC timestamps.

### Step 2.1 — Disk Image Metadata

`fsstat` provides filesystem-level metadata: type, block size, inode count, and volume information. This orients the analyst before beginning file-level examination.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sleuthkit e2fsprogs 2>/dev/null
dd if=/dev/zero of=/tmp/fs.img bs=1M count=10 2>/dev/null
mkfs.ext2 -F /tmp/fs.img 2>/dev/null
mkdir -p /mnt/fs && mount -o loop /tmp/fs.img /mnt/fs
echo 'Normal file' > /mnt/fs/normal.txt
echo 'Secret config: password=hunter2' > /mnt/fs/config.txt
mkdir /mnt/fs/.hidden && echo 'C2=evil.com' > /mnt/fs/.hidden/beacon.conf
umount /mnt/fs

echo '=== Filesystem metadata (fsstat) ==='
fsstat /tmp/fs.img 2>&1 | head -20"
```

!!! success "Expected Output"
    Shows filesystem type (ext2), block size (1024 bytes), total inode count, and volume creation time — all without mounting the image.

📸 **Screenshot checkpoint 12c** — Capture the `fsstat` output showing filesystem metadata.

---

### Step 2.2 — List All Files Including Hidden

`fls` (file listing) traverses the filesystem and lists all allocated and previously deleted files, including hidden directories that begin with `.`.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sleuthkit e2fsprogs 2>/dev/null
dd if=/dev/zero of=/tmp/fs.img bs=1M count=10 2>/dev/null
mkfs.ext2 -F /tmp/fs.img 2>/dev/null
mkdir -p /mnt/fs && mount -o loop /tmp/fs.img /mnt/fs
echo 'Normal file' > /mnt/fs/normal.txt
echo 'Secret: password=hunter2' > /mnt/fs/config.txt
mkdir /mnt/fs/.hidden && echo 'C2=evil.com' > /mnt/fs/.hidden/beacon.conf
umount /mnt/fs

echo '=== All files including hidden (fls) ==='
fls -r /tmp/fs.img 2>&1 | head -20"
```

!!! success "Expected Output"
    Lists all files and directories including the hidden `.hidden/` directory and its contents (`beacon.conf`). The `r` flag makes `fls` recursive.

📸 **Screenshot checkpoint 12d** — Capture the `fls` output showing both normal files and the hidden directory with `beacon.conf`.

---

### Step 2.3 — Read File Contents from Image

`icat` (inode cat) extracts file content using its inode number directly from the disk image — no mounting required. This is the forensically safe way to read file contents.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq sleuthkit e2fsprogs 2>/dev/null
dd if=/dev/zero of=/tmp/fs.img bs=1M count=10 2>/dev/null
mkfs.ext2 -F /tmp/fs.img 2>/dev/null
mkdir -p /mnt/fs && mount -o loop /tmp/fs.img /mnt/fs
echo 'Secret: password=hunter2' > /mnt/fs/config.txt
mkdir /mnt/fs/.hidden && echo 'C2=evil.com' > /mnt/fs/.hidden/beacon.conf
umount /mnt/fs

# Get inode number for config.txt
INODE=\$(fls /tmp/fs.img 2>/dev/null | grep config.txt | awk '{print \$2}' | tr -d ':')
echo \"Reading config.txt (inode \$INODE) directly from image:\"
icat /tmp/fs.img \$INODE 2>/dev/null"
```

!!! success "Expected Output"
    `icat` prints `Secret: password=hunter2` — the file content read directly from the disk image using the inode number, without mounting the filesystem.

📸 **Screenshot checkpoint 12e** — Capture the `fls` inode lookup and `icat` file content output.

---

## Part 3 — Forensic Timeline Analysis

A forensic timeline correlates events from multiple sources (MAC times, logs, network captures) into a single chronological record of attacker activity.

### Step 3.1 — Build Forensic Timeline

```bash
docker run --rm python:3.11-slim python3 -c "
from datetime import datetime, timedelta

base = datetime(2026, 4, 18, 9, 0, 0)

timeline = [
    (base,                         'login.log',   'admin LOGIN from 203.0.113.50'),
    (base + timedelta(minutes=5),  'web.log',     'GET /admin/config.php 200'),
    (base + timedelta(minutes=6),  'web.log',     'GET /admin/export?file=../etc/shadow 200'),
    (base + timedelta(minutes=7),  'filesystem',  'ACCESSED: /etc/shadow (MAC time)'),
    (base + timedelta(minutes=10), 'filesystem',  'CREATED: /tmp/.hidden/beacon.sh'),
    (base + timedelta(minutes=11), 'filesystem',  'CREATED: /tmp/.hidden/exfil_data.txt'),
    (base + timedelta(minutes=12), 'syslog',      'cron: new entry added for root'),
    (base + timedelta(minutes=15), 'auth.log',    'sshd: Accepted password for admin'),
    (base + timedelta(minutes=16), 'auth.log',    'sudo: admin : COMMAND=/bin/bash'),
    (base + timedelta(minutes=17), 'auth.log',    'FILE DELETED: /var/log/auth.log'),
    (base + timedelta(minutes=20), 'network',     'OUTBOUND: POST 185.220.101.45:443 (data exfil)'),
]

print('=== FORENSIC TIMELINE ===')
print(f'{\"Timestamp\":<25} {\"Source\":<12} {\"Event\"}')
print('-' * 75)
for ts, source, event in timeline:
    print(f'{ts.strftime(\"%Y-%m-%d %H:%M:%S\"):<25} {source:<12} {event}')

print()
print('=== FORENSIC SUMMARY ===')
print('Attack Duration: ~20 minutes from initial access to full compromise')
print('Entry Vector:    Web admin panel exploitation')
print('Escalation:      Path traversal \u2192 stolen shadow \u2192 SSH \u2192 sudo root')
print('Persistence:     Cron job + beacon.sh')
print('Exfiltration:    POST to 185.220.101.45:443 (encrypted)')
print('Evidence Wiped:  auth.log deleted at T+17min')
"
```

📸 **Screenshot checkpoint 12f** — Capture the full forensic timeline and summary.

---

## Cleanup

```bash
rm -f /tmp/evidence.img /tmp/forensic_copy.img /tmp/fs.img
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all six screenshots with your lab report. Each must be clearly labeled.

| # | Screenshot ID | Required Content |
|---|---|---|
| 1 | **12a** | `dd` output creating 20MB image + MD5/SHA-256 hashes of original |
| 2 | **12b** | Forensic acquisition output + `VERIFIED: Hashes match` message |
| 3 | **12c** | `fsstat` output showing filesystem type, block size, inode metadata |
| 4 | **12d** | `fls -r` output showing both normal files and hidden `.hidden/beacon.conf` |
| 5 | **12e** | `icat` file content recovery — inode number and `password=hunter2` visible |
| 6 | **12f** | Forensic timeline — all 11 events with timestamps and forensic summary |

---

## Chain of Custody Documentation

Include a chain of custody table in your lab report:

| Step | Action | Tool | Hash (MD5) | Notes |
|---|---|---|---|---|
| 1 | Evidence collected | dd | `<original_hash>` | Original disk — do not modify |
| 2 | Forensic copy made | dd conv=noerror,sync | `<copy_hash>` | Must match original |
| 3 | Hash verification | md5sum | Match confirmed | Integrity verified |
| 4 | Filesystem metadata | fsstat | — | Non-destructive read |
| 5 | File enumeration | fls -r | — | Hidden files found |
| 6 | File content extracted | icat | — | No MAC time modification |
| 7 | Timeline constructed | Python | — | Correlated from 4 sources |

---

## Reflection Questions

Answer each question in **150–200 words** in your lab report.

!!! question "Reflection 1 — Why Bit-for-Bit Copies Matter"
    You used `dd` with `conv=noerror,sync` to create the forensic image. Why must forensic images be **bit-for-bit copies including empty space**? What critical evidence can be found in disk areas that appear empty?

!!! question "Reflection 2 — Chain of Custody"
    You hashed the original evidence disk **before** imaging. In a real investigation, this generates a **hash manifest**. Explain chain of custody for digital evidence and why a hash mismatch between the original and copy would be **catastrophic for a court case**.

!!! question "Reflection 3 — Why Not Mount?"
    You read file contents from the disk image using `icat` without mounting the filesystem. Why is **mounting a forensic image potentially problematic**? What happens to MAC times (Modified, Accessed, Changed) when a filesystem is mounted, and why does this matter?

!!! question "Reflection 4 — Surviving Cleanup"
    The forensic timeline showed the attacker deleted `/var/log/auth.log`. But the timeline was still reconstructed from other sources. Name **three evidence sources** that survived the attacker's cleanup and explain why **centralized logging** is the most important technical control for forensic investigation.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (6 × ~7 pts each) | 40 pts |
    | Chain of custody documentation (complete table, all 7 steps) | 20 pts |
    | Reflection questions (4 × 10 pts each) | 40 pts |
    | **Total** | **100 pts** |
