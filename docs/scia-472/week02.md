---
title: "Week 2 — Reconnaissance & OSINT"
description: Master passive and active reconnaissance techniques using open-source intelligence gathering tools and methodologies.
---

# Week 2 — Reconnaissance & Open Source Intelligence (OSINT)

<div class="week-meta" markdown>
**Course Objectives:** CO2 &nbsp;|&nbsp; **Focus:** Information Gathering &nbsp;|&nbsp; **Difficulty:** ⭐⭐☆☆☆
</div>

---

## Learning Objectives

By the end of this week, you will be able to:

- [ ] Distinguish between passive and active reconnaissance techniques
- [ ] Perform DNS enumeration and identify exposed infrastructure
- [ ] Use Shodan, theHarvester, and Maltego for target profiling
- [ ] Extract metadata from publicly available documents
- [ ] Identify WHOIS, BGP, and certificate transparency data for target mapping

---

## 1. Reconnaissance Overview

Reconnaissance (recon) is **the most critical phase** of any penetration test or attack. The more intelligence gathered, the more precisely targeted subsequent attacks can be.

!!! info "Intelligence Hierarchy"
    Raw data → Processed information → Actionable intelligence → Decision advantage

### Passive vs. Active Recon

| | Passive Reconnaissance | Active Reconnaissance |
|---|---|---|
| **Definition** | Gather info without touching the target | Directly interact with target systems |
| **Detectability** | Extremely low / undetectable | Potentially logged by IDS/IPS/firewalls |
| **Sources** | Internet archives, social media, public records | DNS queries to target, port scans |
| **Examples** | Google dorking, Shodan, WHOIS | Nmap ping sweep, zone transfer attempt |
| **Risk** | Zero | Moderate (may trigger alerts) |

---

## 2. Passive Reconnaissance Techniques

### 2.1 DNS Intelligence

The **Domain Name System** is a gold mine for attackers. DNS records reveal:

```
Record Types of Interest:
──────────────────────────────────────────
A       →  IPv4 address of hostname
AAAA    →  IPv6 address
MX      →  Mail servers (reveals email platform)
NS      →  Authoritative nameservers
TXT     →  SPF, DKIM, DMARC, verification tokens
CNAME   →  Canonical name aliases
SOA     →  Zone authority (admin email often leaked)
SRV     →  Service records (VoIP, Lync, etc.)
```

**DNS Zone Transfer (AXFR):**
If misconfigured, a nameserver will hand over all DNS records for a domain:

```bash
# Attempt zone transfer
dig axfr @ns1.target.com target.com

# If successful, reveals ALL subdomains and IPs
# Modern servers restrict this — but legacy systems still fail
```

!!! danger "Real-World Impact"
    Zone transfers have exposed internal hostnames like `vpn-internal.company.com`, `devdb.company.com`, `admin-panel.company.com` — revealing the entire internal network map.

### 2.2 WHOIS & Registration Data

```bash
whois target.com          # Domain registration info
whois 192.168.1.0/24     # IP WHOIS (ASN, netblock owner)

# ARIN (North America): https://search.arin.net
# RIPE (Europe): https://apps.db.ripe.net
# APNIC (Asia-Pacific): https://search.apnic.net
```

**Intelligence extracted from WHOIS:**
- Registrant name and organization
- Administrative/technical contact emails
- Registration and expiry dates
- Nameservers (identify DNS provider/hosting)
- Historical data via DomainTools or SecurityTrails

### 2.3 Certificate Transparency

Every TLS certificate issued to a domain is logged in public CT logs. This reveals:

- **All subdomains** that have ever had a certificate issued
- Certificate metadata (issuer, validity, SANs)

```bash
# Query crt.sh for all certificates for a domain
curl "https://crt.sh/?q=%.target.com&output=json" | jq '.[].name_value' | sort -u

# Tools: subfinder, amass, ct-exposer
```

### 2.4 Google Dorking

Advanced Google search operators expose misconfigured or sensitive content:

| Operator | Example | What it Finds |
|----------|---------|---------------|
| `site:` | `site:target.com` | All indexed pages |
| `filetype:` | `site:target.com filetype:pdf` | Exposed PDFs |
| `intitle:` | `intitle:"index of"` | Open directory listings |
| `inurl:` | `inurl:admin site:target.com` | Admin panels |
| `cache:` | `cache:target.com` | Google's cached version |
| `-` (exclude) | `site:target.com -www` | Subdomains only |

!!! tip "GHDB"
    The **Google Hacking Database** (exploit-db.com/google-hacking-database) catalogs thousands of dorks for finding: exposed passwords, vulnerable servers, login portals, network devices, and more.

### 2.5 Shodan — The Internet of Vulnerable Things

Shodan continuously crawls the internet and indexes **banner data from every accessible service**. It finds:

- Industrial control systems (SCADA, PLCs)
- Exposed databases (MongoDB, Elasticsearch, Redis)
- IP cameras, routers, printers
- Vulnerable software versions

```bash
# Shodan CLI queries
shodan search "apache 2.4.49"          # Find vulnerable Apache installs
shodan search "org:target org"          # Find org's assets
shodan search "hostname:target.com"     # By hostname
shodan search "ssl:target.com"          # By SSL cert

# Shodan Dorks:
# product:MySQL port:3306 country:US
# "default password" port:23
# os:"Windows XP"
```

---

## 3. Active Reconnaissance Techniques

### 3.1 theHarvester

