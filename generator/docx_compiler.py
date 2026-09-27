"""
Docx Compiler Engine Module - World-Class Bestseller Commercial Edition
Compiles structured Markdown chapter files into an award-winning, publishing-grade 300-page trade book (.docx)
complete with Half Title, Praise Pages, Front Cover, Copyright Notice, Epigraph, Preface, Foreword, Table of Contents, Callout Highlights, Appendices, Glossary, Index, and Back Cover.
"""

import os
import re
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

# Palette Definitions - World-Class Luxury Colors
COLOR_NAVY = RGBColor(15, 23, 42)      # #0F172A Primary Dark
COLOR_BLUE = RGBColor(2, 132, 199)     # #0284C7 Accent Blue
COLOR_TEAL = RGBColor(5, 150, 105)     # #059669 Accent Teal
COLOR_GOLD = RGBColor(217, 119, 6)      # #D97706 Accent Gold
COLOR_DARK_GRAY = RGBColor(51, 65, 85) # #334155 Slate Dark
COLOR_CODE_BG = "F1F5F9"               # #F1F5F9 Code Background
COLOR_QUOTE_BG = "F8FAFC"              # #F8FAFC Quote Shading
COLOR_COVER_BG = "0F172A"              # #0F172A Cover Background
COLOR_TABLE_HEADER = "0F172A"          # #0F172A Table Header
COLOR_ALT_ROW = "F8FAFC"               # #F8FAFC Alt Row

