"""
Book Reviewer - Phase 4
Whole-book release gate: combines measurable checks with a structural read of the finished manuscript.
A book is only reported ready when every check passes.
"""

import os
import re
from collections import Counter
from typing import Dict, List
from pydantic import BaseModel, Field
from schemas.models import BookBrief, StoryState, RevisionBrief
from generator.llm_client import LlmClient
from generator.json_parser import generate_validated, StructuredOutputError
from prompts.system_prompts import BOOK_REVIEWER_PROMPT

MIN_CHAPTER_SCORE = 8.0
MIN_ARC_SCORE = 8.0
WORD_TOLERANCE = 0.9
REPEATED_PHRASE_WORDS = 6
HUMAN_CHECKLIST = [
    "Read the whole book yourself and rewrite anything that is not yours to stand behind.",
    "Hire a human copyeditor and proofreader.",
    "Get 5-10 beta readers from the target audience and act on where they stopped reading.",
    "Verify every claim in fact_check.md and resolve each [VERIFY: ...] marker (non-fiction).",
    "Commission a professional cover from publishing/listing.md's cover brief.",
    "Disclose AI-generated content when your retailer asks (Amazon KDP does at upload).",
    "Check the text for accidental similarity to existing works before release.",
]


class ArcReview(BaseModel):
    arc_score: float = Field(default=0, description="1-10 whole-book structure score")
    problems: List[str] = Field(default_factory=list)


def find_repeated_phrases(chapters: Dict[int, str], min_chapters: int = 3) -> List[str]:
    """Finds long phrases recurring across chapters, the fingerprint of a model's stock moves."""
    seen = Counter()
    for text in chapters.values():
        words = re.findall(r"\w+", text.lower())
        seen.update({" ".join(words[i:i + REPEATED_PHRASE_WORDS]) for i in range(len(words) - REPEATED_PHRASE_WORDS + 1)})
    return [phrase for phrase, count in seen.most_common(10) if count >= min_chapters]


class BookReviewer:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def review(
        self,
        title: str,
        brief: BookBrief,
        story_state: StoryState,
        chapters: Dict[int, str],
        briefs: Dict[int, RevisionBrief],
        target_words: int,
    ) -> dict:
        blockers = []
        total_words = sum(len(t.split()) for t in chapters.values())
        if total_words < target_words * WORD_TOLERANCE:
            blockers.append(f"Length: {total_words:,} words against a {target_words:,} target.")

        for num, chapter_brief in sorted(briefs.items()):
            if not chapter_brief.passed_audit:
                score = chapter_brief.craft_score
                blockers.append(f"Chapter {num} failed editorial audit (score {'unreviewed' if score is None else f'{score:.1f}'}).")

        open_clues = [c.name for c in story_state.foreshadowing_clues if c.status in ("planted", "escalated")]
        if open_clues:
            blockers.append(f"Unresolved setups: {', '.join(open_clues)}.")

        markers = sum(t.count("[VERIFY") for t in chapters.values())
        if markers:
            blockers.append(f"{markers} [VERIFY: ...] marker(s) still in the text.")

        repeated = find_repeated_phrases(chapters)
        if repeated:
            blockers.append("Stock phrases repeat across chapters: " + "; ".join(f'"{p}"' for p in repeated[:5]) + ".")

        arc = self._review_arc(title, brief, story_state, chapters)
        if arc is None:
            blockers.append("Whole-book structural review could not be completed.")
        else:
            if arc.arc_score < MIN_ARC_SCORE:
                blockers.append(f"Whole-book structure scored {arc.arc_score:.1f}/10 (needs {MIN_ARC_SCORE:.0f}).")
            blockers.extend(f"Structure: {p}" for p in arc.problems)

        scores = [b.craft_score for b in briefs.values() if b.craft_score is not None]
        return {
            "ready": not blockers,
            "blockers": blockers,
            "total_words": total_words,
            "chapters": len(chapters),
            "average_craft_score": round(sum(scores) / len(scores), 2) if scores else None,
            "lowest_craft_score": min(scores) if scores else None,
            "arc_score": arc.arc_score if arc else None,
        }

    def _review_arc(self, title: str, brief: BookBrief, story_state: StoryState, chapters: Dict[int, str]):
        if not chapters:
            return None
        recaps = "\n".join(f"{n}. {r}" for n, r in sorted(story_state.chapter_recaps.items()))
        ordered = [chapters[n] for n in sorted(chapters)]
        prompt = f"""TASK: book review
Title: {title}
Promise to the reader: {brief.reader_promise}
Central question: {brief.central_question}
Planned ending: {brief.ending}

Chapter by chapter:
{recaps}

The book's opening:
{ordered[0][:6000]}

The book's ending:
{ordered[-1][-6000:]}

Return ONLY JSON: {{"arc_score": 1-10, "problems": ["specific structural problem, naming chapters"]}}
"""
        try:
            return generate_validated(self.llm, prompt, BOOK_REVIEWER_PROMPT, ArcReview, max_tokens=2000)
        except StructuredOutputError as e:
            print(f"  [Book Reviewer Warning] {e}")
            return None

    @staticmethod
    def write_report(result: dict, title: str, briefs: Dict[int, RevisionBrief], directory: str) -> str:
        os.makedirs(directory, exist_ok=True)
        lines = [f"# Release Report: {title}", ""]
        lines.append("**Automated checks: PASSED**" if result["ready"] else "**Automated checks: NOT READY**")
        lines += [
            "",
            f"- Words: {result['total_words']:,} across {result['chapters']} chapters",
            f"- Average chapter score: {result['average_craft_score']}",
            f"- Lowest chapter score: {result['lowest_craft_score']}",
            f"- Whole-book structure score: {result['arc_score']}",
            "",
            "Scores are an AI editor's opinion, not a measure of sales.",
            "",
        ]
        if result["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in result["blockers"]] + [""]
        lines += ["## Chapter Scores", "", "| Chapter | Score | Passed |", "|---|---|---|"]
        for num, chapter_brief in sorted(briefs.items()):
            lines.append(f"| {num} | {chapter_brief.craft_score} | {'yes' if chapter_brief.passed_audit else 'no'} |")
        lines += ["", "## Required Human Steps", ""] + [f"- [ ] {item}" for item in HUMAN_CHECKLIST] + [""]
        path = os.path.join(directory, "release_report.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path
