---
title: "Lab 07 — Syscall Filtering with seccomp"
course: SCIA-360
topic: Security Policies
chapter: 7
difficulty: "⭐⭐"
time: "45–60 min"
reading: "Chapter 7 — Kernel Security Policies"
---

# Lab 07 — Syscall Filtering with seccomp

| | |
|---|---|
| **Course** | SCIA-360 OS Security |
| **Topic** | Security Policies |
| **Chapter** | 7 |
| **Difficulty** | ⭐⭐ Intermediate |
| **Estimated Time** | 45–60 minutes |
| **Prerequisites** | Lab 06 completed; Docker installed and running |

---

## Overview

**seccomp** (Secure Computing Mode) is a Linux kernel facility that filters system calls before they reach the kernel. Docker applies a default seccomp profile that **blocks ~44 dangerous syscalls** from every container, regardless of capabilities or user ID.

In this lab you will:

- Verify seccomp filter status via `/proc/self/status`
- Observe syscalls blocked by the default Docker profile
- Use `strace` to trace exactly which syscalls real programs make
- Build a syscall audit table classifying calls as allowed or blocked

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (07a – 07g) | 40 pts |
    | Syscall classification table (completed — syscall name, number, allowed/blocked, reason) | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Background: The Three Layers of Container Isolation

| Layer | What It Restricts |
|-------|-----------------|
| **Namespaces** | Visibility — processes, network interfaces, mount points, user IDs |
| **Capabilities** | Privileged kernel operations a process may perform |
| **seccomp** | Which system call numbers the process may invoke at all |

seccomp operates at the lowest layer — the BPF (Berkeley Packet Filter) program runs in the kernel *before* the system call handler. Even if a capability check would have allowed an operation, seccomp can block the syscall entirely.

---

## Part 1 — seccomp Status

### Step 1.1 — Verify the Filter is Active

```bash
docker run --rm ubuntu:22.04 bash -c "grep Seccomp /proc/self/status"
```

**Expected output:**

```
Seccomp:        2
Seccomp_filters: 1
```

**seccomp mode values:**

| Mode | Meaning |
|------|---------|
| `0` | Disabled — all syscalls pass through |
| `1` | Strict — only `read`, `write`, `exit`, `sigreturn` allowed |
| `2` | Filter — a BPF program decides per-syscall (Docker default) |

📸 **Screenshot checkpoint 07a:** Terminal output showing `Seccomp: 2` and `Seccomp_filters: 1`.

---

### Step 1.2 — Disable seccomp and Compare

```bash
docker run --rm --security-opt seccomp=unconfined ubuntu:22.04 bash -c \
  "grep Seccomp /proc/self/status"
```

**Expected output:**

```
Seccomp:        0
Seccomp_filters: 0
```

📸 **Screenshot checkpoint 07b:** `Seccomp: 0` output, ideally placed next to or below 07a for direct comparison.

!!! warning "Never use seccomp=unconfined in production"
    Disabling seccomp removes the last kernel-level syscall barrier. The flag exists for debugging and for cases where a custom profile will be applied — not for leaving containers unfiltered in a live environment.

---

## Part 2 — Observing Blocked Syscalls

### Step 2.1 — `reboot` Syscall Blocked by Default Profile

```bash
docker run --rm python:3.11-slim python3 -c "
import ctypes, ctypes.util, ctypes as ct
libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
ct.set_errno(0)
result = libc.syscall(169, 0xfee1dead, 0x28121969, 0x01234567, 0)
errno_val = ct.get_errno()
print(f'reboot syscall result={result}, errno={errno_val}')
if errno_val == 1: print('EPERM: blocked by seccomp!')
"
```

**Expected output:**

```
reboot syscall result=-1, errno=1
EPERM: blocked by seccomp!
```

Syscall 169 (`reboot`) is in Docker's deny list. The kernel returns `-1` with `errno = EPERM` (1 = Operation not permitted) before any reboot logic executes.

