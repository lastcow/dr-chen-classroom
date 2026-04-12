#!/usr/bin/env python3
"""Generate technical diagrams for SCIA-360 chapters 6-10."""

from PIL import Image, ImageDraw, ImageFont
import os

OUT = "/home/john/wiki/docs/scia-360/img"
W, H = 1400, 750
BG = (13, 27, 42)          # #0d1b2a

def get_font(size, bold=False):
    """Try several common font paths."""
    paths_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    ]
    paths_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    ]
    for p in (paths_bold if bold else paths_reg):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def new_img():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)

def title_bar(d, text, font_lg):
    d.rectangle([0, 0, W, 60], fill=(20, 40, 65))
    bbox = d.textbbox((0, 0), text, font=font_lg)
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) // 2, 14), text, fill=(220, 220, 255), font=font_lg)
    d.line([(0, 60), (W, 60)], fill=(80, 120, 180), width=2)

def rounded_rect(d, x0, y0, x1, y1, r, fill, outline=None, width=2):
    d.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    d.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    d.ellipse([x0, y0, x0 + 2*r, y0 + 2*r], fill=fill)
    d.ellipse([x1 - 2*r, y0, x1, y0 + 2*r], fill=fill)
    d.ellipse([x0, y1 - 2*r, x0 + 2*r, y1], fill=fill)
    d.ellipse([x1 - 2*r, y1 - 2*r, x1, y1], fill=fill)
    if outline:
        d.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=outline, width=width)

def center_text(d, cx, cy, text, font, fill):
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw // 2, cy - th // 2), text, fill=fill, font=font)

def arrow(d, x0, y0, x1, y1, fill, width=2, head=10):
    d.line([(x0, y0), (x1, y1)], fill=fill, width=width)
    # arrowhead (simple horizontal/vertical)
    import math
    angle = math.atan2(y1 - y0, x1 - x0)
    d.polygon([
        (x1, y1),
        (int(x1 - head * math.cos(angle - 0.4)), int(y1 - head * math.sin(angle - 0.4))),
        (int(x1 - head * math.cos(angle + 0.4)), int(y1 - head * math.sin(angle + 0.4))),
    ], fill=fill)

