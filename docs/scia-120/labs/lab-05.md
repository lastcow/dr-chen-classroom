# Lab 05 — Packet Capture & Traffic Analysis with tcpdump

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Network Security — Traffic Analysis & Encryption  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 45–60 minutes  
**Related Reading:** Chapter 7 — Network Security Fundamentals

---

## Overview

Every packet your computer sends travels across networks where it can potentially be intercepted. In this lab you will use **tcpdump** — a foundational network analysis tool — to capture live traffic inside a Docker network. You will clearly see the difference between unencrypted (plaintext) HTTP traffic and encrypted HTTPS traffic, understanding exactly why encryption matters.

---

## Learning Objectives

1. Use `tcpdump` to capture network packets on a Docker network interface.
2. Read and interpret basic packet capture output.
3. Observe plaintext credentials in unencrypted HTTP traffic.
4. Observe that HTTPS traffic reveals no readable content.
5. Understand what a **packet sniffer** is and how defenders use it.

---

## Prerequisites

- Docker Desktop installed and running.
- Lab 04 recommended but not required.

---

## Part 1 — Set Up the Lab Environment

### Step 1.1 — Create a Shared Lab Network

```bash
docker network create sniff-lab
```

### Step 1.2 — Start a Plain HTTP Server (No Encryption)

```bash
docker run -d \
  --name http-server \
  --network sniff-lab \
  -e HTTPD_PORT=80 \
  httpd:alpine
```

### Step 1.3 — Verify It's Running

```bash
docker inspect http-server | grep IPAddress
```

Note the IP address — you'll use it in the capture steps.

📸 **Screenshot checkpoint:** Take a screenshot of the IP address output.

---

## Part 2 — Capture Unencrypted HTTP Traffic

### Step 2.1 — Run Capture and Traffic in One Container

The `nicolaka/netshoot` image includes both `tcpdump` and `wget`, so you can capture and generate traffic in the same container:

```bash
docker run --rm -it \
  --name sniffer \
  --network sniff-lab \
  --cap-add NET_RAW \
  --cap-add NET_ADMIN \
  nicolaka/netshoot bash
```

Inside the container, start tcpdump in the background then send traffic:

```bash
tcpdump -i eth0 -A port 80 &
sleep 1
wget -q -O- http://http-server/
sleep 1
kill %1 2>/dev/null
```

You will see the raw HTTP request and response — in plaintext:

```
GET / HTTP/1.1
Host: http-server
...
HTTP/1.1 200 OK
...
<html><body><h1>It works!</h1></body>
```

📸 **Screenshot checkpoint:** Take a screenshot of the captured HTTP traffic showing the request/response in plaintext.

### Step 2.2 — Capture Login Credentials in Plaintext

Many legacy or poorly designed systems transmit passwords over plain HTTP. Restart tcpdump and simulate a form POST:

```bash
tcpdump -i eth0 -A port 80 &
sleep 1
wget -q --post-data "username=alice&password=SecretPass123" http://http-server/ -O /dev/null
sleep 1
kill %1 2>/dev/null
```

**Look in the output for the POST body — you can see the password in plaintext!**

```
username=alice&password=SecretPass123
```

📸 **Screenshot checkpoint:** Take a screenshot clearly showing the captured POST data including the username and password.

---

## Part 3 — Capture HTTPS Traffic (Encrypted)

### Step 3.1 — Make an HTTPS Request to See Encrypted Traffic

Inside the same netshoot container, restart tcpdump on port 443 and make an HTTPS request using `wget`:

```bash
tcpdump -i eth0 -A port 443 &
sleep 1
wget -q --no-check-certificate https://example.com -O /dev/null 2>&1 || true
sleep 1
kill %1 2>/dev/null
```

### Step 3.2 — Observe the Encrypted Output

Look at Terminal 1. You will see packets captured — but the content is **gibberish**. This is TLS-encrypted data:

```
..h......,@..N5.e.Q.........
.#..1..0..&...."0 ..(.....{...
```

No readable text. No credentials. This is why HTTPS is essential.

📸 **Screenshot checkpoint:** Take a screenshot of the HTTPS packet capture showing only encrypted/binary data.

---

## Part 4 — Capture DNS Queries

DNS (Domain Name System) queries are typically unencrypted — this means an observer on the network can see every hostname you look up, even if the actual connection is HTTPS.

### Step 4.1 — Capture DNS Traffic

In Terminal 1 (sniffer):

```bash
tcpdump -i eth0 -n port 53
```

In Terminal 2:

```bash
docker run --rm --network sniff-lab curlimages/curl \
  curl -s http://http-server/
```

Also try:

```bash
docker run --rm nicolaka/netshoot nslookup google.com
```

📸 **Screenshot checkpoint:** Take a screenshot showing captured DNS query packets.

**Observe:** Even with HTTPS, a passive observer can see *which sites* you visit via DNS queries. This is why **DNS over HTTPS (DoH)** exists.

---

## Part 5 — Save and Analyze a Packet Capture File

Security analysts often save captures to `.pcap` files for later analysis.

### Step 5.1 — Save a Capture

In Terminal 1 (sniffer):

```bash
tcpdump -i eth0 -w /tmp/capture.pcap &
sleep 5
```

In Terminal 2, generate some traffic:

```bash
docker run --rm --network sniff-lab curlimages/curl \
  curl -s http://http-server/
```

Back in Terminal 1:

```bash
kill %1
tcpdump -r /tmp/capture.pcap -A
```

This reads back the saved capture file — the same way forensic analysts replay captured traffic.

📸 **Screenshot checkpoint:** Take a screenshot of the replay output.

Type `exit` to leave the sniffer container.

---

## Cleanup

```bash
docker stop http-server
docker rm http-server
docker network rm sniff-lab
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-05a` — HTTP server IP address
- [ ] `screenshot-05b` — Captured HTTP GET request/response in plaintext
- [ ] `screenshot-05c` — Captured POST data showing username and password in plaintext
- [ ] `screenshot-05d` — HTTPS capture showing encrypted/unreadable data
- [ ] `screenshot-05e` — Captured DNS queries
- [ ] `screenshot-05f` — Saved and replayed pcap file

### Reflection Questions

1. In Part 2, you captured a username and password in plaintext. What does this tell you about using HTTP (not HTTPS) for login forms?
2. Why is DNS considered a **privacy risk** even when all your web connections use HTTPS?
3. What is the difference between a packet sniffer used by an attacker (passive eavesdropping) vs. a network engineer (traffic analysis)? Is tcpdump itself an attack tool?
4. What would an attacker need to be able to intercept your network traffic? (Think about physical access vs. logical position on the network.)

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Observed differences between HTTP and HTTPS noted: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