Automates collection of emails, subdomains, hosts, employee names, open ports, and banners:

```bash
# Gather emails and hosts using multiple sources
theHarvester -d target.com -b google,linkedin,bing,censys,shodan -l 500

# Output to HTML report
theHarvester -d target.com -b all -f target_recon.html

# Key sources: google, bing, linkedin, twitter, github, shodan, 
#              censys, dnsdumpster, crtsh, hunter
```

### 3.2 Maltego — Visual Link Analysis

Maltego transforms raw data into an interactive graph of relationships:

```
Person → Email Address → Domain → IP → Netblock → ASN
       ↘ Phone Number → Location
       ↘ Social Profiles → Connections → Colleagues
```

**Maltego Transforms:**
- **To Email Address** — from company domain or person name
- **To Website** — from company/email
- **To DNS Name** — subdomain discovery
- **Shodan Transform** — enrich IPs with banner data
- **Have I Been Pwned** — check emails in breach databases

### 3.3 Subdomain Enumeration

```bash
# amass — comprehensive subdomain enumeration
amass enum -d target.com -o amass_output.txt

# subfinder — fast passive subdomain discovery
subfinder -d target.com -all -o subdomains.txt

# dnsx — DNS resolution and validation
cat subdomains.txt | dnsx -a -resp

# httpx — probe for live web servers
cat subdomains.txt | httpx -title -status-code -tech-detect
```

### 3.4 Metadata Extraction

Office documents, PDFs, and images often contain hidden metadata:

```bash
# FOCA (Windows tool) or exiftool (cross-platform)
exiftool document.pdf

# Common metadata leaks:
# Author name, username → AD account enumeration
# Software version → vulnerability identification  
# GPS coordinates → physical location
# Revision history → organizational structure
# Printer name → internal hostnames
```

---

## 4. Social Media & Human Intelligence

### LinkedIn Enumeration

LinkedIn is arguably the most valuable OSINT source:

- **Employee names** → derive AD usernames (firstname.lastname@company.com)
- **Job postings** → reveal technology stack ("5 years Palo Alto Networks experience")
- **Org chart** → identify executive targets for spearphishing
- **Recent hires** → infer security team size and focus areas

```bash
# linkedin2username — derive likely AD usernames from LinkedIn
python linkedin2username.py -u yourprofile -c "Target Company"
# Output: jsmith, john.smith, johns, j.smith, smithj...
```

### Breach Data & HaveIBeenPwned

```bash
# Check if target emails appear in breach databases
# API: https://haveibeenpwned.com/API/v3
curl -H "hibp-api-key: YOUR_KEY" \
  https://haveibeenpwned.com/api/v3/breachedaccount/target@company.com

# Tools: h8mail, breach-parse (offline breach data analysis)
```

---

## 5. OSINT Methodology — Structured Approach

```
PHASE 1: SCOPING          PHASE 2: COLLECTION
─────────────────         ──────────────────────
Define target             DNS: subdomains, MX, NS, SOA
Identify IP ranges        Certificate transparency
Map affiliated domains    WHOIS history
                          Shodan/Censys asset discovery
                          Google dorking
                          
PHASE 3: PROCESSING       PHASE 4: ANALYSIS
─────────────────────     ─────────────────────
Deduplicate findings      Build attack surface map
Resolve all subdomains    Identify high-value targets
Screenshot live sites     Prioritize by exploitability
Extract metadata          Select attack vectors
                          Prepare for scanning phase
```

---

## 6. Operational Security (OPSEC) Considerations

As an ethical hacker, you must understand how to minimize your footprint:

| Technique | Purpose |
|-----------|---------|
| **VPN / Tor** | Anonymize active recon traffic |
| **Burner accounts** | Social media research without attribution |
| **Canary tokens** | (Defender) Detect when recon is occurring |
| **Rate limiting queries** | Avoid triggering security alerts |
| **Proxy rotation** | Distribute requests to avoid IP blocks |

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **OSINT** | Open Source Intelligence — info from publicly available sources |
| **Footprinting** | Comprehensive profile building of a target |
| **Attack surface** | All digital touchpoints of a target organization |
| **Zone transfer** | DNS mechanism to replicate records — often misconfigured |
| **Dorking** | Using search operators to find sensitive exposed data |
| **Shodan** | Search engine for internet-connected devices and services |
| **CT Logs** | Certificate Transparency logs — public record of all TLS certs |

---

## Review Questions

!!! question "Self-Assessment"
    1. Explain why passive reconnaissance is preferred during the early stages of a pentest.
    2. A DNS zone transfer succeeds on `ns1.acme.com`. What data can you extract, and what attack does this enable?
    3. Describe three pieces of intelligence extractable from a company's job postings.
    4. You find a PDF on the target's website. How do you extract metadata, and what might you find?
    5. Map LinkedIn enumeration to the MITRE ATT&CK framework (hint: search T1591).

---

## Further Reading

- 📖 *Hacking Exposed 7*, Chapter 2 — "Footprinting"
- 📄 [OSINT Framework](https://osintframework.com/) — comprehensive OSINT resource tree
- 📄 [Maltego Documentation](https://docs.maltego.com/)
- 📄 SANS SEC487 Course Notes — Open-Source Intelligence Gathering
- 📄 [Shodan Filters Reference](https://www.shodan.io/explore)
- 📄 MITRE ATT&CK: TA0043 — Reconnaissance

---

*[← Week 1](week01.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 3 →](week03.md)*
