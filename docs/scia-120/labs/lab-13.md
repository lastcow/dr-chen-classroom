# Lab 13 — Capstone: Harden a Containerized Application

**Course:** SCIA-120 · Introduction to Secure Computing  
**Topic:** Capstone — Applying Security Across All Domains  
**Difficulty:** ⭐⭐⭐ Intermediate  
**Estimated Time:** 90–120 minutes  
**Related Reading:** All chapters; emphasis on Ch. 4, 6, 7, 8, 11, 12, 13, 14

---

## Overview

This capstone lab brings together everything you have learned in SCIA-120. You will start with a deliberately **insecure** containerized web application and systematically harden it by applying controls from across the course — OS permissions, encryption, network isolation, authentication, and log monitoring. By the end, you will have transformed an insecure deployment into a hardened one and documented every change.

---

## Learning Objectives

1. Identify multiple security vulnerabilities in an insecure Docker deployment.
2. Apply OS-level hardening (non-root user, read-only filesystem where possible).
3. Enable HTTPS and disable plain HTTP.
4. Isolate the application network from unnecessary exposure.
5. Enable and review security-relevant logs.
6. Document a security hardening checklist.

---

## Prerequisites

- **All Labs 01–12 should be completed or reviewed before starting this lab.**
- Docker Desktop installed and running.

---

## Part 1 — The Insecure Baseline

You are given a "production" deployment of a Python web application. Your task is to find and fix everything wrong with it.

### Step 1.1 — Create the Insecure Application

```bash
mkdir -p ~/lab13/app
```

Create the insecure Flask app:

```bash
cat > ~/lab13/app/app.py << 'EOF'
from flask import Flask, request, jsonify
import sqlite3, os

app = Flask(__name__)

# INSECURITY 1: Hardcoded credentials in code
DB_PASSWORD = "admin123"
SECRET_KEY = "mysecretkey"

def get_db():
    conn = sqlite3.connect('/tmp/users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    conn.execute("INSERT OR IGNORE INTO users VALUES (1, 'alice', 'password123')")
    conn.execute("INSERT OR IGNORE INTO users VALUES (2, 'bob', 'letmein')")
    conn.commit()
    return conn

@app.route('/')
def index():
    return '<h1>Insecure App v1.0</h1><p>Welcome!</p>'

@app.route('/login')
def login():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    
    # INSECURITY 2: SQL injection vulnerability
    conn = get_db()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = conn.execute(query).fetchone()
    
    if result:
        return jsonify({"status": "logged in", "user": result[1]})
    return jsonify({"status": "failed"})

@app.route('/debug')
def debug():
    # INSECURITY 3: Debug endpoint exposes system info
    return jsonify({
        "env": dict(os.environ),
        "cwd": os.getcwd(),
        "files": os.listdir('/')
    })

if __name__ == '__main__':
    # INSECURITY 4: Debug mode on, listening on all interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF
```

Create the insecure Dockerfile:

```bash
cat > ~/lab13/app/Dockerfile << 'EOF'
FROM python:3.11
# INSECURITY 5: Running as root (no USER directive)
RUN pip install flask
COPY app.py /app/app.py
WORKDIR /app
# INSECURITY 6: Debug mode, no TLS
CMD ["python", "app.py"]
EOF
```

### Step 1.2 — Build and Run the Insecure App

```bash
docker build -t insecure-app ~/lab13/app/
docker run -d \
  --name insecure-app \
  -p 5000:5000 \
  insecure-app
```

### Step 1.3 — Demonstrate the Vulnerabilities

**Test SQL injection:**

```bash
curl "http://localhost:5000/login?username=alice'--&password=wrong"
```

**Test the debug endpoint (information disclosure):**

```bash
curl http://localhost:5000/debug | python3 -m json.tool | head -20
```

📸 **Screenshot checkpoint:** Take a screenshot of the SQL injection bypass working and the debug endpoint exposing sensitive information.

### Step 1.4 — Document the Vulnerabilities

Before hardening, list every vulnerability you can find. Create a **Security Finding Report**:

| Finding | Severity | Description |
|---------|----------|-------------|
| Running as root | High | Container runs as root — compromise = full system access |
| SQL Injection | Critical | Login endpoint vulnerable to SQLi authentication bypass |
| Debug endpoint | High | `/debug` exposes environment variables and filesystem listing |
| No HTTPS | High | Credentials sent over plaintext HTTP |
| Debug mode on | Medium | Flask debug mode enables interactive debugger — RCE risk |
| Hardcoded credentials | High | Database password hardcoded in source code |

