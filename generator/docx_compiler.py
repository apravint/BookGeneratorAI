"""
Docx Compiler Engine Module
Compiles Markdown chapters into a print-ready trade interior (.docx): 6x9 trim with mirrored margins,
real heading styles, a live table of contents, running heads and page numbers.
Prints only facts the author supplied. Covers are separate files in commercial publishing.
"""

import os
import glob
import re
from datetime import datetime
import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

BODY_FONT = "Georgia"
TAMIL_FONT = "Noto Serif Tamil"
CODE_FONT = "Consolas"
BODY_SIZE = Pt(11)
BLACK = RGBColor(0, 0, 0)
SCENE_BREAK = re.compile(r'^(\*\s*\*\s*\*|\*{3,}|-{3,}|#)$')


def _is_tamil(language):
    return bool(language) and language.lower() in ["tamil", "ta"]


def set_style_font(style, font_name, size=None, bold=None, italic=None):
    """Sets a font for Latin and complex scripts, clearing theme fonts that would override it."""
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts')
        rpr.insert(0, fonts)
    for attr in list(fonts.attrib):
        del fonts.attrib[attr]
    for slot in ['w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia']:
        fonts.set(qn(slot), font_name)
    style.font.color.rgb = BLACK
    if size:
        style.font.size = size
        cs_size = rpr.find(qn('w:szCs'))
        if cs_size is None:
            cs_size = OxmlElement('w:szCs')
            rpr.find(qn('w:sz')).addnext(cs_size)
        cs_size.set(qn('w:val'), str(int(size.pt * 2)))
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic


def configure_styles(doc, language):
    font = TAMIL_FONT if _is_tamil(language) else BODY_FONT

    normal = doc.styles['Normal']
    set_style_font(normal, font, BODY_SIZE)
    normal.paragraph_format.line_spacing = 1.2
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.widow_control = True

    for name, size, before, after, align in [
        ('Heading 1', Pt(20), Pt(180), Pt(0), WD_ALIGN_PARAGRAPH.CENTER),
        ('Heading 2', Pt(16), Pt(72), Pt(30), WD_ALIGN_PARAGRAPH.CENTER),
        ('Heading 3', Pt(12), Pt(16), Pt(8), WD_ALIGN_PARAGRAPH.LEFT),
        ('Heading 4', Pt(11), Pt(12), Pt(6), WD_ALIGN_PARAGRAPH.LEFT),
    ]:
        style = doc.styles[name]
        set_style_font(style, font, size, bold=True)
        style.paragraph_format.space_before = before
        style.paragraph_format.space_after = after
        style.paragraph_format.alignment = align
        style.paragraph_format.keep_with_next = True


def configure_page(section):
    section.page_width = Inches(6)
    section.page_height = Inches(9)
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.875)   # inside margin once mirrored, safe for up to ~700 pages
    section.right_margin = Inches(0.5)
    section.header_distance = Inches(0.4)
    section.footer_distance = Inches(0.4)


def add_field(paragraph, instruction, cached_text=""):
    for kind, text in [('begin', None), (None, instruction), ('separate', None), ('result', cached_text), ('end', None)]:
        run = paragraph.add_run()
        if kind in ('begin', 'separate', 'end'):
            fld = OxmlElement('w:fldChar')
            fld.set(qn('w:fldCharType'), kind)
            run._r.append(fld)
        elif kind == 'result':
            run.text = text
        else:
            instr = OxmlElement('w:instrText')
            instr.set(qn('xml:space'), 'preserve')
            instr.text = f" {text} "
            run._r.append(instr)


