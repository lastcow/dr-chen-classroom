#!/usr/bin/env python3
from pathlib import Path
import json, html, re
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'; BASE=DOCS/'scia-120/presentations'; CONTENT=BASE/'_content'; BASE.mkdir(parents=True, exist_ok=True)
def esc(x): return html.escape(str(x or ''))
CSS = '''<style>:root{--bg:#040914;--ink:#e7f2ff;--muted:#a9bad0;--cyan:#38bdf8;--line:rgba(56,189,248,.28);--mono:"IBM Plex Mono",monospace;--serif:"Playfair Display",Georgia,serif;--sans:Inter,Arial,sans-serif}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--sans)}body:before{content:"";position:fixed;inset:0;background:radial-gradient(circle at 15% 15%,rgba(56,189,248,.22),transparent 35%),radial-gradient(circle at 85% 72%,rgba(139,92,246,.18),transparent 37%),linear-gradient(135deg,#040914,#071426 52%,#060b17);z-index:0}body:after{content:"";position:fixed;inset:0;background-image:linear-gradient(rgba(125,211,252,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(125,211,252,.055) 1px,transparent 1px);background-size:42px 42px;z-index:0}#deck{position:fixed;inset:0;display:flex;height:100vh;transition:transform .68s cubic-bezier(.77,0,.175,1);z-index:2}.slide{position:relative;width:100vw;height:100vh;flex:0 0 100vw;overflow:hidden;padding:5.8vh 5.6vw 8vh;display:flex;flex-direction:column}.chrome,.foot{position:absolute;left:5.6vw;right:5.6vw;display:flex;justify-content:space-between;gap:2vw;font:700 11px/1.2 var(--mono);letter-spacing:.16em;text-transform:uppercase;color:rgba(169,186,208,.82)}.chrome{top:3.8vh}.foot{bottom:3.6vh}.kicker{font:800 12px var(--mono);letter-spacing:.22em;text-transform:uppercase;color:var(--cyan);margin-bottom:1.6vh}.hero{justify-content:center}.h-hero{font:900 clamp(48px,6.5vw,104px)/.92 var(--serif);letter-spacing:-.055em;margin:0}.h-xl{font:900 clamp(38px,5vw,76px)/.96 var(--serif);letter-spacing:-.045em;margin:0}.h-md{font:900 clamp(30px,3.85vw,54px)/1.02 var(--serif);letter-spacing:-.035em;margin:0}.lead{font:450 clamp(17px,1.32vw,23px)/1.36 var(--sans);color:#cbdced;max-width:74vw;margin:2vh 0}.frame{position:relative;z-index:1;width:100%}.grid-2{display:grid;grid-template-columns:minmax(0,1.24fr) minmax(280px,.76fr);gap:1.8vw;align-items:center;min-height:74vh}.grid-2>*{min-width:0}.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.2vw}.card{border:1px solid var(--line);background:linear-gradient(180deg,rgba(15,28,49,.88),rgba(7,18,33,.74));box-shadow:0 22px 72px rgba(0,0,0,.32);border-radius:24px;padding:2.4vh 1.35vw}.card h3{font:850 22px/1.08 var(--serif);margin:0 0 1vh}.detail{color:#cfe2f3;font-size:16px;line-height:1.34;margin:.65vh 0;border-left:3px solid rgba(56,189,248,.58);padding-left:1vw}.detail-list{display:grid;gap:.95vh;margin-top:1.8vh}.visual{border:1px solid rgba(56,189,248,.34);border-radius:28px;overflow:hidden;background:#07111f;box-shadow:0 24px 90px rgba(0,0,0,.36);max-width:100%;contain:paint}.visual svg{display:block;width:100%;height:auto;max-height:52vh}.dialog-card{border:1px solid rgba(34,211,238,.28);background:linear-gradient(180deg,rgba(8,24,42,.86),rgba(6,18,32,.78));border-radius:22px;padding:1.7vh 1.2vw;margin-top:1.8vh;box-shadow:0 18px 60px rgba(0,0,0,.28)}.dialog-title{font:800 11px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:#7dd3fc;margin-bottom:1vh}.dialog-row{display:grid;grid-template-columns:102px 1fr;gap:.8vw;margin:.65vh 0;color:#dbeafe;font-size:15px;line-height:1.28}.dialog-row strong{color:#67e8f9;font:800 11px var(--mono);letter-spacing:.08em;text-transform:uppercase}.teaching-point{margin-top:1vh;padding-top:1vh;border-top:1px solid rgba(125,211,252,.18);color:#bfdbfe;font-size:14px;line-height:1.3}.section-num{display:none}.slide-badge{display:inline-flex;align-items:center;justify-content:center;width:34px;height:24px;margin-right:10px;border:1px solid rgba(125,211,252,.45);border-radius:999px;background:rgba(56,189,248,.10);color:#bfdbfe}.mini-map{display:flex;gap:.48vw;position:absolute;bottom:3.6vh;left:50%;transform:translateX(-50%);z-index:5}.mini-map button{width:8px;height:8px;border-radius:99px;border:1px solid rgba(125,211,252,.55);background:transparent;padding:0}.mini-map button.active{width:27px;background:#38bdf8}.hint{position:fixed;right:18px;bottom:14px;z-index:4;color:rgba(169,186,208,.55);font:11px var(--mono)}.index{position:fixed;inset:0;background:rgba(2,6,23,.94);z-index:9;display:none;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;padding:44px;overflow:auto}.index.show{display:grid}.thumb{border:1px solid rgba(56,189,248,.25);border-radius:14px;padding:16px;background:#0b1424;color:#dbeafe;cursor:pointer}.thumb b{color:#38bdf8;font-family:var(--mono);font-size:12px}.thumb span{display:block;margin-top:8px;font-weight:800}.split-stack{display:grid;grid-template-rows:auto auto;gap:1.5vh}.meta-row{display:flex;gap:1vw;flex-wrap:wrap;color:#93c5fd;font:800 12px var(--mono);letter-spacing:.12em;text-transform:uppercase;margin-top:2vh}@media(max-width:900px){.grid-2{grid-template-columns:1fr}.grid-3{grid-template-columns:1fr}.visual{display:none}.slide{padding:7vh 5vw 10vh}.h-hero{font-size:14vw}}</style>'''
JS = '''<script>const deck=document.getElementById('deck');const slides=[...document.querySelectorAll('.slide')];let cur=0;deck.style.width=(slides.length*100)+'vw';const nav=document.createElement('div');nav.className='mini-map';slides.forEach((s,i)=>{const b=document.createElement('button');b.onclick=()=>go(i);nav.appendChild(b)});document.body.appendChild(nav);const idx=document.createElement('div');idx.className='index';slides.forEach((s,i)=>{const t=s.querySelector('h1,h2')?.textContent?.trim()||('Slide '+(i+1));const d=document.createElement('div');d.className='thumb';d.innerHTML='<b>'+String(i+1).padStart(2,'0')+'</b><span>'+t+'</span>';d.onclick=()=>{idx.classList.remove('show');go(i)};idx.appendChild(d)});document.body.appendChild(idx);function go(i){cur=Math.max(0,Math.min(slides.length-1,i));deck.style.transform=`translateX(${-cur*100}vw)`;[...nav.children].forEach((b,j)=>b.classList.toggle('active',j===cur));}addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='PageDown')go(cur+1);if(e.key==='ArrowLeft'||e.key==='PageUp')go(cur-1);if(e.key==='Escape')idx.classList.toggle('show')});let lock=0;addEventListener('wheel',e=>{const now=Date.now();if(now-lock<650)return;lock=now;go(cur+(e.deltaY>0?1:-1))},{passive:true});go(0);</script>'''

