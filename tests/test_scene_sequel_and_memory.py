import os
import tempfile
import unittest
from unittest.mock import MagicMock
from schemas.models import WorldBible, CharacterRegistry, BookBrief, StoryState, ForeshadowingClue
from generator.json_parser import StructuredOutputError
from tests.fake_llm import FakeLlm
from agents.master_outliner import MasterOutlinerAgent
from memory.state_manager import StateManager


class TestSceneSequelAndMemory(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.mktemp(suffix=".db")
        self.state_mgr = StateManager(db_path=self.temp_db)
        self.mock_llm = MagicMock()

    def tearDown(self):
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)

    def test_outliner_uses_model_plan_and_seeds_clues(self):
        bible = WorldBible(title="Shadow Over Arnor", genre="fiction")
        outliner = MasterOutlinerAgent(FakeLlm(chapters=3, scenes=2))
        outline = outliner.build_outline(bible, CharacterRegistry(), BookBrief(), num_chapters=3, scenes_per_chapter=2, target_words=3000)

        self.assertEqual([c.title for c in outline.chapters], ["Unique Title 1", "Unique Title 2", "Unique Title 3"])
        self.assertEqual(outline.chapters[0].target_word_count, 1000)
        self.assertEqual(outline.chapters[0].sub_beats[1].section_number, "1.2")
        self.assertEqual(outline.foreshadowing[0].target_payoff_chapter, 3)
        self.assertEqual(outline.chapters[2].foreshadowing_clues_to_resolve, ["The Ledger"])

    def test_outliner_rejects_wrong_chapter_count(self):
        outliner = MasterOutlinerAgent(FakeLlm(chapters=2, scenes=2))
        with self.assertRaises(StructuredOutputError):
            outliner.build_outline(WorldBible(), CharacterRegistry(), BookBrief(), num_chapters=5, scenes_per_chapter=2)

    def test_chapter_memory_populates_story_state(self):
        story_state = StoryState(foreshadowing_clues=[ForeshadowingClue(name="The Ledger", target_payoff_chapter=2)])
        updated = self.state_mgr.update_dynamic_story_state(
            story_state, 2, "Reckoning", "Full text.", llm_client=FakeLlm(chapters=2), language="english"
        )
        self.assertEqual(updated.chapter_recaps[2], "Things changed.")
        self.assertIn("Who pays?", updated.active_plot_threads)
        self.assertEqual(updated.foreshadowing_clues[0].status, "resolved")

    def test_dynamic_memory_state_update(self):
        story_state = StoryState()
        updated_state = self.state_mgr.update_dynamic_story_state(
            story_state=story_state,
            chapter_number=1,
            chapter_title="The Gathering Storm",
            chapter_text="The city walls trembled under catapult fire.",
            llm_client=None,
            language="english"
        )
        self.assertEqual(updated_state.current_chapter, 1)
        self.assertIn("The Gathering Storm", updated_state.story_so_far_summary)
        self.assertTrue(any("The Gathering Storm" in t for t in updated_state.active_plot_threads))

        # Test persistence
        loaded_state = self.state_mgr.get_story_state()
        self.assertEqual(loaded_state.current_chapter, 1)
        self.assertEqual(len(loaded_state.active_plot_threads), 1)


if __name__ == "__main__":
    unittest.main()
