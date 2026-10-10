import unittest
from generator.blueprint import BookBlueprint


class TestBlueprint(unittest.TestCase):
    def test_blueprint_genre_auto_detection(self):
        # Tamil historical
        bp_tamil = BookBlueprint(title="சோழன் பரம்பரை", genre="auto")
        self.assertEqual(bp_tamil.genre, "tamil_historical")
        self.assertEqual(len(bp_tamil.parts), 4)
        total_chapters = sum(len(p["chapters"]) for p in bp_tamil.parts)
        self.assertEqual(total_chapters, 12)

        # Technical
        bp_tech = BookBlueprint(title="Architecting AI-Native Microservices", genre="auto")
        self.assertEqual(bp_tech.genre, "technical")
        self.assertEqual(len(bp_tech.parts), 4)

        # Business
        bp_biz = BookBlueprint(title="The 100M CEO Leadership Blueprint", genre="auto")
        self.assertEqual(bp_biz.genre, "business")

        # Fiction
        bp_fic = BookBlueprint(title="The Shadow Kingdom Chronicles", genre="auto")
        self.assertEqual(bp_fic.genre, "fiction")

    def test_blueprint_explicit_genre(self):
        bp = BookBlueprint(title="My Journey", genre="self-help")
        self.assertEqual(bp.genre, "self-help")
        self.assertEqual(len(bp.parts), 4)


if __name__ == "__main__":
    unittest.main()
