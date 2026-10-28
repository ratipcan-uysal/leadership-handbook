#!/usr/bin/env python3
"""Check content preservation, source coverage and rendered page boundaries.

Requires the build dependencies plus pdfplumber and pypdfium2 for verification.
Visual inspection of the rendered changed pages is still required.
"""
import hashlib
import io
import json
import re
import subprocess
import unicodedata
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]

def norm(t):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',t).lower())

def main():
    original_bytes=subprocess.check_output(['git','show','2df876d44ef26f1071ab398c2fa3e73dbf41b017:leadership_handbook.pdf'],cwd=ROOT)
    actual_bytes=(ROOT/'leadership_handbook.pdf').read_bytes()
    old=PdfReader(io.BytesIO(original_bytes));new=PdfReader(io.BytesIO(actual_bytes))
    source=(ROOT/'content/appendix-c.md').read_text()
    appendix_start=next(i for i,p in enumerate(new.pages) if 'Appendix C\nQuestion Banks' in p.extract_text())
    sources_start=next(i for i,p in enumerate(new.pages) if 'Appendix D\nSource Library' in p.extract_text())
    assert appendix_start==75
    assert len(new.pages)-sources_start==12
    # Exact PDF body stream preservation before Appendix C.
    for i in range(75):
        assert old.pages[i].get_contents().get_data()==new.pages[i].get_contents().get_data(),f'Original page {i+1} changed'
    # Exact rendered preservation for all untouched pages; source-library
    # footers legitimately have new numbers, so compare above their footer.
    old_render=pdfium.PdfDocument(original_bytes);new_render=pdfium.PdfDocument(actual_bytes)
    for old_i,new_i in [(i,i) for i in range(75)]+[(i,sources_start+i-82) for i in range(82,94)]:
        a=old_render[old_i].render(scale=1).to_pil().convert('RGB')
        b=new_render[new_i].render(scale=1).to_pil().convert('RGB')
        if old_i>=82:
            a=a.crop((0,0,612,740));b=b.crop((0,0,612,740))
        assert a.tobytes()==b.tobytes(),f'Rendered body differs on original page {old_i+1}'
    # Check every Markdown content line, not only the count of questions.
    appendix_text=norm('\n'.join(p.extract_text() for p in new.pages[appendix_start:sources_start]))
    lines=[l for l in source.splitlines() if l.strip() and l!='---' and not l.startswith('<!--')]
    for line in lines:
        clean=re.sub(r'^(?:#{1,3} |[->] )','',line).replace('**','')
        assert norm(clean) in appendix_text,f'Source line missing in PDF: {clean[:80]}'
    questions=re.findall(r'^- (.+)$',source,re.M)
    assert len(questions)==178
    assert len({norm(q) for q in questions})==len(questions),'Exact duplicate question'
    blocks=re.split(r'^## ',source,flags=re.M)[1:]
    banks=[b for b in blocks if not b.startswith(('How to use these banks','Source note'))]
    assert len(banks)==12
    for b in banks:
        for label in ['**Use when.**','**After the answer.**','**Keep in mind.**','> Source:']:
            assert label in b,f'{label} missing from {b.splitlines()[0]}'
    # Geometry catches content placed outside the page frame. A visual review
    # separately checks balance, readability, and awkward continuation pages.
    with pdfplumber.open(io.BytesIO(actual_bytes)) as pdf:
        for i in range(appendix_start,sources_start):
            chars=[c for c in pdf.pages[i].chars if 45<c['top']<735 and c['text'].strip()]
            assert chars,f'Empty appendix body on {i+1}'
            assert all(c['x0']>=78 and c['x1']<=540 and c['bottom']<=735 for c in chars),f'Body bounds on {i+1}'
        for i in range(sources_start,len(pdf.pages)):
            footer=''.join(c['text'] for c in pdf.pages[i].chars if 270<=c['x0']<=342 and 740<c['top']<770)
            assert footer==f'- {i+1} -',f'Duplicate or incorrect footer: {footer}'
    report={'status':'passed','original_body_pages_preserved':87,'exact_original_content_streams':75,'appendix_pages':sources_start-appendix_start,'source_lines_present':len(lines),'question_items':len(questions),'banks_with_use_and_follow_through':len(banks),'total_pages':len(new.pages),'source_library_footer_numbers':'single and correct','sha256':hashlib.sha256(actual_bytes).hexdigest(),'visual_review':'required separately'}
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
