"""
EPUB 3 Compiler Engine Module - World-Class Digital Edition
Compiles structured Markdown chapter files into a validated, commercial-grade EPUB 3 (.epub)
complete with responsive typography, drop caps, Table of Contents, and reading spine.
"""

import os
import re
import glob
import uuid
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from generator.docx_compiler import copyright_lines


CSS_CONTENT = """
@charset "utf-8";
body { font-family: Georgia, "Noto Serif", "Noto Serif Tamil", serif; line-height: 1.5; margin: 0 5%; }
h1, h2, h3, h4 { font-weight: bold; line-height: 1.25; }
h1.part-title { font-size: 1.8em; text-align: center; margin-top: 30%; page-break-before: always; }
h1.book-title { font-size: 2.2em; text-align: center; margin-top: 25%; margin-bottom: 0.2em; }
p.author-name { font-size: 1.2em; text-align: center; margin-bottom: 30%; }
h2.chapter-title { font-size: 1.5em; text-align: center; margin: 2em 0 1.5em; page-break-before: always; }
h3.section-heading { font-size: 1.15em; margin: 1.5em 0 0.5em; }
p { margin: 0; text-indent: 1.3em; text-align: justify; }
p.lead { text-indent: 0; }
p.lead::first-letter { font-size: 2.8em; float: left; margin: 0.05em 0.1em 0 0; line-height: 0.85; font-weight: bold; }
p.front { text-indent: 0; font-size: 0.85em; margin-bottom: 0.8em; }
p.dedication { text-indent: 0; text-align: center; margin-top: 30%; font-style: italic; }
blockquote { margin: 1em 1.5em; font-style: italic; }
blockquote p { text-indent: 0; }
hr.scene { border: 0; margin: 1.2em 0; text-align: center; }
hr.scene::after { content: "* * *"; }
pre { font-size: 0.85em; white-space: pre-wrap; margin: 1em 0; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; }
td, th { border: 1px solid #888; padding: 0.3em; text-align: left; }
ul, ol { margin: 0.7em 0; }
"""


def _inline(text: str) -> str:
    html = escape(text)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*([^*\s](?:.*?[^*\s])?)\*', r'<em>\1</em>', html)
    return re.sub(r'`(.+?)`', r'<code>\1</code>', html)


def markdown_to_xhtml(md_text: str) -> str:
    """Converts Markdown to clean XHTML: headings, scene breaks, quotes, lists, tables and code."""
    out = []
    open_block = None
    table_rows = []
    in_code = False
    code_lines = []
    lead = True

    def close_block():
        nonlocal open_block
        if open_block:
            out.append(f"</{open_block}>")
            open_block = None

    def flush_table():
        if not table_rows:
            return
        out.append("<table>")
        for index, row in enumerate(table_rows):
            tag = "th" if index == 0 else "td"
            out.append("<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in row) + "</tr>")
        out.append("</table>")
        table_rows.clear()

    def in_block(tag):
        nonlocal open_block
        if open_block != tag:
            close_block()
            out.append(f"<{tag}>")
            open_block = tag

    for line in md_text.split('\n'):
        s = line.strip()
        if s.startswith('```'):
            if in_code:
                out.append("<pre>" + escape("\n".join(code_lines)) + "</pre>")
                code_lines = []
            else:
                close_block()
                flush_table()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if s.startswith('|') and s.count('|') >= 2:
            close_block()
            if not re.match(r'^\|?[\s:|-]+\|?$', s):
                table_rows.append([c.strip() for c in s.strip('|').split('|')])
            continue
        flush_table()
        if not s:
            close_block()
            continue

        if s.startswith('### ') or s.startswith('#### '):
            close_block()
            out.append(f'<h3 class="section-heading">{_inline(s.lstrip("#").strip())}</h3>')
            lead = True
        elif s.startswith('## '):
            close_block()
            out.append(f'<h2 class="chapter-title">{_inline(s[3:])}</h2>')
            lead = True
        elif s.startswith('# '):
            close_block()
            out.append(f'<h1 class="part-title">{_inline(s[2:])}</h1>')
            lead = True
        elif re.match(r'^(\*\s*\*\s*\*|\*{3,}|-{3,})$', s):
            close_block()
            out.append('<hr class="scene" />')
            lead = True
        elif s.startswith('>'):
            in_block("blockquote")
            out.append(f"<p>{_inline(s.lstrip('> ').strip())}</p>")
        elif re.match(r'^[-*]\s', s):
            in_block("ul")
            out.append(f"<li>{_inline(s[2:])}</li>")
        elif re.match(r'^\d+\.\s', s):
            in_block("ol")
            out.append(f"<li>{_inline(re.sub(r'^[0-9]+[.][ ]', '', s))}</li>")
        else:
            close_block()
            css_class = ' class="lead"' if lead else ''
            out.append(f'<p{css_class}>{_inline(s)}</p>')
            lead = False

    close_block()
    flush_table()
    return "\n".join(out)


def compile_epub(
    title: str,
    author: str,
    chapters_dir: str,
    output_path: str,
    language: str = "english",
    cover_image_path: str = None,
    metadata: dict = None
) -> str:
    """Compiles markdown chapter files into a validated EPUB 3 document."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    lang_code = "ta" if language.lower() in ["tamil", "ta"] else "en"
    metadata = metadata or {}
    # Stable across rebuilds so retailers and readers see updates to one book
    book_uuid = f"urn:isbn:{metadata['isbn']}" if metadata.get("isbn") else f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, title + '|' + author)}"
    mod_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Use only this book's own cover; never pick up an image belonging to another book
    resolved_cover = cover_image_path
    if not resolved_cover:
        candidate = os.path.join(chapters_dir, "cover.jpg")
        if os.path.exists(candidate):
            resolved_cover = candidate

    # Discover and sort Markdown files
    # Author-supplied front matter only; praise.md must hold real, permissioned quotes
    front_matter_order = ["praise.md"]
    md_files = []
    for fm in front_matter_order:
        p = os.path.join(chapters_dir, fm)
        if os.path.exists(p):
            md_files.append((fm.replace(".md", ""), p))

    chap_files = sorted(glob.glob(os.path.join(chapters_dir, "chapter_*.md")))
    for cf in chap_files:
        base = os.path.splitext(os.path.basename(cf))[0]
        md_files.append((base, cf))

    # Build sections
    manifest_items = []
    spine_items = []
    nav_toc_items = []
    section_contents = {}

    # Title / Cover Page
    if resolved_cover and os.path.exists(resolved_cover):
        manifest_items.append('<item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>')
        title_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang_code}" lang="{lang_code}">
<head>
    <title>{escape(title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body style="margin: 0; padding: 0; text-align: center;">
    <div style="text-align: center; margin: 0; padding: 0;">
        <img src="cover.jpg" alt="{escape(title, {'"': '&quot;'})}" style="max-width: 100%; height: auto; max-height: 100vh; object-fit: contain;" />
    </div>
</body>
</html>"""
    else:
        title_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang_code}" lang="{lang_code}">
