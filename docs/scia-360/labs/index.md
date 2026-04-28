# SCIA-360 Hands-On Labs

**Course:** SCIA-360 · Operating System Security  
**Frostburg State University — Department of Computer Science & Information Technology**

---

## Lab Program Overview

This lab series provides **13 Docker-based hands-on exercises** that complement the SCIA-360 lecture materials. Each lab explores real OS security mechanisms directly — using `/proc`, `unshare`, `chroot`, `strace`, `capsh`, and more — all safely inside isolated Docker containers. No special hardware required.

!!! info "What You Need"
    - A computer running **Windows 10/11**, **macOS**, or **Linux**
    - **Docker Desktop** installed — [Download here](https://www.docker.com/products/docker-desktop)
    - A terminal (PowerShell on Windows, Terminal on macOS/Linux)
    - Approximately **1–1.5 hours** per lab

!!! tip "Lab Philosophy"
    SCIA-360 labs go deeper than SCIA-120. You will interact directly with kernel interfaces (`/proc/sys`), compile C programs, manipulate Linux namespaces, and exploit SUID misconfigurations in a controlled environment. The goal is to understand **why** OS security mechanisms exist by seeing them work — and fail.

---

## Lab Schedule

| Lab | Title | Topic | Ch. | Difficulty | Time |
|-----|-------|--------|-----|------------|------|
| [**Lab 01**](lab-01.md) | Exploring OS Security Layers — /proc, Kernel & User Space | OS Intro | 1 | ⭐ | 45–60 min |
| [**Lab 02**](lab-02.md) | Process Security — Credentials, /proc & Signals | Process Mgmt | 2 | ⭐ | 45–60 min |
| [**Lab 03**](lab-03.md) | Memory Protections — ASLR, Stack Canaries & NX | Memory Security | 3 | ⭐⭐ | 60–75 min |
| [**Lab 04**](lab-04.md) | File System Security — ACLs, SUID, SGID & Sticky Bit | FS Security | 4 | ⭐ | 45–60 min |
| [**Lab 05**](lab-05.md) | PAM & Password Policy — Authentication Hardening | OS Auth | 5 | ⭐⭐ | 60–75 min |
| [**Lab 06**](lab-06.md) | Linux Capabilities — Dropping Root, Least Privilege | Access Control | 6 | ⭐⭐ | 45–60 min |
| [**Lab 07**](lab-07.md) | Syscall Filtering with seccomp | Security Policies | 7 | ⭐⭐ | 45–60 min |
| [**Lab 08**](lab-08.md) | chroot Jail — Filesystem Isolation the Old Way | Sandboxing | 8 | ⭐⭐ | 45–60 min |
| [**Lab 09**](lab-09.md) | Linux Namespaces — Building Blocks of Containers | Containerization | 8 | ⭐⭐ | 60–75 min |
| [**Lab 10**](lab-10.md) | Privilege Escalation via SUID Binaries | Vulnerabilities | 9 | ⭐⭐ | 60–75 min |
| [**Lab 11**](lab-11.md) | System Audit Logging with inotifywait | Linux Architecture | 11 | ⭐⭐ | 60–75 min |
| [**Lab 12**](lab-12.md) | OS Hardening — CIS Benchmark Checks | Hardening | 14 | ⭐⭐ | 60–75 min |
| [**Lab 13**](lab-13.md) | Capstone — Build, Harden & Audit a Containerized System | All topics | — | ⭐⭐⭐ | 90–120 min |

---

## Learning Progression

```
Labs 01–04          Labs 05–07          Labs 08–09          Labs 10–12          Lab 13
Kernel & /proc  →   Auth & Policy   →   Isolation       →   Attacks &       →   Capstone
Process, Memory,    PAM, Capabilities,  chroot,             Defenses            Integration
File System         seccomp             Namespaces          SUID, Logging,
                                                            Hardening
```

---

## Assessment Structure

Each lab is worth **100 points**:

| Component | Points |
|-----------|--------|
| Screenshot submission (6–10 per lab, labeled) | 40 |
| Analysis table or comparison exercise | 20 |
| Reflection questions (4 per lab) | 40 |

Lab 13 (Capstone) uses a modified rubric: Screenshots+table (30) + Hardening applied (20) + Final audit score (20) + Essay (30).

---

## Difficulty Guide

| Symbol | Level | Description |
|--------|-------|-------------|
| ⭐ | Beginner | Basic Linux commands, reading /proc output |
| ⭐⭐ | Intermediate | C compilation, namespace manipulation, exploitation |
| ⭐⭐⭐ | Advanced | Integrates all prior labs into a full hardening exercise |

---

## Key Docker Flags Used in This Course

Some labs require elevated Docker privileges to access kernel features:

| Flag | Labs | Why needed |
|------|------|-----------|
| `--privileged` | 09 | `unshare` for namespace manipulation |
| `--cap-add SYS_PTRACE` | 07 | `strace` to trace syscalls |
| `--cap-add NET_ADMIN` | 06 | iptables and network configuration |
| `--security-opt seccomp=unconfined` | 07 | Disable seccomp to observe its effect |
| `--cap-drop ALL` | 06 | Demonstrate zero-capability baseline |

!!! warning "Privilege Flags"
    Flags like `--privileged` should **never** be used in production containers. They are used here only to observe how kernel features work. Part of the learning is understanding *why* these flags are dangerous.

---

## Technical Troubleshooting

??? question "unshare fails with 'unshare: unshare failed: Operation not permitted'"
    The lab requires `--privileged`: `docker run --rm --privileged ubuntu:22.04 bash`

??? question "strace says 'strace: attach: ptrace(PTRACE_SEIZE, PID): Operation not permitted'"
    Add `--cap-add SYS_PTRACE --security-opt seccomp=unconfined` to the docker run command.

??? question "gcc not found after apt-get install"
    Make sure you are running all commands in the **same** `docker run` session. If you exit and re-enter, run `apt-get install` again.

??? question "chroot fails with 'chroot: cannot change root directory: No such file or directory'"
    Ensure you created the jail directory and copied all required files and libraries first (Part 1 of Lab 08).

??? question "A port is already in use on the host"
    Change the host port: `-p 9090:80` instead of `-p 8080:80`.

---

*Labs authored for SCIA-360 · Frostburg State University · Department of Computer Science & Information Technology · Spring 2026*
