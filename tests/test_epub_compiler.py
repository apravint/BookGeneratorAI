import os
import tempfile
import unittest
import zipfile
from tools.epub_compiler import compile_epub


class TestEpubCompiler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_epub = os.path.join(self.test_dir, "test_novel.epub")

        # Create dummy chapter and front-matter markdown files
        with open(os.path.join(self.test_dir, "praise.md"), "w", encoding="utf-8") as f:
            f.write("# Praise\n\n> “An unforgettable epic.” — The Review")

        with open(os.path.join(self.test_dir, "chapter_01.md"), "w", encoding="utf-8") as f:
            f.write("## Chapter 1: The Spark\n\n### 1.1 The Meeting\nCold rain lashed the granite towers. Marcus gripped his sword.")

    def test_compile_epub_structure(self):
        result_path = compile_epub(
            title="The Iron Crown",
            author="Pravin Tamilan",
            chapters_dir=self.test_dir,
            output_path=self.output_epub,
            language="english"
        )
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(zipfile.is_zipfile(result_path))

        with zipfile.ZipFile(result_path, "r") as z:
            namelist = z.namelist()
            # Mimetype must be first file
            self.assertEqual(namelist[0], "mimetype")
            mimetype_info = z.getinfo("mimetype")
            self.assertEqual(mimetype_info.compress_type, zipfile.ZIP_STORED)
            self.assertEqual(z.read("mimetype").decode("utf-8"), "application/epub+zip")

            # EPUB 3 required artifacts
            self.assertIn("META-INF/container.xml", namelist)
            self.assertIn("OEBPS/content.opf", namelist)
            self.assertIn("OEBPS/nav.xhtml", namelist)
            self.assertIn("OEBPS/style.css", namelist)
            self.assertIn("OEBPS/chapter_01.xhtml", namelist)


if __name__ == "__main__":
    unittest.main()
