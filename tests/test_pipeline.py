import os
import tempfile
import unittest
import zipfile
import docx
from pipeline import BookConfig, BookPipeline, slugify
from tests.fake_llm import FakeLlm


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_book(self, llm, title="The Ledger", **kwargs):
        options = dict(chapters=llm.chapters, scenes_per_chapter=llm.scenes, target_words=500, opening_candidates=2)
        options.update(kwargs)
        config = BookConfig(title=title, author="A. Writer", books_root=self.tmp.name, **options)
        return BookPipeline(config, llm), config

    def test_full_run_produces_book_and_kit(self):
        llm = FakeLlm()
        pipeline, _ = self.run_book(llm)
        result = pipeline.run()
        self.assertTrue(result["ready"], result["blockers"])
        self.assertTrue(os.path.exists(result["docx"]))
        self.assertTrue(zipfile.is_zipfile(result["epub"]))
        self.assertTrue(os.path.exists(os.path.join(pipeline.publishing_dir, "listing.md")))
        self.assertEqual(llm.tasks.count("choose opening"), 1)

        text = "\n".join(p.text for p in docx.Document(result["docx"]).paragraphs)
        for fabricated in ["Praise", "BESTSELLER", "masterpiece", "Thought Leader", "$69.99", "ISBN"]:
            self.assertNotIn(fabricated, text)

    def test_resume_makes_no_new_chapter_calls(self):
        llm = FakeLlm()
        self.run_book(llm)[0].run()
        drafted = llm.tasks.count("scene draft")
        self.run_book(llm)[0].run()
        self.assertEqual(llm.tasks.count("scene draft"), drafted)
        self.assertEqual(llm.tasks.count("book brief"), 1)

    def test_books_do_not_share_state(self):
        llm = FakeLlm()
        self.run_book(llm, title="Book One")[0].run()
        self.run_book(llm, title="Book Two")[0].run()
        self.assertEqual(llm.tasks.count("book brief"), 2)

    def test_revision_rewrites_only_flagged_scene_and_keeps_best_version(self):
        # First chapter scores 6, then 7 after revision, then 5 after a harmful revision
        llm = FakeLlm(chapters=2, scores=[6, 7, 5])
        pipeline, _ = self.run_book(llm, max_revisions=2, opening_candidates=1)
        result = pipeline.run()
        self.assertEqual(llm.tasks.count("scene revision"), 2)
        self.assertFalse(result["ready"])
        self.assertTrue(any("Chapter 1 failed" in b for b in result["blockers"]))
        _, briefs = pipeline._load_finished_chapters()
        self.assertEqual(briefs[1].craft_score, 7)

    def test_short_book_is_not_ready(self):
        pipeline, _ = self.run_book(FakeLlm(), target_words=100000)
        result = pipeline.run()
        self.assertTrue(any("Length" in b for b in result["blockers"]))

    def test_nonfiction_has_no_cast_and_gets_fact_check(self):
        llm = FakeLlm(is_fiction=False)
        pipeline, _ = self.run_book(llm)
        pipeline.run()
        self.assertEqual(pipeline.registry.characters, [])
        self.assertTrue(os.path.exists(os.path.join(pipeline.publishing_dir, "fact_check.md")))
        with open(os.path.join(pipeline.manuscript_dir, "chapter_01.md"), encoding="utf-8") as f:
            self.assertIn("### Heading 0", f.read())

    def test_fiction_uses_scene_breaks_not_headings(self):
        pipeline, _ = self.run_book(FakeLlm())
        pipeline.run()
        with open(os.path.join(pipeline.manuscript_dir, "chapter_01.md"), encoding="utf-8") as f:
            chapter = f.read()
        self.assertIn("* * *", chapter)
        self.assertNotIn("###", chapter)

    def test_unusable_model_output_fails_instead_of_inventing_a_book(self):
        class Garbage(FakeLlm):
            def generate_text(self, prompt, system_prompt="", max_tokens=4096):
                return "not json"
        pipeline, _ = self.run_book(Garbage())
        with self.assertRaises(RuntimeError):
            pipeline.run()

    def test_slug_keeps_tamil_and_blocks_traversal(self):
        self.assertEqual(slugify("../../etc/passwd"), "etc_passwd")
        self.assertEqual(slugify("வேல்விழியின் சபதம்"), "வேல்விழியின்_சபதம்")


if __name__ == "__main__":
    unittest.main()
