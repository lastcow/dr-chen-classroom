# Lab 08 — Securing a Web Server with HTTPS (Nginx + TLS)

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Internet Security — TLS Certificates & HTTPS  
**Difficulty:** ⭐⭐ Beginner–Intermediate  
**Estimated Time:** 60–75 minutes  
**Related Reading:** Chapter 6 — Cryptography Fundamentals, Chapter 8 — Internet Security

---

## Overview

Nearly all modern websites use HTTPS — the combination of HTTP and TLS encryption. In this lab you will configure a real Nginx web server inside Docker to serve content over HTTPS using a self-signed certificate. You will see what happens when you visit a site with an untrusted cert, understand why Certificate Authorities exist, and force HTTP→HTTPS redirection.

---

## Learning Objectives

1. Generate a self-signed TLS certificate with OpenSSL.
2. Configure Nginx to serve HTTPS on port 443.
3. Understand the browser warning for self-signed certificates.
4. Configure HTTP-to-HTTPS redirection.
5. Inspect a live TLS handshake with OpenSSL.

---

## Prerequisites

- Docker Desktop installed and running.
- Lab 07 (OpenSSL) helpful but not required.

---

## Part 1 — Generate a Self-Signed TLS Certificate

### Step 1.1 — Create a Working Directory

```bash
mkdir -p ~/lab08/{ssl,html,conf}
cd ~/lab08
```

### Step 1.2 — Generate the Certificate and Key

```bash
docker run --rm -v ~/lab08/ssl:/ssl ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq openssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /ssl/server.key \
  -out /ssl/server.crt \
  -subj '/C=US/ST=Maryland/L=Frostburg/O=FSU/CN=localhost'
ls -la /ssl/
"
```

**Verify the files were created:**

```bash
ls -la ~/lab08/ssl/
```

📸 **Screenshot checkpoint:** Take a screenshot showing `server.key` and `server.crt` created.

### Step 1.3 — Inspect the Certificate

```bash
docker run --rm -v ~/lab08/ssl:/ssl ubuntu:22.04 bash -c "
apt-get install -y -qq openssl 2>/dev/null
openssl x509 -in /ssl/server.crt -text -noout | head -30
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the certificate details (Issuer = Subject for self-signed, validity dates).

---

## Part 2 — Create the Web Content

### Step 2.1 — Create a Simple HTML Page

```bash
cat > ~/lab08/html/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SCIA-120 Secure Server</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 80px auto; text-align: center; }
        h1 { color: #0f3460; }
        .badge { background: #28a745; color: white; padding: 8px 16px; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>🔒 Secure Connection Established</h1>
    <p>This page is served over HTTPS with TLS encryption.</p>
    <span class="badge">✓ HTTPS Active</span>
    <p><small>SCIA-120 Lab 08 — Frostburg State University</small></p>
</body>
</html>
EOF
```

---

## Part 3 — Configure Nginx for HTTPS

### Step 3.1 — Write the Nginx Configuration

```bash
cat > ~/lab08/conf/nginx.conf << 'EOF'
events {}

http {
    # HTTP server — redirect to HTTPS
    server {
        listen 80;
        server_name localhost;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl;
        server_name localhost;

        ssl_certificate     /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;

        # Modern TLS settings
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ =404;
        }
    }
}
EOF
```

### Step 3.2 — Start Nginx with HTTPS

```bash
docker run -d \
  --name https-server \
  -p 8080:80 \
  -p 8443:443 \
  -v ~/lab08/conf/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v ~/lab08/ssl:/etc/nginx/ssl:ro \
  -v ~/lab08/html:/usr/share/nginx/html:ro \
  nginx:alpine
```

### Step 3.3 — Verify the Server Is Running

```bash
docker ps | grep https-server
docker logs https-server
```

📸 **Screenshot checkpoint:** Take a screenshot of `docker ps` showing the server running with both port mappings.

---

## Part 4 — Test HTTPS Access

### Step 4.1 — Test with curl (Expecting Certificate Warning)

```bash
curl https://localhost:8443
```

**Expected output:**
```
curl: (60) SSL certificate problem: self signed certificate
```

This is the same warning your browser shows. The cert is valid cryptographically, but not signed by a trusted CA.

### Step 4.2 — Bypass the Warning (As You Would in a Lab Setting)

```bash
curl -k https://localhost:8443
```

The `-k` flag skips certificate verification. You should see your HTML page.

📸 **Screenshot checkpoint:** Take a screenshot of the successful HTTPS response (HTML content).

### Step 4.3 — Test HTTP Redirect

```bash
curl -v http://localhost:8080/ 2>&1 | grep -E "< HTTP|Location"
```

**Expected output:**
```
< HTTP/1.1 301 Moved Permanently
< Location: https://localhost/
```

📸 **Screenshot checkpoint:** Take a screenshot showing the 301 redirect from HTTP to HTTPS.

---

## Part 5 — Inspect the TLS Handshake

### Step 5.1 — Use OpenSSL to Inspect the Connection

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get install -y -qq openssl 2>/dev/null
echo | openssl s_client -connect host.docker.internal:8443 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates
"
```

This shows the certificate's subject, issuer, and validity — exactly what a browser checks when you click the padlock icon.

📸 **Screenshot checkpoint:** Take a screenshot showing the handshake certificate information.

### Step 5.2 — Check the TLS Protocol Version

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get install -y -qq openssl 2>/dev/null
echo | openssl s_client -connect host.docker.internal:8443 2>&1 | grep -E 'Protocol|Cipher'
"
```

📸 **Screenshot checkpoint:** Take a screenshot showing the TLS protocol version and cipher suite negotiated.

---

## Part 6 — Why Self-Signed vs. CA-Signed Matters

| | Self-Signed Certificate | CA-Signed Certificate |
|--|------------------------|----------------------|
| **Cost** | Free | Free (Let's Encrypt) to expensive |
| **Browser trust** | Warning shown ❌ | Trusted, no warning ✅ |
| **Use case** | Internal labs, testing | Public-facing websites |
| **How verified** | Not verified by anyone | CA verified the domain owner |
| **Valid for** | Any name you choose | Only domains you prove you own |

---

## Cleanup

```bash
docker stop https-server && docker rm https-server
rm -rf ~/lab08
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-08a` — `server.key` and `server.crt` created
- [ ] `screenshot-08b` — Certificate details (self-signed, dates)
- [ ] `screenshot-08c` — `docker ps` showing port 8080 and 8443 mapped
- [ ] `screenshot-08d` — curl SSL certificate error (without `-k`)
- [ ] `screenshot-08e` — Successful HTTPS response HTML (with `-k`)
- [ ] `screenshot-08f` — 301 redirect from HTTP to HTTPS
- [ ] `screenshot-08g` — TLS handshake certificate details
- [ ] `screenshot-08h` — TLS protocol version and cipher suite

### Reflection Questions

1. What is the difference between a **self-signed certificate** and a **CA-signed certificate**? Why does a browser warn you about one but not the other?
2. What does a **301 redirect** from HTTP to HTTPS accomplish? Why is it important for security?
3. What is the TLS handshake? Describe in your own words what the server and client are doing before encrypted data is transmitted.
4. Why are TLS versions 1.0 and 1.1 no longer considered secure? What was changed in TLS 1.3?

---

!!! tip "Grading Rubric"
    - Screenshots complete and clearly labeled: **40 points**  
    - Self-signed vs CA-signed table understanding: **20 points**  
    - Reflection questions answered thoughtfully: **40 points**  
    - **Total: 100 points**
