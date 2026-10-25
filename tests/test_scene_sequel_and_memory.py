import os
import tempfile
import unittest
from unittest.mock import MagicMock
from schemas.models import WorldBible, CharacterRegistry, SubBeat, StoryState
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

    def test_outliner_populates_scene_sequel_beat_types(self):
        bible = WorldBible(title="Shadow Over Arnor", genre="fiction")
        registry = CharacterRegistry()
        outliner = MasterOutlinerAgent(self.mock_llm)
        outline = outliner.build_outline(bible, registry, language="english")

        first_chap = outline.chapters[0]
        self.assertEqual(len(first_chap.sub_beats), 6)

        beat_types = [sb.beat_type for sb in first_chap.sub_beats]
        expected_types = [
            "SCENE_GOAL",
            "CONFLICT_ESCALATION",
            "DISASTER_REVERSAL",
            "EMOTIONAL_REACTION",
            "DILEMMA_CALCULATION",
            "PIVOTAL_DECISION"
        ]
        self.assertEqual(beat_types, expected_types)

        # Verify micro-tension levels curve
        tensions = [sb.micro_tension_level for sb in first_chap.sub_beats]
        self.assertEqual(tensions, [4, 6, 8, 5, 7, 9])

        # Verify internal subtext is populated
        for sb in first_chap.sub_beats:
            self.assertTrue(len(sb.pov_internal_state) > 0)

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