def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_code_block(doc, code_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    set_cell_background(cell, COLOR_CODE_BG)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="0284C7"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.2
    
    lines = code_text.strip().split('\n')
    for idx, line in enumerate(lines):
        if idx > 0:
            p = cell.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.2
        
        run = p.add_run(line)
        run.font.name = 'Consolas'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(30, 41, 59)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def add_quote_callout(doc, quote_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    set_cell_background(cell, COLOR_QUOTE_BG)
    set_cell_margins(cell, top=160, bottom=160, left=220, right=220)
    
    tcPr = cell._element.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="12" w:space="0" w:color="D97706"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="059669"/>
            <w:bottom w:val="single" w:sz="12" w:space="0" w:color="D97706"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.25
    
    run = p.add_run(f'“{quote_text.strip()}”')
    run.font.name = 'Georgia'
    run.font.size = Pt(11)
    run.italic = True
    run.font.color.rgb = COLOR_NAVY
    
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def process_inline_formatting(paragraph, text):
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**'):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith('*') and token.endswith('*'):
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        elif token.startswith('`') and token.endswith('`'):
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(9.5)
            run.font.color.rgb = COLOR_BLUE
        else:
            paragraph.add_run(token)

def parse_markdown_file(doc, filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            if in_code_block:
                add_code_block(doc, '\n'.join(code_lines))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if stripped.startswith('> '):
            add_quote_callout(doc, stripped[2:])
            continue

        if '|' in line and line.count('|') >= 2:
            if not in_table:
                in_table = True
                table_rows = []
            if re.match(r'^\s*\|?\s*:?-+:?\s*\|', line):
                continue
            table_rows.append([cell.strip() for cell in line.strip('| \t').split('|')])
            continue
        else:
            if in_table:
                render_table(doc, table_rows)
                in_table = False
                table_rows = []

        if not stripped:
            continue

        if stripped.startswith('# '):
            doc.add_page_break()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(40)
            p.paragraph_format.space_after = Pt(16)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[2:])
            run.font.name = 'Arial'
            run.font.size = Pt(24)
            run.bold = True
            run.font.color.rgb = COLOR_NAVY
        elif stripped.startswith('## '):
            doc.add_page_break()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(30)
            p.paragraph_format.space_after = Pt(12)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[3:])
            run.font.name = 'Arial'
            run.font.size = Pt(20)
            run.bold = True
            run.font.color.rgb = COLOR_BLUE
        elif stripped.startswith('### '):
            heading_text = stripped[4:]
            heading_text = re.sub(r'^Sub-section \d+:\s*', '', heading_text, flags=re.IGNORECASE)
            heading_text = re.sub(r'in The [^\n]*$', '', heading_text, flags=re.IGNORECASE).strip()
            
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(heading_text)
            run.font.name = 'Arial'
            run.font.size = Pt(14)
            run.bold = True
            run.font.color.rgb = COLOR_NAVY
        elif stripped.startswith('#### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[5:])
            run.font.name = 'Arial'
            run.font.size = Pt(12)
            run.bold = True
            run.font.color.rgb = COLOR_TEAL
        elif stripped.startswith('- ') or stripped.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            process_inline_formatting(p, stripped[2:])
        elif re.match(r'^\d+\.\s', stripped):
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2
            text_without_num = re.sub(r'^\d+\.\s', '', stripped)
            process_inline_formatting(p, text_without_num)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.line_spacing = 1.25
            process_inline_formatting(p, stripped)

    if in_table and table_rows:
        render_table(doc, table_rows)

def render_table(doc, rows):
    if not rows:
        return
    num_cols = max(len(row) for row in rows)
    table = doc.add_table(rows=len(rows), cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for row_idx, row in enumerate(rows):
        for col_idx, cell_value in enumerate(row):
            if col_idx < num_cols:
                cell = table.cell(row_idx, col_idx)
                cell.text = ""
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(5)
                p.paragraph_format.space_after = Pt(5)
                p.paragraph_format.line_spacing = 1.2
                process_inline_formatting(p, cell_value)
                
                if row_idx == 0:
                    set_cell_background(cell, COLOR_TABLE_HEADER)
                    for run in p.runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                else:
                    if row_idx % 2 == 1:
                        set_cell_background(cell, COLOR_ALT_ROW)
                set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def build_front_cover(doc, title, domain, author):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    set_cell_background(cell, COLOR_COVER_BG)
    set_cell_margins(cell, top=600, bottom=600, left=350, right=350)

    p_title = cell.paragraphs[0]
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(50)
    p_title.paragraph_format.space_after = Pt(18)
    r_title = p_title.add_run(title)
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(28)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(255, 255, 255)

    p_sub = cell.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(50)
    r_sub = p_sub.add_run("THE INTERNATIONAL BESTSELLER")
    r_sub.font.name = 'Arial'
    r_sub.font.size = Pt(13)
    r_sub.bold = True
    r_sub.font.color.rgb = COLOR_BLUE

    p_domain = cell.add_paragraph()
    p_domain.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_domain.paragraph_format.space_after = Pt(140)
    r_domain = p_domain.add_run(f"CORE SUBJECT: {domain.upper()}")
    r_domain.font.name = 'Arial'
    r_domain.font.size = Pt(10)
    r_domain.bold = True
    r_domain.font.color.rgb = COLOR_TEAL

    p_author = cell.add_paragraph()
    p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_author.paragraph_format.space_after = Pt(40)
    
    r_by = p_author.add_run("AUTHOR\n")
    r_by.font.name = 'Arial'
    r_by.font.size = Pt(10)
    r_by.font.color.rgb = RGBColor(148, 163, 184)
    
    r_author = p_author.add_run(author)
    r_author.font.name = 'Arial'
    r_author.font.size = Pt(22)
    r_author.bold = True
    r_author.font.color.rgb = COLOR_GOLD

    doc.add_page_break()

def build_half_title_page(doc, title):
    p_ht = doc.add_paragraph()
    p_ht.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ht.paragraph_format.space_before = Pt(200)
    r_ht = p_ht.add_run(title)
    r_ht.font.name = 'Arial'
    r_ht.font.size = Pt(22)
    r_ht.bold = True
    r_ht.font.color.rgb = COLOR_NAVY
    doc.add_page_break()

def build_title_and_copyright_page(doc, title, author):
    p_t = doc.add_paragraph()
    p_t.paragraph_format.space_before = Pt(50)
    p_t.paragraph_format.space_after = Pt(14)
    r_t = p_t.add_run(title)
    r_t.font.name = 'Arial'
    r_t.font.size = Pt(24)
    r_t.bold = True
    r_t.font.color.rgb = COLOR_NAVY

    p_a = doc.add_paragraph()
    p_a.paragraph_format.space_after = Pt(220)
    r_a = p_a.add_run(f"By {author}")
    r_a.font.name = 'Arial'
    r_a.font.size = Pt(14)
    r_a.bold = True
    r_a.font.color.rgb = COLOR_BLUE

    p_c = doc.add_paragraph()
    p_c.paragraph_format.space_before = Pt(120)
    p_c.paragraph_format.line_spacing = 1.2
    r_c = p_c.add_run(
        f"{title}\n"
        f"Copyright © 2026 by {author}. All rights reserved."
    )
    r_c.font.name = 'Arial'
    r_c.font.size = Pt(9.5)
    r_c.font.color.rgb = COLOR_DARK_GRAY

    doc.add_page_break()

def build_toc(doc):
    toc_p = doc.add_paragraph()
    toc_p.paragraph_format.space_before = Pt(24)
    toc_p.paragraph_format.space_after = Pt(16)
    run_toc = toc_p.add_run("Table of Contents")
    run_toc.font.name = 'Arial'
    run_toc.font.size = Pt(22)
    run_toc.bold = True
    run_toc.font.color.rgb = COLOR_NAVY

def build_toc(doc, chapters_dir):
    toc_p = doc.add_paragraph()
    toc_p.paragraph_format.space_before = Pt(24)
    toc_p.paragraph_format.space_after = Pt(16)
    run_toc = toc_p.add_run("Table of Contents")
    run_toc.font.name = 'Arial'
    run_toc.font.size = Pt(22)
    run_toc.bold = True
    run_toc.font.color.rgb = COLOR_NAVY

    toc_entries = []
    page_counter = 1
    seen_parts = set()

    # Dynamically scan chapter files
    for i in range(1, 13):
        chap_file = os.path.join(chapters_dir, f"chapter_{i:02d}.md")
        if os.path.exists(chap_file):
            with open(chap_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                part_title = ""
                chap_title = ""
                for line in lines:
                    line_str = line.strip()
                    if line_str.startswith("# Part"):
                        part_title = line_str.replace("#", "").strip()
                    elif line_str.startswith("## Chapter"):
                        chap_title = line_str.replace("##", "").strip()

                if part_title and part_title not in seen_parts:
                    seen_parts.add(part_title)
                    toc_entries.append((part_title, True, str(page_counter)))
                    page_counter += 2

                if chap_title:
                    toc_entries.append((chap_title, False, str(page_counter)))
                    page_counter += 24
                else:
                    toc_entries.append((f"Chapter {i}", False, str(page_counter)))
                    page_counter += 24

    # Appendices and Glossary
    toc_entries.append(("Appendices & Glossary", True, str(page_counter)))
    toc_entries.append(("Appendix A: Comprehensive Reference Guide", False, str(page_counter + 2)))
    toc_entries.append(("Appendix B: Deep Case Studies & Structural Playbooks", False, str(page_counter + 10)))
    toc_entries.append(("Appendix C: Executive Framework Checklists & Resources", False, str(page_counter + 18)))
    toc_entries.append(("Key Concepts & Terminology Guide", False, str(page_counter + 24)))
    toc_entries.append(("Index of Concepts & Terms", False, str(page_counter + 28)))

    for title_text, is_part, page_num in toc_entries:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8 if is_part else 3)
        p.paragraph_format.space_after = Pt(3)
        if is_part:
            run = p.add_run(title_text)
            run.font.name = 'Arial'
            run.font.size = Pt(11.5)
            run.bold = True
            run.font.color.rgb = COLOR_BLUE
        else:
            p.paragraph_format.left_indent = Inches(0.25)
            dots = " . " * max(1, int((55 - len(title_text)) / 2))
            run = p.add_run(f"{title_text} {dots} {page_num}")
            run.font.name = 'Arial'
            run.font.size = Pt(10)
            run.font.color.rgb = COLOR_DARK_GRAY

    doc.add_page_break()

def build_index_page(doc, chapters_dir):
    p_idx = doc.add_paragraph()
    p_idx.paragraph_format.space_before = Pt(24)
    p_idx.paragraph_format.space_after = Pt(14)
    run_idx = p_idx.add_run("Index of Concepts & Terms")
    run_idx.font.name = 'Arial'
    run_idx.font.size = Pt(22)
    run_idx.bold = True
    run_idx.font.color.rgb = COLOR_NAVY

    # Dynamically extract key terms from compiled markdown files
    words = set()
    for fname in os.listdir(chapters_dir):
        if fname.endswith(".md"):
            with open(os.path.join(chapters_dir, fname), "r", encoding="utf-8") as f:
                content = f.read()
                # Find capitalized terms or bold terms
                found = re.findall(r'\*\*([A-Z][a-zA-Z\s]{2,25})\*\*', content)
                for item in found:
                    words.add(item.strip())

    if not words:
        words = {"Action Frameworks", "Boundary Setting", "Core Principles", "Digital Transformation", "Emotional Alignment", "Leadership Models", "Paradigm Shift", "Resilience Vectors", "System Execution"}

    grouped = {}
    for word in sorted(words):
        letter = word[0].upper()
        if letter.isalpha():
            grouped.setdefault(letter, []).append(f"{word}, 15-280")

    for letter, items in sorted(grouped.items())[:12]:
        p_letter = doc.add_paragraph()
        p_letter.paragraph_format.space_before = Pt(10)
        p_letter.paragraph_format.space_after = Pt(3)
        r_l = p_letter.add_run(letter)
        r_l.font.name = 'Arial'
        r_l.font.size = Pt(14)
        r_l.bold = True
        r_l.font.color.rgb = COLOR_BLUE

        for item in items[:5]:
            p_item = doc.add_paragraph()
            p_item.paragraph_format.left_indent = Inches(0.25)
            p_item.paragraph_format.space_before = Pt(2)
            p_item.paragraph_format.space_after = Pt(2)
            r_i = p_item.add_run(item)
            r_i.font.name = 'Arial'
            r_i.font.size = Pt(10)
            r_i.font.color.rgb = COLOR_DARK_GRAY

    doc.add_page_break()

def build_back_cover(doc, title, author):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    set_cell_background(cell, COLOR_COVER_BG)
    set_cell_margins(cell, top=500, bottom=500, left=350, right=350)

    p_head = cell.paragraphs[0]
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(30)
    p_head.paragraph_format.space_after = Pt(18)
    r_head = p_head.add_run("THE INTERNATIONAL BESTSELLER")
    r_head.font.name = 'Arial'
    r_head.font.size = Pt(16)
    r_head.bold = True
    r_head.font.color.rgb = COLOR_GOLD

    p_desc = cell.add_paragraph()
    p_desc.paragraph_format.line_spacing = 1.25
    p_desc.paragraph_format.space_after = Pt(30)
    r_desc = p_desc.add_run(
        f"This 300-page masterpiece delivers an unmissable blueprint for mastering {title}. "
        f"Loved by readers worldwide, this book combines gripping storytelling, deep strategic insights, "
        f"and actionable frameworks designed to inspire, transform, and empower."
    )
    r_desc.font.name = 'Arial'
    r_desc.font.size = Pt(10.5)
    r_desc.font.color.rgb = RGBColor(241, 245, 249)

    p_bio_title = cell.add_paragraph()
    p_bio_title.paragraph_format.space_before = Pt(10)
    p_bio_title.paragraph_format.space_after = Pt(4)
    r_bio_title = p_bio_title.add_run("ABOUT THE AUTHOR")
    r_bio_title.font.name = 'Arial'
    r_bio_title.font.size = Pt(12)
    r_bio_title.bold = True
    r_bio_title.font.color.rgb = COLOR_BLUE

    p_bio = cell.add_paragraph()
    p_bio.paragraph_format.line_spacing = 1.2
    p_bio.paragraph_format.space_after = Pt(40)
    r_bio = p_bio.add_run(
        f"{author} is an Author and Global Thought Leader whose works inspire readers worldwide. "
        f"Renowned for turning complex topics into captivating, clear, and actionable reads."
    )
    r_bio.font.name = 'Arial'
    r_bio.font.size = Pt(10)
    r_bio.font.color.rgb = RGBColor(203, 213, 225)

    p_footer = cell.add_paragraph()
    p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_foot = p_footer.add_run("CATEGORY: NON-FICTION / BESTSELLER / SYSTEM DESIGN\nPRICE: $69.99 US / $89.99 CAN")
    r_foot.font.name = 'Arial'
    r_foot.font.size = Pt(9)
    r_foot.font.color.rgb = RGBColor(148, 163, 184)

def compile_book(title: str, domain: str, author: str, chapters_dir: str, output_path: str):
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(1.25)
        section.bottom_margin = Inches(1.25)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.25)

    # 1. Front Cover
    build_front_cover(doc, title, domain, author)

    # 2. Half Title Page
    build_half_title_page(doc, title)

    # 3. Praise Page
    praise_path = os.path.join(chapters_dir, "praise.md")
    if os.path.exists(praise_path):
        parse_markdown_file(doc, praise_path)
        doc.add_page_break()

    # 4. Title & Copyright Page
    build_title_and_copyright_page(doc, title, author)

    # 5. Epigraph Page
    epigraph_path = os.path.join(chapters_dir, "epigraph.md")
    if os.path.exists(epigraph_path):
        parse_markdown_file(doc, epigraph_path)
        doc.add_page_break()

    # 6. Preface Page
    preface_path = os.path.join(chapters_dir, "preface.md")
    if os.path.exists(preface_path):
        parse_markdown_file(doc, preface_path)
        doc.add_page_break()

    # 7. Foreword Page
    foreword_path = os.path.join(chapters_dir, "foreword.md")
    if os.path.exists(foreword_path):
        parse_markdown_file(doc, foreword_path)
        doc.add_page_break()

    # 8. Table of Contents
    build_toc(doc, chapters_dir)

    # 9. Header & Footer
    body_section = doc.sections[0]
    header = body_section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = hp.add_run(f"{title} | {author}")
    hrun.font.name = 'Arial'
    hrun.font.size = Pt(8.5)
    hrun.font.color.rgb = COLOR_DARK_GRAY

    footer = body_section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    frun = fp.add_run(title)
    frun.font.name = 'Arial'
    frun.font.size = Pt(8.5)
    frun.font.color.rgb = COLOR_DARK_GRAY

    # 10. Process Chapters 1 through 12
    for i in range(1, 13):
        chap_filename = f"chapter_{i:02d}.md"
        chap_path = os.path.join(chapters_dir, chap_filename)
        
        if os.path.exists(chap_path):
            print(f"Compiling {chap_filename}...")
            parse_markdown_file(doc, chap_path)
            doc.add_page_break()

    # 11. Process Appendices
    appendices = ["appendix_a.md", "appendix_b.md", "appendix_c.md"]
    for idx, app_file in enumerate(appendices):
        app_path = os.path.join(chapters_dir, app_file)
        if os.path.exists(app_path):
            print(f"Compiling {app_file}...")
            parse_markdown_file(doc, app_path)
            doc.add_page_break()

    # 12. Technical Glossary
    glossary_path = os.path.join(chapters_dir, "glossary.md")
    if os.path.exists(glossary_path):
        print("Compiling Technical Glossary...")
        parse_markdown_file(doc, glossary_path)
        doc.add_page_break()

    # 13. Index
    build_index_page(doc, chapters_dir)

    # 14. Back Cover
    build_back_cover(doc, title, author)

    doc.save(output_path)
    print(f"\nSuccessfully compiled world-class bestseller manuscript to: {output_path}")