def compact_label(x, n=16):
    x=re.sub(r'\s+', ' ', str(x or '')).strip()
    return x if len(x)<=n else x[:n].rsplit(' ',1)[0]+'...'

def svg_art(slide, week):
    title=slide['title']; details=slide.get('details') or []
    visual_kind=(slide.get('visual_kind') or slide.get('visual_prompt') or title).lower()
    raw_labels=[title]+[re.sub(r'[^A-Za-z0-9 /-]','',d.split('.')[0]) for d in details]
    labels=[]
    for x in raw_labels:
        x=compact_label(x, 16)
        if x and x not in labels: labels.append(x)
    while len(labels)<4: labels.append(['Asset','Risk','Control','Evidence'][len(labels)%4])
    sid=f'g{week}_{slide["number"]}'; num=slide['number']
    def label(i): return esc(labels[i % len(labels)])
    if any(k in visual_kind for k in ['hero','shield','network','privacy','lock']):
        main=f"""<path d="M500 115 L690 205 V365 L500 455 L310 365 V205 Z" class="shape big"/><path d="M500 175 C560 205 585 275 560 342 C545 382 522 405 500 420 C478 405 455 382 440 342 C415 275 440 205 500 175Z" class="core"/><path d="M470 304 L493 327 L536 270" class="check"/><circle cx="250" cy="245" r="34" class="core"/><circle cx="750" cy="245" r="34" class="core"/><path d="M284 245 H440 M560 245 H716" class="accent"/><text x="500" y="475" text-anchor="middle">PROTECT - DETECT - RESPOND</text>"""
    elif any(k in visual_kind or k in title.lower() for k in ['cia','triad']):
        main=f"""<polygon points="500,90 720,430 280,430" class="shape big"/><text x="500" y="205" text-anchor="middle">CONFIDENTIALITY</text><text x="390" y="385" text-anchor="middle">INTEGRITY</text><text x="610" y="385" text-anchor="middle">AVAILABILITY</text><circle cx="500" cy="315" r="54" class="core"/><text x="500" y="320" text-anchor="middle">CIA</text>"""
    elif any(k in visual_kind or k in title.lower() for k in ['dad','disclosure','alteration','destruction','warning']):
        main=f"""<polygon points="500,95 735,430 265,430" class="danger"/><text x="500" y="210" text-anchor="middle">DISCLOSURE</text><text x="385" y="385" text-anchor="middle">ALTERATION</text><text x="615" y="385" text-anchor="middle">DESTRUCTION</text><circle cx="500" cy="315" r="54" class="dangerCore"/><text x="500" y="320" text-anchor="middle">DAD</text>"""
    elif any(k in visual_kind or k in title.lower() for k in ['risk','matrix']):
        cells=''.join(f'<rect x="{320+c*120}" y="{160+r*80}" width="110" height="70" rx="14" class="cell c{r+c}"/>' for r in range(3) for c in range(3))
        main=f"""<text x="500" y="130" text-anchor="middle">RISK = ASSET x THREAT x IMPACT</text>{cells}<path d="M330 420 L690 180" class="accent"/><circle cx="665" cy="195" r="20" class="core"/>"""
    elif any(k in visual_kind or k in title.lower() for k in ['evidence','audit','assurance','stamp']):
        main=f"""<rect x="335" y="120" width="330" height="310" rx="28" class="shape big"/><path d="M390 190 H610 M390 245 H610 M390 300 H560" class="accent"/><circle cx="610" cy="345" r="62" class="core"/><path d="M575 345 L600 370 L645 315" class="check"/><text x="500" y="475" text-anchor="middle">VERIFY - MONITOR - IMPROVE</text>"""
    elif any(k in visual_kind or k in title.lower() for k in ['control','dashboard','least privilege','access','defense','layer']):
        main=f"""<rect x="260" y="120" width="480" height="310" rx="30" class="shape big"/><circle cx="375" cy="235" r="58" class="core"/><path d="M350 235 L370 255 L405 210" class="check"/><rect x="470" y="185" width="190" height="34" rx="12" class="pill"/><rect x="470" y="245" width="145" height="34" rx="12" class="pill"/><rect x="470" y="305" width="175" height="34" rx="12" class="pill"/><text x="500" y="475" text-anchor="middle">POLICY - TOOL - TEST - EVIDENCE</text>"""
    else:
        main=f"""<path d="M500 115 L690 205 V365 L500 455 L310 365 V205 Z" class="shape big"/><path d="M500 175 C560 205 585 275 560 342 C545 382 522 405 500 420 C478 405 455 382 440 342 C415 275 440 205 500 175Z" class="core"/><path d="M470 304 L493 327 L536 270" class="check"/><text x="500" y="475" text-anchor="middle">PROTECT - DETECT - RESPOND</text>"""
    card_pos=[(75,120),(75,310),(745,120),(745,310)]
    cards=[]
    for i,(x,y) in enumerate(card_pos):
        cards.append(f'<g><rect x="{x}" y="{y}" width="180" height="92" rx="18" class="mini"/><circle cx="{x+34}" cy="{y+34}" r="15" class="dot"/><text x="{x+64}" y="{y+32}">{label(i)}</text><path d="M{x+28} {y+62} H{x+150}" class="sub"/></g>')
    gridv=''.join(f'<path class="grid" d="M{n} 45V500"/>' for n in range(100,1000,100))
    gridh=''.join(f'<path class="grid" d="M60 {n}H940"/>' for n in range(100,540,100))
    return (
        f'<svg viewBox="0 0 1000 560" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Gamma-style line art for {esc(title)}">'
        f'<defs><linearGradient id="{sid}" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset=".55" stop-color="#6366f1"/><stop offset="1" stop-color="#22d3ee"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
        f'<style>.bg{{fill:#06111f}}.grid{{stroke:#1d3a5f;opacity:.24}}.shape{{fill:rgba(8,24,42,.66);stroke:url(#{sid});stroke-width:2.4}}.big{{filter:url(#glow)}}.core{{fill:rgba(56,189,248,.16);stroke:#67e8f9;stroke-width:2.2}}.danger{{fill:rgba(127,29,29,.22);stroke:#f97316;stroke-width:2.4}}.dangerCore{{fill:rgba(248,113,113,.18);stroke:#fb7185;stroke-width:2.2}}.accent{{fill:none;stroke:#7dd3fc;stroke-width:4;stroke-linecap:round}}.check{{fill:none;stroke:#34d399;stroke-width:8;stroke-linecap:round;stroke-linejoin:round}}.mini{{fill:rgba(15,28,49,.78);stroke:rgba(125,211,252,.38);stroke-width:1.5}}.dot{{fill:#38bdf8;opacity:.75}}.pill{{fill:rgba(125,211,252,.12);stroke:rgba(125,211,252,.34)}}.sub{{stroke:rgba(191,219,254,.35);stroke-width:3}}.cell{{fill:rgba(56,189,248,.08);stroke:rgba(125,211,252,.28)}}.c4{{fill:rgba(251,191,36,.18)}}.c8{{fill:rgba(248,113,113,.20)}}text{{font-family:Inter,Arial,sans-serif;font-size:13px;fill:#dbeafe;font-weight:800}}</style>'
        f'<rect class="bg" width="1000" height="560" rx="28"/>{gridv}{gridh}<text x="60" y="70" style="font-family:IBM Plex Mono,monospace;font-size:13px;fill:#7dd3fc;letter-spacing:1.6px">GAMMA-STYLE VISUAL - SLIDE {num:02d}</text>{main}{"".join(cards)}</svg>'
    )


