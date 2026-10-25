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


CSS_CONTENT = """
@charset "utf-8";
body {
    font-family: "Georgia", "Merriweather", "Noto Serif", "Times New Roman", serif;
    font-size: 1.05em;
    line-height: 1.65;
    color: #1e293b;
    margin: 5% 8%;
    padding: 0;
}
h1, h2, h3, h4 {
    font-family: "Helvetica Neue", "Arial", sans-serif;
    color: #0f172a;
    font-weight: 700;
    line-height: 1.25;
}
h1.book-title {
    font-size: 2.2em;
    text-align: center;
    margin-top: 25%;
    margin-bottom: 0.2em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
p.author-name {
    font-size: 1.2em;
    text-align: center;
    color: #0284c7;
    margin-bottom: 30%;
}
h2.chapter-title {
    font-size: 1.7em;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 0.3em;
    margin-top: 1.5em;
    margin-bottom: 0.8em;
    page-break-before: always;
}
h3.section-heading {
    font-size: 1.2em;
    color: #334155;
    margin-top: 1.2em;
    margin-bottom: 0.5em;
}
p {
    margin: 0 0 1em 0;
    text-indent: 0;
    text-align: justify;
}
p.lead::first-letter {
    font-size: 3.2em;
    float: left;
    margin: 0.05em 0.15em 0 0;
    line-height: 0.85;
    color: #0284c7;
    font-weight: bold;
}
blockquote {
    border-left: 3px solid #059669;
    background-color: #f8fafc;
    margin: 1.2em 0;
    padding: 0.8em 1.2em;
    font-style: italic;
    color: #334155;
}
hr.divider {
    border: 0;
    height: 1px;
    background: #cbd5e1;
    margin: 2em 0;
}
"""


def markdown_to_xhtml(md_text: str) -> str:
    """Converts basic Markdown formatting to clean XHTML."""
    html_lines = []
    lines = md_text.split('\n')
    in_blockquote = False
    first_p = True

    for line in lines:
        s = line.strip()
        if not s:
            if in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False
            continue

        if s.startswith('### '):
            if in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False
            heading = escape(s[4:])
            html_lines.append(f'<h3 class="section-heading">{heading}</h3>')
            first_p = True
        elif s.startswith('## '):
            if in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False
            heading = escape(s[3:])
            html_lines.append(f'<h2 class="chapter-title">{heading}</h2>')
            first_p = True
        elif s.startswith('# '):
            if in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False
            heading = escape(s[2:])
            html_lines.append(f'<h1 class="chapter-title">{heading}</h1>')
            first_p = True
        elif s.startswith('>'):
            if not in_blockquote:
                html_lines.append("<blockquote>")
                in_blockquote = True
            quote_text = escape(s.lstrip('>').strip())
            quote_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', quote_text)
            quote_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', quote_text)
            html_lines.append(f"<p>{quote_text}</p>")
        elif s.startswith('---'):
            if in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False
            html_lines.append('<hr class="divider" />')
        else:
            if in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False
            para = escape(s)
            para = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', para)
            para = re.sub(r'\*(.*?)\*', r'<em>\1</em>', para)
            css_class = ' class="lead"' if first_p else ''
            html_lines.append(f'<p{css_class}>{para}</p>')
            first_p = False

    if in_blockquote:
        html_lines.append("</blockquote>")

    return "\n".join(html_lines)


def compile_epub(
    title: str,
    author: str,
    chapters_dir: str,
    output_path: str,
    language: str = "english"
) -> str:
    """Compiles markdown chapter files into a validated EPUB 3 document."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    lang_code = "ta" if language.lower() in ["tamil", "ta"] else "en"
    book_uuid = f"urn:uuid:{uuid.uuid4()}"
    mod_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Discover and sort Markdown files
    front_matter_order = ["praise.md", "epigraph.md", "preface.md", "foreword.md"]
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

    # Title Page
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

    # Convert sections
    for idx, (section_id, file_path) in enumerate(md_files, start=1):
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        html_body = markdown_to_xhtml(raw_text)
        first_line = raw_text.strip().split('\n')[0]
        heading_match = re.search(r'#+\s*(.*)', first_line)
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
        <h2 class="chapter-title">Table of Contents</h2>
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

    # OEBPS/content.opf
    content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{escape(title)}</dc:title>
        <dc:creator>{escape(author)}</dc:creator>
        <dc:language>{lang_code}</dc:language>
        <dc:identifier id="BookID">{book_uuid}</dc:identifier>
        <meta property="dcterms:modified">{mod_time}</meta>
    </metadata>
    <manifest>
        {"\n        ".join(manifest_items)}
    </manifest>
    <spine>
        {"\n        ".join(spine_items)}
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
        for fname, content in section_contents.items():
            ep.writestr(f"OEBPS/{fname}", content)

    return output_path
