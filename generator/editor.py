"""
Multi-Agent Editorial Engine Module
Applies Developmental Editing, Line Editing, Fact Checking, and Prose Polishing passes
to elevate any generated manuscript into a world-class bestseller.
"""

import re
from .llm_client import LlmClient

class DevelopmentalEditor:
    """Refines narrative structure, flow, clarity, and thematic depth."""

    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def edit_chapter(self, chapter_title: str, raw_markdown: str, genre: str) -> str:
        system_prompt = f"""
You are an elite Senior Developmental Editor at a top-tier publishing house (Penguin Random House / O'Reilly / HarperCollins).
Your job is to polish, refine, and elevate the provided draft chapter titled '{chapter_title}'.

Genre: {genre}.

Editorial Rules:
1. Preserve all markdown section headings (##, ###), code blocks (```), tables (|), and blockquotes (>).
2. Enhance prose quality: eliminate repetitive phrasing, sharpen metaphors, add vivid transitions, and strengthen narrative hooks.
3. Ensure every sub-section ends with a strong takeaway or smooth transition into the next sub-section.
4. Add 1-2 impactful quote blockquotes (> "Quote") if missing.
5. Return ONLY the polished Markdown text.
"""
        user_prompt = f"Please perform a complete Developmental Edit on this draft chapter:\n\n{raw_markdown}"
        
        try:
            edited_text = self.llm.generate_text(user_prompt, system_prompt)
            return edited_text if edited_text and len(edited_text) > 200 else raw_markdown
        except Exception as e:
            print(f"  [Editor Warning] Developmental edit pass skipped (fallback to raw draft): {e}")
            return raw_markdown
