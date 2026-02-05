#!/usr/bin/env python3
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import textwrap

SRC = Path(__file__).resolve().parents[1] / "ARCHITECTURE_TROUBLESHOOTING.md"
OUT_DIR = Path(__file__).resolve().parents[1] / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PLAIN_OUT = OUT_DIR / "ARCHITECTURE_TROUBLESHOOTING.pdf"
RENDERED_OUT = OUT_DIR / "ARCHITECTURE_TROUBLESHOOTING_RENDERED.pdf"


DEF_WIDTH = 100
LINE_HEIGHT = 11
LEFT = 0.7 * inch
TOP_PAD = 0.7 * inch
BOTTOM_PAD = 0.7 * inch


def draw_box(c, x, y, w, h, label):
    c.setStrokeColor(colors.black)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont('Helvetica', 9)
    tx = x + w / 2
    ty = y + h / 2
    lines = label.split('\n')
    for i, line in enumerate(lines):
        c.drawCentredString(tx, ty + (len(lines) / 2 - i - 0.5) * 9, line)


def arrow(c, x1, y1, x2, y2):
    c.line(x1, y1, x2, y2)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 6
    left_ang = ang + math.pi * 0.85
    right_ang = ang - math.pi * 0.85
    c.line(x2, y2, x2 + size * math.cos(left_ang), y2 + size * math.sin(left_ang))
    c.line(x2, y2, x2 + size * math.cos(right_ang), y2 + size * math.sin(right_ang))


def draw_architecture_diagram(c, x, y):
    w = 6.5 * inch
    h = 3.0 * inch
    c.setFont('Helvetica-Bold', 10)
    c.drawString(x, y + h + 6, 'Architecture (CRC)')

    y0 = y + h - 0.6 * inch
    y1 = y + h - 1.4 * inch
    y2 = y + h - 2.2 * inch

    draw_box(c, x + 0.2 * inch, y0, 1.4 * inch, 0.45 * inch, 'Jenkins')
    draw_box(c, x + 2.0 * inch, y0, 1.6 * inch, 0.45 * inch, 'Argo CD')

    draw_box(c, x + 0.2 * inch, y1, 1.4 * inch, 0.45 * inch, 'App Services\n(ecomm)')
    draw_box(c, x + 2.0 * inch, y1, 1.6 * inch, 0.45 * inch, 'Postgres HA\n(db)')

    draw_box(c, x + 4.0 * inch, y1, 1.9 * inch, 0.45 * inch, 'Debezium\n(Kafka Connect)')
    draw_box(c, x + 4.0 * inch, y2, 1.9 * inch, 0.45 * inch, 'Kafka\n(ecomm-streaming)')

    arrow(c, x + 1.6 * inch, y0 + 0.225 * inch, x + 2.0 * inch, y0 + 0.225 * inch)
    arrow(c, x + 2.8 * inch, y0, x + 2.8 * inch, y1 + 0.45 * inch)
    arrow(c, x + 1.6 * inch, y1 + 0.225 * inch, x + 2.0 * inch, y1 + 0.225 * inch)
    arrow(c, x + 3.6 * inch, y1 + 0.225 * inch, x + 4.0 * inch, y1 + 0.225 * inch)
    arrow(c, x + 5.0 * inch, y1, x + 5.0 * inch, y2 + 0.45 * inch)

    return h + 18


def draw_gitops_split_diagram(c, x, y):
    w = 6.5 * inch
    h = 1.6 * inch
    c.setFont('Helvetica-Bold', 10)
    c.drawString(x, y + h + 6, 'GitOps App Split')

    draw_box(c, x + 0.2 * inch, y + 0.8 * inch, 1.8 * inch, 0.45 * inch, 'ecomm-dev')
    draw_box(c, x + 3.0 * inch, y + 0.8 * inch, 2.2 * inch, 0.45 * inch, 'apps/overlays/dev')

    draw_box(c, x + 0.2 * inch, y + 0.1 * inch, 1.8 * inch, 0.45 * inch, 'ecomm-db')
    draw_box(c, x + 3.0 * inch, y + 0.1 * inch, 2.2 * inch, 0.45 * inch, 'apps/overlays/dev-db')

    arrow(c, x + 2.0 * inch, y + 1.0 * inch, x + 3.0 * inch, y + 1.0 * inch)
    arrow(c, x + 2.0 * inch, y + 0.3 * inch, x + 3.0 * inch, y + 0.3 * inch)

    return h + 18


def extract_headings(text):
    headings = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith('## '):
            headings.append(('##', line[3:].strip()))
        elif line.startswith('### '):
            headings.append(('###', line[4:].strip()))
    return headings


def write_toc(c, headings, width, height):
    c.setFont('Helvetica-Bold', 14)
    c.drawString(LEFT, height - TOP_PAD, 'Table of Contents')
    y = height - TOP_PAD - 18
    c.setFont('Helvetica', 9)
    for level, title in headings:
        if y < BOTTOM_PAD:
            c.showPage()
            y = height - TOP_PAD
            c.setFont('Helvetica-Bold', 14)
            c.drawString(LEFT, y, 'Table of Contents (cont.)')
            y -= 18
            c.setFont('Helvetica', 9)
        indent = 0.0 if level == '##' else 0.3
        c.drawString(LEFT + indent * inch, y, f"- {title}")
        y -= LINE_HEIGHT
    c.showPage()


def build_pdf(output_path, include_diagrams):
    text = SRC.read_text()
    headings = extract_headings(text)

    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # TOC page
    write_toc(c, headings, width, height)

    y = height - TOP_PAD

    in_mermaid = False
    mermaid_index = 0

    def new_page():
        c.showPage()
        return height - TOP_PAD

    for raw in text.splitlines():
        if raw.strip().startswith('```mermaid'):
            in_mermaid = True
            mermaid_index += 1
            if include_diagrams:
                needed = 3.6 * inch if mermaid_index == 1 else 2.0 * inch
                if y - needed < BOTTOM_PAD:
                    y = new_page()
                if mermaid_index == 1:
                    y -= draw_architecture_diagram(c, LEFT, y - 3.0 * inch)
                elif mermaid_index == 2:
                    y -= draw_gitops_split_diagram(c, LEFT, y - 1.6 * inch)
            else:
                if y < BOTTOM_PAD + LINE_HEIGHT:
                    y = new_page()
                c.setFont('Helvetica-Oblique', 9)
                c.drawString(LEFT, y, '[Diagram omitted in plain PDF]')
                y -= LINE_HEIGHT
            continue
        if in_mermaid:
            if raw.strip().startswith('```'):
                in_mermaid = False
            continue

        if not raw.strip():
            if y < BOTTOM_PAD + LINE_HEIGHT:
                y = new_page()
            y -= LINE_HEIGHT
            continue

        wrapped = textwrap.wrap(raw, width=DEF_WIDTH, replace_whitespace=False, drop_whitespace=False)
        for line in wrapped:
            if y < BOTTOM_PAD + LINE_HEIGHT:
                y = new_page()
            c.setFont('Helvetica', 9)
            c.drawString(LEFT, y, line)
            y -= LINE_HEIGHT

    c.save()


def main():
    build_pdf(PLAIN_OUT, include_diagrams=False)
    build_pdf(RENDERED_OUT, include_diagrams=True)
    print(PLAIN_OUT)
    print(RENDERED_OUT)


if __name__ == '__main__':
    main()
