# SCIA-120 Hands-On Labs

**Course:** SCIA-120 · Introduction to Secure Computing  
**Frostburg State University — Department of Computer Science & Information Technology**

---

## Lab Program Overview

This lab series provides **13 hands-on, Docker-based exercises** that complement the SCIA-120 lecture materials. Each lab is self-contained, requires no special hardware beyond a personal computer, and uses Docker containers to create safe, isolated environments for exploring real security tools and techniques.

!!! info "What You Need"
    - A computer running **Windows 10/11**, **macOS**, or **Linux**
    - **Docker Desktop** installed — [Download here](https://www.docker.com/products/docker-desktop)
    - A terminal (PowerShell on Windows, Terminal on macOS/Linux)
    - Approximately **1–2 hours** per lab

!!! tip "Lab Philosophy"
    These labs follow a **learn-by-doing** approach. You will run real security tools against real (but isolated) systems. The goal is not just to complete the steps, but to **understand why** each tool and technique works the way it does.

---

## Lab Schedule

| Lab | Title | Topic | Difficulty | Time |
|-----|-------|--------|------------|------|
| [Lab 01](lab-01.md) | Docker Basics & the CIA Triad | InfoSec Fundamentals | ⭐ | 45–60 min |
| [Lab 02](lab-02.md) | Linux File Permissions & OS Hardening | OS Security | ⭐ | 45–60 min |
| [Lab 03](lab-03.md) | Password Storage: Never Store Plaintext | Cryptography | ⭐ | 45–60 min |
| [Lab 04](lab-04.md) | Network Reconnaissance with Nmap | Network Security | ⭐ | 45–60 min |
| [Lab 05](lab-05.md) | Packet Capture & Traffic Analysis | Network Security | ⭐⭐ | 45–60 min |
| [Lab 06](lab-06.md) | Firewall Rules with iptables | Network Security | ⭐⭐ | 45–60 min |
| [Lab 07](lab-07.md) | Encryption in Practice with OpenSSL | Cryptography | ⭐⭐ | 45–60 min |
| [Lab 08](lab-08.md) | Securing a Web Server with HTTPS | Internet Security | ⭐⭐ | 60–75 min |
| [Lab 09](lab-09.md) | Web Vulnerabilities: SQL Injection | Secure Programming | ⭐⭐ | 60–75 min |
| [Lab 10](lab-10.md) | Malware Sandbox: Safe Behavior Analysis | Malware Analysis | ⭐⭐ | 45–60 min |
| [Lab 11](lab-11.md) | SSH Keys & Access Control | Authentication | ⭐⭐ | 60–75 min |
| [Lab 12](lab-12.md) | Log Analysis & Anomaly Detection | Security Practices | ⭐⭐ | 60–75 min |
| [Lab 13](lab-13.md) | Capstone: Harden a Containerized Application | All Topics | ⭐⭐⭐ | 90–120 min |
| [Lab — BST in Java](lab-java-bst.md) | Binary Search Tree in Java | Data Structures | ⭐⭐ | 60–75 min |

---

## Learning Progression

The labs are organized to build on one another:

```
Labs 01–04   →   Labs 05–08   →   Labs 09–12   →   Lab 13
Foundation       Networking &      Application &     Capstone
& OS Basics      Cryptography      Detection         Integration
```

Labs 01–04 introduce Docker, Linux fundamentals, and basic cryptography. Labs 05–08 cover network security and encryption in practice. Labs 09–12 tackle application vulnerabilities, malware analysis, and incident detection. Lab 13 integrates everything into a real hardening exercise.

---

## Assessment Structure

Each lab is worth **100 points**:

| Component | Points |
|-----------|--------|
| Screenshot submission (minimum 6–10 per lab) | 40 |
| Analysis/mapping table or code comparison | 20 |
| Reflection questions (3–4 per lab) | 40 |

All screenshots must be:
- Clearly labeled (e.g., `screenshot-03d-hash-comparison.png`)
- Show your terminal — not generic internet images
- Submitted through the course LMS by the due date

---

## Difficulty Guide

| Symbol | Level | Description |
|--------|-------|-------------|
| ⭐ | Beginner | No prior Linux or networking experience needed |
| ⭐⭐ | Beginner–Intermediate | Basic command-line comfort helpful |
| ⭐⭐⭐ | Intermediate | All prior labs should be completed first |

---

## Technical Troubleshooting

??? question "Docker command says 'permission denied'"
    On Linux, add your user to the docker group: `sudo usermod -aG docker $USER` then log out and back in.

??? question "A Docker image fails to pull"
    Check your internet connection. If on campus, ensure the campus network allows Docker Hub access. You can also try pulling from a different network.

??? question "A port is already in use (e.g., port 8080)"
    Another application is using that port. Either stop the other service, or modify the Docker `-p` flag to use a different host port (e.g., `-p 9090:80` instead of `-p 8080:80`).

??? question "Container commands run but nothing seems to happen"
    Run `docker ps` to check if the container is running. Run `docker logs <container-name>` to see error output.

??? question "I accidentally left a container running"
    Run `docker ps -a` to list all containers, then `docker stop <name>` and `docker rm <name>`. To clean up everything: `docker system prune -f`.

---

## Academic Integrity

!!! warning "Important"
    All lab work must be your own. Screenshots must be from your own computer — do not copy screenshots from classmates or the internet. The tools and techniques in these labs must only be used against the local Docker containers in the lab environment. Scanning, attacking, or probing any system you do not own is illegal.

    Review FSU's Academic Integrity Policy before beginning the labs.

---

## Quick Start

Ready to begin? Start with [Lab 01 →](lab-01.md)

```bash
# Verify Docker is installed and running
docker --version
docker run --rm hello-world
```

If `hello-world` runs successfully, you are ready to start Lab 01.

---

*Labs authored for SCIA-120 · Frostburg State University · Spring 2026*
