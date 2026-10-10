import os
import tempfile
import unittest
import docx
from generator.docx_compiler import compile_book


class TestDocxCompiler(unittest.TestCase):
    def test_docx_compiler_trade_book(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create minimal markdown chapters
            chap1_path = os.path.join(tmp_dir, "chapter_01.md")
            with open(chap1_path, "w", encoding="utf-8") as f:
                f.write("# Part I: The Genesis\n\n## Chapter 1: The Inciting Signal\n\n### 1.1 The Awakening\n\nThe silence shattered at dawn.\n\n> \"Courage is quiet.\"\n")

            praise_path = os.path.join(tmp_dir, "praise.md")
            with open(praise_path, "w", encoding="utf-8") as f:
                f.write("# Praise\n\n> \"A magnificent triumph.\" — Review\n")

            output_docx = os.path.join(tmp_dir, "test_book.docx")

            compile_book(
                title="The Quantum Realm",
                domain="Quantum Computing",
                author="Pravin Tamilan",
                chapters_dir=tmp_dir,
                output_path=output_docx,
                language="english"
            )

            self.assertTrue(os.path.exists(output_docx))
            self.assertGreater(os.path.getsize(output_docx), 5000)  # Should be a fully formatted docx > 5KB

            # Verify it can be loaded with python-docx
            doc = docx.Document(output_docx)
            full_text = " ".join([p.text for p in doc.paragraphs])
            self.assertIn("The Quantum Realm", full_text)
            self.assertIn("Pravin Tamilan", full_text)


if __name__ == "__main__":
    unittest.main()