📸 **Screenshot checkpoint 07c:** `result=-1, errno=1` and `EPERM: blocked by seccomp!` clearly visible.

---

### Step 2.2 — Benign Syscalls Are Allowed

```bash
docker run --rm python:3.11-slim python3 -c "
import ctypes, ctypes.util
libc = ctypes.CDLL(ctypes.util.find_library('c'))
pid = libc.getpid()
uid = libc.getuid()
print(f'getpid()={pid}  getuid()={uid}  (both allowed)')
"
```

**Expected output:** `getpid()=1  getuid()=0  (both allowed)`

`getpid` (syscall 39) and `getuid` (syscall 102) are harmless introspection calls that every process needs — they pass through the seccomp filter without restriction.

📸 **Screenshot checkpoint 07d:** `getpid()` and `getuid()` values printed with `(both allowed)` suffix.

---

## Part 3 — `strace`: Tracing Syscalls in Real Time

### Step 3.1 — Trace `ls` with `strace`

```bash
docker run --rm --cap-add SYS_PTRACE --security-opt seccomp=unconfined ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq strace 2>/dev/null
strace -e trace=openat,read,write,getdents64 ls /tmp 2>&1 | head -12"
```

**Expected output:** Lines like:

```
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libselinux.so.1", ...) = 3
getdents64(3, /* 0 entries */, 32768)   = 0
```

`strace` intercepts every syscall the traced process makes. Filtered here to just four syscall types, you can see `ls` must: open shared libraries, then call `getdents64` to read directory entries.

!!! warning "SYS_PTRACE + seccomp=unconfined"
    `strace` requires `CAP_SYS_PTRACE` to attach to processes and needs seccomp disabled so `ptrace` syscalls aren't blocked. Use this combination only in controlled lab environments — never in production.

📸 **Screenshot checkpoint 07e:** `strace` output showing at least `openat` and `getdents64` calls.

---

### Step 3.2 — Trace Python Reading a File

```bash
docker run --rm --cap-add SYS_PTRACE --security-opt seccomp=unconfined python:3.11-slim bash -c "
apt-get install -y -qq strace 2>/dev/null
echo 'import sys; print(open(\"/etc/hostname\").read().strip())' > /tmp/read_file.py
strace -e trace=openat,read python3 /tmp/read_file.py 2>&1 | grep -E 'openat.*hostname|^[a-f0-9]' | head -5"
```

**Expected output:** At least one `openat` call referencing `/etc/hostname`, confirming that Python's `open()` translates directly to an `openat` syscall.

📸 **Screenshot checkpoint 07f:** `strace` output showing the `openat` call for `/etc/hostname`.

---

## Part 4 — Syscall Audit

### Step 4.1 — Automated Syscall Allow/Block Test

```bash
docker run --rm python:3.11-slim python3 -c "
import ctypes, ctypes.util, ctypes as ct
libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)

syscalls = [
    ('getpid',      39),
    ('getuid',      102),
    ('time',        201),
    ('reboot',      169),
    ('kexec_load',  246),
    ('syslog',      103),
]

for name, num in syscalls:
    ct.set_errno(0)
    result = libc.syscall(num, 0, 0, 0, 0)
    errno_val = ct.get_errno()
    blocked = errno_val == 1
    status = 'BLOCKED (seccomp)' if blocked else 'allowed'
    print(f'{name:15} (#{num:3}): {status}')
"
```

**Expected output:**

```
getpid          (# 39): allowed
getuid          (#102): allowed
time            (#201): allowed
reboot          (#169): BLOCKED (seccomp)
kexec_load      (#246): BLOCKED (seccomp)
syslog          (#103): allowed   ← may vary by kernel config
```

📸 **Screenshot checkpoint 07f:** Full six-line syscall audit table output.

---

### Step 4.2 — Default Profile vs. `seccomp=unconfined`

