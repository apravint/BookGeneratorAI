"""
Master Outliner Agent - Phase 1
Plans the whole book, then each chapter's scenes, from the book's own brief, world and cast.
Outlines are always model-written: a book must never inherit another book's plot template.
"""

from typing import List
from pydantic import BaseModel, Field
from schemas.models import WorldBible, CharacterRegistry, MasterOutline, ChapterBeat, SubBeat, ForeshadowingClue, BookBrief
from generator.llm_client import LlmClient
from generator.json_parser import generate_validated
from prompts.system_prompts import MASTER_OUTLINE_PROMPT, language_directive

FICTION_BEATS = ["SCENE_GOAL", "CONFLICT_ESCALATION", "DISASTER_REVERSAL", "EMOTIONAL_REACTION", "DILEMMA_CALCULATION", "PIVOTAL_DECISION"]
NONFICTION_BEATS = ["STORY_HOOK", "CORE_IDEA", "EVIDENCE", "COUNTERPOINT", "APPLICATION", "CLOSING_TURN"]


class ChapterPlan(BaseModel):
    chapter_number: int
    part_title: str = ""
    title: str
    pov_character: str = ""
    location: str = ""
    core_narrative_arc: str
    prerequisite_chapters: List[int] = Field(default_factory=list)


class SetupPayoff(BaseModel):
    name: str
    description: str
    planted_chapter: int
    target_payoff_chapter: int
    involved_characters: List[str] = Field(default_factory=list)


class BookPlan(BaseModel):
    pacing_notes: str = ""
    chapters: List[ChapterPlan] = Field(default_factory=list)
    setups_and_payoffs: List[SetupPayoff] = Field(default_factory=list)


class ScenePlan(BaseModel):
    scenes: List[SubBeat] = Field(default_factory=list)


