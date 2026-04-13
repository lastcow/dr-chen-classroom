#!/usr/bin/env python3
"""Generate technical diagrams for SCIA 425 chapters 6-10."""

from PIL import Image, ImageDraw, ImageFont
import math, os, random

W, H = 1400, 750
BG = (13, 27, 42)          # #0d1b2a
OUT = "/home/john/wiki/docs/scia-425/img"

def get_font(size=14, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def draw_centered(draw, text, x, y, font, fill):
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    draw.text((x - tw//2, y), text, font=font, fill=fill)

def draw_rect(draw, x1, y1, x2, y2, fill, outline=None, radius=8):
    draw.rounded_rectangle([x1,y1,x2,y2], radius=radius, fill=fill, outline=outline, width=2)

def draw_arrow(draw, x1, y1, x2, y2, color, width=2):
    draw.line([(x1,y1),(x2,y2)], fill=color, width=width)
    # arrowhead
    angle = math.atan2(y2-y1, x2-x1)
    size = 8
    for da in [0.5, -0.5]:
        ax = x2 - size*math.cos(angle-da)
        ay = y2 - size*math.sin(angle-da)
        draw.line([(x2,y2),(int(ax),int(ay))], fill=color, width=width)

# ─────────────────────────────────────────────────────────────
# DIAGRAM 6: Software Testing Taxonomy
# ─────────────────────────────────────────────────────────────
def make_ch06():
    img = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(img)
    
    # Title
    tf = get_font(26, bold=True)
    draw_centered(d, "SOFTWARE TESTING TAXONOMY", W//2, 18, tf, (0,220,255))
    d.line([(60,52),(W-60,52)], fill=(0,180,220), width=2)
    
    # Root node
    rf = get_font(15, bold=True)
    draw_rect(d, W//2-90, 65, W//2+90, 95, (20,60,100), (0,200,255))
    draw_centered(d, "SOFTWARE TESTING", W//2, 72, rf, (255,255,255))
    
    # Branch lines
    d.line([(W//2,95),(W//2,115)], fill=(100,180,255), width=2)
    d.line([(W//2,115),(320,115)], fill=(80,140,255), width=2)
    d.line([(W//2,115),(W-320,115)], fill=(160,80,255), width=2)
    d.line([(320,115),(320,140)], fill=(80,140,255), width=2)
    d.line([(W-320,115),(W-320,140)], fill=(160,80,255), width=2)
    
    # Left branch: FUNCTIONAL TESTING
    draw_rect(d, 195, 140, 445, 170, (20,40,120), (80,140,255))
    draw_centered(d, "FUNCTIONAL TESTING", 320, 148, get_font(13,True), (100,180,255))
    
    # Right branch: NON-FUNCTIONAL TESTING
    draw_rect(d, W-445, 140, W-195, 170, (50,20,100), (160,80,255))
    draw_centered(d, "NON-FUNCTIONAL TESTING", W-320, 148, get_font(13,True), (180,100,255))
    
    # Left leaves
    left_leaves = [
        ("Unit Testing", "Isolated component tests"),
        ("Integration Testing", "Component interactions"),
        ("System Testing", "Full system vs. requirements"),
        ("Acceptance Testing (UAT)", "Customer/business validation"),
    ]
    lf = get_font(11, bold=True)
    lf2 = get_font(9)
    for i,(name,desc) in enumerate(left_leaves):
        x = 80 + i*175
        d.line([(320,170),(320,190)], fill=(80,140,255), width=1)
        d.line([(320,190),(x+70,190)], fill=(80,140,255), width=1)
        d.line([(x+70,190),(x+70,205)], fill=(80,140,255), width=1)
        draw_rect(d, x, 205, x+140, 235, (15,35,90), (80,140,255))
        draw_centered(d, name, x+70, 212, lf, (140,200,255))
        draw_centered(d, desc, x+70, 240, lf2, (150,190,230))
    
    # Right leaves
    right_leaves = [
        ("Performance Testing", "Speed & scalability"),
        ("Security Testing", "Vulnerability assessment"),
        ("Usability Testing", "User experience quality"),
        ("Reliability Testing", "Stability over time"),
    ]
    for i,(name,desc) in enumerate(right_leaves):
        x = W - 220 + i*175 - i*175 + (i*175)
        x = 770 + i*155
        d.line([(W-320,170),(W-320,190)], fill=(160,80,255), width=1)
        d.line([(W-320,190),(x+70,190)], fill=(160,80,255), width=1)
        d.line([(x+70,190),(x+70,205)], fill=(160,80,255), width=1)
        draw_rect(d, x, 205, x+140, 235, (40,15,80), (160,80,255))
        draw_centered(d, name, x+70, 212, lf, (190,130,255))
        draw_centered(d, desc, x+70, 240, lf2, (180,160,230))
    
    # Testing Approach Band
    d.line([(60,275),(W-60,275)], fill=(60,80,100), width=1)
    d.rectangle([60,285,W-60,380], fill=(8,20,35))
    d.rectangle([60,285,W-60,380], outline=(60,100,140), width=1)
    
    band_title = get_font(13, bold=True)
    draw_centered(d, "TESTING APPROACHES", W//2, 290, band_title, (200,220,240))
    
    approaches = [
        ("White-Box Testing", "Code path knowledge required.\nStatement/Branch/Path/MC-DC coverage.\nUsed by developers.", (60,160,100), (100,220,150)),
        ("Grey-Box Testing", "Partial internal knowledge.\nCombines structural + functional.\nAPI & integration testing.", (160,120,0), (240,190,50)),
        ("Black-Box Testing", "Specification-based only.\nEquivalence partitioning,\nBoundary value analysis.", (160,50,0), (240,120,60)),
    ]
    for i,(title,desc,bg_c,fg_c) in enumerate(approaches):
        x = 80 + i*420
        draw_rect(d, x, 305, x+400, 370, bg_c, fg_c, radius=6)
        draw_centered(d, title, x+200, 310, get_font(12,True), fg_c)
        for j,line in enumerate(desc.split("\n")):
            draw_centered(d, line, x+200, 328+j*13, get_font(10), (220,220,220))
    
    # Test Pyramid Inset
    px, py = 60, 390
    pw, ph = 320, 250
    d.rectangle([px,py,px+pw,py+ph], fill=(6,15,28))
    d.rectangle([px,py,px+pw,py+ph], outline=(60,90,120), width=1)
    pf = get_font(11, bold=True)
    draw_centered(d, "TEST PYRAMID", px+pw//2, py+8, pf, (180,220,255))
    
    # Draw pyramid
    cx = px + pw//2
    # E2E (top)
    pts_e2e = [(cx, py+45),(cx-35, py+80),(cx+35, py+80)]
    d.polygon(pts_e2e, fill=(180,50,50))
    draw_centered(d, "E2E", cx, py+57, get_font(9,True), (255,200,200))
    draw_centered(d, "Few / Slow", cx, py+87, get_font(8), (200,150,150))
    # Integration (middle)
    pts_int = [(cx-35,py+80),(cx-90,py+145),(cx+90,py+145),(cx+35,py+80)]
    d.polygon(pts_int, fill=(160,120,30))
    draw_centered(d, "INTEGRATION", cx, py+108, get_font(9,True), (255,230,150))
    draw_centered(d, "Medium speed", cx, py+150, get_font(8), (210,190,130))
    # Unit (base)
    pts_unit = [(cx-90,py+145),(cx-155,py+220),(cx+155,py+220),(cx+90,py+145)]
    d.polygon(pts_unit, fill=(30,100,60))
    draw_centered(d, "UNIT TESTS", cx, py+178, get_font(9,True), (150,255,180))
    draw_centered(d, "Many / Fast / Cheap", cx, py+225, get_font(8), (130,200,150))
    
    # Security testing types panel
    sx, sy = 405, 390
    sw, sh = 560, 250
    d.rectangle([sx,sy,sx+sw,sy+sh], fill=(6,15,28))
    d.rectangle([sx,sy,sx+sw,sy+sh], outline=(60,90,120), width=1)
    sf = get_font(11, bold=True)
    draw_centered(d, "SECURITY TESTING IN THE TAXONOMY", sx+sw//2, sy+8, sf, (0,220,255))
    
    sec_types = [
        ("SAST", "Static Analysis\n(Code-level, pre-compile)", (30,70,30), (100,200,100)),
        ("DAST", "Dynamic Analysis\n(Running app, black-box)", (70,30,30), (220,100,100)),
        ("IAST", "Interactive Analysis\n(Instrumented runtime)", (30,40,80), (100,150,220)),
        ("RASP", "Runtime Protection\n(In-production defense)", (60,40,0), (220,180,60)),
    ]
    for i,(name,desc,bg_c,fg_c) in enumerate(sec_types):
        xi = sx+15 + i*135
        draw_rect(d, xi, sy+30, xi+120, sy+90, bg_c, fg_c, radius=6)
        draw_centered(d, name, xi+60, sy+35, get_font(13,True), fg_c)
        for j,line in enumerate(desc.split("\n")):
            draw_centered(d, line, xi+60, sy+58+j*13, get_font(9), (210,210,210))
    
    # Coverage metrics
    draw_centered(d, "Code Coverage Metrics", sx+sw//2, sy+105, get_font(11,True), (180,220,255))
    cov_data = [
        ("Statement Coverage", "Was each line executed?", "Basic — min. acceptable"),
        ("Branch Coverage", "Was each condition branch taken?", "Intermediate standard"),
        ("Path Coverage", "Were all execution paths taken?", "Thorough — expensive"),
        ("MC/DC Coverage", "Each condition independently affects outcome", "Safety-critical (DO-178C)"),
    ]
    for i,(metric,q,note) in enumerate(cov_data):
        y_row = sy+122+i*28
        d.rectangle([sx+15,y_row,sx+sw-15,y_row+24], fill=(10,25,45))
        draw_centered(d, metric, sx+120, y_row+6, get_font(10,True), (140,200,255))
        draw_centered(d, q, sx+295, y_row+6, get_font(9), (200,200,200))
        draw_centered(d, note, sx+470, y_row+6, get_font(9), (150,200,150))
    
    # Right panel: Test automation
    ax, ay = 985, 390
    aw, ah = 355, 250
    d.rectangle([ax,ay,ax+aw,ay+ah], fill=(6,15,28))
    d.rectangle([ax,ay,ax+aw,ay+ah], outline=(60,90,120), width=1)
    draw_centered(d, "TEST AUTOMATION PRINCIPLES", ax+aw//2, ay+8, get_font(11,True), (0,220,255))
    
    auto_items = [
        ("✓ Automate", "Regression tests, smoke tests,\nrepetitive data-driven tests", (20,60,20), (100,200,100)),
        ("✗ Manual", "Exploratory testing, UX eval,\none-off complex scenarios", (60,20,20), (200,100,100)),
        ("⚙ CI/CD", "Run on every commit: unit+\nintegration, fail fast on errors", (20,40,70), (100,150,220)),
    ]
    for i,(label,desc,bg_c,fg_c) in enumerate(auto_items):
        yi = ay+30+i*68
        draw_rect(d, ax+15, yi, ax+aw-15, yi+60, bg_c, fg_c, radius=5)
        draw_centered(d, label, ax+75, yi+8, get_font(12,True), fg_c)
        for j,line in enumerate(desc.split("\n")):
            draw_centered(d, line, ax+210, yi+8+j*14, get_font(9), (210,210,210))
    
    # Footer
    d.line([(60,650),(W-60,650)], fill=(40,60,80), width=1)
    draw_centered(d, "SCIA 425 — Software Testing & Assurance  |  Chapter 6: Testing Fundamentals", W//2, 658, get_font(10), (100,130,160))
    
    img.save(f"{OUT}/ch06-testing-types.png")
    print("ch06 done")

# ─────────────────────────────────────────────────────────────
# DIAGRAM 7: Dynamic Security Testing
# ─────────────────────────────────────────────────────────────
def make_ch07():
    img = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(img)
    
    CYAN = (0,220,255)
    ORANGE = (255,140,0)
    
    tf = get_font(26, bold=True)
    draw_centered(d, "DYNAMIC SECURITY TESTING TECHNIQUES", W//2, 18, tf, CYAN)
    d.line([(60,52),(W-60,52)], fill=CYAN, width=2)
    
    # Left panel: DAST
    lx, ly, lw, lh = 40, 65, 590, 530
    d.rectangle([lx,ly,lx+lw,ly+lh], fill=(6,15,28))
    d.rectangle([lx,ly,lx+lw,ly+lh], outline=CYAN, width=2)
    draw_centered(d, "DAST — Dynamic Application Security Testing", lx+lw//2, ly+10, get_font(13,True), CYAN)
    
    # DAST Flow boxes
    dast_flow = [
        ("Test Tool\n(ZAP / Burp)", (0,100,140)),
        ("HTTP Requests\n→ Payloads", (0,80,110)),
        ("Target App\n(Running)", (0,60,90)),
        ("Responses\n← Results", (0,80,110)),
        ("Vulnerability\nDetection", (20,80,20)),
    ]
    bx = lx+20
    by = ly+40
    bw, bh = 100, 55
    gap = 9
    for i,(label,bg) in enumerate(dast_flow):
        xb = bx + i*(bw+gap)
        draw_rect(d, xb, by, xb+bw, by+bh, bg, CYAN, radius=6)
        for j,line in enumerate(label.split("\n")):
            draw_centered(d, line, xb+bw//2, by+8+j*18, get_font(9,True), (200,240,255))
        if i < len(dast_flow)-1:
            draw_arrow(d, xb+bw, by+bh//2, xb+bw+gap, by+bh//2, CYAN, 2)
    
    # DAST phases
    phases = [
        ("① SPIDER / CRAWL", "Map all URLs, forms, API endpoints\nBuild complete attack surface inventory", (0,60,100)),
        ("② ACTIVE SCAN", "Send malicious payloads to every parameter\nSQL injection, XSS, path traversal probes", (80,40,0)),
        ("③ REPORT", "Classify findings by severity (CVSS)\nGenerate remediation recommendations", (0,80,20)),
    ]
    for i,(phase,desc,bg) in enumerate(phases):
        yp = ly+110+i*85
        draw_rect(d, lx+15, yp, lx+lw-15, yp+75, bg, CYAN if i==0 else ORANGE if i==1 else (0,180,80), radius=6)
        d.text((lx+25, yp+8), phase, font=get_font(11,True), fill=CYAN if i==0 else ORANGE if i==1 else (0,200,100))
        for j,line in enumerate(desc.split("\n")):
            d.text((lx+25, yp+28+j*16), line, font=get_font(9), fill=(210,210,210))
        if i<2:
            draw_arrow(d, lx+lw//2, yp+75, lx+lw//2, yp+85, (100,150,200), 2)
    
    # Tools
    draw_centered(d, "KEY DAST TOOLS", lx+lw//2, ly+370, get_font(12,True), (180,220,255))
    tools = [("OWASP ZAP",(0,80,120)),("Burp Suite",(80,40,0)),("Nikto",(60,0,100)),("w3af",(0,60,80))]
    for i,(name,bg) in enumerate(tools):
        xi = lx+20+i*137
        draw_rect(d, xi, ly+390, xi+125, ly+425, bg, CYAN, radius=5)
        draw_centered(d, name, xi+62, ly+400, get_font(11,True), (200,240,255))
    
    # Authenticated scanning note
    draw_rect(d, lx+15, ly+435, lx+lw-15, ly+520, (0,40,60), CYAN, radius=5)
    draw_centered(d, "Authenticated Scanning", lx+lw//2, ly+442, get_font(11,True), CYAN)
    notes = ["Provide session cookies / credentials to scanner",
             "Test protected endpoints & authorized functionality",
             "Integrate ZAP via API into CI/CD pipelines"]
    for i,note in enumerate(notes):
        draw_centered(d, note, lx+lw//2, ly+462+i*17, get_font(9), (180,220,240))
    
    # Center divider
    cx = 650
    d.line([(cx,65),(cx,595)], fill=(40,60,80), width=2)
    draw_centered(d, "COMPARISON", cx, 65, get_font(10,True), (150,170,190))
    
    # Comparison table
    tx, ty = 635, 80
    headers = ["", "DAST", "Fuzzing"]
    rows = [
        ["Speed", "Medium", "Fast"],
        ["Coverage", "High (web)", "Deep (inputs)"],
        ["False Pos.", "Medium", "Low"],
        ["Auth Needed", "Optional", "No"],
        ["Finding Type", "Logic flaws", "Memory bugs"],
    ]
    col_w = [90,75,75]
    row_h = 26
    for ci,h in enumerate(headers):
        xh = tx + sum(col_w[:ci])
        draw_rect(d, xh, ty, xh+col_w[ci], ty+row_h, (0,50,80), CYAN, radius=3)
        draw_centered(d, h, xh+col_w[ci]//2, ty+6, get_font(9,True), CYAN)
    for ri,row in enumerate(rows):
        for ci,cell in enumerate(row):
            xc = tx + sum(col_w[:ci])
            yc = ty + (ri+1)*row_h
            bg = (6,18,30) if ri%2==0 else (8,22,38)
            d.rectangle([xc,yc,xc+col_w[ci],yc+row_h], fill=bg)
            d.rectangle([xc,yc,xc+col_w[ci],yc+row_h], outline=(30,50,70), width=1)
            clr = (200,240,255) if ci==0 else (220,220,220)
            draw_centered(d, cell, xc+col_w[ci]//2, yc+6, get_font(9), clr)
    
    # Right panel: Fuzzing
    rx, ry, rw, rh = 660, 65, 690, 530
    d.rectangle([rx,ry,rx+rw,ry+rh], fill=(6,15,28))
    d.rectangle([rx,ry,rx+rw,ry+rh], outline=ORANGE, width=2)
    draw_centered(d, "FUZZING — Automated Input Generation", rx+rw//2, ry+10, get_font(13,True), ORANGE)
    
    # Fuzzing flow
    fuzz_items = [
        ("Seed\nCorpus", (80,50,0), ORANGE),
        ("Mutation\nEngine", (70,40,0), ORANGE),
        ("Fuzzer", (90,30,0), (255,80,0)),
        ("Target\n+ Monitor", (40,15,0), (255,60,60)),
    ]
    fx = rx+25
    fy = ry+40
    fw, fh = 130, 55
    fg = 15
    for i,(label,bg,oc) in enumerate(fuzz_items):
        xf = fx + i*(fw+fg)
        draw_rect(d, xf, fy, xf+fw, fy+fh, bg, oc, radius=6)
        for j,line in enumerate(label.split("\n")):
            draw_centered(d, line, xf+fw//2, fy+8+j*18, get_font(9,True), (255,210,150))
        if i<len(fuzz_items)-1:
            draw_arrow(d, xf+fw, fy+fh//2, xf+fw+fg, fy+fh//2, ORANGE, 2)
    
    # Decision diamond
    ddx, ddy = rx+rw//2, ry+125
    dsize = 30
    d.polygon([(ddx,ddy-dsize),(ddx+dsize,ddy),(ddx,ddy+dsize),(ddx-dsize,ddy)], fill=(80,20,0), outline=ORANGE)
    draw_centered(d, "CRASH?", ddx, ddy-8, get_font(9,True), ORANGE)
    
    # YES -> Triage
    draw_arrow(d, ddx+dsize, ddy, rx+rw-20, ddy, ORANGE, 2)
    draw_rect(d, rx+rw-110, ddy-20, rx+rw-10, ddy+20, (80,0,0), (255,80,80), radius=5)
    draw_centered(d, "TRIAGE", rx+rw-60, ddy-12, get_font(10,True), (255,120,120))
    d.text((rx+rw-60-35, ddy-35), "YES →", font=get_font(9,True), fill=(255,150,100))
    
    # NO -> feedback
    draw_arrow(d, ddx-dsize, ddy, rx+25, ddy, (100,200,100), 2)
    d.text((rx+30, ddy-20), "NO → Feedback", font=get_font(9), fill=(100,220,100))
    d.line([(rx+25,ddy),(rx+25,fy+fh//2)], fill=(100,200,100), width=2)
    draw_arrow(d, rx+25,fy+fh//2, rx+25+fw//2,fy+fh//2, (100,200,100), 2)
    
    # Fuzzing types
    draw_centered(d, "FUZZING TYPES", rx+rw//2, ry+175, get_font(12,True), (255,180,60))
    fuzz_types = [
        ("DUMB FUZZING", "Random/mutated inputs\nNo knowledge of format\nFast but low coverage", (60,40,0)),
        ("SMART FUZZING", "Grammar/protocol-aware\nFormat-valid mutations\nHigher code coverage", (60,30,0)),
        ("COVERAGE-GUIDED", "AFL++ / libFuzzer\nEvolutionary feedback loop\nMaximize branch coverage", (80,20,0)),
    ]
    for i,(name,desc,bg) in enumerate(fuzz_types):
        xi = rx+15 + i*225
        draw_rect(d, xi, ry+195, xi+210, ry+290, bg, ORANGE, radius=6)
        draw_centered(d, name, xi+105, ry+202, get_font(10,True), ORANGE)
        for j,line in enumerate(desc.split("\n")):
            draw_centered(d, line, xi+105, ry+222+j*16, get_font(9), (220,200,180))
    
    # Sanitizers
    draw_centered(d, "CRASH SANITIZERS (Compile-time instrumentation)", rx+rw//2, ry+305, get_font(11,True), (180,220,255))
    sans = [("ASan","AddressSanitizer\nBuffer overflows, UAF","Memory bugs",(0,60,100)),
            ("UBSan","UndefinedBehaviorSanitizer\nInt overflow, null deref","Logic bugs",(60,0,100)),
            ("MSan","MemorySanitizer\nUninitialised memory reads","Init bugs",(0,80,60))]
    for i,(short,long_,type_,bg) in enumerate(sans):
        xi = rx+15+i*225
        draw_rect(d, xi, ry+320, xi+210, ry+400, bg, (100,160,220), radius=5)
        draw_centered(d, short, xi+105, ry+327, get_font(12,True), (140,200,255))
        for j,line in enumerate(long_.split("\n")):
            draw_centered(d, line, xi+105, ry+347+j*16, get_font(9), (200,210,230))
        draw_centered(d, f"Detects: {type_}", xi+105, ry+382, get_font(9,True), (100,200,150))
    
    # OSS-Fuzz note
    draw_rect(d, rx+15, ry+415, rx+rw-15, ry+510, (40,20,0), ORANGE, radius=6)
    draw_centered(d, "Google OSS-Fuzz — Continuous Fuzzing at Scale", rx+rw//2, ry+422, get_font(11,True), ORANGE)
    oss_notes = [
        "Runs libFuzzer/AFL++ on critical open-source projects 24/7",
        "Auto-files bug reports, tracks fixes, measures coverage growth",
        "Found 10,000+ bugs in projects: OpenSSL, FFmpeg, Chromium, curl",
        "Free for qualifying open-source projects — integrate via GitHub Actions"
    ]
    for i,note in enumerate(oss_notes):
        draw_centered(d, note, rx+rw//2, ry+442+i*17, get_font(9), (220,200,160))
    
    # Footer
    d.line([(60,610),(W-60,610)], fill=(40,60,80), width=1)
    draw_centered(d, "SCIA 425 — Software Testing & Assurance  |  Chapter 7: Dynamic Testing & Fuzzing", W//2, 618, get_font(10), (100,130,160))
    
    img.save(f"{OUT}/ch07-dynamic-testing.png")
    print("ch07 done")

# ─────────────────────────────────────────────────────────────
# DIAGRAM 8: Penetration Testing Methodology
# ─────────────────────────────────────────────────────────────
def make_ch08():
    img = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(img)
    
    tf = get_font(26, bold=True)
    draw_centered(d, "PENETRATION TESTING METHODOLOGY", W//2, 16, tf, (255,100,100))
    d.line([(60,50),(W-60,50)], fill=(200,60,60), width=2)
    
    phases = [
        {
            "name": "RECONNAISSANCE",
            "num": "01",
            "color": (120,120,120),
            "outline": (200,200,200),
            "text_c": (220,220,220),
            "activities": ["Passive OSINT","Google dorking","WHOIS / DNS enum","LinkedIn / Shodan","Wayback Machine","Cert transparency"],
            "tools": ["Maltego","theHarvester","Recon-ng","Shodan","SpiderFoot"],
        },
        {
            "name": "SCANNING",
            "num": "02",
            "color": (100,80,0),
            "outline": (240,190,0),
            "text_c": (255,220,50),
            "activities": ["Port scanning","Service enum","OS fingerprint","Vuln scanning","Banner grabbing","Network mapping"],
            "tools": ["Nmap","Nessus","OpenVAS","Masscan","Unicornscan"],
        },
        {
            "name": "EXPLOITATION",
            "num": "03",
            "color": (100,20,20),
            "outline": (255,60,60),
            "text_c": (255,100,100),
            "activities": ["Exploit dev","Metasploit","Manual testing","Payload delivery","Client-side attacks","Phishing / SE"],
            "tools": ["Metasploit","SQLmap","Burp Suite","BeEF","Cobalt Strike"],
        },
        {
            "name": "POST-EXPLOIT",
            "num": "04",
            "color": (70,10,10),
            "outline": (200,40,40),
            "text_c": (220,80,80),
            "activities": ["Privilege escalation","Lateral movement","Data exfiltration","Persistence","Credential dump","Pivoting"],
            "tools": ["Mimikatz","BloodHound","Empire","Impacket","CrackMapExec"],
        },
        {
            "name": "REPORTING",
            "num": "05",
            "color": (0,40,100),
            "outline": (60,140,255),
            "text_c": (100,180,255),
            "activities": ["CVSS scoring","Risk rating","Executive summary","Tech findings","PoC screenshots","Remediation plan"],
            "tools": ["Dradis","Faraday","Plextrac","CVSS Calc","Pentest.ws"],
        },
    ]
    
    col_w = (W - 120) // 5
    col_h = 490
    start_x = 60
    start_y = 65
    
    for i,phase in enumerate(phases):
        x = start_x + i*col_w
        oc = phase["outline"]
        tc = phase["text_c"]
        bg = phase["color"]
        
        # Phase column header
        draw_rect(d, x+5, start_y, x+col_w-5, start_y+50, bg, oc, radius=6)
        draw_centered(d, phase["num"], x+col_w//2, start_y+5, get_font(11,True), tc)
        draw_centered(d, phase["name"], x+col_w//2, start_y+24, get_font(12,True), tc)
        
        # Tools box
        ty_start = start_y+55
        d.rectangle([x+5, ty_start, x+col_w-5, ty_start+100], fill=(6,15,28))
        d.rectangle([x+5, ty_start, x+col_w-5, ty_start+100], outline=oc, width=1)
        draw_centered(d, "TOOLS", x+col_w//2, ty_start+4, get_font(9,True), oc)
        for j,tool in enumerate(phase["tools"]):
            draw_centered(d, tool, x+col_w//2, ty_start+18+j*16, get_font(9), (200,200,210))
        
        # Activities
        act_y = ty_start + 108
        d.rectangle([x+5, act_y, x+col_w-5, act_y+230], fill=(5,12,24))
        d.rectangle([x+5, act_y, x+col_w-5, act_y+230], outline=oc, width=1)
        draw_centered(d, "ACTIVITIES", x+col_w//2, act_y+4, get_font(9,True), oc)
        for j,act in enumerate(phase["activities"]):
            draw_centered(d, f"• {act}", x+col_w//2, act_y+20+j*33, get_font(9), (200,200,210))
        
        # Phase arrow connector
        if i < len(phases)-1:
            arr_x = x + col_w - 5
            arr_y = start_y + 25
            draw_arrow(d, arr_x, arr_y, arr_x+10, arr_y, (150,150,150), 2)
        
        # Milestone checkpoint below activities
        ck_y = act_y + 238
        draw_rect(d, x+10, ck_y, x+col_w-10, ck_y+28, (10,25,45), oc, radius=4)
        milestones = ["Surface mapped","Vulns identified","Access gained","Pivoted / Data","Report delivered"]
        draw_centered(d, f"✓ {milestones[i]}", x+col_w//2, ck_y+7, get_font(9,True), tc)
    
    # Rules of Engagement box at bottom
    roe_y = start_y + col_h - 10
    d.rectangle([60, roe_y, W-60, roe_y+80], fill=(5,15,35))
    d.rectangle([60, roe_y, W-60, roe_y+80], outline=(0,150,255), width=2)
    draw_centered(d, "RULES OF ENGAGEMENT (ROE) — Legal Authorization Required Before Testing", W//2, roe_y+8, get_font(12,True), (0,180,255))
    roe_items = [
        "▪ Signed scope document with explicit IP ranges / domains / accounts in scope",
        "▪ Testing window (dates/times), emergency contacts, safe-to-break thresholds",
        "▪ Data handling: no exfiltration of real PII — use hashes/tokens as proof",
        "▪ Get-out-of-jail letter authorizing testing activities (legal protection for testers)",
    ]
    for i,item in enumerate(roe_items):
        x_offset = 80 + (i%2)*660
        y_offset = roe_y+26 + (i//2)*22
        d.text((x_offset, y_offset), item, font=get_font(9), fill=(180,200,220))
    
    # Footer
    d.line([(60,H-30),(W-60,H-30)], fill=(40,60,80), width=1)
    draw_centered(d, "SCIA 425 — Software Testing & Assurance  |  Chapter 8: Security Testing & Penetration Testing", W//2, H-22, get_font(10), (100,130,160))
    
    img.save(f"{OUT}/ch08-security-testing.png")
    print("ch08 done")

# ─────────────────────────────────────────────────────────────
# DIAGRAM 9: Process Assurance Framework
# ─────────────────────────────────────────────────────────────
def make_ch09():
    img = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(img)
    
    GOLD = (220,180,0)
    BLUE = (60,140,255)
    PURPLE = (160,80,255)
    GREEN = (0,200,100)
    
    tf = get_font(26, bold=True)
    draw_centered(d, "SOFTWARE PROCESS ASSURANCE FRAMEWORK", W//2, 16, tf, GOLD)
    d.line([(60,50),(W-60,50)], fill=GOLD, width=2)
    
    # Center of concentric diagram
    cx, cy = 430, 395
    
    # Outer ring: Organizational (gold)
    r_outer = 270
    d.ellipse([cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer], fill=(25,20,5), outline=GOLD, width=4)
    
    # Middle ring: Project (blue)
    r_mid = 195
    d.ellipse([cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid], fill=(5,15,30), outline=BLUE, width=4)
    
    # Inner ring: Product (purple)
    r_inner = 120
    d.ellipse([cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner], fill=(12,5,28), outline=PURPLE, width=4)
    
    # Center: Deliverable (green)
    r_center = 52
    d.ellipse([cx-r_center, cy-r_center, cx+r_center, cy+r_center], fill=(5,30,15), outline=GREEN, width=4)
    draw_centered(d, "ASSURED", cx, cy-14, get_font(9,True), GREEN)
    draw_centered(d, "SOFTWARE", cx, cy-1, get_font(9,True), GREEN)
    draw_centered(d, "PRODUCT", cx, cy+12, get_font(9,True), GREEN)
    
    # Ring labels - inner product ring
    prod_items = ["Code Quality","Test Coverage","Defect Density","Security Score"]
    prod_angles = [315, 45, 135, 225]
    for item,angle in zip(prod_items, prod_angles):
        rad = math.radians(angle)
        tx_ = cx + int(82*math.cos(rad))
        ty_ = cy + int(82*math.sin(rad))
        draw_centered(d, item, tx_, ty_-6, get_font(8,True), PURPLE)
    
    # Ring labels - middle project ring
    proj_items = ["Software Quality Plan","Metrics Collection","Reviews & Audits","Issue Tracking"]
    proj_angles = [300, 30, 150, 210]
    for item,angle in zip(proj_items, proj_angles):
        rad = math.radians(angle)
        tx_ = cx + int(155*math.cos(rad))
        ty_ = cy + int(155*math.sin(rad))
        draw_centered(d, item, tx_, ty_-6, get_font(8,True), BLUE)
    
    # Ring labels - outer org ring
    org_items = ["Quality\nMgmt System","Process\nPolicies","Standards &\nCompliance","Training &\nCapability"]
    org_angles = [290, 20, 160, 200]
    for item,angle in zip(org_items, org_angles):
        rad = math.radians(angle)
        tx_ = cx + int(230*math.cos(rad))
        ty_ = cy + int(230*math.sin(rad))
        for j,line in enumerate(item.split("\n")):
            draw_centered(d, line, tx_, ty_-7+j*13, get_font(8,True), GOLD)
    
    # PDCA arrows around rings
    pdca = [("PLAN", 315, (0,180,255)), ("DO", 45, (100,220,100)),
            ("CHECK", 135, (255,200,0)), ("ACT", 225, (255,100,100))]
    for label,angle,color in pdca:
        rad = math.radians(angle)
        ax_ = cx + int(r_outer*0.82*math.cos(rad))
        ay_ = cy + int(r_outer*0.82*math.sin(rad))
        # Arrow arc indicator
        a2 = math.radians(angle+35)
        bx_ = cx + int((r_outer-20)*math.cos(a2))
        by_ = cy + int((r_outer-20)*math.sin(a2))
        draw_arrow(d, ax_, ay_, bx_, by_, color, 3)
        a0 = math.radians(angle-30)
        lx_ = cx + int((r_outer+20)*math.cos(a0))
        ly_ = cy + int((r_outer+20)*math.sin(a0))
        draw_centered(d, label, lx_, ly_-8, get_font(13,True), color)
    
    # Ring level indicators (left)
    legend_x = 20
    for i,(label,color) in enumerate([("ORG LEVEL",GOLD),("PROJECT LEVEL",BLUE),("PRODUCT LEVEL",PURPLE)]):
        ly = 65 + i*25
        d.line([(legend_x, ly+10),(legend_x+30,ly+10)], fill=color, width=3)
        d.text((legend_x+35, ly+4), label, font=get_font(9,True), fill=color)
    
    # Right side: CMMI Maturity Levels
    mx, my = 880, 65
    mw, mh = 460, 600
    d.rectangle([mx, my, mx+mw, my+mh], fill=(5,12,25))
    d.rectangle([mx, my, mx+mw, my+mh], outline=(80,100,140), width=2)
    draw_centered(d, "CMMI MATURITY MODEL", mx+mw//2, my+10, get_font(14,True), GOLD)
    
    cmmi = [
        (5, "OPTIMIZING", "Continuous improvement,\ndefect prevention, innovation", (80,0,0), (255,80,80)),
        (4, "QUANTITATIVELY\nMANAGED", "Statistical process control,\nquantitative quality goals", (70,40,0), (220,140,0)),
        (3, "DEFINED", "Org-wide standard processes,\ntailored per project", (0,60,0), (60,200,80)),
        (2, "MANAGED", "Project-level planning,\ntracking, requirements mgmt", (0,30,80), (60,140,220)),
        (1, "INITIAL", "Ad-hoc, heroic efforts,\nunpredictable results", (50,50,50), (160,160,160)),
    ]
    
    step_w = mw - 60
    for i,(level,name,desc,bg,fg) in enumerate(cmmi):
        step_h = 90
        indent = i * 18
        yi = my + mh - (i+1)*step_h - 20
        xi = mx + 30 + indent
        sw = step_w - indent
        draw_rect(d, xi, yi, xi+sw, yi+step_h-5, bg, fg, radius=5)
        d.text((xi+10, yi+8), f"Level {level}", font=get_font(10,True), fill=fg)
        for j,line in enumerate(name.split("\n")):
            draw_centered(d, line, xi+sw//2, yi+8+j*16, get_font(11,True), fg)
        for j,line in enumerate(desc.split("\n")):
            draw_centered(d, line, xi+sw//2, yi+45+j*15, get_font(9), (200,200,200))
    
    # ISO standards panel
    iso_y = my + mh - 5
    draw_rect(d, mx, iso_y, mx+mw, iso_y+65, (5,15,30), (80,140,200), radius=5)
    draw_centered(d, "KEY STANDARDS", mx+mw//2, iso_y+6, get_font(11,True), (140,200,255))
    standards = ["IEEE 730: SQA Plans", "ISO 9001: QMS", "ISO/IEC 12207: SDLC Processes", "ISO/IEC 25010: Product Quality"]
    for i,s in enumerate(standards):
        xi = mx+10 + (i%2)*230
        yi = iso_y+25 + (i//2)*18
        d.text((xi, yi), f"• {s}", font=get_font(9), fill=(180,210,240))
    
    # Footer
    d.line([(60,H-30),(W-60,H-30)], fill=(40,60,80), width=1)
    draw_centered(d, "SCIA 425 — Software Testing & Assurance  |  Chapter 9: Process Assurance", W//2, H-22, get_font(10), (100,130,160))
    
    img.save(f"{OUT}/ch09-process-assurance.png")
    print("ch09 done")

# ─────────────────────────────────────────────────────────────
# DIAGRAM 10: Statistical Quality Control
# ─────────────────────────────────────────────────────────────
def make_ch10():
    img = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(img)
    
    RED = (255,60,60)
    BLUE_C = (60,140,255)
    ORANGE = (255,140,0)
    GREEN = (0,200,100)
    
    tf = get_font(26, bold=True)
    draw_centered(d, "STATISTICAL QUALITY CONTROL IN SOFTWARE", W//2, 16, tf, (0,220,255))
    d.line([(60,50),(W-60,50)], fill=(0,180,220), width=2)
    
    # ── Left panel: Control Chart ──
    lx, ly = 50, 65
    lw, lh = 620, 360
    d.rectangle([lx,ly,lx+lw,ly+lh], fill=(5,12,25))
    d.rectangle([lx,ly,lx+lw,ly+lh], outline=(60,100,140), width=2)
    draw_centered(d, "CONTROL CHART — Defect Rate per Sprint (X-bar)", lx+lw//2, ly+8, get_font(12,True), (0,220,255))
    
    # Chart area
    chart_x = lx+55
    chart_y = ly+35
    chart_w = lw - 70
    chart_h = lh - 65
    d.rectangle([chart_x, chart_y, chart_x+chart_w, chart_y+chart_h], fill=(4,10,20))
    
    # Data points (20 sprints)
    random.seed(42)
    mean_val = 0.5
    ucl_val = 0.85
    lcl_val = 0.15
    
    data = [0.48, 0.52, 0.45, 0.60, 0.38, 0.72, 0.55, 0.90, 0.42, 0.50,
            0.35, 0.58, 0.62, 0.44, 0.95, 0.48, 0.30, 0.55, 0.08, 0.52]
    
    n_pts = len(data)
    pt_x_gap = chart_w // (n_pts + 1)
    
    def data_to_y(v):
        # map v from [0,1.1] to chart_h
        return chart_y + chart_h - int((v / 1.1) * chart_h)
    
    # UCL / LCL / Mean lines
    ucl_y = data_to_y(ucl_val)
    lcl_y = data_to_y(lcl_val)
    mean_y = data_to_y(mean_val)
    
    d.line([(chart_x, ucl_y),(chart_x+chart_w, ucl_y)], fill=RED, width=2)
    d.line([(chart_x, lcl_y),(chart_x+chart_w, lcl_y)], fill=RED, width=2)
    d.line([(chart_x, mean_y),(chart_x+chart_w, mean_y)], fill=GREEN, width=2)
    
    # Labels
    d.text((lx+5, ucl_y-8), "UCL", font=get_font(9,True), fill=RED)
    d.text((lx+5, mean_y-8), "μ", font=get_font(9,True), fill=GREEN)
    d.text((lx+5, lcl_y-8), "LCL", font=get_font(9,True), fill=RED)
    
    # Grid lines
    for gv in [0.2, 0.4, 0.6, 0.8, 1.0]:
        gy = data_to_y(gv)
        d.line([(chart_x, gy),(chart_x+chart_w, gy)], fill=(20,35,55), width=1)
        d.text((lx+5, gy-5), f"{gv:.1f}", font=get_font(7), fill=(80,100,120))
    
    # Plot points and connect
    pts_coords = []
    for i, val in enumerate(data):
        px_ = chart_x + (i+1)*pt_x_gap
        py_ = data_to_y(val)
        pts_coords.append((px_, py_))
    
    # Line
    for i in range(len(pts_coords)-1):
        d.line([pts_coords[i], pts_coords[i+1]], fill=BLUE_C, width=2)
    
    # Points
    for i,(px_,py_) in enumerate(pts_coords):
        out_of_control = data[i] > ucl_val or data[i] < lcl_val
        if out_of_control:
            d.ellipse([px_-8,py_-8,px_+8,py_+8], outline=RED, width=2)
            d.ellipse([px_-4,py_-4,px_+4,py_+4], fill=RED)
        else:
            d.ellipse([px_-4,py_-4,px_+4,py_+4], fill=BLUE_C)
        # Sprint label
        d.text((px_-4, chart_y+chart_h+4), str(i+1), font=get_font(7), fill=(120,140,160))
    
    d.text((chart_x+chart_w//2-15, chart_y+chart_h+15), "SPRINT #", font=get_font(9), fill=(120,140,160))
    draw_centered(d, "Defect Rate", lx+18, chart_y+chart_h//2, get_font(9), (120,140,160))
    
    # OOC annotation
    draw_centered(d, "● = Out-of-Control Signal (Special Cause Variation)", lx+lw//2, ly+lh-12, get_font(9), RED)
    
    # ── Right panel: Pareto Chart ──
    rx, ry = 690, 65
    rw, rh = 660, 360
    d.rectangle([rx,ry,rx+rw,ry+rh], fill=(5,12,25))
    d.rectangle([rx,ry,rx+rw,ry+rh], outline=(60,100,140), width=2)
    draw_centered(d, "PARETO CHART — Defect Categories (80/20 Rule)", rx+rw//2, ry+8, get_font(12,True), ORANGE)
    
    pareto_data = [
        ("SQL Inject.", 38),
        ("Buffer Overflow", 27),
        ("Auth Bypass", 19),
        ("XSS", 8),
        ("CSRF", 4),
        ("Info Disclose", 2),
        ("Config Error", 2),
    ]
    total = sum(v for _,v in pareto_data)
    
    pc_x = rx + 60
    pc_y = ry + 35
    pc_w = rw - 80
    pc_h = rh - 65
    d.rectangle([pc_x, pc_y, pc_x+pc_w, pc_y+pc_h], fill=(4,10,20))
    
    bar_w = pc_w // len(pareto_data) - 6
    max_val = pareto_data[0][1]
    
    cumulative = 0
    cum_points = []
    
    for i,(name,val) in enumerate(pareto_data):
        bar_h = int((val / max_val) * (pc_h - 20))
        bx_ = pc_x + i*(pc_w//len(pareto_data)) + 3
        by_ = pc_y + pc_h - bar_h
        
        # Bar with gradient effect
        intensity = int(60 + (val/max_val)*160)
        d.rectangle([bx_, by_, bx_+bar_w, pc_y+pc_h], fill=(0,40,intensity))
        d.rectangle([bx_, by_, bx_+bar_w, pc_y+pc_h], outline=(60,140,255), width=1)
        
        # Value on bar
        draw_centered(d, str(val), bx_+bar_w//2, by_-14, get_font(9,True), BLUE_C)
        
        # Label below
        short_name = name[:10]
        draw_centered(d, short_name, bx_+bar_w//2, pc_y+pc_h+5, get_font(8), (160,180,200))
        
        # Cumulative line point
        cumulative += val
        cum_pct = cumulative / total
        cx_ = bx_ + bar_w//2
        cy_ = pc_y + pc_h - int(cum_pct*(pc_h-20))
        cum_points.append((cx_, cy_))
        
        # 80% marker
        if abs(cum_pct - 0.8) < 0.12 and cumulative/total >= 0.79:
            pass
    
    # Cumulative line
    for i in range(len(cum_points)-1):
        d.line([cum_points[i], cum_points[i+1]], fill=ORANGE, width=2)
    for pt in cum_points:
        d.ellipse([pt[0]-4,pt[1]-4,pt[0]+4,pt[1]+4], fill=ORANGE)
    
    # 80% horizontal line
    pct80_y = pc_y + pc_h - int(0.80*(pc_h-20))
    d.line([(pc_x, pct80_y),(pc_x+pc_w, pct80_y)], fill=(255,80,80,128), width=1)
    d.text((pc_x+pc_w-35, pct80_y-14), "80%", font=get_font(9,True), fill=RED)
    
    # Y-axis labels
    for pct in [0.25, 0.50, 0.75, 1.0]:
        gy_ = pc_y + pc_h - int(pct*(pc_h-20))
        d.text((rx+10, gy_-6), f"{int(pct*100)}%", font=get_font(8), fill=(100,130,160))
    
    # Legend
    d.rectangle([rx+rw-110, ry+40, rx+rw-10, ry+80], fill=(5,12,25))
    d.rectangle([rx+rw-110, ry+40, rx+rw-10, ry+80], outline=(50,70,100), width=1)
    d.rectangle([rx+rw-105,ry+48,rx+rw-90,ry+58], fill=(0,60,200))
    d.text((rx+rw-86, ry+48), "Count", font=get_font(8), fill=(160,180,210))
    d.line([(rx+rw-105,ry+68),(rx+rw-90,ry+68)], fill=ORANGE, width=2)
    d.text((rx+rw-86, ry+63), "Cumul %", font=get_font(8), fill=ORANGE)
    
    # ── Bottom: Defect Metrics Table ──
    bx_, by_ = 50, 440
    bw_, bh_ = 1300, 240
    d.rectangle([bx_, by_, bx_+bw_, by_+bh_], fill=(5,12,25))
    d.rectangle([bx_, by_, bx_+bw_, by_+bh_], outline=(60,100,140), width=2)
    draw_centered(d, "KEY SOFTWARE QUALITY METRICS", bx_+bw_//2, by_+8, get_font(13,True), (0,220,255))
    
    metrics = [
        {
            "name": "Defect Density",
            "formula": "Defects / KLOC",
            "target": "< 1.0 defects/KLOC",
            "desc": "Number of confirmed defects per\n1000 lines of source code",
            "color": (0,60,120),
            "fc": (80,180,255)
        },
        {
            "name": "Defect Removal\nEfficiency (DRE)",
            "formula": "Defects_Pre / (Defects_Pre + Defects_Post)",
            "target": "> 95% (world class)",
            "desc": "% of defects found before\nproduct reaches the customer",
            "color": (0,60,0),
            "fc": (80,220,120)
        },
        {
            "name": "Mean Time Between\nFailures (MTBF)",
            "formula": "Total_Time / # Failures",
            "target": "Maximize (reliability goal)",
            "desc": "Average operational time\nbetween system failures",
            "color": (60,40,0),
            "fc": (220,160,60)
        },
        {
            "name": "Test Coverage %",
            "formula": "(Covered_Lines / Total_Lines) × 100",
            "target": "> 80% branch coverage",
            "desc": "Percentage of code exercised\nby the test suite",
            "color": (50,0,80),
            "fc": (180,100,255)
        },
        {
            "name": "Cost of Quality\n(COQ) Ratio",
            "formula": "CoQ / Total_Dev_Cost × 100%",
            "target": "Prevention > Appraisal > Failure",
            "desc": "Prevention + Appraisal costs vs.\nInternal + External failure costs",
            "color": (40,30,0),
            "fc": (200,180,60)
        },
    ]
    
    col_w_m = bw_ // len(metrics)
    for i,m in enumerate(metrics):
        mx_ = bx_ + i*col_w_m + 5
        draw_rect(d, mx_, by_+30, mx_+col_w_m-10, by_+bh_-10, m["color"], m["fc"], radius=6)
        for j,line in enumerate(m["name"].split("\n")):
            draw_centered(d, line, mx_+col_w_m//2-5, by_+38+j*16, get_font(10,True), m["fc"])
        d.line([(mx_+10, by_+72),(mx_+col_w_m-20, by_+72)], fill=m["fc"], width=1)
        draw_centered(d, m["formula"], mx_+col_w_m//2-5, by_+76, get_font(8,True), (220,220,180))
        draw_centered(d, f"Target: {m['target']}", mx_+col_w_m//2-5, by_+92, get_font(8,True), GREEN)
        for j,line in enumerate(m["desc"].split("\n")):
            draw_centered(d, line, mx_+col_w_m//2-5, by_+118+j*16, get_font(8), (180,190,210))
    
    # Western Electric Rules note
    we_y = by_ + bh_ - 45
    draw_rect(d, bx_+10, we_y, bx_+bw_-10, we_y+35, (5,15,30), (0,150,200), radius=4)
    draw_centered(d, "Western Electric Rules for Out-of-Control Detection:", bx_+bw_//4, we_y+8, get_font(9,True), (0,200,220))
    rules = ["1 pt outside ±3σ  |  9 pts same side of mean  |  6 pts trending  |  14 pts alternating"]
    draw_centered(d, rules[0], bx_+bw_//2+50, we_y+22, get_font(9), (180,210,230))
    
    img.save(f"{OUT}/ch10-statistical-qc.png")
    print("ch10 done")

if __name__ == "__main__":
    make_ch06()
    make_ch07()
    make_ch08()
    make_ch09()
    make_ch10()
    print("All diagrams generated!")
