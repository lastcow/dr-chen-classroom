# Lab 01 — Docker Basics & the CIA Triad

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** InfoSec Fundamentals  
**Difficulty:** ⭐ Beginner  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 1 — Introduction to Information Security

---

## Overview

In this lab you will install and run your first Docker containers while connecting hands-on actions to the three foundational principles of information security: **Confidentiality**, **Integrity**, and **Availability** (the CIA Triad). You will see how containers provide isolation (Confidentiality), how file hashing verifies data has not changed (Integrity), and how a running service demonstrates Availability.

---

## Learning Objectives

By the end of this lab, you will be able to:

1. Pull and run a Docker container from Docker Hub.
2. Explain what process isolation means in container terms.
3. Demonstrate Confidentiality using container namespace isolation.
4. Demonstrate Integrity by hashing a file and detecting changes.
5. Demonstrate Availability by running and health-checking a web service.

---

## Prerequisites

- A computer running Windows 10/11, macOS, or Linux.
- Docker Desktop installed ([https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)).
- A terminal (PowerShell on Windows, Terminal on macOS/Linux).

> **Tip:** Open your terminal and run `docker --version` to confirm Docker is installed before starting.

---

## Part 1 — Your First Container

### Step 1.1 — Pull the Ubuntu Image

```bash
docker pull ubuntu:22.04
```

You should see Docker downloading layers. This is the base Linux image you will use throughout the lab.

**Expected output:**
```
22.04: Pulling from library/ubuntu
...
Status: Downloaded newer image for ubuntu:22.04
```

📸 **Screenshot checkpoint:** Take a screenshot showing the completed pull output.

---

### Step 1.2 — Run Your First Container

```bash
docker run --rm -it ubuntu:22.04 bash
```

This starts an interactive Ubuntu shell inside a container. You are now *inside* the container. Notice you are `root` — but only inside this isolated environment.

```bash
whoami
hostname
ls /
```

**Expected output:**
```
root
<random_container_id>
bin  boot  dev  etc  home  lib  ...
```

📸 **Screenshot checkpoint:** Take a screenshot of the container shell showing `whoami` and `hostname` output.

Type `exit` to leave the container.

---

## Part 2 — Confidentiality: Container Isolation

Confidentiality means information is accessible only to those authorized to see it. Containers enforce confidentiality through **process namespace isolation** — processes inside one container cannot see processes in another.

### Step 2.1 — Start a Background Container

In **Terminal 1**, run:

```bash
docker run --rm --name secret-server -d ubuntu:22.04 sleep 3600
```

### Step 2.2 — Check What a Second Container Can See

In **Terminal 2**, run a second container and try to inspect the first:

```bash
docker run --rm -it ubuntu:22.04 bash
```

Inside this second container:

```bash
ps aux
```

**Observe:** You will see only processes inside *this* container. The `sleep 3600` process from the first container is **not visible**. This is namespace isolation enforcing Confidentiality.

📸 **Screenshot checkpoint:** Take a screenshot of the `ps aux` output showing only container-local processes.

Type `exit` to leave the second container.

### Step 2.3 — Clean Up

```bash
docker stop secret-server
```

---

## Part 3 — Integrity: Detecting Tampering with File Hashing

Integrity means data has not been altered without authorization. One practical way to verify integrity is **cryptographic hashing** — if even one character changes, the hash changes completely.

### Step 3.1 — Create a File and Hash It

```bash
docker run --rm -it ubuntu:22.04 bash
```

Inside the container:

```bash
echo "This is my original document." > document.txt
sha256sum document.txt
```

**Expected output (example):**
```
6f7b3e...  document.txt
```

Copy down the hash value — this is your "known good" fingerprint.

### Step 3.2 — Tamper with the File and Re-Hash

```bash
echo "This document has been modified." > document.txt
sha256sum document.txt
```

**Observe:** The hash is completely different, even though the file looks similar. This is how **integrity verification** works — any change produces a detectable difference.

📸 **Screenshot checkpoint:** Take a screenshot showing both hash outputs side by side, clearly different.

Type `exit` to leave the container.

---

## Part 4 — Availability: Running a Web Service

Availability means systems and data are accessible when needed by authorized users. A web server that responds to requests demonstrates Availability.

### Step 4.1 — Run an Nginx Web Server Container

```bash
docker run --rm --name web-server -d -p 8080:80 nginx:alpine
```

### Step 4.2 — Verify It Is Available

```bash
curl http://localhost:8080
```

**Expected output:**
```html
<!DOCTYPE html>
<html>
...Welcome to nginx!...
</html>
```

Or open your browser and navigate to `http://localhost:8080`. You should see the Nginx welcome page.

📸 **Screenshot checkpoint:** Take a screenshot of either the `curl` output or the browser showing the Nginx welcome page.

### Step 4.3 — Simulate Unavailability

Stop the container:

```bash
docker stop web-server
```

Try to access it again:

```bash
curl http://localhost:8080
```

**Observe:** The service is now unavailable — `curl` will fail with a connection refused error. This simulates a denial-of-service scenario.

📸 **Screenshot checkpoint:** Take a screenshot of the failed `curl` command.

---

## Part 5 — Review: Mapping Actions to CIA

Fill out the table below as part of your submission:

| CIA Principle | What You Did in This Lab | Why It Demonstrates That Principle |
|---------------|--------------------------|-------------------------------------|
| Confidentiality | | |
| Integrity | | |
| Availability | | |

---

## Cleanup

Remove any remaining containers and images:

```bash
docker ps -a
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

Submit **all of the following screenshots** to the course LMS:

- [ ] `screenshot-01a` — Docker pull completed for ubuntu:22.04
- [ ] `screenshot-01b` — Container shell showing `whoami` and `hostname`
- [ ] `screenshot-01c` — `ps aux` inside isolated container (Part 2)
- [ ] `screenshot-01d` — Both SHA-256 hash values (original and tampered)
- [ ] `screenshot-01e` — Nginx welcome page or successful `curl` output
- [ ] `screenshot-01f` — Failed `curl` after container stopped

### Reflection Questions

Answer the following questions in **3–5 sentences each** and submit with your screenshots:

1. In your own words, what is the CIA Triad and why does it matter in information security?
2. How does Docker container isolation relate to the principle of Confidentiality? Give a specific example from this lab.
3. Why is hashing useful for detecting data tampering? What would happen if an attacker changed a single character in a file and re-hashed it?
4. A web server that goes down during peak hours violates which CIA principle? What are some real-world consequences of this?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - CIA Triad mapping table completed: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
