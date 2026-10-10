import os
import tempfile
import unittest
from memory.state_manager import StateManager
from schemas.models import WorldBible, StoryState, RevisionBrief


class TestStateManager(unittest.TestCase):
    def test_state_manager_sqlite_lifecycle(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            mgr = StateManager(db_path=db_path)

            # 1. Save and retrieve World Bible
            bible = WorldBible(title="Test Bible", genre="fiction", setting_overview="Cyberpunk City")
            mgr.save_world_bible(bible)
            loaded_bible = mgr.get_world_bible()
            self.assertIsNotNone(loaded_bible)
            self.assertEqual(loaded_bible.title, "Test Bible")
            self.assertEqual(loaded_bible.setting_overview, "Cyberpunk City")

            # 2. Save and retrieve Story State
            state = StoryState(current_chapter=1, story_so_far_summary="Opening arc began.")
            mgr.save_story_state(state)
            loaded_state = mgr.get_story_state()
            self.assertIsNotNone(loaded_state)
            self.assertEqual(loaded_state.current_chapter, 1)
            self.assertIn("Opening arc began", loaded_state.story_so_far_summary)

            # 3. Save chapter record
            brief = RevisionBrief(passed_audit=True)
            mgr.save_chapter_record(1, "Draft content", brief, "Final content")

        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


if __name__ == "__main__":
    unittest.main()
