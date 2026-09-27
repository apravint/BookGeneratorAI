"""
Character Architect Agent - Phase 1
Constructs structured CharacterRegistry from WorldBible.
Includes robust JSON extraction, retry logic, and genre-aware fallbacks.
"""

import json
import re
from schemas.models import WorldBible, CharacterRegistry, CharacterProfile, CharacterVoice
from generator.llm_client import LlmClient
from prompts.system_prompts import CHARACTER_ARCHITECT_PROMPT


class CharacterArchitectAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_characters(self, world_bible: WorldBible, author_name: str) -> CharacterRegistry:
        prompt = f"""
World Title: {world_bible.title}
Genre: {world_bible.genre}
Setting Overview: {world_bible.setting_overview}
Core Conflict: {world_bible.core_thematic_conflict}
Author: {author_name}

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
        response_text = self.llm.generate_text(prompt, system_prompt=CHARACTER_ARCHITECT_PROMPT)
        registry = self._parse_registry(response_text)
        if registry:
            return registry

        print("  [CharacterArchitect] Initial JSON parse failed. Retrying with formatting correction prompt...")
        correction_prompt = prompt + "\n\nCRITICAL ERROR: Your previous response was not valid JSON. Output ONLY raw JSON matching the CharacterRegistry schema."
        retry_text = self.llm.generate_text(correction_prompt, system_prompt=CHARACTER_ARCHITECT_PROMPT)
        registry = self._parse_registry(retry_text)
        if registry:
            return registry

        print("  [CharacterArchitect Warning] JSON retry failed, constructing genre-derived CharacterRegistry fallback.")
        return self._fallback_registry(world_bible, author_name)

    def _parse_registry(self, text: str) -> CharacterRegistry:
        try:
            cleaned = self._clean_json(text)
            data = json.loads(cleaned)
            registry = CharacterRegistry.model_validate(data)
            if registry.characters and len(registry.characters) > 0:
                return registry
        except Exception:
            pass
        return None

    def _clean_json(self, text: str) -> str:
        if not text:
            return "{}"
        # 1. Strip reasoning blocks
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        # 2. Extract code block content if wrapped
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        # 3. Match largest JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return match.group(0).strip()
        return text.strip()

    def _fallback_registry(self, world_bible: WorldBible, author_name: str) -> CharacterRegistry:
        g = world_bible.genre.lower()
        if g in ["fiction", "romance"]:
            return CharacterRegistry(
                characters=[
                    CharacterProfile(
                        character_id="char_01",
                        name="Clara Sterling",
                        role="Protagonist",
                        core_motivation="Finding true love and healing past emotional wounds",
                        fatal_flaw="Fear of vulnerability and guarded heart",
                        backstory_summary="Independent and passionate visionary with a cautious heart.",
                        voice_fingerprint=CharacterVoice(
                            tone="Warm, expressive, and deeply reflective",
                            sentence_structure="Sensory and emotional",
                            frequently_used_terms=["devotion", "passion", "forever", "heart"],
                            taboo_phrases=["system", "architecture", "compliance", "data"]
                        ),
                        relationships={"char_02": "Love interest & complex partner"},
                        arc_trajectory="From guarded isolation to unshakeable vulnerability and love"
                    ),
                    CharacterProfile(
                        character_id="char_02",
                        name="Julian Vance",
                        role="Love Interest / Co-Protagonist",
                        core_motivation="Protecting Clara and building an unbroken future together",
                        fatal_flaw="Stoic self-reliance and reluctance to reveal internal pain",
                        backstory_summary="Determined and loyal visionary driven by a sacred promise.",
                        voice_fingerprint=CharacterVoice(
                            tone="Intense, gentle, and deeply sincere",
                            sentence_structure="Direct, powerful, and poetic",
                            frequently_used_terms=["promise", "always", "together", "trust"],
                            taboo_phrases=["protocol", "database", "vector", "framework"]
                        ),
                        relationships={"char_01": "Deeply devoted partner"},
                        arc_trajectory="From stoic solitude to profound emotional openness"
                    )
                ]
            )
        else:
            return CharacterRegistry(
                characters=[
                    CharacterProfile(
                        character_id="char_01",
                        name="Elena Vance",
                        role="Protagonist",
                        core_motivation=f"Mastering the principles of {world_bible.title}",
                        fatal_flaw="Reluctance to delegate critical decisions",
                        backstory_summary="Seasoned practitioner who witnessed legacy failure.",
                        voice_fingerprint=CharacterVoice(
                            tone="Pragmatic",
                            sentence_structure="Clear and decisive",
                            frequently_used_terms=["strategy", "resilience"],
                            taboo_phrases=["cannot be done"]
                        ),
                        relationships={},
                        arc_trajectory="From cautious specialist to transformational leader"
                    ),
                    CharacterProfile(
                        character_id="char_02",
                        name="Marcus Sterling",
                        role="Antagonist",
                        core_motivation="Preserving traditional paradigms and market dominance",
                        fatal_flaw="Arrogant complacency",
                        backstory_summary="Veteran executive resistant to disruption.",
                        voice_fingerprint=CharacterVoice(
                            tone="Authoritative",
                            sentence_structure="Elaborate corporate phrasing",
                            frequently_used_terms=["governance", "status quo"],
                            taboo_phrases=["pivot", "agile"]
                        ),
                        relationships={"char_01": "Ideological rivals"},
                        arc_trajectory="From entrenched resistance to forced adaptiveness"
                    )
                ]
            )
