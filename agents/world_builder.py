"""
World Builder Agent - Phase 1
Generates structured WorldBible from user seed concept using local LLM.
Includes robust JSON extraction, correction retry, and genre-aware fallbacks.
"""

import json
import re
from schemas.models import WorldBible, WorldRule
from generator.llm_client import LlmClient
from prompts.system_prompts import WORLD_BUILDER_PROMPT


class WorldBuilderAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_world(self, seed_title: str, seed_concept: str, genre: str) -> WorldBible:
        prompt = f"""
Seed Title: {seed_title}
Genre: {genre}
Seed Concept: {seed_concept}

Generate a comprehensive, structured World Bible for this manuscript.
Define at least 4 hard rules with clear narrative consequences when broken.
List 3 forbidden world-building tropes.
Return ONLY valid JSON output matching this schema:
{{
  "title": "{seed_title}",
  "genre": "{genre}",
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
        response_text = self.llm.generate_text(prompt, system_prompt=WORLD_BUILDER_PROMPT)
        bible = self._parse_world_bible(response_text)
        if bible:
            return bible

        # Retry Pass with explicit formatting correction prompt
        print("  [WorldBuilder] Initial JSON parse failed. Retrying with formatting correction prompt...")
        correction_prompt = prompt + "\n\nCRITICAL ERROR: Your previous response was not valid JSON. Output ONLY raw JSON. Do NOT include markdown code blocks or introductory text."
        retry_text = self.llm.generate_text(correction_prompt, system_prompt=WORLD_BUILDER_PROMPT)
        bible = self._parse_world_bible(retry_text)
        if bible:
            return bible

        # Genre-specific Fallback derived directly from seed_title and seed_concept
        print("  [WorldBuilder Warning] JSON retry failed, constructing genre-derived WorldBible fallback.")
        return self._fallback_world_bible(seed_title, genre, seed_concept)

    def _parse_world_bible(self, text: str) -> WorldBible:
        try:
            cleaned = self._clean_json(text)
            data = json.loads(cleaned)
            bible = WorldBible.model_validate(data)
            if bible.rules and len(bible.rules) > 0 and bible.title:
                return bible
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

    def _fallback_world_bible(self, title: str, genre: str, concept: str) -> WorldBible:
        g = genre.lower()
        if g in ["fiction", "romance"]:
            return WorldBible(
                title=title,
                genre=genre,
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
                setting_overview=f"Immersive environment based on: {concept}",
                time_period="Modern Era",
                core_thematic_conflict=f"Mastering the dynamics of {title}",
                rules=[
                    WorldRule(
                        category="Systemic Constraint",
                        rule_name="Conservation of Effort",
                        description="Every strategic decision has immediate downstream effects.",
                        narrative_consequence="Shortcuts lead to cascading inefficiencies."
                    )
                ],
                forbidden_tropes=["Deus Ex Machina", "Instant Mastery", "Generic Clichés"]
            )
