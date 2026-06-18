#!/usr/bin/env python3
import re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,'scripts')
from _common import CONTENT, CHAR_DIR, parse_frontmatter
from lint_character_density import density_score
book='红楼梦'
char_dir=CHAR_DIR/book
ids={p.stem for p in char_dir.glob('*.md')}
inbound=defaultdict(set)
for p in char_dir.glob('*.md'):
    for m in re.finditer(r'\[\[([^\]|]+)', p.read_text(encoding='utf-8-sig')):
        t=m.group(1).strip()
        if t in ids and t!=p.stem: inbound[t].add(p.stem)
for p in (CONTENT/'topics'/book).glob('*.md'):
    for m in re.finditer(r'\[\[([^\]|]+)', p.read_text(encoding='utf-8-sig')):
        t=m.group(1).strip()
        if t in ids: inbound[t].add('topic')
lines=[]
for p in sorted(char_dir.glob('*.md')):
    fm, body = parse_frontmatter(p)
    cid=fm.get('id') or p.stem
    if cid=='西门庆': continue
    m=re.search(r'## 关键情节\s*\n(.*?)(?=\n## |\Z)', body, re.S)
    plots=[ln.strip() for ln in (m.group(1).splitlines() if m else []) if ln.strip().startswith('-')]
    d={'rel':len(fm.get('relations') or []),'plot':len(plots),'main':'## 主要关系' in body,'review':'## 评析' in body,'inbound':len(inbound[cid])}
    sc=density_score(d)
    if sc==25:
        lines.append(f"=== {cid} rel={d['rel']} plot={d['plot']} in={d['inbound']} ===")
        lines.extend(plots)
        lines.append('')
Path('scripts/_tier11_scan.txt').write_text('\n'.join(lines), encoding='utf-8')
print(sum(1 for l in lines if l.startswith('===')))
