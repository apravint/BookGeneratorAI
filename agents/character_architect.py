"""
Character Architect Agent - Phase 1
Constructs structured CharacterRegistry from WorldBible.
Includes robust JSON extraction, retry logic, and genre-aware fallbacks.
"""

import json
import re
from schemas.models import WorldBible, CharacterRegistry, CharacterProfile, CharacterVoice
from generator.llm_client import LlmClient
from prompts.system_prompts import CHARACTER_ARCHITECT_PROMPT, TAMIL_CHARACTER_ARCHITECT_PROMPT


class CharacterArchitectAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_characters(self, world_bible: WorldBible, author_name: str, language: str = "english") -> CharacterRegistry:
        is_tamil = (language or getattr(world_bible, 'language', 'english')).lower() in ["tamil", "ta"]
        system_prompt = TAMIL_CHARACTER_ARCHITECT_PROMPT if is_tamil else CHARACTER_ARCHITECT_PROMPT
        lang_directive = "Generate authentic Tamil character names (e.g. அருள்மொழி, மாறன், வந்தியதேவன், கயல்விழி, அமுதா) and write all motivations, flaw, backstory, and voice in TAMIL (தமிழ் எழுத்துக்கள்)." if is_tamil else "Write in English."

        prompt = f"""
World Title: {world_bible.title}
Genre: {world_bible.genre}
Setting Overview: {world_bible.setting_overview}
Core Conflict: {world_bible.core_thematic_conflict}
Author: {author_name}
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

        print("  [CharacterArchitect Warning] JSON retry failed, constructing genre-derived CharacterRegistry fallback.")
        return self._fallback_registry(world_bible, author_name, is_tamil=is_tamil)

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

    def _fallback_registry(self, world_bible: WorldBible, author_name: str, is_tamil: bool = False) -> CharacterRegistry:
        if is_tamil:
            return CharacterRegistry(
                characters=[
                    CharacterProfile(
                        character_id="char_01",
                        name="அருள்மொழி மாறன்",
                        role="கதாநாயகன் (Protagonist)",
                        core_motivation="தாய்நாட்டைக் காத்தல் மற்றும் நீதியை நிலைநாட்டுதல்",
                        fatal_flaw="நம்பிக்கை கொண்டவர்களை சந்தேகிக்கத் தயங்குதல்",
                        backstory_summary="வீரம் மற்றும் கருணை நிறைந்த இளவரசன் / கம்பீரமான தலைவன்.",
                        voice_fingerprint=CharacterVoice(
                            tone="கம்பீரமான, நயமான மற்றும் உணர்ச்சிப்பூர்வமான குரல்",
                            sentence_structure="ஆழமான தமிழ் உரைநடை",
                            frequently_used_terms=["வீரம்", "தர்மம்", "காதல்", "தாய்நாடு"],
                            taboo_phrases=["கோழைத்தனம்", "துரோகம்"]
                        ),
                        relationships={"char_02": "உயிர் தோழன் மற்றும் ஆலோசகன்"},
                        arc_trajectory="இளவரசனில் தொடங்கி பேரரசனாக உருவெடுத்தல்"
                    ),
                    CharacterProfile(
                        character_id="char_02",
                        name="வந்தியதேவன்",
                        role="தோழன் / ஒற்றன் (Ally & Spy)",
                        core_motivation="அருள்மொழி மாறனுக்கு உறுதுணையாக இருந்து இரகசியங்களை சேகரித்தல்",
                        fatal_flaw="அதிகமான துணிச்சல் மற்றும் அவசர முடிவு",
                        backstory_summary="சதுரங்க வியூகங்களில் வல்லவன், நகைச்சுவை உணர்வு மிக்க வீரன்.",
                        voice_fingerprint=CharacterVoice(
                            tone="சுறுசுறுப்பான, விறுவிறுப்பான மற்றும் நகைச்சுவையான பேச்சு",
                            sentence_structure="வேகமான வாக்கியங்கள்",
                            frequently_used_terms=["நண்பா", "சாமர்த்தியம்", "தந்திரம்"],
                            taboo_phrases=["பயம்"]
                        ),
                        relationships={"char_01": "உயிர்த் தோழன்"},
                        arc_trajectory="துணிச்சல்மிக்க வீரனில் இருந்து நம்பிக்கையான தளபதியாக உயர்தல்"
                    ),
                    CharacterProfile(
                        character_id="char_03",
                        name="கயல்விழி",
                        role="நாயகி (Co-Protagonist)",
                        core_motivation="தனது குலத்தின் கௌரவத்தைக் காத்தல் மற்றும் காதல்",
                        fatal_flaw="தன்மான உணர்ச்சி",
                        backstory_summary="அறிவும் வீரமும் நிறைந்த பெண்மணி.",
                        voice_fingerprint=CharacterVoice(
                            tone="கனிவான அதே நேரம் உறுதியான குரல்",
                            sentence_structure="நயமான கவித்துவ வாக்கியங்கள்",
                            frequently_used_terms=["அன்பு", "மானக் காப்பு", "நீதி"],
                            taboo_phrases=["பணியுதல்"]
                        ),
                        relationships={"char_01": "காதலி"},
                        arc_trajectory="அமைதியான இளவரசியில் இருந்து வீரமங்கையாகத் திகழ்தல்"
                    )
                ]
            )
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
