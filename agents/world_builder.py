"""
World Builder Agent - Phase 1
Generates structured WorldBible from user seed concept using local LLM.
Includes robust JSON extraction, correction retry, and genre-aware fallbacks.
"""

import json
import re
from schemas.models import WorldBible, WorldRule
from generator.llm_client import LlmClient
from generator.json_parser import parse_llm_json, clean_json_string
from prompts.system_prompts import WORLD_BUILDER_PROMPT, TAMIL_WORLD_BUILDER_PROMPT


class WorldBuilderAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_world(self, seed_title: str, seed_concept: str, genre: str, language: str = "english") -> WorldBible:
        is_tamil = language.lower() in ["tamil", "ta"]
        system_prompt = TAMIL_WORLD_BUILDER_PROMPT if is_tamil else WORLD_BUILDER_PROMPT
        lang_directive = "Write all setting text, descriptions, and rule details in natural, fluent TAMIL (தமிழ் எழுத்துக்கள்)." if is_tamil else "Write in English."

        prompt = f"""
Seed Title: {seed_title}
Genre: {genre}
Language: {language}
Seed Concept: {seed_concept}
Directive: {lang_directive}

Generate a comprehensive, structured World Bible for this manuscript.
Define at least 4 hard rules with clear narrative consequences when broken.
List 3 forbidden world-building tropes.
Return ONLY valid JSON output matching this schema:
{{
  "title": "{seed_title}",
  "genre": "{genre}",
  "language": "{language}",
  "setting_overview": "Vivid setting overview...",
  "time_period": "Temporal setting...",
  "core_thematic_conflict": "Central conflict...",
  "rules": [
    {{
      "category": "Systemic Rule",
      "rule_name": "Rule Name",
      "description": "Rule description...",
      "narrative_consequence": "Consequence when broken..."
    }}
  ],
  "forbidden_tropes": ["trope_1", "trope_2"]
}}
"""
        # Attempt 1
        response_text = self.llm.generate_text(prompt, system_prompt=system_prompt)
        bible = self._parse_world_bible(response_text)
        if bible:
            bible.language = language
            return bible

        # Retry Pass with explicit formatting correction prompt
        print("  [WorldBuilder] Initial JSON parse failed. Retrying with formatting correction prompt...")
        correction_prompt = prompt + "\n\nCRITICAL ERROR: Your previous response was not valid JSON. Output ONLY raw JSON. Do NOT include markdown code blocks or introductory text."
        retry_text = self.llm.generate_text(correction_prompt, system_prompt=system_prompt)
        bible = self._parse_world_bible(retry_text)
        if bible:
            bible.language = language
            return bible

        # Genre-specific Fallback derived directly from seed_title and seed_concept
        print("  [WorldBuilder Warning] JSON retry failed, constructing genre-derived WorldBible fallback.")
        fallback = self._fallback_world_bible(seed_title, genre, seed_concept, is_tamil=is_tamil)
        fallback.language = language
        return fallback

    def _parse_world_bible(self, text: str) -> WorldBible:
        bible = parse_llm_json(text, model_class=WorldBible)
        if bible and bible.rules and len(bible.rules) > 0 and bible.title:
            return bible
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

    def _fallback_world_bible(self, title: str, genre: str, concept: str, is_tamil: bool = False) -> WorldBible:
        if is_tamil:
            return WorldBible(
                title=title,
                genre=genre,
                language="tamil",
                setting_overview=f"தமிழ் மண், பண்பாடு மற்றும் வரலாற்றுப் பின்னணியில் அமைந்த கம்பீரமான கதைக்களம்: {concept or title}.",
                time_period="பண்டைய / நவீன தமிழகம்",
                core_thematic_conflict="வீரம், காதல், தியாகம் மற்றும் நீதிக்கான உணர்ச்சிப்பூர்வமான போராட்டம்.",
                rules=[
                    WorldRule(
                        category="சமூக விதி",
                        rule_name="சொன்ன சொல் தவறாமை",
                        description="வாக்கு தவறாமை மற்றும் வீரத்தின் கண்ணியம் உயிரினும் மேலானது.",
                        narrative_consequence="வாக்கு தவறினால் பெரும் பழி மற்றும் சமுதாய புறக்கணிப்பு ஏற்படும்."
                    ),
                    WorldRule(
                        category="அரசியல் விதி",
                        rule_name="மகுடத்தின் தர்மம்",
                        description="அரியணை என்பது அதிகாரத்திற்கானதல்ல, மக்களின் நலனுக்கானது.",
                        narrative_consequence="அநீதி இழைக்கும் அரசன் பேரழிவைச் சந்திப்பான்."
                    )
                ],
                forbidden_tropes=["செயற்கையான மொழிபெயர்ப்பு", "ஆங்கில வார்த்தைகள்", "போலித் தத்துவப் பத்திகள்"]
            )
        g = genre.lower()
        if g in ["fiction", "romance"]:
            return WorldBible(
                title=title,
                genre=genre,
                language="english",
                setting_overview=f"An emotionally rich, captivating world centered around {title} and deep personal relationships.",
                time_period="Contemporary",
                core_thematic_conflict="The struggle between intense emotional devotion, vulnerability, and external obstacles.",
                rules=[
                    WorldRule(
                        category="Emotional Constraint",
                        rule_name="The Law of Vulnerability",
                        description="True intimacy requires exposing one's deepest fears and past wounds.",
                        narrative_consequence="Hiding the truth creates painful misunderstandings and emotional distance."
                    ),
                    WorldRule(
                        category="Social Setting",
                        rule_name="High Stakes Relationship",
                        description="External pressures and conflicting loyalties challenge the bond between lovers.",
                        narrative_consequence="Choices made in secret carry heavy consequences for both partners."
                    )
                ],
                forbidden_tropes=["Corporate Jargon", "Software Code", "Technical Diagrams", "Artificial Predictability"]
            )
        else:
            return WorldBible(
                title=title,
                genre=genre,
                language="english",
                setting_overview=f"Immersive environment based on: {concept}",
                time_period="Modern Era",
                core_thematic_conflict=f"Mastering the dynamics of {title}",
                rules=[
                    WorldRule(
                        category="Systemic Rule",
                        rule_name="Core Constraint",
                        description="Domain mastery requires total commitment.",
                        narrative_consequence="Partial execution leads to operational failure."
                    )
                ],
                forbidden_tropes=["Generic Clichés", "Superficial Overviews"]
            )