def dialog_html(d):
    return f'<div class="dialog-card"><div class="dialog-title">Classroom Dialog</div><div class="dialog-row"><strong>Scenario</strong><span>{esc(d.get("scenario"))}</span></div><div class="dialog-row"><strong>Instructor</strong><span>{esc(d.get("instructor_prompt"))}</span></div><div class="dialog-row"><strong>Student</strong><span>{esc(d.get("student_response"))}</span></div><div class="teaching-point"><strong>Teaching point:</strong> {esc(d.get("teaching_point"))}</div></div>'

def slide_html(slide,data):
    week=data['week']; n=slide['number']; total=len(data['slides']); title=slide['title']
    chrome=f'<div class="chrome"><div>SCIA 120 · Week {week:02d}</div><div>{esc(slide["type"])} · {n:02d}/{total:02d}</div></div>'
    foot=f'<div class="foot"><div>{esc(data["author"])} · {esc(data["institution"])}</div><div>Week {week:02d} deck</div></div>'
    visual=f'<div class="visual">{svg_art(slide,week)}</div>'; dialog=dialog_html(slide.get('classroom_dialog',{}))
    details=''.join(f'<div class="detail">{esc(d)}</div>' for d in slide.get('details',[])[:4])
    if slide['type']=='cover':
        body=f'<div class="frame grid-2"><div><div class="kicker">Introduction to Secure Computing and Information Assurance</div><h1 class="h-hero">{esc(title)}</h1><p class="lead">Author: <strong>{esc(data["author"])}</strong> ({esc(data["institution"])})</p><div class="meta-row"><span>Tech dark</span><span>AI line art</span><span>Reading-based content</span></div>{dialog}</div>{visual}</div>'; cls='slide hero'
    elif slide['type']=='agenda':
        cards=''.join(f'<div class="card"><h3>{esc(d)}</h3><p>Core reading concept for Week {week:02d}.</p></div>' for d in slide.get('details',[])[:4])
        body=f'<div class="frame grid-2"><div><div class="kicker">Overall Page</div><h2 class="h-xl">{esc(title)}</h2><p class="lead">{esc(slide["main_idea"])}</p><div class="grid-3">{cards}</div>{dialog}</div>{visual}</div>'; cls='slide'
    else:
        body=f'<div class="frame grid-2"><div class="split-stack"><div><div class="kicker"><span class="slide-badge">{n:02d}</span> {esc(slide["type"])}</div><h2 class="h-md">{esc(title)}</h2><p class="lead">{esc(slide["main_idea"])}</p><div class="detail-list">{details}</div></div>{dialog}</div>{visual}</div>'; cls='slide'
    return f'<section class="{cls}">{chrome}{body}{foot}</section>'