<head>
    <title>{escape(title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
    <h1 class="book-title">{escape(title)}</h1>
    <p class="author-name">{escape(author)}</p>
</body>
</html>"""
    section_contents["titlepage.xhtml"] = title_html
    manifest_items.append('<item id="titlepage" href="titlepage.xhtml" media-type="application/xhtml+xml"/>')
    spine_items.append('<itemref idref="titlepage"/>')

    def add_page(page_id, page_title, body):
        section_contents[f"{page_id}.xhtml"] = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang_code}" lang="{lang_code}">
<head>
    <title>{escape(page_title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
{body}
</body>
</html>"""
        manifest_items.append(f'<item id="{page_id}" href="{page_id}.xhtml" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="{page_id}"/>')

    legal = "".join(f'<p class="front">{escape(line)}</p>' for line in copyright_lines(title, author, language, metadata))
    add_page("copyright", "Copyright", legal)
    if metadata.get("dedication"):
        add_page("dedication", "Dedication", f'<p class="dedication">{escape(metadata["dedication"])}</p>')

    # Convert sections
    for idx, (section_id, file_path) in enumerate(md_files, start=1):
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        html_body = markdown_to_xhtml(raw_text)
        heading_match = re.search(r'^##\s+(.*)$', raw_text, re.MULTILINE) or re.search(r'^#+\s*(.*)$', raw_text, re.MULTILINE)
        section_title = heading_match.group(1).strip() if heading_match else section_id.replace("_", " ").title()

        filename = f"{section_id}.xhtml"
        xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang_code}" lang="{lang_code}">
<head>
    <title>{escape(section_title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
{html_body}
</body>
</html>"""
        section_contents[filename] = xhtml
        manifest_items.append(f'<item id="{section_id}" href="{filename}" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="{section_id}"/>')
        nav_toc_items.append(f'<li><a href="{filename}">{escape(section_title)}</a></li>')

    if metadata.get("author_bio"):
        about = "ஆசிரியர் பற்றி" if lang_code == "ta" else "About the Author"
        add_page("about", about, f'<h2 class="chapter-title">{escape(about)}</h2><p class="lead">{escape(metadata["author_bio"])}</p>')
        nav_toc_items.append(f'<li><a href="about.xhtml">{escape(about)}</a></li>')

    # EPUB 3 Navigation Document (nav.xhtml)
    nav_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang_code}" lang="{lang_code}">
<head>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h2>Contents</h2>
        <ol>
            {"".join(nav_toc_items)}
        </ol>
    </nav>
</body>
</html>"""
    section_contents["nav.xhtml"] = nav_html
    manifest_items.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')

    # Stylesheet
    manifest_items.append('<item id="css" href="style.css" media-type="text/css"/>')

    cover_meta = '<meta name="cover" content="cover-image"/>' if (resolved_cover and os.path.exists(resolved_cover)) else ''

    optional_meta = ""
    if metadata.get("publisher"):
        optional_meta += f"<dc:publisher>{escape(metadata['publisher'])}</dc:publisher>"
    if metadata.get("description"):
        optional_meta += f"<dc:description>{escape(metadata['description'])}</dc:description>"
    # Backslashes are not allowed inside f-string expressions before Python 3.12
    manifest_xml = "\n        ".join(manifest_items)
    spine_xml = "\n        ".join(spine_items)

    # OEBPS/content.opf
    content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{escape(title)}</dc:title>
        <dc:creator>{escape(author)}</dc:creator>
        <dc:language>{lang_code}</dc:language>
        <dc:identifier id="BookID">{book_uuid}</dc:identifier>
        <meta property="dcterms:modified">{mod_time}</meta>
        {cover_meta}
        {optional_meta}
    </metadata>
    <manifest>
        {manifest_xml}
    </manifest>
    <spine>
        {spine_xml}
    </spine>
</package>"""

    # META-INF/container.xml
    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""

    # Pack into EPUB zip archive
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as ep:
        # Mimetype must be first, uncompressed
        ep.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        ep.writestr("META-INF/container.xml", container_xml)
        ep.writestr("OEBPS/content.opf", content_opf)
        ep.writestr("OEBPS/style.css", CSS_CONTENT)
        if resolved_cover and os.path.exists(resolved_cover):
            with open(resolved_cover, "rb") as cf:
                ep.writestr("OEBPS/cover.jpg", cf.read())
        for fname, content in section_contents.items():
            ep.writestr(f"OEBPS/{fname}", content)

    return output_path
