"""
World Builder Agent - Phase 1
Generates structured WorldBible from user seed concept using local LLM.
Includes robust JSON extraction and correction retry. Fails loudly rather than inventing a stock world.
"""

from schemas.models import WorldBible, BookBrief
from generator.llm_client import LlmClient
from generator.json_parser import parse_llm_json, StructuredOutputError
from prompts.system_prompts import WORLD_BUILDER_PROMPT, TAMIL_WORLD_BUILDER_PROMPT


class WorldBuilderAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_world(self, seed_title: str, seed_concept: str, genre: str, language: str = "english", brief: BookBrief = None) -> WorldBible:
        is_tamil = language.lower() in ["tamil", "ta"]
        system_prompt = TAMIL_WORLD_BUILDER_PROMPT if is_tamil else WORLD_BUILDER_PROMPT
        lang_directive = "Write all setting text, descriptions, and rule details in natural, fluent TAMIL (தமிழ் எழுத்துக்கள்)." if is_tamil else "Write in English."

        brief_block = f"Book Brief: {brief.logline} Promise: {brief.reader_promise} Ending: {brief.ending}" if brief else ""
        if brief and not brief.is_fiction:
            brief_block += "\nThis is non-fiction: define the subject's real setting and its governing principles. Do not invent a fictional world."

        prompt = f"""
Seed Title: {seed_title}
Genre: {genre}
Language: {language}
Seed Concept: {seed_concept}
Directive: {lang_directive}
{brief_block}

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

        raise StructuredOutputError(f"World Bible for '{seed_title}' could not be generated: the model returned invalid JSON twice.")

    def _parse_world_bible(self, text: str) -> WorldBible:
        bible = parse_llm_json(text, model_class=WorldBible)
        if bible and bible.rules and len(bible.rules) > 0 and bible.title:
            return bible
        return None
