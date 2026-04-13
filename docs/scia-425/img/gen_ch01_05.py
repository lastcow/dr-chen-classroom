#!/usr/bin/env python3
"""Generate 5 technical diagrams for SCIA 425 chapters 01-05."""

from PIL import Image, ImageDraw, ImageFont
import os, math

OUT = "/home/john/wiki/docs/scia-425/img"
W, H = 1400, 750
BG = (13, 27, 42)

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def draw_text_centered(draw, text, cx, cy, font, fill):
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw//2, cy - th//2), text, font=font, fill=fill)

def draw_rounded_rect(draw, x1, y1, x2, y2, radius, fill, outline=None, width=2):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

def draw_arrow(draw, x1, y1, x2, y2, color, width=3, head_size=12):
    draw.line([(x1,y1),(x2,y2)], fill=color, width=width)
    angle = math.atan2(y2-y1, x2-x1)
    for da in [0.4, -0.4]:
        ax = x2 - head_size*math.cos(angle-da)
        ay = y2 - head_size*math.sin(angle-da)
        draw.line([(x2,y2),(int(ax),int(ay))], fill=color, width=width)

# ─────────────────────────────────────────────
# DIAGRAM 1 — Software Assurance Lifecycle
# ─────────────────────────────────────────────
def gen_diagram1():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title_font = get_font(32, bold=True)
    stage_font = get_font(14, bold=True)
    label_font = get_font(11)
    cost_font  = get_font(12, bold=True)

    draw_text_centered(d, "SOFTWARE ASSURANCE LIFECYCLE", W//2, 36, title_font, (220,230,255))

    stages = [
        ("REQUIREMENTS", (58,123,213),  ["Security Reqs","Quality Reqs","Stakeholder Input"]),
        ("DESIGN",       (142,68,173),  ["Threat Modeling","Secure Architecture","Design Review"]),
        ("IMPLEMENT",    (230,126,34),  ["Secure Coding","Code Review","Unit Tests"]),
        ("VERIFICATION", (23,162,184),  ["Static Analysis","Integration Tests","Peer Review"]),
        ("VALIDATION",   (39,174,96),   ["Pen Testing","Acceptance Tests","UAT"]),
        ("MAINTENANCE",  (200,169,81),  ["Patch Mgmt","Monitoring","Incident Response"]),
    ]

    n = len(stages)
    box_w, box_h = 165, 95
    gap = 22
    total_w = n*box_w + (n-1)*gap
    start_x = (W - total_w)//2
    box_y = 360

    costs = [1, 6, 25, 100, 500, 2000]
    max_cost = 2000
    curve_pts = []
    for i in range(n):
        cx = start_x + i*(box_w+gap) + box_w//2
        norm = math.log(costs[i]+1)/math.log(max_cost+1)
        cy = int(290 - norm*175)
        curve_pts.append((cx,cy))

    for i in range(len(curve_pts)-1):
        d.line([curve_pts[i], curve_pts[i+1]], fill=(255,100,100), width=3)

    cost_labels = ["1×","6×","25×","100×","500×","2000×"]
    for i,(cx,cy) in enumerate(curve_pts):
        r = 5 + int((i/5)*14)
        d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(255,80,80))
        draw_text_centered(d, cost_labels[i], cx, cy-r-11, get_font(11,bold=True), (255,190,190))

    d.text((28, 115), "Relative Cost", font=cost_font, fill=(255,180,180))
    d.text((28, 133), "to Fix Defect →", font=cost_font, fill=(255,180,180))

    for i,(name,color,labels) in enumerate(stages):
        x1 = start_x + i*(box_w+gap)
        y1 = box_y
        x2 = x1 + box_w
        y2 = y1 + box_h
        draw_rounded_rect(d, x1,y1,x2,y2, 10, fill=color, outline=(200,215,255), width=2)
        draw_text_centered(d, name, (x1+x2)//2, y1+19, stage_font, (255,255,255))
        for j,lbl in enumerate(labels):
            draw_text_centered(d, "• "+lbl, (x1+x2)//2, y1+43+j*18, label_font, (235,245,255))
        if i < n-1:
            ay = (y1+y2)//2
            draw_arrow(d, x2, ay, x2+gap, ay, (180,200,255), width=4)
        dot_x = (x1+x2)//2
        for yy in range(box_y-4, curve_pts[i][1]+4, -7):
            d.ellipse([dot_x-1,yy-1,dot_x+1,yy+1], fill=(90,110,150))

    # Phase numbers
    phase_font = get_font(11)
    for i in range(n):
        x = start_x + i*(box_w+gap) + box_w//2
        d.text((x-20, box_y+box_h+8), f"Phase {i+1}", font=phase_font, fill=(110,135,170))

    # Legend
    legend_y = H - 55
    d.text((60, legend_y), "IBM/NIST Cost Multiplier Curve:", font=get_font(12,bold=True), fill=(200,215,235))
    d.line([(280,legend_y+8),(340,legend_y+8)], fill=(255,100,100), width=3)
    d.text((350, legend_y+1), "Relative cost to fix a defect found at each SDLC phase (exponential growth)", font=get_font(11), fill=(170,190,215))

    img.save(os.path.join(OUT, "ch01-software-assurance-overview.png"))
    print("✓ Diagram 1: ch01-software-assurance-overview.png")

# ─────────────────────────────────────────────
# DIAGRAM 2 — Security Requirements Engineering
# ─────────────────────────────────────────────
def gen_diagram2():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title_font = get_font(28, bold=True)
    label_font = get_font(12, bold=True)
    sub_font   = get_font(10)
    draw_text_centered(d, "SECURITY REQUIREMENTS ENGINEERING", W//2, 36, title_font, (220,230,255))

    cx = W//2
    apex_y  = 110
    base_y  = 610
    layers = [
        (apex_y, 255,  55, 175, (180,145,30),  (220,185,60),
         "Business / Mission Security Goals",
         ["Strategic Risk Tolerance","Exec Sponsor Sign-off","Regulatory Mandates"]),
        (255,    430, 175, 295, (42,90,180),   (80,140,230),
         "System-Level Security Requirements",
         ["Functional: Authn / Authz / Encryption","Non-Functional: Brute-force / DDoS resistance","Constraints: HIPAA §164.312 / PCI DSS Req 6 / GDPR Art 25"]),
        (430,    base_y, 295, 400, (18,110,145),(40,175,200),
         "Technical Security Controls & Test Cases",
         ["Input Validation / Crypto Standards / Audit Logging","Security Test Cases","Acceptance Criteria & Traceability Matrix"]),
    ]

    for (ty,by,htop,hbot,fill,outline,title,subs) in layers:
        pts = [(cx-htop,ty),(cx+htop,ty),(cx+hbot,by),(cx-hbot,by)]
        d.polygon(pts, fill=fill)
        d.polygon(pts, outline=outline)
        mid_y = (ty+by)//2
        draw_text_centered(d, title, cx, mid_y-14, label_font, (255,255,255))
        for i,s in enumerate(subs):
            draw_text_centered(d, s, cx, mid_y+8+i*16, sub_font, (225,238,255))

    # Left inputs
    inputs = [("Threat Model",(255,100,100)),("Compliance Regs\n(HIPAA/PCI/GDPR)",(255,160,60)),
              ("Risk Assessment",(100,210,110)),("Stakeholder\nInterviews",(180,110,255))]
    lx = 105
    for i,(label,color) in enumerate(inputs):
        ly = 180 + i*115
        draw_rounded_rect(d, lx-68,ly-24,lx+68,ly+24, 8, fill=(25,40,65), outline=color, width=2)
        parts = label.split("\n")
        if len(parts)==1:
            draw_text_centered(d, parts[0], lx, ly, sub_font, color)
        else:
            draw_text_centered(d, parts[0], lx, ly-8, sub_font, color)
            draw_text_centered(d, parts[1], lx, ly+8, sub_font, color)
        target_x = cx - layers[min(i,2)][3] + 20
        target_y = (layers[min(i,2)][0]+layers[min(i,2)][1])//2
        draw_arrow(d, lx+70, ly, target_x, target_y, color, width=2)

    # Right outputs
    outputs = [("Security\nArchitecture",(58,123,213)),("Test Plans",(39,174,96)),
               ("Acceptance\nCriteria",(23,162,184)),("Traceability\nMatrix",(200,169,81))]
    rx = W-105
    for i,(label,color) in enumerate(outputs):
        ry = 180 + i*115
        draw_rounded_rect(d, rx-68,ry-24,rx+68,ry+24, 8, fill=(25,40,65), outline=color, width=2)
        parts = label.split("\n")
        if len(parts)==1:
            draw_text_centered(d, parts[0], rx, ry, sub_font, color)
        else:
            draw_text_centered(d, parts[0], rx, ry-8, sub_font, color)
            draw_text_centered(d, parts[1], rx, ry+8, sub_font, color)
        source_x = cx + layers[min(i,2)][3] - 20
        source_y = (layers[min(i,2)][0]+layers[min(i,2)][1])//2
        draw_arrow(d, source_x, source_y, rx-70, ry, color, width=2)

    # Use case vs misuse case
    uc_x, uc_y = cx-55, 535
    mc_x, mc_y = cx+55, 535
    d.ellipse([uc_x-30,uc_y-30,uc_x+30,uc_y+30], outline=(80,210,80), width=2)
    draw_text_centered(d, "USE CASE", uc_x, uc_y, get_font(9,bold=True), (80,210,80))
    d.ellipse([mc_x-30,mc_y-30,mc_x+30,mc_y+30], outline=(255,70,70), width=2)
    draw_text_centered(d, "MISUSE CASE", mc_x, mc_y, get_font(8,bold=True), (255,70,70))
    d.line([(uc_x+32,uc_y),(mc_x-32,mc_y)], fill=(210,200,80), width=2)

    img.save(os.path.join(OUT, "ch02-security-requirements.png"))
    print("✓ Diagram 2: ch02-security-requirements.png")

# ─────────────────────────────────────────────
# DIAGRAM 3 — STRIDE Threat Modeling
# ─────────────────────────────────────────────
def gen_diagram3():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title_font = get_font(28, bold=True)
    box_font   = get_font(12, bold=True)
    sub_font   = get_font(10)
    draw_text_centered(d, "STRIDE THREAT MODELING PROCESS", W//2, 32, title_font, (220,230,255))

    dfd_y = 295
    comps = [
        ("BROWSER",    200, dfd_y, (45,85,150)),
        ("WEB SERVER", 450, dfd_y, (25,115,165)),
        ("APP LOGIC",  700, dfd_y, (70,50,155)),
        ("DATABASE",   950, dfd_y, (35,110,70)),
    ]

    def dashed_rect(x1,y1,x2,y2,color,dash=10,gap=5):
        for x in range(x1,x2,dash+gap):
            d.line([(x,y1),(min(x+dash,x2),y1)], fill=color, width=2)
            d.line([(x,y2),(min(x+dash,x2),y2)], fill=color, width=2)
        for y in range(y1,y2,dash+gap):
            d.line([(x1,y),(x1,min(y+dash,y2))], fill=color, width=2)
            d.line([(x2,y),(x2,min(y+dash,y2))], fill=color, width=2)

    dashed_rect(115,250,545,348,(90,135,195))
    d.text((120,254),"Internet Zone", font=sub_font, fill=(90,135,195))
    dashed_rect(575,250,1025,348,(140,90,195))
    d.text((580,254),"Application Zone", font=sub_font, fill=(140,90,195))

    for (name,cx,cy,color) in comps:
        draw_rounded_rect(d, cx-58,cy-30,cx+58,cy+30, 9, fill=color, outline=(190,210,255), width=2)
        draw_text_centered(d, name, cx, cy, box_font, (255,255,255))

    for i in range(len(comps)-1):
        x1=comps[i][1]+58; x2=comps[i+1][1]-58; y=dfd_y
        draw_arrow(d, x1,y,x2,y, (170,195,255), width=3)

    stride = [
        ("S: SPOOFING",          (195,45,45),  175, 155, comps[0][1], dfd_y-30),
        ("T: TAMPERING",         (215,100,25), 415, 150, (comps[0][1]+comps[1][1])//2, dfd_y-30),
        ("R: REPUDIATION",       (195,175,25), 660, 152, comps[1][1], dfd_y-30),
        ("I: INFO DISCLOSURE",   (130,45,175), 915, 155, comps[3][1], dfd_y-30),
        ("D: DENIAL OF SERVICE", (25,150,175), 430, 445, comps[1][1], dfd_y+30),
        ("E: ELEV OF PRIVILEGE", (130,18,18),  680, 445, comps[2][1], dfd_y+30),
    ]

    sf = get_font(11, bold=True)
    for (label,color,sx,sy,tx,ty) in stride:
        bw,bh = 175,38
        draw_rounded_rect(d, sx-bw//2,sy-bh//2,sx+bw//2,sy+bh//2, 8, fill=color, outline=(240,240,240), width=1)
        draw_text_centered(d, label, sx, sy, sf, (255,255,255))
        draw_arrow(d, sx, sy+(bh//2 if ty>sy else -bh//2), tx, ty, color, width=2)

    # DREAD table
    ty2 = 548
    draw_rounded_rect(d, 40,ty2,W-40,H-25, 10, fill=(18,32,52), outline=(90,120,175), width=2)
    d.text((65,ty2+10), "DREAD SCORING MODEL  (Score each 1–10, sum for risk priority)", font=get_font(11,bold=True), fill=(190,210,255))

    cols = ["DAMAGE","REPRODUCIBILITY","EXPLOITABILITY","AFFECTED USERS","DISCOVERABILITY"]
    col_colors = [(255,90,90),(255,155,70),(255,215,70),(90,205,90),(90,175,255)]
    cw = (W-130)//len(cols)
    for i,(col,color) in enumerate(zip(cols,col_colors)):
        cx2 = 65 + i*cw + cw//2
        draw_rounded_rect(d, 65+i*cw+3,ty2+33,65+(i+1)*cw-3,ty2+63, 6, fill=color)
        draw_text_centered(d, col, cx2, ty2+48, get_font(10,bold=True), (20,30,50))

    rows = [("Low (1-3)",(80,200,80),["1-3","1-3","1-3","1-3","1-3"]),
            ("Med (4-6)",(240,190,40),["4-6","4-6","4-6","4-6","4-6"]),
            ("High (7-10)",(255,70,70),["7-10","7-10","7-10","7-10","7-10"])]
    for r,(rl,rc,vals) in enumerate(rows):
        ry = ty2+73+r*26
        d.text((48,ry+4), rl, font=get_font(10,bold=True), fill=rc)
        for c,val in enumerate(vals):
            draw_text_centered(d, val, 65+c*cw+cw//2, ry+12, get_font(11), (195,215,235))

    img.save(os.path.join(OUT, "ch03-threat-modeling.png"))
    print("✓ Diagram 3: ch03-threat-modeling.png")

# ─────────────────────────────────────────────
# DIAGRAM 4 — Quality Attributes in Architecture
# ─────────────────────────────────────────────
def gen_diagram4():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title_font = get_font(26, bold=True)
    draw_text_centered(d, "QUALITY ATTRIBUTES IN SOFTWARE ARCHITECTURE", W//2, 36, title_font, (220,230,255))

    def hex_pts(cx, cy, size):
        return [(cx+size*math.cos(math.pi/6+i*math.pi/3),
                 cy+size*math.sin(math.pi/6+i*math.pi/3)) for i in range(6)]

    def draw_hex(cx, cy, size, fill, outline, lw=2):
        pts = hex_pts(cx, cy, size)
        d.polygon(pts, fill=fill)
        d.polygon(pts, outline=outline)

    cx, cy = W//2, 400
    draw_hex(cx, cy, 82, (28,48,88), (100,150,220), lw=3)
    draw_text_centered(d, "SOFTWARE", cx, cy-12, get_font(13,bold=True), (200,220,255))
    draw_text_centered(d, "SYSTEM",   cx, cy+8,  get_font(13,bold=True), (200,220,255))

    attrs = [
        ("SECURITY",        (160,35,35),   (255,90,90),   ["Confidentiality","Integrity","Non-repudiation"]),
        ("RELIABILITY",     (28,118,55),   (75,215,115),  ["Fault Tolerance","Availability","Recoverability"]),
        ("PERFORMANCE",     (28,72,168),   (75,155,250),  ["Response Time","Throughput","Scalability"]),
        ("MAINTAINABILITY",(155,72,18),   (255,158,72),  ["Modularity","Analyzability","Modifiability"]),
        ("USABILITY",       (95,28,155),   (175,95,250),  ["Learnability","Accessibility","User Feedback"]),
        ("TESTABILITY",     (18,122,152),  (55,205,205),  ["Observability","Controllability","Isolatability"]),
    ]

    orbit = 215
    outer_size = 72
    hex_font = get_font(11, bold=True)
    sub_font  = get_font(9)
    positions = []
    for i,(name,fill,outline,subs) in enumerate(attrs):
        angle = -math.pi/2 + i*2*math.pi/6
        hx = int(cx + orbit*math.cos(angle))
        hy = int(cy + orbit*math.sin(angle))
        positions.append((hx,hy))
        d.line([(cx,cy),(hx,hy)], fill=outline, width=2)
        draw_hex(hx, hy, outer_size, fill, outline, lw=2)
        draw_text_centered(d, name, hx, hy-20, hex_font, (255,255,255))
        for j,s in enumerate(subs):
            draw_text_centered(d, s, hx, hy-2+j*14, sub_font, (225,235,250))

    # Tension arcs
    tension_font = get_font(10, bold=True)
    def draw_tension_arc(p1, p2, label, color):
        mx, my = (p1[0]+p2[0])//2, (p1[1]+p2[1])//2 - 35
        for t in range(21):
            tt = t/20
            x = int(p1[0]*(1-tt)**2 + mx*2*tt*(1-tt) + p2[0]*tt**2)
            y = int(p1[1]*(1-tt)**2 + my*2*tt*(1-tt) + p2[1]*tt**2)
            d.ellipse([x-2,y-2,x+2,y+2], fill=color)
        draw_text_centered(d, label, (p1[0]+p2[0])//2, (p1[1]+p2[1])//2 - 52, tension_font, color)

    draw_tension_arc(positions[0], positions[4], "⟺ TENSION", (255,215,55))
    draw_tension_arc(positions[0], positions[2], "⟺ TENSION", (255,175,55))

    # Legend
    legend_y = H-55
    d.text((50, legend_y), "Trade-off arcs:", font=get_font(11,bold=True), fill=(200,215,235))
    d.line([(180,legend_y+7),(230,legend_y+7)], fill=(255,215,55), width=2)
    d.text((240, legend_y), "Security ↔ Usability", font=get_font(11), fill=(255,215,55))
    d.line([(420,legend_y+7),(470,legend_y+7)], fill=(255,175,55), width=2)
    d.text((480, legend_y), "Security ↔ Performance", font=get_font(11), fill=(255,175,55))

    img.save(os.path.join(OUT, "ch04-quality-architecture.png"))
    print("✓ Diagram 4: ch04-quality-architecture.png")

# ─────────────────────────────────────────────
# DIAGRAM 5 — Static Analysis Techniques & Tools
# ─────────────────────────────────────────────
def gen_diagram5():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    title_font = get_font(28, bold=True)
    box_font   = get_font(12, bold=True)
    sub_font   = get_font(10)
    draw_text_centered(d, "STATIC ANALYSIS TECHNIQUES & TOOLS", W//2, 36, title_font, (220,230,255))

    techniques = [
        ("Lexical Analysis",       (190,170,25), "Token scanning / Pattern matching"),
        ("Data Flow Analysis",     (210,100,25), "Taint tracking / Def-use chains"),
        ("Control Flow Analysis",  (195,45,45),  "CFG construction / Dead code"),
        ("Abstract Interpretation",(120,45,170), "Sound approximation / Formal semantics"),
        ("Model Checking",         (35,95,195),  "State space exploration / Properties"),
    ]
    tools = [
        ("Bandit / Flake8",       (190,170,25), "Python • Severity/Confidence scoring"),
        ("FindBugs / SpotBugs",   (210,100,25), "Java • FindSecBugs plugin"),
        ("Coverity / Fortify",    (195,45,45),  "Enterprise • C/C++ / Java / C#"),
        ("Veracode / SonarQube",  (120,45,170), "Enterprise • Multi-language SAST"),
        ("CodeQL / Semgrep",      (35,95,195),  "GitHub / Multi-lang • Custom rules"),
    ]

    lx, rx = 205, 1195
    bw, bh = 300, 65
    sy = 105
    sp = 84

    d.text((lx - bw//2, 78), "TECHNIQUES", font=get_font(14,bold=True), fill=(175,200,230))
    d.text((rx - bw//2, 78), "TOOLS",      font=get_font(14,bold=True), fill=(175,200,230))

    t_centers, tl_centers = [], []
    for i,(name,color,desc) in enumerate(techniques):
        by = sy + i*sp
        draw_rounded_rect(d, lx-bw//2,by,lx+bw//2,by+bh, 10, fill=color, outline=(220,230,250), width=1)
        draw_text_centered(d, name, lx, by+20, box_font, (15,25,45))
        draw_text_centered(d, desc, lx, by+44, sub_font, (25,38,60))
        t_centers.append((lx+bw//2, by+bh//2))

    for i,(name,color,desc) in enumerate(tools):
        by = sy + i*sp
        draw_rounded_rect(d, rx-bw//2,by,rx+bw//2,by+bh, 10, fill=(22,40,65), outline=color, width=2)
        draw_text_centered(d, name, rx, by+20, box_font, color)
        draw_text_centered(d, desc, rx, by+44, sub_font, (185,205,225))
        tl_centers.append((rx-bw//2, by+bh//2))

    for i,(tc,tlc) in enumerate(zip(t_centers,tl_centers)):
        draw_arrow(d, tc[0], tc[1], tlc[0], tlc[1], techniques[i][1], width=2)

    # CI/CD pipeline
    ply = 568
    draw_rounded_rect(d, 35,ply,W-35,H-22, 10, fill=(16,30,50), outline=(75,115,180), width=2)
    d.text((65,ply+12), "CI/CD INTEGRATION — SHIFT LEFT SECURITY (SAST in Every Phase)", font=get_font(12,bold=True), fill=(155,185,230))

    pipe_stages = [
        ("PRE-COMMIT\nHook",      (45,115,45),  "Bandit / ESLint\nLocal fast scan"),
        ("PR CHECK\nAutomated",   (35,95,175),  "Semgrep / CodeQL\nBlock on HIGH"),
        ("BUILD GATE\nCI Server", (155,75,18),  "Full SAST Scan\nSonarQube Quality Gate"),
        ("DEPLOY GATE\nCD Stage", (125,28,128), "SCA: Snyk / Dependabot\nCVE check"),
        ("RUNTIME\nMonitoring",   (25,118,118), "IAST / RASP\nAnomaly Detection"),
    ]
    psw = (W-100)//len(pipe_stages)
    for i,(label,color,sub) in enumerate(pipe_stages):
        px = 50 + i*psw + psw//2
        py = ply+55
        draw_rounded_rect(d, px-psw//2+8,py-30,px+psw//2-8,py+38, 8, fill=color, outline=(200,220,255), width=1)
        for j,ln in enumerate(label.split("\n")):
            draw_text_centered(d, ln, px, py-16+j*17, get_font(10,bold=True), (255,255,255))
        for j,ln in enumerate(sub.split("\n")):
            draw_text_centered(d, ln, px, py+26+j*14, get_font(9), (195,215,235))
        if i < len(pipe_stages)-1:
            draw_arrow(d, px+psw//2-8,py+4, px+psw//2+8+5,py+4, (140,175,220), width=3)

    img.save(os.path.join(OUT, "ch05-static-analysis.png"))
    print("✓ Diagram 5: ch05-static-analysis.png")

if __name__ == "__main__":
    gen_diagram1()
    gen_diagram2()
    gen_diagram3()
    gen_diagram4()
    gen_diagram5()
    print("\nAll 5 diagrams generated successfully!")
