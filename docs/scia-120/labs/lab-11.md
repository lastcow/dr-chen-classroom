# Lab 11 — SSH Keys & Access Control

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Authentication — Keys, Access Control & Brute-Force Defense  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 60–75 minutes  
**Related Reading:** Chapter 11 — Authentication and Access Control

---

## Overview

SSH (Secure Shell) is the standard protocol for secure remote server access. Using SSH with **key-based authentication** instead of passwords is vastly more secure — a cryptographic key pair is exponentially harder to brute-force than a password. In this lab you will set up SSH key authentication between two Docker containers, disable password login, and configure basic brute-force protection.

---

## Learning Objectives

1. Generate an SSH public/private key pair.
2. Configure SSH key-based authentication on a server.
3. Demonstrate that password authentication and key authentication behave differently.
4. Disable password-based SSH login.
5. Observe SSH brute-force login attempts in logs.

---

## Prerequisites

- Docker Desktop installed and running.
- Lab 07 (Cryptography) helpful but not required.

---

## Part 1 — Set Up the SSH Lab Environment

### Step 1.1 — Create a Docker Network

```bash
docker network create ssh-lab
```

### Step 1.2 — Start the SSH Server Container

```bash
docker run -d \
  --name ssh-server \
  --network ssh-lab \
  --hostname sshserver \
  linuxserver/openssh-server:latest \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=America/New_York \
  -e PASSWORD_ACCESS=true \
  -e USER_PASSWORD=weakpassword \
  -e USER_NAME=student
```

> Note: If `linuxserver/openssh-server` is slow to pull, use the alternative below.

**Alternative (pure Ubuntu SSH server):**

```bash
docker run -d \
  --name ssh-server \
  --network ssh-lab \
  --hostname sshserver \
  ubuntu:22.04 bash -c "
    apt-get update -qq && apt-get install -y -qq openssh-server
    useradd -m -s /bin/bash student
    echo 'student:weakpassword' | chpasswd
    mkdir -p /run/sshd
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
    /usr/sbin/sshd -D
  "
```

### Step 1.3 — Start the SSH Client Container

```bash
docker run -d \
  --name ssh-client \
  --network ssh-lab \
  ubuntu:22.04 sleep 3600
```

```bash
docker exec -it ssh-client bash -c "
apt-get update -qq && apt-get install -y -qq openssh-client sshpass
echo 'SSH client ready.'
"
```

### Step 1.4 — Get the Server's IP

```bash
docker inspect ssh-server | grep '"IPAddress"' | tail -1
```

Note this IP — use it in all subsequent steps (referred to as `<SERVER_IP>`).

📸 **Screenshot checkpoint:** Take a screenshot of the server IP address.

---

## Part 2 — Password-Based SSH Login (Weak)

### Step 2.1 — Connect with Password

```bash
docker exec -it ssh-client bash
```

Inside the client container, use `sshpass` to supply the password non-interactively (required in a terminal-in-terminal scenario):

```bash
sshpass -p 'weakpassword' ssh -o StrictHostKeyChecking=no student@<SERVER_IP>
```

> **What is sshpass?** It passes a password to SSH non-interactively. In a real environment you would type the password at the prompt — `sshpass` just automates it for lab purposes.

```bash
whoami
hostname
pwd
```

📸 **Screenshot checkpoint:** Take a screenshot of the successful SSH login with password, showing `whoami` and `hostname`.

```bash
exit
```

---

## Part 3 — Generate SSH Key Pair

Still inside the client container:

### Step 3.1 — Generate an RSA Key Pair

```bash
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
```

The `-N ""` creates a key with no passphrase (for lab simplicity).

```bash
ls -la /root/.ssh/
cat /root/.ssh/id_rsa.pub
```

📸 **Screenshot checkpoint:** Take a screenshot showing the key files and the public key content.

**Understand the files:**
- `id_rsa` — **PRIVATE KEY** — never share this. Keep it secret.
- `id_rsa.pub` — **PUBLIC KEY** — share this with servers you want to access.

### Step 3.2 — Copy the Public Key to the Server

```bash
ssh-copy-id -i /root/.ssh/id_rsa.pub -o StrictHostKeyChecking=no student@<SERVER_IP>
```

Enter the password `weakpassword` when prompted.

📸 **Screenshot checkpoint:** Take a screenshot of the successful `ssh-copy-id` output.

---

## Part 4 — Key-Based Authentication (Strong)

### Step 4.1 — Connect Without Password

```bash
ssh -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no student@<SERVER_IP>
```

**No password prompt!** The server recognized your key and let you in automatically.

