#!/usr/bin/env python3
from pathlib import Path
import json, html, re
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'; BASE=DOCS/'scia-120/presentations'; CONTENT=BASE/'_content'; BASE.mkdir(parents=True, exist_ok=True)
def esc(x): return html.escape(str(x or ''))
CSS = '''<style>:root{--bg:#040914;--ink:#e7f2ff;--muted:#a9bad0;--cyan:#38bdf8;--line:rgba(56,189,248,.28);--mono:"IBM Plex Mono",monospace;--serif:"Playfair Display",Georgia,serif;--sans:Inter,Arial,sans-serif}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--sans)}body:before{content:"";position:fixed;inset:0;background:radial-gradient(circle at 15% 15%,rgba(56,189,248,.22),transparent 35%),radial-gradient(circle at 85% 72%,rgba(139,92,246,.18),transparent 37%),linear-gradient(135deg,#040914,#071426 52%,#060b17);z-index:0}body:after{content:"";position:fixed;inset:0;background-image:linear-gradient(rgba(125,211,252,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(125,211,252,.055) 1px,transparent 1px);background-size:42px 42px;z-index:0}#deck{position:fixed;inset:0;display:flex;height:100vh;transition:transform .68s cubic-bezier(.77,0,.175,1);z-index:2}.slide{position:relative;width:100vw;height:100vh;flex:0 0 100vw;overflow:hidden;padding:5.8vh 5.6vw 8vh;display:flex;flex-direction:column}.chrome,.foot{position:absolute;left:5.6vw;right:5.6vw;display:flex;justify-content:space-between;gap:2vw;font:700 11px/1.2 var(--mono);letter-spacing:.16em;text-transform:uppercase;color:rgba(169,186,208,.82)}.chrome{top:3.8vh}.foot{bottom:3.6vh}.kicker{font:800 12px var(--mono);letter-spacing:.22em;text-transform:uppercase;color:var(--cyan);margin-bottom:1.6vh}.hero{justify-content:center}.h-hero{font:900 clamp(48px,6.5vw,104px)/.92 var(--serif);letter-spacing:-.055em;margin:0}.h-xl{font:900 clamp(38px,5vw,76px)/.96 var(--serif);letter-spacing:-.045em;margin:0}.h-md{font:900 clamp(30px,3.85vw,54px)/1.02 var(--serif);letter-spacing:-.035em;margin:0}.lead{font:450 clamp(17px,1.32vw,23px)/1.36 var(--sans);color:#cbdced;max-width:74vw;margin:2vh 0}.frame{position:relative;z-index:1;width:100%}.grid-2{display:grid;grid-template-columns:minmax(0,1.24fr) minmax(280px,.76fr);gap:1.8vw;align-items:center;min-height:74vh}.grid-2>*{min-width:0}.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.2vw}.card{border:1px solid var(--line);background:linear-gradient(180deg,rgba(15,28,49,.88),rgba(7,18,33,.74));box-shadow:0 22px 72px rgba(0,0,0,.32);border-radius:24px;padding:2.4vh 1.35vw}.card h3{font:850 22px/1.08 var(--serif);margin:0 0 1vh}.detail{color:#cfe2f3;font-size:16px;line-height:1.34;margin:.65vh 0;border-left:3px solid rgba(56,189,248,.58);padding-left:1vw}.detail-list{display:grid;gap:.95vh;margin-top:1.8vh}.visual{border:1px solid rgba(56,189,248,.34);border-radius:28px;overflow:hidden;background:#07111f;box-shadow:0 24px 90px rgba(0,0,0,.36);max-width:100%;contain:paint}.visual svg{display:block;width:100%;height:auto;max-height:52vh}.dialog-card{border:1px solid rgba(34,211,238,.28);background:linear-gradient(180deg,rgba(8,24,42,.86),rgba(6,18,32,.78));border-radius:22px;padding:1.7vh 1.2vw;margin-top:1.8vh;box-shadow:0 18px 60px rgba(0,0,0,.28)}.dialog-title{font:800 11px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:#7dd3fc;margin-bottom:1vh}.dialog-row{display:grid;grid-template-columns:102px 1fr;gap:.8vw;margin:.65vh 0;color:#dbeafe;font-size:15px;line-height:1.28}.dialog-row strong{color:#67e8f9;font:800 11px var(--mono);letter-spacing:.08em;text-transform:uppercase}.teaching-point{margin-top:1vh;padding-top:1vh;border-top:1px solid rgba(125,211,252,.18);color:#bfdbfe;font-size:14px;line-height:1.3}.section-num{display:none}.slide-badge{display:inline-flex;align-items:center;justify-content:center;width:34px;height:24px;margin-right:10px;border:1px solid rgba(125,211,252,.45);border-radius:999px;background:rgba(56,189,248,.10);color:#bfdbfe}.mini-map{display:flex;gap:.48vw;position:absolute;bottom:3.6vh;left:50%;transform:translateX(-50%);z-index:5}.mini-map button{width:8px;height:8px;border-radius:99px;border:1px solid rgba(125,211,252,.55);background:transparent;padding:0}.mini-map button.active{width:27px;background:#38bdf8}.hint{position:fixed;right:18px;bottom:14px;z-index:4;color:rgba(169,186,208,.55);font:11px var(--mono)}.index{position:fixed;inset:0;background:rgba(2,6,23,.94);z-index:9;display:none;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;padding:44px;overflow:auto}.index.show{display:grid}.thumb{border:1px solid rgba(56,189,248,.25);border-radius:14px;padding:16px;background:#0b1424;color:#dbeafe;cursor:pointer}.thumb b{color:#38bdf8;font-family:var(--mono);font-size:12px}.thumb span{display:block;margin-top:8px;font-weight:800}.split-stack{display:grid;grid-template-rows:auto auto;gap:1.5vh}.meta-row{display:flex;gap:1vw;flex-wrap:wrap;color:#93c5fd;font:800 12px var(--mono);letter-spacing:.12em;text-transform:uppercase;margin-top:2vh}@media(max-width:900px){.grid-2{grid-template-columns:1fr}.grid-3{grid-template-columns:1fr}.visual{display:none}.slide{padding:7vh 5vw 10vh}.h-hero{font-size:14vw}}</style>'''
JS = '''<script>const deck=document.getElementById('deck');const slides=[...document.querySelectorAll('.slide')];let cur=0;deck.style.width=(slides.length*100)+'vw';const nav=document.createElement('div');nav.className='mini-map';slides.forEach((s,i)=>{const b=document.createElement('button');b.onclick=()=>go(i);nav.appendChild(b)});document.body.appendChild(nav);const idx=document.createElement('div');idx.className='index';slides.forEach((s,i)=>{const t=s.querySelector('h1,h2')?.textContent?.trim()||('Slide '+(i+1));const d=document.createElement('div');d.className='thumb';d.innerHTML='<b>'+String(i+1).padStart(2,'0')+'</b><span>'+t+'</span>';d.onclick=()=>{idx.classList.remove('show');go(i)};idx.appendChild(d)});document.body.appendChild(idx);function go(i){cur=Math.max(0,Math.min(slides.length-1,i));deck.style.transform=`translateX(${-cur*100}vw)`;[...nav.children].forEach((b,j)=>b.classList.toggle('active',j===cur));}addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='PageDown')go(cur+1);if(e.key==='ArrowLeft'||e.key==='PageUp')go(cur-1);if(e.key==='Escape')idx.classList.toggle('show')});let lock=0;addEventListener('wheel',e=>{const now=Date.now();if(now-lock<650)return;lock=now;go(cur+(e.deltaY>0?1:-1))},{passive:true});go(0);</script>'''

