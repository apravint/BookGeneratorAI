"""
Book Strategist Agent - Phase 0
Defines the commercial concept (reader, promise, hook, ending, voice) before any story work begins.
"""

from schemas.models import BookBrief
from generator.llm_client import LlmClient
from generator.json_parser import generate_validated
from prompts.system_prompts import BOOK_STRATEGIST_PROMPT, language_directive


class BookStrategistAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_brief(self, title: str, concept: str, genre: str, language: str = "english") -> BookBrief:
        prompt = f"""TASK: book brief
Title: {title}
Genre: {genre}
Concept from the author: {concept}
{language_directive(language)}

Develop the commercial concept for this book. Be specific enough that two different writers would produce the same book.
Return ONLY JSON with this schema:
{{
  "is_fiction": true,
  "logline": "...",
  "target_reader": "...",
  "reader_promise": "...",
  "central_question": "...",
  "what_makes_it_different": "...",
  "genre_conventions": ["..."],
  "ending": "...",
  "voice_guide": "...",
  "voice_sample": "..."
}}
"""
        return generate_validated(self.llm, prompt, BOOK_STRATEGIST_PROMPT, BookBrief, validator=self._validate)

    @staticmethod
    def _validate(brief: BookBrief):
        for field in ("logline", "reader_promise", "central_question", "ending", "voice_guide", "voice_sample"):
            if not getattr(brief, field).strip():
                return f"Field '{field}' is empty."
        return None