```bash
echo "I logged in with a key — no password!" 
whoami
exit
```

📸 **Screenshot checkpoint:** Take a screenshot of the passwordless SSH login.

---

## Part 5 — Disable Password Authentication

Requiring key-only auth prevents password brute-force attacks entirely.

### Step 5.1 — Modify SSH Server Configuration

```bash
docker exec ssh-server bash -c "
echo 'PasswordAuthentication no' >> /etc/ssh/sshd_config
grep '^PasswordAuthentication' /etc/ssh/sshd_config
"
```

### Step 5.2 — Reload SSH Service

Use `kill -HUP` to reload config **without** stopping the container:

```bash
docker exec ssh-server bash -c "
kill -HUP \$(pgrep -f 'sshd -D')
echo 'SSH config reloaded (password auth disabled)'
"
sleep 2
```

### Step 5.3 — Verify Password Login Is Now Blocked

Back in the client container, try connecting without your key:

```bash
docker exec -it ssh-client bash -c "
ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no \
    -o StrictHostKeyChecking=no student@<SERVER_IP>
"
```

**Expected result:** `Permission denied (publickey)` — password login is disabled.

📸 **Screenshot checkpoint:** Take a screenshot of the permission denied message when trying password login.

### Step 5.4 — Verify Key Login Still Works

```bash
docker exec -it ssh-client bash -c "
ssh -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no student@<SERVER_IP> 'echo Key login works!'
"
```

📸 **Screenshot checkpoint:** Take a screenshot of successful key login after disabling password auth.

---

## Part 6 — SSH Brute-Force Simulation

### Step 6.1 — Watch Auth Logs

In Terminal 2:

```bash
docker exec ssh-server bash -c "
tail -f /var/log/auth.log 2>/dev/null || journalctl -f 2>/dev/null || \
  tail -f /var/log/syslog 2>/dev/null
"
```

### Step 6.2 — Simulate Failed Login Attempts

In Terminal 1:

```bash
docker exec ssh-client bash -c "
for i in 1 2 3 4 5; do
  ssh -o StrictHostKeyChecking=no \
      -o PasswordAuthentication=yes \
      -o PubkeyAuthentication=no \
      -o ConnectTimeout=3 \
      student@<SERVER_IP> 2>&1 | grep -i 'denied\|error\|refused' || true
  echo \"Attempt \$i failed\"
done
"
```

**Observe Terminal 2:** Failed attempts appear in the auth log. Security teams monitor these logs for brute-force patterns (many failures from one IP in a short time).

📸 **Screenshot checkpoint:** Take a screenshot of the auth log entries showing failed login attempts.

---

## Part 7 — Key Permission Best Practices

### Step 7.1 — Understand Key File Permissions

```bash
docker exec ssh-client bash -c "
ls -la /root/.ssh/
"
```

- `id_rsa` should be `600` (owner read/write only)
- `id_rsa.pub` should be `644` (owner read/write, others read)
- `.ssh/` directory should be `700`

If permissions are wrong, SSH will refuse to use the key:

```bash
docker exec ssh-client bash -c "
chmod 644 /root/.ssh/id_rsa  # Wrong permission
ssh -i /root/.ssh/id_rsa student@<SERVER_IP> 2>&1 || echo 'Permission too open!'
chmod 600 /root/.ssh/id_rsa  # Fix it
"
```

📸 **Screenshot checkpoint:** Take a screenshot of the permission warning and the fix.

---

## Cleanup

```bash
docker stop ssh-server ssh-client
docker rm ssh-server ssh-client
docker network rm ssh-lab
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-11a` — Server IP address
- [ ] `screenshot-11b` — Successful password-based SSH login
- [ ] `screenshot-11c` — SSH key files and public key content
- [ ] `screenshot-11d` — `ssh-copy-id` success
- [ ] `screenshot-11e` — Passwordless key-based SSH login
- [ ] `screenshot-11f` — Password auth blocked after disabling
- [ ] `screenshot-11g` — Key auth still works after disabling password auth
- [ ] `screenshot-11h` — Auth log showing brute-force attempts
- [ ] `screenshot-11i` — Permission warning for incorrect key permissions

### Reflection Questions

1. What makes SSH key authentication more secure than password authentication? Think in terms of what an attacker needs to succeed with each method.
2. A system admin accidentally posts their **private key** (`id_rsa`) on GitHub. What should they do immediately, and why?
3. Why is it important to disable password-based SSH authentication on a public-facing server? What attack does this prevent?
4. The auth log shows 200 failed SSH login attempts from the same IP in 10 minutes. What is this called, and what are three defenses against it?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Key vs password comparison understanding demonstrated: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
