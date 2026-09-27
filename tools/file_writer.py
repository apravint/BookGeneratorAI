"""
File Writer & Document Compiler Tool
Appends intermediate markdown files and compiles final commercial .docx document.
"""

import os
import shutil
from generator.docx_compiler import compile_book


class FileWriterTool:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def write_markdown_chapter(self, chapter_number: int, content: str) -> str:
        filename = f"chapter_{chapter_number:02d}.md"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def write_front_matter(self, praise: str, epigraph: str, preface: str, foreword: str):
        files = {
            "praise.md": praise,
            "epigraph.md": epigraph,
            "preface.md": preface,
            "foreword.md": foreword
        }
        for name, text in files.items():
            path = os.path.join(self.output_dir, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def compile_docx(self, title: str, domain: str, author: str, docx_path: str):
        compile_book(
            title=title,
            domain=domain,
            author=author,
            chapters_dir=self.output_dir,
            output_path=docx_path
        )
