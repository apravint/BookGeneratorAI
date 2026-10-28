import os
import tempfile
import unittest
from unittest.mock import MagicMock

from schemas.models import (
    WorldBible,
    WorldRule,
    CharacterProfile,
    CharacterRegistry,
    CharacterVoice,
    CharacterRelation,
    ForeshadowingClue,
    ChapterBeat,
    MasterOutline,
    StoryState
)
from memory.state_manager import StateManager
from agents.critics import ContinuityEditorAgent
from tools.card_manager import CardManager


class TestForeshadowingAndRelations(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.mktemp(suffix=".db")
        self.state_mgr = StateManager(db_path=self.temp_db)
        self.mock_llm = MagicMock()

    def tearDown(self):
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)

    def test_foreshadowing_lifecycle(self):
        story_state = StoryState()
        clue = ForeshadowingClue(
            clue_id="clue_poison_ring",
            name="The Poison Signet Ring",
            description="A hollow signet ring containing aconite residue was concealed in the chancellor's desk.",
            planted_chapter=2,
            planted_beat="2.3",
            target_payoff_chapter=5,
            status="planted",
            involved_characters=["Julian", "Chancellor Vane"]
        )

        # 1. Add clue
        self.state_mgr.add_foreshadowing_clue(story_state, clue)
        self.assertEqual(len(story_state.foreshadowing_clues), 1)

        # 2. Check active clues
        active = self.state_mgr.get_active_clues(story_state)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].name, "The Poison Signet Ring")

        # 3. Check due clues at chapter 3 (not due yet)
        due_ch3 = self.state_mgr.get_due_clues(story_state, current_chapter=3)
        self.assertEqual(len(due_ch3), 0)

        # 4. Check due clues at chapter 5 (due!)
        due_ch5 = self.state_mgr.get_due_clues(story_state, current_chapter=5)
        self.assertEqual(len(due_ch5), 1)
        self.assertEqual(due_ch5[0].clue_id, "clue_poison_ring")

        # 5. Resolve clue
        self.state_mgr.resolve_foreshadowing_clue(
            story_state,
            clue_id="clue_poison_ring",
            resolution_notes="Julian confronted Vane at the banquet and revealed the signet ring."
        )
        self.assertEqual(story_state.foreshadowing_clues[0].status, "resolved")
        self.assertEqual(len(self.state_mgr.get_active_clues(story_state)), 0)

    def test_character_relationship_matrix(self):
        story_state = StoryState()

        # Update relation: Julian and Vane are bitter enemies
        self.state_mgr.update_character_relation(
            story_state=story_state,
            source_char="Julian",
            target_char="Chancellor Vane",
            relation_type="blood_feud",
            affinity_score=-9,
            dynamic_status="Vane murdered Julian's mentor"
        )
        self.assertEqual(len(story_state.character_relationships), 1)
        rel = story_state.character_relationships[0]
        self.assertEqual(rel.affinity_score, -9)
        self.assertEqual(rel.relation_type, "blood_feud")

        # Test querying relations by character name (case-insensitive)
        julian_rels = self.state_mgr.get_character_relationships(story_state, "julian")
        self.assertEqual(len(julian_rels), 1)
        self.assertEqual(julian_rels[0].target_char, "Chancellor Vane")

        # Update relation shift after a truce
        self.state_mgr.update_character_relation(
            story_state=story_state,
            source_char="Chancellor Vane",
            target_char="Julian",
            relation_type="fragile_truce",
            affinity_score=-2,
            dynamic_status="Forced alliance against an external invasion"
        )
        self.assertEqual(len(story_state.character_relationships), 1)
        self.assertEqual(story_state.character_relationships[0].affinity_score, -2)
        self.assertEqual(story_state.character_relationships[0].relation_type, "fragile_truce")

    def test_continuity_critic_audits_foreshadowing_omission(self):
        critic = ContinuityEditorAgent(self.mock_llm)
        bible = WorldBible(title="Court of Shadows")
        registry = CharacterRegistry()
        story_state = StoryState()

        # Plant clue due in Chapter 5
        clue = ForeshadowingClue(
            clue_id="clue_vault_key",
            name="The Obsidian Vault Key",
            description="The key hidden behind the library tapestry.",
            planted_chapter=1,
            target_payoff_chapter=5,
            status="planted"
        )
        story_state.foreshadowing_clues.append(clue)

        # Draft for Chapter 5 that completely omits any mention of the key
        chapter_5_draft = "The soldiers marched through the courtyard. The rain continued to fall relentlessly."
        issues = critic.audit_chapter(
            chapter_number=5,
            chapter_text=chapter_5_draft,
            world_bible=bible,
            registry=registry,
            story_state=story_state
        )
        # Should flag omitted payoff
        omitted = [i for i in issues if "foreshadowing payoff omitted" in i.description.lower()]
        self.assertEqual(len(omitted), 1)
        self.assertEqual(omitted[0].severity, "MAJOR")

        # When draft mentions the key, issue is cleared
        chapter_5_good = "Julian reached behind the library tapestry and retrieved the obsidian vault key."
        issues_good = critic.audit_chapter(
            chapter_number=5,
            chapter_text=chapter_5_good,
            world_bible=bible,
            registry=registry,
            story_state=story_state
        )
        omitted_good = [i for i in issues_good if "foreshadowing payoff omitted" in i.description.lower()]
        self.assertEqual(len(omitted_good), 0)

    def test_continuity_critic_audits_hostile_relationship_inconsistency(self):
        critic = ContinuityEditorAgent(self.mock_llm)
        bible = WorldBible(title="Court of Shadows")
        registry = CharacterRegistry()
        story_state = StoryState()

        story_state.character_relationships.append(
            CharacterRelation(
                source_char="Julian",
                target_char="Vane",
                relation_type="nemesis",
                affinity_score=-9,
                dynamic_status="Vane murdered Julian's family"
            )
        )

        bad_text = "Julian looked over at Vane with warmth. 'You are my best friend and dearest ally,' he smiled."
        issues = critic.audit_chapter(
            chapter_number=3,
            chapter_text=bad_text,
            world_bible=bible,
            registry=registry,
            story_state=story_state
        )
        hostile_issues = [i for i in issues if "hostile relationship contradiction" in i.description.lower()]
        self.assertEqual(len(hostile_issues), 1)

    def test_chapter_dag_downstream_and_invalidation(self):
        ch1 = ChapterBeat(chapter_number=1, title="The Theft", prerequisite_chapters=[])
        ch2 = ChapterBeat(chapter_number=2, title="The Chase", prerequisite_chapters=[1])
        ch3 = ChapterBeat(chapter_number=3, title="The Safehouse", prerequisite_chapters=[2])
        ch4 = ChapterBeat(chapter_number=4, title="Meanwhile at Court", prerequisite_chapters=[1])  # Subplot
        ch5 = ChapterBeat(chapter_number=5, title="The Climax", prerequisite_chapters=[3, 4])

        outline = MasterOutline(title="The Heist", chapters=[ch1, ch2, ch3, ch4, ch5])

        # If Chapter 2 is changed, downstream chapters should be [3, 5]
        downstream = self.state_mgr.get_downstream_chapters(outline, modified_chapter=2)
        self.assertEqual(downstream, [3, 5])

        # Save and invalidate chapter
        self.state_mgr.save_chapter_record(chapter_number=2, draft_text="Draft", brief=None, final_text="Final")
        inv = self.state_mgr.invalidate_chapter(chapter_number=2)
        self.assertTrue(inv)

    def test_card_manager_export_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            char = CharacterProfile(
                character_id="char_01",
                name="Aria Thorne",
                role="Master Thief",
                core_motivation="Clear her family name",
                fatal_flaw="Reckless pride",
                backstory_summary="Trained in the catacombs of the capital.",
                voice_fingerprint=CharacterVoice(tone="Sharp and cynical"),
                relationships={"Julian": "Grudging accomplice"}
            )
            card_path = os.path.join(tmpdir, "aria_card.json")

            # Export
            CardManager.export_character_card(char, card_path)
            self.assertTrue(os.path.exists(card_path))

            # Import
            imported_char = CardManager.import_character_card(card_path)
            self.assertEqual(imported_char.name, "Aria Thorne")
            self.assertEqual(imported_char.relationships["Julian"], "Grudging accomplice")

            # Lorebook export & import
            bible = WorldBible(title="Sunken Citadel", genre="fantasy")
            reg = CharacterRegistry(characters=[char])
            rel = [
                CharacterRelation(
                    source_char="Aria Thorne",
                    target_char="Julian",
                    relation_type="partner",
                    affinity_score=4
                )
            ]
            lorebook_path = os.path.join(tmpdir, "lorebook.json")
            CardManager.export_lorebook(bible, reg, rel, lorebook_path)
            self.assertTrue(os.path.exists(lorebook_path))

            imp_bible, imp_reg, imp_rel = CardManager.import_lorebook(lorebook_path)
            self.assertEqual(imp_bible.title, "Sunken Citadel")
            self.assertEqual(len(imp_reg.characters), 1)
            self.assertEqual(len(imp_rel), 1)
            self.assertEqual(imp_rel[0].affinity_score, 4)


if __name__ == "__main__":
    unittest.main()