```bash
echo '=== Default seccomp ==='
docker run --rm python:3.11-slim python3 -c "
import ctypes, ctypes.util, ctypes as ct
libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
ct.set_errno(0); libc.syscall(169,0xfee1dead,0x28121969,0x01234567,0)
print('reboot:', 'BLOCKED' if ct.get_errno()==1 else 'reached kernel')"

echo '=== seccomp=unconfined ==='
docker run --rm --security-opt seccomp=unconfined python:3.11-slim python3 -c "
import ctypes, ctypes.util, ctypes as ct
libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
ct.set_errno(0); libc.syscall(169,0xfee1dead,0x28121969,0x01234567,0)
errno_v = ct.get_errno()
print('reboot:', 'BLOCKED (caps)' if errno_v==1 else f'reached kernel errno={errno_v}')"
```

**Note:** In the unconfined case the reboot syscall *reaches the kernel* but is still blocked by capabilities (`CAP_SYS_BOOT` is not in Docker's default capability set). This demonstrates that capabilities and seccomp are **complementary but independent** layers — removing seccomp does not remove capability checks.

📸 **Screenshot checkpoint 07g:** Both `=== Default seccomp ===` and `=== seccomp=unconfined ===` sections visible, showing the difference in where the block occurs.

---

### Syscall Classification Table

Complete and submit this table with your lab report:

| Syscall | Number | Default Profile | Reason |
|---------|--------|-----------------|--------|
| `getpid` | 39 | ✅ Allowed | Every process needs its own PID |
| `getuid` | 102 | ✅ Allowed | Basic identity introspection |
| `time` | 201 | ✅ Allowed | Read-only clock access |
| `reboot` | 169 | ❌ Blocked | Could reboot or halt the host |
| `kexec_load` | 246 | ❌ Blocked | Load a new kernel — severe host escape vector |
| `syslog` | 103 | ✅ / ❌ Varies | Read kernel ring buffer |
| *(add two more)* | | | |

---

## Cleanup

```bash
docker system prune -f
```

---

## Assessment

### Screenshot Checklist

| ID | Required Content |
|----|-----------------|
| **07a** | `Seccomp: 2` and `Seccomp_filters: 1` from `/proc/self/status` |
| **07b** | `Seccomp: 0` with `seccomp=unconfined` |
| **07c** | `reboot` syscall returning `result=-1, errno=1` + `EPERM: blocked by seccomp!` |
| **07d** | `getpid()` and `getuid()` returning valid values with `(both allowed)` |
| **07e** | `strace` output showing `openat` and `getdents64` calls from `ls` |
| **07f** | Full six-line syscall audit table (allowed vs. blocked) |
| **07g** | Default seccomp `BLOCKED` vs. unconfined `reached kernel` comparison |

---

### Reflection Questions

!!! warning "Submission requirement"
    Answer each question in **complete paragraphs** (minimum 4–6 sentences each). Include technical specifics — syscall names, error codes, and mechanism details where relevant.

**Q1.** What is a system call? Explain the concept using an analogy — a user-space program cannot directly access hardware; it must ask the kernel on its behalf. Using that analogy, explain seccomp's role as the *gatekeeper* of that conversation. How does the BPF program implement that gatekeeping at the kernel level?

**Q2.** Docker's default seccomp profile blocks syscalls including `reboot`, `kexec_load`, and `create_module`. An application container running a Python web service will **never** legitimately need any of these. Explain why each one exists in the kernel and what specific damage an attacker could cause if they were available inside a compromised container.

**Q3.** `strace` revealed that `ls` makes `openat()` and `getdents64()` syscalls — not the high-level `readdir()` C function you might expect. Why would a security analyst use `strace` when investigating a suspicious binary found on a compromised system? What would they be looking for, and what kind of malicious behaviour might be revealed in the syscall trace?

**Q4.** seccomp, Linux capabilities, and namespaces each contribute a distinct layer to container isolation. Explain precisely what each layer restricts and why all three are necessary — in other words, describe the specific attacks that would be possible if any single layer were removed even while the other two remained in place.
