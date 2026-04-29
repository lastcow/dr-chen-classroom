#!/usr/bin/env python3
"""Prepare rich structured SCIA-120 weekly presentation content from reading materials."""
from pathlib import Path
import re, json, html

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
OUT = DOCS / 'scia-120/presentations/_content'
OUT.mkdir(parents=True, exist_ok=True)
AUTHOR = 'Dr. Zhijiang Chen'
INSTITUTION = 'Frostburg State University'

STOP = {'overview','summary','review questions','key terms','references','further reading'}

def clean_md(s: str) -> str:
    s = re.sub(r'```.*?```', ' ', s, flags=re.S)
    s = re.sub(r'`([^`]*)`', r'\1', s)
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[*_>#|~]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', clean_md(text))
    return [p.strip() for p in parts if 35 <= len(p.strip()) <= 260]

def heading_clean(h):
    h = clean_md(h)
    h = re.sub(r'^\d+(\.\d+)*\s*', '', h).strip()
    return h

def split_sections(md):
    title = re.search(r'^#\s+(.+)$', md, re.M)
    title = title.group(1).strip() if title else 'SCIA 120 Reading Material'
    short = re.sub(r'^Chapter\s+\d+:\s*', '', title)
    matches = list(re.finditer(r'^(#{2,3})\s+(.+)$', md, re.M))
    sections=[]
    for idx,m in enumerate(matches):
        h=heading_clean(m.group(2))
        if any(x in h.lower() for x in STOP):
            continue
        start=m.end(); end=matches[idx+1].start() if idx+1 < len(matches) else len(md)
        body=clean_md(md[start:end])
        if len(body) < 90: continue
        sections.append({'heading':h,'body':body,'sentences':sentences(body)})
    return short, sections

def compact(s, n=190):
    s=clean_md(s)
    return s if len(s)<=n else s[:n].rsplit(' ',1)[0]+'…'

def detail_lines(sec, fallback):
    sents = sec.get('sentences') or []
    lines=[]
    for sent in sents[:4]:
        lines.append(compact(sent, 180))
    while len(lines) < 3:
        lines.append(fallback)
    return lines[:4]

def visual_prompt(title, details, week, kind='concept'):
    words = ', '.join([title] + [d.split('.')[0] for d in details[:2]])
    if kind == 'cover':
        return f'Tech-dark line-art hero for Week {week}: {title}, with networks, locks, shields, data paths, and classroom learning cues.'
    if kind == 'agenda':
        return f'Line-art roadmap showing the major learning path for {title}; connected nodes represent reading concepts and classroom application.'
    return f'Line-art explanatory scene for {title}: {words}. Use labels, arrows, and security-control symbols.'

def dialog_for(title, details, week, slide_no, mode):
    main = details[0] if details else f'{title} is a key Week {week} security idea.'
    prompt = f'How would you recognize {title.lower()} in a real organization?'
    if mode == 'definition':
        clean_title = title.strip().rstrip('?')
        prompt = f'How does this concept help us analyze the incident?' if clean_title.lower().startswith(('what is ', 'what are ')) else f'What problem does {clean_title.lower()} help us understand?'
    elif mode == 'application':
        prompt = f'If this issue appeared in a campus or business system, what evidence would you collect first?'
    elif mode == 'review':
        prompt = f'What is the one sentence takeaway for {title.lower()}?'
    return {
        'scenario': f'A campus technology team is reviewing a realistic Week {week} incident where {title.lower()} affects users, data, or operations.',
        'instructor_prompt': prompt,
        'student_response': compact(f'This concept helps us decide what is at risk, what evidence to check, and which control would reduce harm. For this slide, the key clue is: {main}', 210),
        'teaching_point': f'Push the answer beyond a definition: name the asset, identify the risk, choose evidence, and justify a practical control.'
    }

def make_slides(week, title, sections):
    concepts=[s for s in sections if s['heading'].lower()!='overview']
    if not concepts:
        concepts=[{'heading':title,'body':title,'sentences':[title]}]
    overview = next((s for s in sections if s['heading'].lower()=='overview'), concepts[0])
    agenda=[c['heading'] for c in concepts[:7]]
    slides=[]
    def add(slide_type, title_, main, details, mode='dialog_plus_line_art', visual_kind='concept'):
        n=len(slides)+1
        slides.append({
            'number': n,
            'type': slide_type,
            'title': title_,
            'main_idea': compact(main, 230),
            'details': [compact(d, 185) for d in details[:4]],
            'classroom_dialog': dialog_for(title_, details, week, n, slide_type),
            'visual_prompt': visual_prompt(title_, details, week, visual_kind),
            'visual_mode': mode,
            'speaker_goal': f'Teach {title_} using evidence, scenario reasoning, and a concrete security takeaway.'
        })
    # 1 cover, still has line art and dialog metadata
    add('cover', title, f'Introduce Week {week}: {title}.', [overview.get('sentences',[overview.get('body','')])[0] if overview.get('sentences') else compact(overview.get('body',title))], 'line_art', 'cover')
    # 2 agenda
    add('agenda', 'Overall roadmap', 'The week moves from core definitions to practical security decisions.', agenda[:4] or [title], 'dialog_plus_line_art', 'agenda')
    # 3 learning objectives
    add('objectives', 'Learning objectives', 'Students should explain, apply, and evaluate the week’s main security ideas.', [f'Explain {a}.' for a in agenda[:4]], 'dialog_plus_line_art')
    # 4 scenario frame
    add('application', 'Opening scenario', f'Use a realistic scenario to anchor {title} in operational decision-making.', detail_lines(overview, title)[:3], 'dialog_plus_line_art')
    # 5-24 rich concept slides from reading sections
    idx=0
    while len(slides) < 24:
        sec=concepts[idx % len(concepts)]
        details=detail_lines(sec, f'{sec["heading"]} connects to risk, controls, and evidence.')
        stype = ['definition','concept','application','evidence'][idx % 4]
        main = details[0]
        add(stype, sec['heading'], main, details, 'dialog_plus_line_art')
        idx += 1
    # 25 key vocabulary
    terms=[c['heading'] for c in concepts[:10]]
    add('vocabulary', 'Key terms to keep', 'Vocabulary becomes useful when students can connect terms to scenarios and evidence.', terms[:4], 'dialog_plus_line_art')
    # 26 compare
    compare_terms=(terms + [title,title])[:2]
    add('comparison', f'Compare: {compare_terms[0]} vs. {compare_terms[1]}', 'Comparing related ideas helps students avoid shallow memorization.', [f'Where {compare_terms[0]} applies.', f'Where {compare_terms[1]} applies.', 'How the difference changes the security decision.'], 'dialog_plus_line_art')
    # 27 applied decision
    add('application', 'Applied decision checkpoint', 'Students should translate concepts into a defensible security decision.', ['Identify the asset or process at risk.', 'Choose a preventive, detective, or corrective control.', 'Explain what evidence would prove the control is working.'], 'dialog_plus_line_art')
    # 28 review prompts
    add('review', 'Review questions', 'Retrieval practice should ask students to define, compare, apply, and evaluate.', ['Define one core concept in plain language.', 'Compare two controls or threats from the week.', 'Apply one idea to a campus or business system.', 'Evaluate why a solution might fail in practice.'], 'dialog_plus_line_art')
    # 29 bridge
    add('bridge', 'Bridge to lab and assessment', 'The reading should transfer into evidence-based lab work and written explanations.', ['Collect evidence, not just screenshots.', 'Explain what the artifact proves.', 'Connect the proof back to risk and control selection.'], 'dialog_plus_line_art')
    # 30 close
    add('closing', 'Takeaway', f'The central takeaway from Week {week} is to reason from risk to evidence to action.', [title, 'Security is a decision process, not just a tool list.', 'Use the reading to justify practical choices.'], 'dialog_plus_line_art')
    assert len(slides)==30
    return slides

for week in range(1,16):
    src = DOCS / f'scia-120/chapter-{week:02d}.md'
    md = src.read_text(encoding='utf-8', errors='ignore')
    title, sections = split_sections(md)
    slides = make_slides(week, title, sections)
    data = {
        'week': week,
        'title': title,
        'source': f'scia-120/chapter-{week:02d}.md',
        'author': AUTHOR,
        'institution': INSTITUTION,
        'summary': compact((sections[0]['body'] if sections else title), 360),
        'key_concepts': [s['heading'] for s in sections if s['heading'].lower()!='overview'][:8],
        'slides': slides
    }
    (OUT / f'week-{week:02d}.json').write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'prepared 15 JSON files in {OUT}')