def render_deck(data):
    slides=''.join(slide_html(s,data) for s in data['slides'])
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>SCIA 120 Week {data["week"]:02d} · {esc(data["title"])}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600;700&family=Playfair+Display:wght@600;700;800;900&display=swap" rel="stylesheet">{CSS}</head><body><div class="hint">← → navigate · ESC index · Back to quit</div><div id="deck">{slides}</div>{JS}</body></html>'

def render_index(all_data):
    cards=[]
    for data in all_data:
        w=data['week']; cards.append(f'<div class="presentation-card"><h3>Week {w:02d}: {esc(data["title"])}</h3><p>{esc(data.get("summary",""))}</p><div class="presentation-actions"><a class="md-button" href="/scia-120/presentations/week-{w:02d}/">Open presentation page</a><a class="md-button md-button--primary" href="/scia-120/presentations/week-{w:02d}-deck/">Launch deck</a></div></div>')
    return f'''---
title: SCIA 120 Presentations
created: 2026-04-29
updated: 2026-04-29
type: summary
tags: [course, lecture, template]
sources: []
---

# SCIA 120 Presentations

<style>.presentation-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:1.2rem;margin-top:1.5rem}}.presentation-card{{border:1px solid rgba(63,81,181,.24);border-radius:14px;padding:1.1rem 1.2rem;background:var(--md-default-bg-color);box-shadow:0 8px 24px rgba(0,0,0,.06)}}.presentation-card h3{{margin:0 0 .65rem 0!important;line-height:1.25}}.presentation-card p{{margin:0 0 1rem 0}}.presentation-actions{{display:flex;flex-wrap:wrap;gap:.55rem;margin-top:.8rem}}.presentation-actions .md-button{{margin:0!important}}</style>

Magazine-style, tech-dark HTML presentations generated from the **SCIA 120 reading materials**. Each weekly presentation has 30 slides, slide-specific classroom dialog, and AI-generated SVG line-art concept visuals.

Author shown on each cover page: **Dr. Zhijiang Chen (Frostburg State University)**.

## Weekly Presentation Index

<div class="presentation-grid">
{''.join(cards)}
</div>
'''

