"""Render the execution addendum PDF from the authoritative Markdown (requires reportlab)."""
import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs' / 'TEST_CASE_EXECUTION.md'
OUTPUT = ROOT / 'Deliverable-4-Test-Validation' / 'Test_Case_Execution_Revision_1_1.pdf'


def inline(value):
    value = value.replace('\u2014', ' - ').replace('\u2013', '-')
    value = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', value)
    value = escape(value)
    value = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    return value


def main():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyAudit', fontName='Helvetica', fontSize=9.5,
                              leading=14, spaceAfter=7, textColor=colors.HexColor('#263445')))
    styles.add(ParagraphStyle('CodeAudit', fontName='Courier', fontSize=8.5,
                              leading=12, leftIndent=10, spaceAfter=4))
    styles['Title'].fontSize = 22
    styles['Title'].leading = 27
    styles['Title'].alignment = TA_LEFT
    styles['Title'].textColor = colors.HexColor('#163b59')
    styles['Heading2'].textColor = colors.HexColor('#163b59')
    story, headers, in_code = [], None, False
    for line in SOURCE.read_text(encoding='utf-8').splitlines():
        if line.startswith('```'):
            in_code = not in_code
            continue
        if not line.strip():
            story.append(Spacer(1, 3))
            headers = None
            continue
        if in_code:
            story.append(Paragraph(escape(line), styles['CodeAudit']))
        elif line.startswith('# '):
            story.append(Paragraph(inline(line[2:]), styles['Title']))
        elif line.startswith('## '):
            story.append(Paragraph(inline(line[3:]), styles['Heading2']))
        elif line.startswith('|'):
            cells = [x.strip() for x in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r'[-: ]+', x) for x in cells):
                continue
            if headers is None:
                headers = cells
                continue
            block = [Paragraph(inline(cells[0]), styles['Heading3'])]
            for label, value in zip(headers[1:], cells[1:]):
                block.append(Paragraph('<b>' + inline(label) + ':</b> ' + inline(value), styles['BodyAudit']))
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))
        else:
            story.append(Paragraph(inline(line), styles['BodyAudit']))

    def furniture(canvas, doc):
        canvas.setStrokeColor(colors.HexColor('#d4dfe7'))
        canvas.line(20 * mm, 282 * mm, 190 * mm, 282 * mm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#607080'))
        canvas.drawString(20 * mm, 285 * mm, 'ONLINE EXAM PORTAL  |  EXECUTION REVISION 1.1')
        canvas.drawString(20 * mm, 12 * mm, '14 November 2026  |  Recorded results remain separate from planned checks')
        canvas.drawRightString(190 * mm, 12 * mm, str(doc.page))

    SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
                      topMargin=24 * mm, bottomMargin=22 * mm,
                      title='Online Exam Portal - Test Case Execution Revision 1.1',
                      author='Online Exam Portal project').build(story, onFirstPage=furniture, onLaterPages=furniture)
    print(OUTPUT)


if __name__ == '__main__':
    main()