def process_inline_formatting(paragraph, text, language="english"):
    tokens = re.split(r'(\*\*.+?\*\*|\*[^*\s](?:.*?[^*\s])?\*|`.+?`)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) > 4:
            paragraph.add_run(token[2:-2]).bold = True
        elif token.startswith('*') and token.endswith('*') and len(token) > 2:
            paragraph.add_run(token[1:-1]).italic = True
        elif token.startswith('`') and token.endswith('`') and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = CODE_FONT
            run.font.size = Pt(9.5)
        else:
            paragraph.add_run(token)


def add_code_block(doc, code_text):
    for line in code_text.rstrip().split('\n'):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.line_spacing = 1.1
        run = p.add_run(line)
        run.font.name = CODE_FONT
        run.font.size = Pt(9)
    doc.add_paragraph()


def add_quote(doc, quote_text, language):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.right_indent = Inches(0.35)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    process_inline_formatting(p, quote_text, language)
    for run in p.runs:
        run.italic = True


def render_table(doc, rows, language="english"):
    if not rows:
        return
    num_cols = max(len(row) for row in rows)
    table = doc.add_table(rows=len(rows), cols=num_cols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            p = table.cell(row_idx, col_idx).paragraphs[0]
            process_inline_formatting(p, value, language)
            for run in p.runs:
                run.font.size = Pt(9.5)
                if row_idx == 0:
                    run.bold = True
    doc.add_paragraph()


def start_body_section(doc):
    """Each part or chapter is its own section so its opening page can drop the running head."""
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.different_first_page_header_footer = True
    return section


def parse_markdown_file(doc, filepath, language="english", new_sections=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')

    in_code = False
    code_lines = []
    table_rows = []
    indent_next = False
    first_heading = True

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            if in_code:
                add_code_block(doc, '\n'.join(code_lines))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue

        if stripped.startswith('|') and stripped.count('|') >= 2:
            if not re.match(r'^\|?[\s:|-]+\|?$', stripped):
                table_rows.append([c.strip() for c in stripped.strip('|').split('|')])
            continue
        if table_rows:
            render_table(doc, table_rows, language)
            table_rows = []
            indent_next = False

        if not stripped:
            continue

        heading = re.match(r'^(#{1,4})\s+(.*)$', stripped)
        if heading:
            level = len(heading.group(1))
            if level <= 2 and new_sections:
                start_body_section(doc)
            elif level <= 2 and not first_heading:
                doc.add_page_break()
            first_heading = False
            doc.add_heading(heading.group(2), level=level)
            indent_next = False
        elif SCENE_BREAK.match(stripped):
            p = doc.add_paragraph('*  *  *')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(12)
            indent_next = False
        elif stripped.startswith('>'):
            add_quote(doc, stripped.lstrip('> ').strip(), language)
            indent_next = False
        elif re.match(r'^[-*]\s', stripped):
            process_inline_formatting(doc.add_paragraph(style='List Bullet'), stripped[2:], language)
            indent_next = False
        elif re.match(r'^\d+\.\s', stripped):
            process_inline_formatting(doc.add_paragraph(style='List Number'), re.sub(r'^\d+\.\s', '', stripped), language)
            indent_next = False
        else:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if indent_next:
                p.paragraph_format.first_line_indent = Inches(0.25)
            process_inline_formatting(p, stripped, language)
            indent_next = True

    if table_rows:
        render_table(doc, table_rows, language)


def centered(doc, text, size=None, bold=False, before=0, after=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    run = p.add_run(text)
    run.bold = bold
    if size:
        run.font.size = Pt(size)
    return p


def build_title_page(doc, title, author, metadata):
    centered(doc, title, size=26, bold=True, before=130, after=8)
    if metadata.get("subtitle"):
        centered(doc, metadata["subtitle"], size=13, after=8)
    centered(doc, author, size=14, before=30)
    if metadata.get("publisher"):
        centered(doc, metadata["publisher"], size=10, before=170)
    doc.add_page_break()


def copyright_lines(title, author, language, metadata):
    year = metadata.get("year") or datetime.now().year
    lines = []
    if _is_tamil(language):
        lines.append(f"காப்புரிமை © {year} {author}. அனைத்து உரிமைகளும் பாதுகாக்கப்பட்டவை.")
        if metadata.get("is_fiction"):
            lines.append("இது ஒரு கற்பனைப் படைப்பு. பெயர்கள், பாத்திரங்கள், நிகழ்வுகள் அனைத்தும் கற்பனையே.")
    else:
        lines.append(f"Copyright © {year} {author}. All rights reserved.")
        lines.append("No part of this book may be reproduced without written permission from the copyright holder, except for brief quotations in reviews.")
        if metadata.get("is_fiction"):
            lines.append("This is a work of fiction. Names, characters, places and events are products of the author's imagination or are used fictitiously. Any resemblance to actual persons or events is coincidental.")
    if metadata.get("isbn"):
        lines.append(f"ISBN: {metadata['isbn']}")
    if metadata.get("publisher"):
        lines.append(metadata["publisher"])
    return lines


def build_copyright_page(doc, title, author, language, metadata):
    for index, line in enumerate(copyright_lines(title, author, language, metadata)):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(280 if index == 0 else 0)
        p.paragraph_format.space_after = Pt(6)
        p.add_run(line).font.size = Pt(8.5)
    doc.add_page_break()


def insert_setting(doc, element, before):
    """Word rejects settings.xml children that are out of schema order."""
    settings = doc.settings.element
    for child in settings:
        if child.tag in {qn(name) for name in before}:
            child.addprevious(element)
            return
    settings.append(element)


def chapter_files(chapters_dir):
    return sorted(glob.glob(os.path.join(chapters_dir, "chapter_*.md")))


def build_toc(doc, chapters_dir, language):
    doc.add_heading("பொருளடக்கம்" if _is_tamil(language) else "Contents", level=2)
    # Exclude this page's own heading from the field by applying it as a plain paragraph style
    doc.paragraphs[-1].style = doc.styles['Normal']
    title_run = doc.paragraphs[-1].runs[0]
    title_run.bold = True
    title_run.font.size = Pt(16)
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_after = Pt(20)

    entries = []
    for path in chapter_files(chapters_dir):
        with open(path, encoding='utf-8') as f:
            entries += [m.group(1) for m in re.finditer(r'^#{1,2}\s+(.*)$', f.read(), re.MULTILINE)]

    # Word refreshes this field (and adds page numbers) on open; other readers show the cached list
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-2" \\h \\z \\u', cached_text=entries[0] if entries else "")
    for entry in entries[1:]:
        doc.add_paragraph(entry)
    update = OxmlElement('w:updateFields')
    update.set(qn('w:val'), 'true')
    insert_setting(doc, update, before=('w:hdrShapeDefaults', 'w:footnotePr', 'w:endnotePr', 'w:compat', 'w:docVars', 'w:rsids', 'w:themeFontLang', 'w:clrSchemeMapping', 'w:shapeDefaults', 'w:decimalSymbol', 'w:listSeparator'))


def configure_running_heads(section, title, author):
    section.different_first_page_header_footer = True
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    section.even_page_header.is_linked_to_previous = False
    section.even_page_footer.is_linked_to_previous = False

    for container, align, text in [
        (section.header, WD_ALIGN_PARAGRAPH.RIGHT, title),
        (section.even_page_header, WD_ALIGN_PARAGRAPH.LEFT, author),
    ]:
        p = container.paragraphs[0]
        p.alignment = align
        p.add_run(text).font.size = Pt(8.5)

    for container, align in [
        (section.footer, WD_ALIGN_PARAGRAPH.RIGHT),
        (section.even_page_footer, WD_ALIGN_PARAGRAPH.LEFT),
        (section.first_page_footer, WD_ALIGN_PARAGRAPH.CENTER),
    ]:
        p = container.paragraphs[0]
        p.alignment = align
        add_field(p, 'PAGE', '1')
        for run in p.runs:
            run.font.size = Pt(9)



def restart_page_numbers(section):
    """Page 1 is the first body page; later sections continue the count."""
    pg_num = OxmlElement('w:pgNumType')
    pg_num.set(qn('w:start'), '1')
    margins = section._sectPr.find(qn('w:pgMar'))
    margins.addnext(pg_num)


def compile_book(title: str, domain: str, author: str, chapters_dir: str, output_path: str, language: str = "english", metadata: dict = None):
    metadata = metadata or {}
    doc = docx.Document()
    configure_styles(doc, language)
    doc.settings.odd_and_even_pages_header_footer = True
    insert_setting(doc, OxmlElement('w:mirrorMargins'), before=(
        'w:alignBordersAndEdges', 'w:bordersDoNotSurroundHeader', 'w:bordersDoNotSurroundFooter', 'w:gutterAtTop',
        'w:hideSpellingErrors', 'w:hideGrammaticalErrors', 'w:activeWritingStyle', 'w:proofState', 'w:formsDesign',
        'w:attachedTemplate', 'w:linkStyles', 'w:stylePaneFormatFilter', 'w:stylePaneSortMethod', 'w:documentType',
        'w:mailMerge', 'w:revisionView', 'w:trackRevisions', 'w:defaultTabStop', 'w:autoHyphenation', 'w:evenAndOddHeaders',
        'w:characterSpacingControl', 'w:compat', 'w:rsids'
    ))
    configure_page(doc.sections[0])

    build_title_page(doc, title, author, metadata)
    build_copyright_page(doc, title, author, language, metadata)

    if metadata.get("dedication"):
        centered(doc, metadata["dedication"], before=150)
        doc.add_page_break()

    # Praise appears only if the author placed real, permissioned quotes in praise.md
    praise_path = os.path.join(chapters_dir, "praise.md")
    if os.path.exists(praise_path):
        parse_markdown_file(doc, praise_path, language=language)
        doc.add_page_break()

    build_toc(doc, chapters_dir, language)

    files = chapter_files(chapters_dir)
    for index, chap_path in enumerate(files):
        print(f"Compiling {os.path.basename(chap_path)}...")
        parse_markdown_file(doc, chap_path, language=language, new_sections=True)
        if index == 0 and len(doc.sections) > 1:
            configure_running_heads(doc.sections[1], title, author)
            # Set only now: add_section clones the previous section, which would restart numbering at every chapter
    if len(doc.sections) > 1:
        restart_page_numbers(doc.sections[1])

    if metadata.get("author_bio"):
        start_body_section(doc)
        doc.add_heading("ஆசிரியர் பற்றி" if _is_tamil(language) else "About the Author", level=2)
        p = doc.add_paragraph(metadata["author_bio"])
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc.save(output_path)
    print(f"\nSuccessfully compiled manuscript to: {output_path}")


def compile_book_to_docx(book_data, output_path: str, language: str = "english"):
    """
    Compatibility wrapper to compile a book dictionary or file directory to DOCX.
    Supports book_data as a dictionary of chapters or as a directory path containing markdown files.
    """
    if isinstance(book_data, dict):
        metadata = book_data.get("metadata", {})
        title = metadata.get("title", "Untitled Book")
        author = metadata.get("author", "Author")
        chapters = book_data.get("chapters", [])
        lang = metadata.get("language", language)

        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            for idx, ch in enumerate(chapters, 1):
                c_num = ch.get("chapter_number", idx)
                c_title = ch.get("title", f"Chapter {c_num}")
                c_content = ch.get("content", "")
                md_path = os.path.join(temp_dir, f"chapter_{c_num:02d}.md")
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(c_content if c_content.startswith("#") else f"## Chapter {c_num}: {c_title}\n\n{c_content}")

            compile_book(
                title=title,
                domain=metadata.get("genre", title),
                author=author,
                chapters_dir=temp_dir,
                output_path=output_path,
                language=lang
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif isinstance(book_data, str) and os.path.isdir(book_data):
        compile_book(
            title="Book",
            domain="General",
            author="Author",
            chapters_dir=book_data,
            output_path=output_path,
            language=language
        )
    else:
        raise ValueError(f"Unsupported book_data format: {type(book_data)}")
