import unittest
from unittest.mock import MagicMock
from agents.critics import AntiSlopEditorAgent, ContinuityEditorAgent
from schemas.models import StoryState, WorldBible, CharacterRegistry, CharacterProfile, CharacterVoice


class TestCriticsCadenceAndSubtext(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.anti_slop = AntiSlopEditorAgent(self.mock_llm)
        self.continuity = ContinuityEditorAgent(self.mock_llm)

    def test_monotonous_sentence_cadence_detected(self):
        # 6 consecutive sentences with exact same mid-length (15 words)
        monotone_text = (
            "The courier walked into the cold stone castle while holding a sealed leather dispatch. "
            "The captain looked up from his iron table and gestured toward the flickering oil lamp. "
            "Nobody spoke as the heavy wooden doors swung shut behind the tired young royal rider. "
            "A sudden blast of winter wind rattled the tall leaded glass windows along the hall. "
            "Both men understood that their fragile military alliance was coming to a violent end. "
            "The silver coins spilled across the dark oak desk with a loud sharp ringing sound."
        )
        violations = self.anti_slop.audit_sentence_cadence(monotone_text)
        patterns = [v.phrase_or_pattern for v in violations]
        self.assertIn("Monotonous Sentence Cadence", patterns)

    def test_dynamic_provost_sentence_cadence_passes(self):
        # Varied text with short punchy staccato sentences (<=5 words) and sweeping sentences
        dynamic_text = (
            "He ran. "
            "The shadows stretched long across the wet cobbled alleyway as the hounds bayed in the distance. "
            "Silence fell. "
            "Through the icy mist hanging over the river docks, where cargo boats swayed against rotting pilings, he finally caught sight of the signal lantern flashing thrice. "
            "Marcus gripped the hilt tightly. "
            "Not now."
        )
        violations = self.anti_slop.audit_sentence_cadence(dynamic_text)
        self.assertEqual(len(violations), 0)

    def test_perceptual_filter_detection(self):
        filter_text = "Marcus approached the door. He noticed that the guard was asleep, and he felt that someone was watching him."
        violations = self.anti_slop.audit_slop(1, filter_text, language="english")
        patterns = [v.phrase_or_pattern for v in violations]
        self.assertIn("he noticed that", patterns)
        self.assertIn("he felt that", patterns)

    def test_secret_leak_continuity_check(self):
        bible = WorldBible(title="Court of Whispers", rules=[])
        char = CharacterProfile(name="Rowan", voice_fingerprint=CharacterVoice())
        reg = CharacterRegistry(characters=[char])
        state = StoryState(
            epistemic_secrets=[
                {"fact": "The King is Poisoned", "known_by": ["Elaria"], "hidden_from": ["Rowan"]}
            ]
        )
        text = "Rowan slammed his fist on the table. Rowan said that The King is Poisoned and everyone froze."
        issues = self.continuity.audit_chapter(1, text, bible, reg, state)
        self.assertTrue(any("revealed secret" in i.description for i in issues))


if __name__ == "__main__":
    unittest.main()
