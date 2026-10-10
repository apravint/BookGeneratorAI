import unittest
from schemas.models import (
    WorldRule,
    WorldBible,
    CharacterVoice,
    CharacterProfile,
    CharacterRegistry,
    SubBeat,
    ChapterBeat,
    MasterOutline,
    ContinuityIssue,
    RevisionBrief
)


class TestSchemas(unittest.TestCase):
    def test_world_rule_alias_choices(self):
        rule = WorldRule.model_validate({
            "category": "Magic",
            "name": "Law of Conservation",
            "description": "Magic cannot be created from nothing.",
            "consequence": "Severe physical fatigue"
        })
        self.assertEqual(rule.rule_name, "Law of Conservation")
        self.assertEqual(rule.narrative_consequence, "Severe physical fatigue")

    def test_world_bible_validation(self):
        bible = WorldBible(
            title="Ponniyin Selvan Returns",
            genre="tamil_historical",
            language="tamil",
            setting_overview="Chola Empire",
            time_period="10th Century CE",
            core_thematic_conflict="Throne Succession",
            rules=[
                WorldRule(
                    category="Royal",
                    rule_name="Crown Loyalty",
                    description="Treason punished by exile",
                    narrative_consequence="Stripped of titles"
                )
            ],
            forbidden_tropes=["Time travel"]
        )
        self.assertEqual(bible.title, "Ponniyin Selvan Returns")
        self.assertEqual(len(bible.rules), 1)
        self.assertEqual(bible.rules[0].rule_name, "Crown Loyalty")

    def test_character_registry_validation(self):
        char = CharacterProfile(
            character_id="char_01",
            name="Arulmozhi Varman",
            role="Protagonist",
            core_motivation="Protect the Tamil realm",
            fatal_flaw="Too forgiving",
            backstory_summary="Youngest prince",
            voice_fingerprint=CharacterVoice(
                tone="Noble and measured",
                sentence_structure="Compound poetic phrasing",
                frequently_used_terms=["தர்மம்", "நாடு"],
                taboo_phrases=["I surrender"]
            )
        )
        reg = CharacterRegistry(characters=[char])
        self.assertEqual(len(reg.characters), 1)
        self.assertEqual(reg.characters[0].name, "Arulmozhi Varman")
        self.assertIn("தர்மம்", reg.characters[0].voice_fingerprint.frequently_used_terms)

    def test_chapter_beat_validation(self):
        sub = SubBeat(
            section_number="1.1",
            scene_objective="Establish the inciting spark",
            key_interaction="Messenger arrives",
            sensory_or_structural_detail="Drenching monsoon rain",
            ending_hook="The letter contains an unbroken royal seal"
        )
        beat = ChapterBeat(
            chapter_number=1,
            title="The Messenger in the Storm",
            part_name="Part 1: The Rising Storm",
            pov_character="Vanthiyathevan",
            location="Veeranam Lake",
            sub_beats=[sub]
        )
        outline = MasterOutline(book_title="Epic Tale", chapters=[beat])
        self.assertEqual(len(outline.chapters), 1)
        self.assertEqual(outline.chapters[0].sub_beats[0].section_number, "1.1")

    def test_revision_brief_audit(self):
        brief_pass = RevisionBrief(passed_audit=True)
        self.assertTrue(brief_pass.passed_audit)
        self.assertEqual(len(brief_pass.continuity_issues), 0)

        brief_fail = RevisionBrief(
            passed_audit=False,
            editor_overall_directive="Fix tone mismatch",
            continuity_issues=[
                ContinuityIssue(
                    severity="MAJOR",
                    location="Chapter 1.2",
                    description="Character used modern slang",
                    remedy="Replace with period-appropriate dialogue"
                )
            ]
        )
        self.assertFalse(brief_fail.passed_audit)
        self.assertEqual(len(brief_fail.continuity_issues), 1)


if __name__ == "__main__":
    unittest.main()