📸 **Screenshot checkpoint:** Take a screenshot of your completed vulnerability table.

---

## Part 2 — Stop the Insecure App

```bash
docker stop insecure-app && docker rm insecure-app
```

---

## Part 3 — Apply Hardening

### Step 3.1 — Fix the Application Code

```bash
cat > ~/lab13/app/app_secure.py << 'EOF'
from flask import Flask, request, jsonify
import sqlite3, os, hashlib

app = Flask(__name__)

# FIX 1: No hardcoded credentials — use environment variables
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')

def get_db():
    conn = sqlite3.connect('/tmp/users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)''')
    # FIX 2: Store hashed passwords
    conn.execute("INSERT OR IGNORE INTO users VALUES (1, 'alice', ?)",
                 (hashlib.sha256(b'password123').hexdigest(),))
    conn.execute("INSERT OR IGNORE INTO users VALUES (2, 'bob', ?)",
                 (hashlib.sha256(b'letmein').hexdigest(),))
    conn.commit()
    return conn

@app.route('/')
def index():
    return '<h1>Secure App v2.0</h1><p>Welcome!</p>'

@app.route('/login')
def login():
    username = request.args.get('username', '')
    password = request.args.get('password', '')
    
    # FIX 3: Parameterized query — no SQL injection
    conn = get_db()
    result = conn.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        (username, hashlib.sha256(password.encode()).hexdigest())
    ).fetchone()
    
    if result:
        return jsonify({"status": "logged in", "user": result[1]})
    return jsonify({"status": "failed"})

# FIX 4: Debug endpoint REMOVED

if __name__ == '__main__':
    # FIX 5: debug=False, only listen on 127.0.0.1 (behind a proxy)
    app.run(host='127.0.0.1', port=5000, debug=False)
EOF
```

### Step 3.2 — Create the Hardened Dockerfile

```bash
cat > ~/lab13/app/Dockerfile.secure << 'EOF'
FROM python:3.11-slim

# FIX 6: Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

RUN pip install flask --no-cache-dir

COPY app_secure.py /app/app.py
WORKDIR /app

# FIX 7: Change ownership and switch to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

CMD ["python", "app.py"]
EOF
```

### Step 3.3 — Build the Hardened Image

```bash
docker build -t secure-app -f ~/lab13/app/Dockerfile.secure ~/lab13/app/
```

📸 **Screenshot checkpoint:** Take a screenshot of the successful Docker build.

---

## Part 4 — Deploy with Network Isolation

### Step 4.1 — Create an Internal-Only Network for the App

```bash
docker network create --internal app-internal
docker network create app-external
```

### Step 4.2 — Generate TLS Certificate for HTTPS

```bash
mkdir -p ~/lab13/ssl
docker run --rm -v ~/lab13/ssl:/ssl ubuntu:22.04 bash -c "
apt-get install -y -qq openssl 2>/dev/null
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /ssl/server.key -out /ssl/server.crt \
  -subj '/C=US/ST=Maryland/L=Frostburg/O=FSU/CN=localhost'
chmod 600 /ssl/server.key
"
```

### Step 4.3 — Create Nginx Reverse Proxy Config (HTTPS Termination)

```bash
mkdir -p ~/lab13/nginx
cat > ~/lab13/nginx/nginx.conf << 'EOF'
events {}
http {
    server {
        listen 80;
        return 301 https://$host$request_uri;
    }
    server {
        listen 443 ssl;
        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-Content-Type-Options "nosniff";
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000";
        
        location / {
            proxy_pass http://secure-app:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF
```

### Step 4.4 — Deploy the Hardened Stack

```bash
# App container — only on internal network
docker run -d \
  --name secure-app \
  --network app-internal \
  --read-only \
  --tmpfs /tmp \
  --cap-drop ALL \
  -e SECRET_KEY=prod-$(openssl rand -hex 16) \
  secure-app

# Nginx — bridges internal and external
docker run -d \
  --name secure-nginx \
  --network app-external \
  -p 8080:80 \
  -p 8443:443 \
  -v ~/lab13/ssl:/etc/nginx/ssl:ro \
  -v ~/lab13/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:alpine

docker network connect app-internal secure-nginx
```

📸 **Screenshot checkpoint:** Take a screenshot of both containers running with `docker ps`.

---

## Part 5 — Verify the Hardening

### Step 5.1 — Verify Non-Root User

```bash
docker exec secure-app whoami
```

**Expected:** `appuser` — not root.

📸 **Screenshot checkpoint:** Take a screenshot showing `whoami` returns `appuser`.