def svg_art(slide, week):
    title=slide['title']; details=slide.get('details') or []
    labels=[title]+[re.sub(r'[^A-Za-z0-9 /-]','',d.split('.')[0])[:26] for d in details]
    labels=[x for x in labels if x][:5]
    while len(labels)<5: labels.append('Evidence')
    coords=[(250,150),(500,115),(690,170),(635,340),(340,340)]
    sid=f'g{week}_{slide["number"]}'
    links=[]; bits=[]
    colors=['#38bdf8','#22d3ee','#818cf8','#34d399','#fbbf24']
    for i,(x,y) in enumerate(coords):
        color=colors[i%5]
        links.append(f'<path d="M500 245 C{(500+x)//2} {115+i*15}, {(500+x)//2} {y+20}, {x} {y}" class="link"/>')
        lab=esc(labels[i][:22])
        bits.append(f'<g><circle cx="{x}" cy="{y}" r="42" class="shape"/><path d="M{x-18} {y} L{x-2} {y+17} L{x+24} {y-22}" stroke="{color}" stroke-width="6" fill="none" stroke-linecap="round"/><text x="{x}" y="{y+72}" text-anchor="middle">{lab}</text></g>')
    prompt=esc(slide.get('visual_prompt','AI-generated line art')[:92])
    gridv=''.join(f'<path class="grid" d="M{n} 45V500"/>' for n in range(90,1000,90))
    gridh=''.join(f'<path class="grid" d="M60 {n}H940"/>' for n in range(90,540,90))
    num=slide['number']
    return (
        f'<svg viewBox="0 0 1000 560" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AI-generated line art for {esc(title)}">'
        f'<defs><linearGradient id="{sid}" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset=".55" stop-color="#818cf8"/><stop offset="1" stop-color="#22d3ee"/></linearGradient></defs>'
        f'<style>.bg{{fill:#06111f}}.grid{{stroke:#1d3a5f;opacity:.38}}.link{{fill:none;stroke:url(#{sid});stroke-width:2;stroke-dasharray:8 10;opacity:.55}}.shape{{fill:rgba(8,24,42,.72);stroke:url(#{sid});stroke-width:2.2}}text{{font-family:Inter,Arial,sans-serif;font-size:12px;fill:#dbeafe;font-weight:800}}</style>'
        f'<rect class="bg" width="1000" height="560" rx="28"/>{gridv}{gridh}'
        f'<circle cx="500" cy="245" r="72" class="shape"/><text x="500" y="240" text-anchor="middle">SLIDE {num:02d}</text><text x="500" y="264" text-anchor="middle">{esc(title[:18])}</text>'
        f'{"".join(links)}{"".join(bits)}<text x="60" y="520" style="font-family:IBM Plex Mono,monospace;font-size:12px;fill:#7dd3fc;letter-spacing:1.5px">AI LINE ART · SLIDE-SPECIFIC VISUAL</text></svg>'
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