class MasterOutlinerAgent:
    def __init__(self, llm_client: LlmClient):
        self.llm = llm_client

    def build_outline(
        self,
        world_bible: WorldBible,
        registry: CharacterRegistry,
        brief: BookBrief,
        language: str = "english",
        num_chapters: int = 24,
        scenes_per_chapter: int = 4,
        target_words: int = 80000,
    ) -> MasterOutline:
        plan = self._plan_book(world_bible, registry, brief, language, num_chapters)
        words_per_chapter = target_words // num_chapters
        chapters = []
        previous = "None; this is the opening chapter."
        for chapter_plan in plan.chapters:
            print(f"  [Agent: Master Outliner] Planning scenes for Chapter {chapter_plan.chapter_number}/{num_chapters}...")
            scenes = self._plan_scenes(chapter_plan, plan, world_bible, registry, brief, language, scenes_per_chapter, previous)
            chapters.append(ChapterBeat(
                **chapter_plan.model_dump(),
                sub_beats=scenes,
                target_word_count=words_per_chapter,
                foreshadowing_clues_to_plant=[c.name for c in plan.setups_and_payoffs if c.planted_chapter == chapter_plan.chapter_number],
                foreshadowing_clues_to_resolve=[c.name for c in plan.setups_and_payoffs if c.target_payoff_chapter == chapter_plan.chapter_number],
            ))
            previous = " ".join(s.scene_objective for s in scenes)

        clues = [
            ForeshadowingClue(
                clue_id=f"clue_{i:02d}", name=c.name, description=c.description,
                planted_chapter=c.planted_chapter, target_payoff_chapter=c.target_payoff_chapter,
                involved_characters=c.involved_characters
            )
            for i, c in enumerate(plan.setups_and_payoffs, start=1)
        ]
        return MasterOutline(
            title=world_bible.title,
            total_parts=len({c.part_title for c in plan.chapters}),
            chapters=chapters,
            pacing_notes=plan.pacing_notes,
            foreshadowing=clues,
        )

    def _book_context(self, world_bible: WorldBible, registry: CharacterRegistry, brief: BookBrief) -> str:
        cast = "\n".join(
            f"- {c.name} ({c.role}): wants {c.core_motivation}; flaw: {c.fatal_flaw}; arc: {c.arc_trajectory}"
            for c in registry.characters
        ) or "No invented cast (non-fiction)."
        rules = "\n".join(f"- {r.rule_name}: {r.narrative_consequence}" for r in world_bible.rules)
        return f"""Title: {world_bible.title}
Genre: {world_bible.genre}
Logline: {brief.logline}
Reader promise: {brief.reader_promise}
Central question: {brief.central_question}
What makes it different: {brief.what_makes_it_different}
Genre conventions: {brief.genre_conventions}
Ending: {brief.ending}
Setting: {world_bible.setting_overview}
Rules:
{rules}
Cast:
{cast}"""

    def _plan_book(self, world_bible, registry, brief, language, num_chapters) -> BookPlan:
        prompt = f"""TASK: book plan
{self._book_context(world_bible, registry, brief)}
{language_directive(language)}

Plan exactly {num_chapters} chapters grouped into parts, with at least {max(3, num_chapters // 4)} setups that pay off later.
Return ONLY JSON:
{{"pacing_notes": "...",
 "chapters": [{{"chapter_number": 1, "part_title": "...", "title": "...", "pov_character": "...", "location": "...", "core_narrative_arc": "what irreversibly changes", "prerequisite_chapters": []}}],
 "setups_and_payoffs": [{{"name": "...", "description": "...", "planted_chapter": 1, "target_payoff_chapter": 5, "involved_characters": []}}]}}
"""
        validator = lambda plan: self._validate_plan(plan, num_chapters)
        return generate_validated(self.llm, prompt, MASTER_OUTLINE_PROMPT, BookPlan, validator=validator, max_tokens=8000 + num_chapters * 250)

    @staticmethod
    def _validate_plan(plan: BookPlan, num_chapters: int):
        numbers = [c.chapter_number for c in plan.chapters]
        if numbers != list(range(1, num_chapters + 1)):
            return f"Chapters must be numbered 1 to {num_chapters} in order; got {numbers}."
        titles = [c.title.strip().lower() for c in plan.chapters]
        if len(set(titles)) != len(titles):
            return "Chapter titles must be unique."
        for clue in plan.setups_and_payoffs:
            if not 1 <= clue.planted_chapter < clue.target_payoff_chapter <= num_chapters:
                return f"Setup '{clue.name}' must be planted before its payoff, within the book."
        return None

    def _plan_scenes(self, chapter, plan, world_bible, registry, brief, language, scene_count, previous) -> List[SubBeat]:
        beat_types = FICTION_BEATS if brief.is_fiction else NONFICTION_BEATS
        plants = [c.name for c in plan.setups_and_payoffs if c.planted_chapter == chapter.chapter_number]
        payoffs = [c.name for c in plan.setups_and_payoffs if c.target_payoff_chapter == chapter.chapter_number]
        book_map = "\n".join(f"{c.chapter_number}. {c.title}: {c.core_narrative_arc}" for c in plan.chapters)
        heading_rule = "Leave heading empty." if brief.is_fiction else "Give each scene a short, intriguing reader-facing heading."
        prompt = f"""TASK: scene plan
{self._book_context(world_bible, registry, brief)}
{language_directive(language)}

Whole book:
{book_map}

Previous chapter's scenes: {previous}

Plan exactly {scene_count} scenes for Chapter {chapter.chapter_number}: {chapter.title}
Chapter must achieve: {chapter.core_narrative_arc}
Must plant: {plants}
Must pay off: {payoffs}
Choose each beat_type from {beat_types}. {heading_rule}
Tension must vary. The last scene's ending_hook must force the next chapter open.

Return ONLY JSON:
{{"scenes": [{{"section_number": "{chapter.chapter_number}.1", "heading": "", "scene_objective": "specific event", "beat_type": "{beat_types[0]}", "micro_tension_level": 5, "pov_internal_state": "what is hidden or feared", "characters_present": [], "key_interaction": "the concrete turn", "sensory_or_structural_detail": "one unexpected specific detail", "ending_hook": "the open question"}}]}}
"""
        def validator(result: ScenePlan):
            if len(result.scenes) != scene_count:
                return f"Plan exactly {scene_count} scenes; got {len(result.scenes)}."
            if len({s.scene_objective.strip().lower() for s in result.scenes}) != scene_count:
                return "Every scene needs its own distinct objective."
            return None

        result = generate_validated(self.llm, prompt, MASTER_OUTLINE_PROMPT, ScenePlan, validator=validator, max_tokens=800 * scene_count)
        for index, scene in enumerate(result.scenes, start=1):
            scene.section_number = f"{chapter.chapter_number}.{index}"
        return result.scenes