### Step 5.2 — Verify SQL Injection is Fixed

```bash
curl -k "https://localhost:8443/login?username=alice'--&password=wrong"
```

**Expected:** `{"status": "failed"}` — injection doesn't work anymore.

📸 **Screenshot checkpoint:** Take a screenshot showing SQLi no longer bypasses auth.

### Step 5.3 — Verify Debug Endpoint is Gone

```bash
curl -k https://localhost:8443/debug
```

**Expected:** 404 Not Found.

📸 **Screenshot checkpoint:** Take a screenshot showing the debug endpoint is removed.

### Step 5.4 — Verify HTTPS Redirect Works

```bash
curl -v http://localhost:8080/ 2>&1 | grep -E "Location|HTTP/"
```

**Expected:** 301 redirect to HTTPS.

📸 **Screenshot checkpoint:** Take a screenshot of the HTTP→HTTPS redirect.

### Step 5.5 — Verify App Is Not Directly Reachable (Only Through Nginx)

```bash
docker run --rm --network app-external curlimages/curl \
  curl -s http://secure-app:5000/ 2>&1
```

**Expected:** Connection refused — the app container is only on the internal network.

📸 **Screenshot checkpoint:** Take a screenshot showing the app is unreachable directly.

---

## Part 6 — Final Hardening Checklist

Complete and submit this checklist with your screenshots:

| Security Control | Status | Evidence (Screenshot #) |
|-----------------|--------|------------------------|
| Application runs as non-root | ✅ / ❌ | |
| SQL injection patched | ✅ / ❌ | |
| Debug endpoint removed | ✅ / ❌ | |
| HTTPS enabled | ✅ / ❌ | |
| HTTP redirects to HTTPS | ✅ / ❌ | |
| Credentials not hardcoded | ✅ / ❌ | |
| Container uses --read-only filesystem | ✅ / ❌ | |
| Capabilities dropped (--cap-drop ALL) | ✅ / ❌ | |
| App network-isolated behind proxy | ✅ / ❌ | |
| Security headers present (HSTS, X-Frame, etc.) | ✅ / ❌ | |

---

## Cleanup

```bash
docker stop secure-app secure-nginx insecure-app 2>/dev/null
docker rm secure-app secure-nginx insecure-app 2>/dev/null
docker network rm app-internal app-external 2>/dev/null
docker rmi insecure-app secure-app 2>/dev/null
rm -rf ~/lab13
docker system prune -f
```

---

## Lab Assessment

### Screenshot Submission Checklist

- [ ] `screenshot-13a` — SQL injection bypassing insecure app
- [ ] `screenshot-13b` — Debug endpoint exposing env variables
- [ ] `screenshot-13c` — Vulnerability table (all 6 findings)
- [ ] `screenshot-13d` — Successful Docker build of hardened image
- [ ] `screenshot-13e` — Both containers running (`docker ps`)
- [ ] `screenshot-13f` — `whoami` showing non-root user
- [ ] `screenshot-13g` — SQL injection fixed (returns "failed")
- [ ] `screenshot-13h` — Debug endpoint returns 404
- [ ] `screenshot-13i` — HTTP→HTTPS redirect
- [ ] `screenshot-13j` — App unreachable directly (only via proxy)
- [ ] `screenshot-13k` — Completed hardening checklist (all 10 items)

### Final Reflection Essay

Write a **one-page reflection** (approximately 400–500 words) addressing the following:

1. What were the three most critical vulnerabilities in the original insecure application, and why did you rank them as most critical?
2. Describe the **defense-in-depth** strategy you applied in this lab. How do the multiple layers (application code, OS user, network isolation, HTTPS) work together? What happens if one layer fails?
3. Reflect on your learning across all 13 labs. Which concept surprised you most? Which do you think is most important for a real organization to get right?
4. If you were advising a small company on improving their application security, what would be your **top three recommendations** based on what you learned in this course?

---

!!! tip "Grading Rubric"
    - Screenshots complete with hardening checklist: **30 points**  
    - Vulnerability table (Part 1) fully completed: **20 points**  
    - Hardening correctly applied and verified: **20 points**  
    - Final reflection essay: **30 points**  
    - **Total: 100 points**

---

!!! success "Congratulations!"
    You have completed all 13 SCIA-120 labs. You have hands-on experience with Docker security, file permissions, cryptography, network scanning, packet analysis, firewalls, TLS, SQL injection, malware sandboxing, SSH authentication, log analysis, and full application hardening. These skills form the practical foundation of a career in information security.
