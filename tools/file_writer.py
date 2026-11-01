"""
File Writer & Document Compiler Tool
Appends intermediate markdown files and compiles final commercial .docx document.
"""

import os
from generator.docx_compiler import compile_book
from tools.epub_compiler import compile_epub


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

    def compile_docx(self, title: str, domain: str, author: str, docx_path: str, language: str = "english", metadata: dict = None):
        compile_book(
            title=title,
            domain=domain,
            author=author,
            chapters_dir=self.output_dir,
            output_path=docx_path,
            language=language,
            metadata=metadata
        )

    def compile_epub(self, title: str, author: str, epub_path: str, language: str = "english", cover_image_path: str = None, metadata: dict = None) -> str:
        return compile_epub(
            title=title,
            author=author,
            chapters_dir=self.output_dir,
            output_path=epub_path,
            language=language,
            cover_image_path=cover_image_path,
            metadata=metadata
        )