# ─────────────────────────────────────────────────────────────────
# DIAGRAM 6 — Access Control Models Comparison
# ─────────────────────────────────────────────────────────────────
def diag6():
    img, d = new_img()
    fL  = get_font(22, bold=True)
    fM  = get_font(16, bold=True)
    fS  = get_font(13)
    fXS = get_font(11)

    title_bar(d, "ACCESS CONTROL MODELS COMPARISON", fL)

    # Column boundaries
    col_w = W // 3
    cols = [
        {"x": 0,         "color": (41, 98, 195),  "hdr": (30, 70, 150),  "name": "DAC",  "full": "Discretionary Access Control"},
        {"x": col_w,     "color": (120, 40, 180),  "hdr": (90, 25, 140),  "name": "MAC",  "full": "Mandatory Access Control"},
        {"x": col_w * 2, "color": (30, 150, 80),   "hdr": (20, 110, 55),  "name": "RBAC", "full": "Role-Based Access Control"},
    ]

    for i, col in enumerate(cols):
        x = col["x"]
        c = col["color"]
        h = col["hdr"]

        # Header
        d.rectangle([x + 4, 68, x + col_w - 4, 120], fill=h)
        d.rectangle([x + 4, 68, x + col_w - 4, 120], outline=c, width=3)
        center_text(d, x + col_w // 2, 84, col["name"], fM, (255, 255, 255))
        center_text(d, x + col_w // 2, 104, col["full"], fXS, (200, 200, 220))

        # Vertical dividers
        if i > 0:
            d.line([(x, 65), (x, H - 10)], fill=(80, 100, 130), width=2)

    # ── DAC column (col 0) ──
    cx0 = col_w // 2
    boxes_dac = [
        (cx0, 175, "OWNER", (41, 98, 195)),
        (cx0, 280, "PERMISSIONS", (41, 98, 195)),
        (cx0, 385, "OBJECT", (41, 98, 195)),
    ]
    for bx, by, lbl, fc in boxes_dac:
        d.rounded_rectangle([bx - 80, by - 25, bx + 80, by + 25], radius=8, fill=fc, outline=(150, 180, 255), width=2)
        center_text(d, bx, by, lbl, fM, (255, 255, 255))
    # arrows
    arrow(d, cx0, 200, cx0, 254, (150, 200, 255), width=3)
    arrow(d, cx0, 305, cx0, 359, (150, 200, 255), width=3)
    # ACL label on perm box side
    d.text((cx0 + 85, 268), "rwxr-xr-x", font=fXS, fill=(180, 220, 255))
    # Sub-boxes for ACL entries
    acl_items = ["user::rwx", "group::r-x", "other::r--"]
    for k, item in enumerate(acl_items):
        iy = 445 + k * 28
        d.rectangle([cx0 - 75, iy, cx0 + 75, iy + 22], fill=(20, 50, 100), outline=(80, 120, 200), width=1)
        center_text(d, cx0, iy + 11, item, fXS, (180, 220, 255))
    d.text((cx0 - 75, 432), "ACL entries:", font=fXS, fill=(150, 180, 255))
    # Key char
    d.rectangle([4 + 10, H - 95, col_w - 14, H - 15], fill=(15, 35, 65), outline=(41, 98, 195), width=2)
    d.text((20, H - 90), "⚠  Trojan Horse Problem:", font=fXS, fill=(255, 200, 80))
    d.text((20, H - 72), "  Malware runs with owner's", font=fXS, fill=(180, 210, 255))
    d.text((20, H - 55), "  full privileges", font=fXS, fill=(180, 210, 255))
    d.text((20, H - 35), "✦  Owner grants/revokes access", font=fXS, fill=(150, 200, 150))

    # ── MAC column (col 1) ──
    cx1 = col_w + col_w // 2
    # Subject box
    d.rounded_rectangle([cx1 - 90, 148, cx1 + 90, 198], radius=8, fill=(80, 20, 130), outline=(180, 100, 255), width=2)
    center_text(d, cx1, 168, "SUBJECT", fM, (255, 255, 255))
    d.text((cx1 - 88, 200), "label: Top Secret", font=fXS, fill=(200, 150, 255))

    # Object box
    d.rounded_rectangle([cx1 - 90, 268, cx1 + 90, 318], radius=8, fill=(80, 20, 130), outline=(180, 100, 255), width=2)
    center_text(d, cx1, 288, "OBJECT", fM, (255, 255, 255))
    d.text((cx1 - 88, 320), "label: Secret", font=fXS, fill=(200, 150, 255))

    # Policy Engine
    d.rounded_rectangle([cx1 - 100, 368, cx1 + 100, 418], radius=8, fill=(60, 10, 100), outline=(220, 130, 255), width=3)
    center_text(d, cx1, 388, "REFERENCE MONITOR", fM, (255, 220, 255))
    center_text(d, cx1, 406, "Policy Enforcement", fXS, (200, 170, 255))

    # Decision boxes
    d.rounded_rectangle([cx1 - 80, 460, cx1 - 10, 500], radius=6, fill=(30, 120, 50), outline=(80, 220, 100), width=2)
    center_text(d, cx1 - 45, 480, "ALLOW", fS, (150, 255, 150))
    d.rounded_rectangle([cx1 + 10, 460, cx1 + 80, 500], radius=6, fill=(140, 20, 20), outline=(255, 80, 80), width=2)
    center_text(d, cx1 + 45, 480, "DENY", fS, (255, 150, 150))

    arrow(d, cx1, 198, cx1, 267, (200, 150, 255), width=2)
    arrow(d, cx1, 318, cx1, 367, (200, 150, 255), width=2)
    arrow(d, cx1 - 30, 418, cx1 - 45, 459, (80, 220, 100), width=2)
    arrow(d, cx1 + 30, 418, cx1 + 45, 459, (255, 80, 80), width=2)

    # BLP/Biba labels
    d.text((col_w + 8, 530), "Bell-LaPadula: no read↑, no write↓", font=fXS, fill=(200, 160, 255))
    d.text((col_w + 8, 548), "Biba: no read↓, no write↑", font=fXS, fill=(200, 160, 255))

    # Key char MAC
    d.rectangle([col_w + 14, H - 95, col_w * 2 - 14, H - 15], fill=(15, 10, 35), outline=(120, 40, 180), width=2)
    d.text((col_w + 20, H - 90), "✦  Labels enforced by OS kernel", font=fXS, fill=(200, 160, 255))
    d.text((col_w + 20, H - 72), "✦  Users cannot override policy", font=fXS, fill=(200, 160, 255))
    d.text((col_w + 20, H - 55), "✦  Prevents Trojan Horse", font=fXS, fill=(150, 220, 150))

    # ── RBAC column (col 2) ──
    cx2 = col_w * 2 + col_w // 2
    rbac_rows = [
        (155, "USERS",        (30, 150, 80)),
        (255, "ROLES",        (30, 150, 80)),
        (355, "PERMISSIONS",  (30, 150, 80)),
        (455, "OBJECTS",      (30, 150, 80)),
    ]
    for ry, lbl, fc in rbac_rows:
        d.rounded_rectangle([cx2 - 85, ry - 28, cx2 + 85, ry + 28], radius=8, fill=fc, outline=(100, 220, 130), width=2)
        center_text(d, cx2, ry, lbl, fM, (255, 255, 255))

    # Connecting arrows
    for ry in [155, 255, 355]:
        arrow(d, cx2, ry + 28, cx2, ry + 100 - 28, (100, 220, 130), width=3)

    # Side labels
    side_items = [
        (205, "alice, bob, charlie"),
        (305, "admin, developer, viewer"),
        (405, "read, write, execute"),
        (500, "/etc/passwd, /var/log/..."),
    ]
    for sy, txt in side_items:
        d.text((cx2 + 90, sy), txt, font=fXS, fill=(150, 220, 150))

    # Key char RBAC
    d.rectangle([col_w * 2 + 14, H - 95, W - 14, H - 15], fill=(10, 30, 15), outline=(30, 150, 80), width=2)
    d.text((col_w * 2 + 20, H - 90), "✦  Separation of duties", font=fXS, fill=(150, 220, 150))
    d.text((col_w * 2 + 20, H - 72), "✦  Users ≠ Permissions (via Roles)", font=fXS, fill=(150, 220, 150))
    d.text((col_w * 2 + 20, H - 55), "✦  Windows Groups / sudo roles", font=fXS, fill=(150, 220, 150))

    img.save(f"{OUT}/ch06-access-control.png")
    print("Saved ch06-access-control.png")

# ─────────────────────────────────────────────────────────────────
# DIAGRAM 7 — SELinux Policy Enforcement Architecture
# ─────────────────────────────────────────────────────────────────
def diag7():
    img, d = new_img()
    fL = get_font(22, bold=True)
    fM = get_font(15, bold=True)
    fS = get_font(12)
    fXS = get_font(11)

    title_bar(d, "SELINUX POLICY ENFORCEMENT ARCHITECTURE", fL)

    ORANGE = (255, 160, 40)
    GREEN  = (60, 210, 100)
    RED    = (220, 60, 60)
    PURPLE = (160, 80, 220)
    LBLUE  = (80, 160, 240)

    # ── Subject & Object ──
    # Subject
    d.rounded_rectangle([40, 90, 240, 165], radius=10, fill=(20, 50, 110), outline=LBLUE, width=3)
    center_text(d, 140, 112, "PROCESS (Subject)", fS, (255,255,255))
    center_text(d, 140, 132, "unconfined_u:unconfined_r", fXS, (150,200,255))
    center_text(d, 140, 150, "httpd_t:s0", fXS, (150,200,255))

    # Object
    d.rounded_rectangle([40, 220, 240, 295], radius=10, fill=(20, 50, 110), outline=LBLUE, width=3)
    center_text(d, 140, 242, "FILE (Object)", fS, (255,255,255))
    center_text(d, 140, 262, "system_u:object_r", fXS, (150,200,255))
    center_text(d, 140, 280, "httpd_sys_content_t:s0", fXS, (150,200,255))

    # "attempts action" label
    d.text((248, 165), "attempts: read()", font=fXS, fill=ORANGE)
    arrow(d, 140, 165, 140, 219, ORANGE, width=2)
    arrow(d, 240, 192, 380, 235, ORANGE, width=3)
    d.text((255, 175), "──► syscall intercepted", font=fXS, fill=ORANGE)

    # ── AVC / Security Server ──
    d.rounded_rectangle([380, 200, 660, 310], radius=12, fill=(40, 20, 80), outline=PURPLE, width=3)
    center_text(d, 520, 225, "SECURITY SERVER", fM, (220,180,255))
    center_text(d, 520, 250, "AVC — Access Vector Cache", fS, (190,150,255))
    center_text(d, 520, 272, "Caches recent decisions", fXS, (160,130,220))

    # Cache hit/miss decision
    d.rounded_rectangle([380, 340, 660, 400], radius=10, fill=(50, 30, 10), outline=ORANGE, width=2)
    center_text(d, 520, 365, "Policy Cache Hit?", fM, (255,200,80))
    center_text(d, 520, 388, "(AVC lookup)", fXS, (200,160,80))

    arrow(d, 520, 310, 520, 339, PURPLE, width=3)

    # YES → immediate decision
    arrow(d, 380, 370, 230, 370, GREEN, width=2)
    d.text((235, 356), "YES", font=fS, fill=GREEN)
    d.rounded_rectangle([60, 355, 225, 390], radius=8, fill=(10, 60, 20), outline=GREEN, width=2)
    center_text(d, 142, 372, "ALLOW / DENY", font=fS, fill=GREEN)

    # NO → Query policy DB
    arrow(d, 660, 370, 800, 370, RED, width=2)
    d.text((665, 355), "NO", font=fS, fill=RED)
    d.rounded_rectangle([800, 340, 1040, 400], radius=10, fill=(60, 10, 10), outline=RED, width=2)
    center_text(d, 920, 365, "POLICY DATABASE", fM, (255,150,150))
    center_text(d, 920, 386, "type_enforcement rules", fXS, (220,120,120))

    # Policy DB → Decision
    arrow(d, 920, 400, 920, 460, RED, width=3)
    d.rounded_rectangle([800, 460, 1040, 520], radius=10, fill=(40, 10, 10), outline=(200, 80, 80), width=3)
    center_text(d, 920, 480, "DECISION", fM, (255,200,200))
    center_text(d, 920, 500, "kernel enforces result", fXS, (200,150,150))

    # Decision → ALLOW
    arrow(d, 860, 520, 750, 600, GREEN, width=3)
    d.rounded_rectangle([580, 595, 745, 650], radius=10, fill=(10, 60, 20), outline=GREEN, width=3)
    center_text(d, 662, 618, "ALLOW", fM, GREEN)
    center_text(d, 662, 638, "action proceeds", fXS, (100, 220, 120))

    # Decision → DENY
    arrow(d, 980, 520, 1080, 600, RED, width=3)
    d.rounded_rectangle([1080, 595, 1270, 650], radius=10, fill=(70, 10, 10), outline=RED, width=3)
    center_text(d, 1175, 618, "DENY", fM, RED)
    center_text(d, 1175, 638, "EACCES + audit log", fXS, (255, 120, 120))

    # Example policy rule
    d.rectangle([800, 530, 1040, 590], fill=(20, 10, 40), outline=PURPLE, width=1)
    d.text((808, 538), "allow httpd_t", font=fXS, fill=(180, 130, 255))
    d.text((808, 553), "  httpd_sys_content_t:file", font=fXS, fill=(180, 130, 255))
    d.text((808, 568), "  { read getattr open };", font=fXS, fill=(150, 255, 150))

    # Update AVC cache arrow
    arrow(d, 920, 460, 660, 370, (100, 100, 200), width=1)
    d.text((720, 395), "update cache", font=fXS, fill=(100,100,200))

    # Legend
    d.rectangle([40, 600, 370, 700], fill=(10, 20, 40), outline=(80, 100, 140), width=1)
    d.text((50, 610), "Legend:", font=fS, fill=(220,220,255))
    for i, (col, lbl) in enumerate([(ORANGE,"System call / request"), (GREEN,"Allow path"), (RED,"Deny / query path"), (PURPLE,"AVC lookup")]):
        d.rectangle([50, 628 + i*17, 68, 642 + i*17], fill=col)
        d.text((75, 628 + i*17), lbl, font=fXS, fill=(200,200,220))

    img.save(f"{OUT}/ch07-security-policies.png")
    print("Saved ch07-security-policies.png")

# ─────────────────────────────────────────────────────────────────
# DIAGRAM 8 — OS Sandboxing & Isolation Techniques
# ─────────────────────────────────────────────────────────────────
def diag8():
    img, d = new_img()
    fL  = get_font(22, bold=True)
    fM  = get_font(14, bold=True)
    fS  = get_font(12)
    fXS = get_font(10)

    title_bar(d, "OS SANDBOXING & ISOLATION TECHNIQUES", fL)

    layers = [
        # (margin, border_color, fill_color, label, sublabel)
        (30,  (255, 220, 50),  (40, 38, 5),   "chroot jail",            "Restricts: filesystem root"),
        (80,  (255, 140, 30),  (40, 25, 5),   "seccomp filter",         "Restricts: syscall surface"),
        (130, (220, 60, 60),   (40, 8, 8),    "Linux Namespaces",       "Restricts: PID/NET/MNT/UTS/IPC/USER"),
        (180, (180, 60, 220),  (30, 8, 40),   "Container (Docker)",     "Restricts: process/FS/net isolation"),
        (230, (60, 120, 255),  (8, 20, 60),   "VM / Hypervisor",        "Restricts: full hardware emulation"),
    ]

    cx, cy = W // 2, (H + 60) // 2 + 10
    box_h_base = (H - 90) // 2 - 30

    for i, (margin, bc, fc, lbl, sublbl) in enumerate(layers):
        bx0 = margin + 20
        bx1 = W - margin - 20
        by0 = 65 + margin
        by1 = H - margin - 5
        d.rectangle([bx0, by0, bx1, by1], fill=fc, outline=bc, width=3)
        # Label top-left
        d.text((bx0 + 8, by0 + 6), lbl, font=fM, fill=bc)
        d.text((bx0 + 8, by0 + 24), sublbl, font=fXS, fill=tuple(min(255, c + 80) for c in bc))

    # Application core
    app_cx, app_cy = cx, cy
    d.rounded_rectangle([app_cx - 90, app_cy - 35, app_cx + 90, app_cy + 35],
                         radius=12, fill=(20, 60, 100), outline=(100, 200, 255), width=3)
    center_text(d, app_cx, app_cy - 10, "Application", fM, (255, 255, 255))
    center_text(d, app_cx, app_cy + 12, "(sandboxed process)", fXS, (150, 200, 255))

    # Namespace items
    ns_labels = ["PID", "NET", "MNT", "UTS", "IPC", "USER"]
    ns_y = 65 + 130 + 30
    ns_total_w = len(ns_labels) * 72
    ns_x0 = cx - ns_total_w // 2
    for j, ns in enumerate(ns_labels):
        nx = ns_x0 + j * 72
        d.rounded_rectangle([nx, ns_y, nx + 62, ns_y + 28], radius=5,
                              fill=(60, 10, 10), outline=(220, 80, 80), width=2)
        center_text(d, nx + 31, ns_y + 14, ns, fXS, (255, 150, 150))

    # Escape attack arrows — from outside each layer pointing inward with ↗
    escape_configs = [
        (W - 50,  90,   W - 260, 130,  (255, 220, 50),  "escape"),
        (W - 50,  140,  W - 260, 180,  (255, 140, 30),  "escape"),
        (W - 50,  200,  W - 260, 240,  (220, 60, 60),   "escape"),
        (W - 50,  265,  W - 260, 305,  (180, 60, 220),  "escape"),
        (W - 50,  330,  W - 260, 370,  (60, 120, 255),  "escape"),
    ]
    for ex0, ey0, ex1, ey1, ec, elbl in escape_configs:
        arrow(d, ex0, ey0, ex1, ey1, ec, width=2, head=8)
        d.text((ex1 + 5, ey1 - 8), "✗ " + elbl, font=fXS, fill=ec)

    # Isolation strength legend (left side)
    d.text((25, H - 115), "← Less Isolated", font=fXS, fill=(180, 180, 180))
    d.text((25, H - 95), "   (chroot only)", font=fXS, fill=(255, 220, 50))
    # Arrow pointing down
    for yy in range(H - 80, H - 30, 12):
        d.line([(35, yy), (35, yy + 8)], fill=(150, 150, 150), width=2)
    d.text((25, H - 25), "More Isolated →", font=fXS, fill=(180, 180, 180))

    img.save(f"{OUT}/ch08-sandboxing.png")
    print("Saved ch08-sandboxing.png")

# ─────────────────────────────────────────────────────────────────
# DIAGRAM 9 — Software Vulnerability Exploitation Lifecycle
# ─────────────────────────────────────────────────────────────────
def diag9():
    img, d = new_img()
    fL  = get_font(22, bold=True)
    fM  = get_font(13, bold=True)
    fS  = get_font(11)
    fXS = get_font(10)

    title_bar(d, "SOFTWARE VULNERABILITY EXPLOITATION LIFECYCLE", fL)

    stages = [
        ("DISCOVERY",          (200, 180, 0),   (50, 45, 0),   ["Fuzzing", "Code Review", "Bug Bounty"]),
        ("WEAPONIZATION",      (220, 120, 20),  (55, 30, 5),   ["Exploit Dev", "PoC Code", "Shellcode"]),
        ("EXPLOITATION",       (210, 40, 40),   (55, 10, 10),  ["Delivery", "Trigger", "Code Exec"]),
        ("PRIV. ESCALATION",   (160, 20, 20),   (45, 5, 5),    ["Local Exploit", "Kernel Bug", "SUID"]),
        ("PERSISTENCE",        (130, 50, 200),  (35, 10, 55),  ["Rootkit", "Backdoor", "Crontab"]),
    ]

    n = len(stages)
    box_w = 200
    gap = 40
    total = n * box_w + (n - 1) * gap
    x_start = (W - total) // 2
    box_top = 85
    box_bot = 260

    stage_centers = []
    for i, (name, bc, fc, items) in enumerate(stages):
        bx = x_start + i * (box_w + gap)
        # Main stage box
        d.rectangle([bx, box_top, bx + box_w, box_bot], fill=fc, outline=bc, width=3)
        # Stage number circle
        d.ellipse([bx + 5, box_top + 5, bx + 33, box_top + 33], fill=bc)
        center_text(d, bx + 19, box_top + 19, str(i + 1), fM, (0, 0, 0))
        # Stage name
        center_text(d, bx + box_w // 2, box_top + 50, name, fM, (255, 255, 255))
        # Sub-items
        for j, item in enumerate(items):
            iy = box_top + 80 + j * 48
            d.rounded_rectangle([bx + 10, iy, bx + box_w - 10, iy + 38], radius=6,
                                  fill=tuple(max(0, c - 20) for c in fc),
                                  outline=tuple(min(255, c + 40) for c in bc), width=1)
            center_text(d, bx + box_w // 2, iy + 19, item, fXS, (220, 220, 220))

        stage_centers.append((bx + box_w // 2, box_bot))
        # Arrow to next stage
        if i < n - 1:
            ax = bx + box_w
            ay = (box_top + box_bot) // 2
            arrow(d, ax, ay, ax + gap, ay, (200, 200, 200), width=3, head=10)

    # ── DEFENSES row ──
    def_y_top = 320
    def_y_bot = 390
    defenses = [
        ("Patch Mgmt",        (30, 160, 60),  0),
        ("ASLR / NX",         (30, 160, 60),  1),
        ("EDR / AV",          (30, 160, 60),  2),
        ("Sandboxing",        (30, 160, 60),  3),
        ("Integrity Mon.",    (30, 160, 60),  4),
    ]
    def_w = 180
    def_gap = 60
    def_total = n * def_w + (n - 1) * def_gap
    def_x_start = (W - def_total) // 2

    defense_centers = []
    d.text((def_x_start - 60, def_y_top + 10), "DEFENSES:", font=fM, fill=(100, 220, 120))
    for i, (name, fc, stage_i) in enumerate(defenses):
        dx = def_x_start + i * (def_w + def_gap)
        d.rounded_rectangle([dx, def_y_top, dx + def_w, def_y_bot], radius=8,
                              fill=(10, 45, 20), outline=fc, width=2)
        center_text(d, dx + def_w // 2, (def_y_top + def_y_bot) // 2, name, fS, (100, 240, 130))
        defense_centers.append((dx + def_w // 2, def_y_top))

    # Upward green arrows from defenses to stage pipeline
    for i, (dc_x, dc_y) in enumerate(defense_centers):
        sc_x, sc_y = stage_centers[i]
        arrow(d, dc_x, dc_y, sc_x, sc_y, (50, 200, 80), width=2, head=8)

    # ── Attack Chain label ──
    d.text((x_start, box_top - 22), "ATTACK CHAIN  ▶▶▶", font=fM, fill=(220, 100, 100))
    # Attacker icon (simple)
    d.ellipse([x_start - 60, box_top + 10, x_start - 30, box_top + 40], fill=(220, 80, 80))
    d.text((x_start - 68, box_top + 42), "ATTACKER", font=fXS, fill=(220, 80, 80))

    # CVSS/CVE box
    d.rectangle([60, 430, 400, 530], fill=(15, 25, 50), outline=(80, 120, 200), width=2)
    d.text((70, 438), "CVE Scoring (CVSS v3.1):", font=fM, fill=(150, 180, 255))
    d.text((70, 460), "AV:N / AC:L / PR:N / UI:N / S:C / C:H / I:H / A:H", font=fXS, fill=(180, 200, 255))
    d.text((70, 478), "= CVSS Score: 10.0  (Critical)", font=fS, fill=(255, 80, 80))
    d.text((70, 498), "Example: CVE-2016-5195 (Dirty COW) — CVSS 7.8 High", font=fXS, fill=(200, 180, 255))
    d.text((70, 515), "Example: CVE-2019-5736 (runc) — CVSS 8.6 High", font=fXS, fill=(200, 180, 255))

    # Patch management note
    d.rectangle([450, 430, 900, 530], fill=(10, 35, 15), outline=(50, 180, 80), width=2)
    d.text((460, 438), "Primary Defense: Patch Management", font=fM, fill=(100, 220, 120))
    d.text((460, 460), "• Apply OS patches within 24h for Critical CVEs", font=fXS, fill=(150, 220, 160))
    d.text((460, 478), "• Use LinPEAS/WinPEAS to find local privesc vectors", font=fXS, fill=(150, 220, 160))
    d.text((460, 496), "• Principle of Least Privilege reduces attack surface", font=fXS, fill=(150, 220, 160))
    d.text((460, 514), "• Exploit mitigations: ASLR, NX/DEP, SMEP, SMAP", font=fXS, fill=(150, 220, 160))

    img.save(f"{OUT}/ch09-vulnerabilities.png")
    print("Saved ch09-vulnerabilities.png")

# ─────────────────────────────────────────────────────────────────
# DIAGRAM 10 — Windows Security Architecture
# ─────────────────────────────────────────────────────────────────
def diag10():
    img, d = new_img()
    fL  = get_font(22, bold=True)
    fM  = get_font(14, bold=True)
    fS  = get_font(12)
    fXS = get_font(10)

    title_bar(d, "WINDOWS SECURITY ARCHITECTURE", fL)

    GOLD   = (255, 200, 60)
    LBLUE  = (60, 130, 220)
    DBLUE  = (30, 70, 160)
    DKBLUE = (15, 40, 100)
    RED    = (200, 60, 60)
    GREEN  = (60, 200, 100)

    layer_defs = [
        # (y_top, height, bg, border, label, label_color)
        (68,  95,  (15, 35, 80),   LBLUE,  "USER APPLICATIONS",     (180, 210, 255)),
        (168, 75,  (25, 45, 20),   GREEN,  "SECURITY SERVICES",     (150, 230, 150)),
        (248, 90,  (10, 25, 70),   DBLUE,  "KERNEL MODE",           (120, 170, 255)),
        (343, 80,  (30, 15, 60),   GOLD,   "SECURITY KERNEL",       GOLD),
        (428, 80,  (10, 10, 40),   (80,80,80), "HARDWARE SECURITY", (180, 180, 220)),
    ]

    for y0, lh, bg, border, label, lc in layer_defs:
        d.rectangle([10, y0, W - 10, y0 + lh], fill=bg, outline=border, width=2)
        # Left label strip
        d.rectangle([10, y0, 165, y0 + lh], fill=tuple(max(0, c - 10) for c in bg), outline=border, width=1)
        d.text((15, y0 + lh // 2 - 8), label, font=fXS, fill=lc)

    # ── Layer 1: User Applications ──
    apps = [("Win32 API", LBLUE), (".NET Runtime", LBLUE), ("UWP Apps", LBLUE), ("Win64 Apps", LBLUE)]
    for i, (app, ac) in enumerate(apps):
        ax = 175 + i * 220
        d.rounded_rectangle([ax, 78, ax + 180, 150], radius=8, fill=(20, 50, 110), outline=ac, width=2)
        center_text(d, ax + 90, 114, app, fS, (200, 220, 255))

    # ── Layer 2: Security Services ──
    sec_svc = [
        ("Windows Security Ctr", GREEN),
        ("UAC", GREEN),
        ("Windows Defender", GREEN),
        ("Credential Guard", GOLD),
    ]
    for i, (svc, sc) in enumerate(sec_svc):
        sx = 175 + i * 280
        d.rounded_rectangle([sx, 176, sx + 240, 235], radius=8, fill=(15, 40, 15), outline=sc, width=2)
        center_text(d, sx + 120, 205, svc, fS, (180, 230, 180) if sc == GREEN else GOLD)

    # ── Boundary line: User Mode / Kernel Mode ──
    d.line([(0, 248), (W, 248)], fill=(255, 80, 80), width=3)
    d.text((W // 2 - 150, 237), "── User Mode / Kernel Mode Boundary ──", font=fXS, fill=(255, 100, 100))

    # ── Layer 3: Kernel Mode ──
    kern_comps = [("Win32k.sys", DBLUE), ("NTOSKRNL.EXE", DBLUE), ("HAL", DBLUE), ("Device Drivers", DBLUE)]
    for i, (kc, kcolor) in enumerate(kern_comps):
        kx = 175 + i * 270
        d.rounded_rectangle([kx, 258, kx + 230, 328], radius=8, fill=(10, 25, 70), outline=kcolor, width=2)
        center_text(d, kx + 115, 293, kc, fS, (150, 180, 255))

    # ── Layer 4: Security Kernel ──
    sk_comps = [
        ("LSA", GOLD),
        ("SAM", GOLD),
        ("SRM — Security\nRef. Monitor", GOLD),
        ("Token Manager", GOLD),
    ]
    for i, (sc, sc_color) in enumerate(sk_comps):
        sx = 175 + i * 270
        lines = sc.split("\n")
        d.rounded_rectangle([sx, 351, sx + 230, 418], radius=8, fill=(30, 15, 55), outline=sc_color, width=2)
        if len(lines) == 1:
            center_text(d, sx + 115, 384, lines[0], fS, GOLD)
        else:
            center_text(d, sx + 115, 370, lines[0], fS, GOLD)
            center_text(d, sx + 115, 392, lines[1], fXS, GOLD)

    # ── Boundary line: Kernel / Hardware ──
    d.line([(0, 428), (W, 428)], fill=(100, 100, 200), width=3)
    d.text((W // 2 - 150, 417), "─── Kernel / Hardware Boundary ───", font=fXS, fill=(140, 140, 220))

    # ── Layer 5: Hardware Security ──
    hw_comps = [("TPM 2.0", (180, 180, 220)), ("Secure Boot", (180, 180, 220)), ("VBS — Virtualization\nBased Security", (180, 180, 220)), ("Intel SGX / AMD SEV", (180, 180, 220))]
    for i, (hc, hcolor) in enumerate(hw_comps):
        hx = 175 + i * 290
        lines = hc.split("\n")
        d.rounded_rectangle([hx, 436, hx + 250, 500], radius=8, fill=(8, 8, 38), outline=(100,100,160), width=2)
        if len(lines) == 1:
            center_text(d, hx + 125, 468, lines[0], fS, hcolor)
        else:
            center_text(d, hx + 125, 454, lines[0], fS, hcolor)
            center_text(d, hx + 125, 472, lines[1], fXS, hcolor)

    # ── Key security attack targets ──
    d.rectangle([30, 515, 500, 650], fill=(15, 10, 30), outline=(200, 80, 80), width=2)
    d.text((40, 522), "⚠  ATTACKER TARGETS:", font=fM, fill=(255, 100, 100))
    targets = [
        "LSASS.exe  — credential theft (Mimikatz)",
        "SAM db     — pass-the-hash (NTLM)",
        "KRBTGT     — Golden Ticket (Kerberos)",
        "UAC bypass — fodhelper / eventvwr",
        "NTLM Relay — SMB coerce attacks",
    ]
    for i, t in enumerate(targets):
        d.text((45, 544 + i * 20), t, font=fXS, fill=(255, 150, 150))

    # ── Key event IDs ──
    d.rectangle([520, 515, 980, 650], fill=(10, 25, 15), outline=(60, 180, 100), width=2)
    d.text((530, 522), "Key Windows Event IDs:", font=fM, fill=(100, 220, 120))
    evts = [
        "4624 — Logon success",
        "4625 — Logon failure",
        "4648 — Explicit credential logon",
        "4672 — Special privileges assigned",
        "4688 — Process creation",
        "4720 — User account created",
        "4740 — Account locked out",
    ]
    for i, ev in enumerate(evts):
        col = 530 if i < 4 else 750
        row = (i % 4)
        d.text((col, 544 + row * 26), ev, font=fXS, fill=(150, 230, 170))

    # ── VBS / Credential Guard highlight ──
    d.rectangle([990, 515, 1380, 650], fill=(20, 15, 5), outline=GOLD, width=2)
    d.text((1000, 522), "Credential Guard (VBS):", font=fM, fill=GOLD)
    d.text((1005, 545), "Isolates NTLM/Kerberos secrets", font=fXS, fill=(255, 220, 150))
    d.text((1005, 563), "in separate Hyper-V partition", font=fXS, fill=(255, 220, 150))
    d.text((1005, 581), "Even LSASS cannot access", font=fXS, fill=(255, 220, 150))
    d.text((1005, 599), "plaintext credentials", font=fXS, fill=(255, 220, 150))
    d.text((1005, 620), "Requires: UEFI + VT-x/AMD-V", font=fXS, fill=(200, 170, 100))
    d.text((1005, 638), "             + TPM 2.0", font=fXS, fill=(200, 170, 100))

    img.save(f"{OUT}/ch10-windows-security.png")
    print("Saved ch10-windows-security.png")

if __name__ == "__main__":
    diag6()
    diag7()
    diag8()
    diag9()
    diag10()
    print("All diagrams generated.")