def render_wrapper(data):
    w=data['week']; concepts=', '.join(esc(x) for x in data.get('key_concepts',[])[:6])
    return f'''---
title: Week {w:02d} Presentation — {esc(data['title'])}
created: 2026-04-29
updated: 2026-04-29
type: lecture
tags: [course, lecture, template, technology]
sources: [scia-120/chapter-{w:02d}.md]
---

# Week {w:02d} Presentation — {esc(data['title'])}

**Brief:** This tech-dark, magazine-style deck summarizes the Week {w:02d} SCIA 120 reading material. The deck includes a cover page, overall page, learning objectives, concept slides, applied scenarios, review prompts, slide-specific classroom dialog, and AI-generated SVG line-art visuals matched to the slide content.

**Source reading:** [Week {w:02d} Reading Material](/scia-120/chapter-{w:02d}/)  
**Key concepts:** {concepts}

<a class="md-button md-button--primary" href="/scia-120/presentations/week-{w:02d}-deck/">Launch presentation</a>
<a class="md-button" href="/scia-120/chapter-{w:02d}/">Open reading material</a>

## Preview

<iframe src="/scia-120/presentations/week-{w:02d}-deck/" style="width:100%; height:680px; border:1px solid #1e3a5f; border-radius:14px; background:#050b14;"></iframe>
'''

def main():
    all_data=[]
    for i in range(1,16):
        data=json.loads((CONTENT/f'week-{i:02d}.json').read_text(encoding='utf-8')); all_data.append(data)
        deck_dir=BASE/f'week-{i:02d}-deck'; deck_dir.mkdir(parents=True, exist_ok=True)
        (deck_dir/'index.html').write_text(render_deck(data), encoding='utf-8')
        (BASE/f'week-{i:02d}.md').write_text(render_wrapper(data), encoding='utf-8')
    (BASE/'index.md').write_text(render_index(all_data), encoding='utf-8')
    print('rendered 15 decks, wrappers, and index')
if __name__=='__main__': main()
