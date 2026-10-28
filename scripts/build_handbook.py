#!/usr/bin/env python3
"""Replace Appendix C while preserving the published handbook's other pages.

Source: content/appendix-c.md. The immutable baseline is read from Git history;
use --base-pdf for an offline exported baseline. No network calls are made.
"""
import argparse
import hashlib
import html
import io
import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import TextStringObject
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '2df876d44ef26f1071ab398c2fa3e73dbf41b017'
NAVY = HexColor('#0b2a47')
GOLD = HexColor('#b8862d')
TEXT = HexColor('#1a1a1a')
MUTED = HexColor('#3d4a52')
FIRST = 75  # zero-based: Appendix C begins on printed page 76
END = 82    # first original Appendix D page, exclusive replacement boundary


def inline(text):
    text = html.escape(text)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)


def furniture(c, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 766, 612, 26, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(79.2, 776, 'Leadership Handbook')
    c.setFillColor(white)
    c.setFont('Helvetica', 8)
    c.drawRightString(532.8, 776, 'Before You Commit')
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.6)
    c.line(79.2, 765.5, 532.8, 765.5)
    c.setFillColor(HexColor('#999999'))
    c.setFont('Helvetica-Oblique', 7)
    c.drawString(79.2, 36, 'Ratipcan Uysal')
    c.setFillColor(MUTED)
    c.setFont('Helvetica', 8)
    c.drawCentredString(306, 36, f'- {FIRST + doc.page} -')
    c.restoreState()


def appendix_pdf(source):
    styles = {
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10.5, leading=15.2, textColor=TEXT, spaceAfter=8),
        'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=10.5, leading=14.5, textColor=TEXT, leftIndent=12, firstLineIndent=0, bulletIndent=0, spaceAfter=4),
        'label': ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=GOLD, spaceAfter=8),
        'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=NAVY, spaceAfter=14),
        'h2': ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=17, leading=22, textColor=NAVY, spaceAfter=12, keepWithNext=True),
        'h3': ParagraphStyle('h3', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=NAVY, spaceBefore=5, spaceAfter=7, keepWithNext=True),
        'domain': ParagraphStyle('domain', fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=NAVY, spaceBefore=3, spaceAfter=3, keepWithNext=True),
        'source': ParagraphStyle('source', fontName='Helvetica-Oblique', fontSize=8, leading=11, textColor=MUTED, spaceBefore=10, spaceAfter=8),
        'link': ParagraphStyle('link', fontName='Helvetica', fontSize=8, leading=11, textColor=NAVY, spaceAfter=10, splitLongWords=True),
    }
    story = []
    for line in source.splitlines():
        if not line.strip():
            continue
        if line == '# Appendix C':
            story += [Spacer(1, 28), HRFlowable(width='100%', thickness=3.5, color=GOLD), Spacer(1,12), Paragraph('Appendix C', styles['label'])]
        elif line == '# Question Banks':
            story += [Paragraph('Question Banks', styles['title']), HRFlowable(width='100%', thickness=0.6,color=GOLD), Spacer(1,12)]
        elif line in ('---', '<!-- pagebreak -->'):
            story.append(PageBreak())
        elif line.startswith('## '):
            story.append(Paragraph(inline(line[3:]), styles['h2']))
        elif line.startswith('### '):
            style='domain' if line[4:] in ('People','Project','Process','Me') else 'h3'
            story.append(Paragraph(inline(line[4:]), styles[style]))
        elif line.startswith('- '):
            story.append(Paragraph(inline(line[2:]), styles['bullet'], bulletText='\u00b7'))
        elif line.startswith('> '):
            story.append(Paragraph(inline(line[2:]), styles['source']))
        elif line.startswith('https://'):
            url=html.escape(line,quote=True)
            story.append(Paragraph(f'<link href="{url}">{url}</link>',styles['link']))
        else:
            story.append(Paragraph(inline(line), styles['body']))
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(612,792), leftMargin=85.2,rightMargin=73.2,topMargin=70,bottomMargin=60, title='Leadership Handbook - Appendix C')
    doc.build(story, onFirstPage=furniture, onLaterPages=furniture)
    return output.getvalue()


def renumber(page, number):
    # Remove the original footer text operator as well as replacing its pixels,
    # so text extraction does not expose two competing page numbers.
    stream=page.get_contents()
    removed=0
    for operands,operator in stream.operations:
        if operator==b'Tj' and re.fullmatch(r'\u0160 \d+ \u0160',str(operands[0])):
            operands[0]=TextStringObject('')
            removed+=1
    if removed!=1:
        raise ValueError('Expected exactly one original footer number')
    page.replace_contents(stream)
    overlay = io.BytesIO()
    c = canvas.Canvas(overlay, pagesize=(612,792))
    c.setFillColor(MUTED)
    c.setFont('Helvetica',8)
    c.drawCentredString(306,36,f'- {number} -')
    c.save()
    page.merge_page(PdfReader(io.BytesIO(overlay.getvalue())).pages[0])
    return page


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-pdf',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'leadership_handbook.pdf')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    baseline=args.base_pdf.read_bytes() if args.base_pdf else subprocess.check_output(['git','show',f'{BASE_COMMIT}:leadership_handbook.pdf'],cwd=ROOT)
    # A Git blob hash prevents accidentally applying the page surgery to a
    # different edition with different boundaries.
    blob=hashlib.sha1(b'blob '+str(len(baseline)).encode()+b'\0'+baseline).hexdigest()
    if blob != '07cdd1459567d7610983a7e22bcebfe93b97fc7c':
        raise ValueError('Baseline is not the verified 94-page edition')
    original=PdfReader(io.BytesIO(baseline))
    assert len(original.pages)==94
    assert 'Appendix C' in original.pages[FIRST].extract_text()
    assert 'Appendix D' in original.pages[END].extract_text()
    source=(ROOT/'content/appendix-c.md').read_text()
    new=PdfReader(io.BytesIO(appendix_pdf(source)))
    writer=PdfWriter()
    for p in original.pages[:FIRST]: writer.add_page(p)
    for p in new.pages: writer.add_page(p)
    for i,p in enumerate(original.pages[END:]):
        attached=writer.add_page(p)
        renumber(attached,FIRST+len(new.pages)+i+1)
    writer.add_metadata({'/Title':'Leadership Handbook','/Author':'Ratipcan Uysal','/Subject':'Leadership guide; expanded question banks, October 2026','/Creator':'scripts/build_handbook.py'})
    writer.add_outline_item('Appendix C - Question Banks',FIRST)
    writer.add_outline_item('Appendix D - Source Library & Online Resources',FIRST+len(new.pages))
    # Add direct navigation to each bank; only the exact heading line qualifies.
    for heading in re.findall(r'^## (.+)$',source,re.M):
        for i,p in enumerate(new.pages):
            if heading in p.extract_text().splitlines():
                writer.add_outline_item(heading,FIRST+i)
                break
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('wb') as f:writer.write(f)
    report={'baseline_commit':BASE_COMMIT,'baseline_blob':blob,'original_pages':94,'replaced_original_pages':[76,82],'appendix_c_pages':len(new.pages),'revised_pages':len(writer.pages),'appendix_d_start':FIRST+len(new.pages)+1,'question_items':len(re.findall(r'^- ',source,re.M)),'output_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
