"""
Publishing Kit Agent - Phase 5
Writes the store listing and cover direction from the finished book, never from the outline alone.
"""

import json
import os
from schemas.models import BookBrief, PublishingKit, StoryState
from generator.llm_client import LlmClient
from generator.json_parser import generate_validated
from prompts.system_prompts import PUBLISHING_KIT_PROMPT, language_directive


class PublishingKitAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_kit(self, title: str, author: str, brief: BookBrief, story_state: StoryState, language: str = "english") -> PublishingKit:
        recaps = "\n".join(f"{n}. {r}" for n, r in sorted(story_state.chapter_recaps.items()))
        prompt = f"""TASK: publishing kit
Title: {title}
Author: {author}
Logline: {brief.logline}
Target reader: {brief.target_reader}
Reader promise: {brief.reader_promise}
What makes it different: {brief.what_makes_it_different}
{language_directive(language)}

What actually happens in the finished book:
{recaps}

Return ONLY JSON with this schema:
{{
  "subtitle": "",
  "tagline": "...",
  "blurb": "...",
  "kdp_keywords": ["seven search phrases"],
  "bisac_categories": ["..."],
  "comparable_titles": ["..."],
  "cover_brief": "...",
  "launch_plan": ["..."]
}}
"""
        return generate_validated(self.llm, prompt, PUBLISHING_KIT_PROMPT, PublishingKit, validator=self._validate, max_tokens=3000)

    @staticmethod
    def _validate(kit: PublishingKit):
        if not kit.blurb.strip():
            return "The blurb is empty."
        if len(kit.kdp_keywords) > 7:
            return "KDP allows at most seven keyword phrases."
        return None

    @staticmethod
    def write_kit(kit: PublishingKit, directory: str) -> str:
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(kit.model_dump(), f, ensure_ascii=False, indent=2)
        path = os.path.join(directory, "listing.md")
        bullets = lambda items: "\n".join(f"- {i}" for i in items)
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                f"# Store Listing\n\n**Tagline:** {kit.tagline}\n\n## Description\n\n{kit.blurb}\n\n"
                f"## KDP Keywords\n\n{bullets(kit.kdp_keywords)}\n\n## Categories\n\n{bullets(kit.bisac_categories)}\n\n"
                f"## Comparable Titles (AI suggested: confirm they exist and fit)\n\n{bullets(kit.comparable_titles)}\n\n"
                f"## Cover Brief\n\n{kit.cover_brief}\n\n## Launch Plan\n\n{bullets(kit.launch_plan)}\n"
            )
        return path
