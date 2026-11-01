"""
Character Architect Agent - Phase 1
Constructs structured CharacterRegistry from WorldBible.
Includes robust JSON extraction and retry logic. Fails loudly rather than shipping stock characters.
"""

from schemas.models import WorldBible, CharacterRegistry, BookBrief
from generator.llm_client import LlmClient
from generator.json_parser import parse_llm_json, StructuredOutputError
from prompts.system_prompts import CHARACTER_ARCHITECT_PROMPT, TAMIL_CHARACTER_ARCHITECT_PROMPT


class CharacterArchitectAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_characters(self, world_bible: WorldBible, author_name: str, language: str = "english", brief: BookBrief = None) -> CharacterRegistry:
        if brief and not brief.is_fiction:
            # Non-fiction has no invented cast; real people come from each chapter's beats
            return CharacterRegistry()
        is_tamil = (language or getattr(world_bible, 'language', 'english')).lower() in ["tamil", "ta"]
        system_prompt = TAMIL_CHARACTER_ARCHITECT_PROMPT if is_tamil else CHARACTER_ARCHITECT_PROMPT
        lang_directive = "Generate authentic Tamil character names (e.g. அருள்மொழி, மாறன், வந்தியதேவன், கயல்விழி, அமுதா) and write all motivations, flaw, backstory, and voice in TAMIL (தமிழ் எழுத்துக்கள்)." if is_tamil else "Write in English."

        prompt = f"""
World Title: {world_bible.title}
Genre: {world_bible.genre}
Setting Overview: {world_bible.setting_overview}
Core Conflict: {world_bible.core_thematic_conflict}
Book Promise: {brief.reader_promise if brief else ""}
Language Directive: {lang_directive}

Generate a Character Registry with at least 3 core characters (Protagonist, Antagonist/Challenge, Ally/Mentor).
Define distinct Voice Fingerprints for each.
Return output ONLY in JSON matching this schema:
{{
  "characters": [
    {{
      "character_id": "char_01",
      "name": "Character Name",
      "role": "Protagonist",
      "core_motivation": "Motivation...",
      "fatal_flaw": "Fatal flaw...",
      "backstory_summary": "Backstory...",
      "voice_fingerprint": {{
        "tone": "Tone...",
        "sentence_structure": "Structure...",
        "frequently_used_terms": ["term1", "term2"],
        "taboo_phrases": ["taboo1", "taboo2"]
      }},
      "relationships": {{}},
      "arc_trajectory": "Arc description..."
    }}
  ]
}}
"""
        response_text = self.llm.generate_text(prompt, system_prompt=system_prompt)
        registry = self._parse_registry(response_text)
        if registry:
            return registry

        print("  [CharacterArchitect] Initial JSON parse failed. Retrying with formatting correction prompt...")
        correction_prompt = prompt + "\n\nCRITICAL ERROR: Your previous response was not valid JSON. Output ONLY raw JSON matching the CharacterRegistry schema."
        retry_text = self.llm.generate_text(correction_prompt, system_prompt=system_prompt)
        registry = self._parse_registry(retry_text)
        if registry:
            return registry

        raise StructuredOutputError(f"Character Registry for '{world_bible.title}' could not be generated: the model returned invalid JSON twice.")

    def _parse_registry(self, text: str) -> CharacterRegistry:
        registry = parse_llm_json(text, model_class=CharacterRegistry)
        if registry and registry.characters and len(registry.characters) > 0:
            return registry
        return None
