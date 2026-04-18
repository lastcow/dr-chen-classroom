#!/usr/bin/env python3
"""Generate all 5 SCIA-360 chapter diagrams using Pillow."""

from PIL import Image, ImageDraw, ImageFont
import math
import os

OUTDIR = "/home/john/wiki/docs/scia-360/img"
W, H = 1400, 750
BG = (13, 27, 42)  # #0d1b2a

def get_font(size, bold=False):
    """Try to load a TTF font, fall back to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

def draw_arrow(draw, x1, y1, x2, y2, color, width=2, head=12):
    draw.line([(x1,y1),(x2,y2)], fill=color, width=width)
    angle = math.atan2(y2-y1, x2-x1)
    for side in [0.4, -0.4]:
        ax = x2 - head * math.cos(angle - side)
        ay = y2 - head * math.sin(angle - side)
        draw.line([(x2,y2),(int(ax),int(ay))], fill=color, width=width)

def centered_text(draw, text, cx, cy, font, color):
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    draw.text((cx - tw//2, cy - th//2), text, fill=color, font=font)

def rounded_rect(draw, x1, y1, x2, y2, fill, outline, radius=10, width=2):
    draw.rounded_rectangle([x1,y1,x2,y2], radius=radius, fill=fill, outline=outline, width=width)

# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 1 — OS Security Architecture: Layers of Defense
# ─────────────────────────────────────────────────────────────────────────────
def diagram1():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font  = get_font(28, bold=True)
    label_font  = get_font(18, bold=True)
    small_font  = get_font(14)
    tiny_font   = get_font(12)

    # Title
    centered_text(d, "OS SECURITY ARCHITECTURE — LAYERS OF DEFENSE", W//2, 38, title_font, (200,220,255))

    cx, cy = W//2, H//2 + 20
    # Rings (outermost to innermost): radii
    rings = [
        (295, (180, 30, 30),   (255, 80, 80),   "NETWORK PERIMETER",
         ["Firewall", "IDS/IPS", "VPN Gateway", "DDoS Mitigation"]),
        (220, (180, 100, 0),   (255, 165, 0),   "APPLICATION LAYER",
         ["ASLR/NX", "Sandboxing", "Code Signing", "AppArmor/SELinux"]),
        (145, (0, 120, 60),    (0, 210, 100),   "OS KERNEL",
         ["Syscall Filter", "Memory Protection", "DAC/MAC", "Audit Log"]),
        (70,  (0, 60, 160),    (60, 140, 255),  "HARDWARE",
         ["TPM", "Secure Boot", "UEFI", "HSM"]),
    ]

    # Draw rings from outside in
    for radius, fill_dark, fill_bright, name, controls in rings:
        r = radius
        # Ellipse (slightly squashed for depth effect)
        d.ellipse([cx-r, cy-int(r*0.72), cx+r, cy+int(r*0.72)],
                  fill=fill_dark, outline=fill_bright, width=3)

    # White out core
    d.ellipse([cx-68, cy-int(68*0.72), cx+68, cy+int(68*0.72)], fill=(0,60,160))

    # Labels inside rings
    label_positions = [
        (295, "NETWORK PERIMETER", (255,130,130), -int(295*0.72)+18),
        (220, "APPLICATION LAYER", (255,200,80),  -int(220*0.72)+18),
        (145, "OS  KERNEL",        (80,255,160),  -int(145*0.72)+16),
        (70,  "HARDWARE",          (130,190,255), -int(70*0.72)+14),
    ]
    for radius, name, col, y_off in label_positions:
        centered_text(d, name, cx, cy + y_off, label_font, col)

    # Controls callouts — right side
    callout_data = [
        (295, (255,100,100), ["● Firewall / IDS / IPS", "● VPN Termination", "● DDoS Protection"]),
        (220, (255,180,50),  ["● App Sandboxing", "● Code Signing", "● AppArmor / SELinux"]),
        (145, (50,220,120),  ["● Syscall Filtering", "● Memory Isolation", "● DAC / MAC Policies"]),
        (70,  (80,160,255),  ["● TPM / Secure Boot", "● UEFI Lockdown", "● Hardware Crypto"]),
    ]
    x_right = cx + 340
    y_starts = [cy - 290, cy - 190, cy - 100, cy - 20]
    for i, (r, col, items) in enumerate(callout_data):
        ys = y_starts[i]
        # Connector line to ring edge
        d.line([(cx + r + 5, cy), (x_right - 10, ys + len(items)*9)], fill=col, width=1)
        for j, item in enumerate(items):
            d.text((x_right, ys + j*20), item, fill=col, font=small_font)

    # Left side — attack vectors
    d.text((30, 100), "ATTACK VECTORS", fill=(200,200,255), font=label_font)
    attacks = [
        (255,80,80,  "→ Network Intrusion / DDoS"),
        (255,165,0,  "→ Malicious App / Supply Chain"),
        (0,210,100,  "→ Kernel Exploits / Rootkits"),
        (60,140,255, "→ Firmware / Hardware Implants"),
    ]
    for i,(r,g,b,txt) in enumerate(attacks):
        d.text((30, 130 + i*28), txt, fill=(r,g,b), font=small_font)

    # Bottom legend
    d.text((30, H-50), "Defense-in-Depth: Each layer provides independent security controls.",
           fill=(140,160,180), font=tiny_font)
    d.text((30, H-30), "Compromise of outer layer does NOT grant access to inner layers.",
           fill=(140,160,180), font=tiny_font)

    img.save(os.path.join(OUTDIR, "ch01-os-security-layers.png"))
    print("✓ Diagram 1 saved")


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 2 — Process Lifecycle & Security States
# ─────────────────────────────────────────────────────────────────────────────
def diagram2():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font = get_font(26, bold=True)
    node_font  = get_font(17, bold=True)
    label_font = get_font(14, bold=True)
    small_font = get_font(13)
    tiny_font  = get_font(12)

    centered_text(d, "PROCESS LIFECYCLE & SECURITY STATES", W//2, 36, title_font, (200,220,255))

    # ── Privilege boundary ──
    divider_y = 390
    # Top = PRIVILEGED (ring 0), Bottom = USER (ring 3)
    # Background zones
    d.rectangle([20, 55, W-20, divider_y-1], fill=(10, 30, 55))
    d.rectangle([20, divider_y, W-20, H-20], fill=(20, 15, 40))

    # Dashed boundary line
    for x in range(20, W-20, 18):
        d.line([(x, divider_y), (min(x+10, W-20), divider_y)], fill=(200,200,60), width=2)

    d.text((30, 62), "⬡ PRIVILEGED ZONE — Ring 0 (Kernel Mode)", fill=(80,180,255), font=label_font)
    d.text((30, divider_y+8), "⬡ USER SPACE — Ring 3 (User Mode)", fill=(180,100,255), font=label_font)

    # System Call Gate label
    centered_text(d, "◆ SYSTEM CALL GATE  ◆  PRIVILEGE CHECK  ◆  CONTEXT SWITCH", W//2, divider_y, small_font, (240,220,60))

    # ── Process state nodes ──
    # Positions: NEW(left), READY, RUNNING(center), WAITING(right), TERMINATED(far right)
    nodes = {
        "NEW":        ("NEW",        130,  270, (0,180,120),   (0,255,160)),
        "READY":      ("READY",      340,  160, (0,120,200),   (60,180,255)),
        "RUNNING":    ("RUNNING",    580,  270, (180,100,0),   (255,165,0)),
        "WAITING":    ("WAITING",    820,  160, (0,120,200),   (60,180,255)),
        "TERMINATED": ("TERMINATED", 1050, 270, (160,30,30),   (220,60,60)),
    }
    # Kernel-side node
    kernel_node = ("KERNEL\nSCHEDULER", 580, 155, (20,60,140), (80,140,255))

    NW, NH = 110, 50

    def draw_node(name, nx, ny, fill, outline):
        x1, y1 = nx - NW//2, ny - NH//2
        x2, y2 = nx + NW//2, ny + NH//2
        rounded_rect(d, x1, y1, x2, y2, fill, outline, radius=12, width=2)
        for i, line in enumerate(name.split("\n")):
            lf = get_font(15, bold=True)
            bbox = d.textbbox((0,0), line, font=lf)
            tw = bbox[2]-bbox[0]
            yoff = -8 if "\n" in name else 0
            d.text((nx - tw//2, ny + yoff + i*18 - 8), line, fill=(230,240,255), font=lf)

    for name, nx, ny, fill, outline in nodes.values():
        draw_node(name, nx, ny, fill, outline)

    # Kernel scheduler node (in privileged zone)
    kname, knx, kny, kfill, koutline = kernel_node
    draw_node(kname, knx, kny, kfill, koutline)

    # ── Arrows ──
    CYAN   = (60,210,255)
    ORANGE = (255,165,0)
    GREEN  = (60,220,100)
    RED    = (220,80,80)

    # NEW → READY
    draw_arrow(d, 185, 270, 285, 200, GREEN, width=2)
    d.text((195, 220), "admitted", fill=GREEN, font=tiny_font)

    # READY → RUNNING
    draw_arrow(d, 395, 185, 520, 250, CYAN, width=2)
    d.text((430, 195), "scheduled", fill=CYAN, font=tiny_font)

    # RUNNING → WAITING
    draw_arrow(d, 635, 245, 765, 185, ORANGE, width=2)
    d.text((670, 195), "I/O wait", fill=ORANGE, font=tiny_font)

    # WAITING → READY
    draw_arrow(d, 820, 135, 400, 135, CYAN, width=2)
    d.text((580, 110), "I/O complete", fill=CYAN, font=tiny_font)

    # RUNNING → TERMINATED
    draw_arrow(d, 635, 270, 995, 270, RED, width=2)
    d.text((780, 250), "exit()", fill=RED, font=tiny_font)

    # RUNNING ↔ KERNEL SCHEDULER
    draw_arrow(d, 555, 220, 555, 182, (150,150,255), width=2)
    draw_arrow(d, 605, 182, 605, 220, (150,150,255), width=2)
    d.text((615, 195), "syscall /\npreempt", fill=(180,160,255), font=tiny_font)

    # READY → KERNEL
    draw_arrow(d, 370, 135, 520, 135, (100,140,255), width=1)

    # ── User-space process info box (bottom) ──
    info_boxes = [
        (120, 470, "PCB CONTENTS", (20,50,100), (60,140,255),
         ["PID / PPID", "UID / GID / EUID", "Open FDs", "Memory Maps", "Signal Handlers"]),
        (380, 470, "SECURITY FIELDS", (50,20,80), (160,80,255),
         ["Credentials", "Capabilities", "Seccomp Filter", "Namespaces", "Cgroups"]),
        (640, 470, "IPC CHANNELS", (20,60,30), (60,200,100),
         ["Pipes / FIFOs", "Shared Memory", "Message Queues", "Unix Sockets", "Signals"]),
        (900, 470, "INJECTION ATTACKS", (80,20,20), (220,80,80),
         ["ptrace inject", "LD_PRELOAD", "DLL injection", "/proc/mem write", "Signal abuse"]),
        (1150, 470, "DEFENSES", (20,60,50), (60,200,160),
         ["seccomp-bpf", "Namespaces", "AppArmor", "auditd", "Capabilities"]),
    ]
    BW, BH = 190, 200
    for bx, by, btitle, bfill, boutline, items in info_boxes:
        rounded_rect(d, bx-BW//2, by, bx+BW//2, by+BH, bfill, boutline, radius=8, width=2)
        centered_text(d, btitle, bx, by+18, get_font(13, bold=True), boutline)
        d.line([(bx-BW//2+8, by+32), (bx+BW//2-8, by+32)], fill=boutline, width=1)
        for i, item in enumerate(items):
            d.text((bx-BW//2+10, by+42+i*28), f"• {item}", fill=(200,210,225), font=tiny_font)

    img.save(os.path.join(OUTDIR, "ch02-process-security.png"))
    print("✓ Diagram 2 saved")


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 3 — Virtual Memory Layout & Security Controls
# ─────────────────────────────────────────────────────────────────────────────
def diagram3():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font = get_font(26, bold=True)
    label_font = get_font(16, bold=True)
    small_font = get_font(14)
    tiny_font  = get_font(12)
    addr_font  = get_font(13)

    centered_text(d, "VIRTUAL MEMORY LAYOUT & SECURITY CONTROLS", W//2, 34, title_font, (200,220,255))

    # Memory map column
    MX1, MX2 = 320, 660
    TOP_Y = 65
    BOT_Y = H - 40

    segments = [
        # (label, height_frac, fill, outline, addr_high, addr_low, note)
        ("KERNEL SPACE",        0.18, (10,30,80),   (60,120,255),  "0xFFFF...FFFF", "0xC000...0000", "Ring 0 — Kernel Only\nKASLR randomizes base"),
        ("─── User/Kernel Boundary ───", 0.03, (40,40,10), (220,220,40), "", "", ""),
        ("STACK  ↓  grows down",0.14, (100,20,20),  (220,60,60),   "0x7FFF...FFFF", "~random (ASLR)",  "Stack Canary\nNX bit enforced"),
        ("Memory-Mapped Files", 0.10, (60,30,80),   (160,80,200),  "mmap region",   "(ASLR shifted)",  "Shared libs,\nAnon mappings"),
        ("HEAP  ↑  grows up",   0.14, (100,60,0),   (255,165,0),   "brk() limit",   "~random (ASLR)",  "ASLR randomizes\nheap base"),
        ("BSS / Data Segment",  0.09, (30,70,30),   (80,180,80),   ".bss/.data",    "Initialized data","Global variables\nzero-init"),
        ("Text / Code Segment", 0.11, (20,80,50),   (40,200,100),  ".text",         "0x0000...0000+",  "NX: read/exec\nno write"),
    ]

    total_height = BOT_Y - TOP_Y
    y = TOP_Y
    seg_rects = {}

    for seg in segments:
        label, frac, fill, outline, addr_hi, addr_lo, note = seg
        sh = int(total_height * frac)
        x1, y1, x2, y2 = MX1, y, MX2, y + sh

        if "Boundary" in label:
            # Dashed line
            for xd in range(MX1, MX2, 14):
                d.line([(xd, y+sh//2), (min(xd+8, MX2), y+sh//2)], fill=outline, width=3)
            centered_text(d, label, (MX1+MX2)//2, y+sh//2, get_font(13, bold=True), outline)
        else:
            rounded_rect(d, x1, y1, x2, y2, fill, outline, radius=6, width=2)
            # Main label
            centered_text(d, label, (x1+x2)//2, (y1+y2)//2 - 8, small_font, (230,240,255))

        seg_rects[label[:10]] = (x1, y1, x2, y2)
        y += sh

    # Address labels (left side)
    y = TOP_Y
    for seg in segments:
        label, frac, fill, outline, addr_hi, addr_lo, note = seg
        sh = int(total_height * frac)
        if addr_hi:
            d.text((MX1-200, y+4), addr_hi, fill=(140,160,180), font=addr_font)
        if addr_lo and not "Boundary" in label:
            d.text((MX1-200, y+sh-18), addr_lo, fill=(100,120,140), font=addr_font)
        y += sh

    # Right side — security annotations
    annots = [
        (TOP_Y + 30,   (60,120,255),  "KASLR", "Kernel ASLR randomizes\nkernel base address"),
        (TOP_Y + 165,  (220,60,60),   "Stack Canary", "GCC inserts random\nvalue before ret addr"),
        (TOP_Y + 225,  (220,60,60),   "NX bit", "Stack marked non-exec;\nblocks shellcode"),
        (TOP_Y + 330,  (255,165,0),   "ASLR", "Randomizes heap, stack,\nmmap base addresses"),
        (TOP_Y + 490,  (40,200,100),  "NX bit", "Code pages: read+exec\nData pages: read+write"),
    ]
    for ay, col, title, desc in annots:
        d.line([(MX2+5, ay+10), (MX2+60, ay+10)], fill=col, width=2)
        d.text((MX2+65, ay), title, fill=col, font=get_font(14, bold=True))
        d.text((MX2+65, ay+18), desc, fill=(170,185,200), font=tiny_font)

    # Buffer overflow attack arrow
    bof_y = TOP_Y + int(total_height * (0.18+0.03+0.07))
    draw_arrow(d, 60, bof_y - 20, MX1 - 5, bof_y + 40, (255,50,50), width=3)
    d.text((10, bof_y - 55), "BUFFER", fill=(255,80,80), font=get_font(13,bold=True))
    d.text((10, bof_y - 38), "OVERFLOW", fill=(255,80,80), font=get_font(13,bold=True))
    d.text((10, bof_y - 20), "ATTACK", fill=(255,80,80), font=get_font(13,bold=True))
    d.text((10, bof_y),  "Overwrites", fill=(200,100,100), font=tiny_font)
    d.text((10, bof_y+14),"return addr", fill=(200,100,100), font=tiny_font)

    # Stack growth arrow
    stack_top = TOP_Y + int(total_height*0.21)
    stack_bot = TOP_Y + int(total_height*0.35)
    draw_arrow(d, (MX1+MX2)//2 - 30, stack_top + 20, (MX1+MX2)//2 - 30, stack_bot - 10, (220,80,80), width=2)

    # Heap growth arrow
    heap_top = TOP_Y + int(total_height*(0.18+0.03+0.14+0.10))
    heap_bot = heap_top + int(total_height*0.14)
    draw_arrow(d, (MX1+MX2)//2 + 30, heap_bot - 10, (MX1+MX2)//2 + 30, heap_top + 10, (255,165,0), width=2)

    # Bottom note
    d.text((30, H-28), "Virtual addresses shown for 64-bit Linux (x86_64). Actual layout varies with ASLR entropy.",
           fill=(100,120,140), font=tiny_font)

    img.save(os.path.join(OUTDIR, "ch03-memory-security.png"))
    print("✓ Diagram 3 saved")


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 4 — File System Permission Model
# ─────────────────────────────────────────────────────────────────────────────
def diagram4():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font = get_font(26, bold=True)
    hdr_font   = get_font(16, bold=True)
    cell_font  = get_font(15, bold=True)
    small_font = get_font(13)
    tiny_font  = get_font(12)

    centered_text(d, "FILE SYSTEM PERMISSION MODEL", W//2, 34, title_font, (200,220,255))

    GREEN  = (0, 160, 60)
    RED    = (180, 30, 30)
    LGREEN = (60, 220, 110)
    LRED   = (255, 80, 80)
    GRAY   = (60, 70, 90)

    # ── Permission table ──
    TABLE_X = 80
    TABLE_Y = 75
    CW, RH = 130, 52  # cell width, row height

    cols = ["", "READ (r)", "WRITE (w)", "EXECUTE (x)"]
    # (row_label, R, W, X, octal_col)
    perm_sets = [
        # 755 example
        ("OWNER (u)", True,  True,  True,  "7"),
        ("GROUP (g)", True,  False, True,  "5"),
        ("OTHERS (o)",True,  False, True,  "5"),
    ]

    # Draw column headers
    for ci, ch in enumerate(cols):
        cx = TABLE_X + ci * CW + CW//2
        d.text((cx - 40, TABLE_Y + 8), ch, fill=(180,200,240), font=hdr_font)

    # Separator
    d.line([(TABLE_X, TABLE_Y+RH-4), (TABLE_X + 4*CW, TABLE_Y+RH-4)], fill=(80,100,140), width=2)

    octal_vals = []
    for ri, (rlabel, r, w, x, oct_char) in enumerate(perm_sets):
        ry = TABLE_Y + RH + ri * RH
        # Row label
        d.text((TABLE_X + 5, ry + 14), rlabel, fill=(200,220,255), font=cell_font)
        octal_vals.append(oct_char)
        for ci, allowed in enumerate([r, w, x]):
            cx1 = TABLE_X + (ci+1)*CW + 5
            cy1 = ry + 5
            cx2 = TABLE_X + (ci+2)*CW - 5
            cy2 = ry + RH - 5
            fill = GREEN if allowed else RED
            bright = LGREEN if allowed else LRED
            rounded_rect(d, cx1, cy1, cx2, cy2, fill, bright, radius=8, width=2)
            sym = ("r" if ci==0 else "w" if ci==1 else "x") if allowed else "─"
            centered_text(d, sym, (cx1+cx2)//2, (cy1+cy2)//2, cell_font, (230,240,255))

    # Octal column
    OCT_X = TABLE_X + 4*CW + 20
    d.text((OCT_X, TABLE_Y+8), "OCTAL", fill=(255,200,60), font=hdr_font)
    d.line([(OCT_X, TABLE_Y+RH-4), (OCT_X+80, TABLE_Y+RH-4)], fill=(80,100,140), width=2)
    for ri in range(3):
        ry = TABLE_Y + RH + ri * RH
        d.text((OCT_X + 25, ry+14), octal_vals[ri], fill=(255,220,80), font=get_font(26, bold=True))

    # Combined octal
    d.text((OCT_X - 10, TABLE_Y + RH + 3*RH + 15), "= 755 (rwxr-xr-x)", fill=(255,200,60), font=hdr_font)

    # ── Common octal examples ──
    EX_Y = TABLE_Y + RH*5 + 30
    examples = [
        ("755", "rwxr-xr-x", "Executables, dirs (owner full, others read+exec)", (255,200,60)),
        ("644", "rw-r--r--", "Regular files (owner read+write, others read only)", (100,200,255)),
        ("700", "rwx------", "Private files/dirs (owner only)",                    (100,255,160)),
        ("777", "rwxrwxrwx", "DANGEROUS — world-writable (avoid!)",               (255,80,80)),
        ("4755","rwsr-xr-x", "SETUID executable — runs as file owner",            (255,140,0)),
    ]
    d.text((TABLE_X, EX_Y - 22), "COMMON PERMISSION PATTERNS:", fill=(160,180,220), font=hdr_font)
    for i, (oct, sym, desc, col) in enumerate(examples):
        ey = EX_Y + i*28
        d.text((TABLE_X, ey),       oct,  fill=col,          font=cell_font)
        d.text((TABLE_X+60,  ey),   sym,  fill=(180,200,230), font=get_font(14))
        d.text((TABLE_X+200, ey),   desc, fill=(140,160,185), font=small_font)

    # ── ACL section (right side) ──
    ACL_X = 720
    ACL_Y = 80

    d.text((ACL_X, ACL_Y), "POSIX ACL EXTENSION", fill=(160,200,255), font=title_font)
    d.text((ACL_X, ACL_Y+34), "Extends beyond owner/group/other", fill=(120,150,190), font=small_font)

    acl_entries = [
        ("user::",      "rwx", (255,200,60)),
        ("user:alice",  "rw-", (100,220,255)),
        ("user:bob",    "r--", (100,220,255)),
        ("group::",     "r-x", (80,200,140)),
        ("group:devs",  "rwx", (80,200,140)),
        ("group:audit", "r--", (80,200,140)),
        ("other::",     "---", (180,80,80)),
        ("mask::",      "rwx", (200,160,60)),
    ]
    for i, (entry, perms, col) in enumerate(acl_entries):
        ay = ACL_Y + 75 + i * 38
        rounded_rect(d, ACL_X, ay, ACL_X+320, ay+30, (20,35,55), col, radius=6, width=1)
        d.text((ACL_X+10, ay+6),     entry,  fill=col,          font=get_font(14))
        d.text((ACL_X+240, ay+6),    perms,  fill=(230,240,255), font=get_font(15,bold=True))

    # getfacl / setfacl commands
    cmd_y = ACL_Y + 75 + len(acl_entries)*38 + 20
    d.text((ACL_X, cmd_y),    "$ getfacl /srv/project", fill=(80,220,120), font=get_font(13))
    d.text((ACL_X, cmd_y+22), "$ setfacl -m u:alice:rw- /srv/project", fill=(80,220,120), font=get_font(13))

    # Capabilities sidebar
    CAP_X = 1050
    CAP_Y = 80
    d.text((CAP_X, CAP_Y), "LINUX CAPABILITIES", fill=(160,200,255), font=hdr_font)
    caps = [
        ("CAP_NET_ADMIN", "Manage network interfaces"),
        ("CAP_SYS_PTRACE","Trace/debug processes"),
        ("CAP_SETUID",    "Change process UID"),
        ("CAP_NET_BIND",  "Bind ports < 1024"),
        ("CAP_DAC_OVERRIDE","Bypass file permissions"),
        ("CAP_SYS_ADMIN", "Wide admin operations"),
    ]
    for i,(cap, desc) in enumerate(caps):
        cy2 = CAP_Y + 35 + i*52
        rounded_rect(d, CAP_X, cy2, CAP_X+310, cy2+44, (15,35,60), (100,150,220), radius=6, width=1)
        d.text((CAP_X+8,  cy2+4),  cap,  fill=(120,190,255), font=get_font(13,bold=True))
        d.text((CAP_X+8,  cy2+22), desc, fill=(140,160,185), font=tiny_font)

    d.text((CAP_X, CAP_Y + 35 + len(caps)*52 + 8),
           "$ getcap /usr/bin/ping\n$ setcap cap_net_raw+ep /usr/bin/ping",
           fill=(80,220,120), font=tiny_font)

    img.save(os.path.join(OUTDIR, "ch04-filesystem-security.png"))
    print("✓ Diagram 4 saved")


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM 5 — OS Authentication Flow
# ─────────────────────────────────────────────────────────────────────────────
def diagram5():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font = get_font(26, bold=True)
    box_font   = get_font(15, bold=True)
    small_font = get_font(13)
    tiny_font  = get_font(12)

    centered_text(d, "OS AUTHENTICATION FLOW", W//2, 34, title_font, (200,220,255))

    BLUE   = (20, 60, 140)
    LBLUE  = (60, 140, 255)
    GREEN  = (15, 90, 40)
    LGREEN = (50, 210, 100)
    RED    = (120, 20, 20)
    LRED   = (220, 60, 60)
    ORANGE = (140, 80, 0)
    LORNG  = (255, 165, 0)
    PURPLE = (80, 20, 120)
    LPURP  = (180, 80, 255)

    BW, BH = 160, 44

    def box(cx, cy, text, fill, outline, lines=1):
        x1, y1 = cx-BW//2, cy-BH//2
        x2, y2 = cx+BW//2, cy+BH//2
        if lines == 2:
            y1 -= 10; y2 += 10
        rounded_rect(d, x1, y1, x2, y2, fill, outline, radius=8, width=2)
        parts = text.split("\n")
        for i, part in enumerate(parts):
            off = (i - (len(parts)-1)/2) * 18
            centered_text(d, part, cx, cy + off, box_font, (225,235,255))

    def arrow(x1, y1, x2, y2, color=LBLUE, label="", lside="right"):
        draw_arrow(d, x1, y1, x2, y2, color, width=2)
        if label:
            mx, my = (x1+x2)//2, (y1+y2)//2
            lf = get_font(11)
            bbox = d.textbbox((0,0), label, font=lf)
            tw = bbox[2]-bbox[0]
            if lside == "right":
                d.text((mx+4, my-8), label, fill=color, font=lf)
            else:
                d.text((mx-tw-4, my-8), label, fill=color, font=lf)

    # ── Main flow column (center) ──
    cx = 420

    # 1. User enters credentials
    box(cx, 95, "USER ENTERS\nCREDENTIALS", BLUE, LBLUE, lines=2)
    d.text((cx-75, 118), "keyboard / biometric / token", fill=(100,140,200), font=tiny_font)

    arrow(cx, 118, cx, 152)

    # 2. Login / getty
    box(cx, 172, "login / getty\n/ sshd", (30,50,90), (100,160,240), lines=2)

    arrow(cx, 195, cx, 228)

    # 3. PAM Stack
    PAM_Y = 260
    box(cx, PAM_Y, "PAM STACK\n/etc/pam.d/", PURPLE, LPURP, lines=2)

    # PAM legend box
    pam_info_x = cx + 220
    rounded_rect(d, pam_info_x-100, PAM_Y-70, pam_info_x+180, PAM_Y+80, (30,15,50), LPURP, radius=8, width=1)
    d.text((pam_info_x-90, PAM_Y-62), "PAM MODULE TYPES:", fill=LPURP, font=get_font(12,bold=True))
    for i, (mtype, col) in enumerate([("auth — verify identity",(180,120,255)),
                                       ("account — check validity",(160,100,240)),
                                       ("password — update creds",(140,90,220)),
                                       ("session — env setup",(120,80,200))]):
        d.text((pam_info_x-90, PAM_Y-44+i*26), f"• {mtype}", fill=col, font=tiny_font)

    d.line([(cx+BW//2, PAM_Y), (pam_info_x-100, PAM_Y)], fill=LPURP, width=1)

    arrow(cx, PAM_Y+22, cx, PAM_Y+55)

    # 4. Three PAM modules (fan out)
    MOD_Y = PAM_Y + 90
    modules = [
        (cx-260, MOD_Y, "PASSWORD\nMODULE\npam_unix.so", (30,50,100), (80,160,255)),
        (cx,     MOD_Y, "BIOMETRIC\nMODULE\npam_fprintd", (50,30,80), (160,100,255)),
        (cx+260, MOD_Y, "TOKEN MODULE\nTOTP/FIDO2\npam_oath.so", (30,60,50), (80,200,130)),
    ]
    # Fan-out arrows
    for mx, my, _, _, outline in modules:
        draw_arrow(d, cx, PAM_Y+55, mx, my-30, outline, width=2)

    for mx, my, text, fill, outline in modules:
        lines = text.count("\n")+1
        x1,y1 = mx-80, my-42
        x2,y2 = mx+80, my+42
        rounded_rect(d, x1, y1, x2, y2, fill, outline, radius=8, width=2)
        parts = text.split("\n")
        for i,part in enumerate(parts):
            off = (i-1)*17
            centered_text(d, part, mx, my+off, get_font(13, bold=True) if i==0 else tiny_font, (220,230,255))

    # Arrows from modules to credential validation
    VAL_Y = MOD_Y + 90
    for mx, my, _, _, outline in modules:
        draw_arrow(d, mx, my+42, cx, VAL_Y-22, outline, width=2)

    # /etc/shadow reference
    shadow_x = cx - 310
    rounded_rect(d, shadow_x-90, VAL_Y-80, shadow_x+90, VAL_Y+20, (10,30,10), (60,180,60), radius=6, width=1)
    d.text((shadow_x-80, VAL_Y-70), "/etc/passwd", fill=(80,200,100), font=tiny_font)
    d.text((shadow_x-80, VAL_Y-50), "/etc/shadow", fill=(80,200,100), font=tiny_font)
    d.text((shadow_x-80, VAL_Y-30), "$6$salt$hash...", fill=(60,160,80), font=tiny_font)
    d.text((shadow_x-80, VAL_Y-10), "SHA-512 + salt", fill=(60,160,80), font=tiny_font)
    d.line([(shadow_x+90, VAL_Y-30), (cx-BW//2-5, VAL_Y)], fill=(60,180,60), width=1)

    # 5. Credential Validation
    box(cx, VAL_Y, "CREDENTIAL\nVALIDATION", (30,70,30), LGREEN, lines=2)

    # 6. Decision diamond
    DEC_Y = VAL_Y + 80
    dp = 30
    d.polygon([(cx, DEC_Y-dp), (cx+dp*2, DEC_Y), (cx, DEC_Y+dp), (cx-dp*2, DEC_Y)],
              fill=(40,60,20), outline=(180,220,60))
    centered_text(d, "VALID?", cx, DEC_Y, get_font(14, bold=True), (200,230,80))
    arrow(cx, VAL_Y+22, cx, DEC_Y-dp)

    # ── SUCCESS path (right) ──
    SUC_X = cx + 240
    arrow(cx+dp*2, DEC_Y, SUC_X-BW//2, DEC_Y, LGREEN, label="YES")
    box(SUC_X, DEC_Y, "SESSION\nCREATED", GREEN, LGREEN, lines=2)
    arrow(SUC_X, DEC_Y+22, SUC_X, DEC_Y+65)
    box(SUC_X, DEC_Y+88, "USER ENV\nLOADED", (10,80,40), (40,200,90), lines=2)
    d.text((SUC_X-75, DEC_Y+112), ".bashrc, PATH,\ngroups, limits", fill=(60,180,80), font=tiny_font)

    # Audit log (success)
    arrow(SUC_X, DEC_Y+110, SUC_X+100, DEC_Y+110, LGREEN)
    rounded_rect(d, SUC_X+100, DEC_Y+94, SUC_X+240, DEC_Y+128, (10,40,20), LGREEN, radius=6, width=1)
    d.text((SUC_X+108, DEC_Y+100), "syslog: AUTH", fill=LGREEN, font=tiny_font)
    d.text((SUC_X+108, DEC_Y+116), "session opened", fill=(60,160,80), font=tiny_font)

    # ── FAILURE path (left) ──
    FAIL_X = cx - 240
    arrow(cx-dp*2, DEC_Y, FAIL_X+BW//2, DEC_Y, LRED, label="NO", lside="left")
    box(FAIL_X, DEC_Y, "ATTEMPT\nCOUNTER ++", RED, LRED, lines=2)
    arrow(FAIL_X, DEC_Y+22, FAIL_X, DEC_Y+65)
    box(FAIL_X, DEC_Y+88, "LOCKOUT\nCHECK", (100,30,10), LORNG, lines=2)
    d.text((FAIL_X-75, DEC_Y+112), "pam_faillock\nmax_retries=3", fill=LORNG, font=tiny_font)
    arrow(FAIL_X, DEC_Y+110, FAIL_X, DEC_Y+152)
    box(FAIL_X, DEC_Y+175, "LOG EVENT\n/var/log/auth", RED, LRED, lines=2)
    d.text((FAIL_X-80, DEC_Y+200), "journalctl -u ssh\ntail /var/log/auth.log", fill=(180,80,80), font=tiny_font)

    # Windows / Kerberos note bottom right
    kr_x, kr_y = 1100, 400
    rounded_rect(d, kr_x-10, kr_y-10, kr_x+270, kr_y+220, (15,20,45), (80,120,220), radius=8, width=1)
    d.text((kr_x, kr_y), "WINDOWS AUTH STACK", fill=(100,160,255), font=get_font(13,bold=True))
    win_items = [
        "LSA (Local Security Authority)",
        "LSASS process handles tokens",
        "SAM DB → local accounts",
        "NTLM: challenge-response",
        "Kerberos: TGT → service ticket",
        "Active Directory domain auth",
        "LSASS targeted by Mimikatz",
    ]
    for i, item in enumerate(win_items):
        d.text((kr_x+5, kr_y+22+i*26), f"• {item}", fill=(130,160,210), font=tiny_font)

    img.save(os.path.join(OUTDIR, "ch05-authentication-flow.png"))
    print("✓ Diagram 5 saved")


if __name__ == "__main__":
    diagram1()
    diagram2()
    diagram3()
    diagram4()
    diagram5()
    print("\nAll 5 diagrams generated successfully.")
