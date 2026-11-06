"""Xuất PDF bản thảo từ Markdown; không dựng logo hoặc thông tin nhóm giả."""
from pathlib import Path
import html
import re
import json

from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / 'project.json').read_text(encoding='utf-8'))
OUTPUT = ROOT / 'output/pdf/bao_cao_laptop_ban_thao.pdf'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
font_candidates = [
    (Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
    (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
]
normal, bold = next((a, b) for a, b in font_candidates if a.exists() and b.exists())
pdfmetrics.registerFont(TTFont('Body', str(normal)))
pdfmetrics.registerFont(TTFont('BodyBold', str(bold)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')

INK = colors.HexColor('#172c43')
MUTED = colors.HexColor('#526377')
BLUE = colors.HexColor('#2563a6')
WIDTH, HEIGHT = A4
MARGIN = 45
CONTENT = WIDTH - 2 * MARGIN
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TextVN', fontName='Body', fontSize=10.2, leading=15.3, textColor=INK, spaceAfter=9))
styles.add(ParagraphStyle(name='HeadVN', fontName='BodyBold', fontSize=15, leading=20, textColor=INK, spaceAfter=12, keepWithNext=True))
styles.add(ParagraphStyle(name='SubVN', fontName='BodyBold', fontSize=12, leading=17, textColor=INK, spaceBefore=10, spaceAfter=10, keepWithNext=True))
styles.add(ParagraphStyle(name='CellVN', fontName='Body', fontSize=8, leading=11, textColor=INK))
styles.add(ParagraphStyle(name='CellHeadVN', fontName='BodyBold', fontSize=8, leading=11, textColor=colors.white))
styles.add(ParagraphStyle(name='CoverVN', fontName='BodyBold', fontSize=28, leading=35, textColor=INK, spaceAfter=18))
styles.add(ParagraphStyle(name='LabelVN', fontName='BodyBold', fontSize=10, leading=15, textColor=BLUE, spaceAfter=14))
styles.add(ParagraphStyle(name='SmallVN', fontName='Body', fontSize=9, leading=13, textColor=MUTED, spaceAfter=8))
styles.add(ParagraphStyle(name='UniversityVN', fontName='BodyBold', fontSize=15, leading=20, alignment=TA_CENTER, textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle(name='InstituteVN', fontName='BodyBold', fontSize=11.5, leading=17, alignment=TA_CENTER, textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle(name='CoverTitleVN', fontName='BodyBold', fontSize=24, leading=32, alignment=TA_CENTER, textColor=INK, spaceAfter=10))
styles.add(ParagraphStyle(name='CoverCenterVN', fontName='Body', fontSize=12, leading=18, alignment=TA_CENTER, textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle(name='CoverLabelVN', fontName='BodyBold', fontSize=11, leading=17, alignment=TA_CENTER, textColor=BLUE, spaceAfter=8))
styles.add(ParagraphStyle(name='CoverSmallVN', fontName='Body', fontSize=10, leading=15, alignment=TA_CENTER, textColor=MUTED, spaceAfter=8))


def markup(text):
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#2563a6">\1</link>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#d9e1eb'))
    canvas.line(MARGIN, 39, WIDTH-MARGIN, 39)
    canvas.setFont('Body', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 25, 'Mid-term 2 | Đề 6 - Laptop Price | Nhóm 1 | Bản thảo')
    canvas.drawRightString(WIDTH-MARGIN, 25, str(doc.page))
    canvas.restoreState()


story = []
story += [Spacer(1, 12), Paragraph(PROJECT['university'].upper(), styles['UniversityVN']),
          Paragraph(PROJECT['institute'].upper(), styles['InstituteVN']), Spacer(1, 8)]
# Giữ nguyên ảnh logo từ nguồn chính thức, chỉ đặt kích thước trong trang PDF.
neu_logo = Image(str(ROOT/'assets/branding/neu_logo.webp'), width=190, height=190*1807/2560)
aep_logo = Image(str(ROOT/'assets/branding/aep_logo_original.png'), width=139, height=139*1292/1910)
logos = Table([[neu_logo, aep_logo]], colWidths=[190,190], rowHeights=[140], hAlign='CENTER')
logos.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                          ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                          ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
story += [logos, Spacer(1, 20), Paragraph('BẢN THẢO BÁO CÁO GIỮA KỲ 2', styles['CoverLabelVN']),
          Paragraph('PHÂN TÍCH GIÁ LAPTOP', styles['CoverTitleVN']),
          Paragraph('Đề 6: Laptop Price', styles['CoverCenterVN']),
          Paragraph('Học phần: '+PROJECT['course'], styles['CoverCenterVN']),
          Spacer(1, 18), Paragraph('Nhóm thực hiện: '+PROJECT['group'], styles['CoverLabelVN']), Spacer(1, 6)]
team_rows = [[Paragraph('HỌ VÀ TÊN',styles['CellHeadVN']),Paragraph('MÃ SINH VIÊN',styles['CellHeadVN'])]]
team_rows += [[Paragraph(m['name'],styles['TextVN']),Paragraph(m['student_id'],styles['TextVN'])] for m in PROJECT['members']]
team = Table(team_rows, colWidths=[245,115], hAlign='CENTER')
team.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
    ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f4f8'),colors.white]),
    ('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#d9e1eb'))]))
story += [team, Spacer(1, 35), Paragraph('Hà Nội, tháng 11 năm 2026',styles['CoverSmallVN']),PageBreak()]

md = (ROOT / 'reports/bao_cao_phan_tich.md').read_text(encoding='utf-8')
body = md[md.index('## '):]
lines = body.splitlines()
idx = 0
paragraph_lines = []


def flush():
    if paragraph_lines:
        story.append(Paragraph(markup(' '.join(paragraph_lines)), styles['TextVN']))
        paragraph_lines.clear()


while idx < len(lines):
    line = lines[idx].strip()
    if not line:
        flush()
        idx += 1
        continue
    if line.startswith('## '):
        flush()
        title = line[3:]
        # Mỗi hình có trang riêng để giữ nhãn và phần diễn giải dễ đọc.
        if title != '3.1. Phân phối giá' and story and not isinstance(story[-1], PageBreak):
            story.append(PageBreak())
        story.append(Paragraph(markup(title), styles['HeadVN']))
        idx += 1
        continue
    if line.startswith('|'):
        flush()
        rows = []
        while idx < len(lines) and lines[idx].strip().startswith('|'):
            values = [v.strip() for v in lines[idx].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', v) for v in values):
                rows.append(values)
            idx += 1
        cols = len(rows[0])
        if cols == 3:
            widths = [CONTENT*0.24, CONTENT*0.19, CONTENT*0.57]
        elif cols == 2:
            widths = [CONTENT*0.34, CONTENT*0.66]
        elif cols == 6:
            widths = [CONTENT*f for f in [0.15,0.22,0.14,0.15,0.15,0.19]]
        elif cols == 5:
            widths = [CONTENT*f for f in [0.35,0.09,0.18,0.18,0.20]]
        else:
            widths = [CONTENT/cols]*cols
        rendered = [[Paragraph(markup(v), styles['CellHeadVN'] if r == 0 else styles['CellVN']) for v in row] for r, row in enumerate(rows)]
        tbl = Table(rendered, colWidths=widths, repeatRows=1, hAlign='LEFT')
        tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f4f8')]),('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#d9e1eb'))]))
        story += [tbl, Spacer(1,12)]
        continue
    image_match = re.match(r'!\[([^\]]+)\]\(([^)]+)\)', line)
    if image_match:
        flush()
        image_path = ROOT / 'reports' / image_match.group(2)
        with PILImage.open(image_path) as im:
            w, ht = im.size
        draw_width = CONTENT
        draw_height = draw_width * ht / w
        if draw_height > 335:
            draw_width *= 335/draw_height
            draw_height = 335
        story += [Image(str(image_path), width=draw_width, height=draw_height), Spacer(1,14)]
        idx += 1
        continue
    if line.startswith('- '):
        flush()
        story.append(Paragraph(markup(line[2:]), styles['TextVN'], bulletText='-'))
    else:
        paragraph_lines.append(line)
    idx += 1
flush()
doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=MARGIN, leftMargin=MARGIN, topMargin=44, bottomMargin=55,
                        title='Phân tích giá laptop - Nhóm 1 - NEU', author='Nhóm 1 - Đại học Kinh tế Quốc dân')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
